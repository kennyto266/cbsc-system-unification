import React from 'react'
import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FundOutlined,
  LineChartOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()

  // 根據當前路徑選中對應 menu item
  const selectedKey = (() => {
    if (location.pathname.startsWith('/market-data')) return '/market-data'
    if (location.pathname.startsWith('/strategies')) return '/strategies'
    if (location.pathname.startsWith('/reports')) return '/reports'
    if (location.pathname.startsWith('/settings')) return '/settings'
    return '/dashboard'
  })()

  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: '儀表板' },
    { key: '/market-data', icon: <BarChartOutlined />, label: '市場數據中心' },
    { key: '/strategies', icon: <FundOutlined />, label: '策略管理' },
    { key: '/reports', icon: <LineChartOutlined />, label: '分析報告' },
    { key: '/settings', icon: <SettingOutlined />, label: '系統設置' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#001529',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        fontSize: '18px',
        fontWeight: 'bold',
        height: '64px',
        lineHeight: '64px',
      }}>
        📊 CBSC 量化交易系統
      </Header>
      <Layout>
        <Sider
          width={220}
          breakpoint="lg"
          collapsedWidth={0}
          style={{
            background: '#001529',
          }}
        >
          <Menu
            mode="inline"
            theme="dark"
            selectedKeys={[selectedKey]}
            onClick={({ key }) => navigate(key)}
            items={menuItems}
            style={{
              background: '#001529',
              borderRight: 0,
              marginTop: '10px',
            }}
          />
        </Sider>
        <Layout>
          <Content style={{
            margin: 0,
            background: '#f0f2f5',
            minHeight: 'calc(100vh - 64px)',
          }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default AppLayout
