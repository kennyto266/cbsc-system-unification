'use client';

import { SquareCard, SquareButton } from '@/components/ui';
import { TrendingUpIcon, TrendingDownIcon, CalendarIcon, DownloadIcon } from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">數據分析</h1>
        <p className="mt-2 text-gray-600">深入分析您的策略表現和市場數據</p>
      </div>

      {/* Time Range Selector */}
      <div className="mb-6 flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-5 w-5 text-gray-500" />
          <select className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>過去 7 天</option>
            <option>過去 30 天</option>
            <option>過去 90 天</option>
            <option>本年度</option>
          </select>
        </div>
        <SquareButton icon={<DownloadIcon size={16} />} variant="outline">
          導出報告
        </SquareButton>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <SquareCard>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">總收益</h3>
              <TrendingUpIcon className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-green-600">+24.3%</p>
            <p className="text-sm text-gray-500 mt-1">過去 30 天</p>
          </div>
        </SquareCard>

        <SquareCard>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">夏普比率</h3>
              <TrendingUpIcon className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">1.85</p>
            <p className="text-sm text-gray-500 mt-1">風險調整後收益</p>
          </div>
        </SquareCard>

        <SquareCard>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">最大回撤</h3>
              <TrendingDownIcon className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-3xl font-bold text-red-600">-5.2%</p>
            <p className="text-sm text-gray-500 mt-1">過去 30 天</p>
          </div>
        </SquareCard>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <SquareCard className="h-96">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">收益走勢</h3>
          </div>
          <div className="p-6 flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <p>📊 圖表將在此處顯示</p>
              <p className="text-sm mt-2">即將集成 Chart.js</p>
            </div>
          </div>
        </SquareCard>

        <SquareCard className="h-96">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">資產配置</h3>
          </div>
          <div className="p-6 flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <p>🥧 圖表將在此處顯示</p>
              <p className="text-sm mt-2">即將集成 Chart.js</p>
            </div>
          </div>
        </SquareCard>
      </div>

      {/* Strategy Performance Table */}
      <SquareCard>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">策略表現詳情</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  策略
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  收益率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  勝率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  交易次數
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  平均收益
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  移動平均線交叉策略
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                  +15.2%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  68.5%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  245
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  +2.3%
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  RSI超買超賣策略
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                  +8.7%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  72.3%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  182
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  +1.8%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </SquareCard>
    </div>
  );
}