import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Layout, Menu, Space, Badge, Button, Avatar, Dropdown, Typography, theme, Drawer } from 'antd'
import {
  DashboardOutlined,
  BarChartOutlined,
  MonitorOutlined,
  SettingOutlined,
  UserOutlined,
  BellOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RocketOutlined,
  TrophyOutlined,
  AlertOutlined,
} from '@ant-design/icons'

import { useWebSocket } from '../../hooks/useWebSocket'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { selectAuth, logout } from '../../store/slices/authSlice'
import { selectStrategies } from '../../store/slices/strategiesSlice'
import { selectMonitoring } from '../../store/slices/monitoringSlice'
import { selectUI, toggleSidebar, toggleTheme } from '../../store/slices/uiSlice'

// Import enhanced page components
import DashboardOverview from '../pages/DashboardOverview'
import StrategiesManagement from '../pages/StrategiesManagement'
import RealTimeMonitoring from '../../pages/monitoring/RealTimeMonitoring'
import DataAnalytics from '../pages/DataAnalytics'
import Settings from '../pages/Settings'
import UserProfile from '../pages/UserProfile'

// Import responsive components
import NotificationCenter from '../common/NotificationCenter'
import SystemStatusIndicator from '../common/SystemStatusIndicator'
import MobileNavigation from '../common/MobileNavigation'

const { Header, Sider, Content } = Layout
const { Text } = Typography

interface UnifiedDashboardProps {
  defaultPage?: string
  enableMobileNav?: boolean
  enableNotifications?: boolean
  enableRealTimeUpdates?: boolean
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({
  defaultPage = 'dashboard',
  enableMobileNav = true,
  enableNotifications = true,
  enableRealTimeUpdates = true
}) => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // Redux state
  const dispatch = useAppDispatch()
  const { user, isAuthenticated } = useAppSelector(selectAuth)
  const { strategies, loading: strategiesLoading } = useAppSelector(selectStrategies)
  const { systemHealth, alerts } = useAppSelector(selectMonitoring)
  const { sidebarCollapsed, theme: currentTheme, screenSize } = useAppSelector(selectUI)

  // Local state
  const [currentPage, setCurrentPage] = useState(defaultPage)
  const [notificationDrawerVisible, setNotificationDrawerVisible] = useState(false)
  const [userMenuVisible, setUserMenuVisible] = useState(false)

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage, sendMessage } = useWebSocket({
    enabled: enableRealTimeUpdates,
    token: user?.token,
    onMessage: handleWebSocketMessage,
  })

  // Handle WebSocket messages
  function handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'strategy_update':
        // Handle strategy updates
        break
      case 'system_alert':
        // Handle system alerts
        break
      case 'market_data':
        // Handle market data updates
        break
      default:
        console.log('Unknown WebSocket message type:', data.type)
    }
  }

  // Calculate notification count
  const notificationCount = useMemo(() => {
    return alerts.filter(alert => !alert.read).length +
           (strategies.filter(s => s.status === 'attention_needed').length || 0)
  }, [alerts, strategies])

  // Menu items configuration
  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '总览面板',
    },
    {
      key: 'strategies',
      icon: <BarChartOutlined />,
      label: '策略管理',
      badge: strategies.filter(s => s.status === 'active').length || 0,
    },
    {
      key: 'monitoring',
      icon: <MonitorOutlined />,
      label: '实时监控',
      badge: alerts.filter(a => a.severity === 'critical').length || 0,
    },
    {
      key: 'analytics',
      icon: <TrophyOutlined />,
      label: '数据分析',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ]

  // User menu items
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => setCurrentPage('profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '账户设置',
      onClick: () => setCurrentPage('settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => dispatch(logout()),
    },
  ]

  // Handle page navigation
  const handleMenuClick = ({ key }: { key: string }) => {
    setCurrentPage(key)
  }

  // Handle logout
  const handleLogout = useCallback(() => {
    dispatch(logout())
  }, [dispatch])

  // Render current page content
  const renderPageContent = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardOverview />
      case 'strategies':
        return <StrategiesManagement />
      case 'monitoring':
        return <RealTimeMonitoring />
      case 'analytics':
        return <DataAnalytics />
      case 'settings':
        return <Settings />
      case 'profile':
        return <UserProfile />
      default:
        return <DashboardOverview />
    }
  }

  // Enhanced menu items with badges
  const enhancedMenuItems = menuItems.map(item => ({
    ...item,
    label: item.badge ? (
      <Space>
        {item.label}
        <Badge count={item.badge} size="small" />
      </Space>
    ) : item.label,
  }))

  // Responsive sidebar handling
  const isMobile = screenSize === 'mobile' || screenSize === 'tablet'
  const siderWidth = isMobile ? '100%' : 240

  return (
    <Layout className="min-h-screen">
      {/* Sidebar - Hidden on mobile, drawer on mobile */}
      {!isMobile ? (
        <Sider
          trigger={null}
          collapsible
          collapsed={sidebarCollapsed}
          width={siderWidth}
          style={{
            background: colorBgContainer,
            borderRight: '1px solid #f0f0f0',
          }}
        >
          <div className="p-4 text-center">
            <RocketOutlined className="text-2xl text-blue-600" />
            <Text strong className={sidebarCollapsed ? 'hidden' : 'block ml-2'}>
              CBSC Dashboard
            </Text>
          </div>

          <Menu
            mode="inline"
            selectedKeys={[currentPage]}
            items={enhancedMenuItems}
            onClick={handleMenuClick}
          />

          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center justify-between">
              <SystemStatusIndicator
                isConnected={isConnected}
                systemHealth={systemHealth}
                compact={!sidebarCollapsed}
              />
            </div>
          </div>
        </Sider>
      ) : (
        <Drawer
          title="CBSC Dashboard"
          placement="left"
          onClose={() => dispatch(toggleSidebar())}
          open={!sidebarCollapsed}
          bodyStyle={{ padding: 0 }}
          width={240}
        >
          <Menu
            mode="inline"
            selectedKeys={[currentPage]}
            items={enhancedMenuItems}
            onClick={handleMenuClick}
          />
        </Drawer>
      )}

      <Layout>
        {/* Header */}
        <Header
          style={{
            padding: '0 16px',
            background: colorBgContainer,
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div className="flex items-center">
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => dispatch(toggleSidebar())}
              style={{ marginRight: 16 }}
            />

            <div>
              <Text strong className="text-lg">
                {menuItems.find(item => item.key === currentPage)?.label}
              </Text>
              {strategiesLoading && (
                <Text type="secondary" className="ml-2 text-sm">
                  (加载中...)
                </Text>
              )}
            </div>
          </div>

          <Space size="middle">
            {/* Notifications */}
            {enableNotifications && (
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => setNotificationDrawerVisible(true)}
              >
                {notificationCount > 0 && (
                  <Badge count={notificationCount} size="small">
                    <span />
                  </Badge>
                )}
              </Button>
            )}

            {/* Connection Status */}
            <SystemStatusIndicator
              isConnected={isConnected}
              systemHealth={systemHealth}
              showLabel={!isMobile}
            />

            {/* User Menu */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
              open={userMenuVisible}
              onOpenChange={setUserMenuVisible}
            >
              <Space className="cursor-pointer">
                <Avatar src={user?.avatar} icon={<UserOutlined />} />
                {!isMobile && <Text>{user?.username || 'User'}</Text>}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* Main Content */}
        <Content
          style={{
            margin: '16px',
            padding: '16px',
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 'calc(100vh - 112px)',
            overflow: 'auto',
          }}
        >
          {renderPageContent()}
        </Content>

        {/* Mobile Bottom Navigation */}
        {enableMobileNav && isMobile && (
          <MobileNavigation
            currentPage={currentPage}
            onNavigate={setCurrentPage}
            menuItems={menuItems}
          />
        )}
      </Layout>

      {/* Notification Drawer */}
      {enableNotifications && (
        <NotificationCenter
          visible={notificationDrawerVisible}
          onClose={() => setNotificationDrawerVisible(false)}
          alerts={alerts}
          strategies={strategies}
        />
      )}
    </Layout>
  )
}

export default UnifiedDashboard