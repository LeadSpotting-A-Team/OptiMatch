export default function ScoreSlider({ value, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <label htmlFor="score-slider" className="text-sm text-slate-400 shrink-0">
        Min match score:
      </label>
      <input
        id="score-slider"
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-40 h-2 rounded-lg appearance-none cursor-pointer bg-slate-700 accent-sky-500"
      />
      <span className="text-sky-400 font-mono text-sm w-10">{value}%</span>
    </div>
  )
}
