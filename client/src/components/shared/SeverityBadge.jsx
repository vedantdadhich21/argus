import { getSeverityByLabel } from '../../lib/severity'

const EMOJI = { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🔵', SAFE: '🟢' }

export default function SeverityBadge({ label, score, size = 'sm' }) {
  const sev = getSeverityByLabel(label)
  const sizes = { sm: 'text-xs px-2 py-0.5', md: 'text-sm px-3 py-1', lg: 'text-base px-4 py-1.5' }

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-semibold ${sizes[size]} ${sev.bg} ${sev.border} ${sev.color}`}>
      <span>{EMOJI[label] ?? '⚪'}</span>
      {label}
      {score !== undefined && <span className="opacity-70">({score})</span>}
    </span>
  )
}
