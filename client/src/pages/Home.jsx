import Dropzone from '../components/upload/Dropzone'
import SeverityBadge from '../components/shared/SeverityBadge'
import RiskGauge from '../components/scan/RiskGauge'
import { useScans, useStats } from '../hooks/useScans'
import { Link } from 'react-router-dom'
import { Shield, Zap, Eye, Lock } from 'lucide-react'

function StatCard({ label, value, sub }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
      <p className="text-3xl font-black text-white tabular-nums">{value ?? '—'}</p>
      <p className="text-sm font-semibold text-slate-400 mt-1">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Home() {
  const { data: stats }  = useStats()
  const { data: history } = useScans(1, 5)

  const features = [
    { icon: Zap,    title: 'Instant Hash Cache',  desc: 'Previously seen APKs return verdicts in milliseconds' },
    { icon: Eye,    title: 'AI Attack Chain',      desc: 'LLM reconstructs the fraud story step-by-step' },
    { icon: Lock,   title: 'Explainable Scoring',  desc: 'Every point traced to a triggered rule — no black box' },
    { icon: Shield, title: 'Bank-Ready API',        desc: 'POST /api/lookup/hash is one integration away from your gateway' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 pt-20">
      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-red-950/20 via-transparent to-transparent" />
        <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-96 w-96 rounded-full bg-red-500/5 blur-3xl" />

        <div className="relative mx-auto max-w-4xl px-6 py-20 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400">
            <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse" />
            SW-07 · Bank Fraud Prevention · GenAI Powered
          </div>

          <h1 className="mb-4 text-5xl font-black tracking-tight text-white leading-tight">
            APK <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">Sentinel</span>
          </h1>
          <p className="mx-auto mb-10 max-w-xl text-lg text-slate-400">
            Intelligence at the core, protection at the edge — one engine protecting both the bank analyst and the end customer.
          </p>

          {/* Stats strip */}
          <div className="mb-12 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Total Scans"     value={stats?.total_scans?.toLocaleString()} />
            <StatCard label="Threats Found"   value={stats?.malicious_found?.toLocaleString()} />
            <StatCard label="Avg Scan Time"   value={stats?.avg_duration_ms ? `${(stats.avg_duration_ms/1000).toFixed(1)}s` : null} />
            <StatCard label="Unique Hashes"   value={stats?.unique_hashes?.toLocaleString()} />
          </div>

          {/* Dropzone */}
          <Dropzone />
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-4xl px-6 py-16">
        <h2 className="text-center text-2xl font-bold text-white mb-10">Why APK Sentinel</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-5 hover:border-white/10 transition-colors">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-red-500/10 border border-red-500/20">
                <Icon className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Recent scans */}
      {history?.scans?.length > 0 && (
        <section className="mx-auto max-w-4xl px-6 pb-20">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">Recent Scans</h2>
            <Link to="/history" className="text-xs text-slate-400 hover:text-white transition-colors">View all →</Link>
          </div>
          <div className="flex flex-col gap-2">
            {history.scans.slice(0,5).map(scan => (
              <Link key={scan.scan_id} to={`/scan/${scan.scan_id}`}
                className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 hover:border-white/10 hover:bg-white/[0.04] transition-all">
                <div className="flex items-center gap-3">
                  <RiskGauge score={scan.final_score} size="sm" />
                  <div>
                    <p className="text-sm font-medium text-white">{scan.original_filename}</p>
                    <p className="text-xs text-slate-500">{new Date(scan.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <SeverityBadge label={scan.severity} size="sm" />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
