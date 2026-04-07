import { Link } from 'react-router-dom'
import { useLanguageCoverage } from '@/hooks/useLeaderboard'
import { LanguageCoverageGrid } from '@/components/LanguageCoverage'

export function Landing() {
  const { coverage, loading } = useLanguageCoverage()

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-bold mb-3 leading-tight">
          Only Zambians can build
          <br />
          <span className="text-brand-400">Zambia's AI.</span>
        </h1>
        <p className="text-slate-400 text-lg max-w-md mx-auto">
          Translate words, phrases, and sentences into Zambian languages.
          Together we build the dataset for AI that speaks our languages.
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-3 mb-10">
        <Link
          to="/translate"
          className="bg-brand-600 hover:bg-brand-700 rounded-xl p-4 text-center transition-colors"
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
        <Link
          to="/discuss"
          className="bg-slate-800 hover:bg-slate-700 rounded-xl p-4 text-center border border-slate-700 transition-colors"
        >
          <div className="text-2xl mb-1">&#8230;</div>
          <div className="text-sm font-medium">Discuss</div>
        </Link>
      </div>

      {/* Language coverage */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Language Coverage</h2>
        <LanguageCoverageGrid coverage={coverage} loading={loading} />
      </div>

      {/* How it works */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4">How It Works</h2>
        <div className="space-y-4">
          <Step
            n={1}
            title="Translate"
            desc="See an English word, phrase, or sentence. The AI takes a guess — you correct it, improve it, or replace it entirely."
          />
          <Step
            n={2}
            title="Validate"
            desc="Review others' translations. Vote: correct, almost, or wrong. Three correct votes = verified."
          />
          <Step
            n={3}
            title="Discuss"
            desc="When votes are split, a discussion opens. Debate dialect differences, agree on the best translation."
          />
          <Step
            n={4}
            title="Build AI"
            desc="Every verified translation becomes training data for AI models that speak Zambian languages."
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

      {/* Footer CTA */}
      <div className="text-center mt-10 mb-4">
        <Link
          to="/translate"
          className="inline-block bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold text-lg transition-colors"
        >
          Start Contributing
        </Link>
        <p className="text-slate-500 text-sm mt-3">No account required to browse. Sign up to contribute.</p>
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
