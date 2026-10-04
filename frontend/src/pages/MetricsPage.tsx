import { useCallback, useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api, type Metrics } from '../api'

const pct = (ratio: number) => `${(ratio * 100).toFixed(1)}%`
const ms = (v: number) => `${Math.round(v).toLocaleString()} ms`

const TONE = {
  ok: { fill: 'bg-accent', track: 'bg-accent/15', text: 'text-accent' },
  warn: { fill: 'bg-warn', track: 'bg-warn/15', text: 'text-warn' },
  danger: { fill: 'bg-danger', track: 'bg-danger/15', text: 'text-danger' },
}
const usageTone = (v: number) => (v >= 90 ? 'danger' : v >= 70 ? 'warn' : 'ok')
const USAGE_LABEL = { ok: 'Normal', warn: 'Elevated', danger: 'Critical' }
const healthTone = (score: number) => (score < 60 ? 'danger' : score < 85 ? 'warn' : 'ok')
const HEALTH_LABEL = { ok: 'Good', warn: 'Degraded', danger: 'Poor' }

export default function MetricsPage() {
  const [data, setData] = useState<Metrics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updated, setUpdated] = useState<Date | null>(null)

  const load = useCallback(() => {
    api.metrics().then(
      (m) => {
        setData(m)
        setError(null)
        setUpdated(new Date())
      },
      (e: Error) => setError(e.message),
    )
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 30_000)
    return () => clearInterval(id)
  }, [load])

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Live metrics</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">System health</h1>
          <p className="mt-2 text-sm text-muted">
            Counted since the server last started. Refreshes every 30 seconds.
            {updated && ` Last updated ${updated.toLocaleTimeString()}.`}
          </p>
        </div>
        <button type="button" onClick={load} className="btn-ghost">
          <RefreshCw className="size-4" aria-hidden="true" /> Refresh
        </button>
      </div>

      {error && (
        <div role="alert" className="mt-8 rounded-xl border border-danger/30 bg-danger/5 p-4 text-sm">
          {error}
        </div>
      )}

      {!data && !error && (
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-busy="true" aria-label="Loading metrics">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="skeleton h-28 rounded-xl" />
          ))}
        </div>
      )}

      {data && <Dashboard m={data} />}
    </div>
  )
}

function Dashboard({ m }: { m: Metrics }) {
  const health = healthTone(m.health_score)
  // JSON keys arrive alphabetised ('50-100ms' after '200-500ms'); order by the band's lower bound
  const buckets = Object.entries(m.response_time_distribution).sort(([a], [b]) => parseInt(a) - parseInt(b))
  const maxBucket = Math.max(1, ...buckets.map(([, n]) => n))
  const endpoints = Object.entries(m.service_breakdown)
  const sys = m.system_metrics
  const meters = [
    { label: 'CPU', value: sys.cpu_percent },
    { label: 'Memory', value: sys.memory_percent, note: sys.memory_used_mb ? `${Math.round(sys.memory_used_mb).toLocaleString()} MB` : null },
    { label: 'Disk', value: sys.disk_usage_percent },
  ]

  return (
    <>
      <section aria-label="Overview" className="mt-10 grid gap-px overflow-hidden rounded-xl border border-line bg-line lg:grid-cols-[1.3fr_2fr]">
        <div className="bg-canvas p-6 sm:p-8">
          <p className="text-sm text-muted">Total requests</p>
          <p className="mt-2 text-6xl font-semibold tracking-tight">{m.total_requests.toLocaleString()}</p>
          <p className="mt-4 text-sm text-muted">
            Up {m.uptime_human} · health {Math.round(m.health_score)}/100{' '}
            <span className={TONE[health].text}>({HEALTH_LABEL[health]})</span>
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-px bg-line">
          <Stat label="Success rate" value={m.total_requests ? pct(m.success_rate) : '—'} />
          <Stat label="Average latency" value={m.total_requests ? ms(m.average_response_time_ms) : '—'} />
          <Stat label="Cache hit rate" value={m.total_requests ? pct(m.cache_hit_rate) : '—'} />
          <Stat label="Requests per minute" value={m.requests_per_minute.toFixed(1)} hint="last 5 minutes" />
        </dl>
      </section>

      {m.total_requests === 0 && (
        <p className="mt-6 text-sm text-muted">
          No requests yet since the server started. Ask the assistant something and the numbers will fill in.
        </p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="panel p-6" aria-labelledby="latency-h">
          <h2 id="latency-h" className="font-medium">Response time distribution</h2>
          <p className="mt-1 text-sm text-muted">Requests per latency band</p>
          <ul className="mt-6 space-y-3">
            {buckets.map(([band, n]) => (
              <li key={band} className="group grid grid-cols-[5.5rem_1fr_3rem] items-center gap-3 text-sm" title={`${band}: ${n} requests`}>
                <span className="font-mono text-xs text-muted">{band}</span>
                <span className="h-5 rounded-r bg-white/[0.03]">
                  <span
                    className="block h-full rounded-r bg-accent/70 transition-colors group-hover:bg-accent"
                    style={{ width: `${(n / maxBucket) * 100}%`, minWidth: n ? 4 : 0 }}
                  />
                </span>
                <span className="text-right tabular-nums">{n.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel p-6" aria-labelledby="system-h">
          <h2 id="system-h" className="font-medium">Server resources</h2>
          <p className="mt-1 text-sm text-muted">Sampled every minute on the backend host</p>
          <ul className="mt-6 space-y-5">
            {meters.map(({ label, value, note }) => {
              if (value == null) return null
              const tone = usageTone(value)
              const s = TONE[tone]
              return (
                <li key={label}>
                  <div className="flex items-baseline justify-between text-sm">
                    <span>
                      {label} {note && <span className="text-muted">· {note}</span>}
                    </span>
                    <span className="tabular-nums">
                      {value.toFixed(1)}% <span className={`text-xs ${s.text}`}>{USAGE_LABEL[tone]}</span>
                    </span>
                  </div>
                  <div
                    className={`mt-2 h-2 rounded-full ${s.track}`}
                    role="meter"
                    aria-label={label}
                    aria-valuenow={Math.round(value)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div className={`h-full rounded-full ${s.fill}`} style={{ width: `${Math.min(value, 100)}%` }} />
                  </div>
                </li>
              )
            })}
            {meters.every((x) => x.value == null) && <li className="text-sm text-muted">No samples yet.</li>}
          </ul>
        </section>
      </div>

      {endpoints.length > 0 && (
        <section className="panel mt-6 overflow-x-auto" aria-labelledby="endpoints-h">
          <h2 id="endpoints-h" className="px-6 pt-6 font-medium">By endpoint</h2>
          <table className="mt-4 w-full min-w-md text-sm">
            <thead className="border-y border-line font-mono text-xs text-muted">
              <tr>
                <th scope="col" className="px-6 py-3 text-left font-normal">Endpoint</th>
                <th scope="col" className="px-6 py-3 text-right font-normal">Requests</th>
                <th scope="col" className="px-6 py-3 text-right font-normal">Success</th>
                <th scope="col" className="px-6 py-3 text-right font-normal">Avg latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {endpoints.map(([name, e]) => (
                <tr key={name}>
                  <th scope="row" className="px-6 py-3 text-left font-mono font-normal">/api/{name}</th>
                  <td className="px-6 py-3 text-right">{e.total_requests.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">{pct(e.success_rate)}</td>
                  <td className="px-6 py-3 text-right">{ms(e.average_response_time_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  )
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="bg-canvas p-6">
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="mt-2 text-2xl font-semibold tracking-tight">{value}</dd>
      {hint && <dd className="mt-1 text-xs text-muted">{hint}</dd>}
    </div>
  )
}
