export default function ScoreBreakdown({ triggers = [] }) {
  const total = triggers.reduce((s, t) => s + (t.effective_weight ?? t.weight ?? 0), 0)

  if (!triggers.length) return (
    <div className="rounded-xl p-6 text-center text-sm"
      style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.07)', color: '#71717a' }}>
      No suspicious heuristics triggered. Package clean.
    </div>
  )

  return (
    <div className="overflow-hidden rounded-xl"
      style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.08)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div>
          <h3 className="text-sm font-semibold text-white tracking-tight">Deterministic Rule Evidence</h3>
          <p className="text-xs text-zinc-400 mt-0.5">Every threat point is traced to static bytecode and manifest signatures</p>
        </div>
        <span className="text-xs font-mono font-medium px-2.5 py-1 rounded"
          style={{ color: '#a1a1aa', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
          {triggers.length} rules triggered
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider font-semibold text-zinc-400"
              style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.01)' }}>
              <th className="px-6 py-3">Rule Identifier</th>
              <th className="px-6 py-3">Matched Bytecode Evidence</th>
              <th className="px-6 py-3 text-right">Risk Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {triggers.map((t, idx) => {
              const pts = t.effective_weight ?? t.weight ?? 0
              return (
                <tr key={`${t.rule_id}-${idx}`} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 align-top">
                    <div className="font-mono text-xs font-semibold text-zinc-100">{t.rule_id}</div>
                    {t.description && (
                      <div className="text-xs text-zinc-400 mt-1 max-w-sm leading-relaxed">{t.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 align-top">
                    <div className="font-mono text-xs text-zinc-300 break-all max-w-md bg-white/[0.02] px-2.5 py-1.5 rounded border border-white/[0.04]">
                      {t.evidence || 'Pattern detected'}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right align-top">
                    <span className="inline-flex items-center text-sm font-mono font-bold px-2.5 py-1 rounded"
                      style={{ color: '#fb923c', background: 'rgba(251,146,60,0.1)', border: '1px solid rgba(251,146,60,0.2)' }}>
                      +{pts}
                    </span>
                  </td>
                </tr>
              )
            })}
            <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
              <td className="px-6 py-4 text-sm font-semibold text-white" colSpan={2}>
                Aggregated Total Risk <span className="text-xs font-normal text-zinc-400">(Normalized to 100 max)</span>
              </td>
              <td className="px-6 py-4 text-right">
                <span className="text-2xl font-mono font-bold text-white tracking-tight">
                  {Math.min(total, 100)}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}



