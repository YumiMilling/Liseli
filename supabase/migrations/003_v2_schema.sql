-- Liseli v2 Schema
-- Based on best practices from Tatoeba, Common Voice, OPUS, and Wikidata
-- Designed for 10+ years as national language infrastructure

-- ============================================================
-- CLEAN SLATE
-- ============================================================
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS validation_votes CASCADE;
DROP TABLE IF EXISTS contributions CASCADE;
DROP TABLE IF EXISTS translation_pairs CASCADE;
DROP TABLE IF EXISTS corpus CASCADE;
DROP TABLE IF EXISTS sentences CASCADE;
DROP TABLE IF EXISTS user_language_trust CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS source_materials CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
DROP TABLE IF EXISTS languages CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS translations CASCADE;

DROP TYPE IF EXISTS tier_type CASCADE;
DROP TYPE IF EXISTS domain_type CASCADE;
DROP TYPE IF EXISTS zam_language CASCADE;
DROP TYPE IF EXISTS translation_status CASCADE;
DROP TYPE IF EXISTS verdict_type CASCADE;
DROP TYPE IF EXISTS sentence_source CASCADE;
DROP TYPE IF EXISTS discussion_status CASCADE;

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- LANGUAGES
-- ============================================================
CREATE TABLE languages (
    code VARCHAR(8) PRIMARY KEY,        -- ISO 639-3: bem, nya, toi, loz, kqn, lun, lue, eng
    name_en VARCHAR(100) NOT NULL,
    name_native VARCHAR(100) NOT NULL,
    macro_language VARCHAR(8),          -- for dialect grouping (nya covers ZM Nyanja + MW Chichewa)
    region VARCHAR(10),                 -- ISO 3166: ZM, MW, etc.
    bcp47_tag VARCHAR(20),             -- full BCP 47: bem-ZM, ny-ZM, ny-MW
    script VARCHAR(4) DEFAULT 'Latn',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0
);

INSERT INTO languages (code, name_en, name_native, region, bcp47_tag, sort_order) VALUES
    ('eng', 'English', 'English', 'ZM', 'en-ZM', 0),
    ('bem', 'Bemba', 'Icibemba', 'ZM', 'bem-ZM', 1),
    ('nya', 'Nyanja', 'Chinyanja', 'ZM', 'ny-ZM', 2),
    ('toi', 'Tonga', 'Chitonga', 'ZM', 'toi-ZM', 3),
    ('loz', 'Lozi', 'Silozi', 'ZM', 'loz-ZM', 4),
    ('kqn', 'Kaonde', 'Kikaonde', 'ZM', 'kqn-ZM', 5),
    ('lun', 'Lunda', 'Chilunda', 'ZM', 'lun-ZM', 6),
    ('lue', 'Luvale', 'Luvale', 'ZM', 'lue-ZM', 7);

-- ============================================================
-- SOURCES (provenance)
-- ============================================================
CREATE TABLE sources (
    id VARCHAR(50) PRIMARY KEY,         -- short slug: 'bible-bem-ill15', 'storybook-zambia', 'moe-grade1'
    name VARCHAR(200) NOT NULL,
    source_type VARCHAR(30) NOT NULL,   -- bible, storybook, textbook, dictionary, research, government, community, ai
    publisher VARCHAR(200),
    publication_year INT,
    license VARCHAR(50),                -- CC-BY, CC-BY-SA, public-domain, research-only
    url TEXT,
    collection_method VARCHAR(50),      -- manual, scraped, aligned, statistical, crowdsourced
    languages VARCHAR(100),             -- comma-separated ISO codes covered
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SENTENCES (every language is a row, including English)
-- ============================================================
CREATE TABLE sentences (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    source_id VARCHAR(50) REFERENCES sources(id),
    source_ref VARCHAR(100),            -- e.g., 'GEN 1:1', 'Story #0001 line 3', 'Grade 1 p.42'
    tier VARCHAR(10) DEFAULT 'sentence' CHECK (tier IN ('word', 'phrase', 'sentence')),
    domain VARCHAR(30) DEFAULT 'general',
    dialect VARCHAR(20),                -- 'nyanja-zm', 'chichewa-mw', null for standard
    quality VARCHAR(20) DEFAULT 'unvalidated' CHECK (quality IN ('unvalidated', 'validated', 'disputed', 'rejected')),
    validation_score FLOAT DEFAULT 0,   -- weighted vote score
    version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'deleted')),
    created_by UUID,                    -- null for imported data
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup: same text in same language from same source
    UNIQUE(language_code, text, source_id)
);

-- Trigram index for search across all Bantu languages
CREATE INDEX idx_sentences_text_trgm ON sentences USING gin (text gin_trgm_ops);
CREATE INDEX idx_sentences_language ON sentences(language_code);
CREATE INDEX idx_sentences_source ON sentences(source_id);
CREATE INDEX idx_sentences_tier ON sentences(tier);
CREATE INDEX idx_sentences_quality ON sentences(quality) WHERE quality = 'unvalidated';
CREATE INDEX idx_sentences_status ON sentences(status) WHERE status = 'active';
CREATE INDEX idx_sentences_domain ON sentences(domain);

-- ============================================================
-- TRANSLATION PAIRS (many-to-many between sentences)
-- ============================================================
CREATE TABLE translation_pairs (
    id BIGSERIAL PRIMARY KEY,
    source_sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    target_sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.5,       -- 0.0-1.0, computed from votes + source reliability
    alignment_method VARCHAR(30),       -- manual, verse_aligned, statistical, crowdsourced
    alignment_score FLOAT,              -- from alignment tool if applicable
    alignment_type VARCHAR(10) DEFAULT '1-1', -- 1-1, 1-many, many-1
    validation_status VARCHAR(20) DEFAULT 'unvalidated' CHECK (validation_status IN ('unvalidated', 'validated', 'disputed', 'rejected')),
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- No duplicate pairs
    UNIQUE(source_sentence_id, target_sentence_id)
);

CREATE INDEX idx_pairs_source ON translation_pairs(source_sentence_id);
CREATE INDEX idx_pairs_target ON translation_pairs(target_sentence_id);
CREATE INDEX idx_pairs_status ON translation_pairs(validation_status) WHERE validation_status = 'unvalidated';
CREATE INDEX idx_pairs_confidence ON translation_pairs(confidence DESC);

-- ============================================================
-- CORPUS (monolingual raw text, not sentence-aligned)
-- ============================================================
CREATE TABLE corpus (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    source_id VARCHAR(50) REFERENCES sources(id),
    source_file VARCHAR(200),
    domain VARCHAR(30) DEFAULT 'general',
    dialect VARCHAR(20),
    quality VARCHAR(20) DEFAULT 'raw' CHECK (quality IN ('raw', 'reviewed', 'verified')),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(language_code, text)
);

CREATE INDEX idx_corpus_language ON corpus(language_code);
CREATE INDEX idx_corpus_source ON corpus(source_id);
CREATE INDEX idx_corpus_text_trgm ON corpus USING gin (text gin_trgm_ops);

-- ============================================================
-- USER PROFILES
-- ============================================================
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    handle VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    province VARCHAR(30),
    trust_level INT DEFAULT 0 CHECK (trust_level BETWEEN 0 AND 4),
    -- 0=new, 1=contributor, 2=trusted, 3=reviewer, 4=admin
    total_contributions INT DEFAULT 0,
    total_validations INT DEFAULT 0,
    streak_days INT DEFAULT 0,
    last_active DATE,
    is_shadow_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- USER LANGUAGE TRUST (per-language accuracy)
-- ============================================================
CREATE TABLE user_language_trust (
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    language_code VARCHAR(8) NOT NULL REFERENCES languages(code),
    proficiency VARCHAR(20) DEFAULT 'conversational' CHECK (proficiency IN ('native', 'fluent', 'conversational', 'learning')),
    contributions_count INT DEFAULT 0,
    validations_count INT DEFAULT 0,
    accuracy_rate FLOAT DEFAULT 0.5,    -- % of contributions that get validated
    trust_score FLOAT DEFAULT 0.5,      -- computed: 0.0-1.0
    PRIMARY KEY (user_id, language_code)
);

-- ============================================================
-- VALIDATION VOTES
-- ============================================================
CREATE TABLE validation_votes (
    id BIGSERIAL PRIMARY KEY,
    translation_pair_id BIGINT REFERENCES translation_pairs(id) ON DELETE CASCADE,
    sentence_id BIGINT REFERENCES sentences(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    vote VARCHAR(20) NOT NULL CHECK (vote IN ('correct', 'minor_error', 'major_error', 'wrong_language', 'spam')),
    vote_weight FLOAT DEFAULT 1.0,      -- based on voter's trust_score for that language
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- One vote per user per item
    UNIQUE(translation_pair_id, user_id),
    UNIQUE(sentence_id, user_id)
);

CREATE INDEX idx_votes_pair ON validation_votes(translation_pair_id);
CREATE INDEX idx_votes_sentence ON validation_votes(sentence_id);
CREATE INDEX idx_votes_user ON validation_votes(user_id);

-- ============================================================
-- CONTRIBUTIONS (audit of who did what)
-- ============================================================
CREATE TABLE contributions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    action VARCHAR(20) NOT NULL,        -- create, edit, validate, reject, report
    content_type VARCHAR(20) NOT NULL,  -- sentence, translation_pair, vote
    content_id BIGINT NOT NULL,
    points_earned INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contributions_user ON contributions(user_id, created_at DESC);
CREATE INDEX idx_contributions_content ON contributions(content_type, content_id);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id TEXT NOT NULL,
    action VARCHAR(10) NOT NULL,        -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    user_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_table ON audit_log(table_name, created_at DESC);

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, user_id)
    VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT),
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE','DELETE') THEN row_to_json(OLD)::JSONB END,
        CASE WHEN TG_OP IN ('INSERT','UPDATE') THEN row_to_json(NEW)::JSONB END,
        NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Attach audit triggers to content tables
CREATE TRIGGER audit_sentences AFTER INSERT OR UPDATE OR DELETE ON sentences FOR EACH ROW EXECUTE FUNCTION audit_trigger();
CREATE TRIGGER audit_translation_pairs AFTER INSERT OR UPDATE OR DELETE ON translation_pairs FOR EACH ROW EXECUTE FUNCTION audit_trigger();
CREATE TRIGGER audit_validation_votes AFTER INSERT OR UPDATE OR DELETE ON validation_votes FOR EACH ROW EXECUTE FUNCTION audit_trigger();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Sentences
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read active sentences" ON sentences FOR SELECT USING (status = 'active');
CREATE POLICY "Authenticated users can insert" ON sentences FOR INSERT WITH CHECK (auth.uid() IS NOT NULL OR created_by IS NULL);
CREATE POLICY "Users can edit own unvalidated" ON sentences FOR UPDATE USING (created_by = auth.uid() AND quality = 'unvalidated');
CREATE POLICY "Service role full access" ON sentences FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Translation pairs
ALTER TABLE translation_pairs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON translation_pairs FOR SELECT USING (true);
CREATE POLICY "Authenticated can insert" ON translation_pairs FOR INSERT WITH CHECK (auth.uid() IS NOT NULL OR created_by IS NULL);
CREATE POLICY "Service role full access" ON translation_pairs FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Corpus
ALTER TABLE corpus ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON corpus FOR SELECT USING (true);
CREATE POLICY "Service role full access" ON corpus FOR ALL TO service_role USING (true) WITH CHECK (true);

-- User profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read profiles" ON user_profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (id = auth.uid());
CREATE POLICY "Service role full access" ON user_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);

-- User language trust
ALTER TABLE user_language_trust ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON user_language_trust FOR SELECT USING (true);
CREATE POLICY "Service role full access" ON user_language_trust FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Validation votes
ALTER TABLE validation_votes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read votes" ON validation_votes FOR SELECT USING (true);
CREATE POLICY "Authenticated can vote" ON validation_votes FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Service role full access" ON validation_votes FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Contributions
ALTER TABLE contributions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON contributions FOR SELECT USING (true);
CREATE POLICY "Service role full access" ON contributions FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Sources
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON sources FOR SELECT USING (true);
CREATE POLICY "Service role full access" ON sources FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Languages
ALTER TABLE languages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON languages FOR SELECT USING (true);
CREATE POLICY "Service role full access" ON languages FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins can read" ON audit_log FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND trust_level >= 4)
);
CREATE POLICY "Service role full access" ON audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- Language coverage stats
CREATE OR REPLACE VIEW language_stats AS
SELECT
    l.code,
    l.name_en,
    l.name_native,
    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'active') AS sentence_count,
    COUNT(DISTINCT tp.id) AS parallel_pair_count,
    COUNT(DISTINCT c.id) AS corpus_line_count,
    COUNT(DISTINCT s.id) FILTER (WHERE s.quality = 'validated') AS validated_count
FROM languages l
LEFT JOIN sentences s ON s.language_code = l.code
LEFT JOIN translation_pairs tp ON tp.source_sentence_id = s.id OR tp.target_sentence_id = s.id
LEFT JOIN corpus c ON c.language_code = l.code
WHERE l.code != 'eng'
GROUP BY l.code, l.name_en, l.name_native
ORDER BY l.sort_order;

-- Validation queue (unvalidated pairs needing votes)
CREATE OR REPLACE VIEW validation_queue AS
SELECT
    tp.id AS pair_id,
    s1.text AS source_text,
    s1.language_code AS source_lang,
    s2.text AS target_text,
    s2.language_code AS target_lang,
    tp.confidence,
    tp.upvotes,
    tp.downvotes,
    tp.created_at
FROM translation_pairs tp
JOIN sentences s1 ON s1.id = tp.source_sentence_id
JOIN sentences s2 ON s2.id = tp.target_sentence_id
WHERE tp.validation_status = 'unvalidated'
ORDER BY tp.upvotes + tp.downvotes ASC, tp.created_at ASC;
