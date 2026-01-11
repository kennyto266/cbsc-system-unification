'use client';

import { SquareCard, SquareButton, SquareBadge } from '@/components/ui';
import { PlusIcon, PlayIcon, PauseIcon, SquareIcon, Settings } from 'lucide-react';

// Mock strategies data
const strategies = [
  {
    id: '1',
    name: '移動平均線交叉策略',
    type: '技術分析',
    status: 'active',
    performance: '+15.2%',
    trades: 245,
    winRate: '68.5%',
    lastRun: '5分鐘前',
  },
  {
    id: '2',
    name: 'RSI超買超賣策略',
    type: '技術指標',
    status: 'active',
    performance: '+8.7%',
    trades: 182,
    winRate: '72.3%',
    lastRun: '2分鐘前',
  },
  {
    id: '3',
    name: '布林帶突破策略',
    type: '波動率',
    status: 'paused',
    performance: '+5.3%',
    trades: 98,
    winRate: '64.1%',
    lastRun: '1小時前',
  },
  {
    id: '4',
    name: 'MACD金叉策略',
    type: '動量指標',
    status: 'testing',
    performance: '待定',
    trades: 0,
    winRate: '-',
    lastRun: '2天前',
  },
  {
    id: '5',
    name: '支撐阻力位策略',
    type: '價格行為',
    status: 'active',
    performance: '+12.8%',
    trades: 156,
    winRate: '70.1%',
    lastRun: '10分鐘前',
  },
];

export default function StrategiesPage() {
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">策略管理</h1>
          <p className="mt-2 text-gray-600">管理您的量化交易策略</p>
        </div>
        <SquareButton icon={<PlusIcon size={16} />} variant="primary">
          創建新策略
        </SquareButton>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <SquareCard>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <PlusIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">總策略數</p>
                <p className="text-2xl font-semibold text-gray-900">5</p>
              </div>
            </div>
          </div>
        </SquareCard>

        <SquareCard>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <PlayIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">運行中</p>
                <p className="text-2xl font-semibold text-gray-900">3</p>
              </div>
            </div>
          </div>
        </SquareCard>

        <SquareCard>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <PauseIcon className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">已暫停</p>
                <p className="text-2xl font-semibold text-gray-900">1</p>
              </div>
            </div>
          </div>
        </SquareCard>

        <SquareCard>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Settings className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">測試中</p>
                <p className="text-2xl font-semibold text-gray-900">1</p>
              </div>
            </div>
          </div>
        </SquareCard>
      </div>

      {/* Strategies Table */}
      <SquareCard>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">策略列表</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  策略名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  類型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  表現
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  交易數
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  勝率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最後運行
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {strategies.map((strategy) => (
                <tr key={strategy.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {strategy.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{strategy.type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <SquareBadge status={strategy.status}>
                      {strategy.status === 'active' ? '運行中' :
                       strategy.status === 'paused' ? '已暫停' : '測試中'}
                    </SquareBadge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${
                      strategy.performance.startsWith('+') ? 'text-green-600' :
                      strategy.performance === '待定' ? 'text-gray-500' : 'text-gray-900'
                    }`}>
                      {strategy.performance}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {strategy.trades}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {strategy.winRate}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {strategy.lastRun}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button className="text-blue-600 hover:text-blue-900">編輯</button>
                      <button className="text-gray-600 hover:text-gray-900">查看</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SquareCard>
    </div>
  );
}