import { STORY_TOPIC, TOPICS } from './choreography'

/** Seeded PRNG so clusters (and their labels) land in the same place on every visit. */
function mulberry32(seed: number) {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export type Cloud = {
  count: number
  noise: Float32Array
  cluster: Float32Array
  glyph: Float32Array
  line: Float32Array
  rand: Float32Array
  selected: Float32Array
  centers: [number, number, number][]
  query: [number, number, number]
  radius: number
  topics: string[]
}

/** Pixels of `text` drawn on a canvas, as points normalised so the glyph height spans -1..1. */
function samplePixels(draw: (ctx: CanvasRenderingContext2D) => void, w: number, h: number) {
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!
  ctx.fillStyle = '#fff'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  draw(ctx)
  const data = ctx.getImageData(0, 0, w, h).data
  const pts: number[] = []
  for (let y = 0; y < h; y += 2) {
    for (let x = 0; x < w; x += 2) {
      if (data[(y * w + x) * 4 + 3] > 140) pts.push((x - w / 2) / (h / 2), -(y - h / 2) / (h / 2))
    }
  }
  return pts
}

export function buildCloud(count: number): Cloud {
  const rand = mulberry32(7)
  const gauss = () => {
    const u = Math.max(rand(), 1e-6)
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand())
  }

  // Topic clusters spread on a squashed sphere (golden-angle spacing), each with its own stretch
  const k = TOPICS.length
  const centers: [number, number, number][] = []
  for (let i = 0; i < k; i++) {
    const y = 1 - (2 * (i + 0.5)) / k
    const r = Math.sqrt(1 - y * y)
    const a = i * 2.39996
    centers.push([Math.cos(a) * r * 3.1, y * 1.7, Math.sin(a) * r * 2.2])
  }
  // The story's question lands in the cluster nearest the camera, so retrieval reads well
  const front = centers.reduce((best, c, i) => (c[2] > centers[best][2] ? i : best), 0)
  const topics = [...TOPICS]
  ;[topics[front], topics[STORY_TOPIC]] = [topics[STORY_TOPIC], topics[front]]
  const stretch = centers.map(() => [0.35 + rand() * 0.35, 0.3 + rand() * 0.3, 0.3 + rand() * 0.35])

  const noise = new Float32Array(count * 3)
  const cluster = new Float32Array(count * 3)
  const rnd = new Float32Array(count * 4)
  for (let i = 0; i < count; i++) {
    noise.set([(rand() - 0.5) * 16, (rand() - 0.5) * 10, (rand() - 0.5) * 8 - 1], i * 3)
    const ci = i % k
    const [sx, sy, sz] = stretch[ci]
    const c = centers[ci]
    cluster.set([c[0] + gauss() * sx, c[1] + gauss() * sy, c[2] + gauss() * sz], i * 3)
    rnd.set([rand(), rand() ** 2, rand() * 100, Math.floor(rand() * 5)], i * 4)
  }

  // The retrieved set: the 5% of passages nearest the story's question
  const query: [number, number, number] = [...centers[front]]
  query[0] += 0.15
  const dist = new Float32Array(count)
  for (let i = 0; i < count; i++) {
    dist[i] = Math.hypot(cluster[i * 3] - query[0], cluster[i * 3 + 1] - query[1], cluster[i * 3 + 2] - query[2])
  }
  const order = Array.from({ length: count }, (_, i) => i).sort((a, b) => dist[a] - dist[b])
  const take = Math.round(count * 0.05)
  const selected = new Float32Array(count)
  for (let j = 0; j < take; j++) selected[order[j]] = 1
  const radius = dist[order[take - 1]]

  // "[1]": retrieved passages form the numeral, everything else the brackets
  const font = (px: number) => `300 ${px}px Fraunces, Georgia, serif`
  const brackets = samplePixels((ctx) => {
    ctx.font = font(300)
    ctx.fillText('[', 120, 160)
    ctx.fillText(']', 392, 160)
  }, 512, 320)
  const numeral = samplePixels((ctx) => {
    ctx.font = font(250)
    ctx.fillText('1', 256, 165)
  }, 512, 320)

  const glyph = new Float32Array(count * 3)
  const line = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    const pool = selected[i] ? numeral : brackets
    const j = Math.floor(rand() * (pool.length / 2)) * 2
    glyph.set([pool[j] + (rand() - 0.5) * 0.02, pool[j + 1] + (rand() - 0.5) * 0.02, (rand() - 0.5) * 0.12], i * 3)
    // Underline across the input; retrieved passages become the caret at its start
    line.set(selected[i] ? [-0.985 + rand() * 0.006, 0.22 + rand() * 0.56, 0] : [rand() * 2 - 1, (rand() - 0.5) * 0.012, 0], i * 3)
  }

  return { count, noise, cluster, glyph, line, rand: rnd, selected, centers, query, radius, topics }
}
