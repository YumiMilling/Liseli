#!/usr/bin/env python3
"""
ZamAI Scout Agent
=================
Discovers Zambian-language YouTube videos, classifies them by language and topic
using an LLM, and catalogs them into the Supabase `zamai_discovery` table.

Quota-conscious: 100 units per search call, batched contentDetails lookups.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from googleapiclient.discovery import build as yt_build
from openai import OpenAI
from supabase import create_client

# ── Configuration ────────────────────────────────────────────────────────────

load_dotenv()

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

MAX_RESULTS_PER_QUERY = 10  # keep quota usage tight (100 units per search call)

SEARCH_QUERIES = [
    # Bemba
    "ZNBC Bemba news",
    "Muvi TV Bemba",
    "Icibemba news Zambia",
    # Nyanja
    "ZNBC Nyanja news",
    "Muvi TV Nyanja",
    "Chinyanja Zambia news",
    # Tonga
    "Tonga local news Zambia",
    "ZNBC Tonga Zambia",
    "Chitonga language Zambia",
    # Lozi
    "ZNBC Lozi news",
    "Silozi Zambia",
    "Lozi language Zambia",
    # General Zambian language content
    "Zambian local language TV",
    "Kaonde language Zambia",
    "Lunda language Zambia",
    "Luvale language Zambia",
]

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("zamai-scout")

# ── Helpers ──────────────────────────────────────────────────────────────────


def parse_iso8601_duration(raw: str) -> int:
    """Convert ISO 8601 duration (PT1H2M3S) to total seconds."""
    match = re.match(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", raw or ""
    )
    if not match:
        return 0
    h, m, s = (int(g) if g else 0 for g in match.groups())
    return h * 3600 + m * 60 + s


# ── YouTube Discovery ────────────────────────────────────────────────────────


def search_youtube(youtube, queries: list[str]) -> dict[str, dict]:
    """
    Run each search query and collect unique video metadata.
    Returns {video_id: {title, channel_name, description, published_at}}.
    """
    videos: dict[str, dict] = {}

    for query in queries:
        log.info("Searching: %s", query)
        response = (
            youtube.search()
            .list(
                q=query,
                part="snippet",
                type="video",
                maxResults=MAX_RESULTS_PER_QUERY,
                relevanceLanguage="en",  # hint; actual filtering done by LLM
                regionCode="ZM",
            )
            .execute()
        )

        for item in response.get("items", []):
            vid = item["id"]["videoId"]
            snippet = item["snippet"]
            if vid not in videos:
                videos[vid] = {
                    "title": snippet["title"],
                    "channel_name": snippet["channelTitle"],
                    "description": snippet.get("description", ""),
                    "published_at": snippet["publishedAt"],
                }

        log.info("  -> %d results (%d unique so far)", len(response.get("items", [])), len(videos))

    return videos


def fetch_durations(youtube, video_ids: list[str]) -> dict[str, int]:
    """
    Batch-fetch durations via videos().list(part='contentDetails').
    YouTube allows up to 50 IDs per call, so we chunk accordingly.
    """
    durations: dict[str, int] = {}
    chunks = [video_ids[i : i + 50] for i in range(0, len(video_ids), 50)]

    for chunk in chunks:
        log.info("Fetching durations for %d videos…", len(chunk))
        response = (
            youtube.videos()
            .list(part="contentDetails", id=",".join(chunk))
            .execute()
        )
        for item in response.get("items", []):
            raw = item["contentDetails"]["duration"]
            durations[item["id"]] = parse_iso8601_duration(raw)

    return durations


# ── LLM Triage ───────────────────────────────────────────────────────────────

TRIAGE_SYSTEM_PROMPT = """\
You are a classification assistant for Zambian media content.
Given a YouTube video's Title, Channel Name, and Description, return ONLY
a JSON object with exactly two keys:

  "language": one of "Bemba", "Nyanja", "Tonga", "Lozi", "Kaonde", "Lunda", "Luvale", "English", or "Unknown"
  "topic":    one of "News", "Politics", "Agriculture", "Entertainment", "Religion", or "Other"

Return raw JSON, no markdown fences, no explanation."""


def classify_video(client: OpenAI, title: str, channel: str, description: str) -> dict:
    """Ask gpt-4o-mini to classify a single video."""
    user_msg = (
        f"Title: {title}\n"
        f"Channel: {channel}\n"
        f"Description: {description[:500]}"  # truncate to save tokens
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=80,
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )

    text = response.choices[0].message.content.strip()
    # Strip markdown fences if the model wraps them anyway
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        log.warning("LLM returned non-JSON for '%s': %s", title, text)
        result = {"language": "Unknown", "topic": "Other"}

    return {
        "language": result.get("language", "Unknown"),
        "topic": result.get("topic", "Other"),
    }


# ── Supabase Persistence ─────────────────────────────────────────────────────


def upsert_videos(supabase, rows: list[dict]) -> int:
    """Upsert rows into zamai_discovery. Returns count of upserted rows."""
    if not rows:
        return 0

    response = (
        supabase.table("zamai_discovery")
        .upsert(rows, on_conflict="video_id")
        .execute()
    )
    return len(response.data) if response.data else 0


# ── Main Orchestrator ─────────────────────────────────────────────────────────


def main():
    log.info("=== ZamAI Scout Agent starting ===")

    # Clients
    youtube = yt_build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Phase 1 — YouTube search
    log.info("Phase 1: YouTube discovery")
    videos = search_youtube(youtube, SEARCH_QUERIES)
    log.info("Discovered %d unique videos", len(videos))

    if not videos:
        log.warning("No videos found. Exiting.")
        return

    # Phase 2 — Batch-fetch durations (single API call per 50 videos)
    log.info("Phase 2: Fetching durations")
    video_ids = list(videos.keys())
    durations = fetch_durations(youtube, video_ids)

    # Phase 3 — LLM classification
    log.info("Phase 3: LLM triage (%d videos)", len(videos))
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []

    for i, (vid, meta) in enumerate(videos.items(), 1):
        log.info("  [%d/%d] Classifying: %s", i, len(videos), meta["title"][:60])
        classification = classify_video(
            openai_client, meta["title"], meta["channel_name"], meta["description"]
        )

        rows.append(
            {
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": meta["title"],
                "channel_name": meta["channel_name"],
                "duration_seconds": durations.get(vid, 0),
                "language": classification["language"],
                "topic": classification["topic"],
                "published_at": meta["published_at"],
                "scraped_at": now,
            }
        )

    # Phase 4 — Supabase upsert
    log.info("Phase 4: Upserting %d rows to Supabase", len(rows))
    # Upsert in batches of 100 to stay within Supabase payload limits
    total_upserted = 0
    for i in range(0, len(rows), 100):
        batch = rows[i : i + 100]
        count = upsert_videos(supabase, batch)
        total_upserted += count
        log.info("  Upserted batch: %d rows", count)

    log.info("=== Done. %d videos cataloged. ===", total_upserted)


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        log.error("Missing environment variable: %s — check your .env file", e)
        sys.exit(1)
    except Exception:
        log.exception("Fatal error")
        sys.exit(1)
