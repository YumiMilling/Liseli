"""
Whisper transcription pipeline for Zambian language YouTube videos.
Uses vocabulary prompts to bias Whisper toward target language words.
Downloads audio segments, transcribes, creates pre-fill data for community correction.
"""
import os
import json
import whisper
import yt_dlp
from pathlib import Path

# Set ffmpeg path
FFMPEG_DIR = r"C:\Users\chlin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
os.environ["PATH"] = FFMPEG_DIR + ";" + os.environ["PATH"]

OUT_DIR = Path("data/whisper-transcripts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Vocabulary prompts for each language — common words that bias Whisper
LANGUAGE_PROMPTS = {
    "bem": """Icibemba. Umulilo. Amenshi. Abafyashi. Umwana. Abantu. Ukubelenga.
Ukulanda. Ukumfwa. Ukwishiba. Ifitabo. Imbuto. Inkoko. Imbushi. Umushi.
Icalo. Ubushiku. Akasuba. Amano. Ukufunda. Isukulu. Umukashi. Umulume.
Abaana. Inshiku. Imiti. Icitabo. Ukwimba. Ilyashi. Abena. Kabili. Kanshi.
Nomba. Pantu. Elyo. Nangu. Eico. Mukwai. Natotela. Mwapoleni. Eya. Awe.
Ine. Iwe. Ifwe. Imwe. Ukwisa. Ukuya. Ukukwata. Ukulya. Ukuseka.""",

    "nya": """Chinyanja. Mwana. Munthu. Anthu. Nyumba. Madzi. Moto. Sukulu.
Buku. Nkhani. Mphunzitsi. Aphunzi. Kulemba. Kuwelenga. Kulankhula.
Kumvetsela. Mafunso. Mayankho. Zinthu. Citsanzo. Nchito. Makolo.
Bambo. Mayi. Abale. Dziko. Mudzi. Msika. Chakudya. Ndalama.
Ndine. Ndili. Muli. Ali. Tili. Bwino. Zikomo. Moni. Inde. Ayi.
Kupanga. Kufuna. Kudziwa. Kupita. Kubwela. Kugwira.""",

    "toi": """Chitonga. Muntu. Bantu. Anguzu. Bazyali. Mwana. Ng'anda. Maanzi.
Mulilo. Cikolo. Bbuku. Kwiiya. Kubala. Kubamba. Kwaamba. Kuteeleza.
Mibuzyo. Zyintu. Milimo. Nyika. Cisi. Musika. Cakulya. Mali.
Ndime. Ndili. Muli. Uli. Tuli. Kabotu. Ndatumba. Mwabonwa.""",

    "loz": """Silozi. Mutu. Batu. Bashemi. Mwana. Ndu. Mezi. Mulilo.
Sikolo. Buka. Kuituta. Kubala. Kubulela. Kuteeleza. Lipuzo. Lika.
Musebezi. Naha. Munzi. Musika. Sico. Masheleñi.
Ki na. Ki li. Mu li. U li. Lu li. Hande. Ni itumezi. Lumela.""",

    "kqn": """Kikaonde. Muntu. Bantu. Babyeji. Mwana. Nganda. Maanshi.
Mujilo. Shikolo. Buku. Kufunda. Kutanga. Kwamba. Kumvwa. Mepuzho.
Bintu. Milimo. Kyalo. Musumba. Byakulya. Ndalama.
Ame. Obe. Nji. Tu. Mu. Byo. Eyo. Ine.""",

    "lun": """Chilunda. Muntu. Antu. Mwana. Indi. Meya. Kesi.
Shikola. Mukanda. Kuta. Kutala. Kuhosha. Kutiyilila. Mazu.
Yuma. Idimu. Chizala. Kashili. Chachiwahi.
Ami. Eyi. Etu. Enu. Nawa. Chidi.""",

    "lue": """Luvale. Muntu. Vantu. Vatata. Mwana. Nganda. Meya. Kakahya.
Shikola. Mukanda. Kutanga. Kwoloka. Kuvuluka. Kutala. Mahelu.
Vyuma. Woma. Likuta. Kulya. Mashelenga.
Ami. Ove. Etu. Enu. Kanawa. Echi.""",
}

# Top videos to transcribe per language
TOP_VIDEOS = {
    "bem": [
        ("fSlBUBIsnZE", "75 Bemba Words for Everyday Life"),
        ("MI-i7fpkY6g", "Learn to Speak Bemba Lesson 1: Greetings"),
        ("z3xNCSxQYmA", "10 Kitchen items in Bemba"),
        ("tJdUA8pLtO4", "Quick way to learn basic Bemba"),
        ("IqFsFM6b9II", "116 Zambian Proverbs in Bemba"),
    ],
    "nya": [
        ("rRO3gqGX8IQ", "Learn Nyanja 101 - Basic Phrases"),
        ("C4CMHdS2ISM", "Learn Nyanja 101 - Going Places"),
        ("0fORE5Z0MmA", "Learn Nyanja 101 - Shopping"),
        ("s2xK_GMW16o", "Learn Nyanja 101 - Describing People"),
        ("ZJS5NZ0y1jM", "Nyanja sentences part 2"),
    ],
    "toi": [
        ("rb90s_E89WI", "Learn Tonga at Ubuntu Talks"),
        ("Q-zTJAuObbw", "Learn Chitonga Part 1"),
        ("30U8J5Z3ZWQ", "How to greet in Tonga"),
    ],
    "loz": [
        ("3jh-KtWvcs4", "Learn 5 Zambian Languages"),
        ("ig8BBSJoP5k", "Silozi Days of the Week"),
        ("je_Y8rJGS3Q", "Greetings in Silozi"),
    ],
    "kqn": [
        ("ruVgWhA2sO8", "Learn Kaonde 101"),
        ("ROUZSddvEsg", "Learn Kaonde Language in 5 mins"),
        ("0PiTpQfFQiI", "Animal Names in Kaonde"),
    ],
    "lun": [
        ("_Lj20RmT25k", "Lunda Numbers 1-10"),
        ("_BGg7C-8D0g", "LUNOS Lesson 13 - Lunda"),
        ("6z7NRdTentY", "LUNOS Lesson 24 - More Lunda words"),
    ],
    "lue": [
        ("GLXSLkFc2rM", "Basics to Luvale Language"),
        ("jKTKJGbJYVA", "Formal greetings in Luvale"),
        ("HgzJ86lUbak", "Luvale Counting 1-10"),
    ],
}


def download_audio(video_id, output_path, max_duration=300):
    """Download audio from YouTube video."""
    ydl_opts = {
        "format": "worstaudio",
        "outtmpl": str(output_path).replace(".wav", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "ffmpeg_location": FFMPEG_DIR,
        "quiet": True,
        "no_warnings": True,
    }
    if max_duration:
        ydl_opts["download_ranges"] = lambda info, ydl: [{"start_time": 0, "end_time": max_duration}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://youtube.com/watch?v={video_id}"])
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def transcribe_audio(audio_path, language_code, model):
    """Transcribe audio with language-specific vocabulary prompt."""
    prompt = LANGUAGE_PROMPTS.get(language_code, "")

    result = model.transcribe(
        str(audio_path),
        language=None,  # Let Whisper detect, prompt will bias it
        initial_prompt=prompt,
        word_timestamps=True,
    )

    # Build segments with timestamps
    segments = []
    for seg in result["segments"]:
        text = seg["text"].strip()
        if not text or len(text) < 2:
            continue
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": text,
            "detected_language": result.get("language", "unknown"),
        })

    return segments


def main():
    print("=" * 60)
    print("WHISPER TRANSCRIPTION PIPELINE")
    print("=" * 60)

    print("\nLoading Whisper base model...")
    model = whisper.load_model("base")

    all_transcripts = {}

    for lang_code, videos in TOP_VIDEOS.items():
        print(f"\n{'=' * 40}")
        print(f"  {lang_code.upper()}")
        print(f"{'=' * 40}")

        lang_transcripts = []

        for vid_id, title in videos:
            print(f"\n  {title}")
            audio_path = OUT_DIR / f"{lang_code}_{vid_id}.wav"

            # Download if not cached
            if not audio_path.exists():
                print(f"    Downloading audio (max 5 min)...")
                if not download_audio(vid_id, audio_path, max_duration=300):
                    continue
            else:
                print(f"    Using cached audio")

            # Transcribe
            print(f"    Transcribing with {lang_code} vocabulary prompt...")
            segments = transcribe_audio(audio_path, lang_code, model)
            print(f"    Got {len(segments)} segments")

            for seg in segments[:5]:
                print(f"      [{seg['start']:.0f}s-{seg['end']:.0f}s] {seg['text'][:70]}")
            if len(segments) > 5:
                print(f"      ... and {len(segments) - 5} more")

            lang_transcripts.append({
                "video_id": vid_id,
                "title": title,
                "language_code": lang_code,
                "url": f"https://youtube.com/watch?v={vid_id}",
                "segments": segments,
            })

        all_transcripts[lang_code] = lang_transcripts

    # Save all transcripts
    out_file = OUT_DIR / "all_transcripts.json"
    out_file.write_text(json.dumps(all_transcripts, indent=2, ensure_ascii=False), encoding="utf-8")

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    total_segs = 0
    for lang, vids in all_transcripts.items():
        segs = sum(len(v["segments"]) for v in vids)
        total_segs += segs
        print(f"  {lang}: {len(vids)} videos, {segs} segments")
    print(f"\n  Total: {total_segs} transcribed segments")
    print(f"  Saved to: {out_file}")


if __name__ == "__main__":
    main()
