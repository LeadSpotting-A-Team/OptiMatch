import { useState, useCallback, useEffect, useMemo } from 'react'
import QueryFaceUpload from './components/QueryFaceUpload'
import CsvLearnUpload from './components/CsvLearnUpload'
import MatchGallery from './components/MatchGallery'
import ScoreSlider from './components/ScoreSlider'
import ComparisonModal from './components/ComparisonModal'
import './cyber.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [fileQueryFace, setFileQueryFace] = useState(null)
  const [urlQueryFace, setUrlQueryFace]   = useState(null)
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

  const handleFileChange = useCallback(() => {
    setFileQueryFace(null)
    setResults([])
    setHasSearched(false)
    setError(null)
  }, [])

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
    <div className="min-h-screen ls-bg-page text-gray-800">
      {/* Header */}
      <header className="ls-header px-4 py-3 md:px-8 md:py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/leadspotting-logo.png" alt="Leadspotting" className="h-10 w-auto" />
          <div className="hidden sm:flex flex-col border-l border-blue-100 pl-3">
            <span className="text-sm font-bold text-blue-800 leading-tight">LeadSpotting</span>
            <span className="text-[11px] text-blue-400 tracking-wide">Face Search Engine</span>
          </div>
        </div>

        {!backendReady && (
          <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 text-amber-600 text-xs font-medium">
            <span className="animate-spin inline-block w-3 h-3 border-2 border-amber-500 border-t-transparent rounded-full" />
            System initializing...
          </div>
        )}
      </header>

      <main className="flex flex-col md:flex-row gap-6 p-4 md:p-6 items-start max-w-screen-2xl mx-auto">
        {/* Sidebar */}
        <aside className="w-full md:w-[460px] md:shrink-0 md:sticky md:top-6 space-y-4">
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
          <CsvLearnUpload backendReady={backendReady} />
        </aside>

        {/* Results */}
        <section className="flex-1 min-w-0">
          <div className="mb-4 flex items-center gap-4 flex-wrap">
            <ScoreSlider value={minScore} onChange={setMinScore} />
            {hasSearched && identityRanking.length > 0 && (
              <div className="flex items-center gap-3 ls-card rounded-lg px-4 py-2 max-h-10 overflow-hidden hover:max-h-60 transition-all duration-300 cursor-default">
                <span className="text-[11px] text-blue-500 font-semibold tracking-wide uppercase shrink-0">
                  Identities
                </span>
                <div className="flex flex-col gap-0.5 overflow-y-auto max-h-56">
                  {identityRanking.map((item, i) => (
                    <div key={item.username} className="flex items-center gap-3 justify-between min-w-[180px]">
                      <span className={`text-xs tracking-wide ${i === 0 ? 'text-blue-700 font-bold' : 'text-gray-500'}`}>
                        @{item.username}
                      </span>
                      <span className={`text-xs tabular-nums ${i === 0 ? 'text-blue-600 font-semibold' : 'text-gray-400'}`}>
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
