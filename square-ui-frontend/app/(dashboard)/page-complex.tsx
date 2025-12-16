'use client';

import { SquareCard, SquareBadge, SquareButton } from '@/components/ui';
import {
  TrendingUpIcon,
  TrendingDownIcon,
  DollarSignIcon,
  ActivityIcon
} from 'lucide-react';

// Mock data
const stats = [
  {
    id: 1,
    name: '總資產',
    value: '$125,670',
    change: '+12.5%',
    changeType: 'positive',
    icon: DollarSignIcon,
  },
  {
    id: 2,
    name: '活躍策略',
    value: '8',
    change: '+2',
    changeType: 'positive',
    icon: ActivityIcon,
  },
  {
    id: 3,
    name: '本月收益',
    value: '$8,432',
    change: '+23.1%',
    changeType: 'positive',
    icon: TrendingUpIcon,
  },
  {
    id: 4,
    name: '最大回撤',
    value: '-2.3%',
    change: '-0.5%',
    changeType: 'negative',
    icon: TrendingDownIcon,
  },
];

const recentStrategies = [
  {
    id: 1,
    name: '移動平均線交叉策略',
    status: 'active',
    performance: '+15.2%',
    lastUpdate: '2小時前',
  },
  {
    id: 2,
    name: 'RSI超買超賣策略',
    status: 'active',
    performance: '+8.7%',
    lastUpdate: '5小時前',
  },
  {
    id: 3,
    name: '布林帶突破策略',
    status: 'paused',
    performance: '+5.3%',
    lastUpdate: '1天前',
  },
  {
    id: 4,
    name: 'MACD金叉策略',
    status: 'testing',
    performance: '待定',
    lastUpdate: '2天前',
  },
];

export default function DashboardPage() {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">儀表板</h1>
        <p className="mt-2 text-gray-600">歡迎回來！這是您的策略管理概覽。</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <SquareCard key={stat.id} padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-3 rounded-full ${
                  stat.changeType === 'positive' ? 'bg-green-100' : 'bg-red-100'
                }`}>
                  <stat.icon
                    className={`h-6 w-6 ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}
                    aria-hidden="true"
                  />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </SquareCard>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Strategies */}
        <SquareCard>
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">最近策略</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentStrategies.map((strategy) => (
                <div key={strategy.id} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {strategy.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      更新於 {strategy.lastUpdate}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <SquareBadge status={strategy.status} size="sm">
                      {strategy.status === 'active' ? '運行中' :
                       strategy.status === 'paused' ? '已暫停' : '測試中'}
                    </SquareBadge>
                    <span className={`text-sm font-medium ${
                      strategy.performance.startsWith('+') ? 'text-green-600' :
                      strategy.performance === '待定' ? 'text-gray-500' : 'text-gray-900'
                    }`}>
                      {strategy.performance}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <SquareButton variant="outline" className="w-full">
                查看所有策略
              </SquareButton>
            </div>
          </div>
        </SquareCard>

        {/* Quick Actions */}
        <SquareCard>
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <SquareButton variant="primary" className="w-full">
                創建新策略
              </SquareButton>
              <SquareButton variant="outline" className="w-full">
                查看市場數據
              </SquareButton>
              <SquareButton variant="outline" className="w-full">
                運行回測
              </SquareButton>
              <SquareButton variant="outline" className="w-full">
                導出報告
              </SquareButton>
            </div>
          </div>
        </SquareCard>
      </div>
    </div>
  );
}