import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout/Layout'
import Dashboard from './pages/Dashboard/index'

// Strategy pages
import StrategiesListPage from './pages/strategies/StrategiesListPage'
import CreateStrategyPage from './pages/strategies/CreateStrategyPage'
import StrategyTemplatesPage from './pages/strategies/StrategyTemplatesPage'
import StrategyAnalysisPage from './pages/strategies/StrategyAnalysisPage'

// User management pages
import UserManagementPage from './pages/users/UserManagementPage'
import UserListPage from './pages/users/UserListPage'
import RolePermissionsPage from './pages/users/RolePermissionsPage'

// Backtest page
import BacktestMockPage from './pages/backtest/BacktestMockPage'

// Non-price data pages
import NonPriceStrategyManagement from './pages/NonPriceStrategyManagement'
import EconomicDataDashboard from './pages/EconomicDataDashboard'

// Futu account management
import FutuAccountManagement from './pages/FutuAccountManagement'

// Settings page
import SettingsPage from './pages/SettingsPage'

// 實時監控頁面
const RealtimeMonitoring = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-800 mb-4">實時監控</h1>
    <div className="mt-6 bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-700 mb-4">策略執行狀態</h2>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
          <span className="font-medium text-gray-700">策略 #001</span>
          <span className="px-3 py-1 bg-green-500 text-white rounded-full text-sm">運行中</span>
        </div>
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
          <span className="font-medium text-gray-700">策略 #002</span>
          <span className="px-3 py-1 bg-blue-500 text-white rounded-full text-sm">待執行</span>
        </div>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <span className="font-medium text-gray-700">策略 #003</span>
          <span className="px-3 py-1 bg-gray-500 text-white rounded-full text-sm">已停止</span>
        </div>
      </div>
    </div>
  </div>
)

// Simple dashboard without authentication
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />

          {/* Strategy routes */}
          <Route path="strategies" element={<StrategiesListPage />} />
          <Route path="strategies/list" element={<StrategiesListPage />} />
          <Route path="strategies/create" element={<CreateStrategyPage />} />
          <Route path="strategies/templates" element={<StrategyTemplatesPage />} />
          <Route path="strategies/analysis" element={<StrategyAnalysisPage />} />

          {/* User management routes */}
          <Route path="users" element={<UserManagementPage />} />
          <Route path="users/list" element={<UserListPage />} />
          <Route path="users/roles" element={<RolePermissionsPage />} />

          {/* Other routes */}
          <Route path="backtest" element={<BacktestMockPage />} />
          <Route path="portfolio" element={<Dashboard />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="monitoring" element={<RealtimeMonitoring />} />

          {/* Non-price data routes */}
          <Route path="non-price-strategies" element={<NonPriceStrategyManagement />} />
          <Route path="economic-data" element={<EconomicDataDashboard />} />

          {/* Futu account management */}
          <Route path="futu-accounts" element={<FutuAccountManagement />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App
