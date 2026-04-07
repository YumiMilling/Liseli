import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import { queueAction } from '@/lib/offline'
import type { Translation, Sentence, ZamLanguage, Domain, Tier, Verdict } from '@/types'

interface UseTranslationsOptions {
  language?: ZamLanguage
  domain?: Domain
  tier?: Tier
  status?: Translation['status']
}

export function useTranslations(options: UseTranslationsOptions = {}) {
  const [sentences, setSentences] = useState<Sentence[]>([])
  const [loading, setLoading] = useState(true)

  const fetchSentences = useCallback(async () => {
    setLoading(true)
    let query = supabase.from('sentences').select('*')

    if (options.tier) query = query.eq('tier', options.tier)
    if (options.domain) query = query.eq('domain', options.domain)

    query = query.limit(20).order('created_at', { ascending: false })

    const { data } = await query
    setSentences(data ?? [])
    setLoading(false)
  }, [options.tier, options.domain])

  useEffect(() => {
    fetchSentences()
  }, [fetchSentences])

  const submitTranslation = async (
    sentenceId: string,
    contributorId: string,
    language: ZamLanguage,
    text: string,
    aiOriginal: string | null
  ) => {
    if (!navigator.onLine) {
      await queueAction({
        type: 'translation',
        payload: {
          sentence_id: sentenceId,
          contributor_id: contributorId,
          language,
          text,
          ai_original: aiOriginal,
        },
      })
      return
    }

    const { error } = await supabase.from('translations').insert({
      sentence_id: sentenceId,
      contributor_id: contributorId,
      language,
      text,
      ai_original: aiOriginal,
    })
    if (error) throw error
  }

  return { sentences, loading, refetch: fetchSentences, submitTranslation }
}

export function useVerificationQueue(language?: ZamLanguage) {
  const [translations, setTranslations] = useState<Translation[]>([])
  const [loading, setLoading] = useState(true)

  const fetchQueue = useCallback(async () => {
    setLoading(true)
    let query = supabase
      .from('translations')
      .select(`
        *,
        sentence:sentences(*),
        votes(verdict)
      `)
      .eq('status', 'unverified')
      .limit(20)

    if (language) query = query.eq('language', language)

    const { data } = await query
    const mapped = (data ?? []).map((t) => ({
      ...t,
      vote_counts: {
        correct: t.votes?.filter((v: { verdict: string }) => v.verdict === 'correct').length ?? 0,
        almost: t.votes?.filter((v: { verdict: string }) => v.verdict === 'almost').length ?? 0,
        wrong: t.votes?.filter((v: { verdict: string }) => v.verdict === 'wrong').length ?? 0,
      },
    }))
    setTranslations(mapped)
    setLoading(false)
  }, [language])

  useEffect(() => {
    fetchQueue()
  }, [fetchQueue])

  const submitVote = async (
    translationId: string,
    voterId: string,
    verdict: Verdict
  ) => {
    if (!navigator.onLine) {
      await queueAction({
        type: 'vote',
        payload: { translation_id: translationId, voter_id: voterId, verdict },
      })
      return
    }

    const { error } = await supabase.from('votes').insert({
      translation_id: translationId,
      voter_id: voterId,
      verdict,
    })
    if (error) throw error
    await fetchQueue()
  }

  return { translations, loading, refetch: fetchQueue, submitVote }
}
