/**
 * Main Layout Component
 * 主布局组件
 *
 * Features:
 * - 顶部导航栏
 * - 侧边菜单
 * - 用户信息展示
 * - 响应式布局
 */

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Badge } from 'antd';
import {
  UserOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { userAPI } from '../services/api';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);

  // TODO: Fetch user info
  // useEffect(() => {
  //   const fetchUser = async () => {
  //     try {
  //       const userInfo = await userAPI.getCurrentUser();
  //       setUser(userInfo);
  //     } catch (error) {
  //       console.error('Failed to fetch user info:', error);
  //     }
  //   };
  //   fetchUser();
  // }, []);

  // Menu items
  const menuItems = [
    {
      key: '/dashboard',
      icon: <BarChartOutlined />,
      label: '策略仪表板',
    },
    {
      key: '/strategies',
      icon: <BarChartOutlined />,
      label: '策略管理',
      children: [
        {
          key: '/strategies/list',
          label: '策略列表',
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
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
      children: [
        {
          key: '/users/list',
          label: '用户列表',
        },
        {
          key: '/users/create',
          label: '新建用户',
        },
        {
          key: '/users/roles',
          label: '角色权限',
        },
      ],
    },
    {
      key: '/monitoring',
      icon: <BarChartOutlined />,
      label: '系统监控',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // User dropdown menu
  const userMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>
        个人中心
      </Menu.Item>
      <Menu.Item key="settings" icon={<SettingOutlined />}>
        账户设置
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item
        key="logout"
        icon={<LogoutOutlined />}
        onClick={async () => {
          try {
            await userAPI.logout();
            navigate('/login');
          } catch (error) {
            console.error('Logout failed:', error);
          }
        }}
      >
        退出登录
      </Menu.Item>
    </Menu>
  );

  // Handle menu click
  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  // Get selected keys
  const selectedKeys = [location.pathname];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          background: '#fff',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <h1 style={{ margin: 0, color: '#1890ff', fontSize: collapsed ? 16 : 20 }}>
            {collapsed ? 'CBSC' : 'CBSC量化系统'}
          </h1>
        </div>

        {/* Navigation Menu */}
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>

      {/* Main Content */}
      <Layout>
        {/* Header */}
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          }}
        >
          {/* Left */}
          <Space>
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              className: 'trigger',
              onClick: () => setCollapsed(!collapsed),
              style: { fontSize: 18 },
            })}
          </Space>

          {/* Right */}
          <Space size="middle">
            <Badge count={5} size="small">
              <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
            </Badge>

            <Dropdown overlay={userMenu} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar size="small" icon={<UserOutlined />} />
                <span>{user?.username || '管理员'}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* Content */}
        <Content
          style={{
            margin: 0,
            background: '#f0f2f5',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;