import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { Layout, Spin } from 'antd'
import { Helmet } from 'react-helmet-async'

// Components
import UnifiedDashboard from './components/UnifiedDashboard/UnifiedDashboard'
import AuthPage from './pages/auth/AuthPage'
import ErrorPage from './pages/error/ErrorPage'
import ProtectedRoute from './components/auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import LoadingScreen from './components/ui/LoadingScreen'

// Pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import StrategiesPage from './pages/strategies/StrategiesPage'
import StrategyDetailPage from './pages/strategies/StrategyDetailPage'
import CreateStrategyPage from './pages/strategies/CreateStrategyPage'
import MonitoringPage from './pages/monitoring/MonitoringPage'
import AnalyticsPage from './pages/analytics/AnalyticsPage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'
import ProfilePage from './pages/profile/ProfilePage'
import IndicatorLibraryPage from './pages/technical-indicators/IndicatorLibraryPage'
import Showcase from './pages/Showcase'
import NotFoundPage from './pages/error/NotFoundPage'
import ResponsiveDashboardPage from './pages/dashboard/ResponsiveDashboardPage'
import DashboardExample from './pages/dashboard/DashboardExample'

// Hooks
import { useAuth } from '@hooks/useAuth'
import { useWebSocket } from '@hooks/useWebSocket'

// Store
import type { RootState } from '@store/index'

const { Content } = Layout

const App: React.FC = () => {
  const dispatch = useDispatch()
  // Personal use: skip authentication entirely
  const isAuthenticated = true
  const isLoading = false
  const user = { username: 'admin', name: 'Admin' }
  const { isConnected } = useWebSocket()

  // Show loading screen while checking authentication
  if (isLoading) {
    return <LoadingScreen />
  }

  return (
    <>
      <Helmet>
        <title>CBSC Unified Dashboard</title>
        <meta name="description" content="现代化量化交易策略管理平台" />
        <meta name="keywords" content="CBSC,量化交易,策略管理,Dashboard,实时监控" />
        <meta name="author" content="CBSC Team" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:title" content="CBSC Unified Dashboard" />
        <meta property="og:description" content="现代化量化交易策略管理平台" />

        {/* Twitter */}
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:title" content="CBSC Unified Dashboard" />
        <meta property="twitter:description" content="现代化量化交易策略管理平台" />

        {/* PWA Theme Color */}
        <meta name="theme-color" content="#1890ff" />

        {/* Viewport and mobile optimization */}
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />

        {/* Favicon */}
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />

        {/* Manifest */}
        <link rel="manifest" href="/manifest.json" />

        {/* Preload critical resources */}
        <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="" />

        {/* DNS prefetch for external resources */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//api.cbsc.com" />
      </Helmet>

      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <LoginPage />
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <RegisterPage />
            )
          }
        />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        {/* Component Showcase */}
        <Route path="/showcase" element={<Showcase />} />

        {/* Responsive Dashboard Example */}
        <Route
          path="/responsive-dashboard"
          element={
            <ProtectedRoute>
              <ResponsiveDashboardPage />
            </ProtectedRoute>
          }
        />

        {/* Dashboard Grid Example */}
        <Route
          path="/dashboard-example"
          element={
            <ProtectedRoute>
              <DashboardExample />
            </ProtectedRoute>
          }
        />

        {/* Unified Dashboard Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <UnifiedDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="dashboard" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/strategies"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="strategies" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/monitoring"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="monitoring" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="analytics" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="settings" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="profile" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/indicators"
          element={
            <ProtectedRoute>
              <UnifiedDashboard defaultPage="indicators" />
            </ProtectedRoute>
          }
        />

        {/* Legacy Protected routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Content style={{ margin: '24px', padding: '24px', background: '#fff', borderRadius: '8px' }}>
                  <Routes>
                    {/* Strategy Management */}
                    <Route path="/strategies/new" element={<CreateStrategyPage />} />
                    <Route path="/strategies/:id" element={<StrategyDetailPage />} />
                    <Route path="/strategies/:id/edit" element={<CreateStrategyPage />} />

                    {/* Monitoring */}
                    <Route path="/monitoring/system" element={<MonitoringPage />} />
                    <Route path="/monitoring/strategies" element={<MonitoringPage />} />
                    <Route path="/monitoring/alerts" element={<MonitoringPage />} />

                    {/* Analytics */}
                    <Route path="/analytics/portfolio" element={<AnalyticsPage />} />
                    <Route path="/analytics/strategies" element={<AnalyticsPage />} />
                    <Route path="/analytics/market" element={<AnalyticsPage />} />
                    <Route path="/analytics/risk" element={<AnalyticsPage />} />

                    {/* Reports */}
                    <Route path="/reports" element={<ReportsPage />} />
                    <Route path="/reports/generate" element={<ReportsPage />} />
                    <Route path="/reports/history" element={<ReportsPage />} />

                    {/* Settings */}
                    <Route path="/settings/security" element={<SettingsPage />} />
                    <Route path="/settings/preferences" element={<SettingsPage />} />
                    <Route path="/settings/api-keys" element={<SettingsPage />} />

                    {/* 404 Not Found */}
                    <Route path="*" element={<NotFoundPage />} />
                  </Routes>
                </Content>
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>

      {/* Global loading indicator */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          backgroundColor: '#f0f0f0',
          zIndex: 9999,
          display: 'none',
        }}
        id="global-loading-bar"
      >
        <div
          style={{
            height: '100%',
            backgroundColor: '#1890ff',
            width: '0%',
            transition: 'width 0.3s ease',
          }}
          id="global-loading-progress"
        />
      </div>

      {/* WebSocket connection indicator */}
      <div
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: isConnected ? '#52c41a' : '#f5222d',
          zIndex: 1000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          cursor: 'pointer',
        }}
        title={isConnected ? 'WebSocket已连接' : 'WebSocket未连接'}
        onClick={() => {
          // Show connection status details
          console.log('WebSocket status:', {
            connected: isConnected,
            timestamp: new Date().toISOString(),
          })
        }}
      />

      {/* Performance monitoring for development */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            left: '20px',
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            zIndex: 1000,
          }}
        >
          <div>WebSocket: {isConnected ? '✅' : '❌'}</div>
          <div>User: {user ? user.username : 'Guest'}</div>
          <div>Auth: {isAuthenticated ? '✅' : '❌'}</div>
        </div>
      )}
    </>
  )
}

export default App