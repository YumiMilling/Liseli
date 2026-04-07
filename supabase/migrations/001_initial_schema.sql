-- Liseli Database Schema
-- Crowdsourced Zambian language translation platform

-- Custom types
CREATE TYPE tier_type AS ENUM ('word', 'phrase', 'sentence');
CREATE TYPE domain_type AS ENUM (
  'daily_life', 'health', 'agriculture', 'market_commerce',
  'education', 'government', 'weather', 'family', 'religion', 'legal'
);
CREATE TYPE zam_language AS ENUM (
  'bemba', 'nyanja', 'tonga', 'lozi', 'kaonde', 'lunda', 'luvale'
);
CREATE TYPE translation_status AS ENUM ('unverified', 'verified', 'flagged', 'rejected');
CREATE TYPE verdict_type AS ENUM ('correct', 'almost', 'wrong');
CREATE TYPE sentence_source AS ENUM ('moe', 'ai', 'community');
CREATE TYPE discussion_status AS ENUM ('open', 'resolved');

-- Contributors
CREATE TABLE contributors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  handle TEXT UNIQUE NOT NULL,
  languages zam_language[] NOT NULL DEFAULT '{}',
  province TEXT NOT NULL,
  trust_score NUMERIC(5,2) NOT NULL DEFAULT 0,
  points INTEGER NOT NULL DEFAULT 0,
  streak_days INTEGER NOT NULL DEFAULT 0,
  last_active DATE,
  joined TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Sentences (English source content)
CREATE TABLE sentences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  english TEXT NOT NULL,
  tier tier_type NOT NULL,
  domain domain_type NOT NULL,
  concept_id TEXT NOT NULL,
  source sentence_source NOT NULL DEFAULT 'community',
  difficulty INTEGER NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sentences_tier ON sentences(tier);
CREATE INDEX idx_sentences_domain ON sentences(domain);
CREATE INDEX idx_sentences_concept ON sentences(concept_id);

-- Translations
CREATE TABLE translations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sentence_id UUID NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
  contributor_id UUID NOT NULL REFERENCES contributors(id) ON DELETE CASCADE,
  language zam_language NOT NULL,
  text TEXT NOT NULL,
  ai_original TEXT,
  status translation_status NOT NULL DEFAULT 'unverified',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(sentence_id, contributor_id, language)
);

CREATE INDEX idx_translations_sentence ON translations(sentence_id);
CREATE INDEX idx_translations_language ON translations(language);
CREATE INDEX idx_translations_status ON translations(status);
CREATE INDEX idx_translations_contributor ON translations(contributor_id);

-- Votes
CREATE TABLE votes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  translation_id UUID NOT NULL REFERENCES translations(id) ON DELETE CASCADE,
  voter_id UUID NOT NULL REFERENCES contributors(id) ON DELETE CASCADE,
  verdict verdict_type NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(translation_id, voter_id)
);

CREATE INDEX idx_votes_translation ON votes(translation_id);

-- Discussions
CREATE TABLE discussions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  translation_id UUID UNIQUE NOT NULL REFERENCES translations(id) ON DELETE CASCADE,
  status discussion_status NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Discussion comments
CREATE TABLE discussion_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  discussion_id UUID NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
  contributor_id UUID NOT NULL REFERENCES contributors(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_discussion_comments_discussion ON discussion_comments(discussion_id);

-- Views

-- Language coverage view
CREATE OR REPLACE VIEW language_coverage AS
SELECT
  t.language,
  COUNT(DISTINCT s.id) AS total_sentences,
  COUNT(DISTINCT t.sentence_id) AS translated,
  COUNT(DISTINCT t.sentence_id) FILTER (WHERE t.status = 'verified') AS verified,
  ROUND(
    COUNT(DISTINCT t.sentence_id)::NUMERIC /
    NULLIF((SELECT COUNT(*) FROM sentences), 0) * 100, 1
  ) AS percentage
FROM sentences s
LEFT JOIN translations t ON t.sentence_id = s.id
GROUP BY t.language;

-- Verification queue: unverified translations needing votes
CREATE OR REPLACE VIEW verification_queue AS
SELECT
  t.*,
  s.english,
  s.tier,
  s.domain,
  COUNT(v.id) AS vote_count
FROM translations t
JOIN sentences s ON s.id = t.sentence_id
LEFT JOIN votes v ON v.translation_id = t.id
WHERE t.status = 'unverified'
GROUP BY t.id, s.english, s.tier, s.domain
ORDER BY vote_count ASC, t.created_at ASC;

-- Flagged queue: split-vote translations needing discussion
CREATE OR REPLACE VIEW flagged_queue AS
SELECT
  t.*,
  s.english,
  s.tier,
  s.domain
FROM translations t
JOIN sentences s ON s.id = t.sentence_id
WHERE t.status = 'flagged'
AND NOT EXISTS (
  SELECT 1 FROM discussions d WHERE d.translation_id = t.id
)
ORDER BY t.created_at ASC;

-- Row Level Security
ALTER TABLE contributors ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;
ALTER TABLE translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE discussions ENABLE ROW LEVEL SECURITY;
ALTER TABLE discussion_comments ENABLE ROW LEVEL SECURITY;

-- Public read access for all tables
CREATE POLICY "Public read" ON sentences FOR SELECT USING (true);
CREATE POLICY "Public read" ON translations FOR SELECT USING (true);
CREATE POLICY "Public read" ON votes FOR SELECT USING (true);
CREATE POLICY "Public read" ON discussions FOR SELECT USING (true);
CREATE POLICY "Public read" ON discussion_comments FOR SELECT USING (true);
CREATE POLICY "Public read" ON contributors FOR SELECT USING (true);

-- Authenticated write access
CREATE POLICY "Auth insert" ON translations FOR INSERT
  WITH CHECK (auth.uid() = (SELECT auth_id FROM contributors WHERE id = contributor_id));

CREATE POLICY "Auth insert" ON votes FOR INSERT
  WITH CHECK (auth.uid() = (SELECT auth_id FROM contributors WHERE id = voter_id));

CREATE POLICY "Auth insert" ON discussion_comments FOR INSERT
  WITH CHECK (auth.uid() = (SELECT auth_id FROM contributors WHERE id = contributor_id));

CREATE POLICY "Own profile update" ON contributors FOR UPDATE
  USING (auth.uid() = auth_id);

-- Function to auto-verify translations with 3+ correct votes
CREATE OR REPLACE FUNCTION check_translation_verification()
RETURNS TRIGGER AS $$
DECLARE
  correct_count INTEGER;
  wrong_count INTEGER;
  total_count INTEGER;
BEGIN
  SELECT
    COUNT(*) FILTER (WHERE verdict = 'correct'),
    COUNT(*) FILTER (WHERE verdict = 'wrong'),
    COUNT(*)
  INTO correct_count, wrong_count, total_count
  FROM votes
  WHERE translation_id = NEW.translation_id;

  IF correct_count >= 3 THEN
    UPDATE translations SET status = 'verified' WHERE id = NEW.translation_id;
    -- Award bonus points to the translator
    UPDATE contributors SET points = points + 5
    WHERE id = (SELECT contributor_id FROM translations WHERE id = NEW.translation_id);
  ELSIF total_count >= 3 AND wrong_count > 0 AND correct_count > 0 THEN
    UPDATE translations SET status = 'flagged' WHERE id = NEW.translation_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_vote_check_verification
  AFTER INSERT ON votes
  FOR EACH ROW
  EXECUTE FUNCTION check_translation_verification();

-- Function to award points
CREATE OR REPLACE FUNCTION award_translation_points()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE contributors SET points = points + 10
  WHERE id = NEW.contributor_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_translation_award_points
  AFTER INSERT ON translations
  FOR EACH ROW
  EXECUTE FUNCTION award_translation_points();

CREATE OR REPLACE FUNCTION award_vote_points()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE contributors SET points = points + 3
  WHERE id = NEW.voter_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_vote_award_points
  AFTER INSERT ON votes
  FOR EACH ROW
  EXECUTE FUNCTION award_vote_points();
