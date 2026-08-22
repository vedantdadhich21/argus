import { Link, useLocation } from 'react-router-dom'
import { History, Code2, Home, Shield } from 'lucide-react'

const links = [
  { to: '/',        label: 'Analyzer', icon: Home },
  { to: '/history', label: 'Telemetry', icon: History },
  { to: '/docs',    label: 'API Reference', icon: Code2 },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav style={{ background: 'rgba(8,8,10,0.85)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 sm:px-8 h-14">

        {/* Logo — wordmark with subtle security emblem */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="h-6 w-6 rounded flex items-center justify-center"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Shield className="h-3.5 w-3.5 text-zinc-200 group-hover:text-white transition-colors" />
          </div>
          <span className="text-sm font-semibold tracking-tight text-white font-sans">Argus</span>
          <span className="text-[11px] font-mono font-medium px-1.5 py-0.5 rounded text-zinc-400"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
            Mobile MTD
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map(({ to, label }) => {
            const active = pathname === to || (to !== '/' && pathname.startsWith(to))
            return (
              <Link
                key={to}
                to={to}
                className="px-3.5 py-1.5 text-xs font-medium rounded-md transition-all duration-150"
                style={{
                  color: active ? '#fafafa' : '#a1a1aa',
                  background: active ? 'rgba(255,255,255,0.08)' : 'transparent',
                }}
                onMouseEnter={e => { if (!active) { e.currentTarget.style.color = '#fafafa'; e.currentTarget.style.background = 'rgba(255,255,255,0.03)' } }}
                onMouseLeave={e => { if (!active) { e.currentTarget.style.color = '#a1a1aa'; e.currentTarget.style.background = 'transparent' } }}
              >
                {label}
              </Link>
            )
          })}
        </div>

        {/* Operational Status badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full"
          style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)' }}>
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"
            style={{ boxShadow: '0 0 6px rgba(52,211,153,0.9)', animation: 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite' }} />
          <span className="text-[11px] font-mono font-medium text-emerald-400">Cluster Online</span>
        </div>

      </div>
    </nav>
  )
}

