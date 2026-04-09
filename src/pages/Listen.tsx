import { useState, useEffect } from 'react'

interface Segment {
  id: string
  external_url: string
  start_time_ms: number
  end_time_ms: number
  duration_ms: number
  channel_name: string
  language_code: string
  domain: string
  auto_transcript?: string
}

// ISO 639-3 codes used in YouTube segments
const ISO_LANGUAGES = [
  { code: 'bem', name: 'Bemba', endonym: 'Icibemba' },
  { code: 'nya', name: 'Nyanja', endonym: 'Chinyanja' },
  { code: 'toi', name: 'Tonga', endonym: 'Chitonga' },
  { code: 'loz', name: 'Lozi', endonym: 'Silozi' },
  { code: 'kqn', name: 'Kaonde', endonym: 'Kikaonde' },
  { code: 'lun', name: 'Lunda', endonym: 'Chilunda' },
  { code: 'lue', name: 'Luvale', endonym: 'Luvale' },
]

export function Listen() {
  const [segments, setSegments] = useState<Segment[]>([])
  const [language, setLanguage] = useState('bem')
  const [index, setIndex] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [phase, setPhase] = useState<'listen' | 'submitted'>('listen')
  const [sessionCount, setSessionCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    // Try engine-fixed Whisper segments first, fallback to raw YouTube segments
    fetch('/data/whisper-segments.json')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then((data: Segment[]) => {
        const filtered = data.filter(s => s.language_code === language)
        if (filtered.length > 0) {
          setSegments(filtered)
        } else {
          // Fallback to YouTube segments for this language
          return fetch('/data/youtube-segments.json').then(r => r.json()).then((yt: Segment[]) => {
            setSegments(yt.filter(s => s.language_code === language))
          })
        }
      })
      .catch(() => {
        fetch('/data/youtube-segments.json')
          .then(r => r.json())
          .then((data: Segment[]) => setSegments(data.filter(s => s.language_code === language)))
          .catch(() => {})
      })
      .finally(() => {
        setIndex(0)
        setPhase('listen')
        setLoading(false)
      })
  }, [language])

  const segment = segments[index]
  const langInfo = ISO_LANGUAGES.find(l => l.code === language)

  const [hdMode, setHdMode] = useState(false)

  const getEmbedUrl = (seg: Segment) => {
    const vidMatch = seg.external_url.match(/v=([^&]+)/)
    if (!vidMatch) return ''
    const vidId = vidMatch[1]
    const start = Math.floor(seg.start_time_ms / 1000)
    const end = Math.ceil(seg.end_time_ms / 1000)
    // vq=small forces 240p to save data
    const quality = hdMode ? '' : '&vq=small'
    return `https://www.youtube.com/embed/${vidId}?start=${start}&end=${end}&autoplay=0&rel=0&modestbranding=1${quality}`
  }

  const handleSubmit = () => {
    if (!transcript.trim()) return
    // TODO: submit to Supabase transcriptions table
    console.log('Transcription submitted:', { segment: segment?.id, text: transcript, language })
    setPhase('submitted')
    setSessionCount(c => c + 1)
  }

  // Pre-fill transcript from auto-generated text when segment changes
  useEffect(() => {
    if (segment?.auto_transcript) {
      setTranscript(segment.auto_transcript)
    } else {
      setTranscript('')
    }
  }, [segment])

  const handleNext = () => {
    if (index + 1 < segments.length) {
      setIndex(i => i + 1)
      setPhase('listen')
    }
  }

  const handleSkip = () => {
    if (index + 1 < segments.length) {
      setIndex(i => i + 1)
      setPhase('listen')
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Top bar */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-bold">Listen & Transcribe</h2>
            <p className="text-xs text-slate-400">Hear a clip, type what you hear</p>
          </div>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value as ZamLanguage)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            {ISO_LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.endonym}</option>
            ))}
          </select>
        </div>

        {/* Progress */}
        {segments.length > 0 && (
          <>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all duration-500"
                style={{ width: `${((index + 1) / segments.length) * 100}%` }}
              />
            </div>
            <div className="flex justify-between mt-1.5">
              <span className="text-xs text-slate-500">{index + 1} of {segments.length}</span>
              {sessionCount > 0 && (
                <span className="text-xs text-brand-400">{sessionCount} transcribed</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Main area */}
      <div className="flex-1 flex items-center justify-center px-4">
        {loading ? (
          <div className="w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl h-80 animate-pulse" />
          </div>
        ) : !segment ? (
          <div className="text-center text-slate-400">
            <p className="mb-2">No clips available for {langInfo?.endonym}.</p>
            <p className="text-xs text-slate-500">Try another language or check back later.</p>
          </div>
        ) : (
          <div className="w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
              {/* YouTube embed */}
              <div className="aspect-video bg-black">
                <iframe
                  key={`${segment.external_url}-${segment.start_time_ms}`}
                  src={getEmbedUrl(segment)}
                  className="w-full h-full"
                  allow="autoplay; encrypted-media"
                  allowFullScreen
                  title="Listen to this clip"
                />
              </div>

              {/* Clip info */}
              <div className="px-5 py-3 border-b border-slate-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-brand-900/60 text-brand-300 px-2 py-0.5 rounded capitalize">{segment.domain}</span>
                    <span className="text-xs text-slate-500">{Math.round(segment.duration_ms / 1000)}s</span>
                    <span className="text-xs text-slate-500 truncate max-w-[150px]">{segment.channel_name?.slice(0, 40)}</span>
                  </div>
                  <button
                    onClick={() => setHdMode(!hdMode)}
                    className={`text-[10px] px-2 py-0.5 rounded transition-colors ${
                      hdMode ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-400'
                    }`}
                  >
                    {hdMode ? 'HD' : '240p'}
                  </button>
                </div>
              </div>

              {/* Transcription area */}
              <div className="px-5 py-5">
                {phase === 'listen' ? (
                  <>
                    <p className="text-sm text-slate-400 mb-3">
                      {segment.auto_transcript
                        ? `YouTube tried to transcribe this but got it wrong. Replace with what you actually hear in ${langInfo?.endonym ?? 'the language'}.`
                        : `What did you hear in ${langInfo?.endonym ?? 'the language'}? Type it below.`
                      }
                    </p>

                    <textarea
                      value={transcript}
                      onChange={e => setTranscript(e.target.value)}
                      placeholder={`Type what you heard in ${langInfo?.endonym ?? 'the language'}...`}
                      className="w-full bg-slate-900 border border-slate-600 rounded-xl p-4 text-white text-lg placeholder-slate-500 focus:border-brand-500 focus:outline-none resize-none"
                      rows={2}
                      autoFocus
                      onKeyDown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSubmit()
                        }
                      }}
                    />
                    <div className="flex items-center justify-between mt-3">
                      <button
                        onClick={handleSkip}
                        className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
                      >
                        Skip
                      </button>
                      <button
                        onClick={handleSubmit}
                        disabled={!transcript.trim()}
                        className="bg-brand-600 hover:bg-brand-700 disabled:opacity-30 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95"
                      >
                        Submit
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="text-center">
                    <div className="inline-flex items-center gap-2 text-brand-400 mb-3">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-semibold">Transcription saved</span>
                    </div>
                    <p className="text-brand-300 text-sm mb-6">{transcript}</p>
                    <button
                      onClick={handleNext}
                      className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-xl font-semibold transition-all active:scale-95 w-full"
                    >
                      Next Clip
                    </button>
                  </div>
                )}
              </div>
            </div>

            <p className="text-center text-[10px] text-slate-600 mt-2">
              Press Enter to submit
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
