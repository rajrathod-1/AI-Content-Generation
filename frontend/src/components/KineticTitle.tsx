import { useEffect, useRef } from 'react'

/** Display type whose weight swells toward the cursor (Fraunces' wght, SOFT and WONK axes). */
export default function KineticTitle({ lines, className = '' }: { lines: string[]; className?: string }) {
  const ref = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    const el = ref.current
    const fine = window.matchMedia('(pointer: fine)').matches
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!el || !fine || reduced) return
    const chars = [...el.querySelectorAll<HTMLElement>('.ch')]
    let mx = -1e4
    let my = -1e4
    let raf = 0
    const apply = () => {
      raf = 0
      for (const ch of chars) {
        const r = ch.getBoundingClientRect()
        const k = Math.max(0, 1 - Math.hypot(r.left + r.width / 2 - mx, r.top + r.height / 2 - my) / 360)
        ch.style.fontVariationSettings = `"wght" ${Math.round(300 + 480 * k)}, "SOFT" ${Math.round(100 - 100 * k)}, "WONK" ${k > 0.55 ? 1 : 0}`
      }
    }
    const move = (e: PointerEvent) => {
      mx = e.clientX
      my = e.clientY
      raf ||= requestAnimationFrame(apply)
    }
    window.addEventListener('pointermove', move, { passive: true })
    return () => {
      window.removeEventListener('pointermove', move)
      cancelAnimationFrame(raf)
    }
  }, [])

  let n = 0
  return (
    <h1 ref={ref} className={`kinetic ${className}`}>
      <span className="sr-only">{lines.join(' ')}</span>
      <span aria-hidden="true">
        {lines.map((line) => (
          <span key={line} className="block whitespace-nowrap">
            {[...line].map((ch, i) =>
              ch === ' ' ? (
                ' '
              ) : (
                <span key={i} className="ch" style={{ '--i': n++ } as React.CSSProperties}>
                  {ch}
                </span>
              ),
            )}
          </span>
        ))}
      </span>
    </h1>
  )
}
