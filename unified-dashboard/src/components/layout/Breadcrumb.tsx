import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { HomeOutlined } from '@ant-design/icons'
import { Breadcrumb as AntdBreadcrumb } from 'antd'
import { motion } from 'framer-motion'

const Breadcrumb: React.FC = () => {
  const location = useLocation()

  const pathSegments = location.pathname.split('/').filter(segment => segment)

  // Breadcrumb configuration
  const breadcrumbNameMap: Record<string, string> = {
    dashboard: '仪表板',
    strategies: '策略管理',
    monitoring: '监控中心',
    analytics: '数据分析',
    reports: '报告中心',
    indicators: '技术指标',
    settings: '系统设置',
    profile: '个人中心',
    cbsc: 'CBSC牛熊证',
    tools: '工具',
    resources: '资源中心',
    all: '所有策略',
    active: '活跃策略',
    create: '创建策略',
    templates: '策略模板',
    library: '指标库',
    custom: '自定义指标',
    scanner: '指标扫描',
    realtime: '实时监控',
    alerts: '告警管理',
    performance: '性能分析',
    portfolio: '投资组合',
    backtest: '回测分析',
    risk: '风险评估',
    calculator: '收益计算器',
    simulator: '交易模拟器',
    'api-test': 'API测试',
    docs: '文档中心',
    tutorials: '视频教程',
    community: '社区论坛',
    about: '关于我们',
    contact: '联系我们',
    careers: '加入我们',
    partners: '合作伙伴',
    terms: '服务条款',
    privacy: '隐私政策',
    security: '安全声明',
    compliance: '合规说明',
  }

  const generateBreadcrumbItems = () => {
    const items = [
      {
        title: (
          <Link to="/dashboard">
            <HomeOutlined />
          </Link>
        ),
      },
    ]

    // Build breadcrumb items
    let currentPath = ''
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const isLast = index === pathSegments.length - 1

      // Handle numeric IDs (e.g., strategy IDs)
      const isNumeric = /^\d+$/.test(segment)
      const displayName = isNumeric ? `ID: ${segment}` : (breadcrumbNameMap[segment] || segment)

      items.push({
        title: isLast ? (
          <span className="text-gray-900 dark:text-white font-medium">{displayName}</span>
        ) : (
          <Link to={currentPath} className="text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400">
            {displayName}
          </Link>
        ),
      })
    })

    return items
  }

  // Don't show breadcrumb on dashboard
  if (location.pathname === '/dashboard' || location.pathname === '/') {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center justify-between"
    >
      <AntdBreadcrumb
        items={generateBreadcrumbItems()}
        separator="/"
        className="text-sm"
      />

      {/* Additional breadcrumb actions can be added here */}
      <div className="flex items-center space-x-2">
        {/* Example: Quick actions based on current page */}
        {location.pathname.startsWith('/strategies') && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            共 {Math.floor(Math.random() * 50) + 10} 个策略
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default Breadcrumb