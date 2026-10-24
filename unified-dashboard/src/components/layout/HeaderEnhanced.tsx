import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  GlobalOutlined,
  ThunderboltOutlined,
  MonitorOutlined,
  FundOutlined,
  AlertOutlined,
  BulbOutlined,
  SunOutlined,
  MoonOutlined,
  TranslationOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  DashboardOutlined
} from '@ant-design/icons'
import { Input, Avatar, Dropdown, Badge, Button, Space, Tooltip, Switch, Select, Tag } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { logout } from '../../store/slices/authSlice'
import { toggleSidebar, toggleTheme } from '../../store/slices/uiSlice'
import NotificationPanel from '../Notification/NotificationPanel'
import Breadcrumb from './Breadcrumb'
import QuickActions from './QuickActions'
import type { NotificationItem, BreadcrumbItem } from '../../types/layout'

const { Search } = Input
const { Option } = Select

interface HeaderProps {
  collapsed?: boolean
  onToggle?: () => void
}

// Market status indicator component
const MarketStatus: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<'open' | 'closed' | 'pre-market' | 'after-hours'>('open')
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date()
      setCurrentTime(now)
      // Update market status based on Hong Kong market time
      const hour = now.getHours()
      const hkHour = hour // Assuming server time is HK time

      if (hkHour >= 9 && hkHour < 12) {
        setMarketStatus('open')
      } else if (hkHour >= 13 && hkHour < 16) {
        setMarketStatus('open')
      } else if (hkHour >= 8 && hkHour < 9) {
        setMarketStatus('pre-market')
      } else if (hkHour >= 16 && hkHour < 17) {
        setMarketStatus('after-hours')
      } else {
        setMarketStatus('closed')
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [currentTime])

  const statusConfig = {
    open: { color: 'success', text: '開市', bgColor: 'bg-green-100 dark:bg-green-900' },
    closed: { color: 'default', text: '休市', bgColor: 'bg-gray-100 dark:bg-gray-800' },
    'pre-market': { color: 'processing', text: '盤前', bgColor: 'bg-blue-100 dark:bg-blue-900' },
    'after-hours': { color: 'warning', text: '盤後', bgColor: 'bg-orange-100 dark:bg-orange-900' }
  }

  const config = statusConfig[marketStatus]

  return (
    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${config.bgColor}`}>
      <Badge status={config.color as any} />
      <span className="text-xs font-medium">{config.text}</span>
      <span className="text-xs opacity-70">
        {currentTime.toLocaleTimeString('zh-HK', { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  )
}

const HeaderEnhanced: React.FC<HeaderProps> = ({ collapsed = false, onToggle }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useAppDispatch()
  const { user } = useAppSelector(state => state.auth)
  const { themeMode, sidebarCollapsed } = useAppSelector(state => state.ui)
  const [notificationsVisible, setNotificationsVisible] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [language, setLanguage] = useState<'zh' | 'en'>('zh')

  // Mock notification count - would come from Redux store
  const [notificationCount, setNotificationCount] = useState(7)
  const [searchValue, setSearchValue] = useState('')

  // Mock notifications data
  const notifications: NotificationItem[] = [
    {
      id: '1',
      type: 'success',
      title: '策略執行成功',
      message: 'RSI均值回歸策略已完成交易，收益率 +2.34%',
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      read: false,
      action: {
        label: '查看詳情',
        onClick: () => navigate('/strategies/1')
      }
    },
    {
      id: '2',
      type: 'warning',
      title: '風險提醒',
      message: 'MACD動量策略觸及止損線，當前虧損 -1.5%',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      read: false,
      action: {
        label: '調整策略',
        onClick: () => navigate('/strategies/2/edit')
      }
    },
    {
      id: '3',
      type: 'error',
      title: '連接異常',
      message: 'WebSocket連接斷開，正在重連...',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      read: true
    },
    {
      id: '4',
      type: 'info',
      title: '市場異動',
      message: '恒生指數跌破重要支撐位，注意風險控制',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      read: false
    }
  ]

  // Breadcrumb items based on current route
  const breadcrumbItems = useMemo((): BreadcrumbItem[] => {
    const path = location.pathname
    const pathSegments = path.split('/').filter(Boolean)

    const items: BreadcrumbItem[] = []

    // Map paths to breadcrumb items
    const pathMap: Record<string, BreadcrumbItem> = {
      dashboard: { title: '儀表板', icon: <DashboardOutlined /> },
      strategies: { title: '策略管理', icon: <ThunderboltOutlined /> },
      'market-data': { title: '市場數據', icon: <GlobalOutlined /> },
      portfolio: { title: '投資組合', icon: <FundOutlined /> },
      risk: { title: '風險管理', icon: <AlertOutlined /> },
      monitoring: { title: '監控中心', icon: <MonitorOutlined /> },
      team: { title: '團隊協作', icon: <UserOutlined /> },
      cbsc: { title: 'CBSC牛熊證', icon: <BulbOutlined /> }
    }

    // Add home
    items.push({ title: '首頁', path: '/dashboard' })

    // Build breadcrumb from path
    let currentPath = ''
    pathSegments.forEach(segment => {
      currentPath += `/${segment}`
      const item = pathMap[segment]
      if (item) {
        items.push({
          ...item,
          path: currentPath
        })
      }
    })

    return items
  }, [location.pathname])

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '個人資料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系統設置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'theme',
      label: (
        <div className="flex items-center justify-between">
          <span>主題模式</span>
          <Switch
            checked={themeMode === 'dark'}
            onChange={(checked) => dispatch(toggleTheme())}
            checkedChildren={<MoonOutlined />}
            unCheckedChildren={<SunOutlined />}
            size="small"
          />
        </div>
      ),
    },
    {
      key: 'language',
      label: (
        <div className="flex items-center justify-between">
          <span>語言</span>
          <Select
            value={language}
            onChange={setLanguage}
            size="small"
            style={{ width: 80 }}
          >
            <Option value="zh">中文</Option>
            <Option value="en">EN</Option>
          </Select>
        </div>
      ),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登錄',
      onClick: () => {
        dispatch(logout())
        navigate('/login')
      },
      danger: true
    },
  ]

  const handleSearch = (value: string) => {
    console.log('Searching for:', value)
    // Implement global search functionality
    if (value) {
      navigate(`/search?q=${encodeURIComponent(value)}`)
    }
  }

  const handleNotificationClick = () => {
    setNotificationsVisible(!notificationsVisible)
    if (notificationsVisible) {
      setNotificationCount(0)
    }
  }

  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  // Get page specific quick actions
  const getQuickActions = () => {
    const path = location.pathname
    if (path.startsWith('/strategies')) {
      return [
        { key: 'new-strategy', label: '新建策略', icon: <ThunderboltOutlined />, onClick: () => navigate('/strategies/create') },
        { key: 'import', label: '導入策略', icon: <FundOutlined />, onClick: () => console.log('Import strategy') }
      ]
    }
    if (path.startsWith('/market-data')) {
      return [
        { key: 'real-time', label: '實時行情', icon: <MonitorOutlined />, onClick: () => navigate('/market-data/realtime') },
        { key: 'analysis', label: '技術分析', icon: <BulbOutlined />, onClick: () => navigate('/market-data/technical') }
      ]
    }
    return []
  }

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
      themeMode === 'dark'
        ? 'bg-gray-900 border-gray-700'
        : 'bg-white border-gray-200'
    } shadow-sm border-b`}>
      <div className="flex items-center justify-between h-16 px-4 lg:px-8">
        {/* Left side - Menu toggle, breadcrumbs */}
        <div className="flex items-center space-x-4 flex-1">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={onToggle}
            className={`hover:bg-gray-100 dark:hover:bg-gray-800 ${
              themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}
          />

          {/* Breadcrumb Navigation */}
          <div className="hidden md:block">
            <Breadcrumb items={breadcrumbItems} />
          </div>

          {/* Quick Actions */}
          <div className="hidden lg:block">
            <QuickActions actions={getQuickActions()} />
          </div>
        </div>

        {/* Center - Search Bar */}
        <div className="hidden md:flex flex-1 max-w-xl mx-8">
          <Search
            placeholder="搜索策略、指標、文檔或設置..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
            enterButton
            size="middle"
            className="w-full"
            allowClear
          />
        </div>

        {/* Right side - Market status, notifications, user menu */}
        <div className="flex items-center space-x-3">
          {/* Market Status */}
          <div className="hidden xl:block">
            <MarketStatus />
          </div>

          {/* Fullscreen Toggle */}
          <Tooltip title={isFullscreen ? '退出全屏' : '全屏'}>
            <Button
              type="text"
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={handleFullscreen}
              className={`hover:bg-gray-100 dark:hover:bg-gray-800 ${
                themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}
            />
          </Tooltip>

          {/* Help Button */}
          <Tooltip title="幫助中心">
            <Button
              type="text"
              icon={<QuestionCircleOutlined />}
              className={`hover:bg-gray-100 dark:hover:bg-gray-800 ${
                themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}
            />
          </Tooltip>

          {/* Notifications */}
          <div className="relative">
            <Tooltip title="通知中心">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={handleNotificationClick}
                className={`relative hover:bg-gray-100 dark:hover:bg-gray-800 ${
                  themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}
              >
                {notificationCount > 0 && (
                  <Badge
                    count={notificationCount}
                    size="small"
                    className="absolute -top-1 -right-1"
                    style={{ fontSize: '10px' }}
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
                  className={`absolute right-0 mt-2 w-96 rounded-lg shadow-xl border ${
                    themeMode === 'dark'
                      ? 'bg-gray-800 border-gray-700'
                      : 'bg-white border-gray-200'
                  }`}
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
            <div className={`flex items-center space-x-2 cursor-pointer px-3 py-2 rounded-lg transition-colors ${
              themeMode === 'dark'
                ? 'hover:bg-gray-800'
                : 'hover:bg-gray-100'
            }`}>
              <Avatar
                size="small"
                src={user?.avatar}
                icon={<UserOutlined />}
                className="bg-gradient-to-br from-blue-500 to-blue-600"
              />
              <div className="hidden sm:block text-left">
                <div className={`text-sm font-medium ${
                  themeMode === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  {user?.username || '交易員'}
                </div>
                <div className={`text-xs ${
                  themeMode === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  專業版
                </div>
              </div>
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
            className={`md:hidden border-t ${
              themeMode === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'
            } p-4`}
          >
            <Search
              placeholder="搜索策略、指標或文檔..."
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

export default HeaderEnhanced