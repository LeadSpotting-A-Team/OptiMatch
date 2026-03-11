export default function ScoreSlider({ value, onChange }) {
  return (
    <div className="flex items-center gap-4 px-3 py-2 rounded-lg border border-cyan-900/40 bg-slate-950/60">
      <label htmlFor="score-slider" className="text-[11px] text-cyan-800 font-mono tracking-widest uppercase shrink-0">
        Min Score
      </label>
      <input
        id="score-slider"
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-40 h-1 rounded-lg appearance-none cursor-pointer bg-slate-800 accent-cyan-500"
      />
      <span className="text-cyan-400 font-mono text-sm w-10 tabular-nums">{value}%</span>
    </div>
  )
}
