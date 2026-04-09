"""
Liseli Flywheel — the self-improving data pipeline.

Transcribe → Extract → Enrich → Improve prompts → Transcribe better → repeat.

Each stage feeds the next:

  1. EXTRACT: Parse transcripts for vocabulary pairs, grammar patterns, verb forms
  2. ENRICH: Merge extracted data into engine files + public JSON
  3. PROMPT: Generate better Whisper prompts from what we've learned
  4. STATS: Update public stats so the world sees progress

Run: python scripts/flywheel.py
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
PUBLIC = ROOT / "public" / "data"
ENGINE = DATA / "engine"
TRANSCRIPTS_DIR = DATA / "language-courses"
UBUNTU_TRANSCRIPTS = DATA / "ubuntu-talks-transcripts" / "all_ubuntu_talks.json"
WHISPER_TRANSCRIPTS = DATA / "whisper-transcripts" / "all_transcripts.json"

# Language code → full name mapping
LANG_MAP = {
    "bem": "bemba", "nya": "nyanja", "toi": "tonga",
    "loz": "lozi", "kqn": "kaonde", "lun": "lunda",
    "lue": "luvale", "mul": "multi",
}
LANG_MAP_REV = {v: k for k, v in LANG_MAP.items()}

# ============================================================
# STAGE 1: EXTRACT — pull structured data from raw transcripts
# ============================================================

# Patterns that indicate vocabulary teaching:
# "X is Y", "X means Y", "to X is Y", "Y is called X"
VOCAB_PATTERNS = [
    # "hello is moni", "water is madzi"
    re.compile(
        r'\b([A-Z][\w\s]{0,30}?)\s+is\s+([a-z]\w+(?:\s+[a-z]\w+)?)\b',
        re.IGNORECASE
    ),
    # "to eat is kudya"
    re.compile(
        r'\bto\s+(\w+)\s+is\s+(ku\w+)\b',
        re.IGNORECASE
    ),
    # "moni means hello"
    re.compile(
        r'\b(\w+)\s+means?\s+(["\']?[\w\s]+["\']?)\b',
        re.IGNORECASE
    ),
    # "X, which is Y" or "X, meaning Y"
    re.compile(
        r'\b(\w+),?\s+(?:which is|meaning)\s+(["\']?[\w\s]+["\']?)\b',
        re.IGNORECASE
    ),
]

# Verb conjugation patterns:
# "I am eating is ndikudya" / "I ate is ndinadya"
CONJUGATION_PATTERNS = [
    re.compile(
        r'\b(I\s+(?:am\s+)?(?:\w+ing|\w+ed|\w+))\s+is\s+(\w+)\b',
        re.IGNORECASE
    ),
    re.compile(
        r'\b(you\s+(?:are\s+)?(?:\w+ing|\w+ed|\w+))\s+(?:is|are)\s+(\w+)\b',
        re.IGNORECASE
    ),
    re.compile(
        r'\b(he|she|they)\s+(?:is|are)\s+(\w+ing)\s+is\s+(\w+)\b',
        re.IGNORECASE
    ),
]

# Grammar pattern markers
GRAMMAR_MARKERS = [
    "past tense", "present tense", "future tense",
    "plural", "singular", "prefix", "suffix",
    "noun class", "verb", "pronoun",
    "conjugat", "tense",
]

# Common English words to filter out of "local language" side
ENGLISH_STOP = set("""
    the a an is are am was were be been being have has had do does did
    will would shall should can could may might must need to of in for
    on at by with from as into through during before after above below
    between under over about up out off down not no nor or and but if
    then than too very so all each every both few more most other some
    such only own same just now still also here there where when how
    what which who whom this that these those it he she we they i you
    your my his her its our their me him us them yes well ok okay
    really actually basically literally like just right exactly
    lesson number today week words more few final verb verbs word
    good great perfect correct exactly pronounce repeat try again
    next let lets start end begin finish remember practice
    one two three four five six seven eight nine ten
""".split())


def load_all_transcripts():
    """Load transcripts from all sources into a unified format."""
    all_segments = []

    # 1. Language course transcripts (new format)
    if TRANSCRIPTS_DIR.exists():
        for source_dir in TRANSCRIPTS_DIR.iterdir():
            if not source_dir.is_dir() or source_dir.name == "audio":
                continue
            tf = source_dir / "transcripts.json"
            if not tf.exists():
                continue
            data = json.loads(tf.read_text(encoding="utf-8"))
            for vid_id, entry in data.items():
                target = entry.get("target_lang", "?")
                for seg in entry.get("segments", []):
                    all_segments.append({
                        "source": source_dir.name,
                        "video_id": vid_id,
                        "title": entry.get("title", ""),
                        "target_lang": target,
                        "text": seg["text"],
                        "start": seg["start"],
                        "end": seg["end"],
                    })

    # 2. Ubuntu Talks transcripts
    if UBUNTU_TRANSCRIPTS.exists():
        data = json.loads(UBUNTU_TRANSCRIPTS.read_text(encoding="utf-8"))
        for vid_id, entry in data.items():
            lang = entry.get("language_code", "?")
            for seg in entry.get("segments", []):
                all_segments.append({
                    "source": "ubuntu-talks",
                    "video_id": vid_id,
                    "title": entry.get("title", ""),
                    "target_lang": lang,
                    "text": seg["text"],
                    "start": seg["start"],
                    "end": seg["end"],
                })

    # 3. Whisper batch transcripts
    if WHISPER_TRANSCRIPTS.exists():
        data = json.loads(WHISPER_TRANSCRIPTS.read_text(encoding="utf-8"))
        for lang_code, videos in data.items():
            for entry in videos:
                for seg in entry.get("segments", []):
                    all_segments.append({
                        "source": "whisper-batch",
                        "video_id": entry.get("video_id", "?"),
                        "title": entry.get("title", ""),
                        "target_lang": lang_code,
                        "text": seg["text"],
                        "start": seg["start"],
                        "end": seg["end"],
                    })

    # 4. Zambezi Voice + BembaSpeech labeled data (TSV files)
    zambezi_dir = DATA / "zambezi-voice"
    if zambezi_dir.exists():
        lang_map_zv = {
            "bemba": "bem", "nyanja": "nya", "tonga": "toi", "lozi": "loz",
        }
        zv_count = 0
        for tsv_file in zambezi_dir.glob("*.tsv"):
            lang_name = tsv_file.stem.split("_")[0]  # e.g. "bemba" from "bemba_train.tsv"
            lang_code = lang_map_zv.get(lang_name, lang_name)
            with open(tsv_file, encoding="utf-8") as f:
                lines = f.readlines()
            # Skip header
            for i, line in enumerate(lines[1:], 1):
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    sentence = parts[1] if "sentence" not in parts[1].lower() else ""
                    if sentence:
                        all_segments.append({
                            "source": "zambezi-voice",
                            "video_id": parts[0],  # audio filename
                            "title": tsv_file.stem,
                            "target_lang": lang_code,
                            "text": sentence,
                            "start": 0,
                            "end": 0,
                        })
                        zv_count += 1
        print(f"  Zambezi Voice/BembaSpeech: {zv_count} labeled utterances")

    print(f"Loaded {len(all_segments)} segments from all sources")
    return all_segments


def extract_vocabulary(segments):
    """
    Extract English ↔ local language pairs from transcript segments.
    Returns dict: {lang_code: [{english, local, source, confidence}, ...]}
    """
    pairs = defaultdict(list)
    seen = defaultdict(set)  # dedupe per language

    for seg in segments:
        text = seg["text"]
        lang = seg["target_lang"]
        if lang in ("mul", "?"):
            continue

        for pattern in VOCAB_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) < 2:
                    continue

                # Figure out which is English, which is local
                a, b = groups[0].strip().strip('"\''), groups[1].strip().strip('"\'')

                # Heuristic: if it starts with "ku" it's a Bantu verb infinitive
                # If it's a common English word, it's English
                a_lower = a.lower()
                b_lower = b.lower()

                if a_lower in ENGLISH_STOP or b_lower in ENGLISH_STOP:
                    continue

                # For "to X is kuY" pattern, a=English verb, b=local
                if pattern.pattern.startswith(r'\bto\s'):
                    english, local = a, b
                # For "X means Y", X is likely local, Y is English
                elif 'means' in pattern.pattern:
                    local, english = a, b
                # For "X is Y" — check if b looks Bantu (has ku/mu/ba/chi prefix)
                elif b_lower.startswith(('ku', 'mu', 'ba', 'chi', 'ci', 'ka',
                                         'ndi', 'uku', 'ici', 'imi')):
                    english, local = a, b
                elif a_lower.startswith(('ku', 'mu', 'ba', 'chi', 'ci', 'ka',
                                         'ndi', 'uku', 'ici', 'imi')):
                    local, english = a, b
                else:
                    # Default: first is English concept, second is local word
                    english, local = a, b

                # Quality filters
                if local.lower() in ENGLISH_STOP:
                    continue
                if len(local) < 2 or len(english) < 2:
                    continue
                # Reject if local side has too many English words
                local_tokens = local.lower().split()
                english_tokens_in_local = sum(1 for t in local_tokens if t in ENGLISH_STOP)
                if len(local_tokens) > 3:
                    continue  # local words shouldn't be long phrases
                if english_tokens_in_local > 0:
                    continue  # local side should have zero English stop words
                # Reject if english side has too many words (should be a concept)
                if len(english.split()) > 4:
                    continue

                key = f"{english.lower()}|{local.lower()}"
                if key not in seen[lang]:
                    seen[lang].add(key)
                    pairs[lang].append({
                        "english": english.strip(),
                        "local": local.strip(),
                        "source": seg["source"],
                        "video_title": seg["title"],
                        "confidence": 0.7,  # transcription-extracted
                    })

    return dict(pairs)


def extract_grammar_notes(segments):
    """
    Extract segments that discuss grammar rules.
    Returns structured grammar observations per language.
    """
    grammar = defaultdict(list)

    for seg in segments:
        text_lower = seg["text"].lower()
        lang = seg["target_lang"]

        for marker in GRAMMAR_MARKERS:
            if marker in text_lower:
                grammar[lang].append({
                    "text": seg["text"],
                    "marker": marker,
                    "source": seg["source"],
                    "video_title": seg["title"],
                    "timestamp": seg["start"],
                })
                break  # one match per segment is enough

    return dict(grammar)


def extract_verb_conjugations(segments):
    """
    Extract verb conjugation patterns (I am eating = ndikudya).
    """
    conjugations = defaultdict(list)

    for seg in segments:
        text = seg["text"]
        lang = seg["target_lang"]

        for pattern in CONJUGATION_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 2:
                    conjugations[lang].append({
                        "english_form": groups[0].strip(),
                        "local_form": groups[-1].strip(),
                        "full_context": text[:200],
                        "source": seg["source"],
                    })

    return dict(conjugations)


# ============================================================
# STAGE 2: ENRICH — merge extracted data into existing files
# ============================================================

def enrich_dictionary(vocab_pairs):
    """Merge newly extracted vocab into public/data/dictionary.json."""
    dict_path = PUBLIC / "dictionary.json"
    existing = json.loads(dict_path.read_text(encoding="utf-8")) if dict_path.exists() else []

    # Index existing by english text
    by_english = {}
    for entry in existing:
        by_english[entry["english"].lower()] = entry

    added = 0
    updated = 0

    for lang_code, pairs in vocab_pairs.items():
        lang_name = LANG_MAP.get(lang_code, lang_code)
        for pair in pairs:
            en_key = pair["english"].lower()

            if en_key in by_english:
                entry = by_english[en_key]
                if lang_name not in entry.get("translations", {}):
                    entry.setdefault("translations", {})[lang_name] = {
                        "text": pair["local"],
                        "status": "unverified",
                        "source": "transcript",
                    }
                    updated += 1
            else:
                new_entry = {
                    "english": pair["english"],
                    "translations": {
                        lang_name: {
                            "text": pair["local"],
                            "status": "unverified",
                            "source": "transcript",
                        }
                    },
                }
                existing.append(new_entry)
                by_english[en_key] = new_entry
                added += 1

    # Sort by English
    existing.sort(key=lambda e: e["english"].lower())

    dict_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Dictionary: +{added} new entries, {updated} updated ({len(existing)} total)")
    return existing


def enrich_engine(vocab_pairs):
    """
    Add extracted vocabulary to engine word_freq and asr_corrections.
    The asr_corrections field maps common Whisper misheard forms to correct forms.
    """
    for lang_code, pairs in vocab_pairs.items():
        lang_name = LANG_MAP.get(lang_code, lang_code)
        engine_path = ENGINE / f"{lang_name}_engine.json"
        if not engine_path.exists():
            continue

        engine = json.loads(engine_path.read_text(encoding="utf-8"))
        word_freq = engine.get("word_freq", {})

        # Add extracted words to frequency map (low weight — transcript-derived)
        boosted = 0
        for pair in pairs:
            word = pair["local"].lower()
            tokens = word.split()
            for token in tokens:
                if token not in word_freq:
                    word_freq[token] = 1.0
                    boosted += 1
                else:
                    # Small boost for words confirmed by structured lessons
                    word_freq[token] = word_freq[token] + 0.5

        engine["word_freq"] = word_freq
        engine["vocabulary_size"] = len(word_freq)

        engine_path.write_text(
            json.dumps(engine, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if boosted:
            print(f"  Engine {lang_name}: +{boosted} new words in word_freq")


def enrich_engine_from_zambezi():
    """
    Ingest Zambezi Voice / BembaSpeech monolingual text into engine word_freq.
    This massively improves our vocabulary coverage for Whisper prompts.
    """
    zambezi_dir = DATA / "zambezi-voice"
    if not zambezi_dir.exists():
        return

    lang_map_zv = {
        "bemba": "bem", "nyanja": "nya", "tonga": "toi", "lozi": "loz",
    }

    for tsv_file in sorted(zambezi_dir.glob("*.tsv")):
        lang_name = tsv_file.stem.split("_")[0]
        lang_code = lang_map_zv.get(lang_name, lang_name)

        engine_path = ENGINE / f"{lang_code}_engine.json"
        if not engine_path.exists():
            continue

        engine = json.loads(engine_path.read_text(encoding="utf-8"))
        word_freq = engine.get("word_freq", {})
        old_size = len(word_freq)

        with open(tsv_file, encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines[1:]:  # skip header
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                sentence = parts[1].lower()
                for token in sentence.split():
                    # Clean token
                    token = token.strip(".,;:!?\"'()-")
                    if len(token) < 2:
                        continue
                    word_freq[token] = word_freq.get(token, 0) + 1.0

        engine["word_freq"] = word_freq
        engine["vocabulary_size"] = len(word_freq)
        engine_path.write_text(
            json.dumps(engine, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        new_words = len(word_freq) - old_size
        if new_words > 0:
            print(f"  Engine {lang_code}: +{new_words} new words from {tsv_file.name}")


# ============================================================
# STAGE 3: PROMPT — generate better Whisper prompts from data
# ============================================================

def generate_whisper_prompts():
    """
    Build language-specific Whisper prompts from our current knowledge.
    Uses the dictionary + engine data to create prompts dense with
    known vocabulary, so Whisper recognizes these words instead of
    guessing random English.

    Saves to data/whisper-prompts/<lang>.txt
    """
    prompt_dir = DATA / "whisper-prompts"
    prompt_dir.mkdir(exist_ok=True)

    dict_path = PUBLIC / "dictionary.json"
    if not dict_path.exists():
        return

    dictionary = json.loads(dict_path.read_text(encoding="utf-8"))

    for lang_code, lang_name in LANG_MAP.items():
        if lang_code == "mul":
            continue

        # Collect all known words for this language
        words = set()
        pair_examples = []

        for entry in dictionary:
            trans = entry.get("translations", {}).get(lang_name, {})
            if trans:
                local_text = trans.get("text", "")
                if local_text:
                    words.update(local_text.lower().split())
                    if len(pair_examples) < 30:
                        pair_examples.append(
                            f"{entry['english']} = {local_text}"
                        )

        # Also pull top words from engine
        engine_path = ENGINE / f"{lang_name}_engine.json"
        if engine_path.exists():
            engine = json.loads(engine_path.read_text(encoding="utf-8"))
            wf = engine.get("word_freq", {})
            top_words = sorted(wf.items(), key=lambda x: -x[1])[:100]
            words.update(w for w, _ in top_words)

        if not words:
            continue

        # Build the prompt
        endonyms = {
            "bemba": "Icibemba", "nyanja": "Chinyanja", "tonga": "Chitonga",
            "lozi": "Silozi", "kaonde": "Kikaonde", "lunda": "Chilunda",
            "luvale": "Luvale",
        }
        endonym = endonyms.get(lang_name, lang_name)

        # Sort words by length (longer = more distinctive = better hints)
        sorted_words = sorted(words, key=len, reverse=True)[:80]
        word_list = ", ".join(sorted_words)

        prompt = (
            f"This audio contains {endonym} ({lang_name.title()}) language content, "
            f"possibly mixed with English. "
            f"Common {endonym} words that may appear: {word_list}. "
        )

        if pair_examples:
            examples_str = "; ".join(pair_examples[:15])
            prompt += f"Known vocabulary pairs: {examples_str}. "

        prompt_path = prompt_dir / f"{lang_code}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"  Prompt {lang_code}: {len(words)} known words -> {len(prompt)} chars")

    return prompt_dir


# ============================================================
# STAGE 4: STATS — update public-facing numbers
# ============================================================

def update_stats(vocab_pairs, grammar_notes, conjugations):
    """Update public/data/stats.json with latest numbers."""
    stats_path = PUBLIC / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}

    # Count transcript-derived data
    transcript_vocab = sum(len(v) for v in vocab_pairs.values())
    transcript_grammar = sum(len(v) for v in grammar_notes.values())
    transcript_conjugations = sum(len(v) for v in conjugations.values())

    # Count dictionary
    dict_path = PUBLIC / "dictionary.json"
    dict_size = 0
    if dict_path.exists():
        dictionary = json.loads(dict_path.read_text(encoding="utf-8"))
        dict_size = len(dictionary)

    stats["dictionary_entries"] = dict_size
    stats["transcript_vocab_pairs"] = transcript_vocab
    stats["transcript_grammar_notes"] = transcript_grammar
    stats["transcript_conjugations"] = transcript_conjugations

    # Count transcribed audio
    total_segments = 0
    total_sources = 0
    if TRANSCRIPTS_DIR.exists():
        for source_dir in TRANSCRIPTS_DIR.iterdir():
            if not source_dir.is_dir() or source_dir.name == "audio":
                continue
            tf = source_dir / "transcripts.json"
            if tf.exists():
                data = json.loads(tf.read_text(encoding="utf-8"))
                total_sources += 1
                for entry in data.values():
                    total_segments += len(entry.get("segments", []))

    if UBUNTU_TRANSCRIPTS.exists():
        data = json.loads(UBUNTU_TRANSCRIPTS.read_text(encoding="utf-8"))
        total_sources += 1
        for entry in data.values():
            total_segments += len(entry.get("segments", []))

    if WHISPER_TRANSCRIPTS.exists():
        data = json.loads(WHISPER_TRANSCRIPTS.read_text(encoding="utf-8"))
        total_sources += 1
        for videos in data.values():
            for entry in videos:
                total_segments += len(entry.get("segments", []))

    # Count Zambezi Voice labeled utterances
    zambezi_utterances = 0
    zambezi_dir = DATA / "zambezi-voice"
    if zambezi_dir.exists():
        total_sources += 1
        for tsv_file in zambezi_dir.glob("*.tsv"):
            with open(tsv_file, encoding="utf-8") as f:
                zambezi_utterances += sum(1 for _ in f) - 1  # minus header

    stats["transcribed_segments"] = total_segments
    stats["zambezi_voice_utterances"] = zambezi_utterances
    stats["total_labeled_data"] = total_segments + zambezi_utterances
    stats["transcript_sources"] = total_sources

    stats_path.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Stats: {dict_size} dict entries, {total_segments} segments, "
          f"{transcript_vocab} vocab pairs extracted")


# ============================================================
# STAGE 5: EXPORT — save extracted data for the app to use
# ============================================================

def export_transcript_vocabulary(vocab_pairs):
    """
    Export extracted vocab as a browsable JSON for the frontend.
    Separate from the main dictionary — this is "what we learned from audio."
    """
    out_path = PUBLIC / "transcript-vocab.json"
    export = {}

    for lang_code, pairs in vocab_pairs.items():
        lang_name = LANG_MAP.get(lang_code, lang_code)
        export[lang_name] = sorted(pairs, key=lambda p: p["english"].lower())

    out_path.write_text(
        json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(len(v) for v in export.values())
    print(f"  Exported {total} transcript vocab pairs -> {out_path.name}")


def export_grammar_notes(grammar_notes):
    """Export grammar observations from transcripts."""
    out_path = PUBLIC / "transcript-grammar.json"
    export = {}

    for lang_code, notes in grammar_notes.items():
        lang_name = LANG_MAP.get(lang_code, lang_code)
        export[lang_name] = notes

    out_path.write_text(
        json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(len(v) for v in export.values())
    print(f"  Exported {total} grammar notes -> {out_path.name}")


# ============================================================
# RUN THE FLYWHEEL
# ============================================================

def run():
    print("=" * 60)
    print("LISELI FLYWHEEL — self-improving data pipeline")
    print("=" * 60)

    # Stage 1: Extract
    print("\n[1/5] EXTRACT — parsing transcripts...")
    segments = load_all_transcripts()
    vocab_pairs = extract_vocabulary(segments)
    grammar_notes = extract_grammar_notes(segments)
    conjugations = extract_verb_conjugations(segments)

    for lang, pairs in sorted(vocab_pairs.items()):
        print(f"  {lang}: {len(pairs)} vocabulary pairs extracted")
    for lang, notes in sorted(grammar_notes.items()):
        print(f"  {lang}: {len(notes)} grammar segments found")
    for lang, conj in sorted(conjugations.items()):
        print(f"  {lang}: {len(conj)} conjugation patterns")

    # Stage 2: Enrich
    print("\n[2/5] ENRICH — merging into dictionary + engine...")
    enrich_dictionary(vocab_pairs)
    enrich_engine(vocab_pairs)
    enrich_engine_from_zambezi()

    # Stage 3: Prompt
    print("\n[3/5] PROMPT — generating improved Whisper prompts...")
    generate_whisper_prompts()

    # Stage 4: Stats
    print("\n[4/5] STATS — updating public numbers...")
    update_stats(vocab_pairs, grammar_notes, conjugations)

    # Stage 5: Export
    print("\n[5/5] EXPORT — saving extracted data for frontend...")
    export_transcript_vocabulary(vocab_pairs)
    export_grammar_notes(grammar_notes)

    print("\n" + "=" * 60)
    print("FLYWHEEL COMPLETE")
    print("  Next transcription batch will use improved prompts from:")
    print("    data/whisper-prompts/<lang>.txt")
    print("  Run transcribe_language_courses.py, then flywheel.py again.")
    print("=" * 60)


if __name__ == "__main__":
    run()
