import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  ChartBarIcon,
  DocumentTextIcon,
  CogIcon,
  UserGroupIcon,
  AcademicCapIcon,
  BriefcaseIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const menuItems = [
  { name: '仪表盘', href: '/', icon: ChartBarIcon },
  { name: '策略管理', href: '/strategies', icon: AcademicCapIcon },
  { name: '回测分析', href: '/backtest', icon: DocumentTextIcon },
  { name: '投资组合', href: '/portfolio', icon: BriefcaseIcon },
  { name: '用户管理', href: '/users', icon: UserGroupIcon },
  { name: '系统设置', href: '/settings', icon: CogIcon },
]

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation()

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed top-0 left-0 h-full bg-white shadow-lg transition-all duration-300 z-50
          ${isOpen ? 'w-64' : 'w-16'}
          lg:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b">
          {isOpen && (
            <h1 className="text-xl font-bold text-gray-900">
              CBSC
              <span className="text-blue-600">Quant</span>
            </h1>
          )}
          <button
            onClick={onToggle}
            className="p-2 rounded-md hover:bg-gray-100 lg:hidden"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <nav className="mt-8">
          <div className="px-2 space-y-1">
            {menuItems.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={`
                    group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors
                    ${isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon
                    className={`
                      mr-3 flex-shrink-0 h-6 w-6
                      ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                    `}
                  />
                  {isOpen && <span>{item.name}</span>}
                </NavLink>
              )
            })}
          </div>
        </nav>

        {/* Sidebar footer */}
        {isOpen && (
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
              <p className="text-sm font-semibold">升级到专业版</p>
              <p className="text-xs mt-1 opacity-90">解锁更多高级功能</p>
              <button className="mt-3 bg-white text-blue-600 text-xs font-medium px-3 py-1 rounded-md hover:bg-gray-100">
                了解更多
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}