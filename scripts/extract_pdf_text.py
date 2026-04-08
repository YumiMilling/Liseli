"""
Extract text from all MoE Zambian language PDFs.
Pulls out:
1. Glossary/vocabulary sections (English-Zambian word pairs)
2. Full text content for training data
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
TEXT_DIR = BASE_DIR / "data" / "moe-extracted-text"

# Language detection from filename
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


def pdf_to_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception as e:
        print(f"  ERROR extracting {pdf_path.name}: {e}")
        return ""


def extract_glossary_pairs(text: str) -> list[tuple[str, str]]:
    """
    Extract English-Zambian word pairs from glossary sections.
    Patterns found in MoE PDFs:
    - "English Term - Zambian Term" or "English Term � Zambian Term"
    - "Zambian Term - English Term"
    - Numbered lists: "1. Zambian - English"
    """
    pairs = []

    # Pattern 1: "English- Zambian" or "English � Zambian" (from Bemba glossary)
    # e.g., "Overview- Ubulondoloshi", "Theme – Icipande"
    for match in re.finditer(
        r'([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\s*[-–—]\s*([A-Z][a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+(?:\s+[a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+)*)',
        text
    ):
        en, zam = match.group(1).strip(), match.group(2).strip()
        if len(en) > 2 and len(zam) > 2 and len(en) < 50 and len(zam) < 50:
            # Check if English side looks English
            if re.match(r'^[A-Za-z\s]+$', en):
                pairs.append((en, zam))

    # Pattern 2: Numbered glossary "1. Zambian- English" (from Nyanja glossary)
    # e.g., "1. Asanayambe Kulemba- Pre-writing"
    for match in re.finditer(
        r'\d+\.\s+([A-ZÀ-Ö][a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+(?:\s+[a-zA-Zàáâãäåèéêëìíîïòóôõöùúûü]+)*)\s*[-–—]\s*([A-Z][a-zA-Z\s]+)',
        text
    ):
        zam, en = match.group(1).strip(), match.group(2).strip()
        if len(en) > 2 and len(zam) > 2 and len(en) < 60 and len(zam) < 60:
            pairs.append((en.strip(), zam.strip()))

    # Pattern 3: Key terms sections - "Mau ofunika: word1, word2"
    # Look for labeled vocabulary
    for match in re.finditer(
        r'(?:Key\s+(?:Words?|Terms?)|Amashiwi\s+aya\s+kankaala|Mau\s+ofunika(?:\s+kudziwa)?)\s*[:\-]\s*(.+?)(?:\n|$)',
        text, re.IGNORECASE
    ):
        terms = match.group(1).strip()
        # Split by comma or "na"/"ndi"
        for term in re.split(r'[,;]|\s+na\s+|\s+ndi\s+|\s+elyo\s+', terms):
            term = term.strip().strip('.')
            if len(term) > 2 and len(term) < 40:
                pairs.append(("_keyword", term))

    return pairs


def extract_sentences(text: str) -> list[str]:
    """Extract clean sentences from PDF text (for raw training data)."""
    sentences = []
    # Split into lines, clean up
    for line in text.split('\n'):
        line = line.strip()
        # Skip short lines, numbers, headers
        if len(line) < 10 or len(line) > 200:
            continue
        if re.match(r'^\d+$', line):
            continue
        if line.isupper() and len(line) < 60:
            continue
        # Skip lines that are mostly English (curriculum framework text)
        english_words = len(re.findall(r'\b(?:the|and|of|to|in|for|is|are|was|with|that|this|from|by|on|at|or|an|be|has|have|had|not|but|will|would|can|could|should|may|might)\b', line.lower()))
        total_words = len(line.split())
        if total_words > 0 and english_words / total_words > 0.4:
            continue
        sentences.append(line)
    return sentences


def main():
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print("MOE PDF TEXT EXTRACTION")
    print("=" * 60)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDFs")

    all_glossary_pairs = defaultdict(list)
    all_sentences = defaultdict(list)
    total_glossary = 0
    total_sentences = 0

    for pdf_file in pdf_files:
        lang = detect_language(pdf_file.name)
        if not lang:
            continue

        print(f"\n  {pdf_file.name}")
        print(f"    Language: {lang}")

        text = pdf_to_text(pdf_file)
        if not text:
            print("    SKIP: no text extracted")
            continue

        # Save raw text
        text_file = TEXT_DIR / f"{pdf_file.stem}.txt"
        text_file.write_text(text, encoding="utf-8")

        # Extract glossary pairs
        glossary = extract_glossary_pairs(text)
        if glossary:
            print(f"    Glossary pairs: {len(glossary)}")
            for en, zam in glossary[:3]:
                print(f"      {en} -> {zam}")
            if len(glossary) > 3:
                print(f"      ... and {len(glossary) - 3} more")
            all_glossary_pairs[lang].extend(glossary)
            total_glossary += len(glossary)

        # Extract sentences for training
        sents = extract_sentences(text)
        print(f"    Sentences: {len(sents)}")
        all_sentences[lang].extend(sents)
        total_sentences += len(sents)

    # Insert glossary pairs into database
    print(f"\n{'=' * 60}")
    print("INSERTING INTO DATABASE")
    print(f"{'=' * 60}")

    words_inserted = 0
    for lang, pairs in all_glossary_pairs.items():
        for en_text, zam_text in pairs:
            if en_text == "_keyword":
                # Just a keyword, no English pair - store as raw vocab
                continue

            en_clean = en_text.strip().lower()
            zam_clean = zam_text.strip()

            if len(en_clean) < 2 or len(zam_clean) < 2:
                continue

            # Check/create sentence
            existing = conn.execute(
                "SELECT id FROM sentences WHERE english = ? AND tier = 'word'",
                (en_clean,)
            ).fetchone()

            if existing:
                sentence_id = existing[0]
            else:
                sentence_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO sentences (id, english, tier, domain, concept_id, source, difficulty)
                    VALUES (?, ?, 'word', 'education', 'moe-glossary', 'moe', 1)
                """, (sentence_id, en_clean))

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status)
                    VALUES (?, ?, ?, ?, 'moe', 'verified')
                """, (str(uuid.uuid4()), sentence_id, lang, zam_clean))
                words_inserted += 1
            except Exception:
                pass

    # Store raw sentences as training corpus
    sents_inserted = 0
    for lang, sents in all_sentences.items():
        # Deduplicate
        unique_sents = list(set(sents))
        for sent in unique_sents[:500]:  # Cap per language to avoid bloat
            sentence_id = str(uuid.uuid4())
            try:
                conn.execute("""
                    INSERT INTO sentences (id, english, tier, domain, concept_id, source, difficulty)
                    VALUES (?, ?, 'sentence', 'education', 'moe-corpus', 'moe', 2)
                """, (sentence_id, f"[{lang}] {sent}"))
                sents_inserted += 1
            except Exception:
                pass

    conn.commit()

    # Summary
    print(f"\n  Glossary words inserted: {words_inserted}")
    print(f"  Training sentences stored: {sents_inserted}")

    print(f"\n{'=' * 60}")
    print("FINAL DATABASE SUMMARY")
    print(f"{'=' * 60}")

    for row in conn.execute("SELECT tier, source, COUNT(*) FROM sentences GROUP BY tier, source ORDER BY tier, source"):
        print(f"  {row[0]:10s} | {row[1]:12s} | {row[2]}")

    print(f"\nTranslations by language:")
    for row in conn.execute("""
        SELECT t.language, COUNT(*),
               SUM(CASE WHEN t.status='verified' THEN 1 ELSE 0 END) as verified
        FROM translations t
        GROUP BY t.language ORDER BY t.language
    """):
        print(f"  {row[0]:10s}: {row[1]} total ({row[2]} verified)")

    print(f"\nRaw text files: {TEXT_DIR}")
    print(f"Total text files: {len(list(TEXT_DIR.glob('*.txt')))}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
