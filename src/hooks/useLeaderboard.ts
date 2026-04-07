import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import type { LeaderboardEntry, LanguageCoverage } from '@/types'

export function useLeaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    setLoading(true)
    const { data } = await supabase
      .from('contributors')
      .select('*')
      .order('points', { ascending: false })
      .limit(50)

    const mapped: LeaderboardEntry[] = (data ?? []).map((c, i) => ({
      rank: i + 1,
      contributor: c,
      points: c.points,
    }))
    setEntries(mapped)
    setLoading(false)
  }, [])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { entries, loading, refetch: fetch }
}

export function useLanguageCoverage() {
  const [coverage, setCoverage] = useState<LanguageCoverage[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetch() {
      const { data } = await supabase
        .from('language_coverage')
        .select('*')
      setCoverage(data ?? [])
      setLoading(false)
    }
    fetch()
  }, [])

  return { coverage, loading }
}
