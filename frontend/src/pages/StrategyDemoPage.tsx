/**
 * Strategy Demo Page
 * 策略功能演示頁面 - 展示策略嚮導和數據導出功能
 */

import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { StrategyWizard } from '../components/StrategyWizard';
import { DataExporter, ShareManager } from '../components/DataExport';
import { StrategyActionButtons } from '../components/StrategyIntegration/StrategyActionButtons';
import {
  PlayIcon,
  ChartBarIcon,
  DocumentTextIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { Strategy } from '../types/strategyTypes';

// Mock strategy data for demo
const mockStrategies: Strategy[] = [
  {
    id: 'strategy-1',
    name: 'RSI 動量策略',
    description: '基於 RSI 指標的動量策略',
    strategy_type: 'momentum' as any,
    version: '1.0.0',
    is_active: true,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    parameters: {
      rsi_period: 14,
      rsi_oversold: 30,
      rsi_overbought: 70
    },
    metadata: {},
    user_id: 'user-1',
    performance_summary: {
      total_return: 0.15,
      annual_return: 0.18,
      volatility: 0.12,
      sharpe_ratio: 1.5,
      max_drawdown: -0.05,
      total_trades: 45,
      win_rate: 0.64,
      profit_factor: 1.8,
      last_updated: '2024-01-20T00:00:00Z'
    }
  },
  {
    id: 'strategy-2',
    name: '均值回歸策略',
    description: '布林帶均值回歸交易策略',
    strategy_type: 'mean_reversion' as any,
    version: '1.2.0',
    is_active: true,
    created_at: '2024-01-10T10:00:00Z',
    updated_at: '2024-01-18T10:00:00Z',
    parameters: {
      bb_period: 20,
      bb_std: 2,
      entry_threshold: 0.02
    },
    metadata: {},
    user_id: 'user-1'
  }
];

export const StrategyDemoPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>(mockStrategies);
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showShare, setShowShare] = useState(false);

  const handleStrategyCreated = (strategy: Strategy) => {
    setStrategies(prev => [...prev, strategy]);
  };

  const handleStrategySelect = (strategyId: string) => {
    setSelectedStrategies(prev => {
      if (prev.includes(strategyId)) {
        return prev.filter(id => id !== strategyId);
      } else {
        return [...prev, strategyId];
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            策略管理演示
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            展示策略配置嚮導、數據導出和分享功能
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center mb-4">
              <SparklesIcon className="w-8 h-8 text-blue-600 dark:text-blue-400 mr-3" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                智能策略嚮導
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              分步引導創建策略，提供智能建議和預設配置，支持草稿保存和恢復。
            </p>
            <Button
              variant="primary"
              onClick={() => setShowWizard(true)}
              className="w-full"
            >
              開始創建
            </Button>
          </Card>

          <Card className="p-6">
            <div className="flex items-center mb-4">
              <DocumentTextIcon className="w-8 h-8 text-green-600 dark:text-green-400 mr-3" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                多格式導出
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              支持導出為 CSV、JSON、PDF 和 PNG 格式，包含元數據和自定義報告模板。
            </p>
            <Button
              variant="outline"
              onClick={() => setShowExport(true)}
              className="w-full"
            >
              導出數據
            </Button>
          </Card>

          <Card className="p-6">
            <div className="flex items-center mb-4">
              <ShareIcon className="w-8 h-8 text-purple-600 dark:text-purple-400 mr-3" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                安全分享
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              生成安全的分享鏈接，支持密碼保護、過期時間和訪問權限控制。
            </p>
            <Button
              variant="outline"
              onClick={() => setShowShare(true)}
              className="w-full"
              disabled={selectedStrategies.length !== 1}
            >
              分享策略
            </Button>
          </Card>
        </div>

        {/* Action Buttons */}
        <Card className="p-6 mb-8">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            快速操作
          </h3>
          <StrategyActionButtons
            strategies={strategies}
            selectedStrategies={selectedStrategies}
            onStrategyCreated={handleStrategyCreated}
          />
        </Card>

        {/* Strategy List */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            策略列表
          </h3>
          <div className="space-y-3">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className={`
                  p-4 rounded-lg border cursor-pointer transition-colors
                  ${selectedStrategies.includes(strategy.id)
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }
                `}
                onClick={() => handleStrategySelect(strategy.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {strategy.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {strategy.description}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {strategy.is_active && (
                      <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                        活躍
                      </span>
                    )}
                    {strategy.performance_summary && (
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {(strategy.performance_summary.total_return * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Modals */}
      <StrategyWizard
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        onComplete={(strategy) => {
          handleStrategyCreated(strategy);
          setShowWizard(false);
        }}
      />

      <DataExporter
        isOpen={showExport}
        onClose={() => setShowExport(false)}
        data={strategies}
        title={`策略數據_${new Date().toISOString().slice(0, 10)}`}
        type="strategy"
      />

      <ShareManager
        isOpen={showShare}
        onClose={() => setShowShare(false)}
        strategyId={selectedStrategies[0]}
      />
    </div>
  );
};