import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  DashboardOutlined,
  RocketOutlined,
  BarChartOutlined,
  MonitorOutlined,
  FileTextOutlined,
  SettingOutlined,
  LineChartOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  StarOutlined,
  BookOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import { Menu, Button, Tooltip, Badge } from 'antd'
import type { MenuProps } from 'antd'
import { useAppSelector } from '../../hooks/redux'

interface SidebarProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
}

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar: React.FC<SidebarProps> = ({ collapsed = false, onCollapse }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { activeStrategies = 8, unreadAlerts = 3 } = useAppSelector(state => state.monitoring)

  // Recent strategies for quick access
  const recentStrategies = [
    { id: 1, name: 'RSI均值回归', type: 'mean-reversion' },
    { id: 2, name: 'MACD动量策略', type: 'momentum' },
    { id: 3, name: '布林带突破', type: 'breakout' },
  ]

  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/strategies',
      icon: <RocketOutlined />,
      label: '策略管理',
      children: [
        {
          key: '/strategies/all',
          label: '所有策略',
        },
        {
          key: '/strategies/active',
          label: (
            <span className="flex items-center justify-between">
              活跃策略
              <Badge count={activeStrategies} size="small" className="ml-2" />
            </span>
          ),
        },
        {
          key: '/strategies/create',
          label: '创建策略',
        },
        {
          key: '/strategies/templates',
          label: '策略模板',
        },
      ],
    },
    {
      key: '/indicators',
      icon: <LineChartOutlined />,
      label: '技术指标',
      children: [
        {
          key: '/indicators/library',
          label: '指标库',
        },
        {
          key: '/indicators/custom',
          label: '自定义指标',
        },
        {
          key: '/indicators/scanner',
          label: '指标扫描',
        },
      ],
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: '监控中心',
      children: [
        {
          key: '/monitoring/realtime',
          label: (
            <span className="flex items-center justify-between">
              实时监控
              {unreadAlerts > 0 && <Badge dot className="ml-2" />}
            </span>
          ),
        },
        {
          key: '/monitoring/alerts',
          label: '告警管理',
        },
        {
          key: '/monitoring/performance',
          label: '性能分析',
        },
      ],
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
      children: [
        {
          key: '/analytics/portfolio',
          label: '投资组合',
        },
        {
          key: '/analytics/backtest',
          label: '回测分析',
        },
        {
          key: '/analytics/risk',
          label: '风险评估',
        },
        {
          key: '/analytics/reports',
          label: '报告中心',
        },
      ],
    },
    {
      key: '/cbsc',
      icon: <RiseOutlined />,
      label: 'CBSC牛熊证',
    },
    {
      type: 'divider',
    },
    {
      key: 'tools',
      icon: <ThunderboltOutlined />,
      label: '工具',
      children: [
        {
          key: '/tools/calculator',
          label: '收益计算器',
        },
        {
          key: '/tools/simulator',
          label: '交易模拟器',
        },
        {
          key: '/tools/api-test',
          label: 'API测试',
        },
      ],
    },
    {
      key: 'resources',
      icon: <BookOutlined />,
      label: '资源中心',
      children: [
        {
          key: '/resources/docs',
          label: '文档中心',
        },
        {
          key: '/resources/tutorials',
          label: '视频教程',
        },
        {
          key: '/resources/community',
          label: '社区论坛',
        },
      ],
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      children: [
        {
          key: '/settings/profile',
          label: '个人设置',
        },
        {
          key: '/settings/security',
          label: '安全设置',
        },
        {
          key: '/settings/api-keys',
          label: 'API密钥',
        },
        {
          key: '/settings/preferences',
          label: '偏好设置',
        },
      ],
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // Get selected keys based on current location
  const getSelectedKeys = () => {
    const path = location.pathname
    // Check for exact matches first
    if (menuItems.some(item => item?.key === path)) {
      return [path]
    }
    // Check for parent menu matches
    for (const item of menuItems) {
      if (item?.children) {
        const childMatch = item.children.find(child =>
          typeof child === 'object' && 'key' in child && child.key === path
        )
        if (childMatch) {
          return [path]
        }
      }
    }
    return ['/dashboard'] // Default selection
  }

  // Get open keys for submenus
  const getOpenKeys = () => {
    const path = location.pathname
    const openKeys: string[] = []

    for (const item of menuItems) {
      if (item?.children) {
        const hasActiveChild = item.children.some(child =>
          typeof child === 'object' && 'key' in child && path.startsWith(child.key as string)
        )
        if (hasActiveChild) {
          openKeys.push(item.key as string)
        }
      }
    }
    return openKeys
  }

  return (
    <aside className="fixed left-0 top-16 bottom-0 z-40 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300"
      style={{ width: collapsed ? 80 : 256 }}
    >
      {/* Logo and Brand */}
      <div className="flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-700">
        <AnimatePresence mode="wait">
          {!collapsed ? (
            <motion.div
              key="expanded"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="flex items-center space-x-2"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <BarChartOutlined className="text-white text-lg" />
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-white">CBSC</span>
            </motion.div>
          ) : (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <BarChartOutlined className="text-white text-lg" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Menu */}
      <div className="h-full overflow-y-auto overflow-x-hidden custom-scrollbar">
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          inlineCollapsed={collapsed}
          className="border-none bg-transparent"
          style={{
            background: 'transparent',
          }}
        />

        {/* Recent Strategies - Quick Access */}
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="px-4 pb-4"
          >
            <div className="mt-6 mb-3">
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                最近使用
              </h3>
            </div>
            <div className="space-y-1">
              {recentStrategies.map((strategy) => (
                <button
                  key={strategy.id}
                  onClick={() => navigate(`/strategies/${strategy.id}`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center space-x-2 group"
                >
                  <ClockCircleOutlined className="text-gray-400 group-hover:text-blue-500" />
                  <span className="truncate">{strategy.name}</span>
                  <Badge
                    dot
                    status={strategy.type === 'mean-reversion' ? 'processing' : 'default'}
                    className="ml-auto"
                  />
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Quick Actions - Collapsed State */}
        {collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="px-4 pb-4 space-y-2"
          >
            <Tooltip title="新建策略" placement="right">
              <Button
                type="primary"
                icon={<RocketOutlined />}
                className="w-full"
                onClick={() => navigate('/strategies/create')}
              />
            </Tooltip>
            <Tooltip title="实时监控" placement="right">
              <Button
                icon={<MonitorOutlined />}
                className="w-full"
                onClick={() => navigate('/monitoring/realtime')}
              />
            </Tooltip>
          </motion.div>
        )}
      </div>

      {/* Collapse Toggle Button */}
      <div className="absolute bottom-4 right-4">
        <Button
          type="text"
          icon={collapsed ? <BarChartOutlined /> : <BarChartOutlined />}
          onClick={() => onCollapse?.(!collapsed)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        />
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(156, 163, 175, 0.5);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(156, 163, 175, 0.7);
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(75, 85, 99, 0.5);
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(75, 85, 99, 0.7);
        }
      `}</style>
    </aside>
  )
}

export default Sidebar