// Export all StrategyControl components
export { default as StrategyToggleEnhanced } from './StrategyToggleEnhanced';
export { default as BatchOperationsPanel } from './BatchOperationsPanel';
export { default as StrategyControlDashboard } from './StrategyControlDashboard';
export type { StrategyData, StrategyStatus } from './StrategyToggleEnhanced';
export type { BatchOperation } from './BatchOperationsPanel';

// Example usage component
import React, { useState } from 'react';
import { StrategyControlDashboard, StrategyData, StrategyStatus } from './';

// Example strategies data
const exampleStrategies: StrategyData[] = [
  {
    id: 'direct_rsi',
    name: '直接RSI情绪策略',
    isActive: false,
    status: 'inactive' as StrategyStatus,
    lastUpdated: '2025-12-15T10:00:00Z',
    performance: {
      sharpeRatio: 1.85,
      maxDrawdown: 0.12,
      totalReturn: 0.35,
      winRate: 0.65,
    },
  },
  {
    id: 'sentiment_momentum',
    name: '情绪动量策略',
    isActive: true,
    status: 'active' as StrategyStatus,
    lastUpdated: '2025-12-15T10:05:00Z',
    performance: {
      sharpeRatio: 2.12,
      maxDrawdown: 0.08,
      totalReturn: 0.42,
      winRate: 0.71,
    },
  },
  {
    id: 'composite_index',
    name: '综合指数策略',
    isActive: false,
    status: 'inactive' as StrategyStatus,
    lastUpdated: '2025-12-15T09:58:00Z',
    performance: {
      sharpeRatio: 1.65,
      maxDrawdown: 0.15,
      totalReturn: 0.28,
      winRate: 0.58,
    },
  },
  {
    id: 'volatility_adjusted',
    name: '波动率调整策略',
    isActive: true,
    status: 'paused' as StrategyStatus,
    lastUpdated: '2025-12-15T10:02:00Z',
    performance: {
      sharpeRatio: 1.93,
      maxDrawdown: 0.10,
      totalReturn: 0.38,
      winRate: 0.67,
    },
  },
];

/**
 * Example component showing how to use StrategyControl components
 */
export const StrategyControlExample: React.FC = () => {
  const [strategies, setStrategies] = useState<StrategyData[]>(exampleStrategies);

  const handleStrategyUpdate = (updatedStrategies: StrategyData[]) => {
    setStrategies(updatedStrategies);
    console.log('Strategies updated:', updatedStrategies);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          策略管理示例
        </h1>

        <StrategyControlDashboard
          strategies={strategies}
          onStrategyUpdate={handleStrategyUpdate}
        />

        {/* Additional example usage info */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            使用说明
          </h2>
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <p>• 点击策略开关可启用/禁用单个策略</p>
            <p>• 使用批量操作面板可同时管理多个策略</p>
            <p>• 支持搜索和按状态筛选策略</p>
            <p>• 可在网格和列表视图之间切换</p>
            <p>• 操作历史记录显示最近的策略变更</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Export the example as default
export default StrategyControlExample;