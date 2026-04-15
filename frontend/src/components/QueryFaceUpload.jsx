import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function QueryFaceUpload({
  searchMode = 'library',
  onSearchFile,
  onSearchUrl,
  onFileChange,
  onUrlChange,
  loading,
  error,
  fileQueryFace,
  urlQueryFace,
  backendReady,
}) {
  const [mode, setMode] = useState('file')
  const [urlInput, setUrlInput] = useState('')
  const [pendingFile, setPendingFile] = useState(null)
  const [pendingPreview, setPendingPreview] = useState(null)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')

  const isLeadspotting = searchMode === 'leadspotting'

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    setPendingFile(file)
    setPendingPreview(URL.createObjectURL(file))
    onFileChange?.()
  }, [onFileChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    maxFiles: 1,
    disabled: loading,
  })

  const handleSearch = () => {
    if (mode === 'file' && pendingFile) {
      isLeadspotting
        ? onSearchFile(pendingFile, firstName.trim(), lastName.trim())
        : onSearchFile(pendingFile)
    } else if (mode === 'url' && urlInput.trim()) {
      isLeadspotting
        ? onSearchUrl(urlInput.trim(), firstName.trim(), lastName.trim())
        : onSearchUrl(urlInput.trim())
    }
  }

  const namesFilled = !isLeadspotting || (firstName.trim().length > 0 && lastName.trim().length > 0)
  const canSearch = (mode === 'file' ? !!pendingFile : urlInput.trim().length > 0) && namesFilled

  const filePreview = pendingPreview
    || (fileQueryFace ? `data:image/jpeg;base64,${fileQueryFace}` : null)

  const urlPreview = urlInput.trim()
    || (urlQueryFace ? `data:image/jpeg;base64,${urlQueryFace}` : null)

  const displayPreview = mode === 'file' ? filePreview : urlPreview

  return (
    <div className="space-y-4">
      <div className="ls-card rounded-xl overflow-hidden">
        {/* Mode tabs */}
        <div className="flex border-b ls-border">
          <button
            onClick={() => setMode('file')}
            className={`flex-1 py-3 text-xs font-semibold tracking-wide uppercase transition-all
              ${mode === 'file'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'}`}
          >
            Upload Image
          </button>
          <button
            onClick={() => setMode('url')}
            className={`flex-1 py-3 text-xs font-semibold tracking-wide uppercase transition-all
              ${mode === 'url'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'}`}
          >
            From URL
          </button>
        </div>

        {/* Input area */}
        <div className="p-4">
          {mode === 'file' ? (
            <div
              {...getRootProps()}
              className={`
                relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed
                cursor-pointer transition-all min-h-[240px] p-6
                ${isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-blue-200 hover:border-blue-400 hover:bg-blue-50/50'}
                ${loading ? 'pointer-events-none opacity-60' : ''}
              `}
            >
              <input {...getInputProps()} />

              {/* Corner brackets */}
              <div className="reticle-all opacity-40" />
              <span className="reticle-bottom-left opacity-40" />
              <span className="reticle-bottom-right opacity-40" />
              {isDragActive && <div className="reticle-scan" />}

              {displayPreview ? (
                <img
                  src={displayPreview}
                  alt="Query face"
                  className="max-h-52 max-w-full rounded object-contain z-10 relative"
                />
              ) : (
                <div className="text-center space-y-3 z-10 relative">
                  <div className="w-14 h-14 mx-auto rounded-full bg-blue-50 border-2 border-blue-200 flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4-4 4 4 4-6 4 6M4 20h16M12 4v8"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-gray-500 text-sm font-medium mb-1">
                      {isDragActive ? 'Drop image here' : 'Drag & drop or click to upload'}
                    </p>
                    <p className="text-gray-400 text-xs">JPG · PNG · WEBP</p>
                  </div>
                </div>
              )}
            </div>

          ) : (
            <div className="space-y-3">
              <div className="relative rounded-lg border-2 border-dashed border-blue-200 overflow-hidden min-h-[240px] flex flex-col">
                <div className="reticle-all opacity-40 pointer-events-none" />
                <span className="reticle-bottom-left opacity-40 pointer-events-none" />
                <span className="reticle-bottom-right opacity-40 pointer-events-none" />

                {displayPreview ? (
                  <div className="flex-1 flex items-center justify-center p-4">
                    <img
                      src={displayPreview}
                      alt="Query face preview"
                      className="max-h-48 max-w-full rounded object-contain z-10"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                    <div className="flex-1 items-center justify-center text-gray-300 p-8 text-center hidden">
                      <div className="space-y-2">
                        <div className="text-2xl">✕</div>
                        <p className="text-xs text-gray-400">Cannot preview URL directly<br/>Click Search to try anyway</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-gray-300 p-8 text-center">
                    <div className="space-y-3">
                      <svg className="w-8 h-8 text-blue-200 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                      </svg>
                      <p className="text-xs text-gray-400">Paste an image URL below</p>
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
                className="w-full rounded-lg border border-blue-200 bg-white px-4 py-3 text-sm
                  text-gray-700 placeholder-gray-400
                  focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-200 disabled:opacity-50"
              />
            </div>
          )}

          {/* Leadspotting name fields */}
          {isLeadspotting && (
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="John"
                  disabled={loading}
                  className="w-full rounded-lg border border-blue-200 bg-white px-3 py-2.5 text-sm
                    text-gray-700 placeholder-gray-400
                    focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-200 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                  disabled={loading}
                  className="w-full rounded-lg border border-blue-200 bg-white px-3 py-2.5 text-sm
                    text-gray-700 placeholder-gray-400
                    focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-200 disabled:opacity-50"
                />
              </div>
            </div>
          )}
        </div>

        {/* Search button */}
        <div className="px-4 pb-4">
          <button
            onClick={handleSearch}
            disabled={!canSearch || loading || !backendReady}
            className="w-full py-3 rounded-lg font-semibold text-sm tracking-wide transition-all
              disabled:opacity-40 disabled:cursor-not-allowed
              flex items-center justify-center gap-2
              bg-blue-600 hover:bg-blue-700 text-white
              disabled:bg-gray-200 disabled:text-gray-400 shadow-sm"
          >
            {loading ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Searching...
              </>
            ) : !backendReady ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full" />
                System Initializing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
                </svg>
                Search Faces
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-600 text-sm">
          ✕ {error}
        </div>
      )}
    </div>
  )
}
