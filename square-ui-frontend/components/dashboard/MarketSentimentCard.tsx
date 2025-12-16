'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';

interface SentimentData {
  fear_greed_index: number;
  fear_greed_level: string;
  fear_greed_color: string;
  bull_count: number;
  bear_count: number;
  bull_bear_ratio: string;
  total_turnover: string;
  avg_volume: string;
  rsi: string;
  volatility: string;
  last_updated: string;
}

export default function MarketSentimentCard({ className }: { className?: string }) {
  const [data, setData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSentimentData();
    const interval = setInterval(fetchSentimentData, 30000); // 每30秒更新
    return () => clearInterval(interval);
  }, []);

  const fetchSentimentData = async () => {
    try {
      const response = await fetch('/api/data/cbbc?type=sentiment');
      const result = await response.json();

      if (result.success) {
        setData(result.data);
        setError(null);
      } else {
        setError('獲取數據失敗');
      }
    } catch (err) {
      console.error('Failed to fetch sentiment data:', err);
      setError('網絡錯誤');
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (index: number) => {
    if (index >= 70) return 'text-green-600';
    if (index >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSentimentBgColor = (index: number) => {
    if (index >= 70) return 'bg-green-50 border-green-200';
    if (index >= 40) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const formatNumber = (num: string) => {
    const value = parseFloat(num);
    if (value >= 1e9) {
      return (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
      return (value / 1e6).toFixed(2) + 'M';
    }
    return value.toFixed(0);
  };

  if (loading) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-20 bg-gray-200 rounded"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </SquareCard>
    );
  }

  if (error || !data) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <p className="text-red-600">{error || '無法加載市場情緒數據'}</p>
        </div>
      </SquareCard>
    );
  }

  return (
    <SquareCard className={className}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">市場情緒指標</h3>
          <SquareBadge status="active" size="sm">
            CBSC 牛熊證
          </SquareBadge>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 恐懼貪婪指數 */}
        <div className={`p-4 rounded-lg border ${getSentimentBgColor(data.fear_greed_index)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">恐懼貪婪指數</span>
            <span className={`text-2xl font-bold ${getSentimentColor(data.fear_greed_index)}`}>
              {data.fear_greed_index}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">市場情緒</span>
            <SquareBadge
              status={data.fear_greed_color === 'green' ? 'success' :
                     data.fear_greed_color === 'red' ? 'error' : 'warning'}
              size="sm"
            >
              {data.fear_greed_level}
            </SquareBadge>
          </div>
        </div>

        {/* 牛熊比例 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">牛證數量</p>
                <p className="text-xl font-bold text-green-600">{data.bull_count}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">熊證數量</p>
                <p className="text-xl font-bold text-red-600">{data.bear_count}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
          </div>
        </div>

        {/* 其他指標 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">牛熊比例</p>
                <p className="text-lg font-semibold text-blue-600">{data.bull_bear_ratio}</p>
              </div>
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">RSI 指標</p>
                <p className="text-lg font-semibold text-purple-600">{data.rsi}</p>
              </div>
              <Activity className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        {/* 成交量 */}
        <div className="border-t pt-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-xs text-gray-500">總成交額</p>
              <p className="text-lg font-semibold text-gray-900">
                HK$ {formatNumber(data.total_turnover)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">平均成交量</p>
              <p className="text-sm text-gray-700">{formatNumber(data.avg_volume)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 bg-gray-50 text-xs text-gray-500">
        <div className="flex justify-between">
          <span>數據來源：港交所 CBSC</span>
          <span>更新：{new Date(data.last_updated).toLocaleTimeString('zh-TW')}</span>
        </div>
      </div>
    </SquareCard>
  );
}