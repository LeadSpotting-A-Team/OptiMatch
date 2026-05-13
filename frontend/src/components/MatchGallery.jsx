import MatchCard from './MatchCard'

export default function MatchGallery({ results, onCardClick, hasSearched, searchMessage }) {
  if (!hasSearched) {
    return (
      <div className="ls-grid rounded-xl min-h-[400px] flex flex-col items-center justify-center space-y-4 border border-blue-100">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center">
          <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
          </svg>
        </div>
        <p className="text-blue-300 text-sm font-medium">
          Upload an image to start searching
        </p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="ls-grid rounded-xl min-h-[400px] flex flex-col items-center justify-center space-y-4 border border-blue-100">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center">
          <span className="text-3xl text-blue-200">∅</span>
        </div>
        <p className="text-blue-400 text-sm font-medium">No matches found</p>
        <p className="text-gray-400 text-xs text-center max-w-sm">
          {searchMessage || 'No faces matched. Try lowering the minimum score threshold.'}
        </p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-blue-500 text-xs font-semibold tracking-wide uppercase mb-4">
        {results.length} match{results.length !== 1 ? 'es' : ''} found
      </p>
      <div className="ls-grid rounded-xl p-4 border border-blue-100">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {results.map((r) => (
            <MatchCard key={r.face_id} result={r} onClick={onCardClick} />
          ))}
        </div>
      </div>
    </div>
  )
}
