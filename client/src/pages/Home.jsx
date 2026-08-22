import Dropzone from '../components/upload/Dropzone'
import SeverityBadge from '../components/shared/SeverityBadge'
import { useScans, useStats } from '../hooks/useScans'
import { Link } from 'react-router-dom'
import { ShieldCheck, Cpu, Terminal, Sparkles, ArrowRight, Activity, Zap } from 'lucide-react'

function Stat({ label, value, sub }) {
  return (
    <div className="flex flex-col gap-1.5 min-w-[130px]">
      <span className="text-3xl sm:text-4xl font-semibold tracking-tight text-white tabular-nums font-mono">
        {value ?? '—'}
      </span>
      <div className="flex flex-col">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          {label}
        </span>
        {sub && <span className="text-[11px] text-zinc-500 font-mono mt-0.5">{sub}</span>}
      </div>
    </div>
  )
}

const FEATURES = [
  {
    icon: Zap,
    label: 'Zero-Latency Hash Cache',
    desc: 'Instant cryptographic SHA-256 verification against verified malicious threat database — sub-millisecond return for cached samples.',
    tag: 'Cache Layer'
  },
  {
    icon: Terminal,
    label: 'Deep Static & Manifest Parsing',
    desc: 'Comprehensive extraction of declared permissions, dynamic intent filters, exported receivers, and cryptographic certificates via Androguard.',
    tag: 'Static Engine'
  },
  {
    icon: Cpu,
    label: 'Bytecode Pattern Scanning',
    desc: 'Automated Jadx decompilation cross-checked against 32+ deterministic security heuristics with framework-filtering and AST method isolation.',
    tag: 'Heuristics'
  },
  {
    icon: Sparkles,
    label: 'AI Kill Chain Reconstruction',
    desc: 'Specialized LLM behavioral analyst constructs end-to-end attack narratives, MITRE ATT&CK® Mobile mapping, and remediation steps.',
    tag: 'GenAI Analyst'
  },
]

export default function Home() {
  const { data: stats }   = useStats()
  const { data: history } = useScans(1, 5)

  return (
    <div className="relative min-h-screen pt-14 pb-24 overflow-hidden" style={{ background: '#08080a' }}>
      {/* Ambient background glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none radial-glow-cyan opacity-70" />
      <div className="absolute top-40 right-[-10%] w-[500px] h-[500px] pointer-events-none radial-glow-violet opacity-60" />
      <div className="absolute inset-0 bg-grid-pattern opacity-60 pointer-events-none [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

      <div className="relative mx-auto max-w-5xl px-6 sm:px-8">

        {/* Hero Section */}
        <section className="pt-20 sm:pt-28 pb-16">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-12">
            
            {/* Hero Left Content */}
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-6 transition-all duration-200"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  boxShadow: '0 0 15px -3px rgba(255,255,255,0.03)'
                }}>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-mono font-medium text-zinc-300">
                  GenAI Mobile Threat Defense Engine
                </span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white mb-5 leading-[1.08]">
                Dissect, analyze, and neutralise malicious APKs.
              </h1>

              <p className="text-base sm:text-lg text-zinc-400 leading-relaxed max-w-xl font-normal">
                Deterministic bytecode heuristics combined with Generative AI behavioral reconstruction. Full mobile threat intelligence in <span className="text-zinc-200 font-medium">under 15 seconds</span>.
              </p>
            </div>

            {/* Hero Right Visual: Tech Reticle Accent */}
            <div className="hidden lg:flex flex-col items-center justify-center p-6 rounded-2xl relative"
              style={{
                background: 'linear-gradient(145deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))',
                border: '1px solid rgba(255,255,255,0.08)',
                boxShadow: '0 20px 40px -15px rgba(0,0,0,0.8)'
              }}>
              <div className="relative w-48 h-48 flex items-center justify-center">
                {/* Concentric scan radar circles */}
                <div className="absolute inset-0 rounded-full border border-white/5 animate-[spin_20s_linear_infinite]" />
                <div className="absolute inset-4 rounded-full border border-dashed border-sky-500/20 animate-[spin_15s_linear_infinite_reverse]" />
                <div className="absolute inset-10 rounded-full border border-white/10" />
                <div className="absolute inset-16 rounded-full border border-sky-400/30 flex items-center justify-center bg-sky-500/5">
                  <ShieldCheck className="h-8 w-8 text-sky-400" />
                </div>
                {/* Threat indicators */}
                <span className="absolute top-2 right-4 h-2 w-2 rounded-full bg-red-400 shadow-[0_0_8px_#ef4444]" />
                <span className="absolute bottom-4 left-6 h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
                <span className="absolute top-1/2 left-2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-amber-400 shadow-[0_0_6px_#f59e0b]" />
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5 text-sky-400 animate-pulse" />
                <span className="font-mono text-xs text-zinc-400 uppercase tracking-wider">Edge Threat Interceptor</span>
              </div>
            </div>

          </div>
        </section>

        {/* Stats Strip */}
        <section className="mb-14">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-8 px-8 rounded-xl"
            style={{
              background: '#0d0d10',
              border: '1px solid rgba(255,255,255,0.07)',
            }}>
            <Stat label="Total Scans"   value={stats?.total_scans?.toLocaleString()} sub="Processed APKs" />
            <Stat label="Threats Found" value={stats?.malicious_found?.toLocaleString()} sub="High/Critical hits" />
            <Stat label="Avg Scan Time" value={stats?.avg_duration_ms ? `${(stats.avg_duration_ms/1000).toFixed(1)}s` : null} sub="Full 8-stage pipeline" />
            <Stat label="Unique Hashes" value={stats?.unique_hashes?.toLocaleString()} sub="Cached fingerprints" />
          </div>
        </section>

        {/* Dropzone Container */}
        <section className="mb-20">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Package Upload
            </span>
            <span className="text-xs font-mono text-zinc-500">
              REST Endpoint: /api/scan
            </span>
          </div>
          <Dropzone />
        </section>

        {/* Analysis Pipeline Features */}
        <section className="mb-20">
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white tracking-tight">
              Multi-Stage Inspection Pipeline
            </h2>
            <p className="text-sm text-zinc-400 mt-1">
              Every submitted Android application package undergoes eight synchronized verification stages.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FEATURES.map(({ icon: Icon, label, desc, tag }) => (
              <div key={label} className="flex flex-col gap-3 p-6 rounded-xl transition-all duration-200 group"
                style={{
                  background: '#0d0d10',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'}>
                <div className="flex items-center justify-between">
                  <div className="h-9 w-9 rounded-lg flex items-center justify-center"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <Icon className="h-4.5 w-4.5 text-zinc-300 group-hover:text-white transition-colors" />
                  </div>
                  <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded text-zinc-400"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    {tag}
                  </span>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white tracking-tight mb-1.5">
                    {label}
                  </h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Recent Scans */}
        {history?.scans?.length > 0 && (
          <section className="mb-16">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-semibold text-white tracking-tight">
                  Recent Threat Telemetry
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Latest APK analyses processed by the edge cluster
                </p>
              </div>
              <Link to="/history"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-400 hover:text-white transition-colors group">
                <span>View all scans</span>
                <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            <div className="rounded-xl overflow-hidden divide-y divide-white/[0.04]"
              style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.07)' }}>
              {history.scans.slice(0, 5).map((scan) => (
                <Link key={scan.scan_id} to={`/scan/${scan.scan_id}`}
                  className="flex items-center justify-between px-6 py-4.5 transition-colors group hover:bg-white/[0.02]">
                  <div className="flex items-center gap-5 min-w-0">
                    <div className="w-10 text-center font-mono font-bold text-lg text-white tabular-nums flex-shrink-0">
                      {scan.final_score}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate group-hover:text-sky-300 transition-colors">
                        {scan.original_filename}
                      </p>
                      <p className="text-xs text-zinc-500 mt-0.5 font-mono">
                        {scan.fraud_category ?? 'general'} · {new Date(scan.created_at).toLocaleDateString()} {new Date(scan.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                  <SeverityBadge label={scan.severity} size="md" />
                </Link>
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  )
}



