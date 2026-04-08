import { useState, useEffect, useCallback } from 'react'
import { LANGUAGES } from '@/lib/constants'
import type { ZamLanguage } from '@/types'

interface SourceInfo {
  name: string
  type: string
  count: number
  quality?: string
  words?: number
}

interface LangInventory {
  language: string
  sources: SourceInfo[]
  total_parallel: number
  total_corpus: number
  total_words: number
}

interface StatsData {
  total_sentences: number
  total_translations: number
  total_corpus?: number
  tiers: Record<string, number>
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

type View = 'overview' | 'language' | 'parallel' | 'corpus'

export function Browse() {
  const [view, setView] = useState<View>('overview')
  const [language, setLanguage] = useState<ZamLanguage>('nyanja')
  const [stats, setStats] = useState<StatsData | null>(null)
  const [inventory, setInventory] = useState<Record<string, LangInventory>>({})
  const [translations, setTranslations] = useState<Array<Record<string, string>>>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const pageSize = 50

  useEffect(() => {
    fetch('/data/stats.json').then(r => r.json()).then(setStats)
    fetch('/data/inventory.json').then(r => r.json()).then(setInventory)
  }, [])

  const loadTranslations = useCallback((lang: ZamLanguage) => {
    setLoading(true)
    fetch('/data/translations.json').then(r => r.json()).then((data: Array<Record<string, string>>) => {
      const filtered = data.filter(t => t.language === lang)
      setTranslations(filtered)
      setLoading(false)
      setPage(0)
    })
  }, [])

  const openLanguage = (lang: ZamLanguage) => {
    setLanguage(lang)
    setView('language')
  }

  const openParallel = (lang: ZamLanguage) => {
    setLanguage(lang)
    loadTranslations(lang)
    setView('parallel')
  }

  const filteredTranslations = searchQuery
    ? translations.filter(t =>
        t.english?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.text?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : translations

  const pagedTranslations = filteredTranslations.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.ceil(filteredTranslations.length / pageSize)

  const langInfo = LANGUAGES.find(l => l.id === language)
  const langInv = inventory[language]

  // Breadcrumb
  const Breadcrumb = () => (
    <div className="flex items-center gap-2 text-sm mb-4">
      <button onClick={() => setView('overview')} className="text-slate-400 hover:text-white transition-colors">
        Database
      </button>
      {view !== 'overview' && (
        <>
          <span className="text-slate-600">/</span>
          <button
            onClick={() => setView('language')}
            className={`transition-colors ${view === 'language' ? 'text-white' : 'text-slate-400 hover:text-white'}`}
          >
            {langInfo?.endonym}
          </button>
        </>
      )}
      {view === 'parallel' && (
        <>
          <span className="text-slate-600">/</span>
          <span className="text-white">Parallel pairs</span>
        </>
      )}
    </div>
  )

  // === OVERVIEW ===
  if (view === 'overview') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <h2 className="text-xl font-bold mb-1">Database</h2>
        <p className="text-slate-500 text-xs mb-4">Dev view — all raw data</p>

        {/* Global stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-2 mb-6">
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-brand-400">{formatNumber(stats.total_corpus || 0)}</div>
              <div className="text-[10px] text-slate-500">corpus</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-white">{formatNumber(stats.total_translations)}</div>
              <div className="text-[10px] text-slate-500">parallel</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-white">{formatNumber(stats.total_sentences)}</div>
              <div className="text-[10px] text-slate-500">sentences</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-white">7</div>
              <div className="text-[10px] text-slate-500">languages</div>
            </div>
          </div>
        )}

        {/* Language cards — clickable */}
        <div className="space-y-2">
          {LANGUAGES.map(lang => {
            const inv = inventory[lang.id]
            if (!inv) return null
            const maxWords = Math.max(...Object.values(inventory).map(i => i.total_words), 1)
            const barWidth = (inv.total_words / maxWords) * 100

            return (
              <button
                key={lang.id}
                onClick={() => openLanguage(lang.id)}
                className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-semibold text-white">{lang.name}</span>
                    <span className="text-slate-400 text-sm ml-2">{lang.endonym}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-brand-400 font-bold">{formatNumber(inv.total_words)}</span>
                    <span className="text-slate-500 text-xs ml-1">words</span>
                  </div>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden mb-1.5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-400"
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>{formatNumber(inv.total_parallel)} parallel</span>
                  <span>{formatNumber(inv.total_corpus)} corpus</span>
                  <span>{inv.sources.length} sources</span>
                </div>
              </button>
            )
          })}
        </div>

        {/* CC badge */}
        <div className="mt-6 text-center">
          <span className="inline-flex items-center gap-2 text-xs text-slate-500">
            <span className="font-mono bg-slate-800 px-2 py-0.5 rounded border border-slate-700">CC BY-SA</span>
            Open data. Belongs to Zambia.
          </span>
        </div>
      </div>
    )
  }

  // === LANGUAGE DETAIL ===
  if (view === 'language' && langInv) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />

        {/* Header */}
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
          <h3 className="text-xl font-bold mb-1">
            {langInfo?.name} <span className="text-slate-400 font-normal text-base">{langInfo?.endonym}</span>
          </h3>
          <div className="grid grid-cols-3 gap-4 mt-3">
            <div>
              <div className="text-2xl font-bold text-brand-400">{formatNumber(langInv.total_words)}</div>
              <div className="text-xs text-slate-500">total words</div>
            </div>
            <button onClick={() => openParallel(language)} className="text-left hover:bg-slate-700/50 rounded-lg p-1 -m-1 transition-colors">
              <div className="text-2xl font-bold text-white">{formatNumber(langInv.total_parallel)}</div>
              <div className="text-xs text-brand-400">parallel pairs →</div>
            </button>
            <div>
              <div className="text-2xl font-bold text-white">{formatNumber(langInv.total_corpus)}</div>
              <div className="text-xs text-slate-500">corpus lines</div>
            </div>
          </div>
        </div>

        {/* Sources */}
        {langInv.sources.filter(s => s.type === 'parallel').length > 0 && (
          <>
            <h4 className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              Parallel (EN ↔ {langInfo?.endonym})
            </h4>
            <div className="space-y-1.5 mb-5">
              {langInv.sources.filter(s => s.type === 'parallel').map((s, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-brand-500" />
                    <span className="text-sm text-white">{s.name}</span>
                    {s.quality && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        s.quality === 'verified' ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'
                      }`}>{s.quality}</span>
                    )}
                  </div>
                  <span className="text-sm text-slate-300 font-mono">{s.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {langInv.sources.filter(s => s.type === 'monolingual').length > 0 && (
          <>
            <h4 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Monolingual corpus</h4>
            <div className="space-y-1.5">
              {langInv.sources.filter(s => s.type === 'monolingual').map((s, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-slate-500" />
                    <span className="text-sm text-white">{s.name.replace('Corpus: ', '')}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-slate-300 font-mono">{s.count.toLocaleString()}</span>
                    {s.words && <span className="text-xs text-slate-500">~{formatNumber(s.words)}</span>}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    )
  }

  // === PARALLEL PAIRS VIEW ===
  if (view === 'parallel') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={e => { setSearchQuery(e.target.value); setPage(0) }}
            placeholder="Search English or target text..."
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-slate-500">
            {filteredTranslations.length.toLocaleString()} pairs
            {searchQuery && ` matching "${searchQuery}"`}
          </span>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="text-xs text-slate-400 hover:text-white disabled:opacity-30"
              >
                ← Prev
              </button>
              <span className="text-xs text-slate-500">{page + 1}/{totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="text-xs text-slate-400 hover:text-white disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="bg-slate-800 rounded-lg h-16 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-1.5">
            {pagedTranslations.map((t, i) => (
              <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-slate-600 transition-colors">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] text-slate-500 mb-0.5">EN</p>
                    <p className="text-sm text-white">{t.english}</p>
                  </div>
                  <div className="border-l border-slate-700 pl-3">
                    <p className="text-[10px] text-slate-500 mb-0.5">{langInfo?.endonym}</p>
                    <p className="text-sm text-brand-300">{t.text}</p>
                  </div>
                </div>
                <div className="flex gap-2 mt-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">{t.tier}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    t.status === 'verified' ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'
                  }`}>{t.status}</span>
                  {t.story_id && <span className="text-[10px] text-slate-600">story #{t.story_id}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return null
}
