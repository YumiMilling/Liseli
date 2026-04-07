import { useLeaderboard } from '@/hooks/useLeaderboard'
import { LeaderboardTable } from '@/components/LeaderboardTable'

export function Leaderboard() {
  const { entries, loading } = useLeaderboard()

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h2 className="text-xl font-bold mb-6">Leaderboard</h2>
      <LeaderboardTable entries={entries} loading={loading} />
    </div>
  )
}
