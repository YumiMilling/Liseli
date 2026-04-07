import { useState } from 'react'
import type { Verdict } from '@/types'

interface Props {
  onVote: (verdict: Verdict) => void
  voteCounts?: { correct: number; almost: number; wrong: number }
}

const VERDICTS: { id: Verdict; label: string; color: string; icon: string }[] = [
  { id: 'correct', label: 'Correct', color: 'bg-emerald-600 hover:bg-emerald-700', icon: '✓' },
  { id: 'almost', label: 'Almost', color: 'bg-amber-600 hover:bg-amber-700', icon: '~' },
  { id: 'wrong', label: 'Wrong', color: 'bg-red-600 hover:bg-red-700', icon: '✗' },
]

export function VoteButtons({ onVote, voteCounts }: Props) {
  const [voted, setVoted] = useState<Verdict | null>(null)

  const handleVote = (verdict: Verdict) => {
    if (voted) return
    setVoted(verdict)
    onVote(verdict)
  }

  return (
    <div className="flex gap-2">
      {VERDICTS.map(({ id, label, color, icon }) => (
        <button
          key={id}
          onClick={() => handleVote(id)}
          disabled={voted !== null}
          className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
            voted === id
              ? `${color} ring-2 ring-white/30`
              : voted
                ? 'bg-slate-700 opacity-40 cursor-not-allowed'
                : `${color}`
          }`}
        >
          <span className="mr-1">{icon}</span>
          {label}
          {voteCounts && (
            <span className="ml-1 opacity-60">({voteCounts[id]})</span>
          )}
        </button>
      ))}
    </div>
  )
}
