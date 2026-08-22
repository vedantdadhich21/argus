// score → { label, color (tailwind), hex, bg }
export const SEVERITY_BANDS = [
  { min: 75, max: 100, label: 'CRITICAL', color: 'text-red-400',    hex: '#f87171', bg: 'bg-red-500/10',    border: 'border-red-500/30',   ring: 'ring-red-500' },
  { min: 45, max: 74,  label: 'HIGH',     color: 'text-orange-400', hex: '#fb923c', bg: 'bg-orange-500/10', border: 'border-orange-500/30', ring: 'ring-orange-500' },
  { min: 20, max: 44,  label: 'MEDIUM',   color: 'text-yellow-400', hex: '#facc15', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', ring: 'ring-yellow-400' },
  { min: 1,  max: 19,  label: 'LOW',      color: 'text-blue-400',   hex: '#60a5fa', bg: 'bg-blue-500/10',   border: 'border-blue-500/30',  ring: 'ring-blue-400' },
  { min: 0,  max: 0,   label: 'SAFE',     color: 'text-green-400',  hex: '#4ade80', bg: 'bg-green-500/10',  border: 'border-green-500/30', ring: 'ring-green-400' },
]

export function getSeverity(score) {
  if (score >= 75) return SEVERITY_BANDS[0]
  if (score >= 45) return SEVERITY_BANDS[1]
  if (score >= 20) return SEVERITY_BANDS[2]
  if (score >= 1)  return SEVERITY_BANDS[3]
  return SEVERITY_BANDS[4]
}

export function getSeverityByLabel(label) {
  return SEVERITY_BANDS.find(b => b.label === label) ?? SEVERITY_BANDS[4]
}

export const DANGER_COLORS = {
  dangerous: 'text-red-400',
  normal:    'text-slate-400',
  signature: 'text-blue-400',
}
