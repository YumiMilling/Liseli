"""
YouTube Segment Finder for Liseli
Finds Zambian language content on YouTube, extracts subtitle timestamps,
and creates segment pointers for community transcription.

No audio downloaded — stores YouTube URL + start/end timestamps only.
Community sees embedded player that plays just the relevant segment.
"""

import json
import re
import uuid
import yt_dlp
from pathlib import Path

OUT_DIR = Path("data/youtube-segments")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Search queries for each language
SEARCHES = {
    "bem": [
        "icibemba sermon zambia",
        "bemba language lesson",
        "bemba news zambia",
        "zambian proverbs bemba",
        "bemba worship zambia",
        "learn bemba zambia",
        "bemba conversation",
        "bemba story telling",
    ],
    "nya": [
        "chinyanja lesson zambia",
        "nyanja language zambia",
        "cinyanja sermon",
        "lusaka nyanja",
        "nyanja conversation zambia",
        "learn nyanja",
    ],
    "toi": [
        "chitonga lesson zambia",
        "learn tonga zambia",
        "tonga language zambia",
        "tonga sermon zambia",
    ],
    "loz": [
        "silozi language zambia",
        "lozi lesson zambia",
        "barotseland lozi",
        "lozi sermon",
    ],
    "kqn": [
        "kikaonde language zambia",
        "kaonde lesson",
        "kaonde zambia",
    ],
    "lun": [
        "lunda language zambia",
        "chilunda lesson",
        "lunda zambia northwestern",
    ],
    "lue": [
        "luvale language zambia",
        "luvale lesson",
        "luvale zambia",
    ],
}

# Domain classification from title/description
DOMAIN_KEYWORDS = {
    "religion": ["sermon", "worship", "church", "prayer", "bible", "jesus", "god", "pastor", "praise"],
    "education": ["lesson", "learn", "teach", "school", "class", "tutorial", "beginner", "words", "vocabulary", "numbers", "alphabet"],
    "news": ["news", "znbc", "muvi", "prime tv", "parliament", "president", "government"],
    "culture": ["proverb", "tradition", "custom", "ceremony", "dance", "story", "folktale", "history", "documentary"],
    "music": ["song", "music", "sing", "choir", "lyrics", "album"],
    "daily_life": ["conversation", "greetings", "phone", "market", "cooking", "family"],
}


def classify_domain(title):
    title_lower = title.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return domain
    return "general"


def find_videos(language_code, max_per_query=10):
    """Search YouTube for videos in a given language."""
    queries = SEARCHES.get(language_code, [])
    videos = {}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }

    for query in queries:
        search = f"ytsearch{max_per_query}:{query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(search, download=False)
                for entry in info.get("entries") or []:
                    vid_id = entry.get("id")
                    if vid_id and vid_id not in videos:
                        duration = int(entry.get("duration") or 0)
                        if duration < 10 or duration > 7200:  # skip < 10s or > 2h
                            continue
                        videos[vid_id] = {
                            "id": vid_id,
                            "title": entry.get("title", ""),
                            "url": f"https://youtube.com/watch?v={vid_id}",
                            "duration": duration,
                            "query": query,
                        }
            except Exception:
                pass

    return list(videos.values())


def extract_subtitle_segments(video_id):
    """Get auto-generated subtitle segments with timestamps."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writeautomaticsub": True,
        "subtitlesformat": "json3",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)
            auto_subs = info.get("automatic_captions", {})

            # Try English auto-subs first (for bilingual content)
            # Then try any available language
            sub_data = None
            for lang_pref in ["en", "bem", "ny", "toi", "loz"]:
                if lang_pref in auto_subs:
                    # Get the json3 format URL
                    for fmt in auto_subs[lang_pref]:
                        if fmt.get("ext") == "json3":
                            sub_data = {"lang": lang_pref, "url": fmt["url"]}
                            break
                    if sub_data:
                        break

            if not sub_data and auto_subs:
                # Take first available
                first_lang = list(auto_subs.keys())[0]
                for fmt in auto_subs[first_lang]:
                    if fmt.get("ext") == "json3":
                        sub_data = {"lang": first_lang, "url": fmt["url"]}
                        break

            # Download and parse subtitle JSON
            if sub_data:
                import urllib.request
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                req = urllib.request.Request(sub_data["url"], headers={"User-Agent": "Liseli/1.0"})
                resp = urllib.request.urlopen(req, context=ctx, timeout=15)
                sub_json = json.loads(resp.read().decode("utf-8"))

                segments = []
                events = sub_json.get("events", [])
                for event in events:
                    start_ms = event.get("tStartMs", 0)
                    dur_ms = event.get("dDurationMs", 0)
                    segs = event.get("segs", [])
                    text = "".join(s.get("utf8", "") for s in segs).strip()
                    text = re.sub(r"\s+", " ", text).strip()
                    if text and len(text) > 2 and text != "\n":
                        segments.append({
                            "start_ms": start_ms,
                            "end_ms": start_ms + dur_ms,
                            "text": text,
                        })

                return segments, sub_data["lang"]

            # No subtitles — still index the video for manual transcription
            return None, None

        except Exception:
            return None, None


def create_clip_segments(video, subtitle_segments, sub_lang):
    """
    Group subtitle segments into 5-15 second clips.
    Each clip should be a coherent chunk of speech.
    """
    if not subtitle_segments:
        # No subtitles — create segments at regular intervals for manual transcription
        duration_ms = video["duration"] * 1000
        clips = []
        # Sample 5 segments of 10s each from different parts of the video
        for i in range(min(5, video["duration"] // 30)):
            start = (duration_ms // 6) * (i + 1)  # spread across video
            clips.append({
                "start_ms": start,
                "end_ms": start + 10000,
                "text": None,  # needs manual transcription
                "auto_sub_lang": None,
            })
        return clips

    # Group subtitle segments into 5-15 second chunks STRICTLY
    clips = []
    current_clip = {"start_ms": None, "end_ms": None, "texts": []}

    for seg in subtitle_segments:
        if current_clip["start_ms"] is None:
            current_clip["start_ms"] = seg["start_ms"]

        current_clip["end_ms"] = seg["end_ms"]
        current_clip["texts"].append(seg["text"])

        clip_duration = (current_clip["end_ms"] - current_clip["start_ms"]) / 1000

        # Flush when we hit 8-15 seconds
        if clip_duration >= 8:
            combined_text = " ".join(current_clip["texts"])
            if len(combined_text) > 5:
                # Hard cap at 15 seconds — trim end if needed
                max_end = current_clip["start_ms"] + 15000
                clips.append({
                    "start_ms": current_clip["start_ms"],
                    "end_ms": min(current_clip["end_ms"], max_end),
                    "text": combined_text[:200],  # cap text length too
                    "auto_sub_lang": sub_lang,
                })
            current_clip = {"start_ms": None, "end_ms": None, "texts": []}

        # Safety: if somehow over 15 seconds without flushing, force flush
        elif clip_duration > 15:
            current_clip = {"start_ms": None, "end_ms": None, "texts": []}

    # Don't create too many clips per video
    return clips[:30]


def main():
    print("=" * 60)
    print("YOUTUBE SEGMENT FINDER")
    print("=" * 60)

    all_segments = []

    for lang_code, queries in SEARCHES.items():
        print(f"\n{'=' * 40}")
        print(f"  {lang_code.upper()}")
        print(f"{'=' * 40}")

        # Find videos
        videos = find_videos(lang_code)
        print(f"  Found {len(videos)} videos")

        for video in videos:
            print(f"\n  [{video['duration']//60}:{video['duration']%60:02d}] {video['title'][:60]}")

            # Extract subtitles
            sub_segments, sub_lang = extract_subtitle_segments(video["id"])

            if sub_segments:
                print(f"    Subtitles: {len(sub_segments)} segments ({sub_lang})")
            else:
                print(f"    No subtitles — will create manual segments")

            # Create clips
            clips = create_clip_segments(video, sub_segments, sub_lang)
            print(f"    Clips: {len(clips)}")

            domain = classify_domain(video["title"])

            for clip in clips:
                segment = {
                    "id": str(uuid.uuid4()),
                    "source_type": "youtube",
                    "external_url": video["url"],
                    "start_time_ms": clip["start_ms"],
                    "end_time_ms": clip["end_ms"],
                    "duration_ms": clip["end_ms"] - clip["start_ms"],
                    "channel_name": video.get("channel", ""),
                    "video_title": video["title"],
                    "language_code": lang_code,
                    "domain": domain,
                    "auto_transcript": clip.get("text"),
                    "auto_sub_lang": clip.get("auto_sub_lang"),
                    "status": "pending",
                }
                all_segments.append(segment)

    # Save all segments
    out_file = OUT_DIR / "segments.json"
    out_file.write_text(json.dumps(all_segments, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total segments: {len(all_segments)}")

    # By language
    from collections import Counter
    lang_counts = Counter(s["language_code"] for s in all_segments)
    for lang, count in lang_counts.most_common():
        print(f"  {lang}: {count} segments")

    # With vs without subtitles
    with_subs = sum(1 for s in all_segments if s["auto_transcript"])
    print(f"\n  With auto-transcript: {with_subs}")
    print(f"  Need manual transcription: {len(all_segments) - with_subs}")

    # By domain
    domain_counts = Counter(s["domain"] for s in all_segments)
    print(f"\n  By domain:")
    for domain, count in domain_counts.most_common():
        print(f"    {domain}: {count}")

    print(f"\n  Saved to: {out_file}")
    print(f"\n  Embed URL format:")
    if all_segments:
        s = all_segments[0]
        start_sec = s["start_time_ms"] // 1000
        end_sec = s["end_time_ms"] // 1000
        vid_id = s["external_url"].split("v=")[1]
        print(f"    https://youtube.com/embed/{vid_id}?start={start_sec}&end={end_sec}&autoplay=1")

    print("\nDone!")


if __name__ == "__main__":
    main()
