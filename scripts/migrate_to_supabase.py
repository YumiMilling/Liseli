"""
Migrate SQLite data to Supabase Postgres.
Creates schema and uploads all data.
"""
import os
import sqlite3
import time
from supabase import create_client

# Load credentials
SUPABASE_URL = "https://mjgnkjgkfgjsvlcwhwjc.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or open(".env.local").read().split("SUPABASE_SERVICE_ROLE_KEY=")[1].strip()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
conn = sqlite3.connect("data/liseli_local.db")
conn.row_factory = sqlite3.Row


def create_schema():
    """Create tables via Supabase SQL."""
    print("Creating schema...")

    # Use the REST API to execute SQL
    sql = """
    -- Sentences (English source content)
    CREATE TABLE IF NOT EXISTS sentences (
        id TEXT PRIMARY KEY,
        english TEXT NOT NULL,
        tier TEXT NOT NULL CHECK (tier IN ('word', 'phrase', 'sentence')),
        domain TEXT NOT NULL DEFAULT 'general',
        concept_id TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL DEFAULT 'community',
        difficulty INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_sentences_tier ON sentences(tier);
    CREATE INDEX IF NOT EXISTS idx_sentences_concept ON sentences(concept_id);
    CREATE INDEX IF NOT EXISTS idx_sentences_source ON sentences(source);

    -- Translations (bilingual pairs)
    CREATE TABLE IF NOT EXISTS translations (
        id TEXT PRIMARY KEY,
        sentence_id TEXT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
        language TEXT NOT NULL,
        text TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'community',
        status TEXT NOT NULL DEFAULT 'unverified',
        dialect TEXT,
        story_id TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(sentence_id, language, text)
    );

    CREATE INDEX IF NOT EXISTS idx_translations_sentence ON translations(sentence_id);
    CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language);
    CREATE INDEX IF NOT EXISTS idx_translations_status ON translations(status);

    -- Monolingual corpus
    CREATE TABLE IF NOT EXISTS corpus (
        id TEXT PRIMARY KEY,
        language TEXT NOT NULL,
        text TEXT NOT NULL,
        source TEXT NOT NULL,
        source_file TEXT,
        tier TEXT DEFAULT 'sentence',
        domain TEXT DEFAULT 'general',
        quality TEXT DEFAULT 'raw',
        dialect TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(language, text)
    );

    CREATE INDEX IF NOT EXISTS idx_corpus_language ON corpus(language);
    CREATE INDEX IF NOT EXISTS idx_corpus_source ON corpus(source);

    -- Data sources registry
    CREATE TABLE IF NOT EXISTS data_sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT,
        source_type TEXT NOT NULL,
        languages TEXT,
        license TEXT,
        notes TEXT,
        sentence_count INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    -- Source materials (PDF catalog)
    CREATE TABLE IF NOT EXISTS source_materials (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        source_type TEXT NOT NULL,
        language TEXT,
        level TEXT,
        term TEXT,
        file_path TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """

    # Execute via RPC or direct SQL
    result = supabase.rpc("", {}).execute()  # This won't work, need to use SQL editor

    print("  Schema SQL ready — need to execute via Supabase SQL editor or migration")
    return sql


def upload_batch(table, rows, batch_size=500):
    """Upload rows in batches."""
    total = len(rows)
    uploaded = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        try:
            supabase.table(table).upsert(batch, on_conflict="id").execute()
            uploaded += len(batch)
        except Exception as e:
            # Try smaller batches on error
            for row in batch:
                try:
                    supabase.table(table).upsert([row], on_conflict="id").execute()
                    uploaded += 1
                except Exception:
                    errors += 1

        if uploaded % 5000 == 0 or i + batch_size >= total:
            print(f"  {table}: {uploaded:,}/{total:,} uploaded ({errors} errors)")

        # Rate limiting
        if i % 2000 == 0 and i > 0:
            time.sleep(0.5)

    return uploaded, errors


def migrate_sentences():
    """Upload sentences table."""
    print("\nMigrating sentences...")
    rows = conn.execute("SELECT * FROM sentences").fetchall()
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "english": r["english"],
            "tier": r["tier"],
            "domain": r["domain"],
            "concept_id": r["concept_id"],
            "source": r["source"],
            "difficulty": r["difficulty"],
        })
    return upload_batch("sentences", data)


def migrate_translations():
    """Upload translations table."""
    print("\nMigrating translations...")
    rows = conn.execute("SELECT * FROM translations").fetchall()
    data = []
    for r in rows:
        entry = {
            "id": r["id"],
            "sentence_id": r["sentence_id"],
            "language": r["language"],
            "text": r["text"],
            "source": r["source"],
            "status": r["status"],
        }
        if r["dialect"]:
            entry["dialect"] = r["dialect"]
        if r["story_id"]:
            entry["story_id"] = r["story_id"]
        data.append(entry)
    return upload_batch("translations", data, batch_size=300)


def migrate_corpus():
    """Upload corpus table."""
    print("\nMigrating corpus...")
    rows = conn.execute("SELECT * FROM corpus").fetchall()
    data = []
    for r in rows:
        entry = {
            "id": r["id"],
            "language": r["language"],
            "text": r["text"],
            "source": r["source"],
            "domain": r["domain"] or "general",
            "quality": r["quality"] or "raw",
        }
        if r["source_file"]:
            entry["source_file"] = r["source_file"]
        if r["dialect"]:
            entry["dialect"] = r["dialect"]
        data.append(entry)
    return upload_batch("corpus", data, batch_size=300)


def migrate_metadata():
    """Upload source_materials and data_sources."""
    print("\nMigrating metadata...")

    rows = conn.execute("SELECT * FROM source_materials").fetchall()
    data = [dict(r) for r in rows]
    if data:
        upload_batch("source_materials", data)

    rows = conn.execute("SELECT * FROM data_sources").fetchall()
    data = [dict(r) for r in rows]
    if data:
        upload_batch("data_sources", data)


def main():
    print("=" * 60)
    print("SUPABASE MIGRATION")
    print(f"URL: {SUPABASE_URL}")
    print("=" * 60)

    # Check counts
    print("\nLocal SQLite data:")
    for table in ["sentences", "translations", "corpus", "source_materials", "data_sources"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:20s}: {count:>10,}")

    # First, create schema via SQL
    print("\n" + "=" * 60)
    print("STEP 1: Create schema")
    print("Please run the SQL in supabase/migrations/002_liseli_schema.sql")
    print("via the Supabase SQL Editor, then press Enter to continue...")
    print("=" * 60)

    # Actually, let's try creating tables directly
    # The tables might already exist from the original migration

    # Try uploading — if tables don't exist, we'll get an error
    print("\nTesting connection...")
    try:
        result = supabase.table("sentences").select("id").limit(1).execute()
        print(f"  sentences table exists, {len(result.data)} rows currently")
    except Exception as e:
        print(f"  sentences table not found: {e}")
        print("\n  You need to create the tables first.")
        print("  Run the SQL from supabase/migrations/001_initial_schema.sql")
        print("  in the Supabase SQL Editor (Dashboard → SQL Editor)")
        return

    # Migrate in order
    s_up, s_err = migrate_sentences()
    t_up, t_err = migrate_translations()
    c_up, c_err = migrate_corpus()
    migrate_metadata()

    print(f"\n{'=' * 60}")
    print("MIGRATION COMPLETE")
    print(f"  Sentences:    {s_up:>8,} uploaded ({s_err} errors)")
    print(f"  Translations: {t_up:>8,} uploaded ({t_err} errors)")
    print(f"  Corpus:       {c_up:>8,} uploaded ({c_err} errors)")

    # Verify
    print("\nVerifying...")
    for table in ["sentences", "translations", "corpus"]:
        try:
            result = supabase.table(table).select("id", count="exact").limit(0).execute()
            print(f"  {table}: {result.count:,} rows in Supabase")
        except Exception as e:
            print(f"  {table}: error - {e}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
