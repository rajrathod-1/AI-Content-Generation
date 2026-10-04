import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowUp, Check, Copy, RotateCcw, SquarePen } from 'lucide-react'
import { api, type BackendState, type GenerateResponse, type Source } from '../lib/api'

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
  const nextId = useRef(0)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, pending])

  async function ask(query: string) {
    setPending(true)
    try {
      const res = await api.generate(query)
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

  return (
    <div className="flex h-[calc(100dvh-3.5rem)] flex-col">
      <div className="border-b border-line">
        <div className="mx-auto flex h-12 max-w-3xl items-center justify-between px-4">
          <h1 className="text-sm font-medium">Assistant</h1>
          <button
            type="button"
            onClick={() => setMessages([])}
            disabled={!messages.length || pending}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-muted hover:text-fg disabled:pointer-events-none disabled:opacity-40"
          >
            <SquarePen className="size-4" aria-hidden="true" /> New chat
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-8">
          {messages.length === 0 && !pending ? (
            <div className="py-12 sm:py-20">
              <p className="eyebrow">Ask anything current</p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
                I search the web and a vector index, then answer with sources.
              </h2>
              <ul className="mt-10 grid gap-2 sm:grid-cols-2">
                {SUGGESTIONS.map((s) => (
                  <li key={s}>
                    <button
                      type="button"
                      onClick={() => send(s)}
                      className="panel h-full w-full p-4 text-left text-sm text-muted transition-colors hover:border-accent/40 hover:text-fg"
                    >
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <ol className="space-y-8" aria-label="Conversation">
              {messages.map((m) => (
                <li key={m.id} className="msg-in">
                  {m.role === 'user' && (
                    <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-raised px-4 py-2.5 whitespace-pre-wrap">
                      {m.text}
                    </div>
                  )}
                  {m.role === 'assistant' && <Answer text={m.text} res={m.res} />}
                  {m.role === 'error' && (
                    <div role="alert" className="rounded-xl border border-danger/30 bg-danger/5 p-4 text-sm">
                      <p>{m.text}</p>
                      <button type="button" onClick={() => retry(m)} disabled={pending} className="btn-ghost mt-3 py-1.5">
                        <RotateCcw className="size-3.5" aria-hidden="true" /> Retry
                      </button>
                    </div>
                  )}
                </li>
              ))}
              {pending && (
                <li role="status" aria-live="polite" className="space-y-3">
                  <p className="font-mono text-xs text-muted">Searching the web and the vector index…</p>
                  <div className="skeleton h-3 w-11/12 rounded" />
                  <div className="skeleton h-3 w-4/5 rounded" />
                  <div className="skeleton h-3 w-3/5 rounded" />
                </li>
              )}
            </ol>
          )}
          <div ref={endRef} />
        </div>
      </div>

      <form onSubmit={onSubmit} className="border-t border-line bg-canvas">
        <div className="mx-auto max-w-3xl px-4 py-4">
          {backend === 'offline' && (
            <p className="mb-3 text-sm text-warn">
              The backend isn't responding right now. It may be asleep on its free tier, so give it a minute.
            </p>
          )}
          <div className="flex items-end gap-2 rounded-xl border border-line bg-surface p-2 transition-colors focus-within:border-accent/50">
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
              className="field-sizing-content max-h-40 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 outline-none placeholder:text-muted focus-visible:outline-none"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={!input.trim() || pending}
              className="grid size-10 shrink-0 place-items-center rounded-lg bg-accent text-canvas transition-colors hover:bg-accent-strong disabled:bg-raised disabled:text-muted"
            >
              <ArrowUp className="size-5" aria-hidden="true" />
            </button>
          </div>
          <p className="mt-2 flex justify-between gap-4 text-xs text-muted">
            <span>Enter to send, Shift+Enter for a new line. Answers can be wrong, so check the sources.</span>
            {input.length > MAX_CHARS * 0.9 && <span className="font-mono">{input.length}/{MAX_CHARS}</span>}
          </p>
        </div>
      </form>
    </div>
  )
}

function Answer({ text, res }: { text: string; res: GenerateResponse }) {
  const [copied, setCopied] = useState(false)
  const meta = [
    `${Math.round(res.response_time_ms).toLocaleString()} ms`,
    res.cached && 'cached',
    res.sources.length ? `${res.sources.length} sources` : res.used_rag === false && 'no retrieval',
    res.model,
  ].filter(Boolean)

  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div>
      <div className="prose-chat">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{ a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noreferrer" /> }}
        >
          {text}
        </Markdown>
      </div>

      {res.sources.length > 0 && (
        <ol className="mt-5 grid gap-2 sm:grid-cols-2" aria-label="Sources">
          {res.sources.map((s, i) => (
            <SourceCard key={i} source={s} n={i + 1} />
          ))}
        </ol>
      )}

      <div className="mt-4 flex items-center gap-3 font-mono text-xs text-muted">
        <span>{meta.join(' · ')}</span>
        <button type="button" onClick={copy} className="ml-auto inline-flex items-center gap-1 hover:text-fg">
          {copied ? <Check className="size-3.5" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  )
}

function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

function SourceCard({ source, n }: { source: Source; n: number }) {
  const host = hostname(source.url)
  const match = Math.round(Math.min(Math.max(source.score, 0), 1) * 100)
  const body = (
    <>
      <div className="flex items-center gap-2 font-mono text-xs text-muted">
        <span className="text-accent">[{n}]</span>
        <span className="truncate">{host ?? 'knowledge base'}</span>
        <span className="ml-auto shrink-0">{source.source_type === 'web' ? 'web' : 'index'}</span>
      </div>
      <p className="mt-2 line-clamp-2 text-sm">{source.title || 'Untitled source'}</p>
      <div className="mt-3 flex items-center gap-2 font-mono text-xs text-muted">
        <span className="h-1 flex-1 overflow-hidden rounded-full bg-raised">
          <span className="block h-full rounded-full bg-accent/70" style={{ width: `${match}%` }} />
        </span>
        {match}% match
      </div>
    </>
  )
  return (
    <li>
      {host ? (
        <a href={source.url} target="_blank" rel="noreferrer" className="panel block h-full p-3 transition-colors hover:border-accent/40">
          {body}
        </a>
      ) : (
        <div className="panel h-full p-3">{body}</div>
      )}
    </li>
  )
}
