-- Content flagging for profanity, sensitive, and offensive content
-- Accept everything, tag it, control visibility

-- Add content flags to sentences
ALTER TABLE sentences ADD COLUMN IF NOT EXISTS content_flag VARCHAR(30);
ALTER TABLE sentences ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;
-- content_flag: null (clean), 'profanity', 'offensive', 'sensitive', 'adult'
-- is_public: false = hidden from public views, available for research/training

-- Add to transcriptions (audio content)
ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS content_flag VARCHAR(30);
ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;

-- Add to re_recordings
ALTER TABLE re_recordings ADD COLUMN IF NOT EXISTS content_flag VARCHAR(30);
ALTER TABLE re_recordings ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;

-- Profanity word lists per language (community-maintained, never public)
CREATE TABLE IF NOT EXISTS content_filter_words (
    id BIGSERIAL PRIMARY KEY,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    word VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'mild' CHECK (severity IN ('mild', 'moderate', 'severe')),
    notes TEXT,
    added_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(language_code, word)
);

-- This table is NEVER publicly readable
ALTER TABLE content_filter_words ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Only admins and service role" ON content_filter_words
    FOR ALL USING (
        EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND trust_level >= 4)
    );
CREATE POLICY "Service full access" ON content_filter_words
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- User content reports
CREATE TABLE IF NOT EXISTS content_reports (
    id BIGSERIAL PRIMARY KEY,
    reporter_id UUID NOT NULL REFERENCES user_profiles(id),
    content_type VARCHAR(30) NOT NULL, -- sentence, transcription, re_recording
    content_id BIGINT NOT NULL,
    reason VARCHAR(30) NOT NULL CHECK (reason IN ('profanity', 'offensive', 'spam', 'wrong_language', 'nonsense', 'other')),
    comment TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    resolution VARCHAR(30), -- flagged, cleared, removed, shadow_banned_user
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE content_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Auth can report" ON content_reports FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Admins can read" ON content_reports FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND trust_level >= 3)
);
CREATE POLICY "Service full access" ON content_reports FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX idx_reports_unresolved ON content_reports(resolved) WHERE resolved = FALSE;
CREATE INDEX idx_reports_content ON content_reports(content_type, content_id);

-- Update public-facing views to filter out flagged content
CREATE OR REPLACE VIEW public_sentences AS
SELECT * FROM sentences
WHERE status = 'active' AND is_public = TRUE;

-- Auto-flag trigger: when 2+ reports on same content, set is_public = false
CREATE OR REPLACE FUNCTION auto_flag_content() RETURNS TRIGGER AS $$
DECLARE
    report_count INT;
BEGIN
    SELECT COUNT(*) INTO report_count
    FROM content_reports
    WHERE content_type = NEW.content_type
    AND content_id = NEW.content_id
    AND NOT resolved;

    IF report_count >= 2 THEN
        IF NEW.content_type = 'sentence' THEN
            UPDATE sentences SET is_public = FALSE, content_flag = NEW.reason
            WHERE id = NEW.content_id;
        ELSIF NEW.content_type = 'transcription' THEN
            UPDATE transcriptions SET is_public = FALSE, content_flag = NEW.reason
            WHERE id = NEW.content_id;
        ELSIF NEW.content_type = 're_recording' THEN
            UPDATE re_recordings SET is_public = FALSE, content_flag = NEW.reason
            WHERE id = NEW.content_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_content_report
    AFTER INSERT ON content_reports
    FOR EACH ROW
    EXECUTE FUNCTION auto_flag_content();
