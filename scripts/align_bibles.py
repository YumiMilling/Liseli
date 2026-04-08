"""
Align all 7 Bible translations + English by verse reference.
Creates proper parallel pairs in the translations table.
"""
import sqlite3
import uuid
import re
from pathlib import Path

DB_PATH = Path("data/liseli_local.db")

BIBLES = {
    "bemba": "data/bibles/Bemba_ILL15.txt",
    "tonga": "data/bibles/Tonga_Tonga96.txt",
    "lozi": "data/bibles/Lozi_Lozi09.txt",
    "lunda": "data/bibles/Lunda_LNB04.txt",
    "luvale": "data/bibles/Luvale_LUE70.txt",
    "kaonde": "data/bibles/Kaonde_KNTP.txt",
}

ENG_PATH = "data/bibles/eng-engwebp.txt"
VREF_PATH = "data/bibles/vref.txt"
NYA_PATH = "data/bibles/nya-nya.txt"

# Map BibleNLP book codes to bible.com codes (they should be the same 3-letter codes)
# vref format: "GEN 1:1", bible.com header: "GEN\t1", verse: "1\ttext"


def parse_bible_com(path: str) -> dict[str, str]:
    """Parse bible.com format into {ref: text} where ref = 'GEN 1:1'."""
    verses = {}
    current_book = None
    current_chapter = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue

            # Check for header lines like "=== GEN 1 ===" or "### GEN"
            header = re.match(r"^===\s*(\w+)\s+(\d+)\s*===$", line)
            if header:
                current_book = header.group(1)
                current_chapter = header.group(2)
                continue

            section = re.match(r"^###\s*(\w+)", line)
            if section:
                current_book = section.group(1)
                continue

            # Tab-separated: could be "GEN\t1" (book header) or "1\tverse text"
            parts = line.split("\t", 1)
            if len(parts) == 2:
                if re.match(r"^[A-Z0-9]{3}$", parts[0]):
                    # Book + chapter header
                    current_book = parts[0]
                    current_chapter = parts[1].strip()
                elif re.match(r"^\d+$", parts[0]) and current_book and current_chapter:
                    # Verse line
                    verse_num = parts[0]
                    text = parts[1].strip()
                    if text:
                        ref = f"{current_book} {current_chapter}:{verse_num}"
                        verses[ref] = text
            elif re.match(r"^(\d+)\s+(.+)", line) and current_book and current_chapter:
                # Format without tab: "1 In the beginning..."
                m = re.match(r"^(\d+)\s+(.+)", line)
                verse_num = m.group(1)
                text = m.group(2).strip()
                if text:
                    ref = f"{current_book} {current_chapter}:{verse_num}"
                    verses[ref] = text

    return verses


def parse_biblenlp(text_path: str, vref_path: str) -> dict[str, str]:
    """Parse BibleNLP format (line-aligned with vref.txt)."""
    verses = {}
    vrefs = open(vref_path, encoding="utf-8").read().strip().split("\n")
    texts = open(text_path, encoding="utf-8").read().strip().split("\n")
    for ref, text in zip(vrefs, texts):
        text = text.strip()
        if text and len(text) > 2:
            verses[ref.strip()] = text
    return verses


def classify_tier(text: str) -> str:
    words = len(text.split())
    if words <= 2:
        return "word"
    if words <= 6:
        return "phrase"
    return "sentence"


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("=" * 60)
    print("BIBLE ALIGNMENT — ALL LANGUAGES")
    print("=" * 60)

    # Parse English
    print("\nParsing English (BibleNLP)...")
    en_verses = parse_biblenlp(ENG_PATH, VREF_PATH)
    print(f"  {len(en_verses)} English verses")

    # Parse Nyanja (already BibleNLP format)
    print("Parsing Nyanja (BibleNLP)...")
    nya_verses = parse_biblenlp(NYA_PATH, VREF_PATH)
    print(f"  {len(nya_verses)} Nyanja verses")

    # Parse all bible.com translations
    all_bibles = {}
    for lang, path in BIBLES.items():
        print(f"Parsing {lang} (bible.com)...")
        verses = parse_bible_com(path)
        all_bibles[lang] = verses
        print(f"  {len(verses)} verses")

    # Add Nyanja
    all_bibles["nyanja"] = nya_verses

    # Find refs that exist in English AND at least one target language
    all_refs = set(en_verses.keys())
    for lang_verses in all_bibles.values():
        all_refs &= set()  # don't intersect, we want union
    # Actually, iterate all English refs and check what aligns
    print(f"\nTotal English verse refs: {len(en_verses)}")

    # Delete old bible parallel data (we're rebuilding properly)
    old_count = conn.execute("SELECT COUNT(*) FROM sentences WHERE concept_id LIKE 'bible%'").fetchone()[0]
    if old_count:
        conn.execute("DELETE FROM translations WHERE sentence_id IN (SELECT id FROM sentences WHERE concept_id LIKE 'bible%')")
        conn.execute("DELETE FROM sentences WHERE concept_id LIKE 'bible%'")
        conn.commit()
        print(f"Cleared {old_count} old Bible entries")

    # Insert aligned pairs
    total_sentences = 0
    total_translations = 0
    lang_counts = {lang: 0 for lang in all_bibles}

    for ref, en_text in en_verses.items():
        if len(en_text) < 5 or len(en_text) > 500:
            continue

        # Check which languages have this verse
        available = {}
        for lang, verses in all_bibles.items():
            if ref in verses:
                tgt = verses[ref]
                if len(tgt) > 3:
                    available[lang] = tgt

        if not available:
            continue

        # Insert English sentence
        sid = str(uuid.uuid4())
        tier = classify_tier(en_text)
        conn.execute(
            "INSERT INTO sentences (id, english, tier, domain, concept_id, source, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, en_text, tier, "religion", f"bible-{ref}", "community", 2),
        )
        total_sentences += 1

        # Insert translations for each language that has this verse
        for lang, tgt_text in available.items():
            dialect = "chichewa-mw" if lang == "nyanja" else None
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), sid, lang, tgt_text, "community", "verified", dialect),
                )
                lang_counts[lang] += 1
                total_translations += 1
            except Exception:
                pass

        if total_sentences % 5000 == 0:
            conn.commit()
            print(f"  ...{total_sentences:,} sentences, {total_translations:,} translations")

    conn.commit()

    print(f"\n{'=' * 60}")
    print("BIBLE ALIGNMENT COMPLETE")
    print(f"  Sentences: {total_sentences:,}")
    print(f"  Translations: {total_translations:,}")
    print(f"\n  Per language:")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        print(f"    {lang:10s}: {count:>8,}")

    # Verify total DB state
    print(f"\nFull DB translations:")
    for r in conn.execute("SELECT language, COUNT(*) FROM translations GROUP BY language ORDER BY COUNT(*) DESC"):
        print(f"    {r[0]:10s}: {r[1]:>8,}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
