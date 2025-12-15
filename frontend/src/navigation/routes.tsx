import React from 'react'
import { Navigate } from 'react-router-dom'

// Auth protected route wrapper
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // TODO: Implement authentication check
  // const isAuthenticated = useAppSelector(state => state.auth.isAuthenticated)
  const isAuthenticated = true // Temporary

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  return <>{children}</>
}

// Public route wrapper (redirect if authenticated)
export const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // TODO: Implement authentication check
  // const isAuthenticated = useAppSelector(state => state.auth.isAuthenticated)
  const isAuthenticated = false // Temporary

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

// Lazy load components for code splitting
const Dashboard = React.lazy(() => import('../pages/Dashboard'))
const StrategyList = React.lazy(() => import('../pages/strategies/StrategyList'))
const StrategyCreate = React.lazy(() => import('../pages/strategies/StrategyCreate'))
const StrategyTemplates = React.lazy(() => import('../pages/strategies/StrategyTemplates'))
const StrategyAnalysis = React.lazy(() => import('../pages/strategies/StrategyAnalysis'))
const Backtest = React.lazy(() => import('../pages/Backtest'))
const Portfolio = React.lazy(() => import('../pages/Portfolio'))
const UserList = React.lazy(() => import('../pages/users/UserList'))
const UserRoles = React.lazy(() => import('../pages/users/UserRoles'))
const Settings = React.lazy(() => import('../pages/Settings'))
const Profile = React.lazy(() => import('../pages/Profile'))
const Login = React.lazy(() => import('../pages/auth/Login'))
const Register = React.lazy(() => import('../pages/auth/Register'))

export const routeConfig = {
  protected: [
    {
      path: '/',
      element: <Navigate to="/dashboard" replace />,
    },
    {
      path: '/dashboard',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Dashboard />
          </React.Suspense>
        </ProtectedRoute>
      ),
    },
    {
      path: '/strategies/*',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <StrategyList />
          </React.Suspense>
        </ProtectedRoute>
      ),
      children: [
        {
          path: 'list',
          element: <StrategyList />,
        },
        {
          path: 'create',
          element: <StrategyCreate />,
        },
        {
          path: 'templates',
          element: <StrategyTemplates />,
        },
        {
          path: 'analysis',
          element: <StrategyAnalysis />,
        },
      ],
    },
    {
      path: '/backtest',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Backtest />
          </React.Suspense>
        </ProtectedRoute>
      ),
    },
    {
      path: '/portfolio',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Portfolio />
          </React.Suspense>
        </ProtectedRoute>
      ),
    },
    {
      path: '/users/*',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <UserList />
          </React.Suspense>
        </ProtectedRoute>
      ),
      children: [
        {
          path: 'list',
          element: <UserList />,
        },
        {
          path: 'roles',
          element: <UserRoles />,
        },
      ],
    },
    {
      path: '/settings',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Settings />
          </React.Suspense>
        </ProtectedRoute>
      ),
    },
    {
      path: '/profile',
      element: (
        <ProtectedRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Profile />
          </React.Suspense>
        </ProtectedRoute>
      ),
    },
  ],
  public: [
    {
      path: '/auth/login',
      element: (
        <PublicRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Login />
          </React.Suspense>
        </PublicRoute>
      ),
    },
    {
      path: '/auth/register',
      element: (
        <PublicRoute>
          <React.Suspense fallback={<div>Loading...</div>}>
            <Register />
          </React.Suspense>
        </PublicRoute>
      ),
    },
  ],
}