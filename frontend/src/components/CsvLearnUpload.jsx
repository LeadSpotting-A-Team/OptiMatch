import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function CsvLearnUpload({ backendReady }) {
  const [pendingFile, setPendingFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    setPendingFile(file)
    setResult(null)
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/vnd.ms-excel': ['.csv'], 'text/plain': ['.csv'] },
    maxFiles: 1,
    disabled: loading,
  })

  const handleLearn = async () => {
    if (!pendingFile) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append('file', pendingFile)
      const res = await fetch(`${API_BASE}/learn/csv`, { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Upload failed')
      }
      const data = await res.json()
      setResult(data)
      setPendingFile(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ls-card rounded-xl overflow-hidden">
      {/* Panel header */}
      <div className="px-4 py-3 border-b ls-border flex items-center gap-2">
        <h2 className="text-sm font-semibold text-gray-700 tracking-wide">Upload Dataset (CSV)</h2>
      </div>

      <div className="p-4 space-y-3">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            flex flex-col items-center justify-center rounded-lg border-2 border-dashed
            cursor-pointer transition-all min-h-[120px] p-4 text-center
            ${isDragActive
              ? 'border-ls-blue bg-blue-50'
              : 'border-blue-200 hover:border-ls-blue hover:bg-blue-50/50'}
            ${loading ? 'pointer-events-none opacity-50' : ''}
          `}
        >
          <input {...getInputProps()} />
          {pendingFile ? (
            <div className="space-y-1">
              <div className="text-2xl">📄</div>
              <p className="text-sm font-medium text-gray-700">{pendingFile.name}</p>
              <p className="text-xs text-gray-400">
                {(pendingFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-2xl text-blue-300">📂</div>
              <p className="text-sm text-gray-500">
                {isDragActive ? 'Drop the CSV here...' : 'Drag & drop a CSV file, or click to browse'}
              </p>
              <p className="text-xs text-gray-400">.csv files only</p>
            </div>
          )}
        </div>

        {/* Upload button */}
        <button
          onClick={handleLearn}
          disabled={!pendingFile || loading || !backendReady}
          className="w-full py-2.5 rounded-lg text-sm font-semibold tracking-wide transition-all
            disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2
            bg-ls-green text-white hover:brightness-105 active:brightness-95
            disabled:bg-gray-200 disabled:text-gray-400"
        >
          {loading ? (
            <>
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Processing...
            </>
          ) : !backendReady ? (
            <>
              <span className="animate-spin inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full" />
              System Initializing...
            </>
          ) : (
            <>
              Upload &amp; Learn
            </>
          )}
        </button>

        {/* Success */}
        {result && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700 space-y-0.5">
            <p className="font-semibold">✓ Dataset learned successfully</p>
            <p className="text-xs text-green-600">
              {result.learned_posts} post{result.learned_posts !== 1 ? 's' : ''} processed
              &nbsp;·&nbsp;
              {result.total_faces} total faces in index
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            ✕ {error}
          </div>
        )}
      </div>
    </div>
  )
}
