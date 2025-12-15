import React, { createContext, useContext, useState, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

interface BreadcrumbItem {
  label: string
  href?: string
  active?: boolean
}

interface NavigationState {
  currentPage: string
  breadcrumbs: BreadcrumbItem[]
  loading: boolean
  setLoading: (loading: boolean) => void
  updateBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void
  navigateTo: (path: string) => void
  goBack: () => void
}

const NavigationContext = createContext<NavigationState | undefined>(undefined)

export const useNavigation = () => {
  const context = useContext(NavigationContext)
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider')
  }
  return context
}

interface NavigationProviderProps {
  children: React.ReactNode
}

const getBreadcrumbsForPath = (pathname: string): BreadcrumbItem[] => {
  const pathSegments = pathname.split('/').filter(Boolean)
  const breadcrumbs: BreadcrumbItem[] = [{ label: '首页', href: '/' }]

  const pathMap: Record<string, string> = {
    dashboard: '仪表盘',
    strategies: '策略管理',
    backtest: '回测分析',
    portfolio: '投资组合',
    users: '用户管理',
    settings: '系统设置',
    profile: '个人资料',
    list: '列表',
    create: '创建',
    templates: '模板',
    analysis: '分析',
    roles: '角色权限',
    login: '登录',
    register: '注册',
  }

  let currentPath = ''
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`
    const label = pathMap[segment] || segment

    // Only show non-numeric segments
    if (!/^\d+$/.test(segment)) {
      breadcrumbs.push({
        label,
        href: index === pathSegments.length - 1 ? undefined : currentPath,
        active: index === pathSegments.length - 1,
      })
    }
  })

  return breadcrumbs
}

export const NavigationProvider: React.FC<NavigationProviderProps> = ({ children }) => {
  const location = useLocation()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(location.pathname)
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>(
    getBreadcrumbsForPath(location.pathname)
  )

  const updateBreadcrumbs = useCallback((newBreadcrumbs: BreadcrumbItem[]) => {
    setBreadcrumbs(newBreadcrumbs)
  }, [])

  const navigateTo = useCallback((path: string) => {
    setLoading(true)
    navigate(path)
  }, [navigate])

  const goBack = useCallback(() => {
    setLoading(true)
    navigate(-1)
  }, [navigate])

  // Update breadcrumbs when location changes
  React.useEffect(() => {
    setCurrentPage(location.pathname)
    setBreadcrumbs(getBreadcrumbsForPath(location.pathname))
    setLoading(false)
  }, [location.pathname])

  const value: NavigationState = {
    currentPage,
    breadcrumbs,
    loading,
    setLoading,
    updateBreadcrumbs,
    navigateTo,
    goBack,
  }

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  )
}

export default NavigationProvider