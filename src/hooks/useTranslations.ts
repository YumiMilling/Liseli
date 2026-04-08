import { useState, useEffect, useCallback } from 'react'
import { getSentences, getTranslations } from '@/lib/localData'
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
    const data = await getSentences({ tier: options.tier, domain: options.domain })
    setSentences(data)
    setLoading(false)
  }, [options.tier, options.domain])

  useEffect(() => {
    fetchSentences()
  }, [fetchSentences])

  const submitTranslation = async (
    _sentenceId: string,
    _contributorId: string,
    _language: ZamLanguage,
    _text: string,
    _aiOriginal: string | null
  ) => {
    // Local mode: no-op for now
    console.log('Local mode: translation submitted (not saved)', { _sentenceId, _language, _text })
  }

  return { sentences, loading, refetch: fetchSentences, submitTranslation }
}

export function useVerificationQueue(language?: ZamLanguage) {
  const [translations, setTranslations] = useState<Translation[]>([])
  const [loading, setLoading] = useState(true)

  const fetchQueue = useCallback(async () => {
    setLoading(true)
    const data = await getTranslations({ language, limit: 20 })
    const mapped: Translation[] = data.map(t => ({
      ...t,
      sentence: {
        id: t.sentence_id,
        english: t.english,
        tier: t.tier as Tier,
        domain: t.domain as Domain,
        concept_id: '',
        source: 'moe' as const,
        difficulty: 1,
        created_at: t.created_at,
      },
      ai_original: null,
      contributor_id: '',
      vote_counts: { correct: 3, almost: 0, wrong: 0 },
    }))
    setTranslations(mapped)
    setLoading(false)
  }, [language])

  useEffect(() => {
    fetchQueue()
  }, [fetchQueue])

  const submitVote = async (
    _translationId: string,
    _voterId: string,
    _verdict: Verdict
  ) => {
    console.log('Local mode: vote submitted (not saved)', { _translationId, _verdict })
  }

  return { translations, loading, refetch: fetchQueue, submitVote }
}
