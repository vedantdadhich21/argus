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
    <button onClick={copy} className="flex items-center gap-1.5 font-mono text-xs text-slate-300 hover:text-white transition-colors group">
      <span className="break-all text-left">{text}</span>
      {copied
        ? <Check className="h-3 w-3 flex-shrink-0 text-green-400" />
        : <Copy className="h-3 w-3 flex-shrink-0 opacity-0 group-hover:opacity-60 transition-opacity" />
      }
    </button>
  )
}

export default function IocTable({ iocs = {} }) {
  const sections = [
    { key: 'domains',      label: 'Domains',      color: 'text-purple-400' },
    { key: 'ips',          label: 'IP Addresses',  color: 'text-red-400' },
    { key: 'urls',         label: 'URLs',          color: 'text-orange-400' },
    { key: 'phones',       label: 'Phone Numbers', color: 'text-yellow-400' },
    { key: 'base64_blobs', label: 'Encoded Blobs', color: 'text-blue-400' },
  ].filter(s => iocs[s.key]?.length > 0)

  if (sections.length === 0) return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] px-6 py-8 text-center text-sm text-slate-500">
      No IOCs extracted.
    </div>
  )

  return (
    <div className="flex flex-col gap-4">
      {sections.map(({ key, label, color }) => (
        <div key={key} className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className={`px-4 py-2.5 border-b border-white/5 text-xs font-semibold ${color}`}>
            {label} ({iocs[key].length})
          </div>
          <div className="divide-y divide-white/[0.03]">
            {iocs[key].map((item) => (
              <div key={item} className="px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                <CopyCell text={item} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
