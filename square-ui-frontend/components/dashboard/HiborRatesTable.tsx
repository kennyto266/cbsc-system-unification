'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';

interface HiborData {
  date: string;
  overnight: number;
  one_week: number;
  one_month: number;
  two_months: number;
  three_months: number;
  six_months: number;
  twelve_months: number;
}

interface HiborRatesTableProps {
  className?: string;
}

export default function HiborRatesTable({ className }: HiborRatesTableProps) {
  const [data, setData] = useState<HiborData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHiborData();
    // 每30秒更新一次
    const interval = setInterval(fetchHiborData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHiborData = async () => {
    try {
      const response = await fetch('/api/government/hibor?days=7');
      const result = await response.json();

      if (result.success) {
        setData(result.history || []);
        setError(null);
      } else {
        setError(result.message || '獲取數據失敗');
      }
    } catch (err) {
      console.error('Failed to fetch HIBOR data:', err);
      setError('網絡錯誤，請稍後重試');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number | string) => {
    const value = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(value)) return '0.00';
    return value.toFixed(2);
  };

  const getChangeColor = (current: number | string, previous: number | string) => {
    const currentValue = typeof current === 'string' ? parseFloat(current) : current;
    const previousValue = typeof previous === 'string' ? parseFloat(previous) : previous;

    if (isNaN(currentValue) || isNaN(previousValue)) return 'text-gray-600';

    const diff = currentValue - previousValue;
    if (diff > 0) return 'text-green-600';
    if (diff < 0) return 'text-red-600';
    return 'text-gray-600';
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

  return (
    <SquareCard className={className}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">HIBOR 利率</h3>
          <SquareBadge status="active" size="sm">
            香港銀行同業拆息
          </SquareBadge>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                日期
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                隔夜
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                1週
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                1個月
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                3個月
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                6個月
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                12個月
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, index) => {
              const previousRow = data[index + 1];
              return (
                <tr key={row.date} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.date}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.overnight, previousRow.overnight) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.overnight)}%
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.one_week, previousRow.one_week) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.one_week)}%
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.one_month, previousRow.one_month) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.one_month)}%
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.three_months, previousRow.three_months) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.three_months)}%
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.six_months, previousRow.six_months) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.six_months)}%
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-center ${
                    previousRow ? getChangeColor(row.twelve_months, previousRow.twelve_months) : 'text-gray-900'
                  }`}>
                    {formatNumber(row.twelve_months)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-4 bg-gray-50 text-xs text-gray-500">
        <p>數據來源：香港金融管理局 (HKMA) | 更新時間：{new Date().toLocaleTimeString('zh-TW')}</p>
      </div>
    </SquareCard>
  );
}