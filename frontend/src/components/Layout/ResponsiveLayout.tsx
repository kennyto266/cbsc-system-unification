import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Drawer, BackTop, Affix } from 'antd';
import {
  MenuOutlined,
  HomeOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  ArrowUpOutlined
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import '../../styles/responsive.css';
import './ResponsiveLayout.css';

const { Header, Sider, Content } = Layout;

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  title?: string;
  showSidebar?: boolean;
  sidebarItems?: Array<{
    key: string;
    label: string;
    icon?: React.ReactNode;
    path?: string;
  }>;
}

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  title = 'CBSC策略管理系統',
  showSidebar = true,
  sidebarItems = []
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileSidebarVisible, setMobileSidebarVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // 響應式檢測
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 992);

      // 在移動端自動折疊側邊欄
      if (width < 992) {
        setCollapsed(true);
      }
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // 預設導航項目
  const defaultSidebarItems = [
    {
      key: 'dashboard',
      label: '儀表板',
      icon: <HomeOutlined />,
      path: '/'
    },
    {
      key: 'strategies',
      label: '策略管理',
      icon: <BarChartOutlined />,
      path: '/strategies'
    },
    {
      key: 'classification',
      label: '策略分類',
      icon: <BarChartOutlined />,
      path: '/classification'
    },
    {
      key: 'realtime',
      label: '實時監控',
      icon: <BarChartOutlined />,
      path: '/realtime'
    },
    {
      key: 'charts',
      label: '性能圖表',
      icon: <BarChartOutlined />,
      path: '/charts'
    },
    {
      key: 'settings',
      label: '系統設置',
      icon: <SettingOutlined />,
      path: '/settings'
    }
  ];

  const navigationItems = sidebarItems.length > 0 ? sidebarItems : defaultSidebarItems;

  // 處理導航點擊
  const handleMenuClick = ({ key }: { key: string }) => {
    const item = navigationItems.find(item => item.key === key);
    if (item?.path) {
      navigate(item.path);
    }
    if (isMobile) {
      setMobileSidebarVisible(false);
    }
  };

  // 當前選中的菜單項
  const selectedKey = navigationItems.find(item =>
    location.pathname === item.path
  )?.key || 'dashboard';

  // 手機端側邊欄內容
  const sidebarContent = (
    <div className="responsive-sidebar-content">
      <div className="sidebar-header">
        <h2 className="sidebar-title">
          {collapsed && !isMobile ? 'CBSC' : title}
        </h2>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        onClick={handleMenuClick}
        className="sidebar-menu"
        inlineCollapsed={collapsed && !isMobile}
      >
        {navigationItems.map(item => (
          <Menu.Item key={item.key} icon={item.icon}>
            {item.label}
          </Menu.Item>
        ))}
      </Menu>
      <div className="sidebar-footer">
        <Menu mode="inline" className="sidebar-footer-menu">
          <Menu.Item key="profile" icon={<UserOutlined />}>
            個人中心
          </Menu.Item>
          <Menu.Item key="logout" icon={<LogoutOutlined />}>
            登出
          </Menu.Item>
        </Menu>
      </div>
    </div>
  );

  return (
    <Layout className="responsive-layout">
      {/* 桌面端側邊欄 */}
      {showSidebar && !isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={250}
          className="responsive-desktop-sidebar"
          theme="light"
        >
          {sidebarContent}
        </Sider>
      )}

      {/* 移動端遮罩 */}
      {isMobile && mobileSidebarVisible && (
        <div
          className="responsive-overlay active"
          onClick={() => setMobileSidebarVisible(false)}
        />
      )}

      {/* 移動端側邊欄 */}
      {showSidebar && isMobile && (
        <Drawer
          title={title}
          placement="left"
          onClose={() => setMobileSidebarVisible(false)}
          open={mobileSidebarVisible}
          bodyStyle={{ padding: 0 }}
          className="responsive-mobile-sidebar"
          width={280}
        >
          {sidebarContent}
        </Drawer>
      )}

      <Layout className="responsive-main-layout">
        {/* 頂部導航 */}
        <Affix offsetTop={0}>
          <Header className="responsive-header">
            <div className="header-content">
              <div className="header-left">
                {showSidebar && (
                  <Button
                    type="text"
                    icon={<MenuOutlined />}
                    onClick={() => {
                      if (isMobile) {
                        setMobileSidebarVisible(true);
                      } else {
                        setCollapsed(!collapsed);
                      }
                    }}
                    className="menu-toggle"
                  />
                )}
                <h1 className="header-title">
                  {isMobile ? 'CBSC' : title}
                </h1>
              </div>

              <div className="header-right">
                <div className="header-actions">
                  {/* 桌面端用戶信息 */}
                  {!isMobile && (
                    <div className="user-info">
                      <span className="user-name">管理員</span>
                    </div>
                  )}

                  {/* 移動端用戶菜單 */}
                  {isMobile && (
                    <Button
                      type="text"
                      icon={<UserOutlined />}
                      onClick={() => setMobileSidebarVisible(true)}
                    />
                  )}
                </div>
              </div>
            </div>
          </Header>
        </Affix>

        {/* 主要內容區域 */}
        <Content className="responsive-content">
          <div className="content-wrapper">
            {children}
          </div>
        </Content>
      </Layout>

      {/* 返回頂部按鈕 */}
      <BackTop>
        <Button
          type="primary"
          shape="circle"
          icon={<ArrowUpOutlined />}
          size="large"
          className="back-to-top"
        />
      </BackTop>
    </Layout>
  );
};

export default ResponsiveLayout;