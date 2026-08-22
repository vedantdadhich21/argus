export default function ScoreBreakdown({ triggers = [] }) {
  const total = triggers.reduce((s, t) => s + t.weight, 0)

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5">
        <h3 className="text-sm font-semibold text-white">Score Breakdown</h3>
        <p className="text-xs text-slate-500 mt-0.5">Every point is traceable to a triggered rule</p>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-slate-500 border-b border-white/5">
            <th className="text-left px-4 py-2 font-medium">Rule</th>
            <th className="text-left px-4 py-2 font-medium">Evidence</th>
            <th className="text-right px-4 py-2 font-medium">Points</th>
          </tr>
        </thead>
        <tbody>
          {triggers.map((t, i) => (
            <tr key={t.rule_id} className={`border-b border-white/[0.03] ${i % 2 === 0 ? 'bg-white/[0.01]' : ''}`}>
              <td className="px-4 py-2.5">
                <div className="font-mono text-xs text-red-400">{t.rule_id}</div>
                {t.description && (
                  <div className="text-xs text-slate-500 mt-0.5 max-w-xs">{t.description}</div>
                )}
              </td>
              <td className="px-4 py-2.5 text-xs text-slate-400 max-w-[200px]">{t.evidence}</td>
              <td className="px-4 py-2.5 text-right">
                <span className="font-bold text-orange-400">+{t.weight}</span>
              </td>
            </tr>
          ))}
          {/* Total row */}
          <tr className="border-t border-white/10 bg-white/[0.02]">
            <td className="px-4 py-2.5 text-sm font-bold text-white" colSpan={2}>Total (capped at 100)</td>
            <td className="px-4 py-2.5 text-right font-black text-2xl text-red-400">{Math.min(total, 100)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
