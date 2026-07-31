import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AdminLayout } from './components/AdminLayout'
import { LoginPage } from './pages/LoginPage'
import { WeaknessDetailPage } from './pages/WeaknessDetailPage'
import { WeaknessListPage } from './pages/WeaknessListPage'
import { useAuthStore } from './store/auth'

function RequireAuth({ children }: { children: React.ReactElement }) {
  const status = useAuthStore((s) => s.status)
  if (status === 'loading') return <div style={{ padding: 24 }}>확인 중…</div>
  if (status === 'anonymous') return <Navigate to="/login" replace />
  return children
}

function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap)

  useEffect(() => {
    bootstrap()
  }, [bootstrap])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <RequireAuth>
              <AdminLayout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Navigate to="/content/weaknesses" replace />} />
          <Route path="/content/weaknesses" element={<WeaknessListPage />} />
          <Route path="/content/weaknesses/:id" element={<WeaknessDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
