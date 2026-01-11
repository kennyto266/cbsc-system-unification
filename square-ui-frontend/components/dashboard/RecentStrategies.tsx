'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { useRouter } from 'next/navigation';

interface Strategy {
  id: number;
  name: string;
  type: string;
  status: 'active' | 'paused' | 'testing';
  performance: string;
  performanceValue: number;
  lastUpdate: string;
  description: string;
}

interface StrategiesData {
  strategies: Strategy[];
  summary: {
    total: number;
    active: number;
    paused: number;
    testing: number;
    avgPerformance: number;
  };
}

export default function RecentStrategies() {
  const [data, setData] = useState<StrategiesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchStrategies();
    const interval = setInterval(fetchStrategies, 60000); // 每分鐘更新
    return () => clearInterval(interval);
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/dashboard/strategies');
      const result = await response.json();

      if (result.success) {
        setData(result.data);
        setError(null);
      } else {
        setError('無法加載策略數據');
      }
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
      setError('網絡錯誤');
    } finally {
      setLoading(false);
    }
  };

  const handleStrategyClick = (strategyId: number) => {
    router.push(`/dashboard/strategies?id=${strategyId}`);
  };

  const getStatusBadge = (status: Strategy['status']) => {
    switch (status) {
      case 'active':
        return <SquareBadge status="success" size="sm">運行中</SquareBadge>;
      case 'paused':
        return <SquareBadge status="warning" size="sm">已暫停</SquareBadge>;
      case 'testing':
        return <SquareBadge status="info" size="sm">測試中</SquareBadge>;
      default:
        return <SquareBadge status="default" size="sm">未知</SquareBadge>;
    }
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'arbitrage':
        return '💱';
      case 'volatility':
        return '📊';
      case 'sentiment':
        return '😊';
      case 'breakout':
        return '🚀';
      case 'theta':
        return '⏰';
      default:
        return '📈';
    }
  };

  if (loading) {
    return (
      <SquareCard>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </SquareCard>
    );
  }

  if (error) {
    return (
      <SquareCard>
        <div className="p-6">
          <p className="text-red-600 text-center">{error}</p>
        </div>
      </SquareCard>
    );
  }

  if (!data) return null;

  return (
    <SquareCard>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">策略概覽</h3>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>總計: {data.summary.total}</span>
            <span className="text-green-600">運行: {data.summary.active}</span>
            <span className="text-yellow-600">暫停: {data.summary.paused}</span>
            <span className="text-blue-600">測試: {data.summary.testing}</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {data.strategies.map((strategy) => (
            <div
              key={strategy.id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              onClick={() => handleStrategyClick(strategy.id)}
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getTypeIcon(strategy.type)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {strategy.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {strategy.description}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <p className="text-xs text-gray-500">績效</p>
                  <p className={`text-sm font-medium ${getPerformanceColor(strategy.performanceValue)}`}>
                    {strategy.performance}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-xs text-gray-500">更新時間</p>
                  <p className="text-sm text-gray-700">{strategy.lastUpdate}</p>
                </div>

                <div className="text-center">
                  {getStatusBadge(strategy.status)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {data.summary.avgPerformance !== undefined && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">平均績效</span>
              <span className={`font-medium ${getPerformanceColor(data.summary.avgPerformance)}`}>
                {data.summary.avgPerformance > 0 ? '+' : ''}{data.summary.avgPerformance.toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </SquareCard>
  );
}