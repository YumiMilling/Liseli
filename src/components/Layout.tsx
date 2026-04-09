import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useState, useEffect } from 'react'

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: HomeIcon },
  { path: '/browse', label: 'Browse', icon: BrowseIcon },
  { path: '/translate', label: 'Translate', icon: TranslateIcon },
  { path: '/listen', label: 'Listen', icon: ListenIcon },
  { path: '/cross', label: 'Cross', icon: CrossIcon },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { contributor } = useAuth()
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('liseli-theme') !== 'light'
    }
    return true
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    document.documentElement.classList.toggle('light', !dark)
    localStorage.setItem('liseli-theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <div className={`min-h-screen flex flex-col ${dark ? 'bg-slate-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Top bar */}
      <header className={`border-b px-4 py-3 flex items-center justify-between ${dark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'}`}>
        <Link to="/" className="flex items-center gap-2">
          <span className="text-brand-400 font-bold text-xl">Liseli</span>
          <span className={`text-xs hidden sm:inline ${dark ? 'text-slate-500' : 'text-gray-400'}`}>Zambia's Open Language Project</span>
        </Link>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setDark(!dark)}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${dark ? 'bg-slate-700 hover:bg-slate-600 text-slate-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'}`}
            title={dark ? 'Switch to light theme' : 'Switch to dark theme'}
          >
            {dark ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
          {contributor ? (
            <Link
              to="/profile"
              className={`flex items-center gap-2 text-sm ${dark ? 'text-slate-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
            >
              <span className="bg-brand-600 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white">
                {contributor.handle[0].toUpperCase()}
              </span>
              <span className="hidden sm:inline">{contributor.handle}</span>
              <span className="text-brand-400 font-medium">{contributor.points} pts</span>
            </Link>
          ) : (
            <Link
              to="/profile"
              className="text-sm bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              Join
            </Link>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto pb-20">{children}</main>

      {/* Bottom navigation */}
      <nav className={`fixed bottom-0 left-0 right-0 border-t px-2 py-1 flex justify-around safe-bottom ${dark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'}`}>
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
          const active = location.pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                active
                  ? 'text-brand-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{label}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

// Inline SVG icons to avoid external dependencies
function HomeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1" />
    </svg>
  )
}

function TranslateIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
    </svg>
  )
}

function ValidateIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function DiscussIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  )
}

function ListenIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728M12 18.75a.75.75 0 01-.75-.75v-4.5a.75.75 0 011.5 0V18a.75.75 0 01-.75.75zM12 8.25a2.25 2.25 0 100-4.5 2.25 2.25 0 000 4.5z" />
    </svg>
  )
}

function CrossIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
    </svg>
  )
}

function BrowseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7zm0 5h16M9 4v16" />
    </svg>
  )
}

function LeaderboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}
