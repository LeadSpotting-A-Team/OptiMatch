import { useEffect } from 'react'

export default function ComparisonModal({ queryFaceBase64, matchFaceId, matchScore, matchMetadata, onClose }) {
  const scorePct = Math.round(matchScore * 100)
  const matchFaceUrl = `/faces/${matchFaceId}.jpg`
  const isHighScore = scorePct > 85

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 ls-modal-overlay"
      onClick={onClose}
    >
      <div
        className="ls-modal-panel rounded-xl max-w-4xl w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b ls-divider">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-gray-700 tracking-wide">
              Side-by-Side Comparison
            </h2>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full
              ${isHighScore
                ? 'bg-blue-100 text-blue-700 border border-blue-200'
                : 'bg-gray-100 text-gray-500 border border-gray-200'}`}>
              {scorePct}% Match
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 p-4 sm:p-6">
          {/* Query */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gray-300" />
              <h3 className="text-xs font-semibold text-gray-400 tracking-widest uppercase">
                Query Face
              </h3>
            </div>
            <div className="aspect-square bg-blue-50 rounded-lg overflow-hidden flex items-center justify-center border border-blue-100 relative">
              {queryFaceBase64 ? (
                <img
                  src={`data:image/jpeg;base64,${queryFaceBase64}`}
                  alt="Query"
                  className="w-full h-full object-contain"
                />
              ) : (
                <span className="text-gray-300 text-xs">N/A</span>
              )}
              <div className="reticle-all opacity-30" />
              <span className="reticle-bottom-left opacity-30" />
              <span className="reticle-bottom-right opacity-30" />
            </div>
          </div>

          {/* Match */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isHighScore ? 'bg-blue-500' : 'bg-gray-300'}`} />
              <h3 className={`text-xs font-semibold tracking-widest uppercase
                ${isHighScore ? 'text-blue-500' : 'text-gray-400'}`}>
                Match — {scorePct}%
              </h3>
            </div>
            <div className={`aspect-square bg-blue-50 rounded-lg overflow-hidden flex items-center justify-center relative
              ${isHighScore ? 'border border-blue-300 ls-glow' : 'border border-blue-100'}`}>
              <img
                src={matchFaceUrl}
                alt="Match"
                className="w-full h-full object-contain"
              />
              <div className="reticle-all" style={{ opacity: isHighScore ? 0.6 : 0.2 }} />
              <span className="reticle-bottom-left" style={{ opacity: isHighScore ? 0.6 : 0.2 }} />
              <span className="reticle-bottom-right" style={{ opacity: isHighScore ? 0.6 : 0.2 }} />
              {isHighScore && <div className="reticle-scan" />}
            </div>
            <div className="space-y-1">
              {matchMetadata?.link_to_post && (
                <a
                  href={matchMetadata.link_to_post}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700 text-xs block transition-colors font-medium"
                >
                  Open Source →
                </a>
              )}
              {matchMetadata?.platform && (
                <p className="text-gray-400 text-xs uppercase tracking-widest">{matchMetadata.platform}</p>
              )}
              {matchMetadata?.timestamp && (
                <p className="text-gray-400 text-xs">{matchMetadata.timestamp}</p>
              )}
              {matchMetadata?.face_id && (
                <p className="text-gray-300 text-[10px] truncate font-mono" title={matchMetadata.face_id}>
                  ID: {matchMetadata.face_id}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
