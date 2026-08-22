import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

function CopyCell({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button onClick={copy} className="flex items-center justify-between w-full font-mono text-xs text-zinc-300 hover:text-white transition-colors group text-left py-0.5">
      <span className="break-all">{text}</span>
      <span className="ml-3 flex-shrink-0 flex items-center gap-1 text-[11px] font-sans text-zinc-500 group-hover:text-zinc-300">
        {copied ? (
          <span className="text-emerald-400 flex items-center gap-1">
            <Check className="h-3.5 w-3.5" /> Copied
          </span>
        ) : (
          <span className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            <Copy className="h-3 w-3" /> Copy
          </span>
        )}
      </span>
    </button>
  )
}

export default function IocTable({ iocs = {} }) {
  const sections = [
    { key: 'domains',      label: 'C2 & Network Domains' },
    { key: 'ips',          label: 'IP Addresses' },
    { key: 'urls',         label: 'Endpoints & URLs' },
    { key: 'phones',       label: 'SMS / Phone Numbers' },
    { key: 'base64_blobs', label: 'Suspicious Encoded Payloads' },
  ].filter(s => iocs[s.key]?.length > 0)

  if (sections.length === 0) return (
    <div className="rounded-lg p-8 text-center text-sm"
      style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.07)', color: '#71717a' }}>
      No indicators of compromise (IOCs) extracted from this package.
    </div>
  )

  return (
    <div className="flex flex-col gap-5">
      {sections.map(({ key, label }) => (
        <div key={key} className="rounded-lg overflow-hidden"
          style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.07)' }}>
          <div className="px-5 py-3 flex items-center justify-between"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <span className="text-xs font-semibold text-white uppercase tracking-wider">
              {label}
            </span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded"
              style={{ color: '#a1a1aa', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
              {iocs[key].length}
            </span>
          </div>
          <div className="divide-y divide-white/[0.04] px-5 py-1">
            {iocs[key].map((item, idx) => (
              <div key={idx} className="py-2.5">
                <CopyCell text={item} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

