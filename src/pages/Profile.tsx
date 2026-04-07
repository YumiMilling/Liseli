import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { LANGUAGES, PROVINCES } from '@/lib/constants'
import type { ZamLanguage } from '@/types'

export function Profile() {
  const { contributor, user, signUp, signIn, signOut, loading } = useAuth()
  const [mode, setMode] = useState<'signin' | 'signup'>('signup')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [handle, setHandle] = useState('')
  const [province, setProvince] = useState('')
  const [languages, setLanguages] = useState<ZamLanguage[]>([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const toggleLanguage = (lang: ZamLanguage) => {
    setLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (mode === 'signup') {
        if (!handle.trim()) throw new Error('Handle is required')
        if (languages.length === 0) throw new Error('Select at least one language')
        if (!province) throw new Error('Select your province')
        await signUp(email, password, { handle: handle.trim(), languages, province })
      } else {
        await signIn(email, password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center text-slate-400">
        Loading...
      </div>
    )
  }

  // Logged in — show profile
  if (contributor && user) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <h2 className="text-xl font-bold mb-6">Your Profile</h2>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 space-y-4">
          {/* Avatar + handle */}
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-brand-700 flex items-center justify-center text-2xl font-bold">
              {contributor.handle[0].toUpperCase()}
            </div>
            <div>
              <p className="text-lg font-semibold">{contributor.handle}</p>
              <p className="text-sm text-slate-400">{contributor.province}</p>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Points" value={contributor.points.toLocaleString()} />
            <Stat label="Trust" value={contributor.trust_score.toString()} />
            <Stat label="Streak" value={`${contributor.streak_days}d`} />
          </div>

          {/* Languages */}
          <div>
            <p className="text-sm text-slate-400 mb-2">Your languages</p>
            <div className="flex flex-wrap gap-2">
              {contributor.languages.map((lang) => {
                const info = LANGUAGES.find((l) => l.id === lang)
                return (
                  <span
                    key={lang}
                    className="bg-brand-900 text-brand-300 px-2 py-1 rounded text-sm"
                  >
                    {info?.name ?? lang}
                  </span>
                )
              })}
            </div>
          </div>

          <button
            onClick={signOut}
            className="w-full mt-4 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-sm transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    )
  }

  // Auth form
  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-center mb-2">
        {mode === 'signup' ? 'Join Liseli' : 'Welcome Back'}
      </h2>
      <p className="text-slate-400 text-center mb-6">
        {mode === 'signup'
          ? 'Create an account to start contributing translations.'
          : 'Sign in to continue contributing.'}
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm text-slate-300 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-300 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-brand-500 focus:outline-none"
          />
        </div>

        {mode === 'signup' && (
          <>
            <div>
              <label className="block text-sm text-slate-300 mb-1">Handle</label>
              <input
                type="text"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                placeholder="Your display name"
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-1">Province</label>
              <select
                value={province}
                onChange={(e) => setProvince(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-brand-500 focus:outline-none"
              >
                <option value="">Select province</option>
                {PROVINCES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Languages you speak
              </label>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() => toggleLanguage(lang.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      languages.includes(lang.id)
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {lang.name}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 py-2.5 rounded-lg font-medium transition-colors"
        >
          {submitting
            ? 'Loading...'
            : mode === 'signup'
              ? 'Create Account'
              : 'Sign In'}
        </button>
      </form>

      <p className="text-center text-sm text-slate-400 mt-4">
        {mode === 'signup' ? (
          <>
            Already have an account?{' '}
            <button onClick={() => setMode('signin')} className="text-brand-400 hover:underline">
              Sign in
            </button>
          </>
        ) : (
          <>
            New here?{' '}
            <button onClick={() => setMode('signup')} className="text-brand-400 hover:underline">
              Create account
            </button>
          </>
        )}
      </p>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-900 rounded-lg p-3 text-center">
      <p className="text-lg font-bold text-brand-400">{value}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  )
}
