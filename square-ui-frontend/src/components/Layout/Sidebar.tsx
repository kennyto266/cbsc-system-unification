import React, { useState } from 'react'
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ChartBarIcon,
  UserGroupIcon,
  CogIcon,
  DocumentTextIcon,
  BellIcon,
  ShieldCheckIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'
import type { SidebarItem, SidebarProps } from '@/types'

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggle,
  items,
  activeItem,
  onItemClick,
}) => {
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  const renderItem = (item: SidebarItem, level: number = 0) => {
    const isActive = activeItem === item.id
    const isExpanded = expandedItems.includes(item.id)
    const hasChildren = item.children && item.children.length > 0

    return (
      <div key={item.id} className="w-full">
        <button
          type="button"
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(item.id)
            } else {
              onItemClick(item.id)
            }
          }}
          className={cn(
            'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
            'hover:bg-gray-100 dark:hover:bg-gray-800',
            isActive
              ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
              : 'text-gray-700 dark:text-gray-300',
            isCollapsed && level === 0 ? 'justify-center' : 'justify-between'
          )}
        >
          <div className={cn('flex items-center', isCollapsed && level === 0 ? 'justify-center' : '')}>
            <item.icon
              className={cn(
                'flex-shrink-0',
                isCollapsed ? 'h-6 w-6' : 'h-5 w-5 mr-3'
              )}
              aria-hidden="true"
            />
            {!isCollapsed && (
              <>
                <span className="truncate">{item.label}</span>
                {item.badge && (
                  <span
                    className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                  >
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </div>
          {!isCollapsed && hasChildren && (
            isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 ml-2" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 ml-2" />
            )
          )}
        </button>

        {/* Submenu */}
        {hasChildren && !isCollapsed && isExpanded && (
          <div className="mt-1 ml-4">
            {item.children!.map(child => renderItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        isCollapsed ? 'w-20' : 'w-64',
        'lg:flex lg:flex-col'
      )}
    >
      {/* Sidebar header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Square UI
          </h2>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 lg:hidden"
          aria-label="Toggle sidebar"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {items.map(item => renderItem(item))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        {!isCollapsed ? (
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-700" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                User Name
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                user@example.com
              </p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-700" />
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar