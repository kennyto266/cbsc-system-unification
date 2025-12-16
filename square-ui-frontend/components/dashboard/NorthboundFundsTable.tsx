'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

interface NorthboundFundsData {
  date: string;
  net_flow: number;
  source: string;
  status: string;
}

interface NorthboundFundsResponse {
  success: boolean;
  source: string;
  last_updated: string;
  summary: {
    latest: {
      date: string;
      net_flow: number;
      change: number;
      change_percent: number;
    };
    statistics: {
      avg_flow: number;
      max_flow: number;
      min_flow: number;
      positive_days: number;
      negative_days: number;
      total_days: number;
    };
  };
  history: NorthboundFundsData[];
  metadata: {
    currency: string;
    unit: string;
    provider: string;
    description: string;
    note: string;
  };
}

export default function NorthboundFundsTable({ className }: { className?: string }) {
  const [data, setData] = useState<NorthboundFundsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNorthboundFunds();
    // 每30秒更新一次
    const interval = setInterval(fetchNorthboundFunds, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchNorthboundFunds = async () => {
    try {
      const response = await fetch('/api/data/northbound-funds?days=30');
      const result = await response.json();

      if (result.success) {
        setData(result);
        setError(null);
      } else {
        setError(result.message || '獲取數據失敗');
      }
    } catch (err) {
      console.error('Failed to fetch Northbound Funds data:', err);
      setError('網絡錯誤，請稍後重試');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  const getChangeColor = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (value: number) => {
    if (value > 0) return <TrendingUp className="w-4 h-4" />;
    if (value < 0) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-8 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </SquareCard>
    );
  }

  if (error) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <p className="text-red-600">{error}</p>
        </div>
      </SquareCard>
    );
  }

  if (!data) return null;

  const { latest, statistics } = data.summary;

  return (
    <SquareCard className={className}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">北向資金流向</h3>
          <SquareBadge
            status={latest.net_flow > 0 ? 'success' : latest.net_flow < 0 ? 'error' : 'default'}
            size="sm"
          >
            {latest.net_flow > 0 ? '淨流入' : latest.net_flow < 0 ? '淨流出' : '持平'}
          </SquareBadge>
        </div>
      </div>

      {/* 最新數據卡片 */}
      <div className="p-6 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">最新淨流入</span>
              <span className={`inline-flex items-center ${getChangeColor(latest.change)}`}>
                {getChangeIcon(latest.change)}
                {formatNumber(latest.net_flow)}
              </span>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              {latest.date}
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">日均流入</span>
              <span className="text-blue-600 font-medium">
                {formatNumber(statistics.avg_flow)}
              </span>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              {statistics.total_days} 天平均
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">波動範圍</span>
              <span className="text-purple-600 font-medium">
                {formatNumber(statistics.min_flow)} ~ {formatNumber(statistics.max_flow)}
              </span>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              最大波幅
            </div>
          </div>
        </div>
      </div>

      {/* 近期趨勢表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                日期
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                淨流入 (百萬)
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                變化
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                狀態
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.history.slice(-10).reverse().map((row, index) => (
              <tr key={`${row.date}-${index}`} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row.date}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-right ${
                  row.net_flow > 0 ? 'text-green-600' : row.net_flow < 0 ? 'text-red-600' : 'text-gray-900'
                }`}>
                  {formatNumber(row.net_flow)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                  {index > 0 && (
                    <span className={getChangeColor(row.net_flow - data.history[data.history.length - index].net_flow)}>
                      {row.net_flow - data.history[data.history.length - index].net_flow > 0 && '+'}
                      {formatNumber(row.net_flow - data.history[data.history.length - index].net_flow)}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <SquareBadge
                    status={row.net_flow > 0 ? 'success' : row.net_flow < 0 ? 'error' : 'default'}
                    size="sm"
                  >
                    {row.net_flow > 0 ? '流入' : row.net_flow < 0 ? '流出' : '持平'}
                  </SquareBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-4 bg-gray-50 text-xs text-gray-500">
        <div className="flex justify-between">
          <span>
            數據來源：{data.metadata.provider} |
            {statistics.positive_days} 天淨流入 / {statistics.negative_days} 天淨流出
          </span>
          <span>更新時間：{new Date().toLocaleTimeString('zh-TW')}</span>
        </div>
      </div>
    </SquareCard>
  );
}