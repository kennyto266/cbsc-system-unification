import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, Bell, User, ChevronLeft } from 'lucide-react';
import BottomNavigation from './BottomNavigation';
import MobileMenu from './MobileMenu';
import SafeArea from '../common/SafeArea';
import { useResponsive } from '../../hooks/useResponsive';

interface MobileLayoutProps {
  title?: string;
  showBackButton?: boolean;
  onBackClick?: () => void;
  rightActions?: React.ReactNode;
  children?: React.ReactNode;
}

const MobileLayout: React.FC<MobileLayoutProps> = ({
  title,
  showBackButton = false,
  onBackClick,
  rightActions,
  children,
}) => {
  const { isMobile } = useResponsive();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Only render mobile layout on mobile devices
  if (!isMobile) {
    return <>{children || <Outlet />}</>;
  }

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate(-1);
    }
  };

  const getPageTitle = () => {
    if (title) return title;

    // Auto-generate title based on route
    const path = location.pathname;
    const routeMap: Record<string, string> = {
      '/': '儀表板',
      '/dashboard': '儀表板',
      '/strategies': '策略管理',
      '/strategies/list': '策略列表',
      '/strategies/create': '創建策略',
      '/strategies/templates': '策略模板',
      '/users': '用戶管理',
      '/users/list': '用戶列表',
      '/users/create': '新建用戶',
      '/users/roles': '角色權限',
      '/monitoring': '系統監控',
      '/settings': '系統設置',
    };

    return routeMap[path] || 'CBSC量化系統';
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <SafeArea top>
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-14 px-4">
            {/* Left section */}
            <div className="flex items-center gap-3">
              {showBackButton ? (
                <button
                  onClick={handleBackClick}
                  className="p-2 -ml-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors"
                  aria-label="返回"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={() => setMenuOpen(true)}
                  className="p-2 -ml-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors"
                  aria-label="菜單"
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <h1 className="text-lg font-medium text-gray-900 truncate">
                {getPageTitle()}
              </h1>
            </div>

            {/* Right section */}
            <div className="flex items-center gap-2">
              {rightActions}
              <button className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <button className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors">
                <User className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>
      </SafeArea>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children || <Outlet />}
      </main>

      {/* Bottom Navigation */}
      <SafeArea bottom>
        <BottomNavigation />
      </SafeArea>

      {/* Mobile Menu Overlay */}
      {menuOpen && (
        <div className="fixed inset-0 z-50">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setMenuOpen(false)}
          />

          {/* Menu */}
          <MobileMenu
            isOpen={menuOpen}
            onClose={() => setMenuOpen(false)}
          />
        </div>
      )}
    </div>
  );
};

export default MobileLayout;