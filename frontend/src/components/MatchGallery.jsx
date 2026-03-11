import MatchCard from './MatchCard'

export default function MatchGallery({ results, onCardClick, hasSearched }) {
  if (!hasSearched) {
    return (
      <div className="cyber-grid rounded-xl min-h-[400px] flex flex-col items-center justify-center space-y-4 border border-cyan-900/30">
        <div className="text-5xl opacity-20 font-mono select-none">[ ]</div>
        <p className="text-cyan-900 text-sm font-mono tracking-widest uppercase">
          Awaiting target acquisition...
        </p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="cyber-grid rounded-xl min-h-[400px] flex flex-col items-center justify-center space-y-4 border border-cyan-900/30">
        <div className="text-4xl opacity-30 font-mono select-none">∅</div>
        <p className="text-cyan-600 text-sm font-mono tracking-widest uppercase">No matches found</p>
        <p className="text-cyan-900 text-xs font-mono text-center max-w-sm">
          No faces matched. Try lowering the minimum score threshold.
        </p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-cyan-800 text-xs font-mono tracking-widest uppercase mb-4">
        ◈ {results.length} match{results.length !== 1 ? 'es' : ''} acquired
      </p>
      <div className="cyber-grid rounded-xl p-4 border border-cyan-900/30">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {results.map((r) => (
            <MatchCard key={r.face_id} result={r} onClick={onCardClick} />
          ))}
        </div>
      </div>
    </div>
  )
}
