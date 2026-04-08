"""
Populate the corpus table with ALL monolingual text from available sources.
No filtering — raw quantity for language model training.
"""

import sqlite3
import subprocess
import uuid
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
PDF_DIR = BASE_DIR / "data" / "moe-zambian-languages"
TEXT_DIR = BASE_DIR / "data" / "moe-extracted-text"

LANG_KEYWORDS = {
    "ICIBEMBA": "bemba", "BEMBA": "bemba",
    "CINYANJA": "nyanja", "NYANJA": "nyanja",
    "CHITONGA": "tonga", "TONGA": "tonga",
    "SILOZI": "lozi", "LOZI": "lozi",
    "KIKAONDE": "kaonde", "KAONDE": "kaonde",
    "LUNDA": "lunda",
    "LUVALE": "luvale",
}


def detect_language(filename: str) -> str | None:
    name = filename.upper()
    for keyword, lang in LANG_KEYWORDS.items():
        if keyword in name:
            return lang
    return None


def extract_sentences(text: str) -> list[str]:
    """Extract all usable text lines — minimal filtering."""
    sentences = []
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < 5:
            continue
        if re.match(r'^\d+$', line):  # page numbers
            continue
        if re.match(r'^[ivxlcdm]+$', line.lower()):  # roman numerals
            continue
        if len(line) > 500:
            continue
        sentences.append(line)
    return sentences


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("=" * 60)
    print("POPULATING CORPUS TABLE")
    print("=" * 60)

    # Track sources
    sources = {}
    total = 0

    # === 1. MoE PDFs — raw monolingual text ===
    print("\n1. MoE Teaching Module PDFs...")
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        lang = detect_language(pdf.name)
        if not lang:
            continue

        # Use pre-extracted text if available
        text_file = TEXT_DIR / f"{pdf.stem}.txt"
        if text_file.exists():
            text = text_file.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                result = subprocess.run(
                    ["pdftotext", str(pdf), "-"],
                    capture_output=True, text=True, timeout=30
                )
                text = result.stdout
            except Exception:
                continue

        sents = extract_sentences(text)
        count = 0
        for s in sents:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO corpus (id, language, text, source, source_file, domain) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), lang, s, "moe", pdf.name, "education")
                )
                count += 1
            except Exception:
                pass

        if count:
            key = f"moe-{lang}"
            sources[key] = sources.get(key, 0) + count
            total += count

    conn.commit()
    print(f"  Inserted {total:,} lines from MoE PDFs")

    # === 2. Storybook text (monolingual side) ===
    print("\n2. Storybook text (all languages)...")
    storybook_count = 0
    for r in conn.execute("SELECT language, text FROM translations WHERE source IN ('moe', 'community') AND sentence_id IN (SELECT id FROM sentences WHERE concept_id LIKE 'storybook%')"):
        try:
            conn.execute(
                "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), r[0], r[1], "storybook", "education", "verified")
            )
            storybook_count += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Inserted {storybook_count:,} storybook translations")
    total += storybook_count

    # === 3. Bible text (Nyanja monolingual) ===
    print("\n3. Bible text...")
    bible_count = 0
    for r in conn.execute("SELECT language, text FROM translations WHERE sentence_id IN (SELECT id FROM sentences WHERE concept_id LIKE 'bible%')"):
        try:
            conn.execute(
                "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), r[0], r[1], "bible", "religion", "verified")
            )
            bible_count += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Inserted {bible_count:,} Bible verses")
    total += bible_count

    # === 4. English sentences (for English corpus) ===
    print("\n4. English sentences...")
    en_count = 0
    for r in conn.execute("SELECT english FROM sentences WHERE length(english) > 5 AND english NOT LIKE '[%'"):
        try:
            conn.execute(
                "INSERT OR IGNORE INTO corpus (id, language, text, source, domain) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "english", r[0], "parallel", "general")
            )
            en_count += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Inserted {en_count:,} English sentences")
    total += en_count

    # === Register data sources ===
    data_sources = [
        ("storybooks-zambia", "https://storybookszambia.net/", "parallel_corpus",
         "bemba,nyanja,tonga,lozi,kaonde,lunda,luvale,english", "CC-BY",
         "40 stories, all 7 languages + English, primary school level"),
        ("moe-teaching-modules", "https://www.edu.gov.zm/?page_id=1142", "monolingual",
         "bemba,nyanja,tonga,lozi,kaonde,lunda,luvale", "Government",
         "69 teaching modules, Grade 1 / ECE / Form 1, monolingual"),
        ("nyanja-bible", "https://github.com/BibleNLP/ebible", "parallel_corpus",
         "nyanja,english", "Varies",
         "30K+ verse-aligned Nyanja-English pairs from BibleNLP/ebible"),
        ("storybooks-bilingual-pdf", "https://gitlab.com/global-asp/sbzm-pdf", "parallel_corpus",
         "bemba,nyanja,tonga,lozi,kaonde,lunda,luvale,english", "CC-BY",
         "280 bilingual PDFs, imageless format"),
    ]
    for name, url, stype, langs, license, notes in data_sources:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO data_sources (id, name, url, source_type, languages, license, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), name, url, stype, langs, license, notes)
            )
        except Exception:
            pass
    conn.commit()

    # === Summary ===
    print(f"\n{'=' * 60}")
    print("CORPUS SUMMARY")
    print(f"{'=' * 60}")
    print(f"\nTotal corpus entries: {total:,}")
    print(f"\nBy language:")
    for r in conn.execute("SELECT language, COUNT(*), SUM(length(text)) FROM corpus GROUP BY language ORDER BY COUNT(*) DESC"):
        chars = r[2] or 0
        words_est = chars // 6  # rough estimate
        print(f"  {r[0]:10s}: {r[1]:>8,} lines  (~{words_est:>10,} words)")

    print(f"\nBy source:")
    for r in conn.execute("SELECT source, COUNT(*) FROM corpus GROUP BY source ORDER BY COUNT(*) DESC"):
        print(f"  {r[0]:15s}: {r[1]:>8,}")

    print(f"\nBy quality:")
    for r in conn.execute("SELECT quality, COUNT(*) FROM corpus GROUP BY quality ORDER BY COUNT(*) DESC"):
        print(f"  {r[0]:10s}: {r[1]:>8,}")

    print(f"\n{'=' * 60}")
    print("FULL DATABASE OVERVIEW")
    print(f"{'=' * 60}")
    print(f"\n  Parallel pairs (sentences + translations):")
    print(f"    sentences:    {conn.execute('SELECT COUNT(*) FROM sentences').fetchone()[0]:>8,}")
    print(f"    translations: {conn.execute('SELECT COUNT(*) FROM translations').fetchone()[0]:>8,}")
    print(f"\n  Monolingual corpus:")
    print(f"    corpus:       {conn.execute('SELECT COUNT(*) FROM corpus').fetchone()[0]:>8,}")
    print(f"\n  Source materials:")
    print(f"    PDFs:         {conn.execute('SELECT COUNT(*) FROM source_materials').fetchone()[0]:>8,}")
    print(f"    data_sources: {conn.execute('SELECT COUNT(*) FROM data_sources').fetchone()[0]:>8,}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
