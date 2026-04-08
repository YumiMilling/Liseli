"""
Targeted vocabulary extraction from MoE PDFs.
Each language has different patterns for vocabulary sections.
"""

import sqlite3
import subprocess
import uuid
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
PDF_DIR = BASE_DIR / "data" / "moe-zambian-languages"


def pdf_to_text(pdf_path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception:
        return ""


def extract_nyanja_glossary(text: str) -> list[tuple[str, str]]:
    """
    Nyanja PDFs have numbered glossaries like:
    1. Capamutu-Theme
    3. Cidule - Overview
    23. Kumvetsela ndi Kulankhula- Listening and Speaking
    """
    pairs = []
    for match in re.finditer(
        r'\d+\.\s+(.+?)\s*[-–—]\s*(.+?)(?:\s*\d+\.|$|\n)',
        text
    ):
        nyanja = match.group(1).strip()
        english = match.group(2).strip()
        # Clean up OCR artifacts
        english = re.sub(r'\s+', ' ', english).strip()
        nyanja = re.sub(r'\s+', ' ', nyanja).strip()
        if (len(english) > 2 and len(nyanja) > 2
            and len(english) < 60 and len(nyanja) < 60
            and not any(skip in english.lower() for skip in ['school', 'college', 'teacher', 'lecturer', 'head', 'ministry'])):
            pairs.append((english, nyanja))
    return pairs


def extract_lunda_keywords(text: str) -> list[str]:
    """
    Lunda PDFs have: Mazu Alema \n - word1 - word2 - word3
    """
    words = []
    sections = re.split(r'Mazu Alema', text)
    for section in sections[1:]:  # Skip before first occurrence
        # Get the dash-separated words following "Mazu Alema"
        lines = section.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line.startswith('-'):
                word = line.lstrip('- ').strip()
                if len(word) > 1 and len(word) < 40 and not word[0].isdigit():
                    words.append(word)
            # Also handle "Word1 - Word2 - Word3" on one line
            elif ' - ' in line:
                for part in line.split(' - '):
                    part = part.strip().lstrip('- ')
                    if len(part) > 1 and len(part) < 40:
                        words.append(part)
    return list(set(words))


def extract_bemba_glossary(text: str) -> list[tuple[str, str]]:
    """
    Bemba PDFs have: "Overview- Ubulondoloshi", "Theme – Icipande"
    in the AMASHIWI AYABOMFIWA section.
    """
    pairs = []
    # Find the glossary section
    match = re.search(r'AMASHIWI AYABOMFIWA.*?\n(.*?)(?:INTENDEKELO|IFYO ICI)', text, re.DOTALL)
    if not match:
        return pairs

    section = match.group(1)
    for m in re.finditer(r'([A-Z][a-z]+(?:\s+[A-Za-z/]+)*)\s*[-–—]\s*([A-Z][a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+(?:\s+[a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+)*)', section):
        english = m.group(1).strip()
        bemba = m.group(2).strip()
        if (len(english) > 2 and len(bemba) > 2
            and len(english) < 50 and len(bemba) < 50
            and english.lower() not in ('competence', 'outcome')):
            pairs.append((english, bemba))
    return pairs


def extract_silozi_glossary(text: str) -> list[tuple[str, str]]:
    """
    Silozi PDFs have vocabulary sections with terms.
    """
    pairs = []
    # Look for "Manzwi ni lipulelo za butokwa" sections
    sections = re.split(r'Manzwi ni lipulelo za butokwa', text)
    for section in sections[1:]:
        lines = section.split('\n')
        for line in lines[:20]:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                word = line.lstrip('-•  ').strip()
                if len(word) > 1 and len(word) < 40:
                    pairs.append(("_vocab", word))
    return pairs


def extract_reading_sentences(text: str, lang: str) -> list[str]:
    """
    Extract short, clean sentences from reading exercises and stories.
    These are actual language content, not instructions.
    """
    sentences = []

    # Language-specific story/reading markers
    markers = {
        'bemba': ['Ilyashi', 'Icilangililo'],
        'nyanja': ['Nkhani', 'Citsanzo', 'ZITSANZO'],
        'tonga': ['Ciiyo', 'Cilangilizyo'],
        'lozi': ['Likande', 'Mutala'],
        'lunda': ['Kaheka', 'Kukoka'],
        'kaonde': ['Ngitabulwilo', 'Kishina'],
        'luvale': ['Likisholo', 'Mangana'],
    }

    # Split text into lines and find short clean sentences in target language
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < 8 or len(line) > 120:
            continue
        # Skip if mostly numbers, headers, or English
        if re.match(r'^\d+$', line):
            continue
        if line.isupper():
            continue
        # Skip lines with too many English words
        eng_count = len(re.findall(r'\b(?:the|and|of|to|in|for|is|are|was|with|that|this|from|by|on|at)\b', line.lower()))
        if eng_count > 2:
            continue
        # Skip curriculum jargon
        if any(skip in line.lower() for skip in ['competence', 'curriculum', 'assessment', 'methodology', 'module']):
            continue
        # Keep lines that look like actual content sentences
        if line[0].isupper() and line.endswith(('.', '?', '!')):
            # Extra check: should have mostly non-English characters or words
            words = line.split()
            if len(words) >= 3 and len(words) <= 20:
                sentences.append(line)

    return sentences[:100]  # Cap per file


def main():
    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print("TARGETED PDF VOCABULARY EXTRACTION")
    print("=" * 60)

    results = defaultdict(lambda: {"glossary": [], "keywords": [], "sentences": []})

    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        name = pdf.name.upper()

        # Detect language
        lang = None
        for kw, lid in {"ICIBEMBA": "bemba", "BEMBA": "bemba", "CINYANJA": "nyanja",
                        "NYANJA": "nyanja", "CHITONGA": "tonga", "TONGA": "tonga",
                        "SILOZI": "lozi", "LOZI": "lozi", "KIKAONDE": "kaonde",
                        "KAONDE": "kaonde", "LUNDA": "lunda", "LUVALE": "luvale"}.items():
            if kw in name:
                lang = lid
                break
        if not lang:
            continue

        text = pdf_to_text(pdf)
        if not text:
            continue

        # Extract based on language
        if lang == "nyanja":
            glossary = extract_nyanja_glossary(text)
            results[lang]["glossary"].extend(glossary)
        elif lang == "bemba":
            glossary = extract_bemba_glossary(text)
            results[lang]["glossary"].extend(glossary)
        elif lang == "lunda":
            keywords = extract_lunda_keywords(text)
            results[lang]["keywords"].extend(keywords)
        elif lang == "lozi":
            glossary = extract_silozi_glossary(text)
            results[lang]["glossary"].extend(glossary)

        # Extract reading sentences for all languages
        sents = extract_reading_sentences(text, lang)
        results[lang]["sentences"].extend(sents)

    # Print and insert results
    inserted_glossary = 0
    inserted_keywords = 0
    inserted_sentences = 0

    for lang, data in sorted(results.items()):
        print(f"\n--- {lang.upper()} ---")

        # Glossary pairs (bilingual)
        unique_glossary = list(set(data["glossary"]))
        if unique_glossary:
            print(f"  Glossary pairs: {len(unique_glossary)}")
            for en, zam in unique_glossary[:8]:
                if en != "_vocab":
                    print(f"    {en:30s} -> {zam}")
                else:
                    print(f"    [vocab] {zam}")

            for en, zam in unique_glossary:
                if en == "_vocab":
                    continue
                en_clean = en.strip().lower()
                existing = conn.execute(
                    "SELECT id FROM sentences WHERE english = ? AND tier = 'word'", (en_clean,)
                ).fetchone()
                if existing:
                    sid = existing[0]
                else:
                    sid = str(uuid.uuid4())
                    conn.execute(
                        "INSERT INTO sentences (id, english, tier, domain, concept_id, source) VALUES (?, ?, 'word', 'education', 'moe-glossary', 'moe')",
                        (sid, en_clean)
                    )
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status) VALUES (?, ?, ?, ?, 'moe', 'verified')",
                        (str(uuid.uuid4()), sid, lang, zam)
                    )
                    inserted_glossary += 1
                except Exception:
                    pass

        # Keywords (monolingual vocab)
        unique_kw = list(set(data["keywords"]))
        if unique_kw:
            print(f"  Keywords: {len(unique_kw)}")
            for kw in unique_kw[:8]:
                print(f"    {kw}")

            for kw in unique_kw:
                sid = str(uuid.uuid4())
                conn.execute(
                    "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source) VALUES (?, ?, 'word', 'education', 'moe-keyword', 'moe')",
                    (sid, f"[{lang}] {kw}")
                )
                inserted_keywords += 1

        # Reading sentences
        unique_sents = list(set(data["sentences"]))
        if unique_sents:
            print(f"  Reading sentences: {len(unique_sents)}")
            for s in unique_sents[:5]:
                print(f"    {s[:80]}...")

            for sent in unique_sents:
                sid = str(uuid.uuid4())
                conn.execute(
                    "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source) VALUES (?, ?, 'sentence', 'education', 'moe-reading', 'moe')",
                    (sid, f"[{lang}] {sent}")
                )
                inserted_sentences += 1

    conn.commit()

    print(f"\n{'=' * 60}")
    print(f"INSERTED")
    print(f"  Glossary pairs: {inserted_glossary}")
    print(f"  Keywords: {inserted_keywords}")
    print(f"  Reading sentences: {inserted_sentences}")

    # Total DB summary
    print(f"\n{'=' * 60}")
    print(f"DATABASE TOTALS")
    for r in conn.execute("SELECT tier, source, COUNT(*) FROM sentences GROUP BY tier, source ORDER BY tier, source"):
        print(f"  {r[0]:10s} | {r[1]:12s} | {r[2]}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
