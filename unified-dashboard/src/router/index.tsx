import React from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Spin } from 'antd'
import DashboardLayout from '../components/layout/DashboardLayout'
import ComingSoon from '../components/common/ComingSoon'

// Lazy load page components for better performance
const DashboardPage = lazy(() => import('../pages/dashboard/DashboardPage'))
const StrategiesPage = lazy(() => import('../pages/strategies/StrategiesPage'))
const ProfilePage = lazy(() => import('../pages/profile/ProfilePage'))
const SettingsPage = lazy(() => import('../pages/settings/SettingsPage'))

// Pages that don't exist yet — use ComingSoon placeholder instead of
// broken lazy imports (which cause "thenable.then is not a function")
const PersonalStrategiesPage = () => <ComingSoon title="個人策略管理" />
const CBSCStrategiesPage = () => <ComingSoon title="CBSC 策略" />
const TechnicalIndicatorsPage = () => <ComingSoon title="技術指標" />
const PortfolioPage = () => <ComingSoon title="投資組合" />
const MarketDataPage = () => <ComingSoon title="市場數據" />
const RealTimeDataPage = () => <ComingSoon title="實時數據" />
const MarketAnalysisPage = () => <ComingSoon title="市場分析" />
const CBSCDataPage = () => <ComingSoon title="CBSC 數據" />
const HistoryPage = () => <ComingSoon title="歷史記錄" />
const ReportsPage = () => <ComingSoon title="報告" />
const AlertsPage = () => <ComingSoon title="警報" />
const TeamPage = () => <ComingSoon title="團隊" />

// Loading component
const PageLoading: React.FC = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '200px'
  }}>
    <Spin size="large" tip="載入中..." />
  </div>
)

// Error boundary fallback
const ErrorFallback: React.FC = () => (
  <div style={{
    padding: '50px',
    textAlign: 'center',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  }}>
    <h1>頁面載入失敗</h1>
    <p>請重新整理頁面或聯繫系統管理員</p>
  </div>
)

// Route configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardLayout />,
    errorElement: <ErrorFallback />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageLoading />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: 'strategies',
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <StrategiesPage />
              </Suspense>
            ),
          },
          { path: 'personal', element: <PersonalStrategiesPage /> },
          { path: 'cbsc', element: <CBSCStrategiesPage /> },
        ],
      },
      {
        path: 'indicators',
        children: [
          { index: true, element: <TechnicalIndicatorsPage /> },
        ],
      },
      { path: 'portfolio', element: <PortfolioPage /> },
      {
        path: 'market',
        children: [
          { index: true, element: <MarketDataPage /> },
          { path: 'realtime', element: <RealTimeDataPage /> },
          { path: 'analysis', element: <MarketAnalysisPage /> },
          { path: 'cbsc', element: <CBSCDataPage /> },
        ],
      },
      { path: 'history', element: <HistoryPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'alerts', element: <AlertsPage /> },
      { path: 'team', element: <TeamPage /> },
      { path: 'profile', element: <ProfilePage /> },
      {
        path: 'settings',
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <SettingsPage />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },
  // 404 page
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])

// Router provider component
const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />
}

export default AppRouter
