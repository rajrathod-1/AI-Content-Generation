import { Link, NavLink } from 'react-router'
import type { BackendState } from '../api'

const NAV = [
  { to: '/', label: 'Home' },
  { to: '/chat', label: 'Assistant' },
  { to: '/metrics', label: 'Metrics' },
]

const STATUS: Record<BackendState, { label: string; dot: string }> = {
  checking: { label: 'Waking API', dot: 'bg-warn animate-pulse' },
  online: { label: 'API online', dot: 'bg-accent' },
  offline: { label: 'API offline', dot: 'bg-danger' },
}

export function Logo() {
  return (
    <svg viewBox="0 0 32 32" className="size-7" aria-hidden="true">
      <rect width="32" height="32" rx="7" className="fill-raised" />
      <path d="M16 16 8 9M16 16l9-5M16 16l-6 9M16 16l8 7" className="stroke-accent/60" strokeWidth="1.5" />
      <g className="fill-muted">
        <circle cx="8" cy="9" r="2" />
        <circle cx="25" cy="11" r="2" />
        <circle cx="10" cy="25" r="2" />
        <circle cx="24" cy="23" r="2" />
      </g>
      <circle cx="16" cy="16" r="3.5" className="fill-accent" />
    </svg>
  )
}

export function Header({ backend }: { backend: BackendState }) {
  const status = STATUS[backend]
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-line bg-canvas/75 backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-6xl items-center gap-3 px-4 sm:gap-6 sm:px-6">
        <Link to="/" className="flex items-center gap-2.5 font-medium">
          <Logo />
          <span className="hidden sm:inline">RAG Generator</span>
        </Link>
        <nav aria-label="Main" className="ml-auto flex items-center gap-1 text-sm">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                `rounded-md px-2.5 py-1.5 transition-colors ${isActive ? 'bg-white/[0.06] text-fg' : 'text-muted hover:text-fg'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <span
          className="inline-flex items-center gap-2 rounded-full border border-line px-2.5 py-1 font-mono text-xs text-muted"
          title={status.label}
        >
          <span className={`size-1.5 rounded-full ${status.dot}`} aria-hidden="true" />
          <span className="sr-only sm:not-sr-only">{status.label}</span>
        </span>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>Built by Raj Rathod with Flask, FAISS, OpenAI, React and Three.js.</p>
        <div className="flex gap-5">
          <a href="https://github.com/rajrathod-1/AI-Content-Generation" target="_blank" rel="noreferrer" className="hover:text-fg">
            GitHub
          </a>
          <a href="https://www.linkedin.com/in/raj-rathod1/" target="_blank" rel="noreferrer" className="hover:text-fg">
            LinkedIn
          </a>
        </div>
      </div>
    </footer>
  )
}
