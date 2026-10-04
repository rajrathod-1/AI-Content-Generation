import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from 'react'
import { useSearchParams } from 'react-router'
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, type BackendState, type GenerateResponse, type Source } from '../api'
import KineticTitle from '../components/KineticTitle'
import Magnetic from '../components/Magnetic'
import { world } from '../world/state'

type Message =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'assistant'; text: string; res: GenerateResponse }
  | { id: number; role: 'error'; text: string; query: string }

const MAX_CHARS = 2000

const SUGGESTIONS = [
  'What are the biggest AI announcements this month?',
  'How does FAISS search millions of vectors quickly?',
  'When should I use RAG instead of fine-tuning?',
  'Summarize the latest Python release notes.',
]

export default function ChatPage({ backend }: { backend: BackendState }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(false)
  const [params, setParams] = useSearchParams()
  const nextId = useRef(0)
  const endRef = useRef<HTMLDivElement>(null)
  const askedFromUrl = useRef(false)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, pending])

  // The world leans in while we wait
  useEffect(() => {
    world.thinking = pending
  }, [pending])
  useEffect(
    () => () => {
      world.thinking = false
    },
    [],
  )

  async function ask(query: string) {
    setPending(true)
    try {
      const res = await api.generate(query)
      world.pulseAt = performance.now()
      setMessages((m) => [...m, { id: nextId.current++, role: 'assistant', text: res.content, res }])
    } catch (e) {
      const text = e instanceof Error ? e.message : 'Something went wrong.'
      setMessages((m) => [...m, { id: nextId.current++, role: 'error', text, query }])
    } finally {
      setPending(false)
    }
  }

  function send(text: string) {
    const query = text.trim()
    if (!query || pending) return
    setInput('')
    setMessages((m) => [...m, { id: nextId.current++, role: 'user', text: query }])
    ask(query)
  }

  // Arriving from the home page's last chapter with ?q=
  useEffect(() => {
    const q = params.get('q')
    if (!q || askedFromUrl.current) return
    askedFromUrl.current = true
    setParams({}, { replace: true })
    send(q)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function retry(failed: Extract<Message, { role: 'error' }>) {
    setMessages((m) => m.filter((msg) => msg.id !== failed.id))
    ask(failed.query)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    send(input)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send(input)
    }
  }

  let questionNo = 0
  return (
    <div className="page-in is-in min-h-svh pt-28 pb-56">
      <div className="gutter">
        <div className="max-w-[44rem] lg:ml-[6vw]">
          <div className="flex items-baseline justify-between border-b border-rule pb-4">
            <h1 className="eyebrow">Inquiry</h1>
            <button type="button" onClick={() => setMessages([])} disabled={!messages.length || pending} className="bracket-btn text-dim disabled:opacity-30">
              New inquiry
            </button>
          </div>

          {messages.length === 0 && !pending ? (
            <div className="pt-16 sm:pt-24">
              <KineticTitle lines={['What do you', 'want to know?']} className="headline" />
              <ol className="mt-14 border-t border-rule">
                {SUGGESTIONS.map((s, i) => (
                  <li key={s} className="border-b border-rule">
                    <button
                      type="button"
                      onClick={() => send(s)}
                      className="group flex w-full items-baseline gap-6 py-4 text-left text-lg font-light text-dim transition-colors hover:text-paper"
                    >
                      <span className="font-mono text-xs text-signal">{String(i + 1).padStart(2, '0')}</span>
                      <span className="transition-transform duration-500 ease-out-expo group-hover:translate-x-2">{s}</span>
                    </button>
                  </li>
                ))}
              </ol>
            </div>
          ) : (
            <ol className="space-y-16 pt-14" aria-label="Conversation">
              {messages.map((m) => (
                <li key={m.id} className="page-in">
                  {m.role === 'user' && (
                    <div>
                      <p className="font-mono text-xs text-signal">Q.{String(++questionNo).padStart(2, '0')}</p>
                      <h2 className="mt-3 text-3xl leading-tight font-light tracking-tight whitespace-pre-wrap sm:text-4xl">{m.text}</h2>
                    </div>
                  )}
                  {m.role === 'assistant' && <Answer text={m.text} res={m.res} />}
                  {m.role === 'error' && (
                    <div role="alert" className="border-l border-signal pl-5">
                      <p className="font-mono text-xs tracking-wide text-signal uppercase">Error</p>
                      <p className="mt-2 text-lg font-light">{m.text}</p>
                      <button type="button" onClick={() => retry(m)} disabled={pending} className="bracket-btn mt-4 text-paper">
                        Retry
                      </button>
                    </div>
                  )}
                </li>
              ))}
              {pending && (
                <li role="status" aria-live="polite">
                  <p className="seek font-mono text-xs text-dim">
                    Retrieving{' '}
                    {[1, 2, 3, 4, 5].map((n) => (
                      <span key={n} style={{ '--i': n } as React.CSSProperties}>
                        [{n}]{' '}
                      </span>
                    ))}
                  </p>
                  <div className="mt-6 space-y-3">
                    <div className="skeleton h-3.5 w-full" />
                    <div className="skeleton h-3.5 w-11/12" />
                    <div className="skeleton h-3.5 w-3/5" />
                  </div>
                </li>
              )}
            </ol>
          )}
          <div ref={endRef} />
        </div>
      </div>

      <form onSubmit={onSubmit} className="gutter fixed inset-x-0 bottom-0 z-40 bg-linear-to-t from-ink via-ink/95 to-transparent pt-16 pb-6">
        <div className="max-w-[44rem] lg:ml-[6vw]">
          {backend === 'offline' && (
            <p className="mb-3 font-mono text-xs text-warn">The backend isn't responding right now. Try again in a moment.</p>
          )}
          <div className="flex items-end gap-4 border-b border-rule transition-colors focus-within:border-paper">
            <label htmlFor="prompt" className="sr-only">
              Ask a question
            </label>
            <textarea
              id="prompt"
              rows={1}
              maxLength={MAX_CHARS}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask a question…"
              className="field-sizing-content max-h-40 min-h-12 flex-1 resize-none bg-transparent py-3 text-xl font-light outline-none placeholder:text-dim/70 focus-visible:outline-none"
            />
            <Magnetic>
              <button type="submit" disabled={!input.trim() || pending} className="bracket-btn mb-4 text-paper disabled:text-dim/50">
                Ask ↵
              </button>
            </Magnetic>
          </div>
          <p className="mt-3 flex justify-between gap-4 font-mono text-[0.6875rem] text-dim">
            <span>Enter to ask · Shift+Enter for a new line · Answers can be wrong, so check the footnotes.</span>
            {input.length > MAX_CHARS * 0.9 && (
              <span>
                {input.length}/{MAX_CHARS}
              </span>
            )}
          </p>
        </div>
      </form>
    </div>
  )
}

/** Turn the model's [n] markers into links the renderer swaps for citation buttons. Skips `arr[1]`-style code. */
const linkCitations = (text: string, max: number) =>
  text.replace(/(?<!\w)\[(\d{1,2})\](?!\()/g, (m, d) => (+d >= 1 && +d <= max ? `[${d}](#cite-${d})` : m))

// Citation hover is shared through context so the Markdown renderers stay stable (no remount, focus survives)
const CiteContext = createContext({ hover: 0, setHover: (_n: number) => {}, id: '' })

function CiteLink({ href = '', children }: { href?: string; children?: ReactNode }) {
  const { hover, setHover, id } = useContext(CiteContext)
  const n = href.startsWith('#cite-') ? Number(href.slice(6)) : 0
  if (!n)
    return (
      <a href={href} target="_blank" rel="noreferrer">
        {children}
      </a>
    )
  return (
    <button
      type="button"
      className="cite-btn"
      aria-label={`Source ${n}`}
      data-on={hover === n}
      onMouseEnter={() => setHover(n)}
      onMouseLeave={() => setHover(0)}
      onFocus={() => setHover(n)}
      onBlur={() => setHover(0)}
      onClick={() => document.getElementById(`src-${id}-${n}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })}
    >
      {n}
    </button>
  )
}

const MARKDOWN_COMPONENTS: Components = { a: CiteLink }

function Answer({ text, res }: { text: string; res: GenerateResponse }) {
  const [hover, setHover] = useState(0)
  const [copied, setCopied] = useState(false)
  const id = useRef(Math.random().toString(36).slice(2, 7)).current

  const meta = [
    `${Math.round(res.response_time_ms).toLocaleString()} ms`,
    res.model,
    res.cached && 'cached',
    !res.sources.length && res.used_rag === false && 'no retrieval',
  ].filter(Boolean)

  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <article>
      <div className="prose-answer">
        <CiteContext value={{ hover, setHover, id }}>
          <Markdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
            {linkCitations(text, res.sources.length)}
          </Markdown>
        </CiteContext>
      </div>

      {res.sources.length > 0 && (
        <section className="mt-10" aria-label="Sources">
          <p className="eyebrow border-b border-rule pb-3">Sources</p>
          <ol>
            {res.sources.map((s, i) => (
              <Footnote key={i} id={`src-${id}-${i + 1}`} n={i + 1} source={s} on={hover === i + 1} onHover={setHover} />
            ))}
          </ol>
        </section>
      )}

      <div className="mt-5 flex items-center gap-4 font-mono text-[0.6875rem] text-dim">
        <span>{meta.join(' · ')}</span>
        <button type="button" onClick={copy} className="bracket-btn ml-auto">
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </article>
  )
}

function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

function Footnote({ id, n, source, on, onHover }: { id: string; n: number; source: Source; on: boolean; onHover: (n: number) => void }) {
  const host = hostname(source.url)
  const match = Math.round(Math.min(Math.max(source.score, 0), 1) * 100)
  const body = (
    <>
      <span className={`font-mono text-xs transition-colors ${on ? 'text-paper' : 'text-signal'}`}>[{n}]</span>
      <span className="min-w-0 flex-1">
        <span className="line-clamp-2 text-base font-light">{source.title || 'Untitled source'}</span>
        <span className="mt-1 flex items-center gap-3 font-mono text-[0.6875rem] text-dim">
          <span className="truncate">{host ?? 'knowledge base'}</span>
          <span>·</span>
          <span>{source.source_type === 'web' ? 'web' : 'index'}</span>
          <span className="ml-auto inline-flex shrink-0 items-center gap-2">
            <span className="h-px w-12 bg-rule">
              <span className="block h-px bg-signal" style={{ width: `${match}%` }} />
            </span>
            {match}%
          </span>
        </span>
      </span>
    </>
  )
  const cls = `flex gap-4 border-b border-rule py-4 transition-colors ${on ? 'bg-signal/10' : ''}`
  return (
    <li id={id} onMouseEnter={() => onHover(n)} onMouseLeave={() => onHover(0)}>
      {host ? (
        <a href={source.url} target="_blank" rel="noreferrer" className={`${cls} hover:bg-white/[0.03]`}>
          {body}
        </a>
      ) : (
        <div className={cls}>{body}</div>
      )}
    </li>
  )
}
