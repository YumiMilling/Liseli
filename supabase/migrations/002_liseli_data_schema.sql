-- Liseli Data Schema v2
-- Simplified schema for the data pipeline (sentences, translations, corpus)

-- Drop old tables if they exist from v1
DROP TABLE IF EXISTS discussion_comments CASCADE;
DROP TABLE IF EXISTS discussions CASCADE;
DROP TABLE IF EXISTS votes CASCADE;
DROP TABLE IF EXISTS translations CASCADE;
DROP TABLE IF EXISTS sentences CASCADE;
DROP TABLE IF EXISTS contributors CASCADE;
DROP TABLE IF EXISTS source_materials CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS corpus CASCADE;

-- Drop old types
DROP TYPE IF EXISTS tier_type CASCADE;
DROP TYPE IF EXISTS domain_type CASCADE;
DROP TYPE IF EXISTS zam_language CASCADE;
DROP TYPE IF EXISTS translation_status CASCADE;
DROP TYPE IF EXISTS verdict_type CASCADE;
DROP TYPE IF EXISTS sentence_source CASCADE;
DROP TYPE IF EXISTS discussion_status CASCADE;

-- Sentences (English source content)
CREATE TABLE sentences (
    id TEXT PRIMARY KEY,
    english TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('word', 'phrase', 'sentence')),
    domain TEXT NOT NULL DEFAULT 'general',
    concept_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'community',
    difficulty INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sentences_tier ON sentences(tier);
CREATE INDEX idx_sentences_concept ON sentences(concept_id);
CREATE INDEX idx_sentences_source ON sentences(source);

-- Translations (bilingual pairs)
CREATE TABLE translations (
    id TEXT PRIMARY KEY,
    sentence_id TEXT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    language TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'community',
    status TEXT NOT NULL DEFAULT 'unverified',
    dialect TEXT,
    story_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(sentence_id, language, text)
);

CREATE INDEX idx_translations_sentence ON translations(sentence_id);
CREATE INDEX idx_translations_language ON translations(language);
CREATE INDEX idx_translations_status ON translations(status);

-- Monolingual corpus
CREATE TABLE corpus (
    id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    source_file TEXT,
    tier TEXT DEFAULT 'sentence',
    domain TEXT DEFAULT 'general',
    quality TEXT DEFAULT 'raw',
    dialect TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(language, text)
);

CREATE INDEX idx_corpus_language ON corpus(language);
CREATE INDEX idx_corpus_source ON corpus(source);

-- Data sources registry
CREATE TABLE data_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    source_type TEXT NOT NULL,
    languages TEXT,
    license TEXT,
    notes TEXT,
    sentence_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Source materials (PDF catalog)
CREATE TABLE source_materials (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    source_type TEXT NOT NULL,
    language TEXT,
    level TEXT,
    term TEXT,
    file_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS but allow public read
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;
ALTER TABLE translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE corpus ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON sentences FOR SELECT USING (true);
CREATE POLICY "Public read" ON translations FOR SELECT USING (true);
CREATE POLICY "Public read" ON corpus FOR SELECT USING (true);
CREATE POLICY "Public read" ON data_sources FOR SELECT USING (true);
CREATE POLICY "Public read" ON source_materials FOR SELECT USING (true);

-- Service role can insert/update/delete
CREATE POLICY "Service write" ON sentences FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write" ON translations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write" ON corpus FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write" ON data_sources FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write" ON source_materials FOR ALL USING (true) WITH CHECK (true);
