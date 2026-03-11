export default function MatchCard({ result, onClick }) {
  const scorePct = Math.round(result.score * 100)
  const faceImgUrl = `/faces/${result.face_id}.jpg`

  return (
    <div
      onClick={() => onClick(result)}
      className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700 hover:border-sky-500/50 cursor-pointer transition-colors"
    >
      <div className="aspect-square bg-slate-700 flex items-center justify-center overflow-hidden">
        <img
          src={faceImgUrl}
          alt={`Match ${result.face_id}`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23334155" width="100" height="100"/><text x="50" y="55" fill="%2394a3b8" text-anchor="middle" font-size="12">No preview</text></svg>'
          }}
        />
      </div>
      <div className="p-3 space-y-1">
        <span className="text-sky-400 font-semibold text-sm">{scorePct}% Match</span>
        {result.platform && (
          <p className="text-xs text-slate-500 truncate">{result.platform}</p>
        )}
        {result.timestamp && (
          <p className="text-xs text-slate-500 truncate">{result.timestamp}</p>
        )}
        {result.link_to_post && (
          <a
            href={result.link_to_post}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-sky-400 hover:underline block truncate"
          >
            Original Post →
          </a>
        )}
      </div>
    </div>
  )
}
