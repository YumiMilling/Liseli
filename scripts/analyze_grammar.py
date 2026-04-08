"""
Derive comprehensive grammar patterns from parallel data.
Analyzes all 7 Zambian languages using aligned Bible + storybook data.
"""
import sqlite3
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

DB_PATH = Path("data/liseli_local.db")
OUT = Path("public/data")

LANGUAGES = ["bemba", "nyanja", "tonga", "lozi", "kaonde", "lunda", "luvale"]
LANG_NAMES = {
    "bemba": "Icibemba", "nyanja": "Chinyanja", "tonga": "Chitonga",
    "lozi": "Silozi", "kaonde": "Kikaonde", "lunda": "Chilunda", "luvale": "Luvale",
}


def tokenize(text):
    return [w.lower() for w in re.findall(r"[a-zA-Z\u00C0-\u024F\u02B0-\u02FF']+", text) if len(w) > 1]


def get_parallel_pairs(conn, lang, limit=30000):
    """Get English-target parallel pairs."""
    return conn.execute("""
        SELECT s.english, t.text FROM sentences s
        JOIN translations t ON t.sentence_id = s.id
        WHERE t.language = ? AND length(s.english) > 5
        LIMIT ?
    """, (lang, limit)).fetchall()


def analyze_noun_classes(conn, lang):
    """
    Bantu noun classes are marked by prefixes on nouns.
    Analyze word-initial patterns to identify likely noun class prefixes.
    Group by singular/plural pairs.
    """
    words = []
    for r in conn.execute(
        "SELECT text FROM translations WHERE language = ? LIMIT 25000", (lang,)
    ):
        words.extend(tokenize(r[0]))

    word_freq = Counter(words)

    # Get 2, 3, and 4 character prefixes from frequent words
    prefix_groups = defaultdict(list)
    for word, count in word_freq.items():
        if len(word) >= 5 and count >= 3:
            prefix_groups[word[:2]].append((word, count))
            prefix_groups[word[:3]].append((word, count))

    # Score prefixes by how many distinct words they appear on
    prefix_data = []
    seen_prefixes = set()
    for prefix in sorted(prefix_groups.keys(), key=lambda p: -len(prefix_groups[p])):
        words_with = prefix_groups[prefix]
        if len(words_with) < 5:
            continue
        # Skip if a longer prefix of this already captured
        if any(prefix.startswith(s) and len(s) < len(prefix) for s in seen_prefixes):
            continue
        if any(s.startswith(prefix) and len(s) > len(prefix) and s in seen_prefixes for s in prefix_groups):
            continue

        total_uses = sum(c for _, c in words_with)
        distinct_words = len(set(w for w, _ in words_with))
        examples = sorted(set(w for w, _ in words_with), key=lambda w: -word_freq[w])[:8]

        prefix_data.append({
            "prefix": prefix,
            "distinct_words": distinct_words,
            "total_uses": total_uses,
            "examples": examples,
        })
        seen_prefixes.add(prefix)

    # Sort by distinct words
    prefix_data.sort(key=lambda x: -x["distinct_words"])

    # Try to identify singular/plural prefix pairs
    # Common Bantu pattern: mu-/ba- (cl1/2), mu-/mi- (cl3/4), etc.
    sg_pl_pairs = []
    prefix_set = {p["prefix"] for p in prefix_data[:30]}
    common_pairs = [
        ("mu", "ba"), ("mu", "mi"), ("ka", "tu"), ("lu", "ma"),
        ("ci", "fi"), ("bu", "ma"), ("ku", "ma"), ("um", "ab"),
        ("umu", "aba"), ("ici", "ifi"), ("ulu", "ama"), ("aka", "utu"),
        ("in", "im"), ("chi", "zi"), ("li", "ma"), ("si", "li"),
    ]
    for sg, pl in common_pairs:
        if sg in prefix_set or pl in prefix_set:
            sg_words = [w for w, _ in prefix_groups.get(sg, [])][:3]
            pl_words = [w for w, _ in prefix_groups.get(pl, [])][:3]
            if sg_words and pl_words:
                sg_pl_pairs.append({
                    "singular_prefix": sg,
                    "plural_prefix": pl,
                    "singular_examples": sg_words,
                    "plural_examples": pl_words,
                })

    return {
        "prefixes": prefix_data[:25],
        "noun_class_pairs": sg_pl_pairs[:10],
    }


def analyze_verb_morphology(conn, lang):
    """
    Analyze verb patterns by finding how the same concept is expressed
    in different tenses/persons across parallel data.
    """
    pairs = get_parallel_pairs(conn, lang, 15000)

    # Group by English tense patterns
    tense_patterns = {
        "present": [],
        "past": [],
        "future": [],
        "imperative": [],
        "negative": [],
        "progressive": [],
    }

    for en, tgt in pairs:
        en_lower = en.lower()
        tgt_words = tokenize(tgt)
        if not tgt_words:
            continue

        if " is " in en_lower or " are " in en_lower or " am " in en_lower:
            tense_patterns["present"].extend(tgt_words)
        if " was " in en_lower or " were " in en_lower or " did " in en_lower:
            tense_patterns["past"].extend(tgt_words)
        if " will " in en_lower or " shall " in en_lower:
            tense_patterns["future"].extend(tgt_words)
        if en.strip().endswith("!") and len(en.split()) < 8:
            tense_patterns["imperative"].extend(tgt_words)
        if " not " in en_lower or "don't" in en_lower or "didn't" in en_lower:
            tense_patterns["negative"].extend(tgt_words)
        if "ing " in en_lower or en_lower.endswith("ing") or en_lower.endswith("ing."):
            tense_patterns["progressive"].extend(tgt_words)

    # For each tense, find distinctive prefixes/suffixes
    all_words = []
    for words in tense_patterns.values():
        all_words.extend(words)
    all_freq = Counter(all_words)

    tense_markers = {}
    for tense, words in tense_patterns.items():
        if len(words) < 50:
            continue
        tense_freq = Counter(words)

        # Find prefixes that are overrepresented in this tense
        prefix_score = defaultdict(float)
        for word, count in tense_freq.items():
            if len(word) >= 4 and count >= 3:
                for plen in [2, 3]:
                    prefix = word[:plen]
                    # Compare frequency in this tense vs overall
                    tense_rate = count / len(words)
                    overall_rate = all_freq.get(word, 1) / max(len(all_words), 1)
                    if overall_rate > 0:
                        ratio = tense_rate / overall_rate
                        if ratio > 1.5:
                            prefix_score[prefix] = max(prefix_score[prefix], ratio)

        # Also look at suffixes
        suffix_score = defaultdict(float)
        for word, count in tense_freq.items():
            if len(word) >= 4 and count >= 3:
                for slen in [2, 3]:
                    suffix = word[-slen:]
                    tense_rate = count / len(words)
                    overall_rate = all_freq.get(word, 1) / max(len(all_words), 1)
                    if overall_rate > 0:
                        ratio = tense_rate / overall_rate
                        if ratio > 1.5:
                            suffix_score[suffix] = max(suffix_score[suffix], ratio)

        top_prefixes = sorted(prefix_score.items(), key=lambda x: -x[1])[:5]
        top_suffixes = sorted(suffix_score.items(), key=lambda x: -x[1])[:5]

        # Example sentences for this tense
        examples = []
        for en, tgt in pairs[:5000]:
            en_lower = en.lower()
            matches = False
            if tense == "present" and (" is " in en_lower or " are " in en_lower):
                matches = True
            elif tense == "past" and (" was " in en_lower or " were " in en_lower):
                matches = True
            elif tense == "future" and " will " in en_lower:
                matches = True
            elif tense == "negative" and " not " in en_lower:
                matches = True

            if matches and len(examples) < 3 and len(en) < 80:
                examples.append({"english": en, "translation": tgt})

        tense_markers[tense] = {
            "word_count": len(words),
            "likely_prefixes": [{"marker": p, "score": round(s, 1)} for p, s in top_prefixes],
            "likely_suffixes": [{"marker": s, "score": round(sc, 1)} for s, sc in top_suffixes],
            "examples": examples,
        }

    return tense_markers


def analyze_pronouns(conn, lang):
    """
    Find pronoun equivalents by looking at sentences starting with
    I/you/he/she/we/they and comparing the first word of the translation.
    """
    pronoun_map = {}
    en_pronouns = {
        "i ": "1sg", "you ": "2sg", "he ": "3sg_m", "she ": "3sg_f",
        "we ": "1pl", "they ": "3pl", "it ": "3sg_n",
    }

    pairs = get_parallel_pairs(conn, lang, 20000)

    for pronoun, label in en_pronouns.items():
        candidates = Counter()
        for en, tgt in pairs:
            if en.lower().startswith(pronoun) and len(en.split()) < 12:
                tgt_words = tokenize(tgt)
                if tgt_words:
                    # The first word often contains the subject marker
                    candidates[tgt_words[0]] += 1
                    if len(tgt_words[0]) >= 3:
                        candidates[tgt_words[0][:2]] += 1

        top = candidates.most_common(5)
        if top:
            pronoun_map[label] = {
                "english": pronoun.strip(),
                "candidates": [{"form": w, "count": c} for w, c in top],
            }

    return pronoun_map


def analyze_word_order(conn, lang):
    """Analyze word order by comparing sentence structures."""
    pairs = get_parallel_pairs(conn, lang, 10000)

    # Length ratios
    ratios = []
    for en, tgt in pairs:
        en_words = len(en.split())
        tgt_words = len(tgt.split())
        if en_words > 2:
            ratios.append(tgt_words / en_words)

    avg_ratio = sum(ratios) / max(len(ratios), 1)

    # Find sentences where word order clearly differs
    # (question inversion, verb position, etc.)
    question_examples = []
    statement_examples = []
    for en, tgt in pairs:
        if en.strip().endswith("?") and len(en.split()) < 10 and len(question_examples) < 5:
            question_examples.append({"english": en, "translation": tgt})
        elif en.strip().endswith(".") and 5 < len(en.split()) < 10 and len(statement_examples) < 5:
            statement_examples.append({"english": en, "translation": tgt})

    return {
        "avg_word_ratio": round(avg_ratio, 2),
        "description": "more concise" if avg_ratio < 0.85 else "similar length" if avg_ratio < 1.15 else "more verbose",
        "sample_size": len(ratios),
        "question_examples": question_examples,
        "statement_examples": statement_examples,
    }


def analyze_negation(conn, lang):
    """Find negation markers by comparing positive vs negative sentences."""
    pairs = get_parallel_pairs(conn, lang, 15000)

    neg_words = Counter()
    pos_words = Counter()

    for en, tgt in pairs:
        tgt_tokens = tokenize(tgt)
        if " not " in en.lower() or "don't" in en.lower() or "didn't" in en.lower() or "cannot" in en.lower():
            neg_words.update(tgt_tokens)
        else:
            pos_words.update(tgt_tokens)

    # Words that appear much more in negative than positive sentences
    neg_markers = []
    for word, neg_count in neg_words.most_common(100):
        pos_count = pos_words.get(word, 0)
        if neg_count >= 5:
            ratio = neg_count / max(pos_count, 1) * (len(pos_words) / max(len(neg_words), 1))
            if ratio > 3:
                neg_markers.append({
                    "marker": word,
                    "neg_count": neg_count,
                    "pos_count": pos_count,
                    "ratio": round(ratio, 1),
                })

    neg_markers.sort(key=lambda x: -x["ratio"])

    # Example negative sentences
    examples = []
    for en, tgt in pairs:
        if (" not " in en.lower() or "don't" in en.lower()) and len(examples) < 4 and len(en) < 80:
            examples.append({"english": en, "translation": tgt})

    return {
        "likely_markers": neg_markers[:8],
        "examples": examples,
    }


def analyze_shared_roots(conn):
    """Find cognates — words shared across multiple languages."""
    lang_words = {}
    for lang in LANGUAGES:
        words = set()
        for r in conn.execute(
            "SELECT text FROM translations WHERE language = ? LIMIT 20000", (lang,)
        ):
            for w in tokenize(r[0]):
                if len(w) >= 4:
                    words.add(w)
        lang_words[lang] = words

    # Find words in 3+ languages
    all_words = set()
    for words in lang_words.values():
        all_words.update(words)

    cognates = []
    for word in all_words:
        present_in = [lang for lang, words in lang_words.items() if word in words]
        if len(present_in) >= 3:
            cognates.append({
                "word": word,
                "languages": sorted(present_in),
                "count": len(present_in),
            })

    cognates.sort(key=lambda x: (-x["count"], x["word"]))

    # Group by number of languages
    by_count = defaultdict(int)
    for c in cognates:
        by_count[c["count"]] += 1

    return {
        "cognates": cognates[:300],
        "summary": {f"{k}_languages": v for k, v in sorted(by_count.items(), reverse=True)},
    }


def analyze_number_system(conn, lang):
    """Find number words by aligning with English numbers."""
    pairs = get_parallel_pairs(conn, lang, 30000)

    number_words = {}
    en_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "twelve": 12, "twenty": 20, "hundred": 100, "thousand": 1000,
        "first": "1st", "second": "2nd", "third": "3rd",
    }

    for en, tgt in pairs:
        en_words_lower = en.lower().split()
        tgt_words = tokenize(tgt)
        for en_num, value in en_numbers.items():
            if en_num in en_words_lower and len(en_words_lower) < 8:
                # The target word at roughly the same position might be the number
                for tw in tgt_words:
                    if tw not in number_words.get(str(value), {}).get("candidates", {}):
                        if str(value) not in number_words:
                            number_words[str(value)] = {"english": en_num, "candidates": Counter()}
                        number_words[str(value)]["candidates"][tw] += 1

    # Pick best candidate for each number
    result = []
    for value, data in sorted(number_words.items(), key=lambda x: str(x[0]).zfill(10)):
        top = data["candidates"].most_common(3)
        if top:
            result.append({
                "value": value,
                "english": data["english"],
                "candidates": [{"word": w, "count": c} for w, c in top],
            })

    return result


def main():
    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 60)
    print("COMPREHENSIVE GRAMMAR ANALYSIS")
    print("=" * 60)

    grammar = {"languages": {}}

    for lang in LANGUAGES:
        print(f"\n{'=' * 40}")
        print(f"  {lang.upper()} ({LANG_NAMES[lang]})")
        print(f"{'=' * 40}")

        lang_data = {"name": LANG_NAMES[lang]}

        print("  Noun classes...")
        lang_data["noun_classes"] = analyze_noun_classes(conn, lang)

        print("  Verb morphology...")
        lang_data["verb_morphology"] = analyze_verb_morphology(conn, lang)

        print("  Pronouns...")
        lang_data["pronouns"] = analyze_pronouns(conn, lang)

        print("  Word order...")
        lang_data["word_order"] = analyze_word_order(conn, lang)

        print("  Negation...")
        lang_data["negation"] = analyze_negation(conn, lang)

        print("  Number system...")
        lang_data["numbers"] = analyze_number_system(conn, lang)

        grammar["languages"][lang] = lang_data

    print(f"\n{'=' * 40}")
    print("  CROSS-LANGUAGE")
    print(f"{'=' * 40}")
    print("  Shared roots / cognates...")
    grammar["shared_roots"] = analyze_shared_roots(conn)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "grammar.json").write_text(
        json.dumps(grammar, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nExported to {OUT / 'grammar.json'}")
    for lang in LANGUAGES:
        ld = grammar["languages"][lang]
        print(f"  {lang}: {len(ld['noun_classes']['prefixes'])} prefixes, "
              f"{len(ld['verb_morphology'])} tenses, "
              f"{len(ld['pronouns'])} pronouns, "
              f"{len(ld['numbers'])} numbers")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
