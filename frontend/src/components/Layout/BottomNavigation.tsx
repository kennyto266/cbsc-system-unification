import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Home,
  BarChart3,
  TrendingUp,
  Users,
  Settings
} from 'lucide-react';
import { motion } from 'framer-motion';

const navigationItems = [
  {
    icon: Home,
    label: '儀表板',
    path: '/dashboard',
  },
  {
    icon: TrendingUp,
    label: '策略',
    path: '/strategies',
  },
  {
    icon: BarChart3,
    label: '分析',
    path: '/analytics',
  },
  {
    icon: Users,
    label: '用戶',
    path: '/users',
  },
  {
    icon: Settings,
    label: '設置',
    path: '/settings',
  },
];

const BottomNavigation: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="bg-white border-t border-gray-200">
      <ul className="flex items-center justify-around h-16">
        {navigationItems.map((item, index) => {
          const active = isActive(item.path);

          return (
            <li key={item.path} className="flex-1">
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `group relative flex flex-col items-center justify-center h-full transition-colors ${
                    isActive ? 'text-primary-600' : 'text-gray-500 hover:text-gray-700'
                  }`
                }
              >
                <div className="relative">
                  <motion.div
                    className="-inset-2 rounded-full"
                    initial={false}
                    animate={{
                      backgroundColor: active ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                    }}
                    transition={{ duration: 0.2 }}
                  />
                  <item.icon
                    className={`w-6 h-6 relative z-10 transition-transform ${
                      active ? 'scale-110' : 'scale-100'
                    }`}
                  />
                </div>

                {/* Active indicator */}
                {active && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-primary-600 rounded-full"
                    initial={false}
                    transition={{
                      type: "spring",
                      stiffness: 500,
                      damping: 30
                    }}
                  />
                )}

                {/* Label */}
                <span className={`text-xs mt-1 transition-all ${
                  active ? 'font-medium' : 'font-normal'
                }`}>
                  {item.label}
                </span>

                {/* Touch feedback */}
                <div className="absolute inset-0 rounded-lg opacity-0 group-active:opacity-10 bg-gray-900 transition-opacity" />
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

export default BottomNavigation;