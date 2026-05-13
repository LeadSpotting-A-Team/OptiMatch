export default function MatchCard({ result, onClick }) {
  const scorePct = Math.round(result.score * 100)
  const faceImgUrl = result.media_url || `/faces/${result.face_id}.jpg`
  const isHighScore = scorePct > 85

  return (
    <div
      onClick={() => onClick(result)}
      className={`
        rounded-lg overflow-hidden cursor-pointer transition-all duration-200
        border bg-white hover:shadow-md hover:-translate-y-0.5
        ${isHighScore
          ? 'ls-glow' + (scorePct > 95 ? ' ls-glow-pulse' : '')
          : 'border-blue-100 hover:border-blue-300'}
      `}
    >
      <div className="aspect-square bg-blue-50 flex items-center justify-center overflow-hidden relative">
        <img
          src={faceImgUrl}
          alt={`Match ${result.face_id}`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23EEF4FB" width="100" height="100"/><text x="50" y="55" fill="%2390CAF9" text-anchor="middle" font-size="10" font-family="sans-serif">NO IMG</text></svg>'
          }}
        />
        {/* Score badge */}
        <div className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-bold
          ${isHighScore
            ? 'bg-blue-600 text-white'
            : 'bg-white/80 text-gray-500 border border-blue-100'}`}>
          {scorePct}%
        </div>
      </div>

      <div className="p-2 space-y-1 bg-white">
        <div className={`text-xs font-bold tracking-wide
          ${isHighScore ? 'text-blue-600' : 'text-gray-500'}`}>
          {scorePct}% Match
        </div>
        {result.platform && (
          <p className="text-[10px] text-gray-400 truncate uppercase tracking-wider">
            {result.platform}
          </p>
        )}
        {result.timestamp && (
          <p className="text-[10px] text-gray-400 truncate">
            {result.timestamp}
          </p>
        )}
        {result.link_to_post && (
          <a
            href={result.link_to_post}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-[10px] text-blue-500 hover:text-blue-700 block truncate transition-colors"
          >
            View Source →
          </a>
        )}
      </div>
    </div>
  )
}
