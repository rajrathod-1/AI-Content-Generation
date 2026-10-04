import { lazy, Suspense, useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router'
import { useBackendStatus } from './api'
import Cursor from './components/Cursor'
import Header from './components/Header'
import Loader from './components/Loader'
import WorldCanvas from './components/WorldCanvas'
import HomePage from './pages/HomePage'
import { world } from './world/state'

const ChatPage = lazy(() => import('./pages/ChatPage'))
const MetricsPage = lazy(() => import('./pages/MetricsPage'))

export default function App() {
  const backend = useBackendStatus()
  const { pathname } = useLocation()
  const [entryIsHome] = useState(pathname === '/')

  // Each route has its own pose in the world; changing route is the camera move
  useEffect(() => {
    world.mode = pathname === '/chat' ? 'chat' : pathname === '/metrics' ? 'metrics' : 'story'
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <>
      <WorldCanvas />
      <div className="grain" aria-hidden="true" />
      <Cursor />
      <Loader skip={!entryIsHome} />
      <Header backend={backend} />
      <main key={pathname} className="page">
        <Suspense>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage backend={backend} />} />
            <Route path="/metrics" element={<MetricsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </>
  )
}
