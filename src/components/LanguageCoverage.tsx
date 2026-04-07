import { LANGUAGES } from '@/lib/constants'
import type { LanguageCoverage as LangCov } from '@/types'

interface Props {
  coverage: LangCov[]
  loading: boolean
}

export function LanguageCoverageGrid({ coverage, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {LANGUAGES.map((l) => (
          <div key={l.id} className="bg-slate-800 rounded-xl p-4 animate-pulse h-20" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {LANGUAGES.map((lang) => {
        const data = coverage.find((c) => c.language === lang.id)
        const pct = data?.percentage ?? 0
        const verified = data?.verified ?? 0
        const translated = data?.translated ?? 0

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
              <span className="text-brand-400 font-bold text-lg">{pct}%</span>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-700 rounded-full h-2.5 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500"
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-1.5">
              <span>{translated} translated</span>
              <span>{verified} verified</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
