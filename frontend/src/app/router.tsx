// CBSC Trading System - Unified Router Configuration
// Feature-based routing with lazy loading and protected routes

import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { ProtectedRoute } from '@/shared/components/ui/ProtectedRoute';
import { DashboardLayout } from '@/shared/components/layout/DashboardLayout';
import { PageLoading } from '@/shared/components/ui/PageLoading';

// Lazy load feature pages for code splitting
const DashboardPage = lazy(() =>
  import('@/features/dashboard/pages/DashboardPage')
);
const StrategyList = lazy(() =>
  import('@/features/strategies/pages/StrategyList')
);
const StrategyDetail = lazy(() =>
  import('@/features/strategies/pages/StrategyDetail')
);
const StrategyCreate = lazy(() =>
  import('@/features/strategies/pages/StrategyCreate')
);
const BacktestList = lazy(() =>
  import('@/features/backtest/pages/BacktestList')
);
const BacktestCreate = lazy(() =>
  import('@/features/backtest/pages/BacktestCreate')
);
const BacktestReport = lazy(() =>
  import('@/features/backtest/pages/BacktestReport')
);
const RealtimeDashboard = lazy(() =>
  import('@/features/realtime/pages/RealtimeDashboard')
);
const LoginPage = lazy(() =>
  import('@/features/auth/pages/LoginPage')
);

// Loading wrapper for lazy-loaded components
const LazyWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<PageLoading />}>{children}</Suspense>
);

// Route definitions with feature organization
export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <LazyWrapper>
        <LoginPage />
      </LazyWrapper>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <LazyWrapper>
            <DashboardPage />
          </LazyWrapper>
        ),
      },
      // Strategy Management Routes
      {
        path: 'strategies',
        children: [
          {
            index: true,
            element: (
              <LazyWrapper>
                <StrategyList />
              </LazyWrapper>
            ),
          },
          {
            path: ':id',
            element: (
              <LazyWrapper>
                <StrategyDetail />
              </LazyWrapper>
            ),
          },
          {
            path: 'new',
            element: (
              <LazyWrapper>
                <StrategyCreate />
              </LazyWrapper>
            ),
          },
        ],
      },
      // Backtest Routes
      {
        path: 'backtest',
        children: [
          {
            index: true,
            element: (
              <LazyWrapper>
                <BacktestList />
              </LazyWrapper>
            ),
          },
          {
            path: 'new',
            element: (
              <LazyWrapper>
                <BacktestCreate />
              </LazyWrapper>
            ),
          },
          {
            path: ':id',
            element: (
              <LazyWrapper>
                <BacktestReport />
              </LazyWrapper>
            ),
          },
        ],
      },
      // Realtime Data Routes
      {
        path: 'realtime',
        element: (
          <LazyWrapper>
            <RealtimeDashboard />
          </LazyWrapper>
        ),
      },
      // Catch all - redirect to dashboard
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

export default router;
