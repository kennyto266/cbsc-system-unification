import React, { useEffect } from 'react'
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import { useLayout } from '@/components/Layout'
import type { BreadcrumbItem } from '@/types'

// Lazy load pages for code splitting
const Dashboard = React.lazy(() => import('@/pages/Dashboard'))
const UserList = React.lazy(() => import('@/pages/UserList'))
const UserRoles = React.lazy(() => import('@/pages/UserRoles'))
const ReportsAnalytics = React.lazy(() => import('@/pages/ReportsAnalytics'))
const ReportsActivity = React.lazy(() => import('@/pages/ReportsActivity'))
const Calendar = React.lazy(() => import('@/pages/Calendar'))
const Settings = React.lazy(() => import('@/pages/Settings'))
const NotFound = React.lazy(() => import('@/pages/NotFound'))

// Wrapper component to handle breadcrumbs
const RouteWrapper: React.FC<{
  children: React.ReactNode
  breadcrumbs: BreadcrumbItem[]
  activeItemId: string
}> = ({ children, breadcrumbs, activeItemId }) => {
  const { setBreadcrumbs, setActiveItem } = useLayout()
  const location = useLocation()

  useEffect(() => {
    setBreadcrumbs(breadcrumbs)
    setActiveItem(activeItemId)
  }, [location.pathname, breadcrumbs, activeItemId, setBreadcrumbs, setActiveItem])

  return <>{children}</>
}

const AppRoutes: React.FC = () => {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Routes>
        {/* Default route redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard route */}
        <Route
          path="/dashboard"
          element={
            <RouteWrapper
              breadcrumbs={[{ label: 'Dashboard' }]}
              activeItemId="dashboard"
            >
              <Dashboard />
            </RouteWrapper>
          }
        />

        {/* User Management routes */}
        <Route
          path="/users/list"
          element={
            <RouteWrapper
              breadcrumbs={[
                { label: 'User Management' },
                { label: 'All Users' },
              ]}
              activeItemId="users-list"
            >
              <UserList />
            </RouteWrapper>
          }
        />
        <Route
          path="/users/roles"
          element={
            <RouteWrapper
              breadcrumbs={[
                { label: 'User Management' },
                { label: 'Roles & Permissions' },
              ]}
              activeItemId="users-roles"
            >
              <UserRoles />
            </RouteWrapper>
          }
        />

        {/* Reports routes */}
        <Route
          path="/reports/analytics"
          element={
            <RouteWrapper
              breadcrumbs={[
                { label: 'Reports' },
                { label: 'Analytics' },
              ]}
              activeItemId="reports-analytics"
            >
              <ReportsAnalytics />
            </RouteWrapper>
          }
        />
        <Route
          path="/reports/activity"
          element={
            <RouteWrapper
              breadcrumbs={[
                { label: 'Reports' },
                { label: 'Activity Logs' },
              ]}
              activeItemId="reports-activity"
            >
              <ReportsActivity />
            </RouteWrapper>
          }
        />

        {/* Calendar route */}
        <Route
          path="/calendar"
          element={
            <RouteWrapper
              breadcrumbs={[{ label: 'Calendar' }]}
              activeItemId="calendar"
            >
              <Calendar />
            </RouteWrapper>
          }
        />

        {/* Settings route */}
        <Route
          path="/settings"
          element={
            <RouteWrapper
              breadcrumbs={[{ label: 'Settings' }]}
              activeItemId="settings"
            >
              <Settings />
            </RouteWrapper>
          }
        />

        {/* 404 route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </React.Suspense>
  )
}

export default AppRoutes