import React from 'react';
import { motion } from 'framer-motion';
import { DashboardStats } from '../../../types/dashboard';

interface StatCardsProps {
  stats: DashboardStats | null;
  isLoading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeText?: string;
  icon: React.ReactNode;
  color: 'green' | 'red' | 'blue' | 'purple' | 'yellow' | 'orange';
  isLoading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeText,
  icon,
  color,
  isLoading = false,
}) => {
  const colorClasses = {
    green: {
      bg: 'bg-green-50',
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      text: 'text-green-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
    red: {
      bg: 'bg-red-50',
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      text: 'text-red-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
    blue: {
      bg: 'bg-blue-50',
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      text: 'text-blue-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
    purple: {
      bg: 'bg-purple-50',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
      text: 'text-purple-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
    yellow: {
      bg: 'bg-yellow-50',
      iconBg: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      text: 'text-yellow-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
    orange: {
      bg: 'bg-orange-50',
      iconBg: 'bg-orange-100',
      iconColor: 'text-orange-600',
      text: 'text-orange-600',
      changePositive: 'text-green-600',
      changeNegative: 'text-red-600',
    },
  };

  const currentColor = colorClasses[color];

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm animate-pulse">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
          <div className="h-12 w-12 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow ${currentColor.bg}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className={`text-2xl font-bold ${currentColor.text} mb-2`}>
            {value}
          </p>
          {change !== undefined && (
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${
                change >= 0 ? currentColor.changePositive : currentColor.changeNegative
              }`}>
                {change >= 0 ? '+' : ''}{change}%
              </span>
              {changeText && (
                <span className="text-sm text-gray-500">{changeText}</span>
              )}
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${currentColor.iconBg}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
};

export const StatCards: React.FC<StatCardsProps> = ({ stats, isLoading }) => {
  // Format number to display with commas and decimals
  const formatNumber = (num: number, decimals = 2) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  // Format percentage
  const formatPercentage = (num: number) => {
    return `${(num * 100).toFixed(2)}%`;
  };

  const statCardsData = [
    {
      title: '总收益率',
      value: stats ? formatPercentage(stats.totalReturn) : '0.00%',
      change: 2.35,
      changeText: 'vs 上月',
      icon: (
        <svg className={`w-6 h-6 text-blue-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      color: 'blue' as const,
    },
    {
      title: '总资产',
      value: stats ? `¥${formatNumber(stats.totalAssets)}` : '¥0.00',
      change: 5.12,
      changeText: 'vs 上月',
      icon: (
        <svg className={`w-6 h-6 text-green-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      ),
      color: 'green' as const,
    },
    {
      title: '活跃策略',
      value: stats ? `${stats.activeStrategies}/${stats.totalStrategies}` : '0/0',
      change: 12.5,
      changeText: '运行率',
      icon: (
        <svg className={`w-6 h-6 text-purple-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'purple' as const,
    },
    {
      title: '胜率',
      value: stats ? formatPercentage(stats.winRate) : '0.00%',
      change: -2.1,
      changeText: 'vs 上月',
      icon: (
        <svg className={`w-6 h-6 text-yellow-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'yellow' as const,
    },
    {
      title: '夏普比率',
      value: stats ? formatNumber(stats.sharpeRatio, 2) : '0.00',
      change: 0.15,
      changeText: '风险调整收益',
      icon: (
        <svg className={`w-6 h-6 text-orange-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'orange' as const,
    },
    {
      title: '最大回撤',
      value: stats ? formatPercentage(stats.maxDrawdown) : '0.00%',
      change: -0.5,
      changeText: 'vs 上月',
      icon: (
        <svg className={`w-6 h-6 text-red-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      ),
      color: 'red' as const,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {statCardsData.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
        >
          <StatCard {...card} isLoading={isLoading} />
        </motion.div>
      ))}
    </div>
  );
};