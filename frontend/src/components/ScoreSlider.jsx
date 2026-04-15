export default function ScoreSlider({ value, onChange }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg border border-blue-200 bg-white w-full md:w-auto shadow-sm">
      <label htmlFor="score-slider" className="text-xs text-gray-500 font-medium tracking-wide uppercase shrink-0">
        Min Score
      </label>
      <input
        id="score-slider"
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 md:w-40 h-1.5 rounded-lg appearance-none cursor-pointer bg-blue-100 accent-blue-600"
      />
      <span className="text-blue-600 font-semibold text-sm w-10 tabular-nums">{value}%</span>
    </div>
  )
}
