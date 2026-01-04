/**
 * Custom Tabs Component
 * 自定義標籤頁組件 - 支持圖標和徽章
 */

import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ComponentType<any>;
  disabled?: boolean;
  badge?: string | number;
  children?: React.ReactNode;
}

interface CustomTabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
  variant?: 'default' | 'pills' | 'underline';
}

export const CustomTabs: React.FC<CustomTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className = '',
  variant = 'default'
}) => {
  const getTabClasses = (tab: TabItem) => {
    const isActive = activeTab === tab.id;
    const isDisabled = tab.disabled;

    const baseClasses = `
      flex items-center px-4 py-2 text-sm font-medium
      transition-colors duration-200
      ${isDisabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
    `;

    switch (variant) {
      case 'pills':
        return `
          ${baseClasses}
          ${isActive
            ? 'bg-blue-600 text-white'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-700'
          }
          rounded-lg
        `;

      case 'underline':
        return `
          ${baseClasses}
          ${isActive
            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
            : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
          }
          border-b-2 border-transparent
          -mb-px
        `;

      default:
        return `
          ${baseClasses}
          ${isActive
            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
            : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
          }
          border-b-2 border-transparent
        `;
    }
  };

  const getListClasses = () => {
    switch (variant) {
      case 'pills':
        return 'flex space-x-2 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg';
      case 'underline':
        return 'flex space-x-8 border-b border-gray-200 dark:border-gray-700';
      default:
        return 'flex space-x-8 border-b border-gray-200 dark:border-gray-700';
    }
  };

  return (
    <div className={className}>
      {/* Tab Headers */}
      <nav className={getListClasses()}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && onChange(tab.id)}
              disabled={tab.disabled}
              className={getTabClasses(tab)}
            >
              {Icon && (
                <Icon className="w-5 h-5 mr-2" />
              )}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Tab Content */}
      <div className="mt-4">
        {tabs.map((tab) => {
          if (activeTab === tab.id) {
            return <React.Fragment key={tab.id}>{tab.children}</React.Fragment>;
          }
          return null;
        })}
      </div>
    </div>
  );
};

interface TabPanelProps {
  value: string;
  activeTab: string;
  children: React.ReactNode;
}

export const TabPanel: React.FC<TabPanelProps> = ({
  value,
  activeTab,
  children
}) => {
  if (value !== activeTab) {
    return null;
  }

  return (
    <div>
      {children}
    </div>
  );
};

export default CustomTabs;