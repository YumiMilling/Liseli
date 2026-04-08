import { useState, useCallback } from 'react'
import { useTranslations } from '@/hooks/useTranslations'
import { LanguageSelector } from '@/components/LanguageSelector'
import { TIERS, LANGUAGES } from '@/lib/constants'
import type { Tier, ZamLanguage } from '@/types'

export function Translate() {
  const [tier, setTier] = useState<Tier | undefined>('word')
  const [language, setLanguage] = useState<ZamLanguage>('bemba')
  const { sentences, loading, submitTranslation, refetch } = useTranslations({ tier, excludeSentences: true })
  const [index, setIndex] = useState(0)
  const [text, setText] = useState('')
  const [phase, setPhase] = useState<'input' | 'submitted' | 'done'>('input')
  const [sessionCount, setSessionCount] = useState(0)
  const [sessionPoints, setSessionPoints] = useState(0)
  const [animateOut, setAnimateOut] = useState(false)

  const sentence = sentences[index]
  const tierInfo = TIERS.find(t => t.id === sentence?.tier)
  const langInfo = LANGUAGES.find(l => l.id === language)
  const progress = sentences.length > 0 ? ((index + (phase === 'input' ? 0 : 1)) / sentences.length) * 100 : 0

  const handleSubmit = useCallback(() => {
    if (!text.trim() || !sentence) return
    submitTranslation(sentence.id, 'local-user', language, text.trim(), null)
    setPhase('submitted')
    setSessionCount(c => c + 1)
    setSessionPoints(p => p + (tierInfo?.points ?? 10))
  }, [text, sentence, language, submitTranslation, tierInfo])

  const handleNext = useCallback(() => {
    setAnimateOut(true)
    setTimeout(() => {
      if (index + 1 < sentences.length) {
        setIndex(i => i + 1)
      } else {
        setPhase('done')
        setAnimateOut(false)
        return
      }
      setText('')
      setPhase('input')
      setAnimateOut(false)
    }, 250)
  }, [index, sentences.length])

  const handleSkip = useCallback(() => {
    setAnimateOut(true)
    setTimeout(() => {
      if (index + 1 < sentences.length) {
        setIndex(i => i + 1)
      }
      setText('')
      setAnimateOut(false)
    }, 200)
  }, [index, sentences.length])

  const handleNewSession = () => {
    setIndex(0)
    setText('')
    setPhase('input')
    setSessionCount(0)
    setSessionPoints(0)
    refetch()
  }

  // Session complete screen
  if (phase === 'done') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-6">
        <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center mb-6">
          <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold mb-2">Session Complete</h2>
        <p className="text-slate-400 mb-6 text-center">
          You translated <span className="text-brand-400 font-semibold">{sessionCount}</span> items into{' '}
          <span className="text-brand-400 font-semibold capitalize">{langInfo?.endonym}</span>
        </p>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-8 w-full max-w-xs text-center">
          <div className="text-3xl font-bold text-brand-400">+{sessionPoints}</div>
          <div className="text-sm text-slate-400">points earned</div>
        </div>
        <button
          onClick={handleNewSession}
          className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold transition-colors"
        >
          Keep Going
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Top bar: language + progress */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-3">
          <LanguageSelector selected={language} onChange={(l) => l && setLanguage(l)} />
          <div className="flex items-center gap-3">
            {/* Tier pills — words and phrases only */}
            <div className="flex gap-1">
              {TIERS.filter(t => t.id !== 'sentence').map(t => (
                <button
                  key={t.id}
                  onClick={() => setTier(tier === t.id ? undefined : t.id)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    tier === t.id
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-xs text-slate-500">{index + 1} of {sentences.length}</span>
          {sessionCount > 0 && (
            <span className="text-xs text-brand-400">+{sessionPoints} pts this session</span>
          )}
        </div>
      </div>

      {/* Card area */}
      <div className="flex-1 flex items-center justify-center px-4">
        {loading ? (
          <div className="w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl h-64 animate-pulse" />
          </div>
        ) : !sentence ? (
          <div className="text-center text-slate-400">
            <p className="mb-4">No sentences available.</p>
            <button onClick={handleNewSession} className="text-brand-400 hover:text-brand-300">
              Try refreshing
            </button>
          </div>
        ) : (
          <div
            className={`w-full max-w-md transition-all duration-250 ${
              animateOut ? 'opacity-0 translate-x-[-40px]' : 'opacity-100 translate-x-0'
            }`}
          >
            {/* The Card */}
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
              {/* English source — big and centered */}
              <div className="px-6 pt-8 pb-6 text-center">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-900/60 text-brand-300 capitalize">
                    {sentence.tier}
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-700/60 text-slate-400 capitalize">
                    {sentence.domain.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-2xl font-semibold text-white leading-relaxed">
                  {sentence.english}
                </p>
                <p className="text-sm text-slate-500 mt-3">
                  How do you say this in <span className="text-brand-400">{langInfo?.endonym}</span>?
                </p>
              </div>

              {/* Divider */}
              <div className="h-px bg-slate-700 mx-6" />

              {/* Input / Result area */}
              <div className="px-6 py-6">
                {phase === 'input' ? (
                  <>
                    <textarea
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      placeholder={`Type your ${langInfo?.endonym ?? language} translation...`}
                      className="w-full bg-slate-900 border border-slate-600 rounded-xl p-4 text-white text-lg placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 resize-none"
                      rows={2}
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSubmit()
                        }
                      }}
                    />
                    <div className="flex items-center justify-between mt-4">
                      <button
                        onClick={handleSkip}
                        className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
                      >
                        Skip
                      </button>
                      <button
                        onClick={handleSubmit}
                        disabled={!text.trim()}
                        className="bg-brand-600 hover:bg-brand-700 disabled:opacity-30 disabled:cursor-not-allowed px-6 py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95"
                      >
                        Submit
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="text-center">
                    <div className="inline-flex items-center gap-2 text-brand-400 mb-3">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-semibold">+{tierInfo?.points ?? 10} pts</span>
                    </div>
                    <p className="text-brand-300 text-lg mb-6">{text}</p>
                    <button
                      onClick={handleNext}
                      className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold transition-all active:scale-95 w-full"
                    >
                      {index + 1 < sentences.length ? 'Next' : 'Finish'}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Keyboard hint */}
            {phase === 'input' && (
              <p className="text-center text-xs text-slate-600 mt-3">
                Press Enter to submit
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
