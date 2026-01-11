import React, { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { message } from 'antd'
import { routes, menuConfig } from './routes'
import { useAppSelector, useAppDispatch } from '../hooks/redux'
import { setUserPermissions } from '../store/slices/authSlice'

interface NavigationContextType {
  // Navigation state
  currentPath: string
  breadcrumbs: BreadcrumbItem[]
  canAccess: (path: string) => boolean

  // Navigation actions
  navigate: (path: string) => void
  goBack: () => void
  goForward: () => void

  // Menu state
  menuItems: MenuItem[]
  quickAccessItems: QuickAccessItem[]

  // Route utilities
  getRouteMeta: (path: string) => RouteMeta | undefined
  isRouteActive: (path: string) => boolean
}

interface BreadcrumbItem {
  title: string
  path: string
  icon?: React.ReactNode
}

interface MenuItem {
  key: string
  title: string
  icon: string
  permission: string[]
  children?: MenuItem[]
  badge?: string
}

interface QuickAccessItem {
  key: string
  title: string
  icon: string
  path: string
  permission: string[]
}

interface RouteMeta {
  title: string
  requiresAuth?: boolean
  keepAlive?: boolean
  permission?: string[]
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined)

export const useNavigation = () => {
  const context = useContext(NavigationContext)
  if (!context) {
    throw new Error('useNavigation must be used within NavigationProvider')
  }
  return context
}

const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useAppDispatch()
  const { isAuthenticated, user, permissions = [] } = useAppSelector(state => state.auth)

  const [currentPath, setCurrentPath] = useState(location.pathname)
  const [history, setHistory] = useState<string[]>([location.pathname])
  const [historyIndex, setHistoryIndex] = useState(0)

  // Update current path when location changes
  useEffect(() => {
    setCurrentPath(location.pathname)

    // Update navigation history
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(location.pathname)
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)

    // Update document title
    const route = routes.find(r => r.path === location.pathname)
    if (route?.meta?.title) {
      document.title = `${route.meta.title} - CBSC Dashboard`
    }
  }, [location.pathname])

  // Check if user has permission to access a route
  const canAccess = (path: string): boolean => {
    if (!isAuthenticated) {
      // Only allow public routes
      const publicRoutes = ['/login', '/register', '/forgot-password']
      return publicRoutes.includes(path)
    }

    const route = routes.find(r => r.path === path)
    if (!route?.meta?.requiresAuth) return true

    const requiredPermissions = route.meta.permission || []
    if (requiredPermissions.length === 0) return true

    return requiredPermissions.every(permission => permissions.includes(permission))
  }

  // Enhanced navigate with permission check
  const handleNavigate = (path: string) => {
    if (canAccess(path)) {
      navigate(path)
    } else {
      message.error('您没有权限访问该页面')
      if (!isAuthenticated) {
        navigate('/login')
      }
    }
  }

  // Navigation history controls
  const goBack = () => {
    if (historyIndex > 0) {
      const previousPath = history[historyIndex - 1]
      setHistoryIndex(historyIndex - 1)
      navigate(previousPath)
    }
  }

  const goForward = () => {
    if (historyIndex < history.length - 1) {
      const nextPath = history[historyIndex + 1]
      setHistoryIndex(historyIndex + 1)
      navigate(nextPath)
    }
  }

  // Generate breadcrumbs from current path
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const segments = currentPath.split('/').filter(Boolean)
    const breadcrumbs: BreadcrumbItem[] = []

    let currentPath = ''
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const isLast = index === segments.length - 1

      // Handle numeric IDs
      const isNumeric = /^\d+$/.test(segment)
      const title = isNumeric ? `详情 #${segment}` : segment

      breadcrumbs.push({
        title,
        path: isLast ? currentPath : '',
      })
    })

    return breadcrumbs
  }

  // Get route metadata
  const getRouteMeta = (path: string): RouteMeta | undefined => {
    return routes.find(r => r.path === path)?.meta
  }

  // Check if route is active
  const isRouteActive = (path: string): boolean => {
    if (path === currentPath) return true
    return currentPath.startsWith(path + '/')
  }

  // Filter menu items based on permissions
  const filterMenuByPermissions = (items: MenuItem[]): MenuItem[] => {
    return items.filter(item => {
      // Check item permissions
      if (item.permission.length > 0) {
        const hasPermission = item.permission.every(p => permissions.includes(p))
        if (!hasPermission) return false
      }

      // Filter children if exist
      if (item.children) {
        item.children = filterMenuByPermissions(item.children)
        // Only show parent if it has visible children or no permission required
        if (item.children.length === 0 && item.permission.length > 0) {
          return false
        }
      }

      return true
    })
  }

  // Filter quick access items
  const filterQuickAccessByPermissions = (items: QuickAccessItem[]): QuickAccessItem[] => {
    return items.filter(item => {
      if (item.permission.length === 0) return true
      return item.permission.every(p => permissions.includes(p))
    })
  }

  const value: NavigationContextType = {
    currentPath,
    breadcrumbs: generateBreadcrumbs(),
    canAccess,
    navigate: handleNavigate,
    goBack,
    goForward,
    menuItems: filterMenuByPermissions(menuConfig),
    quickAccessItems: filterQuickAccessByPermissions([
      {
        key: 'create-strategy',
        title: '新建策略',
        icon: 'RocketOutlined',
        path: '/strategies/create',
        permission: ['strategy:create'],
      },
      {
        key: 'realtime-monitor',
        title: '实时监控',
        icon: 'MonitorOutlined',
        path: '/monitoring/realtime',
        permission: [],
      },
      {
        key: 'performance-analysis',
        title: '性能分析',
        icon: 'BarChartOutlined',
        path: '/analytics/portfolio',
        permission: ['analytics:view'],
      },
      {
        key: 'cbsc-market',
        title: 'CBSC行情',
        icon: 'TrendingUpOutlined',
        path: '/cbsc',
        permission: ['cbsc:view'],
      },
    ]),
    getRouteMeta,
    isRouteActive,
  }

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  )
}

export default NavigationProvider