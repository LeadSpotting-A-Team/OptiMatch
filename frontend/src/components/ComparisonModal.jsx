import { useEffect } from 'react'

export default function ComparisonModal({ queryFaceBase64, matchFaceId, matchScore, matchMetadata, onClose }) {
  const scorePct = Math.round(matchScore * 100)
  const matchFaceUrl = `/faces/${matchFaceId}.jpg`

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-xl border border-slate-600 shadow-xl max-w-4xl w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold">Side-by-Side Comparison</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="grid grid-cols-2 gap-6 p-6">
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">Query Face</h3>
            <div className="aspect-square bg-slate-700 rounded-lg overflow-hidden flex items-center justify-center">
              {queryFaceBase64 ? (
                <img
                  src={`data:image/jpeg;base64,${queryFaceBase64}`}
                  alt="Query"
                  className="w-full h-full object-contain"
                />
              ) : (
                <span className="text-slate-500">N/A</span>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">Match ({scorePct}%)</h3>
            <div className="aspect-square bg-slate-700 rounded-lg overflow-hidden flex items-center justify-center">
              <img
                src={matchFaceUrl}
                alt="Match"
                className="w-full h-full object-contain"
              />
            </div>
            {matchMetadata?.link_to_post && (
              <a
                href={matchMetadata.link_to_post}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:underline text-sm block"
              >
                Open Original Post →
              </a>
            )}
            {matchMetadata?.platform && (
              <p className="text-slate-500 text-sm">{matchMetadata.platform}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
