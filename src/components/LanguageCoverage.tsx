import { LANGUAGES } from '@/lib/constants'
import type { LanguageCoverage as LangCov } from '@/types'

interface CoverageData extends LangCov {
  corpus_lines?: number
  corpus_words?: number
}

interface Props {
  coverage: CoverageData[]
  loading: boolean
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export function LanguageCoverageGrid({ coverage, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {LANGUAGES.map((l) => (
          <div key={l.id} className="bg-slate-800 rounded-xl p-4 animate-pulse h-24" />
        ))}
      </div>
    )
  }

  // Find max corpus for relative bar sizing
  const maxCorpus = Math.max(...coverage.map(c => c.corpus_words ?? c.translated ?? 0), 1)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {LANGUAGES.map((lang) => {
        const data = coverage.find((c) => c.language === lang.id)
        const pairs = data?.translated ?? 0
        const corpusLines = data?.corpus_lines ?? 0
        const corpusWords = data?.corpus_words ?? 0
        const barWidth = Math.max((corpusWords / maxCorpus) * 100, 2)

        return (
          <div
            key={lang.id}
            className="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="font-semibold text-white">{lang.name}</span>
                <span className="text-slate-400 text-sm ml-2">{lang.endonym}</span>
              </div>
              <span className="text-brand-400 font-bold">{formatNumber(corpusWords)}</span>
            </div>
            {/* Corpus bar */}
            <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden mb-2">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500"
                style={{ width: `${Math.min(barWidth, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>{formatNumber(pairs)} parallel pairs</span>
              <span>{formatNumber(corpusLines)} corpus lines</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
