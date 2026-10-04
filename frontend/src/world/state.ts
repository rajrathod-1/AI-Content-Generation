export type WorldMode = 'story' | 'chat' | 'metrics'

/**
 * Mutable bridge between React and the render loop. Pages write to it; the
 * loop reads it every frame, so nothing here triggers a React render.
 */
export const world = {
  mode: 'story' as WorldMode,
  /** Home-page scroll position measured in chapters, 0..5. */
  chapter: 0,
  thinking: false,
  pulseAt: -Infinity,
  caretHidden: false,
  ready: false,
  /** Live readout for the query chapter: nearest topic and passages within reach. */
  onReadout: null as null | ((topic: string, count: number) => void),
  /** HTML labels the loop positions over 3D anchors. */
  labels: { clusters: [] as (HTMLElement | null)[], sources: [] as (HTMLElement | null)[] },
}

export function markReady() {
  world.ready = true
}
