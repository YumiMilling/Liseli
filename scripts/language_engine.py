"""
Liseli Language Engine
Learns from corrections to improve transcript predictions over time.
Builds phonetic mappings, domain-weighted word frequencies, and
prediction models from community corrections.

The engine improves with every contributor correction:
- Whisper hears "bwajji" → human corrects to "bwanji" → engine learns bwajji→bwanji
- Next time Whisper produces "bwajji", engine auto-corrects it
"""
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict, Counter
from pathlib import Path

DB_PATH = Path("data/liseli_local.db")
ENGINE_DIR = Path("data/engine")
ENGINE_DIR.mkdir(parents=True, exist_ok=True)


def normalize(text):
    return unicodedata.normalize("NFC", text.lower().strip())


class LanguageEngine:
    """
    Per-language prediction engine that learns from data.
    Stores: word frequencies, phonetic mappings, domain vocabularies,
    bigram probabilities, and ASR correction patterns.
    """

    def __init__(self, lang_code, lang_name):
        self.lang_code = lang_code
        self.lang_name = lang_name

        # Word frequencies weighted by domain
        # Higher weight = more likely in everyday speech
        self.word_freq = Counter()
        self.domain_words = defaultdict(Counter)  # domain -> word -> count

        # Phonetic correction map: what ASR produces -> what humans correct to
        self.asr_corrections = defaultdict(Counter)  # asr_word -> {correct_word: count}

        # Bigrams: which words follow which (for prediction)
        self.bigrams = defaultdict(Counter)  # word -> {next_word: count}

        # Known vocabulary (all confirmed correct spellings)
        self.vocabulary = set()

    def load_from_db(self, conn):
        """Bootstrap from existing Liseli database."""
        # Domain weights: everyday > education > religion
        DOMAIN_WEIGHT = {
            "daily_life": 5.0,
            "education": 3.0,
            "health": 4.0,
            "agriculture": 4.0,
            "market_commerce": 4.0,
            "general": 2.0,
            "religion": 1.0,
        }

        # Load from translations (parallel data — verified)
        for r in conn.execute("""
            SELECT t.text, s.domain FROM translations t
            JOIN sentences s ON s.id = t.sentence_id
            WHERE t.language = ?
        """, (self.lang_name,)):
            text = r[0]
            domain = r[1] or "general"
            weight = DOMAIN_WEIGHT.get(domain, 2.0)
            words = re.findall(r"[a-zA-Z\u00C0-\u024F\u02B0-\u02FF']+", text.lower())

            for word in words:
                if len(word) >= 2:
                    self.word_freq[word] += weight
                    self.domain_words[domain][word] += 1
                    self.vocabulary.add(word)

            # Build bigrams
            for i in range(len(words) - 1):
                if len(words[i]) >= 2 and len(words[i + 1]) >= 2:
                    self.bigrams[words[i]][words[i + 1]] += weight

        # Load from corpus (monolingual — broader)
        for r in conn.execute(
            "SELECT text, domain FROM corpus WHERE language = ?", (self.lang_name,)
        ):
            text = r[0]
            domain = r[1] or "general"
            weight = DOMAIN_WEIGHT.get(domain, 2.0) * 0.5  # corpus is lower weight
            words = re.findall(r"[a-zA-Z\u00C0-\u024F\u02B0-\u02FF']+", text.lower())

            for word in words:
                if len(word) >= 2:
                    self.word_freq[word] += weight
                    self.vocabulary.add(word)

            for i in range(len(words) - 1):
                if len(words[i]) >= 2 and len(words[i + 1]) >= 2:
                    self.bigrams[words[i]][words[i + 1]] += weight

        # Load existing ASR corrections (from community corrections)
        # These would come from the validation_votes / contributions tables
        # For now, seed with common ASR error patterns
        self._seed_phonetic_patterns()

    def _seed_phonetic_patterns(self):
        """Seed common ASR misheard patterns for Bantu languages."""
        # Common patterns where English ASR mishears Bantu sounds
        common_patterns = {
            "sh": "sh",   # usually correct
            "ch": "ch",   # usually correct
            "ng": "ng'",  # ASR drops the apostrophe
            "ny": "ny",   # usually correct
            "mb": "mb",   # usually correct
            "nd": "nd",   # usually correct
            "nk": "nk",   # usually correct
        }
        # These get applied during fix_word

    def levenshtein(self, s1, s2):
        if len(s1) < len(s2):
            return self.levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
            prev = curr
        return prev[-1]

    def fix_word(self, word, context_domain=None, prev_word=None):
        """
        Try to correct a single word using all available knowledge.
        Returns (corrected_word, confidence, method).
        """
        word_lower = word.lower()

        # 1. Check ASR correction map (learned from community)
        if word_lower in self.asr_corrections:
            corrections = self.asr_corrections[word_lower]
            best = corrections.most_common(1)[0]
            return best[0], 0.9, "asr_learned"

        # 2. Exact match in vocabulary
        if word_lower in self.vocabulary:
            return word, 1.0, "exact"

        # 3. Domain-weighted fuzzy match
        candidates = []
        for known in self.vocabulary:
            if abs(len(known) - len(word_lower)) > 2:
                continue
            dist = self.levenshtein(word_lower, known)
            if dist <= 2:
                # Score: lower distance is better, higher frequency is better
                freq_score = self.word_freq.get(known, 0)

                # Boost if word is in the video's domain
                domain_boost = 1.0
                if context_domain and known in self.domain_words.get(context_domain, {}):
                    domain_boost = 2.0

                # Boost if bigram matches (prev_word -> this word is common)
                bigram_boost = 1.0
                if prev_word and known in self.bigrams.get(prev_word.lower(), {}):
                    bigram_boost = 3.0

                score = (3 - dist) * freq_score * domain_boost * bigram_boost
                candidates.append((known, dist, score))

        if candidates:
            candidates.sort(key=lambda x: -x[2])  # highest score first
            best = candidates[0]
            confidence = max(0.3, 1.0 - (best[1] * 0.3))  # dist 1 = 0.7, dist 2 = 0.4
            corrected = best[0]
            # Preserve capitalization
            if word[0].isupper():
                corrected = corrected[0].upper() + corrected[1:]
            return corrected, confidence, "fuzzy_weighted"

        # 4. No match — unknown word
        return word, 0.1, "unknown"

    def fix_transcript(self, text, domain=None):
        """Fix an entire transcript segment."""
        words = text.split()
        result = []
        changes = []
        prev_word = None

        for word in words:
            # Strip punctuation
            clean = re.sub(r"[.,!?;:'\"-]", "", word)
            punct = word[len(clean):]

            if len(clean) < 2:
                result.append(word)
                continue

            # Skip obvious English (common function words)
            if clean.lower() in COMMON_ENGLISH:
                result.append(word)
                prev_word = clean
                continue

            fixed, confidence, method = self.fix_word(clean, domain, prev_word)

            if method != "exact" and method != "unknown" and fixed.lower() != clean.lower():
                changes.append({
                    "original": clean,
                    "fixed": fixed,
                    "confidence": confidence,
                    "method": method,
                })

            result.append(fixed + punct)
            prev_word = fixed

        return " ".join(result), changes

    def learn_correction(self, asr_word, correct_word):
        """Learn from a community correction."""
        self.asr_corrections[asr_word.lower()][correct_word.lower()] += 1
        self.vocabulary.add(correct_word.lower())
        self.word_freq[correct_word.lower()] += 5.0  # boost corrected words

    def predict_next(self, current_word, top_n=5):
        """Predict most likely next word (for autocomplete)."""
        if current_word.lower() in self.bigrams:
            return self.bigrams[current_word.lower()].most_common(top_n)
        return []

    def get_stats(self):
        return {
            "vocabulary_size": len(self.vocabulary),
            "total_word_freq": sum(self.word_freq.values()),
            "top_words": self.word_freq.most_common(20),
            "bigram_pairs": sum(len(v) for v in self.bigrams.values()),
            "asr_corrections": len(self.asr_corrections),
            "domains": {d: len(words) for d, words in self.domain_words.items()},
        }

    def save(self):
        """Save engine state to disk."""
        data = {
            "lang_code": self.lang_code,
            "lang_name": self.lang_name,
            "word_freq": dict(self.word_freq.most_common(50000)),
            "asr_corrections": {k: dict(v) for k, v in self.asr_corrections.items()},
            "bigrams": {k: dict(v.most_common(20)) for k, v in self.bigrams.items()
                        if v.most_common(1)[0][1] >= 2},  # only keep bigrams seen 2+ times
            "domain_words": {d: dict(words.most_common(1000)) for d, words in self.domain_words.items()},
            "vocabulary_size": len(self.vocabulary),
        }
        out = ENGINE_DIR / f"{self.lang_code}_engine.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def load(self):
        """Load engine state from disk."""
        path = ENGINE_DIR / f"{self.lang_code}_engine.json"
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        self.word_freq = Counter(data.get("word_freq", {}))
        self.asr_corrections = defaultdict(Counter, {
            k: Counter(v) for k, v in data.get("asr_corrections", {}).items()
        })
        self.bigrams = defaultdict(Counter, {
            k: Counter(v) for k, v in data.get("bigrams", {}).items()
        })
        self.domain_words = defaultdict(Counter, {
            k: Counter(v) for k, v in data.get("domain_words", {}).items()
        })
        self.vocabulary = set(self.word_freq.keys())
        return True


COMMON_ENGLISH = set(
    "the a an is are was were be been being have has had do does did will would "
    "could should may might shall can need to of in for on with at by from as into "
    "through during before after above below between out off over under again "
    "then once here there when where why how all both each few more most other some "
    "such no nor not only own same so than too very just and but or if while because "
    "until although that this these those i me my we our you your he him his she her "
    "it its they them their what which who whom say says said like know go come "
    "take make see want give use find tell think look well good also back even still "
    "way many work now day time world people been right get going thing about "
    "called hello hi thank thanks okay yes please welcome everybody everyone "
    "subscribe share comment below basically language learn speak words".split()
)

LANGUAGES = {
    "bem": "bemba", "nya": "nyanja", "toi": "tonga", "loz": "lozi",
    "kqn": "kaonde", "lun": "lunda", "lue": "luvale",
}


def main():
    print("=" * 60)
    print("LISELI LANGUAGE ENGINE — BUILD")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    engines = {}

    for lang_code, lang_name in LANGUAGES.items():
        print(f"\n  Building {lang_code} ({lang_name}) engine...")
        engine = LanguageEngine(lang_code, lang_name)
        engine.load_from_db(conn)

        stats = engine.get_stats()
        print(f"    Vocabulary: {stats['vocabulary_size']:,} words")
        print(f"    Bigram pairs: {stats['bigram_pairs']:,}")
        print(f"    Domains: {stats['domains']}")
        print(f"    Top 10: {[w for w, _ in stats['top_words'][:10]]}")

        out = engine.save()
        print(f"    Saved to: {out}")
        engines[lang_code] = engine

    # Now fix transcripts if they exist
    transcript_file = Path("data/whisper-transcripts/all_transcripts.json")
    if transcript_file.exists():
        print(f"\n{'=' * 60}")
        print("FIXING TRANSCRIPTS")
        print(f"{'=' * 60}")

        transcripts = json.loads(transcript_file.read_text(encoding="utf-8"))
        fixed_all = {}
        total_fixes = 0

        for lang_code, videos in transcripts.items():
            if lang_code not in engines:
                continue
            engine = engines[lang_code]
            print(f"\n  {lang_code.upper()}:")

            fixed_videos = []
            for video in videos:
                fixed_segs = []
                for seg in video["segments"]:
                    fixed_text, changes = engine.fix_transcript(seg["text"], domain="education")
                    fixed_segs.append({
                        **seg,
                        "original_text": seg["text"],
                        "text": fixed_text,
                        "fixes": changes,
                    })
                    total_fixes += len(changes)

                    # Show interesting fixes
                    for c in changes:
                        if c["confidence"] >= 0.5:
                            print(f"    {c['original']:20s} → {c['fixed']:20s} ({c['method']}, conf={c['confidence']:.1f})")

                fixed_videos.append({**video, "segments": fixed_segs})
            fixed_all[lang_code] = fixed_videos

        # Save fixed transcripts
        out = Path("data/whisper-transcripts/engine_fixed.json")
        out.write_text(json.dumps(fixed_all, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  Total fixes: {total_fixes}")

        # Generate frontend segments
        frontend = []
        for lang_code, videos in fixed_all.items():
            for video in videos:
                for seg in video["segments"]:
                    vid_match = re.search(r"v=([^&]+)", video["url"])
                    vid_id = vid_match.group(1) if vid_match else ""
                    frontend.append({
                        "id": f"{vid_id}_{int(seg['start'])}",
                        "external_url": video["url"],
                        "start_time_ms": int(seg["start"] * 1000),
                        "end_time_ms": int(seg["end"] * 1000),
                        "duration_ms": int((seg["end"] - seg["start"]) * 1000),
                        "channel_name": video["title"],
                        "language_code": lang_code,
                        "domain": "education",
                        "auto_transcript": seg["text"],
                    })

        Path("public/data/whisper-segments.json").write_text(
            json.dumps(frontend, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  Frontend segments: {len(frontend)}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
