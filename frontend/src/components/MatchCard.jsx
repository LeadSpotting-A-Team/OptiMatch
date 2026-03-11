export default function MatchCard({ result, onClick }) {
  const scorePct = Math.round(result.score * 100)
  const faceImgUrl = `/faces/${result.face_id}.jpg`
  const isHighScore = scorePct > 85

  return (
    <div
      onClick={() => onClick(result)}
      className={`
        rounded-lg overflow-hidden cursor-pointer transition-all duration-200
        border bg-slate-900 hover:brightness-110
        ${isHighScore
          ? 'border-cyan-500 cyber-glow' + (scorePct > 95 ? ' cyber-glow-pulse' : '')
          : 'border-slate-800 hover:border-cyan-900'}
      `}
    >
      <div className="aspect-square bg-slate-950 flex items-center justify-center overflow-hidden relative">
        <img
          src={faceImgUrl}
          alt={`Match ${result.face_id}`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%230f172a" width="100" height="100"/><text x="50" y="55" fill="%230e7490" text-anchor="middle" font-size="10" font-family="monospace">NO IMG</text></svg>'
          }}
        />
        {/* Score badge overlay */}
        <div className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold
          ${isHighScore ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50' : 'bg-black/60 text-slate-400 border border-slate-700/60'}`}>
          {scorePct}%
        </div>
      </div>

      <div className="p-2 space-y-1 bg-slate-900">
        <div className={`font-mono text-xs font-bold tracking-wide
          ${isHighScore ? 'text-cyan-400' : 'text-slate-400'}`}>
          {scorePct}% MATCH
        </div>
        {result.platform && (
          <p className="text-[10px] text-slate-600 font-mono truncate uppercase tracking-wider">
            {result.platform}
          </p>
        )}
        {result.timestamp && (
          <p className="text-[10px] text-slate-700 font-mono truncate">
            {result.timestamp}
          </p>
        )}
        {result.link_to_post && (
          <a
            href={result.link_to_post}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-[10px] text-cyan-700 hover:text-cyan-400 block truncate font-mono transition-colors"
          >
            SOURCE →
          </a>
        )}
      </div>
    </div>
  )
}
