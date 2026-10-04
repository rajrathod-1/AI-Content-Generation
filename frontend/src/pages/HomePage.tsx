import { lazy, Suspense } from 'react'
import { Link } from 'react-router'
import { ArrowRight } from 'lucide-react'

const VectorField = lazy(() => import('../components/VectorField'))

const STEPS = [
  { title: 'Classify', body: 'Small talk gets a direct reply. Questions that need facts go on to retrieval.', tag: 'query_classifier' },
  { title: 'Search the web', body: 'Fresh results are pulled from public search and Wikipedia, then cleaned to plain text.', tag: 'realtime_search' },
  { title: 'Retrieve', body: 'The question is embedded and matched against the FAISS index by cosine similarity.', tag: 'MiniLM-L6 · 384-d' },
  { title: 'Augment', body: 'The strongest passages, web first, are packed into a ~4k-token context.', tag: 'context builder' },
  { title: 'Generate', body: 'The model answers from that context and returns the sources it was given.', tag: 'OpenAI' },
]

const COMPARE = [
  ['Knowledge', 'Frozen at its training cutoff', 'Fetched when you ask'],
  ['Citations', 'None', 'Every answer lists its sources'],
  ['Grounding', 'Free to fill gaps with guesses', 'Written from retrieved passages'],
  ['Your documents', 'Invisible to the model', 'Ingested into the vector index'],
]

const STACK = ['React 19', 'Three.js', 'Flask', 'FAISS', 'Sentence-Transformers', 'OpenAI', 'Redis']

export default function HomePage() {
  return (
    <>
      <section className="relative isolate overflow-hidden border-b border-line">
        <div className="hero-grid absolute inset-0 -z-20" />
        <Suspense>
          <VectorField className="absolute inset-0 -z-10 opacity-50 lg:left-[35%] lg:opacity-100" />
        </Suspense>
        <div className="absolute inset-0 -z-10 bg-canvas/40 lg:bg-transparent lg:bg-linear-to-r lg:from-canvas lg:from-25% lg:via-canvas/60 lg:via-40% lg:to-transparent lg:to-65%" />

        <div className="mx-auto flex max-w-6xl flex-col justify-center px-4 py-24 sm:px-6 sm:py-32 lg:min-h-[calc(100dvh-3.5rem)]">
          <p className="eyebrow">Retrieval-augmented generation</p>
          <h1 className="mt-5 max-w-xl text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
            Answers that show their sources.
          </h1>
          <p className="mt-6 max-w-lg text-lg text-pretty text-muted">
            Ask a question. The assistant searches the live web and a FAISS vector index, then writes an answer grounded in
            what it found, with links you can check.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link to="/chat" className="btn-primary">
              Open the assistant <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
            <a href="#how" className="btn-ghost">
              How it works
            </a>
          </div>
          <p className="mt-20 max-w-xs font-mono text-xs leading-relaxed text-muted">
            fig. 1 · a query vector (bright) linked to its six nearest neighbours in embedding space
          </p>
        </div>
      </section>

      <section id="how" className="scroll-mt-14 border-b border-line">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <p className="eyebrow">How it works</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            From question to cited answer in five steps.
          </h2>
          <ol className="mt-12 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((step, i) => (
              <li key={step.title} className="reveal flex flex-col bg-canvas p-6 sm:last:col-span-2 lg:last:col-span-1">
                <span className="font-mono text-xs text-accent">{String(i + 1).padStart(2, '0')}</span>
                <h3 className="mt-8 font-medium">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
                <p className="mt-auto pt-8 font-mono text-xs text-muted">{step.tag}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 sm:py-28 lg:grid-cols-[1fr_1.4fr] lg:items-center">
          <div>
            <p className="eyebrow">Why retrieval</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              A plain chatbot answers from memory. This one looks things up.
            </h2>
            <p className="mt-5 text-pretty text-muted">
              Retrieval gives the model the passages it needs at question time, so answers can be current and you can trace each
              claim back to where it came from.
            </p>
          </div>
          <div className="reveal overflow-x-auto rounded-xl border border-line">
            <table className="w-full min-w-md text-left text-sm">
              <thead className="border-b border-line font-mono text-xs text-muted">
                <tr>
                  <td className="p-4" />
                  <th scope="col" className="p-4 font-normal">Plain LLM</th>
                  <th scope="col" className="p-4 font-normal text-accent">This assistant</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {COMPARE.map(([label, plain, rag]) => (
                  <tr key={label}>
                    <th scope="row" className="p-4 font-medium">{label}</th>
                    <td className="p-4 text-muted">{plain}</td>
                    <td className="p-4">{rag}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="panel relative isolate overflow-hidden px-6 py-14 sm:px-12">
            <div className="hero-grid absolute inset-0 -z-10 opacity-60" />
            <h2 className="max-w-xl text-3xl font-semibold tracking-tight text-balance">
              Ask it about something that happened this week.
            </h2>
            <p className="mt-4 max-w-lg text-pretty text-muted">
              The backend runs on a free tier, so the first request after a quiet spell can take up to a minute while it wakes up.
            </p>
            <Link to="/chat" className="btn-primary mt-8">
              Open the assistant <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
            <ul aria-label="Built with" className="mt-12 flex flex-wrap gap-x-6 gap-y-2 font-mono text-xs text-muted">
              {STACK.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  )
}
