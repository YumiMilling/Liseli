"""
Migrate SQLite data to Supabase v2 schema.
Maps old flat structure to new normalized schema with proper provenance.
"""
import sqlite3
import time
import unicodedata
from supabase import create_client

SUPABASE_URL = "https://mjgnkjgkfgjsvlcwhwjc.supabase.co"
SUPABASE_KEY = open(".env.local").read().split("SUPABASE_SERVICE_ROLE_KEY=")[1].strip()

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
conn = sqlite3.connect("data/liseli_local.db")
conn.row_factory = sqlite3.Row

# ISO 639-3 mapping from old names
LANG_MAP = {
    "bemba": "bem", "nyanja": "nya", "tonga": "toi", "lozi": "loz",
    "kaonde": "kqn", "lunda": "lun", "luvale": "lue", "english": "eng",
}


def nfc(text):
    """Normalize text to NFC Unicode form."""
    return unicodedata.normalize("NFC", text) if text else text


def upload_batch(table, rows, batch_size=500, on_conflict="id"):
    """Upload rows in batches with error handling."""
    uploaded = 0
    errors = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            sb.table(table).upsert(batch, on_conflict=on_conflict).execute()
            uploaded += len(batch)
        except Exception as e:
            # Try one by one
            for row in batch:
                try:
                    sb.table(table).upsert([row], on_conflict=on_conflict).execute()
                    uploaded += 1
                except Exception:
                    errors += 1
        if uploaded % 5000 == 0 and uploaded > 0:
            print(f"    {table}: {uploaded:,} / {len(rows):,}")
        if i % 3000 == 0 and i > 0:
            time.sleep(0.3)
    return uploaded, errors


def create_sources():
    """Register all data sources."""
    print("\n1. Creating sources...")
    sources = [
        {"id": "bible-eng-web", "name": "World English Bible", "source_type": "bible",
         "publisher": "BibleNLP/ebible", "license": "public-domain",
         "url": "https://github.com/BibleNLP/ebible", "collection_method": "aligned",
         "languages": "eng", "notes": "31K verses, verse-aligned reference"},
        {"id": "bible-bem-ill15", "name": "Ishiwi Lyakwa Lesa 2015 (Bemba Bible)", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "url": "https://www.bible.com/versions/1097", "collection_method": "scraped",
         "languages": "bem", "notes": "Full Bible, 66 books"},
        {"id": "bible-nya-blp", "name": "Buku Lopatulika (Nyanja Bible)", "source_type": "bible",
         "publisher": "BibleNLP/ebible", "license": "varies",
         "url": "https://github.com/BibleNLP/ebible", "collection_method": "aligned",
         "languages": "nya", "notes": "Chichewa/Malawian dialect"},
        {"id": "bible-toi-96", "name": "Bbaibele 1996 (Tonga Bible)", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "url": "https://www.bible.com/languages/toi", "collection_method": "scraped",
         "languages": "toi"},
        {"id": "bible-loz-09", "name": "Bibele ye Kenile 2009 (Lozi Bible)", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "collection_method": "scraped", "languages": "loz"},
        {"id": "bible-kqn-nt", "name": "Kaonde New Testament", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "collection_method": "scraped", "languages": "kqn", "notes": "NT only"},
        {"id": "bible-lun-04", "name": "Lunda Bible 2004", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "collection_method": "scraped", "languages": "lun"},
        {"id": "bible-lue-70", "name": "Luvale Bible 1970", "source_type": "bible",
         "publisher": "Bible Society of Zambia", "license": "varies",
         "collection_method": "scraped", "languages": "lue"},
        {"id": "storybook-zambia", "name": "Storybooks Zambia", "source_type": "storybook",
         "publisher": "African Storybook / Saide", "license": "CC-BY",
         "url": "https://storybookszambia.net/", "collection_method": "scraped",
         "languages": "bem,nya,toi,loz,kqn,lun,lue,eng",
         "notes": "40 stories, all 7 languages + English, primary school level"},
        {"id": "moe-modules", "name": "MoE Teaching Modules 2025", "source_type": "textbook",
         "publisher": "Ministry of Education, Zambia", "license": "government",
         "url": "https://www.edu.gov.zm/?page_id=1142", "collection_method": "scraped",
         "languages": "bem,nya,toi,loz,kqn,lun,lue",
         "notes": "69 PDFs, Grade 1 / ECE / Form 1, monolingual"},
        {"id": "usaid-letsread", "name": "USAID Let's Read Zambia", "source_type": "textbook",
         "publisher": "Zambia Educational Publishing House", "license": "government",
         "collection_method": "scraped", "languages": "nya",
         "notes": "9 Grade 1-3 textbooks, Zambian Cinyanja"},
        {"id": "dmatekenya-mt", "name": "dmatekenya Chichewa MT", "source_type": "research",
         "license": "open", "url": "https://huggingface.co/datasets/dmatekenya",
         "collection_method": "manual", "languages": "nya,eng",
         "notes": "14K curated EN-NYA pairs with topic labels, Malawian Chichewa"},
        {"id": "flores-200", "name": "FLORES-200 Evaluation Set", "source_type": "research",
         "publisher": "Meta/Facebook", "license": "CC-BY-SA",
         "url": "https://huggingface.co/datasets/facebook/flores",
         "collection_method": "manual", "languages": "nya,eng",
         "notes": "2K gold-standard human-translated sentences"},
        {"id": "zambezivoice", "name": "ZambeziVoice Transcripts", "source_type": "research",
         "publisher": "UNZA Speech Lab", "license": "CC-BY-NC-ND",
         "url": "https://github.com/unza-speech-lab/zambezi-voice",
         "collection_method": "manual", "languages": "nya",
         "notes": "8.7K speech transcriptions, Zambian Nyanja"},
        {"id": "jw-cinyanja", "name": "JW.org Cinyanja", "source_type": "religious",
         "publisher": "Watch Tower Society", "license": "varies",
         "url": "https://www.jw.org/nya/", "collection_method": "scraped",
         "languages": "nya", "notes": "Zambian Cinyanja, distinct from Malawian /ny/"},
        {"id": "wikimedia", "name": "Wikimedia Interface Translations", "source_type": "community",
         "license": "CC-BY-SA", "collection_method": "aligned", "languages": "nya,eng"},
        {"id": "tatoeba", "name": "Tatoeba Sentence Pairs", "source_type": "community",
         "license": "CC-BY", "url": "https://tatoeba.org", "collection_method": "manual",
         "languages": "nya,toi,eng"},
        {"id": "masakhane-ner", "name": "MasakhaNER 2.0", "source_type": "research",
         "publisher": "Masakhane", "license": "open",
         "url": "https://huggingface.co/datasets/masakhane/masakhaner2",
         "collection_method": "manual", "languages": "nya",
         "notes": "8.9K NER-annotated Chichewa sentences"},
        {"id": "ai-dictionary", "name": "Statistical Dictionary", "source_type": "ai",
         "license": "CC-BY-SA", "collection_method": "statistical",
         "languages": "bem,nya,toi,loz,kqn,lun,lue,eng",
         "notes": "12K words extracted via co-occurrence analysis from parallel data"},
        {"id": "peace-corps", "name": "Peace Corps Nyanja Lessons", "source_type": "textbook",
         "publisher": "US Peace Corps", "license": "public-domain",
         "collection_method": "scraped", "languages": "nya"},
    ]
    upload_batch("sources", sources, on_conflict="id")
    print(f"  {len(sources)} sources registered")


def migrate_sentences_and_pairs():
    """Migrate sentences and create translation pairs."""
    print("\n2. Migrating sentences and translation pairs...")

    # Source mapping from old concept_id to new source_id
    def get_source_id(concept_id, source):
        if concept_id.startswith("bible-"):
            ref = concept_id.replace("bible-", "")
            lang_part = ref.split(" ")[0] if " " in ref else ""
            # Bible source depends on which language created it
            return "bible-eng-web"  # Will be refined per-language below
        if concept_id.startswith("storybook"):
            return "storybook-zambia"
        if concept_id.startswith("dict"):
            return "ai-dictionary"
        if concept_id.startswith("flores"):
            return "flores-200"
        if concept_id.startswith("dmatekenya"):
            return "dmatekenya-mt"
        if concept_id.startswith("tatoeba"):
            return "tatoeba"
        if concept_id.startswith("wikimedia"):
            return "wikimedia"
        if source == "moe":
            return "moe-modules"
        return None

    def get_bible_source(lang_code):
        return {
            "eng": "bible-eng-web", "bem": "bible-bem-ill15", "nya": "bible-nya-blp",
            "toi": "bible-toi-96", "loz": "bible-loz-09", "kqn": "bible-kqn-nt",
            "lun": "bible-lun-04", "lue": "bible-lue-70",
        }.get(lang_code, "bible-eng-web")

    # Step 1: Insert all English sentences
    print("  English sentences...")
    old_rows = conn.execute("""
        SELECT id, english, tier, domain, concept_id, source, difficulty
        FROM sentences WHERE length(english) > 2
    """).fetchall()

    # Map old_id -> new_id for linking
    old_to_new = {}
    eng_sentences = []
    for r in old_rows:
        src_id = get_source_id(r["concept_id"], r["source"])
        src_ref = r["concept_id"].replace("bible-", "").replace("storybook-", "story-") if r["concept_id"] else None
        eng_sentences.append({
            "text": nfc(r["english"]),
            "language_code": "eng",
            "source_id": src_id,
            "source_ref": src_ref,
            "tier": r["tier"],
            "domain": r["domain"],
            "quality": "validated",  # imported data is pre-validated
            "status": "active",
        })

    # Upload in batches, get back IDs
    # Supabase upsert returns the rows, but we need to match them
    # Use source_ref as the key since text can have duplicates across sources
    uploaded_eng = 0
    eng_text_to_id = {}
    for i in range(0, len(eng_sentences), 300):
        batch = eng_sentences[i:i + 300]
        try:
            result = sb.table("sentences").insert(batch).execute()
            for row in result.data:
                eng_text_to_id[(row["text"], row["source_id"])] = row["id"]
            uploaded_eng += len(result.data)
        except Exception as e:
            # Try one by one for conflicts
            for row in batch:
                try:
                    result = sb.table("sentences").insert([row]).execute()
                    if result.data:
                        eng_text_to_id[(result.data[0]["text"], result.data[0]["source_id"])] = result.data[0]["id"]
                    uploaded_eng += 1
                except Exception:
                    pass
        if uploaded_eng % 5000 == 0 and uploaded_eng > 0:
            print(f"    eng sentences: {uploaded_eng:,}")
        if i % 3000 == 0 and i > 0:
            time.sleep(0.3)

    print(f"  English sentences: {uploaded_eng:,}")

    # Step 2: Insert target language sentences and create pairs
    print("  Target language sentences + pairs...")
    old_trans = conn.execute("""
        SELECT t.sentence_id, t.language, t.text, t.status, t.dialect, t.story_id,
               s.english, s.concept_id, s.source, s.tier, s.domain
        FROM translations t
        JOIN sentences s ON s.id = t.sentence_id
        WHERE length(t.text) > 2
    """).fetchall()

    target_batch = []
    pair_batch = []
    count = 0

    for r in old_trans:
        lang_code = LANG_MAP.get(r["language"])
        if not lang_code:
            continue

        src_id_eng = get_source_id(r["concept_id"], r["source"])
        is_bible = r["concept_id"] and r["concept_id"].startswith("bible")
        src_id_tgt = get_bible_source(lang_code) if is_bible else src_id_eng
        src_ref = r["concept_id"].replace("bible-", "").replace("storybook-", "story-") if r["concept_id"] else None

        # Find the English sentence ID
        eng_id = eng_text_to_id.get((nfc(r["english"]), src_id_eng))
        if not eng_id:
            continue

        target_batch.append({
            "text": nfc(r["text"]),
            "language_code": lang_code,
            "source_id": src_id_tgt,
            "source_ref": src_ref,
            "tier": r["tier"],
            "domain": r["domain"],
            "dialect": r["dialect"],
            "quality": "validated" if r["status"] == "verified" else "unvalidated",
            "status": "active",
            "_eng_id": eng_id,  # temp field for pair creation
            "_confidence": 0.9 if is_bible else 0.7 if r["concept_id"] and r["concept_id"].startswith("storybook") else 0.5,
            "_method": "verse_aligned" if is_bible else "manual" if r["concept_id"] and r["concept_id"].startswith("storybook") else "statistical",
        })
        count += 1

    print(f"  Prepared {count:,} target sentences")

    # Upload target sentences and create pairs
    uploaded_tgt = 0
    uploaded_pairs = 0
    for i in range(0, len(target_batch), 200):
        batch = target_batch[i:i + 200]
        # Remove temp fields for insert
        insert_batch = [{k: v for k, v in row.items() if not k.startswith("_")} for row in batch]
        try:
            result = sb.table("sentences").insert(insert_batch).execute()
            # Create pairs
            pairs = []
            for j, row in enumerate(result.data):
                orig = batch[j]
                pairs.append({
                    "source_sentence_id": orig["_eng_id"],
                    "target_sentence_id": row["id"],
                    "confidence": orig["_confidence"],
                    "alignment_method": orig["_method"],
                    "validation_status": "validated" if orig.get("quality") == "validated" else "unvalidated",
                })
            if pairs:
                sb.table("translation_pairs").insert(pairs).execute()
                uploaded_pairs += len(pairs)
            uploaded_tgt += len(result.data)
        except Exception:
            # Try one by one
            for j, row in enumerate(batch):
                try:
                    insert_row = {k: v for k, v in row.items() if not k.startswith("_")}
                    result = sb.table("sentences").insert([insert_row]).execute()
                    if result.data:
                        pair = {
                            "source_sentence_id": row["_eng_id"],
                            "target_sentence_id": result.data[0]["id"],
                            "confidence": row["_confidence"],
                            "alignment_method": row["_method"],
                            "validation_status": "validated" if row.get("quality") == "validated" else "unvalidated",
                        }
                        sb.table("translation_pairs").insert([pair]).execute()
                        uploaded_pairs += 1
                    uploaded_tgt += 1
                except Exception:
                    pass

        if uploaded_tgt % 5000 == 0 and uploaded_tgt > 0:
            print(f"    target sentences: {uploaded_tgt:,}, pairs: {uploaded_pairs:,}")
        if i % 2000 == 0 and i > 0:
            time.sleep(0.3)

    print(f"  Target sentences: {uploaded_tgt:,}")
    print(f"  Translation pairs: {uploaded_pairs:,}")


def migrate_corpus():
    """Migrate monolingual corpus."""
    print("\n3. Migrating corpus...")

    source_map = {
        "moe": "moe-modules", "usaid": "usaid-letsread", "bible": None,  # skip, already in sentences
        "storybook": None,  # skip
        "zambezivoice": "zambezivoice", "jw.org": "jw-cinyanja",
        "dmatekenya": "dmatekenya-mt", "masakhane-ner": "masakhane-ner",
        "other-pdf": "peace-corps", "flores-200": "flores-200",
        "parallel": None,  # skip
    }

    rows = conn.execute("""
        SELECT language, text, source, source_file, domain, dialect, quality
        FROM corpus
        WHERE source NOT IN ('bible', 'storybook', 'parallel')
    """).fetchall()

    data = []
    for r in rows:
        lang_code = LANG_MAP.get(r["language"])
        if not lang_code:
            continue
        src_id = source_map.get(r["source"])
        if src_id is None:
            continue
        data.append({
            "text": nfc(r["text"]),
            "language_code": lang_code,
            "source_id": src_id,
            "source_file": r["source_file"],
            "domain": r["domain"] or "general",
            "dialect": r["dialect"],
            "quality": r["quality"] or "raw",
        })

    print(f"  Prepared {len(data):,} corpus lines")
    uploaded, errors = upload_batch("corpus", data, batch_size=300, on_conflict="language_code,text")
    print(f"  Uploaded: {uploaded:,} ({errors} errors)")


def main():
    print("=" * 60)
    print("LISELI v2 MIGRATION")
    print("=" * 60)

    print("\nLocal data:")
    for t in ["sentences", "translations", "corpus"]:
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {c:,}")

    create_sources()
    migrate_sentences_and_pairs()
    migrate_corpus()

    # Final verification
    print(f"\n{'=' * 60}")
    print("VERIFICATION")
    for t in ["languages", "sources", "sentences", "translation_pairs", "corpus"]:
        r = sb.table(t).select("*", count="exact").limit(0).execute()
        print(f"  {t:25s}: {r.count:,}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
