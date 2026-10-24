import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Layout } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './Header'
import Sidebar from './Sidebar'
import Footer from './Footer'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { toggleSidebar } from '../../store/slices/uiSlice'

const { Content } = Layout

interface LayoutProps {
  children: React.ReactNode
  showFooter?: boolean
}

const AppLayout: React.FC<LayoutProps> = ({ children, showFooter = true }) => {
  const location = useLocation()
  const dispatch = useAppDispatch()
  const { sidebarCollapsed } = useAppSelector(state => state.ui)
  const [isMobile, setIsMobile] = useState(false)

  // Handle responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      // Auto-collapse sidebar on mobile
      if (mobile && !sidebarCollapsed) {
        dispatch(toggleSidebar())
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [dispatch, sidebarCollapsed])

  const handleSidebarToggle = () => {
    dispatch(toggleSidebar())
  }

  // Don't show layout on auth pages
  const noLayoutRoutes = ['/login', '/register', '/forgot-password']
  const shouldShowLayout = !noLayoutRoutes.includes(location.pathname)

  if (!shouldShowLayout) {
    return <>{children}</>
  }

  return (
    <Layout className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header - Fixed at top */}
      <Header
        collapsed={sidebarCollapsed}
        onToggle={handleSidebarToggle}
      />

      {/* Main Layout with Sidebar */}
      <Layout className="pt-16">
        {/* Sidebar - Fixed on desktop, overlay on mobile */}
        <AnimatePresence>
          {(!isMobile || !sidebarCollapsed) && (
            <>
              {isMobile && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 bg-black bg-opacity-50 z-30"
                  onClick={handleSidebarToggle}
                />
              )}
              <Sidebar
                collapsed={sidebarCollapsed}
                onCollapse={handleSidebarToggle}
              />
            </>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <Layout
          className={`transition-all duration-300 ${
            sidebarCollapsed && !isMobile ? 'ml-0' : ''
          }`}
          style={{
            marginLeft: !isMobile ? (sidebarCollapsed ? 80 : 256) : 0,
          }}
        >
          <Content className="min-h-screen">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="p-4 lg:p-6"
            >
              {children}
            </motion.div>
          </Content>

          {/* Footer - Only show on desktop and specific pages */}
          {showFooter && !isMobile && <Footer />}
        </Layout>
      </Layout>
    </Layout>
  )
}

export default AppLayout