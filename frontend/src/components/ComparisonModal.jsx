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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 cyber-modal-overlay"
      onClick={onClose}
    >
      <div
        className="cyber-modal-panel rounded-xl max-w-4xl w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b cyber-divider">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-mono font-bold tracking-widest uppercase text-cyan-400">
              ◈ Side-by-Side Analysis
            </h2>
            <span className={`font-mono text-xs px-2 py-0.5 rounded border
              ${isHighScore
                ? 'text-cyan-400 border-cyan-500/60 bg-cyan-500/10'
                : 'text-slate-400 border-slate-700 bg-slate-800'}`}>
              {scorePct}% MATCH
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-cyan-900 hover:text-cyan-400 font-mono text-lg transition-colors leading-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="grid grid-cols-2 gap-6 p-6">
          {/* Query */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-500" />
              <h3 className="text-[11px] font-mono font-semibold text-slate-500 tracking-widest uppercase">
                Query Face
              </h3>
            </div>
            <div className="aspect-square bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center border border-slate-800 relative">
              {queryFaceBase64 ? (
                <img
                  src={`data:image/jpeg;base64,${queryFaceBase64}`}
                  alt="Query"
                  className="w-full h-full object-contain"
                />
              ) : (
                <span className="text-slate-700 font-mono text-xs">N/A</span>
              )}
              {/* Corner reticle */}
              <div className="reticle-all opacity-40" />
              <span className="reticle-bottom-left opacity-40" />
              <span className="reticle-bottom-right opacity-40" />
            </div>
          </div>

          {/* Match */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${isHighScore ? 'bg-cyan-400' : 'bg-slate-500'}`} />
              <h3 className={`text-[11px] font-mono font-semibold tracking-widest uppercase
                ${isHighScore ? 'text-cyan-600' : 'text-slate-500'}`}>
                Match — {scorePct}%
              </h3>
            </div>
            <div className={`aspect-square bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center relative
              ${isHighScore ? 'border border-cyan-900 cyber-glow' : 'border border-slate-800'}`}>
              <img
                src={matchFaceUrl}
                alt="Match"
                className="w-full h-full object-contain"
              />
              {/* Corner reticle */}
              <div className="reticle-all" style={{ opacity: isHighScore ? 0.7 : 0.3 }} />
              <span className="reticle-bottom-left" style={{ opacity: isHighScore ? 0.7 : 0.3 }} />
              <span className="reticle-bottom-right" style={{ opacity: isHighScore ? 0.7 : 0.3 }} />
              {isHighScore && <div className="reticle-scan" />}
            </div>
            <div className="space-y-1 font-mono">
              {matchMetadata?.link_to_post && (
                <a
                  href={matchMetadata.link_to_post}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-600 hover:text-cyan-400 text-xs block transition-colors tracking-wide"
                >
                  OPEN SOURCE →
                </a>
              )}
              {matchMetadata?.platform && (
                <p className="text-slate-600 text-xs uppercase tracking-widest">{matchMetadata.platform}</p>
              )}
              {matchMetadata?.timestamp && (
                <p className="text-slate-700 text-xs">{matchMetadata.timestamp}</p>
              )}
              {matchMetadata?.face_id && (
                <p className="text-slate-800 text-[10px] truncate" title={matchMetadata.face_id}>
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
