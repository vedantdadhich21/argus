import { getSeverity } from '../../lib/severity'

/**
 * SVG semicircle gauge. score 0-100, animates via strokeDashoffset.
 * size: 'sm' | 'lg'
 */
export default function RiskGauge({ score = 0, size = 'lg' }) {
  const sev = getSeverity(score)
  const dim = size === 'sm' ? 120 : 220
  const cx  = dim / 2
  const cy  = dim / 2
  const r   = size === 'sm' ? 48 : 88
  const strokeW = size === 'sm' ? 8 : 14

  // Semicircle: start from 180° (left) to 0° (right) — top half
  const circumference = Math.PI * r
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={dim} height={dim / 2 + (size === 'sm' ? 10 : 20)} viewBox={`0 0 ${dim} ${dim / 2 + 20}`}>
        {/* Track */}
        <path
          d={`M ${strokeW / 2} ${cy} A ${r} ${r} 0 0 1 ${dim - strokeW / 2} ${cy}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={`M ${strokeW / 2} ${cy} A ${r} ${r} 0 0 1 ${dim - strokeW / 2} ${cy}`}
          fill="none"
          stroke={sev.hex}
          strokeWidth={strokeW}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1), stroke 0.6s ease', filter: `drop-shadow(0 0 8px ${sev.hex}80)` }}
        />
        {/* Score text */}
        <text x={cx} y={cy - (size === 'sm' ? 6 : 10)} textAnchor="middle"
          fill="white" fontSize={size === 'sm' ? 22 : 40} fontWeight="700" fontFamily="Inter,sans-serif">
          {score}
        </text>
        <text x={cx} y={cy + (size === 'sm' ? 12 : 18)} textAnchor="middle"
          fill={sev.hex} fontSize={size === 'sm' ? 9 : 14} fontWeight="600" fontFamily="Inter,sans-serif">
          {sev.label}
        </text>
      </svg>
    </div>
  )
}
