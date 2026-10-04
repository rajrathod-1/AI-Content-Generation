import { useEffect, useRef } from 'react'
import { markReady } from '../world/state'

/** Mounts the particle world once, behind every route. Three.js loads lazily. */
export default function WorldCanvas() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let disposed = false
    let instance: { dispose(): void } | null = null
    import('../world/World').then(
      ({ World }) => {
        if (disposed || !ref.current) return
        try {
          const w = new World(ref.current, {
            reduced: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            compact: window.matchMedia('(max-width: 767px), (pointer: coarse)').matches,
          })
          instance = w
          w.start().catch(markReady)
        } catch {
          markReady() // no WebGL: every page still works on the plain backdrop
        }
      },
      markReady,
    )
    return () => {
      disposed = true
      instance?.dispose()
    }
  }, [])

  return (
    <div className="world" aria-hidden="true">
      <div ref={ref} className="absolute inset-0" />
    </div>
  )
}
