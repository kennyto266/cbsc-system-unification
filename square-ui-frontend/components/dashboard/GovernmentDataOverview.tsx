'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { DollarSignIcon, TrendingUpIcon, ActivityIcon } from 'lucide-react';

interface MonetaryBaseData {
  total: number;
  total_trillions: number;
  change: number;
  change_percent: number;
}

interface ExchangeRateData {
  rate: number;
  change: number;
  change_percent: number;
}

interface GovernmentDataOverviewProps {
  className?: string;
}

export default function GovernmentDataOverview({ className }: GovernmentDataOverviewProps) {
  const [monetaryBase, setMonetaryBase] = useState<MonetaryBaseData | null>(null);
  const [exchangeRate, setExchangeRate] = useState<ExchangeRateData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGovernmentData();
    const interval = setInterval(fetchGovernmentData, 30000); // 每30秒更新
    return () => clearInterval(interval);
  }, []);

  const fetchGovernmentData = async () => {
    try {
      const [monetaryResponse, exchangeResponse] = await Promise.all([
        fetch('/api/government/monetary-base?days=1'),
        fetch('/api/government/exchange-rate?days=1')
      ]);

      const monetaryResult = await monetaryResponse.json();
      const exchangeResult = await exchangeResponse.json();

      if (monetaryResult.success) {
        setMonetaryBase(monetaryResult.latest);
      }

      if (exchangeResult.success) {
        setExchangeRate(exchangeResult.latest);
      }
    } catch (error) {
      console.error('Failed to fetch government data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="h-16 bg-gray-200 rounded"></div>
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </SquareCard>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'HKD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      notation: value > 1e12 ? 'compact' : 'standard'
    }).format(value);
  };

  const getChangeColor = (value: number) => {
    return value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600';
  };

  const getChangeIcon = (value: number) => {
    if (value > 0) return '+';
    if (value < 0) return '';
    return '';
  };

  return (
    <SquareCard className={className}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">宏觀經濟數據</h3>
          <SquareBadge status="active" size="sm">
            HKMA
          </SquareBadge>
        </div>
      </div>
      <div className="p-6 space-y-6">
        {/* 貨幣基礎 */}
        {monetaryBase && (
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <DollarSignIcon className="w-5 h-5 text-blue-600" />
              <h4 className="text-base font-semibold text-gray-900">貨幣基礎</h4>
            </div>
            <div className="pl-7">
              <div className="text-2xl font-bold text-gray-900">
                {monetaryBase.total_trillions}萬億港元
              </div>
              <div className={`text-sm font-medium ${getChangeColor(monetaryBase.change)}`}>
                {getChangeIcon(monetaryBase.change)}{formatCurrency(monetaryBase.change)}
                <span className="ml-1">({getChangeIcon(monetaryBase.change_percent)}{monetaryBase.change_percent}%)</span>
              </div>
            </div>
          </div>
        )}

        {/* 美元兌港元匯率 */}
        {exchangeRate && (
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <ActivityIcon className="w-5 h-5 text-green-600" />
              <h4 className="text-base font-semibold text-gray-900">美元/港元匯率</h4>
            </div>
            <div className="pl-7">
              <div className="text-2xl font-bold text-gray-900">
                {exchangeRate.rate.toFixed(3)}
              </div>
              <div className={`text-sm font-medium ${getChangeColor(exchangeRate.change)}`}>
                {getChangeIcon(exchangeRate.change)}{exchangeRate.change.toFixed(3)}
                <span className="ml-1">({getChangeIcon(exchangeRate.change_percent)}{exchangeRate.change_percent}%)</span>
              </div>
            </div>
          </div>
        )}

        {/* 數據來源說明 */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-start space-x-2">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-1"></div>
            <div className="flex-1">
              <p className="text-sm text-gray-600">
                數據來源：香港金融管理局 (HKMA)
              </p>
              <p className="text-xs text-gray-500 mt-1">
                貨幣基礎包括負債證明書、政府發行的銀行紙幣及硬幣等
              </p>
            </div>
          </div>
        </div>

        {/* 更新時間 */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            最後更新：{new Date().toLocaleString('zh-TW')}
          </p>
          <button
            onClick={fetchGovernmentData}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            刷新數據
          </button>
        </div>
      </div>
    </SquareCard>
  );
}