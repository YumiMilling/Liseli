"""Import quality Nyanja sources into the database."""
import sqlite3, uuid, csv
from pathlib import Path

conn = sqlite3.connect("data/liseli_local.db")
conn.execute("PRAGMA journal_mode=WAL")
SRC = Path("data/nyanja-sources")

def tier(text):
    w = len(text.split())
    return "word" if w <= 2 else "phrase" if w <= 6 else "sentence"

total_p = total_c = 0

# 1. FLORES-200
print("1. FLORES-200...")
ins = 0
for split_en, split_ny in [
    ("flores200_dataset/dev/eng_Latn.dev", "flores200_dataset/dev/nya_Latn.dev"),
    ("flores200_dataset/devtest/eng_Latn.devtest", "flores200_dataset/devtest/nya_Latn.devtest"),
]:
    en_f = SRC / split_en
    ny_f = SRC / split_ny
    if not en_f.exists() or not ny_f.exists():
        continue
    en_lines = en_f.read_text(encoding="utf-8").strip().split("\n")
    ny_lines = ny_f.read_text(encoding="utf-8").strip().split("\n")
    for en, ny in zip(en_lines, ny_lines):
        en, ny = en.strip(), ny.strip()
        if not en or not ny or len(en) < 5:
            continue
        sid = str(uuid.uuid4())
        conn.execute(
            "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, en, tier(en), "general", "flores-200", "community", 3),
        )
        conn.execute(
            "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), sid, "nyanja", ny, "community", "verified", "chichewa-mw"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "nyanja", ny, "flores-200", "general", "verified", "chichewa-mw"),
        )
        ins += 1
conn.commit()
print(f"  {ins} FLORES pairs")
total_p += ins

# 2. ZambeziVoice
print("2. ZambeziVoice...")
ins = 0
try:
    import pandas as pd
    df = pd.read_parquet(str(SRC / "zambezivoice-nya-text.parquet"))
    for _, row in df.iterrows():
        text = str(row.iloc[0]).strip()
        if len(text) < 5:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "nyanja", text, "zambezivoice", "general", "reviewed", "nyanja-zm"),
        )
        ins += 1
    conn.commit()
    print(f"  {ins} ZambeziVoice utterances (Zambian Nyanja!)")
    total_c += ins
except Exception as e:
    print(f"  SKIP ZambeziVoice: {e}")

# 3. dmatekenya MT
print("3. dmatekenya...")
csv_path = SRC / "chichewa-machine-translation.csv"
ins = 0
if csv_path.exists():
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        for row in reader:
            en = (row.get("english") or row.get("English") or "").strip()
            ny = (row.get("chichewa") or row.get("Chichewa") or row.get("nyanja") or "").strip()
            if not en or not ny or len(en) < 5 or len(ny) < 5:
                continue
            if len(en) > 300:
                continue
            sid = str(uuid.uuid4())
            conn.execute(
                "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, en, tier(en), "general", "dmatekenya", "community", 2),
            )
            conn.execute(
                "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), sid, "nyanja", ny, "community", "verified", "chichewa-mw"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "nyanja", ny, "dmatekenya", "general", "reviewed", "chichewa-mw"),
            )
            ins += 1
    conn.commit()
    print(f"  {ins} dmatekenya pairs")
    total_p += ins

# 4. MasakhaNER2
print("4. MasakhaNER2...")
ner_dir = SRC / "masakhane-ner2"
ins = 0
if ner_dir.exists():
    for split in ["train.txt", "dev.txt", "test.txt"]:
        fp = ner_dir / split
        if not fp.exists():
            continue
        current = []
        for line in fp.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if not line:
                if current:
                    text = " ".join(current)
                    if len(text) > 5:
                        conn.execute(
                            "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (str(uuid.uuid4()), "nyanja", text, "masakhane-ner", "general", "verified", "chichewa-mw"),
                        )
                        ins += 1
                    current = []
            else:
                parts = line.split()
                if parts:
                    current.append(parts[0])
    conn.commit()
    print(f"  {ins} NER sentences")
    total_c += ins

# 5. Tatoeba
print("5. Tatoeba...")
t_en = SRC / "tatoeba-en-ny" / "Tatoeba.en-ny.en"
t_ny = SRC / "tatoeba-en-ny" / "Tatoeba.en-ny.ny"
ins = 0
if t_en.exists() and t_ny.exists():
    for en, ny in zip(
        t_en.read_text(encoding="utf-8").strip().split("\n"),
        t_ny.read_text(encoding="utf-8").strip().split("\n"),
    ):
        en, ny = en.strip(), ny.strip()
        if not en or not ny:
            continue
        sid = str(uuid.uuid4())
        conn.execute(
            "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, en, tier(en), "general", "tatoeba", "community"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), sid, "nyanja", ny, "community", "verified"),
        )
        ins += 1
    conn.commit()
    print(f"  {ins} Tatoeba pairs")
    total_p += ins

# 6. Wikimedia
print("6. Wikimedia...")
w_en = SRC / "wikimedia-en-ny" / "wikimedia.en-ny.en"
w_ny = SRC / "wikimedia-en-ny" / "wikimedia.en-ny.ny"
ins = 0
if w_en.exists() and w_ny.exists():
    for en, ny in zip(
        w_en.read_text(encoding="utf-8").strip().split("\n"),
        w_ny.read_text(encoding="utf-8").strip().split("\n"),
    ):
        en, ny = en.strip(), ny.strip()
        if not en or not ny or len(en) < 3:
            continue
        sid = str(uuid.uuid4())
        conn.execute(
            "INSERT OR IGNORE INTO sentences (id, english, tier, domain, concept_id, source) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, en, tier(en), "general", "wikimedia", "community"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), sid, "nyanja", ny, "community", "verified"),
        )
        ins += 1
    conn.commit()
    print(f"  {ins} Wikimedia pairs")
    total_p += ins

# Summary
print()
print("=" * 60)
print(f"New parallel pairs:  {total_p:,}")
print(f"New corpus entries:  {total_c:,}")
print()
print("FULL DATABASE:")
print(f"  sentences:    {conn.execute('SELECT COUNT(*) FROM sentences').fetchone()[0]:>8,}")
print(f"  translations: {conn.execute('SELECT COUNT(*) FROM translations').fetchone()[0]:>8,}")
print(f"  corpus:       {conn.execute('SELECT COUNT(*) FROM corpus').fetchone()[0]:>8,}")
print()
print("Nyanja by dialect:")
for r in conn.execute(
    "SELECT dialect, COUNT(*) FROM translations WHERE language='nyanja' GROUP BY dialect ORDER BY COUNT(*) DESC"
):
    print(f"  {r[0] or 'untagged':15s}: {r[1]:>8,}")
print()
print("Corpus by source (nyanja only):")
for r in conn.execute(
    "SELECT source, dialect, COUNT(*) FROM corpus WHERE language='nyanja' GROUP BY source, dialect ORDER BY COUNT(*) DESC"
):
    print(f"  {r[0]:20s} {r[1] or 'untagged':15s}: {r[2]:>8,}")

conn.close()
print("\nDone!")
