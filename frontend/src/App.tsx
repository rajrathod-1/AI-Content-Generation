import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router'
import { Footer, Header } from './components/Layout'
import { useBackendStatus } from './api'
import HomePage from './pages/HomePage'

const ChatPage = lazy(() => import('./pages/ChatPage'))
const MetricsPage = lazy(() => import('./pages/MetricsPage'))

export default function App() {
  const backend = useBackendStatus()
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-dvh flex-col">
      <Header backend={backend} />
      <main className="flex-1">
        <Suspense>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage backend={backend} />} />
            <Route path="/metrics" element={<MetricsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      {pathname !== '/chat' && <Footer />}
    </div>
  )
}
