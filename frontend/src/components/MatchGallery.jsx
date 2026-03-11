import MatchCard from './MatchCard'

export default function MatchGallery({ results, onCardClick, hasSearched }) {
  if (!hasSearched) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] text-slate-500 space-y-3">
        <div className="text-5xl opacity-30">🔍</div>
        <p className="text-lg">Upload an image or paste a URL and click Search</p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] space-y-3">
        <div className="text-5xl opacity-40">🙁</div>
        <p className="text-lg text-slate-400 font-medium">No matches found</p>
        <p className="text-sm text-slate-500 text-center max-w-sm">
          No faces in the database matched your query. Try lowering the minimum score
          or searching with a different image.
        </p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-slate-500 text-sm mb-4">{results.length} match{results.length !== 1 ? 'es' : ''} found</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {results.map((r) => (
          <MatchCard key={r.face_id} result={r} onClick={onCardClick} />
        ))}
      </div>
    </div>
  )
}
