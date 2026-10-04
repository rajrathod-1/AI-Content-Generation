import type { WorldMode } from './state'

export const CHAPTERS = [
  { id: 'noise', label: 'Noise' },
  { id: 'embed', label: 'Embed' },
  { id: 'query', label: 'Query' },
  { id: 'retrieve', label: 'Retrieve' },
  { id: 'cite', label: 'Cite' },
  { id: 'ask', label: 'Ask' },
] as const

export const TOPICS = [
  'court rulings',
  'protein folding',
  'match reports',
  'earnings calls',
  'climate data',
  'transit maps',
  'recipes',
  'python release notes',
]
/** The cluster the story's question lands in (its topic is moved to this slot at build time). */
export const STORY_TOPIC = TOPICS.length - 1

export const STORY_QUESTION = 'What changed in the latest Python release?'
export const STORY_SOURCES = [
  'docs.python.org / whatsnew',
  'peps.python.org',
  'en.wikipedia.org / History_of_Python',
  'faiss index · doc 0412',
  'discuss.python.org',
]

/** Where the final input sits, shared by the DOM and the particle underline. */
export const ASK_INPUT = { topVh: 0.56, heightPx: 64, maxWidthPx: 680, widthVw: 0.86 }

export type Pose = {
  cluster: number
  focus: number
  lock: number
  retrieve: number
  glyph: number
  line: number
  opacity: number
  mouse: number
  cam: [number, number, number]
  look: [number, number, number]
}

const clamp01 = (x: number) => Math.min(Math.max(x, 0), 1)
const smooth = (a: number, b: number, x: number) => {
  const t = clamp01((x - a) / (b - a))
  return t * t * (3 - 2 * t)
}

// One camera keyframe per chapter
const CAMERA: Pick<Pose, 'cam' | 'look'>[] = [
  { cam: [0, 0.3, 11], look: [0, 0, 0] },
  { cam: [-3.4, 1.3, 7.6], look: [2.2, 0.3, 0] }, // cloud sits left of the copy
  { cam: [0.9, 0.4, 6.4], look: [0, 0, 0] },
  { cam: [0, 0, 7.5], look: [0, 0, 0] },
  { cam: [0, 0, 8], look: [0, 0, 0] },
  { cam: [0, 0, 8], look: [0, 0, 0] },
]

/**
 * Chapter i holds (text pinned) for c in [i, i+0.33]; the world moves toward
 * chapter i+1 over [i+0.3, i+1], so it has arrived when the next text pins.
 */
export function storyPose(c: number, out: Pose): Pose {
  const focus = smooth(1.3, 2, c) * (1 - smooth(2.3, 2.9, c))
  const line = smooth(4.35, 5, c)
  out.cluster = smooth(0.3, 1, c)
  out.focus = focus
  out.lock = smooth(2.3, 2.9, c)
  out.retrieve = smooth(2.35, 3, c)
  out.glyph = smooth(3.35, 4, c)
  out.line = line
  out.opacity = 1
  out.mouse = (1 - focus) * (1 - line * 0.6)

  const i = Math.min(Math.floor(c), CAMERA.length - 2)
  const t = smooth(i + 0.3, i + 1, c)
  for (let k = 0; k < 3; k++) {
    out.cam[k] = CAMERA[i].cam[k] + (CAMERA[i + 1].cam[k] - CAMERA[i].cam[k]) * t
    out.look[k] = CAMERA[i].look[k] + (CAMERA[i + 1].look[k] - CAMERA[i].look[k]) * t
  }
  return out
}

const base = { focus: 0, lock: 0, retrieve: 0, glyph: 0, line: 0 }
export const MODE_POSE: Record<Exclude<WorldMode, 'story'>, Pose> = {
  chat: { ...base, cluster: 1, focus: 0.45, lock: 1, opacity: 0.55, mouse: 0.6, cam: [-5.8, 1.2, 9.5], look: [-2.4, 0, 0] },
  metrics: { ...base, cluster: 1, opacity: 0.35, mouse: 0.5, cam: [0, 7.5, 9], look: [0, 0, 0] },
}

export const newPose = (): Pose => ({ ...base, cluster: 0, opacity: 0, mouse: 1, cam: [0, 0.3, 14], look: [0, 0, 0] })

export function blendPose(cur: Pose, target: Pose, k: number) {
  for (const key of ['cluster', 'focus', 'lock', 'retrieve', 'glyph', 'line', 'opacity', 'mouse'] as const) {
    cur[key] += (target[key] - cur[key]) * k
  }
  for (let i = 0; i < 3; i++) {
    cur.cam[i] += (target.cam[i] - cur.cam[i]) * k
    cur.look[i] += (target.look[i] - cur.look[i]) * k
  }
}
