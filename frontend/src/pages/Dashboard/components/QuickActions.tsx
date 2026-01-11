import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import Card from '../../../components/ui/Card';
import Button from '../../../components/ui/Button';

interface QuickAction {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  path?: string;
  action?: () => void;
  badge?: string | number;
}

export const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  // Quick actions configuration
  const quickActions: QuickAction[] = [
    {
      title: '创建新策略',
      description: '使用向导创建新的量化交易策略',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      ),
      color: 'primary',
      path: '/strategies/create',
      badge: '新建',
    },
    {
      title: '策略回测',
      description: '测试策略的历史表现',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'success',
      path: '/strategies/backtest',
    },
    {
      title: '实时监控',
      description: '查看策略实时运行状态',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ),
      color: 'info',
      path: '/monitoring',
      badge: 'Live',
    },
    {
      title: '风险管理',
      description: '设置和管理风险控制参数',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      color: 'warning',
      path: '/risk-management',
    },
    {
      title: '数据分析',
      description: '深入分析交易数据和绩效',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      ),
      color: 'info',
      path: '/analytics',
    },
    {
      title: '系统设置',
      description: '配置系统参数和偏好设置',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      color: 'secondary',
      path: '/settings',
    },
  ];

  // Handle action click
  const handleActionClick = (action: QuickAction) => {
    if (action.path) {
      navigate(action.path);
    } else if (action.action) {
      action.action();
    }
  };

  // Color variants
  const colorVariants = {
    primary: 'hover:bg-blue-50 hover:border-blue-300 group-hover:text-blue-600',
    success: 'hover:bg-green-50 hover:border-green-300 group-hover:text-green-600',
    warning: 'hover:bg-yellow-50 hover:border-yellow-300 group-hover:text-yellow-600',
    danger: 'hover:bg-red-50 hover:border-red-300 group-hover:text-red-600',
    info: 'hover:bg-purple-50 hover:border-purple-300 group-hover:text-purple-600',
    secondary: 'hover:bg-gray-50 hover:border-gray-300 group-hover:text-gray-600',
  };

  return (
    <Card title="快捷操作" className="overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {quickActions.map((action, index) => (
          <motion.div
            key={action.title}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <button
              onClick={() => handleActionClick(action)}
              className={`w-full p-4 text-left border-2 border-gray-200 rounded-xl transition-all duration-200 group ${colorVariants[action.color]}`}
            >
              <div className="flex items-start justify-between">
                <div className={`p-2 rounded-lg bg-${action.color === 'primary' ? 'blue' : action.color === 'success' ? 'green' : action.color === 'warning' ? 'yellow' : action.color === 'danger' ? 'red' : action.color === 'info' ? 'purple' : 'gray'}-100 text-${action.color === 'primary' ? 'blue' : action.color === 'success' ? 'green' : action.color === 'warning' ? 'yellow' : action.color === 'danger' ? 'red' : action.color === 'info' ? 'purple' : 'gray'}-600 mb-3`}>
                  {action.icon}
                </div>
                {action.badge && (
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    action.badge === '新建' ? 'bg-green-100 text-green-700' :
                    action.badge === 'Live' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {action.badge}
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-gray-900 mb-1 group-hover:underline">
                {action.title}
              </h3>
              <p className="text-sm text-gray-600">
                {action.description}
              </p>
            </button>
          </motion.div>
        ))}
      </div>
    </Card>
  );
};