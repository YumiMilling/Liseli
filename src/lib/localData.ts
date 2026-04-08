/**
 * Local data layer — fetches from static JSON files exported from SQLite.
 * Replaces Supabase calls when running without a backend.
 */

import type { Sentence, Translation, LanguageCoverage, ZamLanguage, Tier, Domain } from '@/types'

interface SourceMaterial {
  id: string
  filename: string
  source_type: string
  language: string | null
  level: string | null
  term: string | null
  file_path: string | null
}

interface Stats {
  total_sentences: number
  total_translations: number
  languages: number
  tiers: Record<string, number>
  sources: Record<string, number>
  coverage: Record<string, { translated: number; percentage: number }>
}

const cache: Record<string, unknown> = {}

async function fetchJSON<T>(path: string): Promise<T> {
  if (cache[path]) return cache[path] as T
  const resp = await fetch(path)
  const data = await resp.json()
  cache[path] = data
  return data
}

export async function getSentences(opts?: {
  tier?: Tier
  domain?: Domain
  limit?: number
}): Promise<Sentence[]> {
  const all = await fetchJSON<Sentence[]>('/data/sentences.json')
  let filtered = all
  if (opts?.tier) filtered = filtered.filter(s => s.tier === opts.tier)
  if (opts?.domain) filtered = filtered.filter(s => s.domain === opts.domain)
  return filtered.slice(0, opts?.limit ?? 20)
}

export async function getTranslations(opts?: {
  language?: ZamLanguage
  sentenceId?: string
  status?: string
  limit?: number
}): Promise<(Translation & { english: string; tier: string; domain: string })[]> {
  const all = await fetchJSON<(Translation & { english: string; tier: string; domain: string })[]>('/data/translations.json')
  let filtered = all
  if (opts?.language) filtered = filtered.filter(t => t.language === opts.language)
  if (opts?.sentenceId) filtered = filtered.filter(t => t.sentence_id === opts.sentenceId)
  if (opts?.status) filtered = filtered.filter(t => t.status === opts.status)
  return filtered.slice(0, opts?.limit ?? 20)
}

export async function getCoverage(): Promise<LanguageCoverage[]> {
  return fetchJSON<LanguageCoverage[]>('/data/coverage.json')
}

export async function getStats(): Promise<Stats> {
  return fetchJSON<Stats>('/data/stats.json')
}

export async function getMaterials(): Promise<SourceMaterial[]> {
  return fetchJSON<SourceMaterial[]>('/data/materials.json')
}

export async function getTranslationsForSentence(
  sentenceId: string,
  language?: ZamLanguage
): Promise<(Translation & { english: string })[]> {
  const all = await fetchJSON<(Translation & { english: string })[]>('/data/translations.json')
  return all.filter(t =>
    t.sentence_id === sentenceId &&
    (!language || t.language === language)
  )
}
