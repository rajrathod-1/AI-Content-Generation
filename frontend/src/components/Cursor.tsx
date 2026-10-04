import { useEffect, useRef } from 'react'

/** Brackets that "cite" whatever is under them. Fine pointers only. */
export default function Cursor() {
  const dot = useRef<HTMLDivElement>(null)
  const ring = useRef<HTMLDivElement>(null)
  const label = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const root = document.documentElement
    root.classList.add('has-cursor')
    let x = -100
    let y = -100
    let rx = x
    let ry = y
    let raf = 0

    const classify = (target: Element | null) => {
      const hit = target?.closest<HTMLElement>('a, button, [data-cursor]')
      ring.current!.dataset.mode = target?.closest('input, textarea') ? 'text' : hit ? (hit.dataset.cursor ?? 'link') : ''
      label.current!.textContent = hit?.dataset.cursorLabel ?? ''
    }
    const move = (e: PointerEvent) => {
      x = e.clientX
      y = e.clientY
      classify(e.target instanceof Element ? e.target : null)
    }
    // Scrolling changes what's under a still cursor
    const scroll = () => classify(document.elementFromPoint(x, y))
    const down = () => ring.current!.classList.add('is-down')
    const up = () => ring.current!.classList.remove('is-down')
    const tick = () => {
      const k = reduced ? 1 : 0.2
      rx += (x - rx) * k
      ry += (y - ry) * k
      dot.current!.style.transform = `translate3d(${x}px, ${y}px, 0)`
      ring.current!.style.transform = `translate3d(${rx}px, ${ry}px, 0)`
      raf = requestAnimationFrame(tick)
    }

    window.addEventListener('pointermove', move, { passive: true })
    window.addEventListener('scroll', scroll, { passive: true })
    window.addEventListener('pointerdown', down)
    window.addEventListener('pointerup', up)
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('pointermove', move)
      window.removeEventListener('scroll', scroll)
      window.removeEventListener('pointerdown', down)
      window.removeEventListener('pointerup', up)
      root.classList.remove('has-cursor')
    }
  }, [])

  return (
    <>
      <div ref={dot} className="cursor-dot" aria-hidden="true" />
      <div ref={ring} className="cursor-ring" aria-hidden="true">
        <span ref={label} />
      </div>
    </>
  )
}
