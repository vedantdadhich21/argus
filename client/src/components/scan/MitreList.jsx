import { ExternalLink } from 'lucide-react'

export default function MitreList({ techniques = [] }) {
  if (!techniques?.length) return (
    <p className="text-sm" style={{ color: '#52525b' }}>No MITRE ATT&CK techniques mapped for this sample.</p>
  )

  return (
    <div className="flex flex-col gap-3">
      {techniques.map((t) => (
        <div key={t.id} className="flex items-start gap-4 rounded-lg p-4 transition-all duration-150 group"
          style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.07)' }}>
          <a
            href={`https://attack.mitre.org/techniques/${t.id}/`}
            target="_blank"
            rel="noreferrer"
            className="flex-shrink-0 inline-flex items-center gap-1.5 rounded px-2.5 py-1 font-mono text-xs font-semibold text-white transition-colors"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <span>{t.id}</span>
            <ExternalLink className="h-3 w-3 text-zinc-400 group-hover:text-white transition-colors" />
          </a>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white mb-0.5">{t.name}</p>
            <p className="text-xs text-zinc-400 leading-relaxed">{t.reason}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

