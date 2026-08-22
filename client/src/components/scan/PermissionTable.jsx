const DANGER_LABELS = {
  dangerous: { label: 'Dangerous', cls: 'text-red-400 bg-red-500/10 border-red-500/20' },
  normal:    { label: 'Normal',    cls: 'text-slate-400 bg-white/5 border-white/10' },
  signature: { label: 'Signature', cls: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
}

export default function PermissionTable({ permissions = [] }) {
  const dangerous = permissions.filter(p => p.danger_level === 'dangerous')
  const normal    = permissions.filter(p => p.danger_level !== 'dangerous')

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Permissions</h3>
          <p className="text-xs text-slate-500">{dangerous.length} dangerous · {normal.length} normal</p>
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
          dangerous.length > 5 ? 'text-red-400 bg-red-500/10 border-red-500/20' :
          dangerous.length > 2 ? 'text-orange-400 bg-orange-500/10 border-orange-500/20' :
          'text-green-400 bg-green-500/10 border-green-500/20'
        }`}>{permissions.length} total</span>
      </div>
      <div className="divide-y divide-white/[0.03]">
        {[...dangerous, ...normal].map((p) => {
          const meta = DANGER_LABELS[p.danger_level] ?? DANGER_LABELS.normal
          return (
            <div key={p.name} className="flex items-center justify-between px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
              <span className="font-mono text-xs text-slate-300 break-all">{p.name}</span>
              <span className={`ml-3 flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${meta.cls}`}>
                {meta.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
