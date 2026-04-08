import type { ZamLanguage, Domain, Tier } from '@/types'

export const LANGUAGES: { id: ZamLanguage; name: string; endonym: string }[] = [
  { id: 'bemba', name: 'Bemba', endonym: 'Icibemba' },
  { id: 'nyanja', name: 'Nyanja', endonym: 'Chinyanja' },
  { id: 'tonga', name: 'Tonga', endonym: 'Chitonga' },
  { id: 'lozi', name: 'Lozi', endonym: 'Silozi' },
  { id: 'kaonde', name: 'Kaonde', endonym: 'Kikaonde' },
  { id: 'lunda', name: 'Lunda', endonym: 'Chilunda' },
  { id: 'luvale', name: 'Luvale', endonym: 'Luvale' },
]

export const DOMAINS: { id: Domain; label: string; icon: string }[] = [
  { id: 'daily_life', label: 'Daily Life', icon: 'home' },
  { id: 'health', label: 'Health', icon: 'heart' },
  { id: 'agriculture', label: 'Agriculture', icon: 'leaf' },
  { id: 'market_commerce', label: 'Market & Commerce', icon: 'shopping-bag' },
  { id: 'education', label: 'Education', icon: 'book' },
  { id: 'government', label: 'Government', icon: 'building' },
  { id: 'weather', label: 'Weather', icon: 'cloud' },
  { id: 'family', label: 'Family', icon: 'users' },
  { id: 'religion', label: 'Religion', icon: 'star' },
  { id: 'legal', label: 'Legal', icon: 'scale' },
]

export const TIERS: { id: Tier; label: string; description: string; points: number }[] = [
  { id: 'word', label: 'Words', description: 'Single vocabulary items', points: 5 },
  { id: 'phrase', label: 'Phrases', description: 'Short combinations', points: 10 },
  { id: 'sentence', label: 'Sentences', description: 'Full structures', points: 15 },
]

export const POINTS = {
  translation: 10,
  vote: 3,
  discussion_resolve: 15,
  verified_bonus: 5,
} as const

export const PROVINCES = [
  'Central',
  'Copperbelt',
  'Eastern',
  'Luapula',
  'Lusaka',
  'Muchinga',
  'Northern',
  'North-Western',
  'Southern',
  'Western',
] as const

export const MILESTONES = [
  { count: 10, label: 'First 10 translations' },
  { count: 1, label: 'First verified translation', type: 'verified' as const },
  { count: 100, label: '100 translations' },
  { count: 7, label: 'Contributed across all languages', type: 'languages' as const },
] as const
