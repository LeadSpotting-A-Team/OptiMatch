import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function QueryFaceUpload({ onSearchFile, onSearchUrl, loading, error, previewBase64, backendReady }) {
  const [mode, setMode] = useState('file')
  const [urlInput, setUrlInput] = useState('')
  const [pendingFile, setPendingFile] = useState(null)
  const [pendingPreview, setPendingPreview] = useState(null)

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    setPendingFile(file)
    setPendingPreview(URL.createObjectURL(file))
  }, [])

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

  // For file mode: show base64 from API response, or local object URL
  // For URL mode: show base64 from API response, or the URL itself directly
  const displayPreview = previewBase64
    ? `data:image/jpeg;base64,${previewBase64}`
    : mode === 'url' && urlInput.trim()
      ? urlInput.trim()
      : pendingPreview

  return (
    <div className="space-y-5">
      {/* Mode tabs */}
      <div className="flex rounded-xl overflow-hidden border border-slate-700 text-base">
        <button
          onClick={() => setMode('file')}
          className={`flex-1 py-3 font-medium transition-colors ${
            mode === 'file'
              ? 'bg-sky-600 text-white'
              : 'bg-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setMode('url')}
          className={`flex-1 py-3 font-medium transition-colors ${
            mode === 'url'
              ? 'bg-sky-600 text-white'
              : 'bg-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          From URL
        </button>
      </div>

      {/* Input area */}
      {mode === 'file' ? (
        <div
          {...getRootProps()}
          className={`
            flex flex-col items-center justify-center rounded-xl border-2 border-dashed cursor-pointer
            transition-colors min-h-[280px] p-8
            ${isDragActive ? 'border-sky-500 bg-sky-500/10' : 'border-slate-600 hover:border-sky-500/60 hover:bg-slate-800/60'}
            ${loading ? 'pointer-events-none opacity-70' : ''}
          `}
        >
          <input {...getInputProps()} />
          {displayPreview ? (
            <img
              src={displayPreview}
              alt="Query face"
              className="max-h-64 max-w-full rounded-lg object-contain shadow-lg"
            />
          ) : (
            <div className="text-center space-y-3">
              <div className="text-5xl text-slate-500">📁</div>
              <p className="text-slate-300 text-lg font-medium">
                {isDragActive ? 'Drop the image here' : 'Drag & drop or click to select'}
              </p>
              <p className="text-slate-500 text-sm">JPG, PNG, WEBP</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="rounded-xl border-2 border-slate-600 overflow-hidden min-h-[280px] flex flex-col">
            {displayPreview ? (
              <div className="flex-1 flex items-center justify-center p-4">
                <img
                  src={displayPreview}
                  alt="Query face preview"
                  className="max-h-64 max-w-full rounded-lg object-contain shadow-lg"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
                <div className="flex-1 items-center justify-center text-slate-500 p-8 text-center hidden">
                  <div className="space-y-2">
                    <div className="text-4xl">🚫</div>
                    <p className="text-sm text-slate-500">Cannot preview this URL directly<br/>Click Search to try anyway</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-500 p-8 text-center">
                <div className="space-y-3">
                  <div className="text-5xl">🔗</div>
                  <p className="text-lg text-slate-400">Paste an image URL below and click Search</p>
                </div>
              </div>
            )}
          </div>
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && canSearch && !loading && handleSearch()}
            placeholder="https://example.com/photo.jpg"
            disabled={loading}
            className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-base text-slate-200 placeholder-slate-500
              focus:outline-none focus:border-sky-500 disabled:opacity-50"
          />
        </div>
      )}

      {/* Search button */}
      <button
        onClick={handleSearch}
        disabled={!canSearch || loading || !backendReady}
        className="w-full py-4 rounded-xl font-bold text-lg transition-all
          bg-sky-600 hover:bg-sky-500 active:scale-[0.98] text-white shadow-lg shadow-sky-900/40
          disabled:opacity-40 disabled:cursor-not-allowed
          flex items-center justify-center gap-3"
      >
        {loading ? (
          <>
            <span className="animate-spin inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
            Searching...
          </>
        ) : !backendReady ? (
          <>
            <span className="animate-spin inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
            Backend Loading...
          </>
        ) : (
          <>
            <span>🔍</span>
            Search
          </>
        )}
      </button>

      {error && (
        <div className="rounded-xl border border-red-800 bg-red-900/30 px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
