'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface ContractData {
  rank: number;
  code: string;
  ticker: string;
  name: string;
  type: string;
  currency: string;
  volume: number;
  turnover: number;
  high: number;
  low: number;
}

export default function TopCBBCContracts({ className }: { className?: string }) {
  const [data, setData] = useState<ContractData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTopContracts();
    const interval = setInterval(fetchTopContracts, 30000); // 每30秒更新
    return () => clearInterval(interval);
  }, []);

  const fetchTopContracts = async () => {
    try {
      const response = await fetch('/api/data/cbbc?type=top-10');
      const result = await response.json();

      if (result.success) {
        setData(result.data);
        setError(null);
      } else {
        setError('獲取數據失敗');
      }
    } catch (err) {
      console.error('Failed to fetch top contracts:', err);
      setError('網絡錯誤');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1e9) {
      return (num / 1e9).toFixed(2) + 'B';
    } else if (num >= 1e6) {
      return (num / 1e6).toFixed(2) + 'M';
    } else if (num >= 1e3) {
      return (num / 1e3).toFixed(2) + 'K';
    }
    return num.toFixed(0);
  };

  const formatPrice = (price: number) => {
    return price.toFixed(3);
  };

  const getTypeIcon = (type: string) => {
    return type === '牛證' ?
      <TrendingUp className="w-4 h-4 text-green-600" /> :
      <TrendingDown className="w-4 h-4 text-red-600" />;
  };

  const getTypeBadge = (type: string) => {
    return type === '牛證' ?
      <SquareBadge status="success" size="sm">牛證</SquareBadge> :
      <SquareBadge status="error" size="sm">熊證</SquareBadge>;
  };

  if (loading) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
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
          <h3 className="text-lg font-medium text-gray-900">牛熊證成交排行榜</h3>
          <div className="flex items-center space-x-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray-600">按成交額排序</span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                排名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                代碼/名稱
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                類型
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                成交量
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                成交額 (HK$)
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                價格區間
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((contract) => (
              <tr key={contract.rank} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${
                      contract.rank <= 3 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                    } font-medium text-sm`}>
                      {contract.rank}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {contract.code}
                    </div>
                    <div className="text-xs text-gray-500 truncate max-w-[150px]">
                      {contract.name}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center space-x-2">
                    {getTypeIcon(contract.type)}
                    {getTypeBadge(contract.type)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  {formatNumber(contract.volume)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatNumber(contract.turnover)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="text-xs text-gray-600">
                    <div className="flex items-center justify-center space-x-1">
                      <span>{formatPrice(contract.low)}</span>
                      <span>-</span>
                      <span>{formatPrice(contract.high)}</span>
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-4 bg-gray-50 text-xs text-gray-500">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <span>數據來源：港交所 CBSC</span>
            <span>|</span>
            <span>前 10 名活躍合約</span>
          </div>
          <span>更新：{new Date().toLocaleTimeString('zh-TW')}</span>
        </div>
      </div>
    </SquareCard>
  );
}