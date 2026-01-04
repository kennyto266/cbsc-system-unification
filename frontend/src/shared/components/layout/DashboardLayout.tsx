// CBSC Trading System - Dashboard Layout Component
// Main application layout with header, sidebar, and content area

import { Layout, Menu } from 'antd';
import {
  HomeOutlined,
  LineChartOutlined,
  ExperimentOutlined,
  DotChartOutlined,
  UserOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = Layout;

/**
 * Main dashboard layout with navigation
 */
export const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Get current key from path
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/') return ['dashboard'];
    if (path === '/strategies/generator') return ['generator'];
    if (path.startsWith('/strategies')) return ['strategies'];
    if (path.startsWith('/backtest')) return ['backtest'];
    if (path.startsWith('/realtime')) return ['realtime'];
    return ['dashboard'];
  };

  const menuItems = [
    { key: 'dashboard', icon: <HomeOutlined />, label: '儀表板', path: '/' },
    { key: 'strategies', icon: <LineChartOutlined />, label: '策略管理', path: '/strategies' },
    { key: 'generator', icon: <ThunderboltOutlined />, label: '策略生成器', path: '/strategies/generator' },
    { key: 'backtest', icon: <ExperimentOutlined />, label: '回測系統', path: '/backtests' },
    { key: 'realtime', icon: <DotChartOutlined />, label: '實時數據', path: '/realtime' },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    const item = menuItems.find((i) => i.key === key);
    if (item) {
      navigate(item.path);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        theme="dark"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 32,
            margin: 16,
            color: 'white',
            fontSize: 18,
            fontWeight: 'bold',
            textAlign: 'center',
          }}
        >
          CBSC 量化交易
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={getSelectedKey()}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: 200 }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <div style={{ fontSize: 18, fontWeight: 500 }}>
            {menuItems.find((i) => i.key === getSelectedKey()[0])?.label || '儀表板'}
          </div>
          <Menu
            mode="horizontal"
            style={{ border: 'none', minWidth: 0 }}
            items={[
              {
                key: 'profile',
                icon: <UserOutlined />,
                label: '個人資料',
                onClick: () => navigate('/profile'),
              },
            ]}
          />
        </Header>
        <Content style={{ margin: '24px', overflow: 'initial' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: '#fff',
              borderRadius: 8,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};
