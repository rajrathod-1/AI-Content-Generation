import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import KineticTitle from '../components/KineticTitle'
import Magnetic from '../components/Magnetic'
import Split from '../components/Split'
import { ASK_INPUT, CHAPTERS, STORY_QUESTION, STORY_SOURCES, TOPICS } from '../world/choreography'
import { world } from '../world/state'

const LAST = CHAPTERS.length - 1

export default function HomePage() {
  const [active, setActive] = useState(0)
  const sections = useRef<(HTMLElement | null)[]>([])
  const readoutTopic = useRef<HTMLSpanElement>(null)
  const readoutCount = useRef<HTMLSpanElement>(null)

  // Scroll drives the world: chapter = how many section-heights we've scrolled
  useEffect(() => {
    let raf = 0
    const update = () => {
      raf = 0
      const height = sections.current[0]?.offsetHeight
      if (!height) return
      const c = Math.min(Math.max(window.scrollY / height, 0), LAST)
      world.chapter = c
      setActive(Math.min(LAST, Math.floor(c + 0.35)))
    }
    const schedule = () => {
      raf ||= requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('resize', schedule)
    world.onReadout = (topic, count) => {
      if (readoutTopic.current) readoutTopic.current.textContent = topic
      if (readoutCount.current) readoutCount.current.textContent = count.toLocaleString()
    }
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('scroll', schedule)
      window.removeEventListener('resize', schedule)
      world.onReadout = null
      world.chapter = 0
    }
  }, [])

  const goTo = (i: number) => {
    const height = sections.current[0]?.offsetHeight ?? 0
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.scrollTo({ top: i * height, behavior: reduced ? 'auto' : 'smooth' })
  }

  const chapter = (i: number, children: ReactNode, extra: Record<string, string> = {}) => (
    <section
      ref={(el) => {
        sections.current[i] = el
      }}
      aria-label={`${String(i).padStart(2, '0')} ${CHAPTERS[i].label}`}
      data-active={active === i}
      className={i === LAST ? 'h-svh' : 'h-[150svh]'}
    >
      <div className="sticky top-0 h-svh overflow-hidden" {...extra}>
        {children}
      </div>
    </section>
  )

  return (
    <>
      {/* Labels the world pins to topic clusters and retrieved sources */}
      {TOPICS.map((_, i) => (
        <span
          key={i}
          ref={(el) => {
            world.labels.clusters[i] = el
          }}
          className="anchor"
          data-index={`C·${String(i + 1).padStart(2, '0')}`}
          aria-hidden="true"
        />
      ))}
      {STORY_SOURCES.map((source, i) => (
        <span
          key={source}
          ref={(el) => {
            world.labels.sources[i] = el
          }}
          className="anchor anchor-source"
          aria-hidden="true"
        >
          <span className="text-signal">[{i + 1}]</span> {source}
        </span>
      ))}

      <ChapterIndex active={active} onSelect={goTo} />

      {chapter(
        0,
        <div className="gutter flex h-full flex-col justify-between pt-28 pb-10">
          <p className="eyebrow fade">An answer engine with footnotes</p>
          <div>
            <KineticTitle lines={['Ask the internet', 'anything.']} className="display" />
            <div className="mt-8 flex flex-wrap items-end justify-between gap-6">
              <p className="lede fade max-w-sm" style={{ '--d': 0.6 } as React.CSSProperties}>
                It will always answer. It rarely says where from.
              </p>
              <button type="button" onClick={() => goTo(1)} className="bracket-btn fade text-dim" style={{ '--d': 0.8 } as React.CSSProperties}>
                Follow a question ↓
              </button>
            </div>
          </div>
        </div>,
      )}

      {chapter(
        1,
        <div className="gutter flex h-full flex-col items-end justify-start pt-32 text-right">
          <p className="eyebrow fade">01 — Embed</p>
          <Split as="h2" text="Every passage becomes a *point.*" className="headline mt-5 max-w-3xl" />
          <p className="lede fade mt-8 max-w-md" style={{ '--d': 0.3 } as React.CSSProperties}>
            An embedding model turns each passage into 384 numbers. Passages that mean similar things land close together, so
            meaning becomes distance.
          </p>
          <p className="eyebrow fade mt-6" style={{ '--d': 0.45 } as React.CSSProperties}>
            text-embedding-3-small · 384 dimensions, drawn here in three
          </p>
        </div>,
      )}

      {chapter(
        2,
        <div className="gutter flex h-full flex-col justify-end pb-14">
          <div className="flex flex-wrap items-end justify-between gap-10">
            <div className="max-w-2xl">
              <p className="eyebrow fade">02 — Query</p>
              <Split as="h2" text="Now move the *question.*" className="headline mt-5" />
              <p className="lede fade mt-8 max-w-md" style={{ '--d': 0.3 } as React.CSSProperties}>
                Your question is embedded the same way. Wherever it lands, its nearest neighbours light up. This is the search FAISS
                runs on every request, in miniature.
              </p>
            </div>
            <div className="fade min-w-64 border-t border-rule pt-4 font-mono text-xs" style={{ '--d': 0.5 } as React.CSSProperties}>
              <dl>
                <div className="flex justify-between gap-6 py-1">
                  <dt className="text-dim">nearest topic</dt>
                  <dd ref={readoutTopic} className="text-signal">—</dd>
                </div>
                <div className="flex justify-between gap-6 py-1">
                  <dt className="text-dim">within reach</dt>
                  <dd>
                    <span ref={readoutCount}>0</span> passages
                  </dd>
                </div>
              </dl>
              <p className="mt-3 text-dim [@media(pointer:coarse)]:hidden">Move your cursor through the field</p>
              <p className="mt-3 hidden text-dim [@media(pointer:coarse)]:block">Touch the field to steer it</p>
            </div>
          </div>
        </div>,
        { 'data-cursor': 'query', 'data-cursor-label': 'your question' },
      )}

      {chapter(
        3,
        <div className="gutter flex h-full flex-col justify-start pt-28">
          <p className="eyebrow fade">03 — Retrieve</p>
          <Split as="h2" text="Five passages *step forward.*" className="headline mt-5 max-w-3xl" />
          <p className="lede fade mt-8 max-w-md" style={{ '--d': 0.3 } as React.CSSProperties}>
            The closest passages from the vector index and a live web search are pulled out, ranked, and handed to the model as its
            only evidence.
          </p>
          <p className="fade mt-6 font-mono text-xs text-dim" style={{ '--d': 0.45 } as React.CSSProperties}>
            q = <span className="text-paper">“{STORY_QUESTION}”</span>
          </p>
        </div>,
      )}

      {chapter(
        4,
        <div className="gutter flex h-full flex-col justify-end pb-16 sm:justify-center sm:pb-0">
          <div className="max-w-xl">
            <p className="eyebrow fade">04 — Cite</p>
            <Split as="h2" text="Every answer arrives with its *sources.*" className="headline mt-5" />
            <p className="lede fade mt-8 max-w-md" style={{ '--d': 0.3 } as React.CSSProperties}>
              The model writes only from those passages and marks each claim with the one it came from
              <sup className="cite">1</sup>. Follow any footnote back to the page.
            </p>
          </div>
          <p className="fade absolute bottom-8 left-5 hidden font-mono sm:block text-xs text-dim sm:left-10 lg:left-16" style={{ '--d': 0.6 } as React.CSSProperties}>
            <span className="text-signal">1</span> Like this one. In the assistant, hovering a marker lights up its source.
          </p>
        </div>,
      )}

      {chapter(LAST, <AskChapter />)}
    </>
  )
}

function ChapterIndex({ active, onSelect }: { active: number; onSelect: (i: number) => void }) {
  return (
    <>
      <nav aria-label="Chapters" className="fixed top-1/2 right-5 z-40 hidden -translate-y-1/2 lg:block">
        <ol className="space-y-2.5 text-right font-mono text-[0.6875rem] tracking-[0.14em] uppercase">
          {CHAPTERS.map((c, i) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => onSelect(i)}
                aria-current={active === i ? 'step' : undefined}
                className={`group inline-flex items-center gap-3 transition-colors ${active === i ? 'text-paper' : 'text-dim/60 hover:text-paper'}`}
              >
                <span className={active === i ? 'opacity-100' : 'opacity-0 transition-opacity group-hover:opacity-100'}>{c.label}</span>
                <span className={active === i ? 'text-signal' : ''}>{String(i).padStart(2, '0')}</span>
              </button>
            </li>
          ))}
        </ol>
      </nav>
      <p className={`fixed bottom-5 left-5 z-40 font-mono text-[0.6875rem] tracking-[0.14em] text-dim uppercase lg:hidden ${active === LAST ? 'hidden' : ''}`} aria-hidden="true">
        <span className="text-signal">{String(active).padStart(2, '0')}</span> / {CHAPTERS[active].label}
      </p>
    </>
  )
}

function AskChapter() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    if (q.trim()) navigate(`/chat?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div className="gutter relative h-full">
      <div className="absolute inset-x-0 text-center" style={{ bottom: `${(1 - ASK_INPUT.topVh) * 100 + 4}%` }}>
        <p className="eyebrow fade">05 — Ask</p>
        <Split as="h2" text="Your *turn.*" className="headline mt-4" />
      </div>

      <form
        onSubmit={submit}
        className="absolute left-1/2 -translate-x-1/2"
        style={{ top: `${ASK_INPUT.topVh * 100}%`, width: `min(${ASK_INPUT.maxWidthPx}px, ${ASK_INPUT.widthVw * 100}vw)` }}
      >
        <label htmlFor="ask" className="sr-only">
          Ask a question
        </label>
        {/* No visible border: the particles draw the underline and caret. The faint rule is the no-WebGL fallback. */}
        <input
          id="ask"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => (world.caretHidden = true)}
          onBlur={() => (world.caretHidden = false)}
          placeholder="What happened in AI this week?"
          maxLength={2000}
          autoComplete="off"
          className="w-full border-b border-rule/40 bg-transparent pl-4 text-xl font-light outline-none placeholder:text-dim/70 focus-visible:outline-none sm:text-2xl"
          style={{ height: ASK_INPUT.heightPx }}
        />
        <div className="mt-6 flex justify-end">
          <Magnetic>
            <button type="submit" className="bracket-btn text-paper" disabled={!q.trim()}>
              Ask ↵
            </button>
          </Magnetic>
        </div>
      </form>

      <footer className="absolute inset-x-5 bottom-6 flex flex-col gap-2 font-mono text-[0.6875rem] tracking-wide text-dim sm:inset-x-10 sm:flex-row sm:justify-between lg:inset-x-16">
        <span>Built by Raj Rathod · Flask · FAISS · OpenAI · React · Three.js</span>
        <span className="flex gap-5">
          <a href="https://github.com/rajrathod-1/AI-Content-Generation" target="_blank" rel="noreferrer" className="hover:text-paper">
            GitHub
          </a>
          <a href="https://www.linkedin.com/in/raj-rathod1/" target="_blank" rel="noreferrer" className="hover:text-paper">
            LinkedIn
          </a>
        </span>
      </footer>
    </div>
  )
}
