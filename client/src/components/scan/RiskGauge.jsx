import { getSeverity } from '../../lib/severity'

/**
 * SVG semicircle gauge. score 0-100, animates via strokeDashoffset.
 * size: 'sm' | 'lg'
 */
export default function RiskGauge({ score = 0, size = 'lg' }) {
  const sev = getSeverity(score)
  const isSm = size === 'sm'

  const dim     = isSm ? 160 : 260
  const cx      = dim / 2
  const r       = isSm ? 60 : 100
  const strokeW = isSm ? 10 : 16
  const cy      = isSm ? 85 : 135

  // Left to right semicircle (top half)
  const sx = cx - r
  const sy = cy
  const ex = cx + r
  const ey = cy

  // Standard SVG top-arc path (sweeps 180° through top)
  const trackPath = `M ${sx} ${sy} A ${r} ${r} 0 0 1 ${ex} ${ey}`
  const circumference = Math.PI * r

  // Clamp score: 0 to 100
  const clampedScore = Math.min(Math.max(Number(score) || 0, 0), 100)
  // When score = 0, offset = circumference (hidden). When score = 100, offset = 0 (full arc).
  const offset = circumference * (1 - clampedScore / 100)

  const svgH = cy + strokeW + 4

  return (
    <div className="flex flex-col items-center justify-center select-none">
      <svg width={dim} height={svgH} viewBox={`0 0 ${dim} ${svgH}`} className="overflow-visible">
        <defs>
          <linearGradient id={`gauge-grad-${dim}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={sev.hex} stopOpacity="0.85" />
            <stop offset="100%" stopColor={sev.hex} stopOpacity="1" />
          </linearGradient>
          <filter id={`gauge-glow-${dim}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={isSm ? "3" : "5"} result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Base Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />

        {/* Dynamic Fill Arc */}
        {clampedScore > 0 && (
          <path
            d={trackPath}
            fill="none"
            stroke={`url(#gauge-grad-${dim})`}
            strokeWidth={strokeW}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={offset}
            filter={`url(#gauge-glow-${dim})`}
            style={{
              transition: 'stroke-dashoffset 1.1s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.4s ease',
            }}
          />
        )}

        {/* Score Number */}
        <text
          x={cx}
          y={cy - (isSm ? 10 : 18)}
          textAnchor="middle"
          fill="#fafafa"
          fontSize={isSm ? 32 : 54}
          fontWeight="700"
          className="font-mono tracking-tighter"
        >
          {clampedScore}
        </text>

        {/* Severity Label */}
        <text
          x={cx}
          y={cy + (isSm ? 8 : 12)}
          textAnchor="middle"
          fill={sev.hex}
          fontSize={isSm ? 11 : 14}
          fontWeight="600"
          letterSpacing="0.1em"
          className="uppercase tracking-widest font-sans"
        >
          {sev.label}
        </text>
      </svg>
    </div>
  )
}



