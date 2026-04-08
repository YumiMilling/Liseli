import { useState, useCallback } from 'react'
import { useVerificationQueue } from '@/hooks/useTranslations'
import { LanguageSelector } from '@/components/LanguageSelector'
import { LANGUAGES } from '@/lib/constants'
import type { ZamLanguage, Verdict } from '@/types'

const VERDICTS: { id: Verdict; label: string; color: string; activeColor: string; icon: string }[] = [
  { id: 'correct', label: 'Correct', color: 'border-emerald-600 text-emerald-400', activeColor: 'bg-emerald-600 border-emerald-600 text-white', icon: '✓' },
  { id: 'almost', label: 'Almost', color: 'border-amber-600 text-amber-400', activeColor: 'bg-amber-600 border-amber-600 text-white', icon: '~' },
  { id: 'wrong', label: 'Wrong', color: 'border-red-600 text-red-400', activeColor: 'bg-red-600 border-red-600 text-white', icon: '✗' },
]

export function Validate() {
  const [language, setLanguage] = useState<ZamLanguage>('bemba')
  const { translations, loading, submitVote } = useVerificationQueue(language)
  const [index, setIndex] = useState(0)
  const [voted, setVoted] = useState<Verdict | null>(null)
  const [sessionCount, setSessionCount] = useState(0)
  const [animateOut, setAnimateOut] = useState(false)
  const [done, setDone] = useState(false)

  const translation = translations[index]
  const langInfo = LANGUAGES.find(l => l.id === language)
  const progress = translations.length > 0 ? ((index + (voted ? 1 : 0)) / translations.length) * 100 : 0

  const handleVote = useCallback((verdict: Verdict) => {
    if (voted || !translation) return
    setVoted(verdict)
    submitVote(translation.id, 'local-user', verdict)
    setSessionCount(c => c + 1)

    // Auto-advance after a moment
    setTimeout(() => {
      setAnimateOut(true)
      setTimeout(() => {
        if (index + 1 < translations.length) {
          setIndex(i => i + 1)
        } else {
          setDone(true)
        }
        setVoted(null)
        setAnimateOut(false)
      }, 250)
    }, 600)
  }, [voted, translation, index, translations.length, submitVote])

  if (done) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-6">
        <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center mb-6">
          <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold mb-2">All Reviewed</h2>
        <p className="text-slate-400 mb-2 text-center">
          You validated <span className="text-brand-400 font-semibold">{sessionCount}</span> translations
        </p>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-8 w-full max-w-xs text-center">
          <div className="text-3xl font-bold text-brand-400">+{sessionCount * 3}</div>
          <div className="text-sm text-slate-400">points earned</div>
        </div>
        <button
          onClick={() => { setIndex(0); setDone(false); setSessionCount(0) }}
          className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold transition-colors"
        >
          Keep Going
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Top bar */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-3">
          <LanguageSelector selected={language} onChange={(l) => l && setLanguage(l)} />
          {sessionCount > 0 && (
            <span className="text-xs text-brand-400">+{sessionCount * 3} pts</span>
          )}
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-xs text-slate-500 mt-1 block">{index + 1} of {translations.length}</span>
      </div>

      {/* Card area */}
      <div className="flex-1 flex items-center justify-center px-4">
        {loading ? (
          <div className="w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl h-72 animate-pulse" />
          </div>
        ) : !translation ? (
          <div className="text-center text-slate-400">
            <p>No translations to validate right now.</p>
          </div>
        ) : (
          <div
            className={`w-full max-w-md transition-all duration-250 ${
              animateOut ? 'opacity-0 translate-x-[-40px]' : 'opacity-100 translate-x-0'
            }`}
          >
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
              {/* English source */}
              <div className="px-6 pt-8 pb-4 text-center">
                <p className="text-sm text-slate-500 mb-2">English</p>
                <p className="text-xl font-semibold text-white leading-relaxed">
                  {translation.sentence?.english}
                </p>
              </div>

              <div className="h-px bg-slate-700 mx-6" />

              {/* Translation to judge */}
              <div className="px-6 py-6 text-center">
                <p className="text-sm text-slate-500 mb-2">
                  <span className="capitalize">{langInfo?.endonym}</span> translation
                </p>
                <p className="text-2xl text-brand-300 font-medium leading-relaxed mb-8">
                  {translation.text}
                </p>

                {/* Vote buttons — big, tappable */}
                <div className="flex gap-3">
                  {VERDICTS.map(({ id, label, color, activeColor, icon }) => (
                    <button
                      key={id}
                      onClick={() => handleVote(id)}
                      disabled={voted !== null}
                      className={`flex-1 py-4 rounded-xl border-2 font-semibold transition-all active:scale-95 ${
                        voted === id
                          ? activeColor
                          : voted
                            ? 'border-slate-700 text-slate-600 cursor-not-allowed'
                            : `${color} hover:bg-slate-700/50`
                      }`}
                    >
                      <span className="text-lg block mb-0.5">{icon}</span>
                      <span className="text-xs">{label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
