import { useState, useCallback, useEffect, useMemo } from 'react'
import QueryFaceUpload from './components/QueryFaceUpload'
import MatchGallery from './components/MatchGallery'
import ScoreSlider from './components/ScoreSlider'
import ComparisonModal from './components/ComparisonModal'
import './cyber.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  // Each input mode keeps its own cropped-face result so switching tabs never bleeds state
  const [fileQueryFace, setFileQueryFace] = useState(null)
  const [urlQueryFace, setUrlQueryFace]   = useState(null)
  // Always holds the query face from the most recent completed search (used by the comparison modal)
  const [lastQueryFace, setLastQueryFace] = useState(null)
  const [results, setResults]             = useState([])
  const [hasSearched, setHasSearched]     = useState(false)
  const [minScore, setMinScore]           = useState(50)
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState(null)
  const [modalState, setModalState]       = useState(null)
  const [backendReady, setBackendReady]   = useState(false)

  // Poll /health until backend is up
  useEffect(() => {
    let interval
    const check = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`)
        if (res.ok) {
          setBackendReady(true)
          clearInterval(interval)
        }
      } catch {
        // still loading
      }
    }
    check()
    interval = setInterval(check, 2000)
    return () => clearInterval(interval)
  }, [])

  // onFaceResult: (face: string | null) => void  — mode-specific setter passed by the caller
  const runSearch = useCallback(async (fetchFn, onFaceResult) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchFn()
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Search failed')
      }
      const data = await res.json()
      const face  = data.query_faces?.[0] ?? null
      onFaceResult(face)
      setLastQueryFace(face)
      setResults(data.results || [])
      setHasSearched(true)
    } catch (e) {
      setError(e.message)
      onFaceResult(null)
      setResults([])
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSearchFile = useCallback((file) => {
    runSearch(
      () => {
        const formData = new FormData()
        formData.append('file', file)
        return fetch(`${API_BASE}/search`, { method: 'POST', body: formData })
      },
      (face) => setFileQueryFace(face),
    )
  }, [runSearch])

  const handleSearchUrl = useCallback((url) => {
    runSearch(
      () => {
        const formData = new FormData()
        formData.append('url', url)
        return fetch(`${API_BASE}/search/url`, { method: 'POST', body: formData })
      },
      (face) => setUrlQueryFace(face),
    )
  }, [runSearch])

  // Called when the user selects a new file — clears only the file-mode result
  const handleFileChange = useCallback(() => {
    setFileQueryFace(null)
    setResults([])
    setHasSearched(false)
    setError(null)
  }, [])

  // Called when the user edits the URL input — clears only the url-mode result
  const handleUrlChange = useCallback(() => {
    setUrlQueryFace(null)
    setResults([])
    setHasSearched(false)
    setError(null)
  }, [])

  const openComparison = (result) => {
    setModalState({
      queryFaceBase64: lastQueryFace,
      matchFaceId: result.face_id,
      matchScore: result.score,
      matchMetadata: result,
    })
  }

  const filteredResults = results.filter((r) => r.score * 100 >= minScore)

  const identityRanking = useMemo(() => {
    if (!filteredResults.length) return []
    const sumByUsername = {}
    const countByUsername = {}
    for (const r of filteredResults) {
      if (!r.username) continue
      sumByUsername[r.username] = (sumByUsername[r.username] || 0) + r.score
      countByUsername[r.username] = (countByUsername[r.username] || 0) + 1
    }
    return Object.keys(sumByUsername)
      .map((username) => ({
        username,
        pct: Math.round((sumByUsername[username] / countByUsername[username]) * 100),
      }))
      .sort((a, b) => b.pct - a.pct)
  }, [filteredResults])

  return (
    <div className="min-h-screen text-slate-100" style={{ backgroundColor: '#050505' }}>
      {/* Header */}
      <header className="relative border-b border-cyan-900/60 px-4 py-4 md:px-6 md:py-5 flex flex-col items-center gap-1 overflow-hidden cyber-scanlines"
        style={{ background: 'linear-gradient(180deg, #060d14 0%, #050505 100%)' }}>
        {/* Subtle top accent line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-70" />
        <div className="flex items-center gap-3 relative z-10">
          <h1 className="text-2xl md:text-4xl font-extrabold tracking-widest font-mono">
            <span className="text-slate-100">OPTI</span><span className="text-cyan-400">MATCH</span>
          </h1>
        </div>
        <span className="text-[10px] md:text-xs text-cyan-800 tracking-widest uppercase font-mono relative z-10 text-center">
          ◈ Face Search Engine — Visual Intelligence Platform ◈
        </span>

      </header>

      <main className="flex flex-col md:flex-row gap-6 p-4 md:p-6 items-start">
        <aside className="w-full md:w-[480px] md:shrink-0 md:sticky md:top-6">
          {!backendReady && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-800/60 bg-amber-950/40 px-4 py-2 text-amber-400 text-xs font-mono tracking-wide">
              <span className="animate-spin inline-block w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full shrink-0" />
              SYSTEM INITIALIZING... PLEASE WAIT
            </div>
          )}
          <QueryFaceUpload
            onSearchFile={handleSearchFile}
            onSearchUrl={handleSearchUrl}
            onFileChange={handleFileChange}
            onUrlChange={handleUrlChange}
            loading={loading}
            error={error}
            fileQueryFace={fileQueryFace}
            urlQueryFace={urlQueryFace}
            backendReady={backendReady}
          />
        </aside>

        <section className="flex-1 min-w-0">
          <div className="mb-4 flex items-center gap-4 flex-wrap">
            <ScoreSlider value={minScore} onChange={setMinScore} />
            {hasSearched && identityRanking.length > 0 && (
              <div className="flex items-center gap-3 border border-cyan-900/60 bg-slate-900/70 rounded-lg px-4 py-2 backdrop-blur-sm max-h-10 overflow-hidden hover:max-h-60 transition-all duration-300">
                <span className="text-[10px] text-cyan-700 font-mono tracking-widest uppercase shrink-0">Identities</span>
                <div className="flex flex-col gap-0.5 overflow-y-auto max-h-56">
                  {identityRanking.map((item, i) => (
                    <div key={item.username} className="flex items-center gap-3 justify-between min-w-[180px]">
                      <span className={`font-mono text-xs tracking-wide ${i === 0 ? 'text-cyan-300 font-bold' : 'text-slate-400'}`}>
                        @{item.username}
                      </span>
                      <span className={`font-mono text-xs tabular-nums ${i === 0 ? 'text-cyan-400' : 'text-slate-500'}`}>
                        {item.pct}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <MatchGallery
            results={filteredResults}
            onCardClick={openComparison}
            hasSearched={hasSearched}
          />
        </section>
      </main>

      {modalState && (
        <ComparisonModal
          queryFaceBase64={modalState.queryFaceBase64}
          matchFaceId={modalState.matchFaceId}
          matchScore={modalState.matchScore}
          matchMetadata={modalState.matchMetadata}
          onClose={() => setModalState(null)}
        />
      )}
    </div>
  )
}
