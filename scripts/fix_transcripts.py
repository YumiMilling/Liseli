"""
Fix Whisper transcripts using Liseli's existing language data.
Cross-references against dictionary, corpus, and grammar patterns
to correct spelling errors in ASR output.
"""
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

DB_PATH = Path("data/liseli_local.db")
TRANSCRIPTS_DIR = Path("data/whisper-transcripts")

LANG_MAP_REVERSE = {
    "bem": "bemba", "nya": "nyanja", "toi": "tonga", "loz": "lozi",
    "kqn": "kaonde", "lun": "lunda", "lue": "luvale",
}


def normalize(text):
    """Lowercase, strip diacritics, normalize unicode."""
    text = unicodedata.normalize("NFC", text.lower().strip())
    return text


def build_word_index(conn, lang_iso):
    """Build a lookup of known correct words for a language."""
    lang_name = LANG_MAP_REVERSE.get(lang_iso, lang_iso)

    words = set()

    # From translations (parallel data — high quality)
    for r in conn.execute(
        "SELECT text FROM translations WHERE language = ?", (lang_name,)
    ):
        for w in re.findall(r"[a-zA-Z\u00C0-\u024F\u02B0-\u02FF']+", r[0]):
            if len(w) >= 2:
                words.add(w.lower())

    # From corpus (monolingual — broader coverage)
    for r in conn.execute(
        "SELECT text FROM corpus WHERE language = ?", (lang_name,)
    ):
        for w in re.findall(r"[a-zA-Z\u00C0-\u024F\u02B0-\u02FF']+", r[0]):
            if len(w) >= 2:
                words.add(w.lower())

    return words


def levenshtein(s1, s2):
    """Compute edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def find_closest(word, known_words, max_distance=2):
    """Find the closest known word by edit distance."""
    word_lower = word.lower()
    if word_lower in known_words:
        return word, 0  # exact match

    best = None
    best_dist = max_distance + 1

    # Only check words of similar length (optimization)
    for known in known_words:
        if abs(len(known) - len(word_lower)) > max_distance:
            continue
        dist = levenshtein(word_lower, known)
        if dist < best_dist:
            best_dist = dist
            best = known

    if best and best_dist <= max_distance:
        # Preserve original capitalization pattern
        if word[0].isupper():
            best = best[0].upper() + best[1:]
        return best, best_dist

    return None, None


def fix_segment(text, known_words, common_english):
    """Fix a transcription segment using known words."""
    words = text.split()
    fixed_words = []
    changes = []

    for word in words:
        # Strip punctuation for matching
        clean = re.sub(r"[.,!?;:'\"-]", "", word)
        punct_after = word[len(clean):] if len(clean) < len(word) else ""

        if len(clean) < 2:
            fixed_words.append(word)
            continue

        # Skip if it's a common English word (likely correct)
        if clean.lower() in common_english:
            fixed_words.append(word)
            continue

        # Check if it's already a known target language word
        if clean.lower() in known_words:
            fixed_words.append(word)
            continue

        # Try to find closest match in target language
        closest, dist = find_closest(clean, known_words)
        if closest and dist > 0:
            fixed_words.append(closest + punct_after)
            changes.append({"original": clean, "fixed": closest, "distance": dist})
        else:
            fixed_words.append(word)

    return " ".join(fixed_words), changes


def main():
    print("=" * 60)
    print("TRANSCRIPT FIXER")
    print("=" * 60)

    # Load transcripts
    transcript_file = TRANSCRIPTS_DIR / "all_transcripts.json"
    if not transcript_file.exists():
        print("No transcripts found. Run whisper_transcribe.py first.")
        return

    transcripts = json.loads(transcript_file.read_text(encoding="utf-8"))
    conn = sqlite3.connect(str(DB_PATH))

    # Common English words (don't try to "fix" these)
    common_english = set(
        "the a an is are was were be been being have has had do does did will would "
        "could should may might shall can need to of in for on with at by from as into "
        "through during before after above below between out off over under again further "
        "then once here there when where why how all both each few more most other some "
        "such no nor not only own same so than too very just and but or if while because "
        "until although that this these those i me my we our you your he him his she her "
        "it its they them their what which who whom the say says said like know go come "
        "take make see want give use find tell think look well good also back even still "
        "way many work now day time world people been right get going been thing about "
        "called hello hi thank thanks okay yes please welcome everybody everyone "
        "subscribe share comment below".split()
    )

    total_fixes = 0
    fixed_transcripts = {}

    for lang_code, videos in transcripts.items():
        print(f"\n{'=' * 40}")
        print(f"  {lang_code.upper()}")
        print(f"{'=' * 40}")

        # Build word index for this language
        known_words = build_word_index(conn, lang_code)
        print(f"  Known words: {len(known_words):,}")

        lang_fixed = []
        lang_fixes = 0

        for video in videos:
            print(f"\n  {video['title'][:50]}")
            fixed_segs = []

            for seg in video["segments"]:
                fixed_text, changes = fix_segment(seg["text"], known_words, common_english)
                fixed_segs.append({
                    **seg,
                    "original_text": seg["text"],
                    "text": fixed_text,
                    "fixes": changes,
                    "was_fixed": len(changes) > 0,
                })
                if changes:
                    lang_fixes += len(changes)

            # Show sample fixes
            for seg in fixed_segs:
                if seg["fixes"]:
                    for fix in seg["fixes"][:3]:
                        print(f"    {fix['original']:20s} → {fix['fixed']:20s} (dist={fix['distance']})")

            lang_fixed.append({
                **video,
                "segments": fixed_segs,
            })

        fixed_transcripts[lang_code] = lang_fixed
        total_fixes += lang_fixes
        print(f"\n  Fixes applied: {lang_fixes}")

    # Save fixed transcripts
    out_file = TRANSCRIPTS_DIR / "fixed_transcripts.json"
    out_file.write_text(json.dumps(fixed_transcripts, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"  Total fixes: {total_fixes}")
    print(f"  Saved to: {out_file}")

    # Also generate a clean segments file for the frontend
    frontend_segments = []
    for lang_code, videos in fixed_transcripts.items():
        for video in videos:
            for seg in video["segments"]:
                vid_match = re.search(r"v=([^&]+)", video["url"])
                vid_id = vid_match.group(1) if vid_match else ""
                frontend_segments.append({
                    "id": f"{vid_id}_{int(seg['start'])}",
                    "external_url": video["url"],
                    "start_time_ms": int(seg["start"] * 1000),
                    "end_time_ms": int(seg["end"] * 1000),
                    "duration_ms": int((seg["end"] - seg["start"]) * 1000),
                    "channel_name": video["title"],
                    "language_code": lang_code,
                    "domain": "education",
                    "auto_transcript": seg["text"],
                    "was_fixed": seg.get("was_fixed", False),
                    "fix_count": len(seg.get("fixes", [])),
                })

    frontend_file = Path("public/data/whisper-segments.json")
    frontend_file.write_text(json.dumps(frontend_segments, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Frontend segments: {len(frontend_segments)}")
    print(f"  Saved to: {frontend_file}")

    conn.close()


if __name__ == "__main__":
    main()
