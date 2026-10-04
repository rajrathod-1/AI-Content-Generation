# RAG Generator: Frontend

**Concept: Provenance.** The site is one persistent particle world made of fragments of web text. Scrolling the home page tells the RAG story inside it, in six chapters:

| | Chapter | What the world does |
|---|---|---|
| 00 | Noise | Loose fragments drift; the cursor pushes them aside |
| 01 | Embed | Fragments settle into labelled topic clusters |
| 02 | Query | The cursor *is* the question: its nearest neighbours light up, with a live readout |
| 03 | Retrieve | Five passages step forward as sources, threaded back to the question |
| 04 | Cite | Everything collapses into a citation mark, **[1]** |
| 05 | Ask | The mark becomes the underline and caret of a real input that starts a chat |

The world persists across routes: it drifts aside behind the assistant, leans in while an answer is retrieved, and flashes when it lands. Answers show inline `[n]` markers linked to numbered footnotes.

## Stack

React 19, React Router 8, Vite 8, Tailwind CSS 4, Three.js (lazy-loaded, about 137 KB gzipped). Type is Fraunces (variable: `wght`, `SOFT`, `WONK`, `opsz`) with Geist Mono.

## Code map

- `src/world/`: framework-free Three.js. `World.ts` (renderer, loop, camera, labels), `shaders.ts` (every particle's journey through the six states, on the GPU), `geometry.ts` (clusters, the retrieved set, and the citation glyph sampled from the font), `choreography.ts` (scroll → poses), `state.ts` (the mutable bridge pages write to)
- `src/components/`: world mount, bracket cursor, loader, magnetic links, kinetic and split-reveal type
- `src/pages/`: Home (the story), Chat (the assistant), Metrics

## Performance and accessibility

- One draw call for 24k particles (10k on phones; 6k on software WebGL). The CPU only updates uniforms each frame.
- Rendering pauses in background tabs. Pixel density drops to 1× if frames run slow.
- All copy is real DOM text and reads fine without WebGL.
- `prefers-reduced-motion` freezes drift and reveals. The custom cursor is mouse-only.

## Develop

Requires Node 20.19+.

```bash
npm install
npm run dev      # http://localhost:3000; proxies /api to the Flask backend on :5000
npm run build    # type-checks, then builds to dist/
```

`VITE_API_BASE_URL`: the backend URL, with or without a trailing `/api`. Leave it unset locally to use the dev proxy.
