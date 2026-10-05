import { useEffect, useState } from 'react'

const BASE = (() => {
  const raw = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '')
  return raw.endsWith('/api') ? raw : `${raw}/api`
})()

export type Source = {
  title: string
  url: string
  snippet: string
  score: number
  source_type?: 'web' | 'paper' | 'knowledge_base'
  meta?: string | null
}

export type GenerateResponse = {
  content: string
  sources: Source[]
  response_time_ms: number
  cached?: boolean
  used_rag?: boolean
  model?: string
}

export type Metrics = {
  uptime_human: string
  total_requests: number
  successful_requests: number
  failed_requests: number
  success_rate: number
  average_response_time_ms: number
  cache_hit_rate: number
  requests_per_minute: number
  response_time_distribution: Record<string, number>
  service_breakdown: Record<string, { total_requests: number; success_rate: number; average_response_time_ms: number }>
  system_metrics: { cpu_percent?: number; memory_percent?: number; memory_used_mb?: number; disk_usage_percent?: number }
  health_score: number
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 90_000): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, {
      ...init,
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(timeoutMs),
    })
  } catch {
    throw new Error('Could not reach the backend. Check your connection and try again.')
  }
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`)
  return body as T
}

export const api = {
  health: () => request<{ status: string }>('/health', {}, 60_000),
  generate: (query: string) => request<GenerateResponse>('/generate', { method: 'POST', body: JSON.stringify({ query }) }),
  metrics: () => request<Metrics>('/metrics'),
}

export type BackendState = 'checking' | 'online' | 'offline'

export function useBackendStatus(): BackendState {
  const [state, setState] = useState<BackendState>('checking')
  useEffect(() => {
    let alive = true
    const check = () =>
      api.health().then(
        (h) => alive && setState(h.status === 'healthy' ? 'online' : 'offline'),
        () => alive && setState('offline'),
      )
    check()
    const id = setInterval(check, 60_000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [])
  return state
}
