import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useVerificationQueue } from '@/hooks/useTranslations'
import { VoteButtons } from '@/components/VoteButtons'
import { LanguageSelector } from '@/components/LanguageSelector'
import type { ZamLanguage } from '@/types'
import { Link } from 'react-router-dom'

export function Validate() {
  const { contributor } = useAuth()
  const [language, setLanguage] = useState<ZamLanguage | undefined>(
    contributor?.languages[0]
  )
  const { translations, loading, submitVote } = useVerificationQueue(language)

  if (!contributor) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-3">Join to Validate</h2>
        <p className="text-slate-400 mb-6">
          Create a free account to vote on translations.
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
        <h2 className="text-xl font-bold">Validate</h2>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </div>

      {!language ? (
        <div className="text-center text-slate-400 py-12">
          Select a language to start validating.
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-36 animate-pulse" />
          ))}
        </div>
      ) : translations.length === 0 ? (
        <div className="text-center text-slate-400 py-12">
          No translations to validate right now. Check back soon!
        </div>
      ) : (
        <div className="space-y-4">
          {translations.map((translation) => (
            <div
              key={translation.id}
              className="bg-slate-800 rounded-xl p-5 border border-slate-700"
            >
              {/* English source */}
              <p className="text-sm text-slate-400 mb-1">English</p>
              <p className="text-white font-medium mb-3">
                {translation.sentence?.english}
              </p>

              {/* Translation */}
              <p className="text-sm text-slate-400 mb-1">
                <span className="capitalize">{translation.language}</span> translation
              </p>
              <p className="text-brand-300 text-lg mb-4">{translation.text}</p>

              {/* AI original if different */}
              {translation.ai_original && translation.ai_original !== translation.text && (
                <div className="bg-slate-900 rounded-lg p-2 mb-3 text-xs text-slate-400">
                  AI original: <span className="italic">{translation.ai_original}</span>
                </div>
              )}

              {/* Vote */}
              <VoteButtons
                onVote={(verdict) => submitVote(translation.id, contributor.id, verdict)}
                voteCounts={translation.vote_counts}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
