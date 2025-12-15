import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  X,
  BarChart3,
  TrendingUp,
  Users,
  Settings,
  Monitor,
  LogOut,
  User,
  HelpCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSwipeGesture } from '../../hooks/useSwipeGesture';
import { userAPI } from '../../services/api';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

const menuItems = [
  {
    icon: BarChart3,
    label: '儀表板',
    path: '/dashboard',
  },
  {
    icon: TrendingUp,
    label: '策略管理',
    path: '/strategies',
    submenu: [
      { label: '策略列表', path: '/strategies/list' },
      { label: '創建策略', path: '/strategies/create' },
      { label: '策略模板', path: '/strategies/templates' },
    ],
  },
  {
    icon: Users,
    label: '用戶管理',
    path: '/users',
    submenu: [
      { label: '用戶列表', path: '/users/list' },
      { label: '新建用戶', path: '/users/create' },
      { label: '角色權限', path: '/users/roles' },
    ],
  },
  {
    icon: Monitor,
    label: '系統監控',
    path: '/monitoring',
  },
  {
    icon: Settings,
    label: '系統設置',
    path: '/settings',
  },
];

const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [menuRef] = useSwipeGesture({
    onSwipeLeft: onClose,
    preventDefault: false,
  });

  const handleLogout = async () => {
    try {
      await userAPI.logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleMenuItemClick = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Menu Panel */}
          <motion.div
            ref={menuRef as any}
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 bottom-0 w-72 bg-white shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">菜單</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* User Info */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">管理員</p>
                  <p className="text-sm text-gray-500">admin@cbsc.com</p>
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <nav className="flex-1 overflow-y-auto py-4">
              <ul className="space-y-1">
                {menuItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={() => handleMenuItemClick(item.path)}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors ${
                          isActive ? 'bg-primary-50 text-primary-600 border-r-2 border-primary-600' : ''
                        }`
                      }
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="font-medium">{item.label}</span>
                    </NavLink>

                    {/* Submenu */}
                    {item.submenu && (
                      <ul className="ml-4 mt-1 space-y-1">
                        {item.submenu.map((subItem) => (
                          <li key={subItem.path}>
                            <NavLink
                              to={subItem.path}
                              onClick={() => handleMenuItemClick(subItem.path)}
                              className={({ isActive }) =>
                                `block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors ${
                                  isActive ? 'text-primary-600 font-medium' : ''
                                }`
                              }
                            >
                              {subItem.label}
                            </NavLink>
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </nav>

            {/* Footer Actions */}
            <div className="p-4 border-t border-gray-200 space-y-2">
              <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 transition-colors rounded-lg">
                <HelpCircle className="w-5 h-5" />
                <span className="font-medium">幫助中心</span>
              </button>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 transition-colors rounded-lg"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-medium">退出登錄</span>
              </button>
            </div>
          </motion.div>

          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={onClose}
          />
        </>
      )}
    </AnimatePresence>
  );
};

export default MobileMenu;