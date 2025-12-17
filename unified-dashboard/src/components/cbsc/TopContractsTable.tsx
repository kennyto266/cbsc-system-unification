/**
 * 牛熊证前十名表格组件
 * Top CBSC Contracts Table Component
 */

import React, { useState } from 'react';
import { CBSCTopContracts, CBSCContract } from '../../types/cbsc';

interface TopContractsTableProps {
  contracts: CBSCTopContracts;
  loading?: boolean;
}

const TopContractsTable: React.FC<TopContractsTableProps> = ({ contracts, loading = false }) => {
  const [activeTab, setActiveTab] = useState<'bull' | 'bear'>('bull');

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toFixed(decimals);
  };

  // 格式化交易量
  const formatVolume = (volume: number): string => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  };

  // 获取涨跌颜色
  const getChangeColor = (change: number): string => {
    if (change > 0) return 'text-red-600'; // 港股红色表示上涨
    if (change < 0) return 'text-green-600'; // 港股绿色表示下跌
    return 'text-gray-600';
  };

  // 渲染合约行
  const renderContractRow = (contract: CBSCContract, index: number) => (
    <tr key={contract.code} className="hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3 text-sm">
        <span className="font-medium text-gray-900">#{contract.rank}</span>
      </td>
      <td className="px-4 py-3">
        <div>
          <div className="text-sm font-medium text-gray-900">{contract.code}</div>
          <div className="text-xs text-gray-500">{contract.name}</div>
        </div>
      </td>
      <td className="px-4 py-3 text-sm font-medium text-gray-900">
        {formatNumber(contract.price, 4)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {formatNumber(contract.strike)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {contract.leverage}x
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {formatVolume(contract.volume)}
      </td>
      <td className="px-4 py-3 text-sm font-medium">
        <span className={getChangeColor(contract.change)}>
          {contract.change >= 0 ? '+' : ''}{formatNumber(contract.change)}%
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {new Date(contract.expiry).toLocaleDateString('zh-CN')}
      </td>
    </tr>
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">🏆</span>
        牛熊证前十名
      </h3>

      {/* Tab 切换 */}
      <div className="flex space-x-1 mb-4 bg-gray-100 p-1 rounded-lg">
        <button
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'bull'
              ? 'bg-white text-red-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('bull')}
        >
          牛证 (看涨)
        </button>
        <button
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'bear'
              ? 'bg-white text-green-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('bear')}
        >
          熊证 (看跌)
        </button>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                排名
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                代码/名称
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                价格
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                行使价
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                杠杆
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                成交量
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                变动
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                到期日
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {activeTab === 'bull'
              ? contracts.bull_contracts.map((contract, index) => renderContractRow(contract, index))
              : contracts.bear_contracts.map((contract, index) => renderContractRow(contract, index))
            }
          </tbody>
        </table>
      </div>

      {/* 底部统计 */}
      <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between text-sm text-gray-600">
        <div>
          总计 {activeTab === 'bull' ? contracts.bull_contracts.length : contracts.bear_contracts.length} 只合约
        </div>
        <div className="flex space-x-4">
          <span>
            平均杠杆: {activeTab === 'bull'
              ? (contracts.bull_contracts.reduce((sum, c) => sum + c.leverage, 0) / contracts.bull_contracts.length).toFixed(1)
              : (contracts.bear_contracts.reduce((sum, c) => sum + c.leverage, 0) / contracts.bear_contracts.length).toFixed(1)
            }x
          </span>
          <span>
            总成交量: {formatVolume(
              activeTab === 'bull'
                ? contracts.bull_contracts.reduce((sum, c) => sum + c.volume, 0)
                : contracts.bear_contracts.reduce((sum, c) => sum + c.volume, 0)
            )}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TopContractsTable;