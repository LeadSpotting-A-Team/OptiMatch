import { useState, useCallback, useEffect } from 'react'
import QueryFaceUpload from './components/QueryFaceUpload'
import MatchGallery from './components/MatchGallery'
import ScoreSlider from './components/ScoreSlider'
import ComparisonModal from './components/ComparisonModal'
import './cyber.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [queryFaces, setQueryFaces] = useState([])
  const [results, setResults] = useState([])
  const [hasSearched, setHasSearched] = useState(false)
  const [minScore, setMinScore] = useState(50)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [modalState, setModalState] = useState(null)
  const [backendReady, setBackendReady] = useState(false)

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

  const runSearch = useCallback(async (fetchFn) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchFn()
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Search failed')
      }
      const data = await res.json()
      setQueryFaces(data.query_faces || [])
      setResults(data.results || [])
      setHasSearched(true)
    } catch (e) {
      setError(e.message)
      setQueryFaces([])
      setResults([])
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSearchFile = useCallback((file) => {
    runSearch(() => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE}/search`, { method: 'POST', body: formData })
    })
  }, [runSearch])

  const handleSearchUrl = useCallback((url) => {
    runSearch(() => {
      const formData = new FormData()
      formData.append('url', url)
      return fetch(`${API_BASE}/search/url`, { method: 'POST', body: formData })
    })
  }, [runSearch])

  const openComparison = (result) => {
    setModalState({
      queryFaceBase64: queryFaces[0] || null,
      matchFaceId: result.face_id,
      matchScore: result.score,
      matchMetadata: result,
    })
  }

  const filteredResults = results.filter((r) => r.score * 100 >= minScore)

  return (
    <div className="min-h-screen text-slate-100" style={{ backgroundColor: '#050505' }}>
      {/* Header */}
      <header className="relative border-b border-cyan-900/60 px-6 py-5 flex flex-col items-center gap-1 overflow-hidden cyber-scanlines"
        style={{ background: 'linear-gradient(180deg, #060d14 0%, #050505 100%)' }}>
        {/* Subtle top accent line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-70" />
        <div className="flex items-center gap-3 relative z-10">
          <span className="text-3xl">🔎</span>
          <h1 className="text-4xl font-extrabold tracking-widest font-mono">
            <span className="text-slate-100">OPTI</span><span className="text-cyan-400">MATCH</span>
          </h1>
        </div>
        <span className="text-xs text-cyan-800 tracking-widest uppercase font-mono relative z-10">
          ◈ Face Search Engine — Visual Intelligence Platform ◈
        </span>
      </header>

      <main className="flex gap-6 p-6 items-start">
        <aside className="w-[480px] shrink-0 sticky top-6">
          {!backendReady && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-800/60 bg-amber-950/40 px-4 py-2 text-amber-400 text-xs font-mono tracking-wide">
              <span className="animate-spin inline-block w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full shrink-0" />
              SYSTEM INITIALIZING... PLEASE WAIT
            </div>
          )}
          <QueryFaceUpload
            onSearchFile={handleSearchFile}
            onSearchUrl={handleSearchUrl}
            loading={loading}
            error={error}
            previewBase64={queryFaces[0]}
            backendReady={backendReady}
          />
        </aside>

        <section className="flex-1 min-w-0">
          <div className="mb-4 flex items-center gap-4">
            <ScoreSlider value={minScore} onChange={setMinScore} />
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
