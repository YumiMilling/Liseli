import { TIERS } from '@/lib/constants'
import type { Tier } from '@/types'

interface Props {
  selected: Tier | undefined
  onChange: (tier: Tier | undefined) => void
}

export function TierFilter({ selected, onChange }: Props) {
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onChange(undefined)}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          !selected ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
        }`}
      >
        All
      </button>
      {TIERS.map((tier) => (
        <button
          key={tier.id}
          onClick={() => onChange(tier.id)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            selected === tier.id
              ? 'bg-brand-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          {tier.label}
        </button>
      ))}
    </div>
  )
}
