import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AdminLayout } from './components/AdminLayout'
import { ArticleDetailPage } from './pages/ArticleDetailPage'
import { ArticleListPage } from './pages/ArticleListPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { DesignSystemPage } from './pages/DesignSystemPage'
import { FoodDetailPage } from './pages/FoodDetailPage'
import { FoodListPage } from './pages/FoodListPage'
import { HealthSignDetailPage } from './pages/HealthSignDetailPage'
import { HealthSignListPage } from './pages/HealthSignListPage'
import { HerbDetailPage } from './pages/HerbDetailPage'
import { HerbListPage } from './pages/HerbListPage'
import { IllnessDetailPage } from './pages/IllnessDetailPage'
import { IllnessListPage } from './pages/IllnessListPage'
import { LifeArticleDetailPage } from './pages/LifeArticleDetailPage'
import { LifeArticleListPage } from './pages/LifeArticleListPage'
import { LoginPage } from './pages/LoginPage'
import { NutrientDetailPage } from './pages/NutrientDetailPage'
import { NutrientListPage } from './pages/NutrientListPage'
import { PointDetailPage } from './pages/PointDetailPage'
import { PointListPage } from './pages/PointListPage'
import { ProductDetailPage } from './pages/ProductDetailPage'
import { ProductListPage } from './pages/ProductListPage'
import { TemTypeDetailPage } from './pages/TemTypeDetailPage'
import { TemTypeListPage } from './pages/TemTypeListPage'
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
          <Route path="/content/tem-types" element={<TemTypeListPage />} />
          <Route path="/content/tem-types/:id" element={<TemTypeDetailPage />} />
          <Route path="/content/nutrients" element={<NutrientListPage />} />
          <Route path="/content/nutrients/:id" element={<NutrientDetailPage />} />
          <Route path="/content/herbs" element={<HerbListPage />} />
          <Route path="/content/herbs/:id" element={<HerbDetailPage />} />
          <Route path="/content/foods" element={<FoodListPage />} />
          <Route path="/content/foods/:id" element={<FoodDetailPage />} />
          <Route path="/content/points" element={<PointListPage />} />
          <Route path="/content/points/:id" element={<PointDetailPage />} />
          <Route path="/content/health-signs" element={<HealthSignListPage />} />
          <Route path="/content/health-signs/:id" element={<HealthSignDetailPage />} />
          <Route path="/content/illnesses" element={<IllnessListPage />} />
          <Route path="/content/illnesses/:id" element={<IllnessDetailPage />} />
          <Route path="/content/products" element={<ProductListPage />} />
          <Route path="/content/products/:id" element={<ProductDetailPage />} />
          <Route path="/content/articles" element={<ArticleListPage />} />
          <Route path="/content/articles/:id" element={<ArticleDetailPage />} />
          <Route path="/content/life-articles" element={<LifeArticleListPage />} />
          <Route path="/content/life-articles/:id" element={<LifeArticleDetailPage />} />
          <Route path="/system/audit-logs" element={<AuditLogPage />} />
          <Route path="/system/design" element={<DesignSystemPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
