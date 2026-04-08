import { useState, useEffect } from 'react'
import { LANGUAGES } from '@/lib/constants'
import type { ZamLanguage } from '@/types'

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

interface Story {
  id: string
  title: string
  line_count: number
  languages: string[]
  lines: { english: string; tier: string; translations: Record<string, string> }[]
}

interface BibleBook {
  code: string
  name: string
  verse_count: number
  languages: string[]
  verses: { ref: string; english: string; translations: Record<string, string> }[]
}

interface CorpusGroup {
  source: string
  language: string
  total_lines: number
  files: { name: string; line_count: number; sample: string[] }[]
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GrammarData = Record<string, any>

type View =
  | { type: 'home' }
  | { type: 'source'; source: string }
  | { type: 'story'; storyId: string }
  | { type: 'bible-book'; bookCode: string }
  | { type: 'corpus-detail'; source: string; language: string }

export function Browse() {
  const [view, setView] = useState<View>({ type: 'home' })
  const [stories, setStories] = useState<Story[]>([])
  const [bible, setBible] = useState<BibleBook[]>([])
  const [stats, setStats] = useState<{ total_sentences: number; total_translations: number; total_corpus: number } | null>(null)
  const [viewLang, setViewLang] = useState<ZamLanguage>('nyanja')
  const [corpusGroups, setCorpusGroups] = useState<CorpusGroup[]>([])
  const [dictionary, setDictionary] = useState<{ english: string; translations: Record<string, { text: string; status: string }> }[]>([])
  const [grammar, setGrammar] = useState<GrammarData | null>(null)
  const [searchQ, setSearchQ] = useState('')
  const [page, setPage] = useState(0)

  useEffect(() => {
    fetch('/data/stats.json').then(r => r.json()).then(setStats)
  }, [])

  const loadStories = () => {
    if (stories.length === 0) {
      fetch('/data/storybooks.json').then(r => r.json()).then(setStories)
    }
  }

  const loadBible = () => {
    if (bible.length === 0) {
      fetch('/data/bible.json').then(r => r.json()).then(setBible)
    }
  }

  const loadDictionary = () => {
    setPage(0)
    setSearchQ('')
    if (dictionary.length === 0) {
      fetch('/data/dictionary.json').then(r => r.json()).then(setDictionary)
    }
  }

  const loadGrammar = () => {
    if (!grammar) {
      fetch('/data/grammar.json').then(r => r.json()).then(setGrammar)
    }
  }

  const loadCorpus = () => {
    if (corpusGroups.length === 0) {
      fetch('/data/corpus_browse.json').then(r => r.json()).then(setCorpusGroups)
    }
  }

  // Breadcrumb
  const crumbs: { label: string; onClick?: () => void }[] = [
    { label: 'Database', onClick: () => setView({ type: 'home' }) },
  ]
  if (view.type === 'source') {
    const srcLabels: Record<string, string> = { storybooks: 'Storybooks Zambia', bible: 'Bible', dictionary: 'Dictionary', grammar: 'Grammar Patterns', corpus: 'Corpus' }
    crumbs.push({ label: srcLabels[view.source] ?? view.source })
  } else if (view.type === 'story') {
    crumbs.push({ label: 'Storybooks', onClick: () => setView({ type: 'source', source: 'storybooks' }) })
    const story = stories.find(s => s.id === view.storyId)
    crumbs.push({ label: story ? `#${story.id}` : view.storyId })
  } else if (view.type === 'bible-book') {
    crumbs.push({ label: 'Bible', onClick: () => setView({ type: 'source', source: 'bible' }) })
    const book = bible.find(b => b.code === view.bookCode)
    crumbs.push({ label: book?.name ?? view.bookCode })
  } else if (view.type === 'corpus-detail') {
    crumbs.push({ label: 'Corpus', onClick: () => setView({ type: 'source', source: 'corpus' }) })
    const langInfo = LANGUAGES.find(l => l.id === view.language)
    crumbs.push({ label: `${langInfo?.endonym ?? view.language} — ${view.source}` })
  }

  const Breadcrumb = () => (
    <div className="flex items-center gap-1.5 text-sm mb-4 flex-wrap">
      {crumbs.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span className="text-slate-600">/</span>}
          {c.onClick ? (
            <button onClick={c.onClick} className="text-slate-400 hover:text-white transition-colors">{c.label}</button>
          ) : (
            <span className="text-white">{c.label}</span>
          )}
        </span>
      ))}
    </div>
  )

  // === HOME ===
  if (view.type === 'home') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <h2 className="text-xl font-bold mb-1">Database</h2>
        <p className="text-slate-500 text-xs mb-4">Dev view — explore all raw data</p>

        {stats && (
          <div className="grid grid-cols-3 gap-2 mb-6">
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-brand-400">{fmt(stats.total_translations)}</div>
              <div className="text-[10px] text-slate-500">parallel pairs</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-white">{fmt(stats.total_corpus)}</div>
              <div className="text-[10px] text-slate-500">corpus lines</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className="text-lg font-bold text-white">7</div>
              <div className="text-[10px] text-slate-500">languages</div>
            </div>
          </div>
        )}

        <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Data Sources</h3>
        <div className="space-y-2">
          <button
            onClick={() => { loadStories(); setView({ type: 'source', source: 'storybooks' }) }}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Storybooks Zambia</p>
                <p className="text-xs text-slate-400">40 stories, all 7 languages + English, CC-BY</p>
              </div>
              <span className="text-slate-400">→</span>
            </div>
          </button>

          <button
            onClick={() => { loadBible(); setView({ type: 'source', source: 'bible' }) }}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Bible</p>
                <p className="text-xs text-slate-400">66 books, ~31K verses, 7 languages aligned</p>
              </div>
              <span className="text-slate-400">→</span>
            </div>
          </button>

          <button
            onClick={() => { loadDictionary(); setView({ type: 'source', source: 'dictionary' }) }}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Dictionary</p>
                <p className="text-xs text-slate-400">14K+ English words with translations in 7 languages (draft, unverified)</p>
              </div>
              <span className="text-slate-400">→</span>
            </div>
          </button>

          <button
            onClick={() => { loadGrammar(); setView({ type: 'source', source: 'grammar' }) }}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Grammar Patterns</p>
                <p className="text-xs text-slate-400">Noun prefixes, cognates, sentence structure — derived from parallel data</p>
              </div>
              <span className="text-slate-400">→</span>
            </div>
          </button>

          <button
            onClick={() => { loadCorpus(); setView({ type: 'source', source: 'corpus' }) }}
            className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Monolingual Corpus</p>
                <p className="text-xs text-slate-400">MoE modules, USAID, ZambeziVoice, JW.org — raw text by language</p>
              </div>
              <span className="text-slate-400">→</span>
            </div>
          </button>
        </div>

        <div className="mt-4 text-center">
          <span className="inline-flex items-center gap-2 text-xs text-slate-500">
            <span className="font-mono bg-slate-800 px-2 py-0.5 rounded border border-slate-700">CC BY-SA</span>
            Open data. Belongs to Zambia.
          </span>
        </div>
      </div>
    )
  }

  // === STORYBOOKS LIST ===
  if (view.type === 'source' && view.source === 'storybooks') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <h2 className="text-lg font-bold mb-4">Storybooks Zambia — {stories.length} stories</h2>
        <div className="space-y-2">
          {stories.map(story => (
            <button
              key={story.id}
              onClick={() => setView({ type: 'story', storyId: story.id })}
              className="w-full bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-brand-600 transition-colors text-left"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">#{story.id}: {story.title}</p>
                  <p className="text-xs text-slate-400 mt-1">{story.line_count} lines, {story.languages.length} languages</p>
                </div>
                <span className="text-slate-400 ml-2">→</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // === SINGLE STORY ===
  if (view.type === 'story') {
    const story = stories.find(s => s.id === view.storyId)
    if (!story) return <div className="p-4 text-slate-400">Story not found</div>

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">Story #{story.id}</h2>
          <select
            value={viewLang}
            onChange={e => setViewLang(e.target.value as ZamLanguage)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            {LANGUAGES.filter(l => story.languages.includes(l.id)).map(l => (
              <option key={l.id} value={l.id}>{l.endonym}</option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          {story.lines.map((line, i) => (
            <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <p className="text-sm text-slate-400 mb-1">English</p>
              <p className="text-white mb-3">{line.english}</p>
              <p className="text-sm text-slate-400 mb-1 capitalize">{LANGUAGES.find(l => l.id === viewLang)?.endonym}</p>
              <p className="text-brand-300 text-lg">{line.translations[viewLang] ?? '—'}</p>
              {/* Show all languages collapsed */}
              <details className="mt-3">
                <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">All {Object.keys(line.translations).length} languages</summary>
                <div className="mt-2 space-y-1">
                  {LANGUAGES.map(l => {
                    const text = line.translations[l.id]
                    if (!text) return null
                    return (
                      <div key={l.id} className="flex gap-2 text-sm">
                        <span className="text-slate-500 w-20 flex-shrink-0 text-right">{l.endonym}</span>
                        <span className="text-slate-300">{text}</span>
                      </div>
                    )
                  })}
                </div>
              </details>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // === BIBLE BOOKS LIST ===
  if (view.type === 'source' && view.source === 'bible') {
    const ot = bible.filter(b => ['GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','1SA','2SA','1KI','2KI','1CH','2CH','EZR','NEH','EST','JOB','PSA','PRO','ECC','SNG','ISA','JER','LAM','EZK','DAN','HOS','JOL','AMO','OBA','JON','MIC','NAM','HAB','ZEP','HAG','ZEC','MAL'].includes(b.code))
    const nt = bible.filter(b => !ot.includes(b))

    const BookList = ({ books, title }: { books: BibleBook[]; title: string }) => (
      <>
        <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2 mt-4">{title}</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
          {books.map(book => (
            <button
              key={book.code}
              onClick={() => setView({ type: 'bible-book', bookCode: book.code })}
              className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-brand-600 transition-colors text-left"
            >
              <p className="text-white text-sm font-medium">{book.name}</p>
              <p className="text-[10px] text-slate-500">{book.verse_count} verses, {book.languages.length} langs</p>
            </button>
          ))}
        </div>
      </>
    )

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <h2 className="text-lg font-bold mb-1">Bible — {bible.length} books</h2>
        <p className="text-xs text-slate-400 mb-4">{bible.reduce((s, b) => s + b.verse_count, 0).toLocaleString()} verses, aligned across 7 languages + English</p>
        <BookList books={ot} title="Old Testament" />
        <BookList books={nt} title="New Testament" />
      </div>
    )
  }

  // === SINGLE BIBLE BOOK ===
  if (view.type === 'bible-book') {
    const book = bible.find(b => b.code === view.bookCode)
    if (!book) return <div className="p-4 text-slate-400">Book not found</div>

    const filtered = searchQ
      ? book.verses.filter(v =>
          v.english.toLowerCase().includes(searchQ.toLowerCase()) ||
          (v.translations[viewLang] ?? '').toLowerCase().includes(searchQ.toLowerCase())
        )
      : book.verses

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />

        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold">{book.name}</h2>
          <select
            value={viewLang}
            onChange={e => setViewLang(e.target.value as ZamLanguage)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            {LANGUAGES.filter(l => book.languages.includes(l.id)).map(l => (
              <option key={l.id} value={l.id}>{l.endonym}</option>
            ))}
          </select>
        </div>

        <input
          type="text"
          value={searchQ}
          onChange={e => setSearchQ(e.target.value)}
          placeholder="Search verses..."
          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none mb-3"
        />

        <p className="text-xs text-slate-500 mb-3">{filtered.length} verses</p>

        <div className="space-y-1.5">
          {filtered.slice(0, 100).map((verse, i) => (
            <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
              <div className="flex gap-2 items-start">
                <span className="text-[10px] text-slate-600 font-mono w-10 flex-shrink-0 pt-0.5">{verse.ref}</span>
                <div className="flex-1 grid grid-cols-2 gap-3">
                  <p className="text-sm text-white">{verse.english}</p>
                  <p className="text-sm text-brand-300">{verse.translations[viewLang] ?? '—'}</p>
                </div>
              </div>
            </div>
          ))}
          {filtered.length > 100 && (
            <p className="text-center text-xs text-slate-500 py-4">
              Showing first 100 of {filtered.length} verses. Use search to filter.
            </p>
          )}
        </div>
      </div>
    )
  }

  // === DICTIONARY ===
  if (view.type === 'source' && view.source === 'dictionary') {
    if (dictionary.length === 0) {
      return (
        <div className="max-w-3xl mx-auto px-4 py-6">
          <Breadcrumb />
          <h2 className="text-lg font-bold mb-4">Dictionary</h2>
          <p className="text-slate-400 text-sm">Loading 14,000+ entries...</p>
          <div className="space-y-2 mt-4">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="bg-slate-800 rounded-lg h-12 animate-pulse" />
            ))}
          </div>
        </div>
      )
    }

    const filtered = searchQ
      ? dictionary.filter(d => d.english.toLowerCase().includes(searchQ.toLowerCase()) ||
          Object.values(d.translations).some(t => t.text.toLowerCase().includes(searchQ.toLowerCase())))
      : dictionary

    const paged = filtered.slice(page * 100, (page + 1) * 100)
    const totalPg = Math.ceil(filtered.length / 100)

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <h2 className="text-lg font-bold mb-1">Dictionary</h2>
        <p className="text-xs text-slate-400 mb-3">
          {dictionary.length.toLocaleString()} English words, statistically extracted from parallel data. Draft — needs verification.
        </p>

        {/* Language filter + search */}
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={searchQ}
            onChange={e => { setSearchQ(e.target.value); setPage(0) }}
            placeholder="Search English or any language..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
          />
          <select
            value={viewLang}
            onChange={e => setViewLang(e.target.value as ZamLanguage)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            {LANGUAGES.map(l => (
              <option key={l.id} value={l.id}>{l.endonym}</option>
            ))}
          </select>
        </div>

        {/* Alphabet jump bar */}
        <div className="flex flex-wrap gap-1 mb-3">
          {'abcdefghijklmnopqrstuvwxyz'.split('').map(letter => {
            const idx = filtered.findIndex(d => d.english.toLowerCase().startsWith(letter))
            return (
              <button
                key={letter}
                onClick={() => { if (idx >= 0) setPage(Math.floor(idx / 100)) }}
                disabled={idx < 0}
                className={`w-7 h-7 rounded text-xs font-medium transition-colors ${
                  idx >= 0 ? 'bg-slate-800 text-slate-300 hover:bg-brand-600 hover:text-white' : 'bg-slate-800/50 text-slate-600'
                }`}
              >
                {letter.toUpperCase()}
              </button>
            )
          })}
        </div>

        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-slate-500">{filtered.length.toLocaleString()} words</span>
          {totalPg > 1 && (
            <div className="flex items-center gap-2">
              <button onClick={() => { setPage(p => Math.max(0, p - 1)); window.scrollTo(0, 0) }} disabled={page === 0}
                className="text-xs text-slate-400 hover:text-white disabled:opacity-30">← Prev</button>
              <span className="text-xs text-slate-500">{page + 1}/{totalPg}</span>
              <button onClick={() => { setPage(p => Math.min(totalPg - 1, p + 1)); window.scrollTo(0, 0) }} disabled={page >= totalPg - 1}
                className="text-xs text-slate-400 hover:text-white disabled:opacity-30">Next →</button>
            </div>
          )}
        </div>

        <div className="space-y-1">
          {paged.map((d, i) => {
            const primary = d.translations[viewLang]
            const otherLangs = Object.entries(d.translations).filter(([l]) => l !== viewLang)
            return (
              <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-baseline gap-3">
                      <span className="text-white font-medium">{d.english}</span>
                      {primary && (
                        <span className="text-brand-300">{primary.text}</span>
                      )}
                      {!primary && (
                        <span className="text-slate-500 text-sm italic">no {LANGUAGES.find(l => l.id === viewLang)?.endonym} entry</span>
                      )}
                    </div>
                  </div>
                  {primary && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ml-2 flex-shrink-0 ${
                      primary.status === 'verified' ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'
                    }`}>{primary.status}</span>
                  )}
                </div>
                {otherLangs.length > 0 && (
                  <details className="mt-2">
                    <summary className="text-[10px] text-slate-500 cursor-pointer hover:text-slate-300">
                      {otherLangs.length} other language{otherLangs.length > 1 ? 's' : ''}
                    </summary>
                    <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5">
                      {otherLangs.map(([lang, t]) => (
                        <span key={lang} className="text-xs">
                          <span className="text-slate-500">{LANGUAGES.find(l => l.id === lang)?.endonym}: </span>
                          <span className="text-slate-300">{t.text}</span>
                        </span>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )
          })}
        </div>

        {/* Bottom pagination */}
        {totalPg > 1 && (
          <div className="flex items-center justify-center gap-4 mt-4 py-4 border-t border-slate-700">
            <button onClick={() => { setPage(p => Math.max(0, p - 1)); window.scrollTo(0, 0) }} disabled={page === 0}
              className="px-4 py-2 bg-slate-800 rounded-lg text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition-colors">← Prev</button>
            <span className="text-sm text-slate-400">{page + 1} of {totalPg}</span>
            <button onClick={() => { setPage(p => Math.min(totalPg - 1, p + 1)); window.scrollTo(0, 0) }} disabled={page >= totalPg - 1}
              className="px-4 py-2 bg-slate-800 rounded-lg text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition-colors">Next →</button>
          </div>
        )}
      </div>
    )
  }

  // === GRAMMAR PATTERNS ===
  if (view.type === 'source' && view.source === 'grammar') {
    if (!grammar) {
      return (
        <div className="max-w-3xl mx-auto px-4 py-6">
          <Breadcrumb />
          <h2 className="text-lg font-bold mb-4">Grammar Patterns</h2>
          <div className="space-y-3">{Array.from({length:5}).map((_,i) => <div key={i} className="bg-slate-800 rounded-xl h-24 animate-pulse" />)}</div>
        </div>
      )
    }

    const langInfo = LANGUAGES.find(l => l.id === viewLang)
    const gLang = (grammar as Record<string, unknown> & { languages: Record<string, unknown>; shared_roots: { cognates: { word: string; languages: string[]; count: number }[] } }).languages[viewLang] as Record<string, unknown> | undefined
    const sharedRoots = (grammar as unknown as { shared_roots: { cognates: { word: string; languages: string[]; count: number }[] } }).shared_roots

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const g = gLang as any

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">Grammar: {langInfo?.endonym}</h2>
          <select value={viewLang} onChange={e => setViewLang(e.target.value as ZamLanguage)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white">
            {LANGUAGES.map(l => <option key={l.id} value={l.id}>{l.name} ({l.endonym})</option>)}
          </select>
        </div>
        <p className="text-xs text-slate-400 mb-6">Derived from {viewLang === 'kaonde' ? '~8K' : '~31K'} parallel Bible verses. Draft — needs linguist verification.</p>

        {g && (
          <>
            {/* Word order */}
            <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
              <h3 className="text-sm font-semibold mb-2">Word Order &amp; Length</h3>
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-2xl font-bold text-brand-400">{g.word_order?.avg_word_ratio}x</span>
                  <p className="text-xs text-slate-400">{g.word_order?.description} than English</p>
                </div>
              </div>
              {g.word_order?.statement_examples?.slice(0, 3).map((ex: {english: string; translation: string}, i: number) => (
                <div key={i} className="mt-3 border-t border-slate-700 pt-3">
                  <p className="text-sm text-white">{ex.english}</p>
                  <p className="text-sm text-brand-300">{ex.translation}</p>
                </div>
              ))}
            </div>

            {/* Noun classes */}
            <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
              <h3 className="text-sm font-semibold mb-1">Noun Class Prefixes</h3>
              <p className="text-xs text-slate-500 mb-3">Bantu languages mark nouns with class prefixes that determine agreement on verbs, adjectives, and pronouns.</p>
              <div className="space-y-1.5">
                {g.noun_classes?.prefixes?.slice(0, 15).map((p: {prefix: string; distinct_words: number; examples: string[]}, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="font-mono text-brand-300 text-sm w-10 font-bold">{p.prefix}-</span>
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-brand-600 rounded-full" style={{ width: `${Math.min(p.distinct_words / 2, 100)}%` }} />
                    </div>
                    <span className="text-xs text-slate-500 w-8 text-right">{p.distinct_words}</span>
                    <span className="text-xs text-slate-400 hidden sm:inline truncate max-w-[180px]">{p.examples.slice(0,3).join(', ')}</span>
                  </div>
                ))}
              </div>
              {g.noun_classes?.noun_class_pairs?.length > 0 && (
                <div className="mt-4 border-t border-slate-700 pt-3">
                  <p className="text-xs text-slate-500 mb-2">Likely singular/plural prefix pairs:</p>
                  <div className="flex flex-wrap gap-2">
                    {g.noun_classes.noun_class_pairs.map((pair: {singular_prefix: string; plural_prefix: string}, i: number) => (
                      <span key={i} className="text-xs bg-slate-700 px-2 py-1 rounded font-mono">
                        {pair.singular_prefix}- / {pair.plural_prefix}-
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Pronouns */}
            {Object.keys(g.pronouns || {}).length > 0 && (
              <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
                <h3 className="text-sm font-semibold mb-3">Subject Markers / Pronouns</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {Object.entries(g.pronouns).map(([key, val]: [string, unknown]) => {
                    const v = val as {english: string; candidates: {form: string; count: number}[]}
                    return (
                      <div key={key} className="bg-slate-700/50 rounded-lg p-2">
                        <p className="text-xs text-slate-400">{v.english} <span className="text-slate-600">({key})</span></p>
                        <p className="text-sm text-brand-300 font-mono">{v.candidates?.[0]?.form ?? '?'}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Verb morphology */}
            {Object.keys(g.verb_morphology || {}).length > 0 && (
              <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
                <h3 className="text-sm font-semibold mb-3">Verb Tense Markers</h3>
                {Object.entries(g.verb_morphology).map(([tense, data]: [string, unknown]) => {
                  const d = data as {likely_prefixes: {marker: string; score: number}[]; likely_suffixes: {marker: string; score: number}[]; examples: {english: string; translation: string}[]}
                  return (
                    <div key={tense} className="mb-4 last:mb-0">
                      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{tense}</p>
                      <div className="flex flex-wrap gap-1 mb-2">
                        {d.likely_prefixes?.slice(0,3).map((p, i) => (
                          <span key={i} className="text-xs bg-brand-900/50 text-brand-300 px-2 py-0.5 rounded font-mono">{p.marker}-</span>
                        ))}
                        {d.likely_suffixes?.slice(0,3).map((s, i) => (
                          <span key={i} className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono">-{s.marker}</span>
                        ))}
                      </div>
                      {d.examples?.slice(0,2).map((ex, i) => (
                        <div key={i} className="text-xs ml-2 mb-1">
                          <span className="text-slate-400">{ex.english}</span>
                          <span className="text-slate-600 mx-1">→</span>
                          <span className="text-brand-300">{ex.translation}</span>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </div>
            )}

            {/* Negation */}
            {g.negation?.likely_markers?.length > 0 && (
              <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
                <h3 className="text-sm font-semibold mb-3">Negation</h3>
                <div className="flex flex-wrap gap-2 mb-3">
                  {g.negation.likely_markers.slice(0, 5).map((m: {marker: string; ratio: number}, i: number) => (
                    <span key={i} className="text-sm bg-red-900/30 text-red-300 px-2 py-1 rounded font-mono">{m.marker}</span>
                  ))}
                </div>
                {g.negation.examples?.slice(0,3).map((ex: {english: string; translation: string}, i: number) => (
                  <div key={i} className="text-xs mb-1">
                    <span className="text-slate-400">{ex.english}</span>
                    <span className="text-slate-600 mx-1">→</span>
                    <span className="text-brand-300">{ex.translation}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Numbers */}
            {g.numbers?.length > 0 && (
              <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-4">
                <h3 className="text-sm font-semibold mb-3">Number System</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {g.numbers.map((n: {value: string; english: string; candidates: {word: string; count: number}[]}, i: number) => (
                    <div key={i} className="bg-slate-700/50 rounded-lg p-2">
                      <p className="text-xs text-slate-400">{n.english} ({n.value})</p>
                      <p className="text-sm text-brand-300 font-mono">{n.candidates?.[0]?.word ?? '?'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Cognates */}
        {sharedRoots?.cognates && (
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
            <h3 className="text-sm font-semibold mb-3">Shared Vocabulary (Cognates)</h3>
            <p className="text-xs text-slate-500 mb-3">Words appearing in 3+ Zambian languages.</p>
            <div className="space-y-1 max-h-72 overflow-y-auto">
              {sharedRoots.cognates.filter(v => v.languages.includes(viewLang)).slice(0, 60).map((v, i) => (
                <div key={i} className="flex items-center justify-between py-0.5">
                  <span className="text-sm text-white">{v.word}</span>
                  <div className="flex gap-0.5">
                    {v.languages.map(l => (
                      <span key={l} className={`text-[9px] px-1 py-0.5 rounded ${l === viewLang ? 'bg-brand-900 text-brand-300' : 'bg-slate-700 text-slate-500'}`}>
                        {l.slice(0,3)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // === CORPUS SOURCES LIST ===
  if (view.type === 'source' && view.source === 'corpus') {
    // Group by source type
    const sourceTypes = [...new Set(corpusGroups.map(g => g.source))]

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <h2 className="text-lg font-bold mb-4">Monolingual Corpus</h2>
        {sourceTypes.map(src => {
          const groups = corpusGroups.filter(g => g.source === src)
          const srcLabels: Record<string, string> = {
            moe: 'MoE Teaching Modules',
            usaid: 'USAID Let\'s Read',
            zambezivoice: 'ZambeziVoice Transcripts',
            'jw.org': 'JW.org Cinyanja',
            'other-pdf': 'Other PDFs (Peace Corps, UNZA)',
            bible: 'Bible (monolingual)',
            storybook: 'Storybooks (monolingual)',
          }
          return (
            <div key={src} className="mb-5">
              <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">{srcLabels[src] ?? src}</h3>
              <div className="space-y-1.5">
                {groups.map((g, i) => {
                  const langInfo = LANGUAGES.find(l => l.id === g.language)
                  return (
                    <button
                      key={i}
                      onClick={() => setView({ type: 'corpus-detail', source: g.source, language: g.language })}
                      className="w-full bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-brand-600 transition-colors text-left flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-slate-500" />
                        <span className="text-sm text-white">{langInfo?.endonym ?? g.language}</span>
                        <span className="text-xs text-slate-500">{g.files.length} files</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-300 font-mono">{g.total_lines.toLocaleString()}</span>
                        <span className="text-slate-400">→</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // === CORPUS DETAIL ===
  if (view.type === 'corpus-detail') {
    const group = corpusGroups.find(g => g.source === view.source && g.language === view.language)
    if (!group) return <div className="p-4 text-slate-400">Not found</div>
    const langInfo = LANGUAGES.find(l => l.id === group.language)

    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Breadcrumb />
        <h2 className="text-lg font-bold mb-1">{langInfo?.endonym} — {group.source}</h2>
        <p className="text-xs text-slate-400 mb-4">{group.total_lines.toLocaleString()} lines across {group.files.length} files</p>

        <div className="space-y-4">
          {group.files.map((file, fi) => (
            <div key={fi} className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-700 flex justify-between items-center">
                <p className="text-sm text-white font-medium truncate">{file.name}</p>
                <span className="text-xs text-slate-500 flex-shrink-0 ml-2">{file.line_count} lines</span>
              </div>
              <div className="p-4 space-y-1 max-h-80 overflow-y-auto">
                {file.sample.map((line, li) => (
                  <p key={li} className="text-sm text-slate-300 leading-relaxed">{line}</p>
                ))}
                {file.line_count > file.sample.length && (
                  <p className="text-xs text-slate-500 pt-2">... and {file.line_count - file.sample.length} more lines</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return null
}
