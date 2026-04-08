import { Link } from 'react-router-dom'
import { useLanguageCoverage, useStats } from '@/hooks/useLeaderboard'
import { LanguageCoverageGrid } from '@/components/LanguageCoverage'

export function Landing() {
  const { coverage, loading } = useLanguageCoverage()
  const stats = useStats()

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-bold mb-3 leading-tight">
          Our languages deserve
          <br />
          <span className="text-brand-400">a digital future.</span>
        </h1>
        <p className="text-slate-400 text-lg max-w-md mx-auto mb-4">
          Technology that doesn't speak your language excludes you.
          Liseli is building the open dataset to change that — for all 7 Zambian languages.
        </p>
        <p className="text-slate-500 text-sm max-w-sm mx-auto">
          When a mother can describe symptoms in Lozi, a farmer can get advice in Bemba,
          and a child can learn to read in Kaonde — that's what this data makes possible.
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-slate-800 rounded-xl p-3 border border-slate-700 text-center">
            <div className="text-xl font-bold text-brand-400">{(stats.total_corpus || 0).toLocaleString()}</div>
            <div className="text-xs text-slate-400">Corpus lines</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-3 border border-slate-700 text-center">
            <div className="text-xl font-bold text-brand-400">{stats.total_translations.toLocaleString()}</div>
            <div className="text-xs text-slate-400">Parallel pairs</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-3 border border-slate-700 text-center">
            <div className="text-xl font-bold text-brand-400">7</div>
            <div className="text-xs text-slate-400">Languages</div>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-3 mb-10">
        <Link
          to="/browse"
          className="bg-brand-600 hover:bg-brand-700 rounded-xl p-4 text-center transition-colors"
        >
          <div className="text-2xl mb-1">{'\u{1F4CA}'}</div>
          <div className="text-sm font-medium">Browse</div>
        </Link>
        <Link
          to="/translate"
          className="bg-slate-800 hover:bg-slate-700 rounded-xl p-4 text-center border border-slate-700 transition-colors"
        >
          <div className="text-2xl mb-1">+</div>
          <div className="text-sm font-medium">Translate</div>
        </Link>
        <Link
          to="/validate"
          className="bg-slate-800 hover:bg-slate-700 rounded-xl p-4 text-center border border-slate-700 transition-colors"
        >
          <div className="text-2xl mb-1">&#10003;</div>
          <div className="text-sm font-medium">Validate</div>
        </Link>
      </div>

      {/* Language coverage */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Language Coverage</h2>
        <LanguageCoverageGrid coverage={coverage} loading={loading} />
      </div>

      {/* Why it matters */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4">Why This Matters</h2>
        <div className="space-y-4">
          <Step
            n={1}
            title="Digital exclusion is real"
            desc="Technology that only works in English excludes millions of Zambians. A farmer can't get crop advice. A patient can't describe symptoms. A child can't learn to read."
          />
          <Step
            n={2}
            title="Languages without data disappear"
            desc="If our languages don't exist digitally, they lose relevance. Making them part of technology is an act of preservation."
          />
          <Step
            n={3}
            title="Only we can do this"
            desc="No tech company will build this — the market is too small. Only Zambian speakers have the knowledge to get the translations right."
          />
          <Step
            n={4}
            title="The data is open, forever"
            desc="Everything built here is CC BY-SA — owned by the community, free for anyone to use. Nobody locks up what the crowd built."
          />
        </div>
      </div>

      {/* How to contribute */}
      <div className="mt-8 bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4">How to Contribute</h2>
        <div className="space-y-4">
          <Step
            n={1}
            title="Translate"
            desc="See an English word or sentence. Translate it into your language — you're the expert."
          />
          <Step
            n={2}
            title="Validate"
            desc="Review others' translations. Vote: correct, almost, or wrong. Three correct votes = verified."
          />
          <Step
            n={3}
            title="Discuss"
            desc="When opinions differ, a discussion opens. Dialect differences are documented, not erased."
          />
        </div>
      </div>

      {/* Three tiers */}
      <div className="mt-8 bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4">Three Tiers of Content</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <span className="bg-brand-900 text-brand-300 text-xs font-bold px-2 py-1 rounded">T1</span>
            <div>
              <p className="font-medium">Words</p>
              <p className="text-sm text-slate-400">Single vocabulary items. "maize", "school", "fever"</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="bg-brand-900 text-brand-300 text-xs font-bold px-2 py-1 rounded">T2</span>
            <div>
              <p className="font-medium">Phrases</p>
              <p className="text-sm text-slate-400">"bag of maize", "the school is closed"</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="bg-brand-900 text-brand-300 text-xs font-bold px-2 py-1 rounded">T3</span>
            <div>
              <p className="font-medium">Sentences</p>
              <p className="text-sm text-slate-400">"How much is a bag of maize at the market?"</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center mt-10 mb-4">
        <Link
          to="/browse"
          className="inline-block bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold text-lg transition-colors"
        >
          Explore the Data
        </Link>
        <p className="text-slate-500 text-sm mt-3">
          Open data. Open source. Owned by Zambia.
        </p>
        <div className="mt-4 inline-flex items-center gap-3 text-xs text-slate-500">
          <span className="font-mono bg-slate-800 px-2 py-1 rounded border border-slate-700">CC BY-SA</span>
          <span className="font-mono bg-slate-800 px-2 py-1 rounded border border-slate-700">AGPL-3.0</span>
        </div>
        <div className="mt-6 text-xs text-slate-600">
          Powered by <span className="text-slate-400 font-semibold">ZAMAI</span>
          <span className="mx-2">·</span>
          <a href="mailto:hello@zamai.pro" className="text-slate-500 hover:text-slate-300 transition-colors">hello@zamai.pro</a>
        </div>
      </div>
    </div>
  )
}

function Step({ n, title, desc }: { n: number; title: string; desc: string }) {
  return (
    <div className="flex gap-3">
      <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-900 text-brand-400 flex items-center justify-center text-sm font-bold">
        {n}
      </span>
      <div>
        <p className="font-medium">{title}</p>
        <p className="text-sm text-slate-400">{desc}</p>
      </div>
    </div>
  )
}
