-- Liseli Audio Layer
-- Handles: YouTube clip references, transcriptions, translations, re-recordings
-- Designed for TTS/ASR training, dialect mapping, and community contribution

-- ============================================================
-- AUDIO CLIPS (source material — YouTube refs or direct uploads)
-- ============================================================
CREATE TABLE audio_clips (
    id BIGSERIAL PRIMARY KEY,

    -- Source: YouTube reference OR direct upload
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('youtube', 'upload', 'radio', 'podcast', 'field_recording')),

    -- YouTube/external reference (no copyrighted audio stored)
    external_url TEXT,                  -- e.g., youtube.com/watch?v=xxx
    start_time_ms INT,                  -- millisecond offset
    end_time_ms INT,                    -- millisecond offset
    channel_name VARCHAR(200),          -- e.g., "ZNBC Radio 1", "Muvi TV"

    -- Direct upload (community recordings stored in Supabase Storage)
    storage_path TEXT,                  -- supabase storage path

    -- Content metadata
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    dialect VARCHAR(20),                -- e.g., 'nyanja-zm', 'bemba-northern'
    duration_ms INT,                    -- clip duration in milliseconds
    domain VARCHAR(30) DEFAULT 'general', -- religion, news, education, health, agriculture, government

    -- Quality
    audio_quality VARCHAR(20) DEFAULT 'unknown' CHECK (audio_quality IN ('unknown', 'clean', 'noisy', 'unusable')),
    speaker_count INT DEFAULT 1,        -- 1 = single speaker, 2+ = conversation

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'transcribed', 'translated', 'complete', 'rejected')),

    -- Who submitted it
    submitted_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clips_language ON audio_clips(language_code);
CREATE INDEX idx_clips_status ON audio_clips(status);
CREATE INDEX idx_clips_domain ON audio_clips(domain);
CREATE INDEX idx_clips_source ON audio_clips(source_type);

-- ============================================================
-- TRANSCRIPTIONS (what was said — text in original language)
-- ============================================================
CREATE TABLE transcriptions (
    id BIGSERIAL PRIMARY KEY,
    clip_id BIGINT NOT NULL REFERENCES audio_clips(id) ON DELETE CASCADE,

    -- The transcription
    text TEXT NOT NULL,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    dialect VARCHAR(20),

    -- Links to sentence table if matched
    sentence_id BIGINT REFERENCES sentences(id),

    -- Quality
    confidence FLOAT DEFAULT 0.5,
    validation_status VARCHAR(20) DEFAULT 'unvalidated' CHECK (validation_status IN ('unvalidated', 'validated', 'disputed', 'rejected')),
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,

    -- Who transcribed
    transcribed_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(clip_id, language_code, text)
);

CREATE INDEX idx_transcriptions_clip ON transcriptions(clip_id);
CREATE INDEX idx_transcriptions_status ON transcriptions(validation_status);

-- ============================================================
-- CLIP TRANSLATIONS (English meaning of what was said)
-- ============================================================
CREATE TABLE clip_translations (
    id BIGSERIAL PRIMARY KEY,
    transcription_id BIGINT NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,

    -- English translation of the transcription
    english_text TEXT NOT NULL,

    -- Links to translation pair if matched
    translation_pair_id BIGINT REFERENCES translation_pairs(id),

    -- Quality
    confidence FLOAT DEFAULT 0.5,
    validation_status VARCHAR(20) DEFAULT 'unvalidated' CHECK (validation_status IN ('unvalidated', 'validated', 'disputed', 'rejected')),
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,

    -- Who translated
    translated_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clip_trans_transcription ON clip_translations(transcription_id);

-- ============================================================
-- RE-RECORDINGS (community re-speaks the same phrase)
-- ============================================================
CREATE TABLE re_recordings (
    id BIGSERIAL PRIMARY KEY,

    -- What they're re-speaking (links to a known text)
    transcription_id BIGINT REFERENCES transcriptions(id) ON DELETE CASCADE,
    sentence_id BIGINT REFERENCES sentences(id) ON DELETE CASCADE,
    -- At least one must be set

    -- The recording
    storage_path TEXT NOT NULL,         -- supabase storage path
    duration_ms INT,

    -- Speaker metadata (anonymous but useful for training)
    speaker_id UUID,                    -- links to user_profiles if logged in
    speaker_province VARCHAR(30),
    speaker_gender VARCHAR(10),         -- optional: male, female, other
    speaker_age_range VARCHAR(10),      -- optional: 18-25, 26-35, 36-50, 50+

    -- Language/dialect
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    dialect VARCHAR(20),

    -- Quality
    audio_quality VARCHAR(20) DEFAULT 'unknown' CHECK (audio_quality IN ('unknown', 'clean', 'noisy', 'unusable')),
    validation_status VARCHAR(20) DEFAULT 'unvalidated' CHECK (validation_status IN ('unvalidated', 'validated', 'rejected')),
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rerecordings_transcription ON re_recordings(transcription_id);
CREATE INDEX idx_rerecordings_sentence ON re_recordings(sentence_id);
CREATE INDEX idx_rerecordings_language ON re_recordings(language_code);
CREATE INDEX idx_rerecordings_province ON re_recordings(speaker_province);
CREATE INDEX idx_rerecordings_status ON re_recordings(validation_status);

-- ============================================================
-- AUDIO VALIDATION VOTES
-- ============================================================
CREATE TABLE audio_votes (
    id BIGSERIAL PRIMARY KEY,

    -- What's being voted on (one of these)
    transcription_id BIGINT REFERENCES transcriptions(id) ON DELETE CASCADE,
    clip_translation_id BIGINT REFERENCES clip_translations(id) ON DELETE CASCADE,
    re_recording_id BIGINT REFERENCES re_recordings(id) ON DELETE CASCADE,

    -- The vote
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    vote VARCHAR(20) NOT NULL CHECK (vote IN ('correct', 'minor_error', 'major_error', 'wrong_language', 'unintelligible', 'spam')),
    vote_weight FLOAT DEFAULT 1.0,
    comment TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audio_votes_user ON audio_votes(user_id);

-- ============================================================
-- PRONUNCIATION GUIDE (word-level audio for dictionary)
-- ============================================================
CREATE TABLE pronunciations (
    id BIGSERIAL PRIMARY KEY,
    sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,  -- word or phrase

    -- The recording
    storage_path TEXT NOT NULL,
    duration_ms INT,

    -- Speaker
    speaker_id UUID,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    dialect VARCHAR(20),
    speaker_province VARCHAR(30),

    -- Quality / voting
    is_primary BOOLEAN DEFAULT FALSE,   -- featured pronunciation
    validation_status VARCHAR(20) DEFAULT 'unvalidated',
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pronunciations_sentence ON pronunciations(sentence_id);
CREATE INDEX idx_pronunciations_language ON pronunciations(language_code);
CREATE INDEX idx_pronunciations_primary ON pronunciations(is_primary) WHERE is_primary = TRUE;

-- ============================================================
-- RLS
-- ============================================================
ALTER TABLE audio_clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clip_translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE pronunciations ENABLE ROW LEVEL SECURITY;

-- Public read
CREATE POLICY "Public read" ON audio_clips FOR SELECT USING (true);
CREATE POLICY "Public read" ON transcriptions FOR SELECT USING (true);
CREATE POLICY "Public read" ON clip_translations FOR SELECT USING (true);
CREATE POLICY "Public read" ON re_recordings FOR SELECT USING (true);
CREATE POLICY "Public read" ON audio_votes FOR SELECT USING (true);
CREATE POLICY "Public read" ON pronunciations FOR SELECT USING (true);

-- Authenticated insert
CREATE POLICY "Auth insert" ON audio_clips FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Auth insert" ON transcriptions FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Auth insert" ON clip_translations FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Auth insert" ON re_recordings FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Auth insert" ON audio_votes FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Auth insert" ON pronunciations FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Service role full access
CREATE POLICY "Service all" ON audio_clips FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service all" ON transcriptions FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service all" ON clip_translations FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service all" ON re_recordings FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service all" ON audio_votes FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service all" ON pronunciations FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Audit triggers
CREATE TRIGGER audit_transcriptions AFTER INSERT OR UPDATE OR DELETE ON transcriptions FOR EACH ROW EXECUTE FUNCTION audit_trigger();
CREATE TRIGGER audit_re_recordings AFTER INSERT OR UPDATE OR DELETE ON re_recordings FOR EACH ROW EXECUTE FUNCTION audit_trigger();
CREATE TRIGGER audit_pronunciations AFTER INSERT OR UPDATE OR DELETE ON pronunciations FOR EACH ROW EXECUTE FUNCTION audit_trigger();

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- Clips needing transcription
CREATE OR REPLACE VIEW clips_pending_transcription AS
SELECT ac.*, l.name_native AS language_name
FROM audio_clips ac
JOIN languages l ON l.code = ac.language_code
WHERE ac.status = 'pending'
ORDER BY ac.created_at ASC;

-- Transcriptions needing English translation
CREATE OR REPLACE VIEW transcriptions_pending_translation AS
SELECT t.*, ac.external_url, ac.start_time_ms, ac.end_time_ms
FROM transcriptions t
JOIN audio_clips ac ON ac.id = t.clip_id
WHERE t.validation_status = 'validated'
AND NOT EXISTS (SELECT 1 FROM clip_translations ct WHERE ct.transcription_id = t.id)
ORDER BY t.created_at ASC;

-- Words/phrases available for pronunciation recording
CREATE OR REPLACE VIEW words_needing_pronunciation AS
SELECT s.id, s.text, s.language_code, l.name_native,
    COUNT(p.id) AS recording_count
FROM sentences s
JOIN languages l ON l.code = s.language_code
LEFT JOIN pronunciations p ON p.sentence_id = s.id AND p.validation_status != 'rejected'
WHERE s.tier IN ('word', 'phrase')
AND s.status = 'active'
AND s.language_code != 'eng'
GROUP BY s.id, s.text, s.language_code, l.name_native
HAVING COUNT(p.id) < 3
ORDER BY COUNT(p.id) ASC, s.id ASC;
