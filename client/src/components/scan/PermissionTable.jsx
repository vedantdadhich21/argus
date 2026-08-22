const DANGER_STYLES = {
  dangerous: { label: 'Dangerous', text: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.25)' },
  normal:    { label: 'Normal',    text: '#71717a', bg: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.06)' },
  signature: { label: 'Signature', text: '#38bdf8', bg: 'rgba(56,189,248,0.08)', border: 'rgba(56,189,248,0.2)' },
}

export default function PermissionTable({ permissions = [] }) {
  const dangerous = permissions.filter(p => p.danger_level === 'dangerous')
  const normal    = permissions.filter(p => p.danger_level !== 'dangerous')

  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.07)' }}>
      <div className="px-5 py-3.5 flex items-center justify-between"
        style={{ background: '#111113', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div>
          <h3 className="text-sm font-semibold text-white">Declared Permissions</h3>
          <p className="text-xs mt-0.5" style={{ color: '#71717a' }}>
            {dangerous.length} elevated · {normal.length} standard
          </p>
        </div>
        <span className="text-xs font-mono font-medium px-2.5 py-1 rounded"
          style={{ color: '#a1a1aa', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
          {permissions.length} total
        </span>
      </div>

      <div className="divide-y divide-white/[0.04] max-h-[420px] overflow-y-auto">
        {[...dangerous, ...normal].map((p) => {
          const meta = DANGER_STYLES[p.danger_level] ?? DANGER_STYLES.normal
          return (
            <div key={p.name} className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors">
              <span className="font-mono text-xs text-zinc-300 break-all">{p.name}</span>
              <span className="ml-3 flex-shrink-0 text-xs font-mono font-medium px-2 py-0.5 rounded"
                style={{ color: meta.text, background: meta.bg, border: `1px solid ${meta.border}` }}>
                {meta.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

