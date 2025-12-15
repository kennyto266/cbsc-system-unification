import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import Footer from './Footer'
import Breadcrumb from './Breadcrumb'
import type { LayoutContextType, SidebarItem, BreadcrumbItem, User } from '@/types'
import { useResponsive } from '@/utils/useResponsive'

// Create layout context
const LayoutContext = createContext<LayoutContextType | undefined>(undefined)

// Layout Provider component
export const LayoutProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeItemId, setActiveItem] = useState('dashboard')
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([])
  const deviceType = useResponsive()

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    if (deviceType === 'mobile') {
      setSidebarCollapsed(true)
    }
  }, [deviceType])

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev)
  }, [])

  const handleSetBreadcrumbs = useCallback((items: BreadcrumbItem[]) => {
    setBreadcrumbs(items)
  }, [])

  const value: LayoutContextType = {
    isSidebarCollapsed,
    toggleSidebar,
    activeItemId,
    setActiveItem,
    breadcrumbs,
    setBreadcrumbs: handleSetBreadcrumbs,
  }

  return (
    <LayoutContext.Provider value={value}>
      {children}
    </LayoutContext.Provider>
  )
}

// Hook to use layout context
export const useLayout = () => {
  const context = useContext(LayoutContext)
  if (!context) {
    throw new Error('useLayout must be used within a LayoutProvider')
  }
  return context
}

// Sidebar navigation items
const navigationItems: SidebarItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: require('@heroicons/react/24/outline').ChartBarIcon,
    href: '/dashboard',
  },
  {
    id: 'users',
    label: 'User Management',
    icon: require('@heroicons/react/24/outline').UserGroupIcon,
    href: '/users',
    badge: 5,
    children: [
      {
        id: 'users-list',
        label: 'All Users',
        icon: require('@heroicons/react/24/outline').UserGroupIcon,
        href: '/users/list',
      },
      {
        id: 'users-roles',
        label: 'Roles & Permissions',
        icon: require('@heroicons/react/24/outline').ShieldCheckIcon,
        href: '/users/roles',
      },
    ],
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: require('@heroicons/react/24/outline').DocumentTextIcon,
    href: '/reports',
    children: [
      {
        id: 'reports-analytics',
        label: 'Analytics',
        icon: require('@heroicons/react/24/outline').ChartBarIcon,
        href: '/reports/analytics',
      },
      {
        id: 'reports-activity',
        label: 'Activity Logs',
        icon: require('@heroicons/react/24/outline').DocumentTextIcon,
        href: '/reports/activity',
      },
    ],
  },
  {
    id: 'calendar',
    label: 'Calendar',
    icon: require('@heroicons/react/24/outline').CalendarIcon,
    href: '/calendar',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: require('@heroicons/react/24/outline').CogIcon,
    href: '/settings',
  },
]

// Main Layout component
const Layout: React.FC<{ user?: User }> = ({ user }) => {
  const deviceType = useResponsive()
  const {
    isSidebarCollapsed,
    toggleSidebar,
    activeItemId,
    setActiveItem,
    breadcrumbs,
  } = useLayout()

  // Mobile sidebar overlay
  if (deviceType === 'mobile' && !isSidebarCollapsed) {
    return (
      <>
        <div className="fixed inset-0 z-50">
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={toggleSidebar}
          />

          {/* Mobile sidebar */}
          <Sidebar
            isCollapsed={false}
            onToggle={toggleSidebar}
            items={navigationItems}
            activeItem={activeItemId}
            onItemClick={setActiveItem}
          />
        </div>
      </>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Desktop sidebar */}
      {deviceType !== 'mobile' && (
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggle={toggleSidebar}
          items={navigationItems}
          activeItem={activeItemId}
          onItemClick={setActiveItem}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onSidebarToggle={toggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
          user={user}
        />

        {/* Breadcrumb */}
        <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 sm:px-6 lg:px-8 py-3">
          <Breadcrumb items={breadcrumbs} />
        </div>

        {/* Page content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
          <Outlet />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  )
}

export default Layout