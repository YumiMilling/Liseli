"""
Upload pre-deduplicated clean data to Supabase v2.
All data is pre-cleaned — no conflict handling needed, pure bulk inserts.
"""
import json
import time
import unicodedata
from supabase import create_client

SUPABASE_URL = "https://mjgnkjgkfgjsvlcwhwjc.supabase.co"
SUPABASE_KEY = open(".env.local").read().split("SUPABASE_SERVICE_ROLE_KEY=")[1].strip()
sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload(table, rows, batch_size=500):
    uploaded = errors = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            sb.table(table).insert(batch).execute()
            uploaded += len(batch)
        except Exception:
            for row in batch:
                try:
                    sb.table(table).insert([row]).execute()
                    uploaded += 1
                except Exception:
                    errors += 1
        if uploaded % 10000 == 0 and uploaded > 0:
            print(f"  {table}: {uploaded:,} / {len(rows):,}")
        if i % 5000 == 0 and i > 0:
            time.sleep(0.2)
    print(f"  {table}: {uploaded:,} uploaded ({errors} errors)")
    return uploaded


def main():
    print("=" * 60)
    print("CLEAN UPLOAD TO SUPABASE")
    print("=" * 60)

    # 1. English sentences
    print("\n1. English sentences...")
    eng = json.loads(open("data/migration/eng_sentences.json", encoding="utf-8").read())
    upload("sentences", eng)

    # Build text+source -> id lookup
    print("  Building ID lookup...")
    eng_ids = {}
    offset = 0
    while True:
        r = sb.table("sentences").select("id, text, source_id").eq("language_code", "eng").range(offset, offset + 999).execute()
        if not r.data:
            break
        for row in r.data:
            eng_ids[(row["text"], row["source_id"])] = row["id"]
        offset += 1000
        if offset % 10000 == 0:
            print(f"    Loaded {offset:,} IDs...")
    print(f"  {len(eng_ids):,} English IDs loaded")

    # 2. Target sentences + pairs
    print("\n2. Target sentences + translation pairs...")
    pairs = json.loads(open("data/migration/pairs.json", encoding="utf-8").read())

    tgt_batch = []
    pair_meta = []  # store pair info to create after target insert

    for p in pairs:
        eng_id = eng_ids.get((p["eng_text"], p["eng_src"]))
        if not eng_id:
            continue

        tgt_batch.append({
            "text": p["tgt_text"],
            "language_code": p["tgt_lang"],
            "source_id": p["tgt_src"],
            "source_ref": p.get("src_ref"),
            "tier": p["tier"],
            "domain": p["domain"],
            "dialect": p.get("dialect"),
            "quality": p["quality"],
            "status": "active",
        })
        pair_meta.append({
            "eng_id": eng_id,
            "confidence": p["confidence"],
            "method": p["method"],
            "validation_status": p["quality"],
        })

    print(f"  {len(tgt_batch):,} target sentences to upload")

    # Upload target sentences in batches and create pairs immediately
    tgt_uploaded = pair_uploaded = 0
    batch_size = 200

    for i in range(0, len(tgt_batch), batch_size):
        t_batch = tgt_batch[i:i + batch_size]
        p_batch = pair_meta[i:i + batch_size]

        try:
            result = sb.table("sentences").insert(t_batch).execute()
            # Create pairs
            pair_rows = []
            for j, row in enumerate(result.data):
                pair_rows.append({
                    "source_sentence_id": p_batch[j]["eng_id"],
                    "target_sentence_id": row["id"],
                    "confidence": p_batch[j]["confidence"],
                    "alignment_method": p_batch[j]["method"],
                    "validation_status": p_batch[j]["validation_status"],
                })
            if pair_rows:
                sb.table("translation_pairs").insert(pair_rows).execute()
                pair_uploaded += len(pair_rows)
            tgt_uploaded += len(result.data)
        except Exception:
            # One by one fallback
            for j, row in enumerate(t_batch):
                try:
                    result = sb.table("sentences").insert([row]).execute()
                    if result.data:
                        pair_row = {
                            "source_sentence_id": p_batch[j]["eng_id"],
                            "target_sentence_id": result.data[0]["id"],
                            "confidence": p_batch[j]["confidence"],
                            "alignment_method": p_batch[j]["method"],
                            "validation_status": p_batch[j]["validation_status"],
                        }
                        sb.table("translation_pairs").insert([pair_row]).execute()
                        pair_uploaded += 1
                    tgt_uploaded += 1
                except Exception:
                    pass

        if tgt_uploaded % 10000 == 0 and tgt_uploaded > 0:
            print(f"  targets: {tgt_uploaded:,}, pairs: {pair_uploaded:,}")
        if i % 5000 == 0 and i > 0:
            time.sleep(0.2)

    print(f"  Target sentences: {tgt_uploaded:,}")
    print(f"  Translation pairs: {pair_uploaded:,}")

    # 3. Corpus
    print("\n3. Corpus...")
    corpus = json.loads(open("data/migration/corpus.json", encoding="utf-8").read())
    upload("corpus", corpus, batch_size=300)

    # Verify
    print(f"\n{'=' * 60}")
    print("DONE — VERIFICATION")
    for t in ["languages", "sources", "sentences", "translation_pairs", "corpus"]:
        r = sb.table(t).select("*", count="exact").limit(0).execute()
        print(f"  {t:25s}: {r.count:,}")


if __name__ == "__main__":
    main()
