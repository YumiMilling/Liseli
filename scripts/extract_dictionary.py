"""
Extract word-level dictionary from parallel sentence pairs.
Uses co-occurrence analysis: if an English word appears in sentences
where a target word also consistently appears, they're likely translations.
"""

import sqlite3
import json
import uuid
import re
from collections import defaultdict, Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"

# Common English stop words to skip
STOP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'and', 'but', 'or', 'if', 'while', 'because', 'until', 'although',
    'that', 'this', 'these', 'those', 'i', 'me', 'my', 'myself', 'we',
    'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
    'they', 'them', 'their', 'what', 'which', 'who', 'whom', 'up', 'down',
    'about', 'also', 'am', 'it\'s', 'don\'t', 'didn\'t', 'doesn\'t',
}


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens."""
    return [w.lower() for w in re.findall(r"[a-zA-Z\u00C0-\u024F']+", text) if len(w) > 1]


def extract_dictionary(conn: sqlite3.Connection, language: str) -> list[dict]:
    """
    Extract word translations using co-occurrence statistics.

    For each English content word, find which target-language words
    most consistently co-occur with it across all sentence pairs.
    """
    # Get all parallel pairs for this language
    pairs = conn.execute("""
        SELECT s.english, t.text
        FROM sentences s
        JOIN translations t ON t.sentence_id = s.id
        WHERE t.language = ?
    """, (language,)).fetchall()

    if not pairs:
        return []

    # Build co-occurrence matrix
    # For each English word, count how often each target word appears in the same pair
    en_word_count = Counter()  # how many sentences contain this English word
    cooccurrence = defaultdict(Counter)  # en_word -> {target_word: count}
    target_word_count = Counter()  # how many sentences contain this target word

    for en_text, tgt_text in pairs:
        en_words = set(tokenize(en_text)) - STOP_WORDS
        tgt_words = set(tokenize(tgt_text))

        for ew in en_words:
            en_word_count[ew] += 1
            for tw in tgt_words:
                cooccurrence[ew][tw] += 1

        for tw in tgt_words:
            target_word_count[tw] += 1

    # Score each (en_word, target_word) pair
    # Use PMI-like score: how much more likely they co-occur than by chance
    total_pairs = len(pairs)
    dictionary = []

    for en_word, tgt_counts in cooccurrence.items():
        if en_word_count[en_word] < 2:
            continue  # need at least 2 occurrences for confidence

        best_score = 0
        best_target = None
        best_count = 0

        for tgt_word, count in tgt_counts.items():
            if len(tgt_word) < 2:
                continue

            # P(co-occur) / (P(en) * P(tgt))
            p_co = count / total_pairs
            p_en = en_word_count[en_word] / total_pairs
            p_tgt = target_word_count[tgt_word] / total_pairs

            if p_en * p_tgt > 0:
                pmi = p_co / (p_en * p_tgt)
            else:
                pmi = 0

            # Also factor in raw co-occurrence ratio
            ratio = count / en_word_count[en_word]

            # Combined score: PMI * ratio * minimum count filter
            score = pmi * ratio
            if count >= 2 and score > best_score:
                best_score = score
                best_target = tgt_word
                best_count = count

        if best_target and best_score > 0.8:
            confidence = min(best_count / en_word_count[en_word], 1.0)
            dictionary.append({
                "english": en_word,
                "translation": best_target,
                "occurrences": en_word_count[en_word],
                "co_occurrences": best_count,
                "confidence": round(confidence, 2),
                "score": round(best_score, 2),
            })

    # Sort by confidence then occurrences
    dictionary.sort(key=lambda x: (-x["confidence"], -x["occurrences"]))
    return dictionary


def extract_short_phrase_words(conn: sqlite3.Connection, language: str) -> list[dict]:
    """
    Extract words from very short parallel pairs where mapping is obvious.
    e.g., "Fire burns." -> "Umulilo ulooca." => fire=umulilo, burns=ulooca
    """
    pairs = conn.execute("""
        SELECT s.english, t.text
        FROM sentences s
        JOIN translations t ON t.sentence_id = s.id
        WHERE t.language = ? AND length(s.english) < 25
        ORDER BY length(s.english)
    """, (language,)).fetchall()

    words = []
    for en_text, tgt_text in pairs:
        en_tokens = [w for w in tokenize(en_text) if w not in STOP_WORDS]
        tgt_tokens = tokenize(tgt_text)

        # Only extract from 1-to-1 or 2-to-2 mappings
        if len(en_tokens) == 1 and len(tgt_tokens) == 1:
            words.append({
                "english": en_tokens[0],
                "translation": tgt_tokens[0],
                "source": f"{en_text} -> {tgt_text}",
                "confidence": 0.9,
                "method": "direct_1to1",
            })
        elif len(en_tokens) == 2 and len(tgt_tokens) == 2:
            # Assume same order
            for i in range(2):
                words.append({
                    "english": en_tokens[i],
                    "translation": tgt_tokens[i],
                    "source": f"{en_text} -> {tgt_text}",
                    "confidence": 0.7,
                    "method": "positional_2to2",
                })

    return words


def main():
    conn = sqlite3.connect(str(DB_PATH))

    languages = ["bemba", "nyanja", "tonga", "lozi", "kaonde", "lunda", "luvale"]
    all_words = []

    print("=" * 60)
    print("LISELI DICTIONARY EXTRACTION")
    print("=" * 60)

    for lang in languages:
        print(f"\n--- {lang.upper()} ---")

        # Method 1: Short phrase extraction
        short_words = extract_short_phrase_words(conn, lang)
        print(f"  Short phrase words: {len(short_words)}")

        # Method 2: Statistical co-occurrence
        stats_words = extract_dictionary(conn, lang)
        print(f"  Statistical words: {len(stats_words)}")

        # Merge: prefer short-phrase extractions, supplement with statistical
        seen = set()
        merged = []

        for w in short_words:
            key = w["english"]
            if key not in seen:
                seen.add(key)
                merged.append(w)

        for w in stats_words:
            key = w["english"]
            if key not in seen and w["confidence"] >= 0.5:
                seen.add(key)
                merged.append(w)

        print(f"  Merged unique: {len(merged)}")

        # Show top entries
        for w in merged[:10]:
            print(f"    {w['english']:20s} -> {w['translation']:20s} (conf: {w['confidence']})")

        # Insert into database
        for w in merged:
            en_text = w["english"]

            # Check if sentence exists
            existing = conn.execute(
                "SELECT id FROM sentences WHERE english = ? AND tier = 'word'",
                (en_text,)
            ).fetchone()

            if existing:
                sentence_id = existing[0]
            else:
                sentence_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO sentences (id, english, tier, domain, concept_id, source, difficulty)
                    VALUES (?, ?, 'word', 'education', ?, 'community', 1)
                """, (sentence_id, en_text, f"dict-{lang}"))

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status)
                    VALUES (?, ?, ?, ?, 'community', 'unverified')
                """, (str(uuid.uuid4()), sentence_id, lang, w["translation"]))
            except Exception:
                pass

        all_words.extend([{**w, "language": lang} for w in merged])

    conn.commit()

    # Print summary
    total_words = conn.execute("SELECT COUNT(*) FROM sentences WHERE tier = 'word'").fetchone()[0]
    total_trans = conn.execute("""
        SELECT COUNT(*) FROM translations t
        JOIN sentences s ON s.id = t.sentence_id
        WHERE s.tier = 'word'
    """).fetchone()[0]

    print(f"\n{'=' * 60}")
    print(f"DICTIONARY SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total unique words: {total_words}")
    print(f"Total word translations: {total_trans}")

    print(f"\nPer language:")
    for row in conn.execute("""
        SELECT t.language, COUNT(*)
        FROM translations t JOIN sentences s ON s.id = t.sentence_id
        WHERE s.tier = 'word'
        GROUP BY t.language ORDER BY t.language
    """):
        print(f"  {row[0]}: {row[1]} words")

    conn.close()
    print("\nDone! Run export_to_json.py to update the frontend.")


if __name__ == "__main__":
    main()
