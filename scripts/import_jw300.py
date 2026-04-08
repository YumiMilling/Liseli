"""
Import JW300 parallel corpus for all 7 Zambian languages.
Downloads from OPUS/HuggingFace and inserts bilingual pairs into SQLite.
"""

import sqlite3
import uuid
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"

# JW300 language codes -> our language names
LANG_MAP = {
    "bem": "bemba",
    "nya": "nyanja",
    "toi": "tonga",
    "loz": "lozi",
    "kqn": "kaonde",
    "lun": "lunda",
    "lue": "luvale",
}


def classify_tier(text: str) -> str:
    words = text.split()
    if len(words) <= 2:
        return "word"
    elif len(words) <= 6:
        return "phrase"
    return "sentence"


def download_jw300(lang_code: str) -> list[tuple[str, str]]:
    """Download JW300 en-XX pairs from OPUS via HuggingFace."""
    from datasets import load_dataset

    pair_name = f"en-{lang_code}" if "en" < lang_code else f"{lang_code}-en"

    print(f"  Downloading JW300 {pair_name}...")
    try:
        ds = load_dataset("opus-100", pair_name, split="train", trust_remote_code=True)
        pairs = []
        for row in ds:
            trans = row["translation"]
            en = trans.get("en", "")
            tgt = trans.get(lang_code, "")
            if en and tgt:
                pairs.append((en.strip(), tgt.strip()))
        return pairs
    except Exception as e1:
        print(f"    opus-100 failed: {e1}")

    # Fallback: try opus_jw300 directly
    try:
        ds = load_dataset("Helsinki-NLP/opus-100", f"en-{lang_code}", split="train", trust_remote_code=True)
        pairs = []
        for row in ds:
            trans = row["translation"]
            en = trans.get("en", "")
            tgt = trans.get(lang_code, "")
            if en and tgt:
                pairs.append((en.strip(), tgt.strip()))
        return pairs
    except Exception as e2:
        print(f"    Helsinki-NLP failed: {e2}")

    # Try direct OPUS download
    try:
        import urllib.request
        import zipfile
        import io
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        base_url = f"https://object.pouta.csc.fi/OPUS-JW300/v1/moses/{lang_code}-en.txt.zip"
        alt_url = f"https://object.pouta.csc.fi/OPUS-JW300/v1/moses/en-{lang_code}.txt.zip"

        for url in [base_url, alt_url]:
            try:
                print(f"    Trying OPUS direct: {url}")
                req = urllib.request.Request(url, headers={"User-Agent": "Liseli/1.0"})
                resp = urllib.request.urlopen(req, context=ctx, timeout=60)
                data = resp.read()

                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    files = zf.namelist()
                    print(f"    Files in zip: {files}")

                    en_file = [f for f in files if f.endswith('.en')]
                    tgt_file = [f for f in files if f.endswith(f'.{lang_code}')]

                    if en_file and tgt_file:
                        en_lines = zf.read(en_file[0]).decode('utf-8').strip().split('\n')
                        tgt_lines = zf.read(tgt_file[0]).decode('utf-8').strip().split('\n')

                        pairs = []
                        for en, tgt in zip(en_lines, tgt_lines):
                            en, tgt = en.strip(), tgt.strip()
                            if en and tgt and len(en) > 2 and len(tgt) > 2:
                                pairs.append((en, tgt))
                        return pairs
            except Exception:
                continue

    except Exception as e3:
        print(f"    OPUS direct failed: {e3}")

    return []


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("=" * 60)
    print("JW300 IMPORT")
    print("=" * 60)

    grand_total_sentences = 0
    grand_total_translations = 0

    for lang_code, lang_name in LANG_MAP.items():
        print(f"\n--- {lang_name.upper()} ({lang_code}) ---")

        pairs = download_jw300(lang_code)
        if not pairs:
            print(f"  No data found, skipping")
            continue

        print(f"  Downloaded {len(pairs)} pairs")

        # Filter: skip very long or very short
        pairs = [(en, tgt) for en, tgt in pairs
                 if 3 < len(en) < 300 and 3 < len(tgt) < 300]
        print(f"  After filtering: {len(pairs)} pairs")

        inserted_s = 0
        inserted_t = 0

        for en_text, tgt_text in pairs:
            tier = classify_tier(en_text)

            # Deduplicate by English text
            existing = conn.execute(
                "SELECT id FROM sentences WHERE english = ?", (en_text,)
            ).fetchone()

            if existing:
                sentence_id = existing[0]
            else:
                sentence_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO sentences (id, english, tier, domain, concept_id, source, difficulty)
                    VALUES (?, ?, ?, 'religion', 'jw300', 'community', 2)
                """, (sentence_id, en_text, tier))
                inserted_s += 1

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status)
                    VALUES (?, ?, ?, ?, 'community', 'verified')
                """, (str(uuid.uuid4()), sentence_id, lang_name, tgt_text))
                inserted_t += 1
            except Exception:
                pass

        conn.commit()
        print(f"  Inserted: {inserted_s} sentences, {inserted_t} translations")
        grand_total_sentences += inserted_s
        grand_total_translations += inserted_t

    # Summary
    print(f"\n{'=' * 60}")
    print(f"JW300 IMPORT COMPLETE")
    print(f"  New sentences: {grand_total_sentences}")
    print(f"  New translations: {grand_total_translations}")

    print(f"\nDATABASE TOTALS:")
    total_s = conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
    total_t = conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
    print(f"  Sentences: {total_s}")
    print(f"  Translations: {total_t}")

    print(f"\nBy source:")
    for r in conn.execute("SELECT source, COUNT(*) FROM sentences GROUP BY source ORDER BY COUNT(*) DESC"):
        print(f"  {r[0]:12s}: {r[1]}")

    print(f"\nTranslations by language:")
    for r in conn.execute("SELECT language, COUNT(*) FROM translations GROUP BY language ORDER BY language"):
        print(f"  {r[0]:10s}: {r[1]}")

    conn.close()
    print("\nDone! Run export_to_json.py to update the frontend.")


if __name__ == "__main__":
    main()
