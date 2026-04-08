"""
Build cross-language translation pairs from aligned parallel sentences.
Since all 7 languages translate the same English sentences, we can derive
direct translations between any two Zambian languages.

Also generates conjugation-style pattern sentences from short verb phrases.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from itertools import combinations

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
OUT_DIR = BASE_DIR / "public" / "data"

LANGUAGES = ["bemba", "nyanja", "tonga", "lozi", "kaonde", "lunda", "luvale"]


def build_cross_language_pairs(conn: sqlite3.Connection):
    """
    For each sentence that has translations in multiple Zambian languages,
    create pairs between every combination of languages.
    """
    print("Building cross-language pairs...")

    # Get sentences with translations in all 7 languages
    sentences = conn.execute("""
        SELECT s.id, s.english, s.tier
        FROM sentences s
        WHERE (SELECT COUNT(DISTINCT t.language) FROM translations t WHERE t.sentence_id = s.id) >= 2
        AND s.tier IN ('phrase', 'sentence', 'word')
        AND s.concept_id LIKE 'storybook-%'
    """).fetchall()

    print(f"  Found {len(sentences)} aligned sentences")

    cross_pairs = []
    for sid, english, tier in sentences:
        # Get all translations for this sentence
        trans = {}
        for row in conn.execute(
            "SELECT language, text FROM translations WHERE sentence_id = ?", (sid,)
        ):
            trans[row[0]] = row[1]

        # Generate all language pairs
        for lang_a, lang_b in combinations(LANGUAGES, 2):
            if lang_a in trans and lang_b in trans:
                cross_pairs.append({
                    "english": english,
                    "tier": tier,
                    "lang_a": lang_a,
                    "text_a": trans[lang_a],
                    "lang_b": lang_b,
                    "text_b": trans[lang_b],
                })

    print(f"  Generated {len(cross_pairs)} cross-language pairs")

    # Save as JSON
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "cross_language.json").write_text(
        json.dumps(cross_pairs, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Summary by language pair
    pair_counts = {}
    for p in cross_pairs:
        key = f"{p['lang_a']}-{p['lang_b']}"
        pair_counts[key] = pair_counts.get(key, 0) + 1

    print(f"\n  Language pair counts:")
    for pair, count in sorted(pair_counts.items()):
        print(f"    {pair}: {count}")

    return cross_pairs


def build_verb_patterns(conn: sqlite3.Connection):
    """
    Extract verb-like patterns from short parallel phrases.
    Group by English verb stem to show conjugation patterns across languages.
    e.g., "I am singing" / "She is waving" / "He is calling" -> verb pattern group
    """
    print("\nBuilding verb pattern groups...")

    # Get short English sentences that look like verb patterns
    patterns = conn.execute("""
        SELECT s.id, s.english
        FROM sentences s
        WHERE s.tier IN ('phrase', 'sentence')
        AND length(s.english) < 40
        AND (s.english LIKE 'I %' OR s.english LIKE 'He %' OR s.english LIKE 'She %'
             OR s.english LIKE 'It %' OR s.english LIKE 'We %' OR s.english LIKE 'They %'
             OR s.english LIKE 'You %')
        AND s.concept_id LIKE 'storybook-%'
        ORDER BY s.english
    """).fetchall()

    print(f"  Found {len(patterns)} verb pattern sentences")

    verb_groups = []
    for sid, english in patterns:
        trans = {}
        for row in conn.execute(
            "SELECT language, text FROM translations WHERE sentence_id = ?", (sid,)
        ):
            trans[row[0]] = row[1]

        if len(trans) >= 5:  # Need most languages
            verb_groups.append({
                "english": english,
                "translations": trans,
            })

    # Save
    (OUT_DIR / "verb_patterns.json").write_text(
        json.dumps(verb_groups, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"  Saved {len(verb_groups)} verb patterns")

    # Show some examples
    for vg in verb_groups[:5]:
        print(f"\n  EN: {vg['english']}")
        for lang in LANGUAGES:
            if lang in vg['translations']:
                print(f"    {lang:8s}: {vg['translations'][lang]}")

    return verb_groups


def main():
    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print("LISELI CROSS-LANGUAGE & VERB PATTERNS")
    print("=" * 60)

    cross_pairs = build_cross_language_pairs(conn)
    verb_patterns = build_verb_patterns(conn)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Cross-language pairs: {len(cross_pairs)}")
    print(f"Verb pattern groups:  {len(verb_patterns)}")
    print(f"\nFiles written to {OUT_DIR}:")
    print(f"  cross_language.json")
    print(f"  verb_patterns.json")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
