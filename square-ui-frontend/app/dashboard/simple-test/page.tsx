'use client';

import { SquareCard, SquareButton, SquareBadge } from '@/components/ui';
import {
  TrendingUpIcon,
  TrendingDownIcon,
  DollarSignIcon,
  ActivityIcon,
  PlusIcon,
  FileTextIcon,
  DownloadIcon,
  TrendingUp
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { SimpleDataProvider, useSimpleData } from '@/components/dashboard/SimpleDataProvider';

// Mock stats
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

function DashboardContent() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const { data, loading: dataLoading, error, refresh } = useSimpleData();

  // Quick action handlers
  const handleCreateStrategy = async () => {
    console.log('=== handleCreateStrategy 被调用 ===');
    setLoading('create');
    try {
      router.push('/dashboard/strategies?action=create');
    } catch (error) {
      console.error('创建策略失败:', error);
      alert('创建策略失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  const handleViewMarketData = async () => {
    console.log('=== handleViewMarketData 被调用 ===');
    setLoading('market');
    try {
      const response = await fetch('/api/data/stocks');
      if (response.ok) {
        const data = await response.json();
        console.log('市场数据:', data);
        alert(`获取到 ${data.data?.length || 0} 支股票数据`);
      } else {
        alert('获取市场数据失败');
      }
    } catch (error) {
      console.error('获取市场数据失败:', error);
      alert('获取市场数据失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  const handleRunBacktest = async () => {
    console.log('=== handleRunBacktest 被调用 ===');
    setLoading('backtest');
    try {
      alert('回测功能正在开发中...');
    } catch (error) {
      console.error('运行回测失败:', error);
      alert('运行回测失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  const handleExportReport = async () => {
    console.log('=== handleExportReport 被调用 ===');
    setLoading('export');
    try {
      alert('导出报告功能正在开发中...');
    } catch (error) {
      console.error('导出报告失败:', error);
      alert('导出报告失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">儀表板（測試版）</h1>
        <p className="mt-2 text-gray-600">這是一個簡化版本，用於測試基本功能。</p>
      </div>

      {/* Connection Status */}
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${error ? 'bg-red-500' : dataLoading ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
            <span className="text-sm text-gray-600">
              {error ? '連接錯誤' : dataLoading ? '載入中...' : '數據已更新'}
            </span>
          </div>
          <button
            onClick={refresh}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            刷新數據
          </button>
        </div>
        {error && (
          <p className="text-red-600 text-sm mt-2">{error}</p>
        )}
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

      {/* Government Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Monetary Base */}
        <SquareCard>
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">貨幣基礎</h3>
            <SquareBadge status="active" size="sm">HKMA</SquareBadge>
          </div>
          <div className="p-6">
            {data.monetaryBase ? (
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {data.monetaryBase.total_trillions}萬億港元
                </div>
                <div className={`text-sm font-medium ${
                  data.monetaryBase.change > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.monetaryBase.change > 0 ? '+' : ''}{data.monetaryBase.change_percent}%
                </div>
              </div>
            ) : (
              <div className="text-gray-500">載入中...</div>
            )}
          </div>
        </SquareCard>

        {/* Exchange Rate */}
        <SquareCard>
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">美元/港元匯率</h3>
            <SquareBadge status="active" size="sm">HKMA</SquareBadge>
          </div>
          <div className="p-6">
            {data.exchangeRate ? (
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {data.exchangeRate.rate.toFixed(3)}
                </div>
                <div className={`text-sm font-medium ${
                  data.exchangeRate.change > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.exchangeRate.change > 0 ? '+' : ''}{data.exchangeRate.change_percent}%
                </div>
              </div>
            ) : (
              <div className="text-gray-500">載入中...</div>
            )}
          </div>
        </SquareCard>

        {/* Market Regime */}
        <SquareCard>
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">市場狀態</h3>
          </div>
          <div className="p-6">
            {data.marketRegime ? (
              <div>
                <div className={`text-2xl font-bold ${
                  data.marketRegime.state === 'BULL' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.marketRegime.state === 'BULL' ? '牛市' : '熊市'}
                </div>
                <div className="text-sm text-gray-600">
                  信心: {data.marketRegime.confidence}%
                </div>
              </div>
            ) : (
              <div className="text-gray-500">載入中...</div>
            )}
          </div>
        </SquareCard>
      </div>

      {/* Quick Actions */}
      <SquareCard>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <SquareButton
              variant="primary"
              className="w-full"
              onClick={handleCreateStrategy}
              loading={loading === 'create'}
              icon={<PlusIcon size={16} />}
            >
              創建新策略
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleViewMarketData}
              loading={loading === 'market'}
              icon={<TrendingUp size={16} />}
            >
              查看市場數據
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleRunBacktest}
              loading={loading === 'backtest'}
              icon={<FileTextIcon size={16} />}
            >
              運行回測
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleExportReport}
              loading={loading === 'export'}
              icon={<DownloadIcon size={16} />}
            >
              導出報告
            </SquareButton>
          </div>
        </div>
      </SquareCard>
    </div>
  );
}

export default function SimpleTestPage() {
  return (
    <SimpleDataProvider>
      <DashboardContent />
    </SimpleDataProvider>
  );
}