import React from 'react'
import { Layout } from 'antd'

const { Header, Sider, Content } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#001529',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        fontSize: '18px',
        fontWeight: 'bold'
      }}>
        CBSC Unified Dashboard
      </Header>
      <Layout>
        <Sider
          width={250}
          style={{
            background: '#001529',
            padding: '20px 0'
          }}
        >
          <div style={{
            color: 'white',
            padding: '0 16px',
            marginBottom: '20px'
          }}>
            导航菜单
          </div>
          <div style={{ color: '#888', padding: '0 16px', fontSize: '12px' }}>
            <div>📊 仪表板</div>
            <div>🎯 策略管理</div>
            <div>📈 监控中心</div>
            <div>📉 分析报告</div>
            <div>⚙️ 系统设置</div>
          </div>
        </Sider>
        <Layout>
          <Content style={{
            margin: 0,
            background: '#f0f2f5'
          }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default AppLayout