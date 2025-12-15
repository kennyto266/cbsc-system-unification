'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  TrendingUp,
  Settings,
  BarChart3,
  Users,
  Shield,
  ChevronDown,
  LogOut,
  Menu
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/providers/AuthProvider';

interface SidebarItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  children?: SidebarItem[];
}

const sidebarItems: SidebarItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    title: 'Strategies',
    href: '/dashboard/strategies',
    icon: <TrendingUp className="h-5 w-5" />,
    children: [
      {
        title: 'All Strategies',
        href: '/dashboard/strategies',
        icon: null,
      },
      {
        title: 'Create Strategy',
        href: '/dashboard/strategies/create',
        icon: null,
      },
      {
        title: 'Backtesting',
        href: '/dashboard/strategies/backtesting',
        icon: null,
      },
    ],
  },
  {
    title: 'Analytics',
    href: '/dashboard/analytics',
    icon: <BarChart3 className="h-5 w-5" />,
    children: [
      {
        title: 'Performance',
        href: '/dashboard/analytics/performance',
        icon: null,
      },
      {
        title: 'Risk Metrics',
        href: '/dashboard/analytics/risk',
        icon: null,
      },
      {
        title: 'Market Analysis',
        href: '/dashboard/analytics/market',
        icon: null,
      },
    ],
  },
  {
    title: 'Users',
    href: '/dashboard/users',
    icon: <Users className="h-5 w-5" />,
  },
  {
    title: 'Settings',
    href: '/dashboard/settings',
    icon: <Settings className="h-5 w-5" />,
  },
  {
    title: 'Security',
    href: '/dashboard/security',
    icon: <Shield className="h-5 w-5" />,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Strategies', 'Analytics']);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleExpand = (title: string) => {
    setExpandedItems(prev =>
      prev.includes(title)
        ? prev.filter(item => item !== title)
        : [...prev, title]
    );
  };

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <div className={cn(
      "flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300",
      isCollapsed ? "w-20" : "w-64"
    )}>
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">C</span>
          </div>
          {!isCollapsed && (
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              CBSC
            </span>
          )}
        </Link>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {sidebarItems.map((item) => {
          const active = isActive(item.href);
          const hasChildren = item.children && item.children.length > 0;
          const isExpanded = expandedItems.includes(item.title);

          return (
            <div key={item.title}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center justify-between w-full px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
                  isCollapsed && "justify-center"
                )}
                onClick={(e) => {
                  if (hasChildren) {
                    e.preventDefault();
                    toggleExpand(item.title);
                  }
                }}
              >
                <div className="flex items-center space-x-3">
                  {item.icon}
                  {!isCollapsed && <span>{item.title}</span>}
                </div>
                {!isCollapsed && hasChildren && (
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 transition-transform",
                      isExpanded && "transform rotate-180"
                    )}
                  />
                )}
              </Link>

              {/* Submenu */}
              {hasChildren && !isCollapsed && isExpanded && (
                <div className="mt-1 ml-9 space-y-1">
                  {item.children?.map((child) => {
                    const childActive = pathname === child.href;
                    return (
                      <Link
                        key={child.href}
                        href={child.href}
                        className={cn(
                          "block px-3 py-2 text-sm rounded-md transition-colors",
                          childActive
                            ? "bg-gray-100 dark:bg-gray-700 text-primary dark:text-primary-foreground"
                            : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                        )}
                      >
                        {child.title}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* User menu */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {!isCollapsed && user && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {user.firstName || user.username}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {user.email}
            </p>
          </div>
        )}
        <button
          onClick={logout}
          className={cn(
            "flex items-center space-x-3 w-full px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
            isCollapsed && "justify-center"
          )}
        >
          <LogOut className="h-5 w-5" />
          {!isCollapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  );
}