import { useState, useEffect } from 'react'
import { getCoverage, getStats } from '@/lib/localData'
import type { LeaderboardEntry, LanguageCoverage } from '@/types'

export function useLeaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Local mode: no real contributors yet, show placeholder
    setEntries([])
    setLoading(false)
  }, [])

  return { entries, loading, refetch: () => {} }
}

export function useLanguageCoverage() {
  const [coverage, setCoverage] = useState<LanguageCoverage[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCoverage().then(data => {
      setCoverage(data)
      setLoading(false)
    })
  }, [])

  return { coverage, loading }
}

export function useStats() {
  const [stats, setStats] = useState<{
    total_sentences: number
    total_translations: number
    total_corpus?: number
    tiers: Record<string, number>
  } | null>(null)

  useEffect(() => {
    getStats().then(setStats)
  }, [])

  return stats
}
