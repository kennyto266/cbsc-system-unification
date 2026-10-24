import React, { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { motion } from 'framer-motion'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { toggleTheme } from '../../store/slices/uiSlice'

// Layout Components
import AppLayout from '../Layout'
import LoadingScreen from '../ui/LoadingScreen'

// Pages
import DashboardPage from '../../pages/dashboard/DashboardPage'
import ResponsiveDashboardPage from '../../pages/dashboard/ResponsiveDashboardPage'
import StrategiesPage from '../../pages/strategies/StrategiesPage'
import MonitoringPage from '../../pages/monitoring/MonitoringPage'
import AnalyticsPage from '../../pages/analytics/AnalyticsPage'
import SettingsPage from '../../pages/settings/SettingsPage'
import ProfilePage from '../../pages/profile/ProfilePage'
import IndicatorLibraryPage from '../../pages/technical-indicators/IndicatorLibraryPage'
import CBSCTabPage from '../../pages/dashboard/CBSCTabPage'

// Theme configuration
const themeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    colorInfo: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  algorithm: undefined, // Will be set based on theme mode
}

interface UnifiedDashboardProps {
  defaultPage?: string
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({ defaultPage = 'dashboard' }) => {
  const dispatch = useAppDispatch()
  const { themeMode, isLoading } = useAppSelector(state => state.ui)
  const { isAuthenticated } = useAppSelector(state => state.auth)
  const [mounted, setMounted] = useState(false)

  // Handle mounted state to avoid SSR mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  // Apply theme
  useEffect(() => {
    const root = document.documentElement
    if (themeMode === 'dark') {
      root.classList.add('dark')
      // Update Ant Design theme for dark mode
      // themeConfig.algorithm = theme.darkAlgorithm // Uncomment when antd theme is properly configured
    } else {
      root.classList.remove('dark')
      themeConfig.algorithm = undefined
    }
  }, [themeMode])

  // Show loading screen
  if (!mounted || isLoading) {
    return <LoadingScreen />
  }

  return (
    <ConfigProvider
      locale={zhCN}
      theme={themeConfig}
    >
      <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300`}>
        <AppLayout>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="w-full h-full"
          >
            <Routes>
              {/* Dashboard Routes */}
              <Route path="/" element={<ResponsiveDashboardPage />} />
              <Route path="/dashboard" element={<ResponsiveDashboardPage />} />
              <Route path="/dashboard/legacy" element={<DashboardPage />} />

              {/* Strategy Management Routes */}
              <Route path="/strategies/*" element={<StrategiesPage />} />

              {/* Technical Indicators Routes */}
              <Route path="/indicators/*" element={<IndicatorLibraryPage />} />

              {/* Monitoring Routes */}
              <Route path="/monitoring/*" element={<MonitoringPage />} />

              {/* Analytics Routes */}
              <Route path="/analytics/*" element={<AnalyticsPage />} />

              {/* CBSC Routes */}
              <Route path="/cbsc" element={<CBSCTabPage />} />

              {/* Settings Routes */}
              <Route path="/settings/*" element={<SettingsPage />} />

              {/* Profile Routes */}
              <Route path="/profile" element={<ProfilePage />} />
            </Routes>
          </motion.div>
        </AppLayout>
      </div>
    </ConfigProvider>
  )
}

export default UnifiedDashboard