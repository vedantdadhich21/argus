import { Link, useLocation } from 'react-router-dom'
import { Shield, History, Code2, Home } from 'lucide-react'

const links = [
  { to: '/',        label: 'Home',     icon: Home },
  { to: '/history', label: 'History',  icon: History },
  { to: '/docs',    label: 'API Docs', icon: Code2 },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-white group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center shadow-lg shadow-red-500/20 group-hover:shadow-red-500/40 transition-shadow">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <span className="tracking-tight">
            <span className="text-white">Argus</span>
          </span>
        </Link>

        {/* Links */}
        <div className="flex items-center gap-1">
          {links.map(({ to, label, icon: Icon }) => {
            const active = pathname === to
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </Link>
            )
          })}
        </div>

        {/* Badge */}
        <div className="flex items-center gap-1.5 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
          <span className="text-xs font-medium text-green-400">Live</span>
        </div>
      </div>
    </nav>
  )
}
