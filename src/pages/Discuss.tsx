import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import { supabase } from '@/lib/supabase'
import type { Discussion, ZamLanguage } from '@/types'
import { LanguageSelector } from '@/components/LanguageSelector'
import { Link } from 'react-router-dom'

export function Discuss() {
  const { contributor } = useAuth()
  const [language, setLanguage] = useState<ZamLanguage | undefined>(
    contributor?.languages[0]
  )
  const [discussions, setDiscussions] = useState<Discussion[]>([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')

  const fetchDiscussions = useCallback(async () => {
    setLoading(true)
    let query = supabase
      .from('discussions')
      .select(`
        *,
        translation:translations(
          *,
          sentence:sentences(*)
        ),
        comments:discussion_comments(
          *,
          contributor:contributors(handle)
        )
      `)
      .eq('status', 'open')
      .order('created_at', { ascending: false })
      .limit(20)

    if (language) {
      query = query.eq('translation.language', language)
    }

    const { data } = await query
    setDiscussions(data ?? [])
    setLoading(false)
  }, [language])

  useEffect(() => {
    fetchDiscussions()
  }, [fetchDiscussions])

  const submitComment = async (discussionId: string) => {
    if (!contributor || !commentText.trim()) return
    await supabase.from('discussion_comments').insert({
      discussion_id: discussionId,
      contributor_id: contributor.id,
      text: commentText.trim(),
    })
    setCommentText('')
    fetchDiscussions()
  }

  if (!contributor) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold mb-3">Join to Discuss</h2>
        <p className="text-slate-400 mb-6">
          Help resolve disputed translations by joining the conversation.
        </p>
        <Link
          to="/profile"
          className="inline-block bg-brand-600 hover:bg-brand-700 px-6 py-2.5 rounded-lg font-medium transition-colors"
        >
          Create Account
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Discussions</h2>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-32 animate-pulse" />
          ))}
        </div>
      ) : discussions.length === 0 ? (
        <div className="text-center text-slate-400 py-12">
          No open discussions. All translations are in agreement!
        </div>
      ) : (
        <div className="space-y-4">
          {discussions.map((disc) => (
            <div
              key={disc.id}
              className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden"
            >
              {/* Header */}
              <button
                onClick={() => setActiveId(activeId === disc.id ? null : disc.id)}
                className="w-full text-left p-5"
              >
                <p className="text-sm text-slate-400 mb-1">English</p>
                <p className="text-white font-medium">
                  {disc.translation?.sentence?.english}
                </p>
                <p className="text-sm text-slate-400 mt-2 mb-1">
                  Disputed <span className="capitalize">{disc.translation?.language}</span> translation
                </p>
                <p className="text-amber-400">{disc.translation?.text}</p>
                <p className="text-xs text-slate-500 mt-2">
                  {disc.comments?.length ?? 0} comments · tap to{' '}
                  {activeId === disc.id ? 'collapse' : 'expand'}
                </p>
              </button>

              {/* Comments */}
              {activeId === disc.id && (
                <div className="border-t border-slate-700 p-4 space-y-3">
                  {disc.comments?.map((comment) => (
                    <div key={comment.id} className="flex gap-2">
                      <div className="w-6 h-6 rounded-full bg-slate-600 flex items-center justify-center text-xs flex-shrink-0">
                        {(comment.contributor as unknown as { handle: string })?.handle?.[0]?.toUpperCase() ?? '?'}
                      </div>
                      <div>
                        <span className="text-sm text-slate-300 font-medium">
                          {(comment.contributor as unknown as { handle: string })?.handle}
                        </span>
                        <p className="text-sm text-slate-400">{comment.text}</p>
                      </div>
                    </div>
                  ))}

                  {/* Add comment */}
                  <div className="flex gap-2 mt-3">
                    <input
                      type="text"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Add your perspective..."
                      className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') submitComment(disc.id)
                      }}
                    />
                    <button
                      onClick={() => submitComment(disc.id)}
                      disabled={!commentText.trim()}
                      className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 px-3 py-2 rounded-lg text-sm transition-colors"
                    >
                      Send
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
