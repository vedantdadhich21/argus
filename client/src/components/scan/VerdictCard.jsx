import { getSeverityByLabel } from '../../lib/severity'
import RiskGauge from './RiskGauge'
import { Shield, AlertCircle } from 'lucide-react'

const CATEGORY_LABELS = {
  banking_trojan:    'Banking Trojan',
  sms_otp_stealer:   'SMS/OTP Stealer',
  overlay_phishing:  'Overlay Phishing',
  spyware:           'Spyware',
  premium_sms_fraud: 'Premium SMS Fraud',
  ransomware:        'Ransomware',
  adware:            'Adware',
  pupe:              'PUP / Riskware',
  benign:            'Benign Clean Sample',
}

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#38bdf8',
  SAFE:     '#22c55e',
}

export default function VerdictCard({ scan }) {
  const sev   = getSeverityByLabel(scan.severity)
  const color = SEVERITY_COLORS[scan.severity] ?? '#71717a'

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 rounded-xl px-7 py-7 overflow-hidden transition-all"
      style={{
        background: '#0d0d10',
        border: '1px solid rgba(255,255,255,0.08)',
        borderLeft: `4px solid ${color}`,
        boxShadow: '0 10px 30px -10px rgba(0,0,0,0.6)'
      }}>

      {/* Left: verdict info */}
      <div className="flex flex-col gap-3 max-w-xl">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-3xl sm:text-4xl font-bold tracking-tight font-mono" style={{ color }}>
            {scan.severity}
          </span>
          <span className="text-xs font-mono font-medium px-2.5 py-1 rounded"
            style={{ color: '#d4d4d8', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
            {CATEGORY_LABELS[scan.fraud_category] ?? scan.fraud_category ?? 'Unknown Category'}
          </span>
        </div>

        <div>
          <h2 className="text-lg sm:text-xl text-white font-semibold tracking-tight truncate max-w-md">
            {scan.original_filename}
          </h2>
          <p className="text-xs font-mono text-zinc-500 mt-1 select-all break-all">
            SHA-256: {scan.sha256}
          </p>
        </div>

        {scan.ai_status === 'unavailable' && (
          <div className="flex items-center gap-2 text-xs font-medium text-amber-400 mt-1">
            <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
            <span>AI narrative layer offline — score computed via deterministic rules engine</span>
          </div>
        )}
      </div>

      {/* Right: gauge */}
      <div className="flex-shrink-0 flex items-center justify-center sm:justify-end">
        <RiskGauge score={scan.final_score} size="lg" />
      </div>
    </div>
  )
}





