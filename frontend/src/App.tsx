import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './pages/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { useAppSelector } from './hooks/redux'

function App() {
  const { isAuthenticated } = useAppSelector((state) => state.auth)

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/strategies" element={<div>策略管理页面</div>} />
                  <Route path="/strategies/*" element={<div>策略管理详情页面</div>} />
                  <Route path="/backtest" element={<div>回测页面</div>} />
                  <Route path="/portfolio" element={<div>投资组合页面</div>} />
                  <Route path="/monitoring" element={<div>系统监控页面</div>} />
                  <Route path="/analytics" element={<div>数据分析页面</div>} />
                  <Route path="/risk-management" element={<div>风险管理页面</div>} />
                  <Route path="/settings" element={<div>设置页面</div>} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  )
}

export default App