import { Routes, Route, Navigate } from 'react-router-dom'
import ResponsiveLayout from './components/Layout/MainLayout'
import Dashboard from './pages/Dashboard/index'
import Strategies from './pages/Strategies/index'
import Users from './pages/Users/index'
import Portfolio from './pages/Portfolio/index'
import Backtest from './pages/Backtest/index'
import Monitoring from './pages/Monitoring/index'
import Analytics from './pages/Analytics/index'
import RiskManagement from './pages/RiskManagement/index'
import Settings from './pages/Settings/index'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

// Removed authentication - direct access to all pages
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <ToastContainer />
      <Routes>
        <Route path="/" element={<ResponsiveLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="strategies/*" element={<Strategies />} />
          <Route path="users/*" element={<Users />} />
          <Route path="portfolio/*" element={<Portfolio />} />
          <Route path="backtest/*" element={<Backtest />} />
          <Route path="monitoring/*" element={<Monitoring />} />
          <Route path="analytics/*" element={<Analytics />} />
          <Route path="risk-management/*" element={<RiskManagement />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App
