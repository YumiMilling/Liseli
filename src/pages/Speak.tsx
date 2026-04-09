import { useState, useRef, useEffect, useCallback } from 'react'

const ISO_LANGUAGES = [
  { code: 'bem', name: 'Bemba', endonym: 'Icibemba' },
  { code: 'nya', name: 'Nyanja', endonym: 'Chinyanja' },
  { code: 'toi', name: 'Tonga', endonym: 'Chitonga' },
  { code: 'loz', name: 'Lozi', endonym: 'Silozi' },
  { code: 'kqn', name: 'Kaonde', endonym: 'Kikaonde' },
  { code: 'lun', name: 'Lunda', endonym: 'Chilunda' },
  { code: 'lue', name: 'Luvale', endonym: 'Luvale' },
]

// Web Speech API types
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

type Phase = 'ready' | 'recording' | 'processing' | 'guess' | 'done'

export function Speak() {
  const [language, setLanguage] = useState('bem')
  const [phase, setPhase] = useState<Phase>('ready')
  const [aiGuess, setAiGuess] = useState('')
  const [aiConfidence, setAiConfidence] = useState(0)
  const [correctText, setCorrectText] = useState('')
  const [englishMeaning, setEnglishMeaning] = useState('')
  const [sessionCount, setSessionCount] = useState(0)
  const [interimText, setInterimText] = useState('')
  const [error, setError] = useState('')
  const [supported, setSupported] = useState(true)

  const recognitionRef = useRef<unknown>(null)
  const audioRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const langInfo = ISO_LANGUAGES.find(l => l.code === language)

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition
    if (!SpeechRecognition) {
      setSupported(false)
    }
  }, [])

  const startListening = useCallback(async () => {
    setError('')
    setAiGuess('')
    setInterimText('')

    const SpeechRecognition = (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition

    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser. Try Chrome on Android.')
      return
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition = new (SpeechRecognition as any)()
    recognition.continuous = false
    recognition.interimResults = true
    // Force English recognition — it will try to interpret Zambian languages as English
    // which produces the funny wrong guesses
    recognition.lang = 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let final = ''
      let conf = 0

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
          conf = result[0].confidence
        } else {
          interim += result[0].transcript
        }
      }

      if (interim) {
        setInterimText(interim)
      }

      if (final) {
        setAiGuess(final)
        setAiConfidence(conf)
        setPhase('guess')
      }
    }

    recognition.onerror = (event: { error: string }) => {
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow it in browser settings.')
      } else if (event.error === 'no-speech') {
        setError("Didn't hear anything. Try again?")
        setPhase('ready')
      } else {
        setError(`Error: ${event.error}`)
        setPhase('ready')
      }
    }

    recognition.onend = () => {
      if (phase === 'recording' && !aiGuess) {
        setPhase('processing')
        // Give it a moment then show result or error
        setTimeout(() => {
          if (!aiGuess) {
            setPhase('ready')
          }
        }, 2000)
      }
    }

    // Also record audio for storage
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }
      recorder.onstop = () => stream.getTracks().forEach(t => t.stop())
      recorder.start()
      audioRecorderRef.current = recorder
    } catch {
      // Audio recording optional — speech recognition can work without it
    }

    recognition.start()
    recognitionRef.current = recognition
    setPhase('recording')
  }, [phase, aiGuess])

  const stopListening = () => {
    if (recognitionRef.current) {
      (recognitionRef.current as { stop: () => void }).stop()
    }
    if (audioRecorderRef.current && audioRecorderRef.current.state === 'recording') {
      audioRecorderRef.current.stop()
    }
    if (!aiGuess) {
      setPhase('processing')
    }
  }

  const handleSubmit = () => {
    if (!correctText.trim()) return

    // TODO: Save to Supabase
    // - Audio blob from audioChunksRef → Supabase Storage → re_recordings
    // - Correct text → transcriptions
    // - English meaning → clip_translations or translation_pairs
    // - AI guess → for ASR error pattern learning
    console.log('Teaching AI:', {
      language,
      aiGuess,
      aiConfidence,
      correctText: correctText.trim(),
      englishMeaning: englishMeaning.trim(),
      hasAudio: audioChunksRef.current.length > 0,
    })

    setSessionCount(c => c + 1)
    setPhase('done')
  }

  const handleNext = () => {
    setAiGuess('')
    setAiConfidence(0)
    setCorrectText('')
    setEnglishMeaning('')
    setInterimText('')
    setError('')
    setPhase('ready')
  }

  if (!supported) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] px-6">
        <div className="text-center">
          <p className="text-xl mb-2">Speech recognition not available</p>
          <p className="text-slate-400 text-sm">Open this page in Chrome on your phone or desktop for the full experience.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-lg font-bold">Teach the AI</h2>
            <p className="text-xs text-slate-400">Speak your language. Watch it fail. Correct it.</p>
          </div>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            {ISO_LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.endonym}</option>
            ))}
          </select>
        </div>
        {sessionCount > 0 && (
          <p className="text-xs text-brand-400">{sessionCount} corrections — the AI is getting smarter</p>
        )}
      </div>

      {/* Main area */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">

          {/* READY */}
          {phase === 'ready' && (
            <div className="text-center">
              <p className="text-slate-400 mb-8">
                Say something in {langInfo?.endonym}.<br />
                <span className="text-slate-500 text-sm">The AI will try to understand — it won't.</span>
              </p>
              <button
                onClick={startListening}
                className="w-28 h-28 rounded-full bg-brand-600 hover:bg-brand-700 flex items-center justify-center mx-auto transition-all active:scale-90 shadow-lg shadow-brand-600/30"
              >
                <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              </button>
              <p className="text-xs text-slate-600 mt-4">Tap the mic and speak</p>
              {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
            </div>
          )}

          {/* RECORDING */}
          {phase === 'recording' && (
            <div className="text-center">
              <p className="text-white mb-6">Listening to you...</p>
              <button
                onClick={stopListening}
                className="w-28 h-28 rounded-full bg-red-600 flex items-center justify-center mx-auto shadow-lg shadow-red-600/40"
              >
                <div className="w-12 h-12 rounded-full border-4 border-white animate-ping opacity-30 absolute" />
                <svg className="w-10 h-10 text-white relative" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              </button>
              {interimText && (
                <p className="text-slate-400 text-sm mt-4 italic">hearing: "{interimText}"</p>
              )}
              <p className="text-xs text-slate-600 mt-2">Tap to stop</p>
            </div>
          )}

          {/* PROCESSING */}
          {phase === 'processing' && (
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-slate-800 border-2 border-brand-500 flex items-center justify-center mx-auto mb-4">
                <div className="w-4 h-4 bg-brand-400 rounded-full animate-bounce" />
              </div>
              <p className="text-slate-400">AI is thinking...</p>
            </div>
          )}

          {/* GUESS — the fun part */}
          {phase === 'guess' && (
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
              {/* AI's wrong interpretation */}
              <div className="px-6 py-6 text-center bg-slate-900/50">
                <p className="text-xs text-slate-500 mb-2">AI heard you say:</p>
                <p className="text-2xl text-amber-400 font-medium leading-relaxed mb-1">
                  "{aiGuess}"
                </p>
                <p className="text-[10px] text-slate-600">
                  {aiConfidence > 0 ? `${Math.round(aiConfidence * 100)}% confident (and wrong)` : 'not confident at all'}
                </p>
              </div>

              <div className="h-px bg-slate-700" />

              {/* Correction form */}
              <div className="px-6 py-5">
                <p className="text-sm text-slate-400 mb-3">
                  What did you actually say?
                </p>
                <textarea
                  value={correctText}
                  onChange={e => setCorrectText(e.target.value)}
                  placeholder={`Correct ${langInfo?.endonym} text...`}
                  className="w-full bg-slate-900 border border-slate-600 rounded-xl p-3 text-white text-lg placeholder-slate-500 focus:border-brand-500 focus:outline-none resize-none mb-3"
                  rows={2}
                  autoFocus
                />

                <p className="text-sm text-slate-400 mb-2">What does it mean in English?</p>
                <input
                  type="text"
                  value={englishMeaning}
                  onChange={e => setEnglishMeaning(e.target.value)}
                  placeholder="English meaning (optional)..."
                  className="w-full bg-slate-900 border border-slate-600 rounded-xl p-3 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none mb-4"
                  onKeyDown={e => { if (e.key === 'Enter') handleSubmit() }}
                />

                <div className="flex gap-3">
                  <button
                    onClick={handleNext}
                    className="flex-1 py-3 rounded-xl bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
                  >
                    Try again
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={!correctText.trim()}
                    className="flex-1 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-30 font-semibold transition-all active:scale-95"
                  >
                    Teach it
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* DONE */}
          {phase === 'done' && (
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-bold mb-3">The AI just got smarter!</h3>
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-6 text-left">
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-red-400 text-xs mt-0.5">AI:</span>
                  <p className="text-red-400/60 line-through text-sm">"{aiGuess}"</p>
                </div>
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-brand-400 text-xs mt-0.5">{langInfo?.code}:</span>
                  <p className="text-brand-300 text-sm">{correctText}</p>
                </div>
                {englishMeaning && (
                  <div className="flex items-start gap-2">
                    <span className="text-slate-500 text-xs mt-0.5">EN:</span>
                    <p className="text-white text-sm">{englishMeaning}</p>
                  </div>
                )}
              </div>
              <button
                onClick={handleNext}
                className="w-full bg-brand-600 hover:bg-brand-700 py-3 rounded-xl font-semibold transition-all active:scale-95"
              >
                Say something else
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
