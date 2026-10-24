import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SearchOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import { Input, Avatar, Dropdown, Badge, Button, Space, Tooltip } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { logout } from '../../store/slices/authSlice'
import { toggleSidebar } from '../../store/slices/uiSlice'
import NotificationPanel from '../Notification/NotificationPanel'

const { Search } = Input

interface HeaderProps {
  collapsed?: boolean
  onToggle?: () => void
}

const Header: React.FC<HeaderProps> = ({ collapsed = false, onToggle }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useAppDispatch()
  const { user } = useAppSelector(state => state.auth)
  const { sidebarCollapsed } = useAppSelector(state => state.ui)
  const [notificationsVisible, setNotificationsVisible] = useState(false)
  const [notificationCount, setNotificationCount] = useState(5)
  const [searchValue, setSearchValue] = useState('')

  // Mock notifications data
  const notifications = [
    { id: 1, type: 'success', title: '策略执行成功', message: 'RSI均值回归策略已完成交易', time: '2分钟前' },
    { id: 2, type: 'warning', title: '风险提醒', message: 'MACD动量策略触及止损线', time: '5分钟前' },
    { id: 3, type: 'info', title: '系统更新', message: '技术指标库已更新至最新版本', time: '10分钟前' },
    { id: 4, type: 'error', title: '连接异常', message: 'WebSocket连接断开，正在重连...', time: '15分钟前' },
    { id: 5, type: 'success', title: '新策略创建', message: '布林带突破策略创建成功', time: '30分钟前' },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '账户设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        dispatch(logout())
        navigate('/login')
      },
    },
  ]

  const handleSearch = (value: string) => {
    // Implement search functionality
    console.log('Searching for:', value)
    // Navigate to search results page or show search modal
  }

  const handleNotificationClick = () => {
    setNotificationsVisible(!notificationsVisible)
    if (notificationsVisible) {
      setNotificationCount(0)
    }
  }

  // Get current page title based on route
  const getPageTitle = () => {
    const path = location.pathname
    const titles: Record<string, string> = {
      '/dashboard': '仪表板',
      '/strategies': '策略管理',
      '/monitoring': '监控中心',
      '/analytics': '数据分析',
      '/reports': '报告中心',
      '/indicators': '技术指标',
      '/settings': '系统设置',
      '/profile': '个人中心',
    }
    return titles[path] || 'CBSC Dashboard'
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between h-16 px-4 lg:px-8">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={onToggle}
            className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
          />

          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="hidden sm:block"
          >
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              {getPageTitle()}
            </h1>
          </motion.div>
        </div>

        {/* Center - Search Bar */}
        <div className="hidden md:flex flex-1 max-w-xl mx-8">
          <Search
            placeholder="搜索策略、指标或文档..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
            size="large"
            className="w-full"
          />
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Help Button */}
          <Tooltip title="帮助中心">
            <Button
              type="text"
              icon={<QuestionCircleOutlined />}
              className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            />
          </Tooltip>

          {/* Notifications */}
          <div className="relative">
            <Tooltip title="通知中心">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={handleNotificationClick}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white relative"
              >
                {notificationCount > 0 && (
                  <Badge
                    count={notificationCount}
                    size="small"
                    className="absolute -top-1 -right-1"
                  />
                )}
              </Button>
            </Tooltip>

            {/* Notification Dropdown */}
            <AnimatePresence>
              {notificationsVisible && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
                >
                  <NotificationPanel
                    notifications={notifications}
                    onClose={() => setNotificationsVisible(false)}
                    onMarkAllRead={() => setNotificationCount(0)}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* User Menu */}
          <Dropdown
            menu={{ items: userMenuItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <div className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition-colors">
              <Avatar
                size="small"
                src={user?.avatar}
                icon={<UserOutlined />}
                className="bg-blue-500"
              />
              <span className="hidden sm:block text-sm font-medium text-gray-700 dark:text-gray-300">
                {user?.username || '用户'}
              </span>
            </div>
          </Dropdown>
        </div>
      </div>

      {/* Mobile Search Bar */}
      <AnimatePresence>
        {searchValue && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden border-t border-gray-200 dark:border-gray-700 p-4"
          >
            <Search
              placeholder="搜索策略、指标或文档..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onSearch={handleSearch}
              enterButton
              autoFocus
            />
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

export default Header