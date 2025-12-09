import React from 'react';
import { StrategyFilter } from '../../types/strategy';

interface StrategyFiltersProps {
  filters: StrategyFilter;
  onFilterChange: (filters: Partial<StrategyFilter>) => void;
  strategyCount: number;
}

export const StrategyFilters: React.FC<StrategyFiltersProps> = ({
  filters,
  onFilterChange,
  strategyCount
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">策略筛选</h3>
        <span className="text-sm text-gray-500">
          显示 {strategyCount} 个策略
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            策略类别
          </label>
          <select
            value={filters.category}
            onChange={(e) => onFilterChange({ category: e.target.value as StrategyFilter['category'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">全部类别</option>
            <option value="core_cbsc">核心CBSC</option>
            <option value="monthly">月度策略</option>
            <option value="multi_strategy">多策略组合</option>
            <option value="multi_factor">多因子模型</option>
            <option value="other">其他</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            运行状态
          </label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ status: e.target.value as StrategyFilter['status'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">全部状态</option>
            <option value="active">运行中</option>
            <option value="inactive">已停止</option>
            <option value="processing">处理中</option>
            <option value="error">错误</option>
          </select>
        </div>

        {/* Performance Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            表现评级
          </label>
          <select
            value={filters.performance}
            onChange={(e) => onFilterChange({ performance: e.target.value as StrategyFilter['performance'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">全部评级</option>
            <option value="excellent">优秀 (S级, Sharpe≥1.5)</option>
            <option value="good">良好 (A级, Sharpe≥1.0)</option>
            <option value="average">一般 (B级, Sharpe≥0.8)</option>
            <option value="poor">待改进 (C级及以下)</option>
          </select>
        </div>
      </div>

      {/* Quick Filter Buttons */}
      <div className="flex flex-wrap gap-2 mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={() => onFilterChange({ category: 'core_cbsc', status: 'active', performance: 'all' })}
          className="px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          核心CBSC策略
        </button>
        <button
          onClick={() => onFilterChange({ category: 'all', status: 'active', performance: 'excellent' })}
          className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          优秀策略
        </button>
        <button
          onClick={() => onFilterChange({ category: 'all', status: 'all', performance: 'all' })}
          className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          重置筛选
        </button>
      </div>
    </div>
  );
};