import React from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Spin } from 'antd'
import DashboardLayout from '../components/layout/DashboardLayout'

// Lazy load page components for better performance
const DashboardPage = lazy(() => import('../pages/dashboard/DashboardPage'))
const StrategiesPage = lazy(() => import('../pages/strategies/StrategiesPage'))
const PersonalStrategiesPage = lazy(() => import('../pages/strategies/PersonalStrategiesPage'))
const CBSCStrategiesPage = lazy(() => import('../pages/strategies/CBSCStrategiesPage'))
const TechnicalIndicatorsPage = lazy(() => import('../pages/indicators/TechnicalIndicatorsPage'))
const PortfolioPage = lazy(() => import('../pages/portfolio/PortfolioPage'))
const MarketDataPage = lazy(() => import('../pages/market/MarketDataPage'))
const RealTimeDataPage = lazy(() => import('../pages/market/RealTimeDataPage'))
const MarketAnalysisPage = lazy(() => import('../pages/market/MarketAnalysisPage'))
const CBSCDataPage = lazy(() => import('../pages/market/CBSCDataPage'))
const HistoryPage = lazy(() => import('../pages/history/HistoryPage'))
const ReportsPage = lazy(() => import('../pages/reports/ReportsPage'))
const AlertsPage = lazy(() => import('../pages/alerts/AlertsPage'))
const TeamPage = lazy(() => import('../pages/team/TeamPage'))
const ProfilePage = lazy(() => import('../pages/profile/ProfilePage'))
const SettingsPage = lazy(() => import('../pages/settings/SettingsPage'))

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
          {
            path: 'personal',
            element: (
              <Suspense fallback={<PageLoading />}>
                <PersonalStrategiesPage />
              </Suspense>
            ),
          },
          {
            path: 'cbsc',
            element: (
              <Suspense fallback={<PageLoading />}>
                <CBSCStrategiesPage />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: 'indicators',
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <TechnicalIndicatorsPage />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: 'portfolio',
        element: (
          <Suspense fallback={<PageLoading />}>
            <PortfolioPage />
          </Suspense>
        ),
      },
      {
        path: 'market',
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <MarketDataPage />
              </Suspense>
            ),
          },
          {
            path: 'realtime',
            element: (
              <Suspense fallback={<PageLoading />}>
                <RealTimeDataPage />
              </Suspense>
            ),
          },
          {
            path: 'analysis',
            element: (
              <Suspense fallback={<PageLoading />}>
                <MarketAnalysisPage />
              </Suspense>
            ),
          },
          {
            path: 'cbsc',
            element: (
              <Suspense fallback={<PageLoading />}>
                <CBSCDataPage />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: 'history',
        element: (
          <Suspense fallback={<PageLoading />}>
            <HistoryPage />
          </Suspense>
        ),
      },
      {
        path: 'reports',
        element: (
          <Suspense fallback={<PageLoading />}>
            <ReportsPage />
          </Suspense>
        ),
      },
      {
        path: 'alerts',
        element: (
          <Suspense fallback={<PageLoading />}>
            <AlertsPage />
          </Suspense>
        ),
      },
      {
        path: 'team',
        element: (
          <Suspense fallback={<PageLoading />}>
            <TeamPage />
          </Suspense>
        ),
      },
      {
        path: 'profile',
        element: (
          <Suspense fallback={<PageLoading />}>
            <ProfilePage />
          </Suspense>
        ),
      },
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