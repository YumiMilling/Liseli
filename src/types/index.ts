export type Tier = 'word' | 'phrase' | 'sentence'

export type Domain =
  | 'daily_life'
  | 'health'
  | 'agriculture'
  | 'market_commerce'
  | 'education'
  | 'government'
  | 'weather'
  | 'family'
  | 'religion'
  | 'legal'

export type ZamLanguage =
  | 'bemba'
  | 'nyanja'
  | 'tonga'
  | 'lozi'
  | 'kaonde'
  | 'lunda'
  | 'luvale'

export type TranslationStatus = 'unverified' | 'verified' | 'flagged' | 'rejected'

export type Verdict = 'correct' | 'almost' | 'wrong'

export type SentenceSource = 'moe' | 'ai' | 'community'

export type DiscussionStatus = 'open' | 'resolved'

export interface Contributor {
  id: string
  handle: string
  languages: ZamLanguage[]
  province: string
  trust_score: number
  points: number
  streak_days: number
  joined: string
}

export interface Sentence {
  id: string
  english: string
  tier: Tier
  domain: Domain
  concept_id: string
  source: SentenceSource
  difficulty: number
  created_at: string
}

export interface Translation {
  id: string
  sentence_id: string
  contributor_id: string
  language: ZamLanguage
  text: string
  ai_original: string | null
  status: TranslationStatus
  created_at: string
  // joined fields
  sentence?: Sentence
  contributor?: Contributor
  vote_counts?: { correct: number; almost: number; wrong: number }
}

export interface Vote {
  id: string
  translation_id: string
  voter_id: string
  verdict: Verdict
  created_at: string
}

export interface Discussion {
  id: string
  translation_id: string
  status: DiscussionStatus
  created_at: string
  translation?: Translation
  comments?: DiscussionComment[]
}

export interface DiscussionComment {
  id: string
  discussion_id: string
  contributor_id: string
  text: string
  created_at: string
  contributor?: Contributor
}

export interface LanguageCoverage {
  language: ZamLanguage
  total_sentences: number
  translated: number
  verified: number
  percentage: number
}

export interface LeaderboardEntry {
  rank: number
  contributor: Contributor
  points: number
}
