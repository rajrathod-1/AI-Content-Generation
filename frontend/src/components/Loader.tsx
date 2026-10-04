import { useEffect, useRef, useState } from 'react'
import { markReady, world } from '../world/state'

/** "[ 000 ]": the brackets open as the index builds, then part to reveal the world. Home page entries only. */
export default function Loader({ skip }: { skip: boolean }) {
  const [phase, setPhase] = useState<'load' | 'exit' | 'gone'>(skip ? 'gone' : 'load')
  const root = useRef<HTMLDivElement>(null)
  const count = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (skip) {
      document.documentElement.classList.add('is-loaded')
      return
    }
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const start = performance.now()
    let shown = 0
    let last = start
    let raf = 0
    let exit = 0
    const fallback = window.setTimeout(markReady, 6000) // never trap anyone behind the loader

    const tick = (now: number) => {
      const target = world.ready ? 1 : Math.min((now - start) / 1600, 0.9)
      // time-based easing, so a slow device doesn't stretch the intro
      shown = reduced ? target : shown + (target - shown) * (1 - Math.exp(-(now - last) / 160))
      last = now
      count.current!.textContent = String(Math.round(shown * 100)).padStart(3, '0')
      root.current!.style.setProperty('--p', String(shown))
      if (world.ready && shown > 0.995) {
        setPhase('exit')
        document.documentElement.classList.add('is-loaded')
        exit = window.setTimeout(() => setPhase('gone'), 1300)
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(fallback)
      clearTimeout(exit)
    }
  }, [skip])

  if (phase === 'gone') return null
  return (
    <div ref={root} className="loader" data-phase={phase} role="status" aria-label="Loading">
      <div className="text-center">
        <div className="loader-mark" aria-hidden="true">
          <span>[</span>
          <span ref={count} className="px-6 font-mono text-[0.22em] tracking-[0.2em] text-signal">
            000
          </span>
          <span>]</span>
        </div>
        <p className="eyebrow mt-6">Indexing the web</p>
      </div>
    </div>
  )
}
