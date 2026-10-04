import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Color,
  LineBasicMaterial,
  LineSegments,
  PerspectiveCamera,
  Points,
  Raycaster,
  Scene,
  ShaderMaterial,
  Vector2,
  Vector3,
  WebGLRenderer,
} from 'three'
import { ASK_INPUT, MODE_POSE, blendPose, newPose, storyPose } from './choreography'
import { buildCloud, type Cloud } from './geometry'
import { particleFragment, particleVertex } from './shaders'
import { markReady, world } from './state'

const BASE = new Color('#efe9dd')
const ACCENT = new Color('#ff4d2e')

type Options = { reduced: boolean; compact: boolean }

/** The particle world behind every page. Framework-free; React only mounts and disposes it. */
export class World {
  private renderer: WebGLRenderer
  private scene = new Scene()
  private camera = new PerspectiveCamera(40, 1, 0.1, 60)
  private cloud!: Cloud
  private geometry!: BufferGeometry
  private material!: ShaderMaterial
  private threads!: LineSegments<BufferGeometry, LineBasicMaterial>

  private pose = newPose()
  private storyTarget = newPose()
  private pointer = new Vector2()
  private pointerSmooth = new Vector2()
  private pointerAt = -Infinity
  private mouseKind = ''
  private liveQuery = new Vector3()
  private query = new Vector3()
  private preset = new Vector3()
  private slots = Array.from({ length: 5 }, () => new Vector3())
  private lastChapter = 0
  private velocity = 0
  private orbitAngle = 0
  private orbit = 0
  private think = 0
  private touch = 0
  private last = performance.now()
  private readoutAt = 0
  private running = false
  private labelDrop = 0.32
  private slowFrames = 0
  private frames = 0
  private disposed = false

  private raycaster = new Raycaster()
  private hit = new Vector3()
  private anchor = new Vector3()
  private tmp = new Vector3()

  private light: boolean

  constructor(container: HTMLElement, private opts: Options) {
    this.renderer = new WebGLRenderer({ antialias: false, alpha: true, powerPreference: 'high-performance' })
    // Software WebGL (no GPU, blocklisted driver) gets a much lighter scene
    const gl = this.renderer.getContext()
    const info = gl.getExtension('WEBGL_debug_renderer_info')
    const name = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : ''
    this.light = /swiftshader|llvmpipe|software/i.test(name)
    this.renderer.setPixelRatio(this.light ? 1 : Math.min(window.devicePixelRatio, opts.compact ? 1.5 : 2))
    container.appendChild(this.renderer.domElement)
  }

  async start() {
    // The citation mark is sampled from the display font, so wait for it (briefly)
    await Promise.race([document.fonts.load('300 100px Fraunces'), new Promise((r) => setTimeout(r, 2000))]).catch(() => {})
    if (this.disposed) return

    const cloud = (this.cloud = buildCloud(this.light ? 6_000 : this.opts.compact ? 10_000 : 24_000))
    this.preset.fromArray(cloud.query)
    this.liveQuery.copy(this.preset)

    const g = (this.geometry = new BufferGeometry())
    g.setAttribute('position', new BufferAttribute(cloud.noise, 3))
    g.setAttribute('aCluster', new BufferAttribute(cloud.cluster, 3))
    g.setAttribute('aGlyph', new BufferAttribute(cloud.glyph, 3))
    g.setAttribute('aLine', new BufferAttribute(cloud.line, 3))
    g.setAttribute('aRand', new BufferAttribute(cloud.rand, 4))
    g.setAttribute('aSelected', new BufferAttribute(cloud.selected, 1))

    this.material = new ShaderMaterial({
      vertexShader: particleVertex,
      fragmentShader: particleFragment,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: this.renderer.getPixelRatio() },
        uSize: { value: this.opts.compact ? 3.4 : 2.8 },
        uAspect: { value: 1 },
        uDrift: { value: this.opts.reduced ? 0 : 1 },
        uCluster: { value: 0 },
        uFocus: { value: 0 },
        uQuery: { value: this.query },
        uRadius: { value: cloud.radius },
        uRetrieve: { value: 0 },
        uSlots: { value: this.slots },
        uClump: { value: 0.35 },
        uGlyph: { value: 0 },
        uGlyphOffset: { value: new Vector3() },
        uGlyphScale: { value: 1 },
        uLine: { value: 0 },
        uLineOffset: { value: new Vector3() },
        uLineScale: { value: new Vector2(1, 1) },
        uBlink: { value: 1 },
        uMouse: { value: this.pointerSmooth },
        uMouseForce: { value: 0 },
        uVelocity: { value: 0 },
        uThink: { value: 0 },
        uPulse: { value: 0 },
        uBase: { value: BASE },
        uAccent: { value: ACCENT },
        uOpacity: { value: 0 },
      },
    })
    const points = new Points(g, this.material)
    points.frustumCulled = false // the shader moves particles far from their buffer positions

    // Provenance threads: the question linked to each retrieved source
    const tg = new BufferGeometry().setAttribute('position', new BufferAttribute(new Float32Array(30), 3))
    this.threads = new LineSegments(tg, new LineBasicMaterial({ color: ACCENT, transparent: true, opacity: 0, depthWrite: false }))
    this.threads.frustumCulled = false
    this.scene.add(points, this.threads)

    window.addEventListener('resize', this.resize)
    window.addEventListener('pointermove', this.onPointer, { passive: true })
    window.addEventListener('pointerdown', this.onPointer, { passive: true })
    window.addEventListener('pointerout', this.onLeave)
    document.addEventListener('visibilitychange', this.toggle)
    this.resize()
    this.toggle()
    requestAnimationFrame(() => markReady())
  }

  private toggle = () => {
    const run = !document.hidden && !this.disposed
    if (run === this.running) return
    this.running = run
    this.last = performance.now()
    this.renderer.setAnimationLoop(run ? this.frame : null)
  }

  private onPointer = (e: PointerEvent) => {
    this.pointer.set((e.clientX / window.innerWidth) * 2 - 1, -(e.clientY / window.innerHeight) * 2 + 1)
    this.pointerAt = performance.now()
    this.mouseKind = e.pointerType
  }

  private onLeave = (e: PointerEvent) => {
    if (!e.relatedTarget) this.pointerAt = -Infinity // left the window
  }

  private resize = () => {
    const w = window.innerWidth
    const h = window.innerHeight
    this.renderer.setSize(w, h)
    this.camera.aspect = w / h
    this.camera.updateProjectionMatrix()
    if (!this.material) return
    const u = this.material.uniforms
    u.uAspect.value = w / h

    const tanHalf = Math.tan((this.camera.fov * Math.PI) / 360)
    const portrait = w < h
    // Citation mark, framed for the camera at z = 8: right of the copy on wide screens, above it on tall ones
    const vh8 = 2 * 8 * tanHalf
    const vw8 = vh8 * (w / h)
    u.uGlyphScale.value = portrait ? Math.min(0.2 * vh8, 0.26 * vw8) : Math.min(0.24 * vh8, 0.15 * vw8)
    u.uGlyphOffset.value.set(portrait ? 0 : 0.2 * vw8, portrait ? 0.2 * vh8 : 0, 0)

    // Underline and caret sit exactly on the DOM input in the last chapter
    const wpp = vh8 / h
    const inputW = Math.min(ASK_INPUT.maxWidthPx, ASK_INPUT.widthVw * w)
    u.uLineOffset.value.set(0, (h / 2 - (ASK_INPUT.topVh * h + ASK_INPUT.heightPx)) * wpp, 0)
    u.uLineScale.value.set((inputW / 2) * wpp, ASK_INPUT.heightPx * wpp)

    // Five source clumps, framed for the camera at z = 7.5
    const vh = 2 * 7.5 * tanHalf
    const vw = vh * (w / h)
    // Tall screens stack them in a tight column with labels beside; wide screens line them up with labels below
    this.slots.forEach((s, j) =>
      portrait ? s.set(-0.28 * vw, -0.04 * vh - j * 0.085 * vh, 0) : s.set((j - 2) * 0.16 * vw, -0.12 * vh, (j % 2) * 0.4),
    )
    u.uClump.value = portrait ? 0.18 : 0.35
    this.labelDrop = portrait ? 0 : 0.32
  }

  private frame = (now: number) => {
    const raw = now - this.last
    const dt = Math.min(raw / 1000, 0.05)
    this.last = now
    this.adaptQuality(raw)
    const { reduced } = this.opts
    const ease = (rate: number) => (reduced ? 1 : 1 - Math.exp(-dt * rate))
    const story = world.mode === 'story'
    const u = this.material.uniforms
    const p = this.pose

    // Story follows scroll; other pages hold a pose. Damping turns both into camera moves.
    const target = story ? storyPose(world.chapter, this.storyTarget) : MODE_POSE[world.mode as 'chat' | 'metrics']
    blendPose(p, target, ease(story ? 6 : 1.8))
    const v = Math.max(-1, Math.min(1, ((world.chapter - this.lastChapter) / Math.max(dt, 1e-3)) * 0.25))
    this.lastChapter = world.chapter
    this.velocity += (v - this.velocity) * ease(5)

    // Pointer: mice stay "present" until they leave; touches fade out after a moment
    const active = now - this.pointerAt < (this.mouseKind === 'mouse' ? Infinity : 2500)
    this.touch += ((active ? 1 : 0) - this.touch) * ease(4)
    this.pointerSmooth.lerp(this.pointer, ease(8))

    // Camera: chapter keyframe + parallax, plus a slow orbit away from the story
    this.orbit += ((story ? 0 : 1) - this.orbit) * ease(1.5)
    this.orbitAngle = story ? this.orbitAngle * (1 - ease(2)) : this.orbitAngle + dt * 0.035
    const [lx, ly, lz] = p.look
    const ox = p.cam[0] - lx
    const oz = p.cam[2] - lz
    const a = this.orbitAngle * this.orbit
    const parallax = (1 - p.line) * this.touch
    this.camera.position.set(
      lx + ox * Math.cos(a) - oz * Math.sin(a) + this.pointerSmooth.x * 0.45 * parallax,
      p.cam[1] + this.pointerSmooth.y * 0.25 * parallax,
      lz + ox * Math.sin(a) + oz * Math.cos(a),
    )
    this.camera.lookAt(lx, ly, lz)
    this.camera.updateMatrixWorld()

    // The question: under the cursor (or wandering on its own), then locked onto the story's question
    if (active) {
      // Snap the question's depth to whichever cluster the cursor is over
      this.raycaster.setFromCamera(this.pointer, this.camera)
      const ray = this.raycaster.ray
      let best = Infinity
      for (const c of this.cloud.centers) {
        const d = ray.distanceSqToPoint(this.anchor.fromArray(c))
        if (d < best) {
          best = d
          ray.closestPointToPoint(this.anchor, this.hit)
        }
      }
      this.liveQuery.lerp(this.hit, ease(6))
    } else if (!reduced) {
      // No pointer (touch, idle): drift from topic to topic so the readout still tells the story
      const t = now / 1000
      const c = this.cloud.centers[Math.floor(t / 3.2) % this.cloud.centers.length]
      this.hit.set(c[0] + Math.sin(t * 0.9) * 0.35, c[1] + Math.cos(t * 0.7) * 0.25, c[2])
      this.liveQuery.lerp(this.hit, ease(1.2))
    }
    this.query.copy(this.liveQuery).lerp(this.preset, p.lock)

    this.think += ((world.thinking ? 1 : 0) - this.think) * ease(3)
    const pulse = Math.max(0, 1 - (now - world.pulseAt) / 1600)

    u.uTime.value = reduced ? 0 : now / 1000
    u.uCluster.value = p.cluster
    u.uFocus.value = p.focus
    u.uRetrieve.value = p.retrieve
    u.uGlyph.value = p.glyph
    u.uLine.value = p.line
    u.uOpacity.value = p.opacity
    u.uMouseForce.value = p.mouse * this.touch * (reduced ? 0 : 1)
    u.uVelocity.value = reduced ? 0 : this.velocity
    u.uThink.value = this.think
    u.uPulse.value = pulse * pulse
    u.uBlink.value = world.caretHidden ? 0 : Math.floor(now / 530) % 2 ? 1 : 0.12

    this.updateThreads(story ? p.retrieve * (1 - p.glyph) : 0)
    this.placeLabels(story)
    if (story && p.focus > 0.5 && now - this.readoutAt > 150) this.readout(now)

    this.renderer.render(this.scene, this.camera)
  }

  // ponytail: one-way quality step (drop to 1x pixels after ~2s of sub-45fps); add tiers if low-end devices need more
  private adaptQuality(frameMs: number) {
    if (this.frames++ < 30 || this.renderer.getPixelRatio() <= 1) return
    this.slowFrames = frameMs > 22 ? this.slowFrames + 1 : Math.max(0, this.slowFrames - 1)
    if (this.slowFrames < 90) return
    this.renderer.setPixelRatio(1)
    this.material.uniforms.uPixelRatio.value = 1
    this.resize()
  }

  private updateThreads(alpha: number) {
    this.threads.material.opacity = alpha * 0.45
    if (alpha < 0.01) return
    const pos = this.threads.geometry.attributes.position
    this.slots.forEach((s, j) => {
      this.query.toArray(pos.array, j * 6)
      s.toArray(pos.array, j * 6 + 3)
    })
    pos.needsUpdate = true
  }

  private placeLabels(story: boolean) {
    const p = this.pose
    const w = window.innerWidth
    const h = window.innerHeight
    const place = (el: HTMLElement | null, at: Vector3, alpha: number) => {
      if (!el) return
      this.tmp.copy(at).project(this.camera)
      const show = story && alpha > 0.02 && this.tmp.z < 1
      el.style.opacity = show ? alpha.toFixed(3) : '0'
      if (show) el.style.transform = `translate3d(${((this.tmp.x + 1) / 2) * w}px, ${((1 - this.tmp.y) / 2) * h}px, 0)`
    }
    const clusterAlpha = p.cluster * (1 - p.retrieve) * (1 - p.focus * 0.6)
    world.labels.clusters.forEach((el, i) => {
      if (el && !el.textContent) el.textContent = this.cloud.topics[i]
      const c = this.cloud.centers[i]
      place(el, this.anchor.set(c[0], c[1] + 0.7, c[2]), clusterAlpha)
    })
    const sourceAlpha = p.retrieve * (1 - p.glyph)
    world.labels.sources.forEach((el, j) => place(el, this.anchor.copy(this.slots[j]).setY(this.slots[j].y - this.labelDrop), sourceAlpha))
  }

  private readout(now: number) {
    this.readoutAt = now
    const { cluster, count, centers, topics, radius } = this.cloud
    const [qx, qy, qz] = this.query.toArray()
    let within = 0
    for (let i = 0; i < count; i++) {
      const dx = cluster[i * 3] - qx
      const dy = cluster[i * 3 + 1] - qy
      const dz = cluster[i * 3 + 2] - qz
      if (dx * dx + dy * dy + dz * dz < radius * radius * 1.6 * 1.6) within++ // same reach as the shader's live probe
    }
    let best = 0
    centers.forEach((c, i) => {
      const d = Math.hypot(c[0] - qx, c[1] - qy, c[2] - qz)
      if (d < Math.hypot(centers[best][0] - qx, centers[best][1] - qy, centers[best][2] - qz)) best = i
    })
    world.onReadout?.(topics[best], within)
  }

  dispose() {
    this.disposed = true
    this.renderer.setAnimationLoop(null)
    window.removeEventListener('resize', this.resize)
    window.removeEventListener('pointermove', this.onPointer)
    window.removeEventListener('pointerdown', this.onPointer)
    window.removeEventListener('pointerout', this.onLeave)
    document.removeEventListener('visibilitychange', this.toggle)
    this.geometry?.dispose()
    this.material?.dispose()
    this.threads?.geometry.dispose()
    this.threads?.material.dispose()
    this.renderer.dispose()
    this.renderer.forceContextLoss()
    this.renderer.domElement.remove()
  }
}
