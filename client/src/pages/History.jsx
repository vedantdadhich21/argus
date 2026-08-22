import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useScans } from '../hooks/useScans'
import SeverityBadge from '../components/shared/SeverityBadge'
import { Loader2, Filter } from 'lucide-react'

const ALL_SEVERITIES = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE']

const CATEGORY_LABELS = {
  banking_trojan: 'Banking Trojan', sms_otp_stealer: 'OTP Stealer',
  overlay_phishing: 'Overlay Phishing', spyware: 'Spyware',
  benign: 'Benign', adware: 'Adware',
}

export default function History() {
  const { data, isLoading } = useScans()
  const [filter, setFilter] = useState('All')

  const scans = data?.scans ?? []
  const filtered = filter === 'All' ? scans : scans.filter(s => s.severity === filter)

  return (
    <div className="min-h-screen bg-slate-950 pt-20">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Scan History</h1>
            <p className="text-sm text-slate-500 mt-1">{data?.total ?? 0} total scans</p>
          </div>

          {/* Severity filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <div className="flex gap-1">
              {ALL_SEVERITIES.map(s => (
                <button
                  key={s}
                  onClick={() => setFilter(s)}
                  className={`rounded-lg px-3 py-1 text-xs font-medium transition-all ${
                    filter === s
                      ? 'bg-white/10 text-white'
                      : 'text-slate-500 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-red-400" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] py-16 text-center text-slate-500">
            No scans found{filter !== 'All' ? ` with severity ${filter}` : ''}.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map(scan => (
              <Link
                key={scan.scan_id}
                to={`/scan/${scan.scan_id}`}
                className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] px-5 py-4 hover:border-white/10 hover:bg-white/[0.04] transition-all group"
              >
                <div className="flex items-center gap-4 min-w-0">
                  {/* Score badge */}
                  <div className="flex-shrink-0 w-12 text-center">
                    <span className="text-2xl font-black text-white">{scan.final_score}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate group-hover:text-red-300 transition-colors">{scan.original_filename}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {CATEGORY_LABELS[scan.fraud_category] ?? scan.fraud_category} · {new Date(scan.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <SeverityBadge label={scan.severity} size="sm" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
