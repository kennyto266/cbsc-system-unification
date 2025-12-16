'use client';

import { useState } from 'react';
import { SquareButton } from '@/components/ui';
import {
  MenuIcon,
  XIcon,
  HomeIcon,
  BarChart3Icon,
  LineChartIcon,
  CogIcon,
  UserIcon
} from 'lucide-react';

const navigation = [
  { name: '儀表板', href: '/dashboard', icon: HomeIcon },
  { name: '策略管理', href: '/dashboard/strategies', icon: BarChart3Icon },
  { name: '分析', href: '/dashboard/analytics', icon: LineChartIcon },
  { name: '設置', href: '/dashboard/settings', icon: CogIcon },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 z-50 flex">
          <div className="relative flex w-full max-w-xs flex-1 flex-col bg-white">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <SquareButton
                variant="ghost"
                size="sm"
                icon={<XIcon size={20} />}
                onClick={() => setSidebarOpen(false)}
              />
            </div>
            {/* Sidebar content */}
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <span className="text-blue-600 font-bold text-xl">CBSC</span>
              </div>
              <nav className="mt-5 flex-1 px-2 space-y-1">
                {navigation.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  >
                    <item.icon
                      className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                      aria-hidden="true"
                    />
                    {item.name}
                  </a>
                ))}
              </nav>
            </div>
          </div>
          <div className="w-14 flex-shrink-0" />
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200 pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <span className="text-blue-600 font-bold text-xl">CBSC策略管理</span>
          </div>
          <nav className="mt-5 flex-1 px-2 space-y-1">
            {navigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                <item.icon
                  className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                  aria-hidden="true"
                />
                {item.name}
              </a>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64 flex flex-col flex-1">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <SquareButton
              variant="ghost"
              size="sm"
              icon={<MenuIcon size={20} />}
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden"
            />

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">歡迎回來</span>
              <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                <UserIcon size={16} className="text-gray-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}