import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'

import { Layout } from '@/components/layout'
import { AuthGuard } from '@/components/auth'
import { DashboardPage } from '@/pages/dashboard'
import { StrategiesPage } from '@/pages/strategies'
import { AnalyticsPage } from '@/pages/analytics'
import { SettingsPage } from '@/pages/settings'
import { LoginPage } from '@/pages/auth'
import { NotFoundPage } from '@/pages/not-found'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

import type { RootState } from '@/store'

function App() {
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth)

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <Routes>
      {/* Auth routes */}
      <Route
        path="/auth/*"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
        }
      />

      {/* Protected routes */}
      <Route
        path="/*"
        element={
          <AuthGuard>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/strategies/*" element={<StrategiesPage />} />
                <Route path="/analytics/*" element={<AnalyticsPage />} />
                <Route path="/settings/*" element={<SettingsPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Layout>
          </AuthGuard>
        }
      />
    </Routes>
  )
}

export default App