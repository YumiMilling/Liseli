import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useTranslations } from '@/hooks/useTranslations'
import { TranslationCard } from '@/components/TranslationCard'
import { TierFilter } from '@/components/TierFilter'
import { LanguageSelector } from '@/components/LanguageSelector'
import type { Tier, ZamLanguage } from '@/types'
import { Link } from 'react-router-dom'

export function Translate() {
  const { contributor } = useAuth()
  const [tier, setTier] = useState<Tier | undefined>()
  const [language, setLanguage] = useState<ZamLanguage | undefined>(
    contributor?.languages[0]
  )
  const { sentences, loading, submitTranslation } = useTranslations({ tier })

  if (!contributor) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-3">Join to Translate</h2>
        <p className="text-slate-400 mb-6">
          Create a free account to start contributing translations.
        </p>
        <Link
          to="/profile"
          className="inline-block bg-brand-600 hover:bg-brand-700 px-6 py-2.5 rounded-lg font-medium transition-colors"
        >
          Create Account
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Translate</h2>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </div>

      <div className="mb-6">
        <TierFilter selected={tier} onChange={setTier} />
      </div>

      {!language ? (
        <div className="text-center text-slate-400 py-12">
          Select a language to start translating.
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-40 animate-pulse" />
          ))}
        </div>
      ) : sentences.length === 0 ? (
        <div className="text-center text-slate-400 py-12">
          No sentences available. Check back soon!
        </div>
      ) : (
        <div className="space-y-4">
          {sentences.map((sentence) => (
            <TranslationCard
              key={sentence.id}
              sentence={sentence}
              language={language}
              onSubmit={(text, aiOriginal) =>
                submitTranslation(sentence.id, contributor.id, language, text, aiOriginal)
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}
