import type { LeaderboardEntry } from '@/types'

interface Props {
  entries: LeaderboardEntry[]
  loading: boolean
}

export function LeaderboardTable({ entries, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="bg-slate-800 rounded-lg h-14 animate-pulse" />
        ))}
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="text-center text-slate-400 py-12">
        No contributors yet. Be the first!
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      {entries.map((entry) => (
        <div
          key={entry.contributor.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
            entry.rank <= 3 ? 'bg-slate-800 border border-brand-800' : 'bg-slate-800/60'
          }`}
        >
          {/* Rank */}
          <span
            className={`w-8 text-center font-bold ${
              entry.rank === 1
                ? 'text-yellow-400 text-lg'
                : entry.rank === 2
                  ? 'text-slate-300 text-lg'
                  : entry.rank === 3
                    ? 'text-amber-600 text-lg'
                    : 'text-slate-500'
            }`}
          >
            {entry.rank}
          </span>

          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center text-sm font-bold">
            {entry.contributor.handle[0].toUpperCase()}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{entry.contributor.handle}</div>
            <div className="text-xs text-slate-400">
              {entry.contributor.province} · Trust {entry.contributor.trust_score}
            </div>
          </div>

          {/* Points */}
          <div className="text-brand-400 font-bold">{entry.points.toLocaleString()}</div>
        </div>
      ))}
    </div>
  )
}
