import { getSeverityByLabel } from '../../lib/severity'
import RiskGauge from './RiskGauge'
import { Shield, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

const ICONS = {
  CRITICAL: AlertTriangle,
  HIGH:     AlertTriangle,
  MEDIUM:   Info,
  LOW:      Info,
  SAFE:     CheckCircle2,
}

const CATEGORY_LABELS = {
  banking_trojan:    'Banking Trojan',
  sms_otp_stealer:   'SMS/OTP Stealer',
  overlay_phishing:  'Overlay Phishing',
  spyware:           'Spyware',
  premium_sms_fraud: 'Premium SMS Fraud',
  ransomware:        'Ransomware',
  adware:            'Adware',
  pupe:              'PUP/Adware',
  benign:            'Benign',
}

export default function VerdictCard({ scan }) {
  const sev  = getSeverityByLabel(scan.severity)
  const Icon = ICONS[scan.severity] ?? Shield

  return (
    <div className={`relative overflow-hidden rounded-2xl border p-6 ${sev.bg} ${sev.border}`}>
      {/* Background glow */}
      <div className={`pointer-events-none absolute -top-20 -right-20 h-60 w-60 rounded-full opacity-20 blur-3xl`}
        style={{ backgroundColor: sev.hex }} />

      <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        {/* Left: verdict info */}
        <div className="flex items-start gap-4">
          <div className={`flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl ${sev.bg} border ${sev.border}`}>
            <Icon className={`h-7 w-7 ${sev.color}`} />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className={`text-3xl font-black tracking-tight ${sev.color}`}>{scan.severity}</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-slate-400">
                {CATEGORY_LABELS[scan.fraud_category] ?? scan.fraud_category}
              </span>
            </div>
            <p className="text-sm text-slate-400">{scan.original_filename}</p>
            <p className="text-xs text-slate-600 mt-0.5">
              SHA-256: {scan.sha256?.slice(0, 16)}…
            </p>
            {scan.ai_status === 'unavailable' && (
              <p className="mt-2 text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded px-2 py-1">
                ⚠️ AI analysis unavailable — verdict based on rules engine only
              </p>
            )}
          </div>
        </div>

        {/* Right: gauge */}
        <div className="flex-shrink-0">
          <RiskGauge score={scan.final_score} size="lg" />
        </div>
      </div>
    </div>
  )
}
