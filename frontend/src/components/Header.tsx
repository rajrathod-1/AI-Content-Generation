import { Link, NavLink } from 'react-router'
import type { BackendState } from '../api'
import Magnetic from './Magnetic'

const NAV = [
  { to: '/', label: 'Story' },
  { to: '/chat', label: 'Ask' },
  { to: '/metrics', label: 'Metrics' },
]

const STATUS: Record<BackendState, { label: string; dot: string }> = {
  checking: { label: 'Waking', dot: 'bg-warn animate-pulse' },
  online: { label: 'Online', dot: 'bg-ok' },
  offline: { label: 'Offline', dot: 'bg-signal' },
}

export default function Header({ backend }: { backend: BackendState }) {
  const status = STATUS[backend]
  return (
    <header className="gutter fixed inset-x-0 top-0 z-50 flex h-20 items-center gap-6 bg-linear-to-b from-ink from-35% via-ink/70 to-transparent pb-3">
      <Link to="/" className="text-lg font-light tracking-tight whitespace-nowrap">
        <span className="italic">RAG</span>
        <span className="hidden sm:inline"> Generator</span>
        <sup className="cite">[1]</sup>
      </Link>
      <nav aria-label="Main" className="ml-auto flex items-center sm:gap-3">
        {NAV.map((item) => (
          <Magnetic key={item.to}>
            <NavLink
              to={item.to}
              end
              className={({ isActive }) =>
                `group px-1 py-2 font-mono text-[0.6875rem] tracking-widest uppercase sm:px-1.5 sm:tracking-[0.16em] transition-colors ${isActive ? 'text-paper' : 'text-dim hover:text-paper'}`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={isActive ? 'text-signal' : 'opacity-0 group-hover:opacity-100'}>[</span>
                  {item.label}
                  <span className={isActive ? 'text-signal' : 'opacity-0 group-hover:opacity-100'}>]</span>
                </>
              )}
            </NavLink>
          </Magnetic>
        ))}
      </nav>
      <span className="flex items-center gap-2 font-mono text-[0.6875rem] tracking-[0.16em] text-dim uppercase" title={`API ${status.label}`}>
        <span className={`size-1.5 rounded-full ${status.dot}`} aria-hidden="true" />
        <span className="sr-only">API </span>
        <span className="sr-only sm:not-sr-only">{status.label}</span>
      </span>
    </header>
  )
}
