import { useCallback, useEffect, useState } from 'react'
import { api, type Metrics } from '../api'
import Split from '../components/Split'

const pct = (ratio: number) => `${(ratio * 100).toFixed(1)}%`
const ms = (v: number) => `${Math.round(v).toLocaleString()} ms`

// Status colours always ship with a text label
const TONE = {
  ok: { fill: 'bg-paper/80', text: 'text-ok' },
  warn: { fill: 'bg-warn', text: 'text-warn' },
  danger: { fill: 'bg-signal', text: 'text-signal' },
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
    <div className="gutter page-in is-in min-h-svh pt-32 pb-24">
      <div className="flex flex-wrap items-end justify-between gap-6 border-b border-rule pb-8">
        <div>
          <p className="eyebrow">Instrument panel</p>
          <Split as="h1" text="How the engine is *holding up.*" className="headline mt-5 max-w-4xl" />
        </div>
        <div className="ml-auto text-right font-mono text-[0.6875rem] text-dim">
          <p>Counted since the server last started · refreshes every 30 s</p>
          {updated && <p className="mt-1">Updated {updated.toLocaleTimeString()}</p>}
          <button type="button" onClick={load} className="bracket-btn mt-4 text-paper">
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="mt-10 border-l border-signal pl-5">
          <p className="font-mono text-xs tracking-wide text-signal uppercase">Unavailable</p>
          <p className="mt-2 text-lg font-light">{error}</p>
        </div>
      )}

      {!data && !error && (
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4" aria-busy="true" aria-label="Loading metrics">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="skeleton h-24" />
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
  const none = m.total_requests === 0

  return (
    <>
      <section aria-label="Overview" className="grid gap-10 border-b border-rule py-12 lg:grid-cols-[1.2fr_2fr]">
        <div>
          <p className="eyebrow">Requests answered</p>
          <p className="mt-3 text-[clamp(5rem,13vw,11rem)] leading-[0.85] font-extralight tracking-tighter">{m.total_requests.toLocaleString()}</p>
          <p className="mt-6 font-mono text-xs text-dim">
            Up {m.uptime_human} · health {Math.round(m.health_score)}/100 <span className={TONE[health].text}>{HEALTH_LABEL[health]}</span>
          </p>
        </div>
        <dl className="grid grid-cols-2 content-end gap-x-10 gap-y-8">
          <Stat label="Success rate" value={none ? '—' : pct(m.success_rate)} />
          <Stat label="Average latency" value={none ? '—' : ms(m.average_response_time_ms)} />
          <Stat label="Cache hit rate" value={none ? '—' : pct(m.cache_hit_rate)} />
          <Stat label="Requests / minute" value={m.requests_per_minute.toFixed(1)} hint="last 5 minutes" />
        </dl>
      </section>

      {none && <p className="mt-8 text-lg font-light text-dim">No requests since the server started. Ask the assistant something and these fill in.</p>}

      <div className="grid gap-16 py-12 lg:grid-cols-2">
        <section aria-labelledby="latency-h">
          <h2 id="latency-h" className="text-2xl font-light">
            Response time
          </h2>
          <p className="mt-1 font-mono text-[0.6875rem] text-dim">Requests per latency band</p>
          <ul className="mt-8 space-y-4">
            {buckets.map(([band, n]) => (
              <li key={band} className="group grid grid-cols-[5.5rem_1fr_3rem] items-center gap-4" title={`${band}: ${n} requests`}>
                <span className="font-mono text-xs text-dim">{band}</span>
                <span className="h-px bg-rule">
                  <span className="block h-[3px] -translate-y-px bg-paper/70 transition-colors group-hover:bg-signal" style={{ width: `${(n / maxBucket) * 100}%` }} />
                </span>
                <span className="text-right font-mono text-sm tabular-nums">{n.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="system-h">
          <h2 id="system-h" className="text-2xl font-light">
            Server resources
          </h2>
          <p className="mt-1 font-mono text-[0.6875rem] text-dim">Sampled every minute on the backend host</p>
          <ul className="mt-8 space-y-6">
            {meters.map(({ label, value, note }) => {
              if (value == null) return null
              const tone = usageTone(value)
              return (
                <li key={label}>
                  <div className="flex items-baseline justify-between font-mono text-xs">
                    <span>
                      {label} {note && <span className="text-dim">· {note}</span>}
                    </span>
                    <span className="tabular-nums">
                      {value.toFixed(1)}% <span className={TONE[tone].text}>{USAGE_LABEL[tone]}</span>
                    </span>
                  </div>
                  <div className="mt-3 h-px bg-rule" role="meter" aria-label={label} aria-valuenow={Math.round(value)} aria-valuemin={0} aria-valuemax={100}>
                    <div className={`h-[3px] -translate-y-px ${TONE[tone].fill}`} style={{ width: `${Math.min(value, 100)}%` }} />
                  </div>
                </li>
              )
            })}
            {meters.every((x) => x.value == null) && <li className="font-mono text-xs text-dim">No samples yet.</li>}
          </ul>
        </section>
      </div>

      {endpoints.length > 0 && (
        <section className="overflow-x-auto border-t border-rule pt-12" aria-labelledby="endpoints-h">
          <h2 id="endpoints-h" className="text-2xl font-light">
            By endpoint
          </h2>
          <table className="mt-6 w-full min-w-md font-mono text-sm">
            <thead className="text-[0.6875rem] tracking-[0.14em] text-dim uppercase">
              <tr className="border-b border-rule">
                <th scope="col" className="py-3 text-left font-normal">Endpoint</th>
                <th scope="col" className="py-3 text-right font-normal">Requests</th>
                <th scope="col" className="py-3 text-right font-normal">Success</th>
                <th scope="col" className="py-3 text-right font-normal">Avg latency</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {endpoints.map(([name, e]) => (
                <tr key={name} className="border-b border-rule">
                  <th scope="row" className="py-3 text-left font-normal">
                    <span className="text-signal">/api/</span>
                    {name}
                  </th>
                  <td className="py-3 text-right">{e.total_requests.toLocaleString()}</td>
                  <td className="py-3 text-right">{pct(e.success_rate)}</td>
                  <td className="py-3 text-right">{ms(e.average_response_time_ms)}</td>
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
    <div className="border-t border-rule pt-4">
      <dt className="eyebrow">{label}</dt>
      <dd className="mt-3 text-4xl font-light tracking-tight">{value}</dd>
      {hint && <dd className="mt-1 font-mono text-[0.6875rem] text-dim">{hint}</dd>}
    </div>
  )
}
