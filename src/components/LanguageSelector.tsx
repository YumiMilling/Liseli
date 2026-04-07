import { LANGUAGES } from '@/lib/constants'
import type { ZamLanguage } from '@/types'

interface Props {
  selected: ZamLanguage | undefined
  onChange: (language: ZamLanguage) => void
}

export function LanguageSelector({ selected, onChange }: Props) {
  return (
    <select
      value={selected ?? ''}
      onChange={(e) => onChange(e.target.value as ZamLanguage)}
      className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
    >
      <option value="" disabled>
        Select language
      </option>
      {LANGUAGES.map((lang) => (
        <option key={lang.id} value={lang.id}>
          {lang.name} ({lang.endonym})
        </option>
      ))}
    </select>
  )
}
