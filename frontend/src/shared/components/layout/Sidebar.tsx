import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  FileText,
  Briefcase,
  Users,
  Settings,
  X,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Shield,
  Activity
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

interface MenuItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  {
    name: '仪表盘',
    href: '/',
    icon: BarChart3,
  },
  {
    name: '策略管理',
    href: '/strategies',
    icon: TrendingUp,
    badge: '新',
    children: [
      {
        name: '策略列表',
        href: '/strategies',
        icon: FileText,
      },
      {
        name: '创建策略',
        href: '/strategies/new',
        icon: Sparkles,
      },
      {
        name: '策略模板',
        href: '/strategies/templates',
        icon: Shield,
      },
      {
        name: '策略分析',
        href: '/strategies/analysis',
        icon: Activity,
      },
    ],
  },
  {
    name: '回测分析',
    href: '/backtest',
    icon: FileText,
  },
  {
    name: '实时数据',
    href: '/realtime',
    icon: Activity,
  },
  {
    name: '系统设置',
    href: '/settings',
    icon: Settings,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation();
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['策略管理']);

  const toggleExpanded = (item: string) => {
    setExpandedItems(prev =>
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  const renderMenuItem = (item: MenuItem, level = 0) => {
    const isActive = location.pathname === item.href ||
                    (item.children && item.children.some(child => location.pathname === child.href));
    const isExpanded = expandedItems.includes(item.name);
    const hasChildren = item.children && item.children.length > 0;

    const handleClick = (e: React.MouseEvent) => {
      if (hasChildren) {
        e.preventDefault();
        toggleExpanded(item.name);
      }
    };

    return (
      <div key={item.name}>
        <NavLink
          to={item.href}
          onClick={handleClick}
          className={`group flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
            isActive
              ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          } ${level > 0 ? 'pl-9' : ''}`}
        >
          <item.icon
            className={`mr-3 h-4 w-4 flex-shrink-0 ${
              isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
            }`}
          />
          {isOpen && (
            <>
              <span className="flex-1 text-left">{item.name}</span>
              {item.badge && (
                <Badge variant="secondary" className="mr-2 text-xs">
                  {item.badge}
                </Badge>
              )}
              {hasChildren && (
                isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-gray-500" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-gray-500" />
                )
              )}
            </>
          )}
        </NavLink>

        {hasChildren && isExpanded && isOpen && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 z-50 shadow-lg ${
          isOpen ? 'w-64' : 'w-16'
        } ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          {isOpen ? (
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
              CBSC<span className="text-blue-400">Quant</span>
            </h1>
          ) : (
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CQ</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="lg:hidden"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
          {menuItems.map(item => renderMenuItem(item))}
        </nav>

        {/* Sidebar footer */}
        {isOpen && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="bg-gradient-to-r from-blue-600 to-blue-400 rounded-lg p-4 text-white">
              <p className="text-sm font-semibold">升级到专业版</p>
              <p className="text-xs mt-1 opacity-90">解锁更多高级功能</p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-3 w-full"
                onClick={() => console.log('Upgrade clicked')}
              >
                了解更多
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar;
