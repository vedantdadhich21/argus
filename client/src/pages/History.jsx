import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useScans } from '../hooks/useScans'
import SeverityBadge from '../components/shared/SeverityBadge'
import { Loader2, Database } from 'lucide-react'

const ALL_SEVERITIES = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE']

const CATEGORY_LABELS = {
  banking_trojan:    'Banking Trojan',
  sms_otp_stealer:   'OTP Stealer',
  overlay_phishing:  'Overlay Phishing',
  spyware:           'Spyware',
  premium_sms_fraud: 'Premium SMS Fraud',
  ransomware:        'Ransomware',
  adware:            'Adware',
  pupe:              'PUP / Riskware',
  benign:            'Benign Clean',
}

export default function History() {
  const { data, isLoading } = useScans()
  const [filter, setFilter] = useState('All')

  const scans = data?.scans ?? []
  const filtered = filter === 'All' ? scans : scans.filter(s => s.severity === filter)

  return (
    <div className="min-h-screen pt-14 pb-28" style={{ background: '#08080a' }}>
      <div className="mx-auto max-w-5xl px-6 sm:px-8 py-16">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10 pb-6 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Database className="h-4 w-4 text-zinc-400" />
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Threat Telemetry Database
              </h1>
            </div>
            <p className="text-sm text-zinc-400">
              {data?.total ?? 0} historical APK analyses registered
            </p>
          </div>

          {/* Filter pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {ALL_SEVERITIES.map(s => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className="px-3 py-1.5 text-xs rounded-lg font-mono font-medium transition-all duration-150"
                style={{
                  color: filter === s ? '#fafafa' : '#71717a',
                  background: filter === s ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                  border: filter === s ? '1px solid rgba(255,255,255,0.15)' : '1px solid rgba(255,255,255,0.05)',
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-28 gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
            <p className="text-xs font-mono text-zinc-500">Querying telemetry records…</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl p-16 text-center"
            style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.07)' }}>
            <p className="text-sm text-zinc-400">
              No analyses recorded {filter !== 'All' ? `with severity level ${filter}` : 'yet'}.
            </p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden divide-y divide-white/[0.04]"
            style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.07)' }}>
            {filtered.map((scan) => (
              <Link
                key={scan.scan_id}
                to={`/scan/${scan.scan_id}`}
                className="flex items-center justify-between px-6 py-4.5 transition-colors group hover:bg-white/[0.02]"
              >
                <div className="flex items-center gap-6 min-w-0">
                  <div className="w-10 text-center font-mono font-bold text-lg text-white tabular-nums flex-shrink-0">
                    {scan.final_score}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white truncate group-hover:text-sky-300 transition-colors">
                      {scan.original_filename}
                    </p>
                    <p className="text-xs text-zinc-500 mt-1 font-mono">
                      {CATEGORY_LABELS[scan.fraud_category] ?? scan.fraud_category ?? 'General Threat'}
                      {' · '}
                      SHA: {scan.sha256?.slice(0, 16)}…
                      {' · '}
                      {new Date(scan.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <SeverityBadge label={scan.severity} size="md" />
              </Link>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}


