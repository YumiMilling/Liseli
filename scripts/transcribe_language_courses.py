"""
Strategic transcription of YouTube language courses using OpenAI Whisper API.

Key insight: Whisper needs a context prompt to handle code-switched content
(English + Zambian language). We use the video title and known vocabulary
to guide transcription so it doesn't produce nonsense.

Cost: ~$0.006/min. $7 budget = ~1,167 minutes of audio.
"""
import os
import json
import time
import ssl
import urllib.request
import yt_dlp
from pathlib import Path

os.environ["PATH"] = (
    r"C:\Users\chlin\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1-full_build\bin"
    + ";"
    + os.environ["PATH"]
)

API_KEY = open(".env.local").read().split("OPENAI_API_KEY=")[1].strip()

BASE_DIR = Path("data/language-courses")
BASE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SOURCES — each source has a language context prompt that tells
# Whisper what to expect. This is critical for getting usable
# transcriptions instead of garbage.
# ============================================================

SOURCES = {
    "chichewa-101": {
        "description": "Chichewa 101 — bilingual English/Chinyanja lessons by hkatsonga",
        "language": "en",  # primary language for Whisper (instruction is in English)
        "target_lang": "nya",
        "prompt": (
            "This is a Chichewa language lesson. The instructor speaks English "
            "and teaches Chichewa (Chinyanja) words and phrases. "
            "Common Chichewa words: moni (hello), zikomo (thank you), "
            "inde (yes), ayi (no), bwanji (how), chabwino (fine/good), "
            "nyumba (house), madzi (water), chakudya (food), ana (children), "
            "bwera (come), pita (go), konda (love), funa (want), "
            "mwana (child), bambo (father), mayi (mother), "
            "dzina (name), sukulu (school), msika (market), "
            "kwathu (our home), ndikufuna (I want), ndimakonda (I love), "
            "kodi (question marker), ndi (is/am), "
            "mtengo (tree/price), njira (road/path), "
            "munthu (person), anthu (people), dziko (country/land). "
            "Lesson numbers and greetings are mixed English and Chichewa."
        ),
        "videos": [
            ("1zcHNxbeltQ", "Chichewa 101.01 - learning to speak Chichewa"),
            ("zKiBbpY_rVo", "Chichewa 101.02 - learning to speak Chichewa"),
            ("Kq-cdTrurJ0", "Chichewa 101.03 - learning to speak Chichewa"),
            ("wSe-hpKaQMY", "Chichewa 101.04 - learning to speak Chichewa"),
            ("bEGJ2hV6T9o", "Chichewa 101.05 - learning to speak Chichewa"),
            ("uNE_znhZPdg", "Chichewa 101.06 - learning to speak Chichewa"),
            ("NKBih9TSw74", "Chichewa 101.07 - learning to speak Chichewa"),
            ("WZBuW1hxaks", "Chichewa 101.08 - learning to speak Chichewa"),
            ("EKuBXtEUHoo", "Chichewa 101.09 - learning to speak Chichewa"),
            ("Q6H38TwYA6o", "Chichewa 101.10 - learning to speak Chichewa"),
            ("0l6hR_7xFyo", "Chichewa 101.11 - learning to speak Chichewa"),
            ("kcwJrq0p3lc", "Chichewa 101.12 - learning to speak Chichewa"),
            ("8jWp5K7FO6A", "Chichewa 101.13 - learning to speak Chichewa"),
            ("qwx_n4L2xgg", "Chichewa 101.14 - learning to speak Chichewa"),
            ("09n0skR_-4Q", "Chichewa 101.15 - learning to speak Chichewa"),
            ("qpi4A5BIb7k", "Chichewa 101.16 - learning to speak Chichewa"),
            ("rbEOJczFHB0", "Chichewa 101.17 - learning to speak Chichewa"),
            ("_NdGXX-gZpM", "Chichewa 101.18 - learning to speak Chichewa"),
            ("EUvJ2LTkjhk", "Chichewa 101.19 - learning to speak Chichewa"),
            ("GqOusxbn_Fs", "Chichewa 101.20 - learning to speak Chichewa"),
            ("qt0Tqp6JG5M", "Chichewa 101.21 - learning to speak Chichewa"),
            ("AJmpulnEKzA", "Chichewa 101.22 - learning to speak Chichewa"),
            ("9m6lseso1mk", "Chichewa 101.23 - learning to speak Chichewa"),
            ("Smjyi0PnbWo", "Chichewa 101.24 - learning to speak Chichewa"),
            ("Yp6MgcFXzLk", "Chichewa 101 - Quiz 1 - learning to speak Chichewa"),
        ],
    },
    "learn-bemba": {
        "description": "Learn Bemba channel — vocabulary, phrases, body parts, everyday words",
        "language": "en",
        "target_lang": "bem",
        "prompt": (
            "This is a Bemba (Icibemba) language lesson. The instructor speaks English "
            "and teaches Bemba vocabulary and phrases. "
            "Common Bemba words: mulishani (how are you), eya (yes), awe (no), "
            "natotela (thank you), ine (I/me), iwe (you), umwana (child), "
            "abana (children), bashi (father), bama (mother), "
            "inshiku (days), amenshi (water), ifya kulya (food), "
            "ukwimba (to sing), ukubomba (to work), ukuya (to go), "
            "umutwe (head), amolu (legs), iminwe (fingers), "
            "umushi (village), ing'anda (house), icibemba (Bemba language), "
            "imiti (trees), insoka (snake), imbwa (dog), "
            "ukufunda (to read), ukusambilila (to learn), "
            "ulushiku (day), ubushiku (night), icungulo (evening)."
        ),
        "videos": [
            ("fSlBUBIsnZE", "75 Bemba Words for Everyday Life"),
            ("iBHqM1ry2DY", "12 Bemba Words For Everyday Life"),
            ("cM3lkCq4YLc", "I am sentences in Bemba"),
            ("jYLD-dHr45Y", "15 easy words in Bemba"),
            ("dQ6_vokHxDI", "Bemba Lesson 2 - CLOTHES in Bemba"),
            ("yNAkFOnoEoo", "Bemba Made Easy"),
            ("7IdErESCXk0", "Phone conversation in Bemba"),
            ("MQwLXIPeOH0", "The Body Parts in Bemba"),
            ("8_mGTZk_B0M", "Nature Vocabulary in Bemba"),
            ("gMiFJN5-umE", "How to say Rain in Bemba"),
            ("l1D3_ZGd3D0", "Learn Colors in Bemba"),
            ("WBITypK4I_4", "Lets count 1 to 70 in Bemba"),
            ("n4Bm8VythvA", "How to say Im going to work in Bemba"),
            ("H_mMTjl4QUU", "How to say I woke up early in the morning in Bemba"),
        ],
    },
    "kitwe-online-bemba": {
        "description": "KitweOnline — structured Bemba lessons, directions, self-intro",
        "language": "en",
        "target_lang": "bem",
        "prompt": (
            "This is a structured Bemba language lesson from KitweOnline. "
            "The instructor teaches Bemba vocabulary, pronunciation, and phrases. "
            "Common Bemba words: mulishani (how are you), mwabombeni (how are you doing), "
            "eya (yes), awe (no), natotela (thank you), "
            "ishina lyandi (my name is), ndefuma ku (I come from), "
            "ukuya (to go), ukwisa (to come), ukufunda (to read), "
            "pa (on/at), mu (in), ku (to/from), "
            "umutwe (head), amolu (legs), umunwe (finger), "
            "icilila (direction), ulwelelo (right), ulubali (side)."
        ),
        "videos": [
            ("jnNhwJ3Ih_s", "Learn to Read and Pronounce Bemba Words"),
            ("qnVYwSTDUbc", "Bemba Lesson 12 Self Introduction"),
            ("x4tmjtjuhb0", "33 Bemba Lesson - The Head - Umutwe 2023"),
            ("RnGkyhNyPsk", "38-How to Ask for Directions in Bemba"),
            ("z0iHJr0DscE", "Learn Bemba With Mulenga - My Week"),
        ],
    },
    "bemblin": {
        "description": "Bemblin — Bemba greetings, alphabet, counting",
        "language": "en",
        "target_lang": "bem",
        "prompt": (
            "This is a Bemba language lesson. The instructor teaches Bemba "
            "greetings, the alphabet, and counting. "
            "Bemba greetings: mulishani (how are you), mwabombeni, "
            "eya (yes), awe (no), natotela (thank you), shani (fine), "
            "Bemba numbers: cimo (1), fibili (2), fitatu (3), fine (4), "
            "fisano (5), mutanda (6), cine lubali (7), cine konse (8), "
            "pabula (9), ikumi (10). "
            "Alphabet and pronunciation of Bemba letters and sounds."
        ),
        "videos": [
            ("hK-7cHa69lk", "Bemba Greetings"),
            ("itRWkSBaPm8", "Bemba Alphabet System and Pronunciations Lesson 2"),
            ("gpMyp5EkJ0k", "Bemba Numbers and Counting Lesson 3"),
        ],
    },
    "kaputu-bemba": {
        "description": "KAPUTU BEMBA LESSONS — structured Bemba teaching",
        "language": "en",
        "target_lang": "bem",
        "prompt": (
            "This is a Bemba (Icibemba) language lesson by Kaputu. "
            "The instructor teaches Bemba vocabulary, grammar, and everyday phrases. "
            "Common Bemba: mulishani, natotela, eya, awe, ishina lyandi, "
            "ukubomba (to work), ukuya (to go), ukwisa (to come), "
            "ing'anda (house), umushi (village), icibemba."
        ),
        "videos": [
            ("yyuJdToZ9xo", "kaputu bemba teacher lesson 1"),
            ("7GNrS2pvMR0", "KAPUTU BEMBA TEACHER INTRO"),
        ],
    },
    "zambian-american-nyanja": {
        "description": "ZambianAmerican — Nyanja 101 series: phrases, shopping, travel, business",
        "language": "en",
        "target_lang": "nya",
        "prompt": (
            "This is a Nyanja (Chinyanja) language lesson for English speakers. "
            "The instructor teaches practical Nyanja for everyday situations. "
            "Common Nyanja: moni (hello), muli bwanji (how are you), "
            "ndili bwino (I am fine), zikomo (thank you), "
            "inde (yes), ayi (no), kodi (question word), "
            "ndikufuna (I want), bwanji (how much), "
            "nyumba (house), msika (market), sukulu (school), "
            "kudya (to eat), kumwa (to drink), kugula (to buy), "
            "ndalama (money), chitenje (cloth), malaya (clothes), "
            "galimoto (car), ndege (airplane), hotelo (hotel)."
        ),
        "videos": [
            ("rRO3gqGX8IQ", "Learn Nyanja 101 - Basic Phrases"),
            ("0fORE5Z0MmA", "Learn Nyanja 101 - Shopping"),
            ("s2xK_GMW16o", "Learn Nyanja 101 - Describing People"),
            ("pSguYvdDRn8", "Learn Nyanja 101 - Hotels and Travel"),
            ("gAc6jEbXg6w", "Learn Nyanja for Business / Work"),
        ],
    },
    "its-alice-nyanja": {
        "description": "Its Alice — Nyanja lessons, body parts, shopping phrases, sentences",
        "language": "en",
        "target_lang": "nya",
        "prompt": (
            "This is a Nyanja (Chinyanja) lesson by a Zambian creator. "
            "She teaches everyday Nyanja vocabulary and phrases. "
            "Common Nyanja: moni, zikomo, ndikufuna, bwanji, "
            "mwana (child), mayi (mother), bambo (father), "
            "thupi (body), mutu (head), manja (hands), miyendo (legs), "
            "msika (market), zinthu (things), nyumba (house), "
            "madzi (water), chakudya (food), nsomba (fish)."
        ),
        "videos": [
            ("C5braMM1U10", "Lets learn Nyanja part 1"),
            ("zlGpHftNW1Y", "Lets learn Nyanja part 2"),
            ("g1gHh7xmzUc", "Nyanja lesson 4"),
            ("I4hh5QRHmss", "Nyanja sentences"),
            ("ihAtAVom2sI", "Useful Nyanja phrases used when shopping"),
            ("7C9SXOuX8hM", "body parts vocabulary Nyanja"),
            ("Dvb84JB-PXw", "things around us in Nyanja"),
            ("OYgJ234jeVw", "Body care vocabulary Nyanja"),
            ("aDu-K6ctK_g", "Nyanja lessons part 6"),
        ],
    },
    "zedlexicon-tonga": {
        "description": "ZedLexicon — Chitonga reading, writing, vocabulary",
        "language": "en",
        "target_lang": "toi",
        "prompt": (
            "This is a Chitonga (Tonga) language lesson. The instructor teaches "
            "reading, writing, and vocabulary in Chitonga. "
            "Chitonga vowels: a e i o u. Consonant-vowel pairs are taught. "
            "Common Chitonga: ndakuyanda (I love you), boola kuno (come here), "
            "musimbi (girl), mulombe (boy), "
            "mutalika (teacher), bbuku (book), "
            "kuyanda (to love), kubala (to read), kulemba (to write), "
            "ulibuti (how are you), kabotu (fine/good), "
            "mulonga (river), muunzi (village), ng'anda (house)."
        ),
        "videos": [
            ("tvRAYpdL_3w", "Writing Chitonga Lesson 1 The English Alphabet"),
            ("u2DPVKu8ruU", "Reading Chitonga Lesson 1 Vowels"),
            ("5TqahFeoTOQ", "Reading Chitonga Lesson 2 Consonant and Vowel"),
            ("u1x6iEOZLy4", "Reading Chitonga Lesson 3 Simple Method"),
            ("kATg3_izYjg", "How to say girl in chitonga Musimbi"),
            ("j6SQyi7SCfU", "How to say Come here in Chitonga"),
            ("1ttkwc8ZcwY", "How to say I Love You in Chitonga Ndakuyanda"),
        ],
    },
    "learn-tonga-nyanja": {
        "description": "Learn Tonga and Nyanja — bilingual Tonga/Nyanja vocabulary",
        "language": "en",
        "target_lang": "toi",
        "prompt": (
            "This is a Chitonga (Tonga) language lesson. The creator teaches "
            "Tonga vocabulary, counting, greetings, and everyday phrases. "
            "Common Chitonga: ulibuti (how are you), kabotu (fine), "
            "ndakuyanda (I love you), boola kuno (come here), "
            "omwe (1), obile (2), otatwe (3), one (4), osanwe (5), "
            "musimbi (girl), mulombe (boy), muunzi (village)."
        ),
        "videos": [
            ("Q-zTJAuObbw", "LEARN CHITONGA Part 1"),
            ("KTulJqS7FxE", "LEARN TONGA CHITONGA"),
            ("30U8J5Z3ZWQ", "HOW TO GREET IN TONGA CHITONGA"),
            ("BOK9LwlvinI", "Learn Chitonga"),
            ("tAyJhNyeGjk", "LEARN TONGA CHITONGA Numbers counting"),
            ("pBlvSU4A1H0", "POSITIONS IN CHITONGA"),
            ("1x2vtzfcpxA", "LEARN TONGA CHITONGA Part 4 Name of Months"),
            ("5YXEVKJuosI", "Daily Nyanja Part 1"),
        ],
    },
    "say-it-chichewa": {
        "description": "Say It In Chichewa — tourist/beginner Chichewa lessons",
        "language": "en",
        "target_lang": "nya",
        "prompt": (
            "This is a Chichewa (Nyanja) lesson for tourists and beginners. "
            "The instructor teaches basic Chichewa greetings and phrases. "
            "Common Chichewa: moni (hello), muli bwanji (how are you), "
            "ndili bwino (I am fine), zikomo (thank you), "
            "inde (yes), ayi (no), palibe (nothing/no), "
            "ndikufuna (I want), ndikhoza (I can), "
            "nyumba (house), madzi (water), chakudya (food)."
        ),
        "videos": [
            ("5AA00Ma07TI", "Learn Chichewa Language For Tourists and beginners"),
            ("vIwvBKHqD4g", "Learn Chichewa Language For Tourists and beginners 2"),
        ],
    },
}


def download_audio(video_id, output_path):
    """Download audio only as mp3."""
    if output_path.exists() and output_path.stat().st_size > 1000:
        return True

    ydl_opts = {
        "format": "worstaudio",
        "outtmpl": str(output_path).replace(".mp3", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "ffmpeg_location": (
            r"C:\Users\chlin\AppData\Local\Microsoft\WinGet\Packages"
            r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
            r"\ffmpeg-8.1-full_build\bin"
        ),
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://youtube.com/watch?v={video_id}"])
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def transcribe_with_api(audio_path, language="en", prompt=""):
    """
    Send to OpenAI Whisper API with strategic prompting.

    The prompt parameter is KEY — it tells Whisper what vocabulary and
    language patterns to expect. Without it, Zambian language words
    get mangled into nonsense English.

    Args:
        audio_path: path to audio file
        language: ISO 639-1 code for primary language ('en' for English-medium lessons)
        prompt: context prompt with expected vocabulary and language description
    """
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(audio_path)

    with open(audio_path, "rb") as f:
        file_data = f.read()

    # Build multipart form data
    parts = []

    # Model
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
    )

    # Response format — verbose JSON with timestamps
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'
    )

    # Timestamp granularity
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\nsegment\r\n'
    )

    # Language hint — tells Whisper the primary language
    if language:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="language"\r\n\r\n{language}\r\n'
        )

    # THE KEY PART: context prompt with vocabulary hints
    if prompt:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="prompt"\r\n\r\n{prompt}\r\n'
        )

    # Audio file
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    )

    body = "".join(parts).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
    result = json.loads(resp.read().decode("utf-8"))

    segments = []
    for seg in result.get("segments", []):
        segments.append(
            {
                "start": round(seg["start"], 1),
                "end": round(seg["end"], 1),
                "text": seg["text"].strip(),
            }
        )

    return {
        "language": result.get("language", "unknown"),
        "text": result.get("text", ""),
        "segments": segments,
    }


def build_video_prompt(source_config, video_title):
    """
    Build a per-video prompt by combining the source-level prompt
    with flywheel-generated vocabulary hints and video title context.

    The flywheel generates data/whisper-prompts/<lang>.txt with known
    vocabulary from previous transcription runs. Each run gets smarter.
    """
    base = source_config["prompt"]
    title_context = f' The video title is: "{video_title}".'

    # Try to augment with flywheel-generated prompt (known vocabulary)
    target_lang = source_config.get("target_lang", "")
    flywheel_prompt_path = Path("data/whisper-prompts") / f"{target_lang}.txt"
    if flywheel_prompt_path.exists():
        flywheel_vocab = flywheel_prompt_path.read_text(encoding="utf-8")
        # Whisper prompt limit is ~224 tokens, so be selective
        # Take the flywheel vocab list (after "Common X words that may appear:")
        # and append the most distinctive words
        if "words that may appear:" in flywheel_vocab:
            vocab_part = flywheel_vocab.split("words that may appear:")[1]
            vocab_part = vocab_part.split(".")[0]  # up to first period
            # Trim to fit within limits alongside base prompt
            max_vocab = 500 - len(base) - len(title_context)
            if max_vocab > 50:
                base += f" Additional known vocabulary: {vocab_part[:max_vocab]}."

    return base + title_context


def discover_playlist(url):
    """
    Utility: extract video IDs and titles from a YouTube playlist URL.
    Run this to populate a new source's video list.

    Usage:
        python -c "from transcribe_language_courses import *; discover_playlist('https://...')"
    """
    ydl_opts = {"extract_flat": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = list(info.get("entries", []))
    print(f"Found {len(entries)} videos:")
    total_dur = 0
    for e in entries:
        d = e.get("duration") or 0
        total_dur += d
        vid_id = e.get("id", "?")
        title = e.get("title", "?")
        print(f'            ("{vid_id}", "{title}"),')
    print(f"\nTotal: {total_dur}s = {total_dur / 60:.0f} min")
    print(f"Estimated cost: ${total_dur / 60 * 0.006:.2f}")


def transcribe_source(source_key, skip_existing=True):
    """Transcribe all videos in a single source."""
    source = SOURCES[source_key]
    videos = source["videos"]
    language = source.get("language", "en")

    out_dir = BASE_DIR / source_key
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"SOURCE: {source['description']}")
    print(f"Videos: {len(videos)} | Language: {language}")
    print(f"Target: {source.get('target_lang', '?')}")
    print("=" * 60)

    all_results = {}
    total_cost = 0
    skipped = 0

    # Load existing results if any
    results_file = out_dir / "transcripts.json"
    if results_file.exists():
        all_results = json.loads(results_file.read_text(encoding="utf-8"))

    for vid_id, title in videos:
        # Skip already transcribed
        if skip_existing and vid_id in all_results:
            skipped += 1
            continue

        print(f"\n  [{vid_id}] {title}")
        audio_path = AUDIO_DIR / f"{source_key}_{vid_id}.mp3"

        # Download
        if not download_audio(vid_id, audio_path):
            continue

        if not audio_path.exists():
            for ext in [".mp3", ".m4a", ".webm", ".wav"]:
                alt = AUDIO_DIR / f"{source_key}_{vid_id}{ext}"
                if alt.exists():
                    audio_path = alt
                    break

        if not audio_path.exists():
            print("    No audio file found")
            continue

        size_mb = audio_path.stat().st_size / 1024 / 1024
        print(f"    Audio: {size_mb:.1f} MB")

        # Build strategic prompt for this specific video
        prompt = build_video_prompt(source, title)

        # Transcribe
        try:
            result = transcribe_with_api(audio_path, language=language, prompt=prompt)
            segments = result["segments"]
            detected = result["language"]
            print(f"    Detected: {detected} | Segments: {len(segments)}")

            # Cost estimate
            if segments:
                duration_min = segments[-1]["end"] / 60
                cost = duration_min * 0.006
                total_cost += cost
                print(f"    Duration: {duration_min:.1f} min | Cost: ${cost:.3f}")

            # Preview
            for seg in segments[:3]:
                print(f"    [{seg['start']:.0f}s] {seg['text'][:80]}")

            all_results[vid_id] = {
                "video_id": vid_id,
                "title": title,
                "source": source_key,
                "target_lang": source.get("target_lang", "?"),
                "url": f"https://youtube.com/watch?v={vid_id}",
                "detected_language": detected,
                "prompt_used": prompt[:200] + "...",
                "segments": segments,
                "full_text": result["text"],
            }

            # Save after each video (in case of crash)
            results_file.write_text(
                json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        except Exception as e:
            print(f"    API error: {e}")

        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"DONE: {source_key}")
    print(f"  Transcribed: {len(all_results) - skipped} new")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Total in file: {len(all_results)}")
    print(f"  Cost this run: ${total_cost:.2f}")
    print(f"  Saved to: {results_file}")

    return all_results


def transcribe_all(skip_existing=True):
    """Transcribe all sources."""
    grand_total = 0
    for key in SOURCES:
        results = transcribe_source(key, skip_existing=skip_existing)
        grand_total += len(results)
    print(f"\n{'=' * 60}")
    print(f"ALL SOURCES COMPLETE — {grand_total} total transcriptions")


def cost_estimate():
    """Estimate total cost for all untranscribed videos."""
    for key, source in SOURCES.items():
        results_file = BASE_DIR / key / "transcripts.json"
        existing = set()
        if results_file.exists():
            existing = set(json.loads(results_file.read_text(encoding="utf-8")).keys())

        remaining = [v for v in source["videos"] if v[0] not in existing]
        print(f"\n{key}: {len(remaining)} remaining / {len(source['videos'])} total")
        print(f"  {source['description']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "discover" and len(sys.argv) > 2:
            discover_playlist(sys.argv[2])
        elif cmd == "estimate":
            cost_estimate()
        elif cmd in SOURCES:
            transcribe_source(cmd)
        else:
            print(f"Unknown source: {cmd}")
            print(f"Available: {', '.join(SOURCES.keys())}")
            print("Or: python transcribe_language_courses.py discover <playlist_url>")
    else:
        transcribe_all()
