-- ZamAI Scout Agent — discovery table
-- Stores YouTube videos found and classified by the scout script.

CREATE TABLE IF NOT EXISTS zamai_discovery (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id        TEXT NOT NULL UNIQUE,
    url             TEXT NOT NULL,
    title           TEXT NOT NULL,
    channel_name    TEXT NOT NULL,
    duration_seconds INTEGER DEFAULT 0,
    language        TEXT NOT NULL,
    topic           TEXT NOT NULL,
    published_at    TIMESTAMPTZ,
    scraped_at      TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lookups by language and topic
CREATE INDEX IF NOT EXISTS idx_zamai_discovery_language ON zamai_discovery (language);
CREATE INDEX IF NOT EXISTS idx_zamai_discovery_topic ON zamai_discovery (topic);
