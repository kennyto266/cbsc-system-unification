import React, { useState, useEffect, ReactNode, useRef } from 'react'
import { Layout } from 'antd'
import { useTheme } from '../../contexts/ThemeContext'
import Sidebar from './Sidebar'
import Header from './Header'
import { useWindowSize } from '../../hooks/useWindowSize'

const { Content } = Layout

interface DashboardLayoutProps {
  children: ReactNode
  sidebarCollapsed?: boolean
  onSidebarToggle?: () => void
}

// Breakpoint configuration
const BREAKPOINTS = {
  mobile: 768,
  tablet: 1024,
  desktop: 1440,
  wide: 1920,
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  sidebarCollapsed: externalCollapsed,
  onSidebarToggle,
}) => {
  const { themeConfig } = useTheme()
  const { width } = useWindowSize()
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [isTablet, setIsTablet] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Determine if sidebar should be collapsed
  const sidebarCollapsed = externalCollapsed !== undefined ? externalCollapsed : internalCollapsed

  // Handle sidebar toggle
  const handleSidebarToggle = () => {
    if (onSidebarToggle) {
      onSidebarToggle()
    } else {
      setInternalCollapsed(!sidebarCollapsed)
    }
  }

  // Detect device type based on window size
  useEffect(() => {
    setIsMobile(width < BREAKPOINTS.mobile)
    setIsTablet(width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet)

    // Auto-collapse on mobile
    if (width < BREAKPOINTS.mobile && !sidebarCollapsed) {
      setInternalCollapsed(true)
    }
    // Auto-expand on desktop
    else if (width >= BREAKPOINTS.tablet && sidebarCollapsed && externalCollapsed === undefined) {
      setInternalCollapsed(false)
    }
  }, [width, sidebarCollapsed, externalCollapsed])

  // Handle click outside sidebar on mobile
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isMobile &&
        !sidebarCollapsed &&
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node)
      ) {
        setInternalCollapsed(true)
      }
    }

    if (isMobile) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isMobile, sidebarCollapsed])

  // Calculate sidebar width
  const sidebarWidth = isMobile ? '100%' : sidebarCollapsed ? '80px' : '280px'

  // Calculate layout styles
  const layoutStyles: React.CSSProperties = {
    minHeight: '100vh',
    background: themeConfig.colors.background,
    transition: 'all 0.3s ease',
  }

  const contentStyles: React.CSSProperties = {
    marginLeft: isMobile ? 0 : sidebarCollapsed ? '80px' : '280px',
    padding: 0,
    background: themeConfig.colors.background,
    transition: 'all 0.3s ease',
    position: 'relative',
    overflow: 'hidden',
  }

  const mobileOverlayStyles: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 999,
    display: isMobile && !sidebarCollapsed ? 'block' : 'none',
  }

  return (
    <>
      {/* Mobile overlay */}
      <div style={mobileOverlayStyles} onClick={handleSidebarToggle} />

      <Layout style={layoutStyles}>
        {/* Sidebar */}
        <div
          ref={sidebarRef}
          style={{
            position: isMobile ? 'fixed' : 'relative',
            top: 0,
            left: 0,
            height: '100vh',
            width: sidebarWidth,
            background: themeConfig.colors.surface,
            borderRight: `1px solid ${themeConfig.colors.border}`,
            zIndex: isMobile ? 1000 : 1,
            transition: 'all 0.3s ease',
            transform: isMobile && sidebarCollapsed ? 'translateX(-100%)' : 'translateX(0)',
          }}
        >
          <Sidebar
            collapsed={sidebarCollapsed}
            onToggle={handleSidebarToggle}
            isMobile={isMobile}
          />
        </div>

        {/* Main content area */}
        <div style={contentStyles}>
          {/* Header */}
          <Header
            onMenuClick={isMobile ? handleSidebarToggle : undefined}
            sidebarCollapsed={sidebarCollapsed}
          />

          {/* Page content */}
          <Content
            style={{
              padding: isMobile ? '16px' : '24px',
              background: themeConfig.colors.background,
              minHeight: 'calc(100vh - 64px)',
              overflowY: 'auto',
            }}
          >
            {children}
          </Content>
        </div>
      </Layout>
    </>
  )
}

export default DashboardLayout