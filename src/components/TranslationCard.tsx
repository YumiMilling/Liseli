import { useState } from 'react'
import type { Sentence, ZamLanguage } from '@/types'
import { TIERS } from '@/lib/constants'

interface Props {
  sentence: Sentence
  language: ZamLanguage
  aiAttempt?: string
  onSubmit: (text: string, aiOriginal: string | null) => void
}

export function TranslationCard({ sentence, language, aiAttempt, onSubmit }: Props) {
  const [text, setText] = useState(aiAttempt ?? '')
  const [submitted, setSubmitted] = useState(false)
  const tierInfo = TIERS.find((t) => t.id === sentence.tier)

  const handleSubmit = () => {
    if (!text.trim()) return
    onSubmit(text.trim(), aiAttempt ?? null)
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="bg-slate-800 rounded-xl p-5 border border-brand-600">
        <div className="flex items-center gap-2 text-brand-400">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span className="font-medium">Translation submitted! +{tierInfo?.points ?? 10} pts</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
      {/* Tier & domain badges */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs px-2 py-0.5 rounded-full bg-brand-900 text-brand-300 capitalize">
          {sentence.tier}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 capitalize">
          {sentence.domain.replace('_', ' ')}
        </span>
      </div>

      {/* English source */}
      <p className="text-lg font-medium text-white mb-1">{sentence.english}</p>
      <p className="text-xs text-slate-400 mb-4">
        Translate to <span className="text-brand-400 capitalize">{language}</span>
      </p>

      {/* AI attempt indicator */}
      {aiAttempt && (
        <div className="bg-slate-900 rounded-lg p-3 mb-3 border border-slate-600">
          <p className="text-xs text-slate-400 mb-1">AI attempt (edit or replace):</p>
          <p className="text-slate-300 italic">{aiAttempt}</p>
        </div>
      )}

      {/* Input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`Type your ${language} translation...`}
        className="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 resize-none"
        rows={2}
      />

      {/* Submit */}
      <div className="flex items-center justify-between mt-3">
        <span className="text-xs text-slate-400">+{tierInfo?.points ?? 10} pts</span>
        <button
          onClick={handleSubmit}
          disabled={!text.trim()}
          className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Submit Translation
        </button>
      </div>
    </div>
  )
}
