import React from 'react'
import { Navigate } from 'react-router-dom'

// Lazy load components for code splitting
const DashboardPage = React.lazy(() => import('../pages/dashboard/DashboardPage'))
const StrategiesPage = React.lazy(() => import('../pages/strategies/StrategiesPage'))
const StrategyDetailPage = React.lazy(() => import('../pages/strategies/StrategyDetailPage'))
const CreateStrategyPage = React.lazy(() => import('../pages/strategies/CreateStrategyPage'))
const MonitoringPage = React.lazy(() => import('../pages/monitoring/MonitoringPage'))
const AnalyticsPage = React.lazy(() => import('../pages/analytics/AnalyticsPage'))
const ReportsPage = React.lazy(() => import('../pages/reports/ReportsPage'))
const SettingsPage = React.lazy(() => import('../pages/settings/SettingsPage'))
const ProfilePage = React.lazy(() => import('../pages/profile/ProfilePage'))
const IndicatorLibraryPage = React.lazy(() => import('../pages/technical-indicators/IndicatorLibraryPage'))
const CBSCTabPage = React.lazy(() => import('../pages/dashboard/CBSCTabPage'))
const NotFoundPage = React.lazy(() => import('../pages/error/NotFoundPage'))

// Route configuration
export const routes = [
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: <DashboardPage />,
    meta: {
      title: '仪表板',
      requiresAuth: true,
      keepAlive: true,
    },
  },
  {
    path: '/strategies',
    element: <StrategiesPage />,
    meta: {
      title: '策略管理',
      requiresAuth: true,
    },
    children: [
      {
        path: '/strategies/create',
        element: <CreateStrategyPage />,
        meta: {
          title: '创建策略',
          requiresAuth: true,
        },
      },
      {
        path: '/strategies/:id',
        element: <StrategyDetailPage />,
        meta: {
          title: '策略详情',
          requiresAuth: true,
        },
      },
      {
        path: '/strategies/:id/edit',
        element: <CreateStrategyPage />,
        meta: {
          title: '编辑策略',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/indicators',
    element: <IndicatorLibraryPage />,
    meta: {
      title: '技术指标',
      requiresAuth: true,
    },
    children: [
      {
        path: '/indicators/library',
        element: <IndicatorLibraryPage />,
        meta: {
          title: '指标库',
          requiresAuth: true,
        },
      },
      {
        path: '/indicators/custom',
        element: <IndicatorLibraryPage />,
        meta: {
          title: '自定义指标',
          requiresAuth: true,
        },
      },
      {
        path: '/indicators/scanner',
        element: <IndicatorLibraryPage />,
        meta: {
          title: '指标扫描',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/monitoring',
    element: <MonitoringPage />,
    meta: {
      title: '监控中心',
      requiresAuth: true,
      keepAlive: true,
    },
    children: [
      {
        path: '/monitoring/realtime',
        element: <MonitoringPage />,
        meta: {
          title: '实时监控',
          requiresAuth: true,
          keepAlive: true,
        },
      },
      {
        path: '/monitoring/alerts',
        element: <MonitoringPage />,
        meta: {
          title: '告警管理',
          requiresAuth: true,
        },
      },
      {
        path: '/monitoring/performance',
        element: <MonitoringPage />,
        meta: {
          title: '性能分析',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/analytics',
    element: <AnalyticsPage />,
    meta: {
      title: '数据分析',
      requiresAuth: true,
    },
    children: [
      {
        path: '/analytics/portfolio',
        element: <AnalyticsPage />,
        meta: {
          title: '投资组合',
          requiresAuth: true,
        },
      },
      {
        path: '/analytics/backtest',
        element: <AnalyticsPage />,
        meta: {
          title: '回测分析',
          requiresAuth: true,
        },
      },
      {
        path: '/analytics/risk',
        element: <AnalyticsPage />,
        meta: {
          title: '风险评估',
          requiresAuth: true,
        },
      },
      {
        path: '/analytics/reports',
        element: <ReportsPage />,
        meta: {
          title: '报告中心',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/cbsc',
    element: <CBSCTabPage />,
    meta: {
      title: 'CBSC牛熊证',
      requiresAuth: true,
    },
  },
  {
    path: '/reports',
    element: <ReportsPage />,
    meta: {
      title: '报告中心',
      requiresAuth: true,
    },
    children: [
      {
        path: '/reports/generate',
        element: <ReportsPage />,
        meta: {
          title: '生成报告',
          requiresAuth: true,
        },
      },
      {
        path: '/reports/history',
        element: <ReportsPage />,
        meta: {
          title: '历史报告',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/settings',
    element: <SettingsPage />,
    meta: {
      title: '系统设置',
      requiresAuth: true,
    },
    children: [
      {
        path: '/settings/profile',
        element: <ProfilePage />,
        meta: {
          title: '个人设置',
          requiresAuth: true,
        },
      },
      {
        path: '/settings/security',
        element: <SettingsPage />,
        meta: {
          title: '安全设置',
          requiresAuth: true,
        },
      },
      {
        path: '/settings/api-keys',
        element: <SettingsPage />,
        meta: {
          title: 'API密钥',
          requiresAuth: true,
        },
      },
      {
        path: '/settings/preferences',
        element: <SettingsPage />,
        meta: {
          title: '偏好设置',
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/profile',
    element: <ProfilePage />,
    meta: {
      title: '个人中心',
      requiresAuth: true,
    },
  },
  {
    path: '*',
    element: <NotFoundPage />,
    meta: {
      title: '页面未找到',
    },
  },
]

// Navigation menu configuration
export const menuConfig = [
  {
    key: '/dashboard',
    title: '仪表板',
    icon: 'DashboardOutlined',
    permission: [],
  },
  {
    key: '/strategies',
    title: '策略管理',
    icon: 'RocketOutlined',
    permission: [],
    children: [
      {
        key: '/strategies/all',
        title: '所有策略',
        permission: [],
      },
      {
        key: '/strategies/active',
        title: '活跃策略',
        permission: [],
        badge: 'activeStrategies',
      },
      {
        key: '/strategies/create',
        title: '创建策略',
        permission: ['strategy:create'],
      },
      {
        key: '/strategies/templates',
        title: '策略模板',
        permission: [],
      },
    ],
  },
  {
    key: '/indicators',
    title: '技术指标',
    icon: 'LineChartOutlined',
    permission: [],
    children: [
      {
        key: '/indicators/library',
        title: '指标库',
        permission: [],
      },
      {
        key: '/indicators/custom',
        title: '自定义指标',
        permission: ['indicator:create'],
      },
      {
        key: '/indicators/scanner',
        title: '指标扫描',
        permission: ['indicator:scan'],
      },
    ],
  },
  {
    key: '/monitoring',
    title: '监控中心',
    icon: 'MonitorOutlined',
    permission: [],
    children: [
      {
        key: '/monitoring/realtime',
        title: '实时监控',
        permission: [],
        badge: 'unreadAlerts',
      },
      {
        key: '/monitoring/alerts',
        title: '告警管理',
        permission: [],
      },
      {
        key: '/monitoring/performance',
        title: '性能分析',
        permission: ['analytics:view'],
      },
    ],
  },
  {
    key: '/analytics',
    title: '数据分析',
    icon: 'BarChartOutlined',
    permission: ['analytics:view'],
    children: [
      {
        key: '/analytics/portfolio',
        title: '投资组合',
        permission: [],
      },
      {
        key: '/analytics/backtest',
        title: '回测分析',
        permission: [],
      },
      {
        key: '/analytics/risk',
        title: '风险评估',
        permission: [],
      },
      {
        key: '/analytics/reports',
        title: '报告中心',
        permission: [],
      },
    ],
  },
  {
    key: '/cbsc',
    title: 'CBSC牛熊证',
    icon: 'RiseOutlined',
    permission: ['cbsc:view'],
  },
]

// Quick access configuration
export const quickAccessConfig = [
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
    icon: 'RiseOutlined',
    path: '/cbsc',
    permission: ['cbsc:view'],
  },
]