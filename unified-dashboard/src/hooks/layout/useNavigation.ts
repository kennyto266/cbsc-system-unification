import { useCallback, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import type { NavigationItem } from '../../types/layout'

// Enhanced navigation configuration for CBSC trading platform
export const navigationConfig: NavigationItem[] = [
  {
    key: 'dashboard',
    label: '儀表板總覽',
    icon: 'DashboardOutlined', // Will be resolved to actual icon component
    path: '/dashboard',
    children: [
      {
        key: 'overview',
        label: '市場總覽',
        icon: 'GlobalOutlined',
        path: '/dashboard/overview'
      },
      {
        key: 'portfolio',
        label: '投資組合',
        icon: 'FundOutlined',
        path: '/dashboard/portfolio',
        badge: { count: 3, color: 'warning' }
      },
      {
        key: 'performance',
        label: '績效分析',
        icon: 'LineChartOutlined',
        path: '/dashboard/performance'
      }
    ]
  },
  {
    key: 'strategies',
    label: '策略管理',
    icon: 'RocketOutlined',
    path: '/strategies',
    children: [
      {
        key: 'strategy-list',
        label: '策略列表',
        icon: 'StockOutlined',
        path: '/strategies/list',
        badge: { count: 12, color: 'success' }
      },
      {
        key: 'create-strategy',
        label: '創建策略',
        icon: 'ThunderboltOutlined',
        path: '/strategies/create'
      },
      {
        key: 'backtest',
        label: '回測分析',
        icon: 'HistoryOutlined',
        path: '/strategies/backtest'
      },
      {
        key: 'template-library',
        label: '策略模板庫',
        icon: 'FileTextOutlined',
        path: '/strategies/templates'
      }
    ]
  },
  {
    key: 'market-data',
    label: '市場數據',
    icon: 'TradingViewOutlined',
    path: '/market-data',
    children: [
      {
        key: 'realtime-quotes',
        label: '實時行情',
        icon: 'LineChartOutlined',
        path: '/market-data/realtime',
        badge: { count: 0, color: 'primary' }
      },
      {
        key: 'technical-analysis',
        label: '技術分析',
        icon: 'BarChartOutlined',
        path: '/market-data/technical'
      },
      {
        key: 'heatmap',
        label: '市場熱力圖',
        icon: 'FundOutlined',
        path: '/market-data/heatmap'
      },
      {
        key: 'market-sentiment',
        label: '市場情緒',
        icon: 'BulbOutlined',
        path: '/market-data/sentiment'
      }
    ]
  },
  {
    key: 'portfolio',
    label: '投資組合',
    icon: 'BankOutlined',
    path: '/portfolio',
    children: [
      {
        key: 'asset-overview',
        label: '資產概覽',
        icon: 'DollarOutlined',
        path: '/portfolio/overview'
      },
      {
        key: 'positions',
        label: '持倉分析',
        icon: 'StockOutlined',
        path: '/portfolio/positions'
      },
      {
        key: 'transaction-history',
        label: '交易記錄',
        icon: 'HistoryOutlined',
        path: '/portfolio/history'
      },
      {
        key: 'asset-allocation',
        label: '資產配置',
        icon: 'FundOutlined',
        path: '/portfolio/allocation'
      }
    ]
  },
  {
    key: 'risk-management',
    label: '風險管理',
    icon: 'SafetyCertificateOutlined',
    path: '/risk',
    children: [
      {
        key: 'risk-metrics',
        label: '風險指標',
        icon: 'AlertOutlined',
        path: '/risk/metrics',
        badge: { count: 1, color: 'error' }
      },
      {
        key: 'stop-loss',
        label: '止損止盈',
        icon: 'SafetyCertificateOutlined',
        path: '/risk/stop-loss'
      },
      {
        key: 'stress-test',
        label: '壓力測試',
        icon: 'AlertOutlined',
        path: '/risk/stress-test'
      },
      {
        key: 'var-analysis',
        label: 'VaR分析',
        icon: 'BarChartOutlined',
        path: '/risk/var'
      }
    ]
  },
  {
    key: 'monitoring',
    label: '監控中心',
    icon: 'MonitorOutlined',
    path: '/monitoring',
    children: [
      {
        key: 'execution-monitor',
        label: '執行監控',
        icon: 'MonitorOutlined',
        path: '/monitoring/execution'
      },
      {
        key: 'alerts',
        label: '警報中心',
        icon: 'BellOutlined',
        path: '/monitoring/alerts',
        badge: { count: 5, color: 'warning' }
      },
      {
        key: 'system-health',
        label: '系統健康',
        icon: 'AlertOutlined',
        path: '/monitoring/health'
      }
    ]
  },
  {
    key: 'cbsc',
    label: 'CBSC牛熊證',
    icon: 'TrendingUpOutlined',
    path: '/cbsc',
    badge: { count: 2, color: 'primary' }
  },
  {
    key: 'team',
    label: '團隊協作',
    icon: 'TeamOutlined',
    path: '/team',
    children: [
      {
        key: 'members',
        label: '團隊成員',
        icon: 'UserOutlined',
        path: '/team/members'
      },
      {
        key: 'shared-strategies',
        label: '共享策略',
        icon: 'StockOutlined',
        path: '/team/strategies'
      },
      {
        key: 'discussions',
        label: '策略討論',
        icon: 'FileTextOutlined',
        path: '/team/discussions'
      }
    ]
  }
]

export const useNavigation = () => {
  const navigate = useNavigate()
  const location = useLocation()

  // Get current navigation item based on path
  const currentItem = useMemo(() => {
    const findItem = (items: NavigationItem[], path: string): NavigationItem | null => {
      for (const item of items) {
        // Check exact match
        if (item.path === path) return item

        // Check if path starts with item path
        if (item.path && path.startsWith(item.path)) {
          // Check children
          if (item.children) {
            const childMatch = findItem(item.children, path)
            if (childMatch) return childMatch
          }
          // Return parent if no child match
          return item
        }

        // Check children
        if (item.children) {
          const found = findItem(item.children, path)
          if (found) return found
        }
      }
      return null
    }

    return findItem(navigationConfig, location.pathname)
  }, [location.pathname])

  // Get parent items for breadcrumb
  const breadcrumbItems = useMemo(() => {
    const items: NavigationItem[] = []
    const path = location.pathname

    // Build breadcrumb hierarchy
    const buildBreadcrumb = (navItems: NavigationItem[], targetPath: string, parentItems: NavigationItem[] = []): NavigationItem[] => {
      for (const item of navItems) {
        if (item.path === targetPath) {
          return [...parentItems, item]
        }

        if (item.children) {
          const found = buildBreadcrumb(item.children, targetPath, [...parentItems, item])
          if (found.length > 0) return found
        }
      }
      return []
    }

    return buildBreadcrumb(navigationConfig, path)
  }, [location.pathname])

  // Get open keys for sidebar
  const openKeys = useMemo(() => {
    const keys: string[] = []

    const findParentKeys = (items: NavigationItem[], path: string): string[] => {
      for (const item of items) {
        if (item.children) {
          const hasActiveChild = item.children.some(child =>
            child.path === path || path.startsWith(child.path + '/')
          )
          if (hasActiveChild) {
            keys.push(item.key)
          }
        }
      }
      return keys
    }

    return findParentKeys(navigationConfig, location.pathname)
  }, [location.pathname])

  // Navigation handlers
  const navigateTo = useCallback((path: string) => {
    navigate(path)
  }, [navigate])

  const navigateByKey = useCallback((key: string) => {
    const findPathByKey = (items: NavigationItem[], targetKey: string): string | null => {
      for (const item of items) {
        if (item.key === targetKey && item.path) return item.path
        if (item.children) {
          const found = findPathByKey(item.children, targetKey)
          if (found) return found
        }
      }
      return null
    }

    const path = findPathByKey(navigationConfig, key)
    if (path) {
      navigate(path)
    }
  }, [navigate])

  // Check if a navigation item is active
  const isActive = useCallback((item: NavigationItem) => {
    if (item.path === location.pathname) return true
    if (item.path && location.pathname.startsWith(item.path)) return true
    return false
  }, [location.pathname])

  return {
    // Navigation data
    navigationConfig,
    currentItem,
    breadcrumbItems,
    openKeys,

    // Navigation actions
    navigateTo,
    navigateByKey,
    isActive,

    // Computed values
    currentPath: location.pathname,
    isHomePage: location.pathname === '/dashboard' || location.pathname === '/',
  }
}