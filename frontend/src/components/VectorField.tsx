import { useEffect, useRef } from 'react'
import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Color,
  Group,
  LineBasicMaterial,
  LineSegments,
  NormalBlending,
  PerspectiveCamera,
  Points,
  Scene,
  ShaderMaterial,
  Vector3,
  WebGLRenderer,
} from 'three'

const ACCENT = new Color('#5eead4')
const BASE = new Color('#a3a9b3')
const K = 6 // neighbours per query
const CYCLE = 3600 // ms per query

const vertexShader = /* glsl */ `
  uniform float uSize;
  uniform float uPixelRatio;
  varying float vDepth;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * uPixelRatio * (6.0 / -mv.z);
    vDepth = clamp((-mv.z - 4.0) / 6.0, 0.0, 1.0);
  }
`

const fragmentShader = /* glsl */ `
  uniform vec3 uColor;
  uniform float uOpacity;
  varying float vDepth;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    gl_FragColor = vec4(uColor, smoothstep(0.5, 0.1, d) * uOpacity * (1.0 - 0.7 * vDepth));
  }
`

const dots = (color: Color, size: number, opacity: number, additive = false) =>
  new ShaderMaterial({
    uniforms: {
      uColor: { value: color },
      uSize: { value: size },
      uOpacity: { value: opacity },
      uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
    },
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    blending: additive ? AdditiveBlending : NormalBlending,
  })

const gauss = () => (Math.random() + Math.random() + Math.random() - 1.5) * 0.9
const easeOut = (t: number) => 1 - (1 - t) ** 3

/** Clustered points stand in for document embeddings; a query vector keeps finding its nearest neighbours. */
export default function VectorField({ className = '' }: { className?: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    let renderer: WebGLRenderer
    try {
      renderer = new WebGLRenderer({ antialias: true, alpha: true })
    } catch {
      return // no WebGL: the CSS backdrop is enough
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const count = window.matchMedia('(max-width: 640px)').matches ? 700 : 1400

    const scene = new Scene()
    const camera = new PerspectiveCamera(45, 1, 0.1, 50)
    const group = new Group()
    scene.add(group)

    const centers = Array.from({ length: 7 }, () => new Vector3().randomDirection().multiplyScalar(0.6 + Math.random() * 1.5))
    const cloud = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const c = centers[i % centers.length]
      cloud.set([c.x + gauss() * 0.45, c.y + gauss() * 0.45, c.z + gauss() * 0.45], i * 3)
    }

    const geo = (n: number) => new BufferGeometry().setAttribute('position', new BufferAttribute(new Float32Array(n * 3), 3))
    const cloudGeo = new BufferGeometry().setAttribute('position', new BufferAttribute(cloud, 3))
    const hitGeo = geo(K)
    const queryGeo = geo(1)
    const lineGeo = geo(K * 2)
    const cloudMat = dots(BASE, 4, 0.75)
    const hitMat = dots(ACCENT, 7, 0, true)
    const queryMat = dots(ACCENT, 14, 0, true)
    const lineMat = new LineBasicMaterial({ color: ACCENT, transparent: true, opacity: 0, depthWrite: false })
    group.add(new Points(cloudGeo, cloudMat), new LineSegments(lineGeo, lineMat), new Points(hitGeo, hitMat), new Points(queryGeo, queryMat))

    const query = new Vector3()
    const hits = Array.from({ length: K }, () => new Vector3())
    const dist = new Float32Array(count)
    const order = Array.from({ length: count }, (_, i) => i)

    const pickQuery = () => {
      const c = centers[Math.floor(Math.random() * centers.length)]
      query.set(c.x + gauss() * 0.3, c.y + gauss() * 0.3, c.z + gauss() * 0.3)
      for (let i = 0; i < count; i++) {
        dist[i] = (cloud[i * 3] - query.x) ** 2 + (cloud[i * 3 + 1] - query.y) ** 2 + (cloud[i * 3 + 2] - query.z) ** 2
      }
      order.sort((a, b) => dist[a] - dist[b])
      const hp = hitGeo.attributes.position.array as Float32Array
      hits.forEach((h, j) => {
        h.fromArray(cloud, order[j] * 3)
        h.toArray(hp, j * 3)
      })
      query.toArray(queryGeo.attributes.position.array as Float32Array)
      hitGeo.attributes.position.needsUpdate = true
      queryGeo.attributes.position.needsUpdate = true
    }

    // t = ms since this query was picked
    const update = (t: number, now: number) => {
      const grow = easeOut(Math.min(t / 800, 1))
      const fade = t > CYCLE - 600 ? (CYCLE - t) / 600 : Math.min(t / 300, 1)
      const lp = lineGeo.attributes.position.array as Float32Array
      hits.forEach((h, j) => {
        query.toArray(lp, j * 6)
        lp[j * 6 + 3] = query.x + (h.x - query.x) * grow
        lp[j * 6 + 4] = query.y + (h.y - query.y) * grow
        lp[j * 6 + 5] = query.z + (h.z - query.z) * grow
      })
      lineGeo.attributes.position.needsUpdate = true
      lineMat.opacity = 0.85 * fade
      hitMat.uniforms.uOpacity.value = fade * grow
      queryMat.uniforms.uOpacity.value = fade
      queryMat.uniforms.uSize.value = 14 + Math.sin(now / 200) * 2.5
    }

    const pointer = { x: 0, y: 0 }
    const onPointer = (e: PointerEvent) => {
      pointer.x = (e.clientX / window.innerWidth) * 2 - 1
      pointer.y = (e.clientY / window.innerHeight) * 2 - 1
    }

    let raf = 0
    let last = performance.now()
    let picked = -Infinity
    let spin = 0
    const frame = (now: number) => {
      const dt = Math.min(now - last, 50)
      last = now
      if (now - picked > CYCLE) {
        pickQuery()
        picked = now
      }
      update(now - picked, now)
      spin += dt * 0.00006
      group.rotation.x += (pointer.y * 0.25 - group.rotation.x) * 0.04
      group.rotation.y += (spin + pointer.x * 0.35 - group.rotation.y) * 0.04
      renderer.render(scene, camera)
      raf = requestAnimationFrame(frame)
    }

    let visible = true
    const toggle = () => {
      cancelAnimationFrame(raf)
      if (!reduced && visible && !document.hidden) raf = requestAnimationFrame(frame)
    }
    const io = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting
      toggle()
    })
    const ro = new ResizeObserver(() => {
      const { clientWidth: w, clientHeight: h } = el
      if (!w || !h) return
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.position.z = w / h < 1 ? 9 : 7
      camera.updateProjectionMatrix()
      if (reduced) renderer.render(scene, camera)
    })

    if (reduced) {
      pickQuery()
      update(CYCLE / 2, 0)
    } else {
      window.addEventListener('pointermove', onPointer)
      document.addEventListener('visibilitychange', toggle)
      io.observe(el)
    }
    ro.observe(el)

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
      ro.disconnect()
      window.removeEventListener('pointermove', onPointer)
      document.removeEventListener('visibilitychange', toggle)
      for (const d of [cloudGeo, hitGeo, queryGeo, lineGeo, cloudMat, hitMat, queryMat, lineMat]) d.dispose()
      renderer.dispose()
      renderer.forceContextLoss()
      renderer.domElement.remove()
    }
  }, [])

  return <div ref={ref} className={className} aria-hidden="true" />
}
