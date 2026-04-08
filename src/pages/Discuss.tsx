import { useState } from 'react'
import type { ZamLanguage } from '@/types'
import { LanguageSelector } from '@/components/LanguageSelector'

export function Discuss() {
  const [_language, setLanguage] = useState<ZamLanguage | undefined>()

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Discussions</h2>
        <LanguageSelector selected={_language} onChange={setLanguage} />
      </div>

      <div className="text-center text-slate-400 py-12">
        No open discussions yet. Discussions open when translations receive split votes.
      </div>
    </div>
  )
}
