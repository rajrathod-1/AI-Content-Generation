# RAG Generator: Frontend

React 19 + TypeScript, built with Vite 8 and Tailwind CSS 4. The hero is a Three.js scene of document embeddings with a query vector linking to its nearest neighbours, a picture of what the FAISS search does. Three.js is lazy-loaded, so the chat and metrics pages don't pay for it.

## Pages

- `/`: overview, the five-step RAG pipeline, and a comparison with a plain LLM
- `/chat`: the assistant, with Markdown answers, source cards and match scores, and retry on failure
- `/metrics`: live request, latency, and server resource metrics from `/api/metrics`

## Develop

Requires Node 20.19+.

```bash
npm install
npm run dev      # http://localhost:3000; proxies /api to the Flask backend on :5000
npm run build    # type-checks, then builds to dist/
```

## Configure

`VITE_API_BASE_URL`: the backend URL, with or without a trailing `/api`. Leave it unset locally to use the dev proxy.
