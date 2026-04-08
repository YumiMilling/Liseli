"""Export SQLite database to JSON files for the frontend."""
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
OUT_DIR = BASE_DIR / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# Export sentences
rows = conn.execute("SELECT * FROM sentences ORDER BY created_at DESC").fetchall()
sentences = [dict(r) for r in rows]
(OUT_DIR / "sentences.json").write_text(json.dumps(sentences, indent=2), encoding="utf-8")
print(f"Exported {len(sentences)} sentences")

# Export translations with sentence data joined
rows = conn.execute("""
    SELECT t.*, s.english, s.tier, s.domain, s.concept_id, s.difficulty
    FROM translations t
    JOIN sentences s ON s.id = t.sentence_id
    ORDER BY t.language, t.created_at DESC
""").fetchall()
translations = [dict(r) for r in rows]
(OUT_DIR / "translations.json").write_text(json.dumps(translations, indent=2), encoding="utf-8")
print(f"Exported {len(translations)} translations")

# Export language coverage summary
rows = conn.execute("""
    SELECT
        t.language,
        (SELECT COUNT(*) FROM sentences) as total_sentences,
        COUNT(DISTINCT t.sentence_id) as translated,
        COUNT(DISTINCT t.sentence_id) as verified,
        ROUND(COUNT(DISTINCT t.sentence_id) * 100.0 / (SELECT COUNT(*) FROM sentences), 1) as percentage
    FROM translations t
    GROUP BY t.language
""").fetchall()
coverage = [dict(r) for r in rows]
(OUT_DIR / "coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
print(f"Exported coverage for {len(coverage)} languages")

# Export source materials catalog
rows = conn.execute("SELECT * FROM source_materials ORDER BY language, level, term").fetchall()
materials = [dict(r) for r in rows]
(OUT_DIR / "materials.json").write_text(json.dumps(materials, indent=2), encoding="utf-8")
print(f"Exported {len(materials)} source materials")

# Summary stats
stats = {
    "total_sentences": len(sentences),
    "total_translations": len(translations),
    "languages": len(coverage),
    "tiers": {r["tier"]: r["count"] for r in conn.execute("SELECT tier, COUNT(*) as count FROM sentences GROUP BY tier")},
    "sources": {r["source"]: r["count"] for r in conn.execute("SELECT source, COUNT(*) as count FROM sentences GROUP BY source")},
    "coverage": {r["language"]: {"translated": r["translated"], "percentage": r["percentage"]} for r in coverage},
}
(OUT_DIR / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
print(f"\nStats: {json.dumps(stats, indent=2)}")

conn.close()
print(f"\nAll exported to {OUT_DIR}")
