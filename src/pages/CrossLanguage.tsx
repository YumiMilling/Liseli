import { useState, useEffect } from 'react'
import { LANGUAGES } from '@/lib/constants'
import type { ZamLanguage } from '@/types'

interface CrossPair {
  english: string
  tier: string
  lang_a: string
  text_a: string
  lang_b: string
  text_b: string
}

export function CrossLanguage() {
  const [pairs, setPairs] = useState<CrossPair[]>([])
  const [langA, setLangA] = useState<ZamLanguage>('bemba')
  const [langB, setLangB] = useState<ZamLanguage>('nyanja')
  const [loading, setLoading] = useState(true)
  const [showEnglish, setShowEnglish] = useState(true)

  const langAInfo = LANGUAGES.find(l => l.id === langA)
  const langBInfo = LANGUAGES.find(l => l.id === langB)

  useEffect(() => {
    setLoading(true)
    fetch('/data/cross_language.json').then(r => r.json()).then((data: CrossPair[]) => {
      const filtered = data.filter(p =>
        (p.lang_a === langA && p.lang_b === langB) ||
        (p.lang_a === langB && p.lang_b === langA)
      )
      setPairs(filtered)
      setLoading(false)
    })
  }, [langA, langB])

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h2 className="text-xl font-bold mb-1">Cross-Language</h2>
      <p className="text-slate-400 text-sm mb-5">
        Compare any two Zambian languages side by side — because understanding each other is what One Zambia means.
      </p>

      {/* Language pair selector */}
      <div className="bg-slate-800 rounded-2xl border border-slate-700 p-4 mb-5">
        <div className="flex items-center gap-3">
          {/* Language A */}
          <div className="flex-1">
            <p className="text-xs text-slate-500 mb-1.5">I speak</p>
            <div className="flex flex-wrap gap-1.5">
              {LANGUAGES.map(l => (
                <button
                  key={l.id}
                  onClick={() => {
                    if (l.id === langB) setLangB(langA)
                    setLangA(l.id)
                  }}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    langA === l.id
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-700 text-slate-400 hover:text-white'
                  }`}
                >
                  {l.endonym}
                </button>
              ))}
            </div>
          </div>

          {/* Swap button */}
          <button
            onClick={() => { const tmp = langA; setLangA(langB); setLangB(tmp) }}
            className="w-10 h-10 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center flex-shrink-0 transition-colors"
          >
            <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </button>

          {/* Language B */}
          <div className="flex-1">
            <p className="text-xs text-slate-500 mb-1.5">I'm learning</p>
            <div className="flex flex-wrap gap-1.5">
              {LANGUAGES.map(l => (
                <button
                  key={l.id}
                  onClick={() => {
                    if (l.id === langA) setLangA(langB)
                    setLangB(l.id)
                  }}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    langB === l.id
                      ? 'bg-emerald-700 text-white'
                      : 'bg-slate-700 text-slate-400 hover:text-white'
                  }`}
                >
                  {l.endonym}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Show English toggle */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-700">
          <button
            onClick={() => setShowEnglish(!showEnglish)}
            className={`w-8 h-5 rounded-full transition-colors relative ${
              showEnglish ? 'bg-brand-600' : 'bg-slate-600'
            }`}
          >
            <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.5 transition-all ${
              showEnglish ? 'left-[14px]' : 'left-[3px]'
            }`} />
          </button>
          <span className="text-xs text-slate-400">Show English</span>
        </div>
      </div>

      {/* Results header */}
      {!loading && pairs.length > 0 && (
        <p className="text-xs text-slate-500 mb-3">
          {pairs.length} sentences in {langAInfo?.endonym} and {langBInfo?.endonym}
        </p>
      )}

      {/* Pairs */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-24 animate-pulse" />
          ))}
        </div>
      ) : langA === langB ? (
        <div className="text-center text-slate-400 py-12">
          Select two different languages.
        </div>
      ) : pairs.length === 0 ? (
        <div className="text-center text-slate-400 py-12">
          No pairs found for this combination.
        </div>
      ) : (
        <div className="space-y-2.5">
          {pairs.slice(0, 80).map((p, i) => {
            const isA = p.lang_a === langA
            const textA = isA ? p.text_a : p.text_b
            const textB = isA ? p.text_b : p.text_a
            return (
              <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                {showEnglish && (
                  <p className="text-xs text-slate-500 mb-2">{p.english}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 mb-1">{langAInfo?.endonym}</p>
                    <p className="text-white">{textA}</p>
                  </div>
                  <div className="border-l border-slate-700 pl-4">
                    <p className="text-xs text-slate-500 mb-1">{langBInfo?.endonym}</p>
                    <p className="text-brand-300">{textB}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
