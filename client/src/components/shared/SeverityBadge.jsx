import { getSeverityByLabel } from '../../lib/severity'

const SEVERITY_DOTS = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#3b82f6',
  SAFE:     '#22c55e',
}

export default function SeverityBadge({ label, score, size = 'sm' }) {
  const sev = getSeverityByLabel(label)
  const dot = SEVERITY_DOTS[label] ?? '#71717a'
  const sizes = { sm: 'text-xs px-2 py-0.5 gap-1.5', md: 'text-xs px-2.5 py-1 gap-1.5', lg: 'text-sm px-3 py-1 gap-2' }

  return (
    <span
      className={`inline-flex items-center rounded-md font-medium ${sizes[size]}`}
      style={{
        color: dot,
        background: `${dot}14`,
        border: `1px solid ${dot}30`,
      }}
    >
      <span className="h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ background: dot }} />
      {label}
      {score !== undefined && <span style={{ color: `${dot}99` }}>({score})</span>}
    </span>
  )
}

