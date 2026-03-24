import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function QueryFaceUpload({ onSearchFile, onSearchUrl, onUrlChange, loading, error, previewBase64, backendReady }) {
  const [mode, setMode] = useState('file')
  const [urlInput, setUrlInput] = useState('')
  const [pendingFile, setPendingFile] = useState(null)
  const [pendingPreview, setPendingPreview] = useState(null)

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    setPendingFile(file)
    setPendingPreview(URL.createObjectURL(file))
    // Clear previous search state so the new local preview takes priority
    // over any base64 face that was returned from a prior search request
    onUrlChange?.()
  }, [onUrlChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    maxFiles: 1,
    disabled: loading,
  })

  const handleSearch = () => {
    if (mode === 'file' && pendingFile) {
      onSearchFile(pendingFile)
    } else if (mode === 'url' && urlInput.trim()) {
      onSearchUrl(urlInput.trim())
    }
  }

  const canSearch = mode === 'file' ? !!pendingFile : urlInput.trim().length > 0

  const displayPreview = mode === 'url' && urlInput.trim()
    ? urlInput.trim()
    : previewBase64
      ? `data:image/jpeg;base64,${previewBase64}`
      : pendingPreview

  return (
    <div className="space-y-4">
      {/* Panel wrapper */}
      <div className="rounded-xl border border-cyan-900/50 overflow-hidden"
        style={{ background: 'linear-gradient(160deg, #060d14 0%, #050505 100%)' }}>

        {/* Mode tabs */}
        <div className="flex border-b border-cyan-900/40">
          <button
            onClick={() => setMode('file')}
            className={`flex-1 py-3 text-xs font-mono font-bold tracking-widest uppercase transition-all
              ${mode === 'file'
                ? 'bg-cyan-500/10 text-cyan-400 border-b-2 border-cyan-500'
                : 'text-slate-600 hover:text-slate-400'}`}
          >
            ▲ Upload File
          </button>
          <button
            onClick={() => setMode('url')}
            className={`flex-1 py-3 text-xs font-mono font-bold tracking-widest uppercase transition-all
              ${mode === 'url'
                ? 'bg-cyan-500/10 text-cyan-400 border-b-2 border-cyan-500'
                : 'text-slate-600 hover:text-slate-400'}`}
          >
            ◈ From URL
          </button>
        </div>

        {/* Input area */}
        <div className="p-4">
          {mode === 'file' ? (
            <div
              {...getRootProps()}
              className={`
                relative flex flex-col items-center justify-center rounded-lg border cursor-pointer
                transition-all min-h-[260px] p-6
                ${isDragActive
                  ? 'border-cyan-500 bg-cyan-500/5'
                  : 'border-cyan-900/50 hover:border-cyan-700/60 hover:bg-cyan-950/20'}
                ${loading ? 'pointer-events-none opacity-60' : ''}
              `}
            >
              <input {...getInputProps()} />

              {/* Camera reticle corners */}
              <div className="reticle-all" />
              <span className="reticle-bottom-left" />
              <span className="reticle-bottom-right" />
              {isDragActive && <div className="reticle-scan" />}

              {displayPreview ? (
                <img
                  src={displayPreview}
                  alt="Query face"
                  className="max-h-56 max-w-full rounded object-contain z-10 relative"
                />
              ) : (
                <div className="text-center space-y-4 z-10 relative">
                  <div className="w-16 h-16 mx-auto border-2 border-cyan-900/60 rounded-full flex items-center justify-center">
                    <span className="text-2xl text-cyan-900">◉</span>
                  </div>
                  <div>
                    <p className="text-cyan-800 text-xs font-mono tracking-widest uppercase mb-1">
                      {isDragActive ? 'Release to acquire target' : 'Drag & drop or click to select'}
                    </p>
                    <p className="text-slate-800 text-[10px] font-mono">JPG · PNG · WEBP</p>
                  </div>
                </div>
              )}
            </div>

          ) : (
            <div className="space-y-3">
              <div className="relative rounded-lg border border-cyan-900/50 overflow-hidden min-h-[260px] flex flex-col">
                {/* Reticle corners on URL preview */}
                <div className="reticle-all pointer-events-none" />
                <span className="reticle-bottom-left pointer-events-none" />
                <span className="reticle-bottom-right pointer-events-none" />

                {displayPreview ? (
                  <div className="flex-1 flex items-center justify-center p-4">
                    <img
                      src={displayPreview}
                      alt="Query face preview"
                      className="max-h-52 max-w-full rounded object-contain z-10"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                    <div className="flex-1 items-center justify-center text-slate-700 p-8 text-center hidden">
                      <div className="space-y-2 font-mono">
                        <div className="text-2xl">✕</div>
                        <p className="text-xs tracking-wide">Cannot preview URL directly<br/>Click Search to try anyway</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-700 p-8 text-center">
                    <div className="space-y-3 font-mono">
                      <div className="text-3xl text-cyan-900/50">◈</div>
                      <p className="text-xs tracking-widest uppercase text-cyan-900">Paste target URL below</p>
                    </div>
                  </div>
                )}
              </div>

              <input
                type="url"
                value={urlInput}
                onChange={(e) => { setUrlInput(e.target.value); onUrlChange?.() }}
                onKeyDown={(e) => e.key === 'Enter' && canSearch && !loading && handleSearch()}
                placeholder="https://example.com/photo.jpg"
                disabled={loading}
                className="w-full rounded-lg border border-cyan-900/50 bg-slate-950 px-4 py-3 text-sm
                  text-slate-300 placeholder-slate-700 font-mono
                  focus:outline-none focus:border-cyan-700 disabled:opacity-50"
              />
            </div>
          )}
        </div>

        {/* Search button */}
        <div className="px-4 pb-4">
          <button
            onClick={handleSearch}
            disabled={!canSearch || loading || !backendReady}
            className="w-full py-3 rounded-lg font-mono font-bold text-sm tracking-widest uppercase transition-all
              disabled:opacity-30 disabled:cursor-not-allowed
              flex items-center justify-center gap-3"
            style={{
              background: (!canSearch || loading || !backendReady)
                ? undefined
                : 'linear-gradient(90deg, #0891b2, #06b6d4)',
              backgroundColor: (!canSearch || loading || !backendReady) ? '#0a1520' : undefined,
              color: (!canSearch || loading || !backendReady) ? '#164e63' : '#050505',
              border: '1px solid',
              borderColor: (!canSearch || loading || !backendReady) ? '#0e3a4a' : '#06b6d4',
              boxShadow: (!canSearch || loading || !backendReady) ? 'none' : '0 0 12px rgba(6,182,212,0.3)',
            }}
          >
            {loading ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                Scanning...
              </>
            ) : !backendReady ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                System Initializing...
              </>
            ) : (
              <>
                <span>◉</span>
                Acquire Target
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900/60 bg-red-950/30 px-4 py-3 text-red-500 text-xs font-mono tracking-wide">
          ✕ {error}
        </div>
      )}
    </div>
  )
}
