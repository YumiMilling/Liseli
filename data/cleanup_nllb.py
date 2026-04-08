"""
Cleanup script for liseli_local.db - removes nonsensical English sentences
from the opus-bem-nllb corpus and their associated translations.
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "liseli_local.db")

# Top ~3000 common English words (condensed set covering most usage)
COMMON_WORDS = set("""
a about above after again against all am an and any are as at be because been
before being below between both but by can could did do does doing down during
each few for from further get got had has have having he her here hers herself
him himself his how i if in into is it its itself just know let like make me
might more most my myself no nor not now of off on once only or other our ours
ourselves out over own put quite really right said same say says she should so
some still such take than that the their theirs them themselves then there these
they this those through to too under until up us very want was we were what when
where which while who whom why will with would yes yet you your yours yourself
yourselves able also always another ask away back bad been before began begin
best better big bring came change city close come could country day different
does each end even every face fact family feel find first follow found give go
going gone good great group hand help here high home house important keep kind
large last late left life little live long look man many may men might mind
money move much must name need never new next night nothing number off old
one open order own part people place play point put read right run same school
seem set show side since small something stand start state still stop story
study take tell think thought three time together too try turn two under
understand use very walk want watch water way well went were what when where
which while white whole why will without word work world would write year young
about above across after again age ago air all almost along already also always
among animal another answer any anything area around as ask at away back be
became because become bed been before began begin behind being believe below
beside best better between big black blue body book both bottom box boy bring
brought build built business busy but buy by call came can car care carry case
catch cause certain change child children church city class clear close cold
come complete contain could course cover cross cut dark day dead deal death
deep did die different direction do does dog done door down draw during each
early earth east eat eight else end enough even evening ever every example eye
face fall family far fast father feel feet few field fight fill final find fire
first fish five floor follow food foot for force form found four friend from
front full game gave get girl give glad go god gold gone good got great green
ground grow had half hand happen hard has have he head hear heart heavy help
her here high him hold home hope hot hour house how hundred hunt i idea if
important in inch inside instead interest into iron island it its just keep
kind king knew know land language large last late laugh lay lead learn leave
left less let letter life light like line list listen little live long look
lose lot love low machine made main make man many map mark matter may me mean
measure men met might mile mind miss money month moon more morning most mother
mountain mouth move mrs much music must my name near need never new next night
nine no north nose not note nothing notice now number of off often oh old on
once one only open or order other our out over own page pair paper part pass
past pattern people perhaps period person picture piece place plan plant play
please point poor possible power probably problem product pull put question
quite rain ran reach read ready real red remember rest rich ride right ring
river road rock room round run sad safe said same sat saw say sea second see
seem sentence set seven several shall she short should show side silver simple
since sing sit six size sleep small snow so some something sometimes son soon
south space special spring stand star start stay step still stood stop story
street strong study such sun sure system table take talk tell ten test than
thank that the their them then there these they thing think this those though
thought three through time to today together told too took top toward town
tree true turn two type under understand unit until up upon us use usual
valley very voice walk want war warm was wash watch water way we weather week
well went were west what wheel when where whether which while white who whole
why wide will wind window wish with without woman women wonder wood word work
world would year yes yet you young
able act add age ago agree air allow also animal answer appear area arm army
art ask at away baby ball bank base be beat beautiful bed behind believe
bird bit blood board boat bone born break brother brown burn buy by call
camp capital captain care carry cat catch caught century chance character
charge chief child choose church circle class clean clear climb clock
close clothe coat cold collect colony color common company compare complete
condition consider cook cool copy corner cost cotton count country cover
cow create cry current dance daughter dead dear decide deep degree
depend describe desert design develop dictionary die difficult dinner
direct discover distance divide doctor dollar done double doubt dream
dress drink drive drop dry ear early earn earth east edge education
effect egg eight electric else employ end enemy engine english enough
enter equal especially europe evening ever every exact example except
excite exercise expect experience experiment explain express face fail
fair fall family famous far farm father fear feed feel field fifteen
fight figure fill find finger finish fly follow food foot force foreign
forest forget form forward free fresh friend from front fruit full
future garden general gentle girl glad glass god gone govern grass gray
grew grow guard guess gun hair half hall hang happen happy hard hat hate
he hear heavy hello help high hill history hit hold hole holiday horse
hospital hot hotel house human hundred hurry hurt husband ice idea imagine
include increase industry information inside instead interest iron
island it joy jump keep key kill kind king knee knife know land large
last late laugh lay lead leaf learn least leave leg lend less lesson
letter library lie life lift light like likely line lip list little
live long look lord lose lot love luck lunch machine main make
manner many mark market master may me meal mean meet member men
middle might mile milk million mind minute miss mistake mix modern
moment money month moon more morning most mother mountain move
movie much music must my name narrow nation nature near necessary
neck need never news nine noise none nor normal north nose note
notice now number obey object ocean offer office often oil only
open operate opinion order other outside own pair paper parent
particular party pass past pay people perhaps period person pick
picture piece place plan plant plate play please pocket point
police poor popular position possible post pound power practice
prepare present president press pretty price prince private probably
problem produce program promise prove provide public pull purpose
push quarter question quickly quiet race rain raise ran rather reach
read ready real reason receive record red region remain remember
repeat reply report rest result return ride ring rise river road
roll room rule run safe sail sale salt save say school science
sea seat second see seem sell send sentence serve set settle seven
shake shall shape share she shine ship shoe shoot short shot should
shoulder shout show shut sick side sight sign silence silver similar
simple since sing sir sister sit situation six skill skin sleep
smell smile smoke soft soldier some son song soon sorry sort sound
south space speak special speed spend sport spread spring square
stage stand star start station stay step stick still stock stomach
stone stop store storm story strange street strong student study
stuff subject succeed such sudden suggest suit summer supply support
suppose sure surprise sweet swim system table tail take talk tall
taste teach team tell ten term test than that the themselves
thick thin thing think third this though thousand three throw thus
tie till time tiny to today together tomorrow tonight too top total
touch toward town trade train travel tree trouble true trust try
twelve twenty two ugly uncle under university unless until up upon
upper use valley visit voice wait walk wall want war warm wash
waste watch water wave way we wear weather week weight welcome well
west western what whatever wheel whether which while white who
whose wide wife wild will win wind window winter wire wise wish
with within without woman wonder word work world worry would
wrong wrote year yellow you young youth zero
""".split())

def is_garbage(text):
    """Return (True, reason) if text is garbage, else (False, '')."""

    # Strip whitespace
    text = text.strip()

    # 1. Length filters
    if len(text) < 8:
        return True, "too_short"
    if len(text) > 250:
        return True, "too_long"

    # 2. Spam patterns: URLs, emails, code
    if re.search(r'https?://', text, re.I):
        return True, "url"
    if re.search(r'\S+@\S+\.\S+', text):
        return True, "email"
    if re.search(r'[{}<>\\|]', text):
        return True, "code_chars"
    if re.search(r'\d{4,}', text) and not re.search(r'(18|19|20)\d{2}', text):
        return True, "long_numbers"

    # 3. Non-ASCII check (allow common punctuation and accented names)
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    if ascii_ratio < 0.85:
        return True, "non_ascii"

    # 4. All-caps or all-lowercase over 20 chars
    alpha_text = re.sub(r'[^a-zA-Z]', '', text)
    if len(alpha_text) > 20:
        if alpha_text == alpha_text.upper():
            return True, "all_caps"
        if alpha_text == alpha_text.lower() and len(text) > 30:
            return True, "all_lowercase"

    # 5. Word-level analysis
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if len(words) < 2:
        return True, "too_few_words"

    # 5a. Word repetition: any word 4+ times
    from collections import Counter
    word_counts = Counter(words)
    for word, count in word_counts.items():
        if count >= 4 and word not in {'the', 'a', 'and', 'of', 'to', 'i', 'in', 'is'}:
            return True, "word_repetition"
        if count >= 6:  # Even function words shouldn't repeat this much
            return True, "excessive_repetition"

    # 5b. 3+ consecutive single-letter words (except "I")
    if re.search(r'\b[a-hj-zA-HJ-Z]\b\s+\b[a-hj-zA-HJ-Z]\b\s+\b[a-hj-zA-HJ-Z]\b', text):
        return True, "consecutive_single_letters"

    # 5c. Function word ratio - if >70% function words, likely garbage
    function_words = {'the', 'a', 'an', 'and', 'or', 'but', 'of', 'to', 'in', 'on',
                      'at', 'for', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
                      'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
                      'does', 'did', 'will', 'would', 'could', 'should', 'may',
                      'might', 'shall', 'can', 'not', 'no', 'it', 'its', 'this',
                      'that', 'these', 'those'}
    if len(words) > 6:
        func_count = sum(1 for w in words if w in function_words)
        if func_count / len(words) > 0.70:
            return True, "too_many_function_words"

    # 5d. Common English word check: at least 50% should be recognized
    if len(words) >= 4:
        known = sum(1 for w in words if w.lower() in COMMON_WORDS)
        ratio = known / len(words)
        if ratio < 0.40:  # be slightly lenient (names, places OK)
            return True, "low_english_ratio"

    # 6. Incomplete/fragment patterns
    # Ends with ellipsis or dash (truncated)
    if text.rstrip().endswith('...') or text.rstrip().endswith('--'):
        return True, "truncated"

    # Starts with lowercase and no preceding context indicator
    if text[0].islower() and not text.startswith(('i ', "i'", 'e.g', 'i.e')):
        # Fragment starting mid-sentence
        if len(words) < 6:
            return True, "fragment_start"

    # 7. Excessive punctuation
    punct_count = sum(1 for c in text if c in '.,;:!?()[]"\'-')
    if len(text) > 10 and punct_count / len(text) > 0.3:
        return True, "excessive_punctuation"

    # 8. No verb heuristic for longer sentences
    if len(words) > 12:
        verb_indicators = {'is', 'are', 'was', 'were', 'be', 'been', 'being',
                          'have', 'has', 'had', 'do', 'does', 'did', 'will',
                          'would', 'could', 'should', 'may', 'might', 'shall',
                          'can', 'go', 'went', 'gone', 'come', 'came', 'make',
                          'made', 'take', 'took', 'give', 'gave', 'get', 'got',
                          'say', 'said', 'tell', 'told', 'know', 'knew', 'think',
                          'thought', 'see', 'saw', 'want', 'need', 'use', 'find',
                          'found', 'put', 'keep', 'let', 'begin', 'show', 'hear',
                          'play', 'run', 'move', 'live', 'believe', 'hold',
                          'bring', 'happen', 'write', 'provide', 'sit', 'stand',
                          'lose', 'pay', 'meet', 'include', 'continue', 'set',
                          'learn', 'change', 'lead', 'understand', 'watch',
                          'follow', 'stop', 'create', 'speak', 'read', 'allow',
                          'add', 'spend', 'grow', 'open', 'walk', 'win', 'offer',
                          'remember', 'love', 'consider', 'appear', 'buy', 'wait',
                          'serve', 'die', 'send', 'expect', 'build', 'stay',
                          'fall', 'cut', 'reach', 'kill', 'remain', 'pray',
                          'asked', 'answered', 'called', 'looked', 'turned',
                          'helped', 'started', 'tried', 'needed', 'wanted'}
        has_verb = any(w in verb_indicators for w in words)
        # Also check for -ed, -ing, -es endings
        if not has_verb:
            has_verb = any(w.endswith(('ed', 'ing', 'es')) and len(w) > 3 for w in words)
        if not has_verb:
            return True, "no_verb"

    # 9. Religious corpus specific: mostly numbers/references
    if re.match(r'^[\d:,;\s\-\.]+$', text):
        return True, "numbers_only"

    # 10. Sentence is just a title/heading (all title case, no verb, short)
    # Skip this - many valid sentences are short

    return False, ""


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Only process opus-bem-nllb entries
    cur.execute("""
        SELECT id, english FROM sentences
        WHERE concept_id LIKE 'opus-bem-nllb%'
    """)
    rows = cur.fetchall()
    print(f"Total opus-bem-nllb sentences to evaluate: {len(rows)}")

    to_delete = []  # (id, english, reason)
    kept = 0
    reason_counts = {}

    for sid, english in rows:
        is_bad, reason = is_garbage(english)
        if is_bad:
            to_delete.append((sid, english, reason))
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        else:
            kept += 1

    print(f"\n=== RESULTS ===")
    print(f"Flagged for deletion: {len(to_delete)}")
    print(f"Kept: {kept}")

    print(f"\n=== REASONS BREAKDOWN ===")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    print(f"\n=== 10 EXAMPLES OF DELETED ENTRIES ===")
    import random
    random.seed(42)
    samples = random.sample(to_delete, min(10, len(to_delete)))
    for sid, english, reason in samples:
        print(f"  [{reason}] {english!r}")

    # Now delete
    if to_delete:
        delete_ids = [t[0] for t in to_delete]

        # Delete translations first (foreign key reference)
        print(f"\nDeleting translations for {len(delete_ids)} sentences...")
        # Do in batches to avoid SQL variable limits
        batch_size = 500
        trans_deleted = 0
        sent_deleted = 0
        for i in range(0, len(delete_ids), batch_size):
            batch = delete_ids[i:i+batch_size]
            placeholders = ','.join('?' * len(batch))
            cur.execute(f"DELETE FROM translations WHERE sentence_id IN ({placeholders})", batch)
            trans_deleted += cur.rowcount
            cur.execute(f"DELETE FROM sentences WHERE id IN ({placeholders})", batch)
            sent_deleted += cur.rowcount

        conn.commit()
        print(f"Deleted {trans_deleted} translations")
        print(f"Deleted {sent_deleted} sentences")

    # Final counts
    cur.execute("SELECT COUNT(*) FROM sentences")
    print(f"\nFinal sentence count: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM translations")
    print(f"Final translation count: {cur.fetchone()[0]}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
