export default function MitreList({ techniques = [] }) {
  if (!techniques.length) return (
    <p className="text-sm text-slate-500">No MITRE techniques mapped.</p>
  )

  return (
    <div className="flex flex-col gap-3">
      {techniques.map((t) => (
        <div key={t.id} className="flex gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-white/10 transition-colors">
          <a
            href={`https://attack.mitre.org/techniques/${t.id}/`}
            target="_blank"
            rel="noreferrer"
            className="flex-shrink-0 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-1.5 font-mono text-sm font-bold text-red-400 hover:bg-red-500/20 transition-colors"
          >
            {t.id}
          </a>
          <div>
            <p className="text-sm font-semibold text-white">{t.name}</p>
            <p className="text-xs text-slate-400 mt-0.5">{t.reason}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
