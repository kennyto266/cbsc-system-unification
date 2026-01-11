'use client';

import React from 'react';
import { SquareCard } from '@/components/ui';
import {
  DollarSignIcon,
  ActivityIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  TrendingUp as TrendingUp,
  TrendingDown as TrendingDown,
  ZapIcon
} from 'lucide-react';
import { useStrategyPerformance } from '@/hooks/useRealTimeData';

interface StatsData {
  assets: {
    value: string;
    change: string;
    changeType: 'positive' | 'negative';
  };
  strategies: {
    active: number;
    total: number;
    winRate: number;
  };
  monthly: {
    value: string;
    change: 'up' | 'down';
  };
  risk: {
    maxDrawdown: string;
    sharpeRatio: string;
  };
}

export default function DashboardStats() {
  const { data: strategyData, isConnected, isUsingMock } = useStrategyPerformance();
  const [loading, setLoading] = React.useState(true);

  // 根據實時策略數據計算統計信息
  const stats: StatsData | null = React.useMemo(() => {
    if (!strategyData || !strategyData.strategies) {
      return null;
    }

    const strategies = strategyData.strategies;
    const activeStrategies = strategies.length;
    const avgSharpeRatio = strategies.reduce((sum, s) => sum + s.sharpe_ratio, 0) / strategies.length;
    const avgReturn = strategies.reduce((sum, s) => sum + s.total_return, 0) / strategies.length;
    const avgWinRate = strategies.reduce((sum, s) => sum + (s.win_rate || 0), 0) / strategies.length;
    const maxDrawdown = Math.max(...strategies.map(s => s.max_drawdown));

    // 模擬資產總值（基於策略表現）
    const baseAssets = 100000;
    const totalAssets = baseAssets * (1 + avgReturn);

    return {
      assets: {
        value: `$${totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        change: avgReturn > 0 ? `+${(avgReturn * 100).toFixed(2)}%` : `${(avgReturn * 100).toFixed(2)}%`,
        changeType: avgReturn > 0 ? 'positive' : 'negative'
      },
      strategies: {
        active: activeStrategies,
        total: 4, // 總策略數
        winRate: avgWinRate * 100
      },
      monthly: {
        value: `$${(totalAssets * avgReturn / 12).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        change: avgReturn > 0 ? 'up' : 'down'
      },
      risk: {
        maxDrawdown: `${(maxDrawdown * 100).toFixed(2)}%`,
        sharpeRatio: avgSharpeRatio.toFixed(2)
      }
    };
  }, [strategyData]);

  React.useEffect(() => {
    setLoading(false);
  }, []);

  const statCards = [
    {
      id: 1,
      name: '總資產',
      value: stats?.assets?.value || '--',
      change: stats?.assets?.change || '--',
      changeType: stats?.assets?.changeType || 'positive',
      icon: DollarSignIcon,
    },
    {
      id: 2,
      name: '活躍策略',
      value: stats ? `${stats.strategies.active}/${stats.strategies.total}` : '--',
      change: stats ? `勝率: ${stats.strategies.winRate.toFixed(1)}%` : '--',
      changeType: 'positive' as const,
      icon: ActivityIcon,
    },
    {
      id: 3,
      name: '本月收益',
      value: stats?.monthly?.value || '--',
      change: stats?.monthly?.change || '--',
      changeType: stats?.monthly?.change === 'up' ? 'positive' : 'negative',
      icon: TrendingUpIcon,
    },
    {
      id: 4,
      name: '風險指標',
      value: stats ? `夏普比率: ${stats.risk.sharpeRatio}` : '--',
      change: stats ? `最大回撤: ${stats.risk.maxDrawdown}` : '--',
      changeType: stats?.risk?.maxDrawdown && parseFloat(stats.risk.maxDrawdown) < 3 ? 'positive' : 'negative',
      icon: TrendingDownIcon,
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <SquareCard key={i} className="animate-pulse">
            <div className="p-6">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            </div>
          </SquareCard>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <SquareCard className="col-span-full">
        <div className="p-6">
          <p className="text-red-600 text-center">{error}</p>
        </div>
      </SquareCard>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat) => (
        <SquareCard key={stat.id}>
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon
                  className={`w-8 h-8 ${
                    stat.id === 1
                      ? 'text-blue-600'
                      : stat.id === 2
                      ? 'text-green-600'
                      : stat.id === 3
                      ? 'text-purple-600'
                      : 'text-orange-600'
                  }`}
                />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd>
                    <div className="text-lg font-medium text-gray-900">
                      {stat.value}
                    </div>
                    <div className={`flex items-center text-sm ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.changeType === 'positive' ? (
                        <TrendingUp className="w-4 h-4 mr-1" />
                      ) : (
                        <TrendingDown className="w-4 h-4 mr-1" />
                      )}
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </SquareCard>
      ))}
    </div>
  );
}