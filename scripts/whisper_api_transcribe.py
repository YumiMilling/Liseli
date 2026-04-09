"""
Batch transcribe Ubuntu Talks videos using OpenAI Whisper API.
~$0.006/min = ~$0.36 for all 50 videos.
Downloads audio, sends to API, saves timestamped transcripts.
"""
import os
import json
import time
import ssl
import urllib.request
import yt_dlp
from pathlib import Path

os.environ["PATH"] = r"C:\Users\chlin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin" + ";" + os.environ["PATH"]

API_KEY = open(".env.local").read().split("OPENAI_API_KEY=")[1].strip()

OUT_DIR = Path("data/ubuntu-talks-transcripts")
OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = Path("data/ubuntu-talks-audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# All Ubuntu Talks videos found
VIDEOS = [
    ("z3xNCSxQYmA", "bem", "10 Kitchen items in Bemba"),
    ("jYLD-dHr45Y", "bem", "15 easy words in Bemba"),
    ("tJdUA8pLtO4", "bem", "Quick way to learn basic Bemba"),
    ("ZsNXyaLlFyA", "bem", "Bemba Objects Lesson 7"),
    ("0Qy_cncJd8A", "bem", "Learn Bemba at Ubuntu Talks"),
    ("hcQSUfFHafo", "bem", "Learn ChiBemba Beginner to fluent"),
    ("T5vW1zLiWeM", "bem", "Ubuntu Talks Chibemba"),
    ("EdWGK43_SGk", "bem", "My Friend in Bemba"),
    ("KqlSTtXtD8s", "bem", "God Bless You in Bemba"),
    ("s3EtxzVfh_U", "bem", "Goodmorning in Bemba"),
    ("wGzsvwJzXuE", "bem", "I am sick in Bemba"),
    ("5sAkGN_5OXQ", "bem", "I dont know in Bemba"),
    ("le_tkXOK--8", "bem", "Time in Bemba"),
    ("em0ksx_pVus", "nya", "Chichewa Crash Course"),
    ("YZNtsO9A8yI", "nya", "Chinyanja vowels"),
    ("yV6mkImOV_U", "nya", "English to Chinyanja 1"),
    ("mnLu89OsXuM", "nya", "English to Chinyanja 2"),
    ("BS55PkQW6x4", "nya", "Zambia Language Nyanja"),
    ("NUzUW7mTUs4", "nya", "Learn Chinyanja at Ubuntu Talks"),
    ("cwAJdNS8H6o", "nya", "Nyanja lessons part 5"),
    ("aDu-K6ctK_g", "nya", "Nyanja lessons part 6"),
    ("ZJS5NZ0y1jM", "nya", "Nyanja sentences part 2"),
    ("I4hh5QRHmss", "nya", "Nyanja sentences"),
    ("FwdFR6jffBk", "nya", "Learn Nyanja Language"),
    ("g1gHh7xmzUc", "nya", "Nyanja lesson 4"),
    ("C5braMM1U10", "nya", "Lets learn Nyanja part 1"),
    ("VAoKzcqgUmY", "nya", "Hello in Chinyanja"),
    ("rb90s_E89WI", "toi", "Learn Tonga at Ubuntu Talks"),
    ("fWLS-6VrQPg", "toi", "Learning Tonga"),
    ("_5skwl2ubHc", "toi", "Ubuntu Talks Chitonga"),
    ("ylIiJNxl_wo", "toi", "Unlock beauty of Chitonga"),
    ("u2DPVKu8ruU", "toi", "Reading Chitonga Lesson 1 Vowels"),
    ("5TqahFeoTOQ", "toi", "Reading Chitonga Lesson 2"),
    ("j6SQyi7SCfU", "toi", "Come here in Chitonga"),
    ("1ttkwc8ZcwY", "toi", "I Love You in Chitonga"),
    ("ndGInTlbfCo", "lun", "Lunda Ndembu Alphabet part 1"),
    ("zkMbzpHoIZ0", "mul", "Welcome in 7 Zambian languages"),
    ("gXhVwXbjpAI", "mul", "Love in 6 Zambian languages"),
    ("JYD5AAcdSlo", "mul", "Words in Bemba Chewa Xhosa"),
]


def download_audio(video_id, output_path):
    """Download audio only."""
    if output_path.exists() and output_path.stat().st_size > 1000:
        return True

    ydl_opts = {
        "format": "worstaudio",
        "outtmpl": str(output_path).replace(".mp3", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "ffmpeg_location": r"C:\Users\chlin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin",
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


def transcribe_with_api(audio_path, language_hint=None):
    """Send to OpenAI Whisper API via raw HTTP — no openai package needed."""
    import io
    import mimetypes

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(audio_path)
    mime = mimetypes.guess_type(filename)[0] or "audio/mpeg"

    with open(audio_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\nsegment\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

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
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip(),
        })

    return {
        "language": result.get("language", "unknown"),
        "text": result.get("text", ""),
        "segments": segments,
    }


def main():
    print("=" * 60)
    print("UBUNTU TALKS — WHISPER API BATCH TRANSCRIPTION")
    print(f"Videos: {len(VIDEOS)}")
    print("=" * 60)

    all_results = {}
    total_cost = 0

    for vid_id, lang, title in VIDEOS:
        print(f"\n  [{lang}] {title}")
        audio_path = AUDIO_DIR / f"{vid_id}.mp3"

        # Download
        if not download_audio(vid_id, audio_path):
            continue

        if not audio_path.exists():
            # Check for other extensions
            for ext in [".mp3", ".m4a", ".webm", ".wav"]:
                alt = AUDIO_DIR / f"{vid_id}{ext}"
                if alt.exists():
                    audio_path = alt
                    break

        if not audio_path.exists():
            print(f"    No audio file found")
            continue

        size_mb = audio_path.stat().st_size / 1024 / 1024
        print(f"    Audio: {size_mb:.1f} MB")

        # Transcribe via API
        try:
            result = transcribe_with_api(audio_path)
            segments = result["segments"]
            detected_lang = result["language"]
            print(f"    Language: {detected_lang}, Segments: {len(segments)}")

            # Estimate cost ($0.006/min)
            if segments:
                duration_min = segments[-1]["end"] / 60
                cost = duration_min * 0.006
                total_cost += cost
                print(f"    Duration: {duration_min:.1f} min, Cost: ${cost:.3f}")

            # Show first few segments
            for seg in segments[:3]:
                print(f"    [{seg['start']:.0f}s] {seg['text'][:70]}")

            all_results[vid_id] = {
                "video_id": vid_id,
                "language_code": lang,
                "title": title,
                "url": f"https://youtube.com/watch?v={vid_id}",
                "detected_language": detected_lang,
                "segments": segments,
                "full_text": result["text"],
            }

        except Exception as e:
            print(f"    API error: {e}")

        time.sleep(0.5)  # Rate limiting

    # Save results
    out_file = OUT_DIR / "all_ubuntu_talks.json"
    out_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"DONE")
    print(f"  Transcribed: {len(all_results)} / {len(VIDEOS)}")
    print(f"  Total estimated cost: ${total_cost:.2f}")
    print(f"  Saved to: {out_file}")

    # Summary by language
    from collections import Counter
    lang_counts = Counter(v["language_code"] for v in all_results.values())
    seg_counts = Counter()
    for v in all_results.values():
        seg_counts[v["language_code"]] += len(v["segments"])
    print(f"\n  By language:")
    for lang, count in lang_counts.most_common():
        print(f"    {lang}: {count} videos, {seg_counts[lang]} segments")


if __name__ == "__main__":
    main()
