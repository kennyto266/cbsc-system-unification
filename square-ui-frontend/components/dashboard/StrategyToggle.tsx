'use client';

import React, { useState } from 'react';
import { SquareCard, SquareButton, SquareBadge } from '@/components/ui';
import {
  PowerIcon,
  PauseIcon,
  PlayIcon,
  SettingsIcon,
  AlertTriangleIcon,
  CheckCircleIcon
} from 'lucide-react';

interface Strategy {
  id: string;
  name: string;
  status: 'enabled' | 'disabled' | 'error';
  lastSignal?: {
    timestamp: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    price: number;
    symbol: string;
  };
  performance: {
    sharpe_ratio: number;
    max_drawdown: number;
    total_return: number;
    win_rate: number;
  };
  description: string;
}

interface StrategyToggleProps {
  strategies?: Strategy[];
  onToggle?: (strategyId: string, enabled: boolean) => void;
}

export default function StrategyToggle({ strategies: propStrategies, onToggle }: StrategyToggleProps) {
  // 使用模擬數據或傳入的策略數據
  const [strategies, setStrategies] = useState<Strategy[]>(
    propStrategies || [
      {
        id: '1',
        name: 'DirectRSIStrategy',
        status: 'enabled',
        lastSignal: {
          timestamp: '2025-12-16T10:30:00Z',
          action: 'BUY',
          price: 385.20,
          symbol: '0700.HK'
        },
        performance: {
          sharpe_ratio: 1.23,
          max_drawdown: 0.15,
          total_return: 0.25,
          win_rate: 0.68
        },
        description: '基於RSI指標的直接交易策略'
      },
      {
        id: '2',
        name: 'MACDCrossStrategy',
        status: 'enabled',
        lastSignal: {
          timestamp: '2025-12-16T09:45:00Z',
          action: 'SELL',
          price: 52.15,
          symbol: '0941.HK'
        },
        performance: {
          sharpe_ratio: 0.95,
          max_drawdown: 0.12,
          total_return: 0.18,
          win_rate: 0.62
        },
        description: 'MACD交叉策略，捕捉趨勢變化'
      },
      {
        id: '3',
        name: 'BollingerBandsStrategy',
        status: 'disabled',
        lastSignal: {
          timestamp: '2025-12-15T15:20:00Z',
          action: 'HOLD',
          price: 145.60,
          symbol: '2318.HK'
        },
        performance: {
          sharpe_ratio: 1.45,
          max_drawdown: 0.18,
          total_return: 0.32,
          win_rate: 0.72
        },
        description: '布林帶策略，利用價格波動範圍'
      },
      {
        id: '4',
        name: 'VWAPStrategy',
        status: 'enabled',
        lastSignal: {
          timestamp: '2025-12-16T11:15:00Z',
          action: 'BUY',
          price: 282.40,
          symbol: '1299.HK'
        },
        performance: {
          sharpe_ratio: 1.12,
          max_drawdown: 0.14,
          total_return: 0.22,
          win_rate: 0.65
        },
        description: '成交量加權平均價策略'
      }
    ]
  );

  const [toggling, setToggling] = useState<string | null>(null);

  // 處理策略切換
  const handleToggle = async (strategyId: string) => {
    setToggling(strategyId);

    try {
      // 更新本地狀態
      setStrategies(prev => prev.map(strategy =>
        strategy.id === strategyId
          ? {
              ...strategy,
              status: strategy.status === 'enabled' ? 'disabled' : 'enabled'
            }
          : strategy
      ));

      // 調用外部回調
      if (onToggle) {
        const strategy = strategies.find(s => s.id === strategyId);
        if (strategy) {
          await onToggle(strategyId, strategy.status === 'enabled');
        }
      }

      // 模擬 API 調用
      console.log(`Strategy ${strategyId} ${strategies.find(s => s.id === strategyId)?.status === 'enabled' ? 'enabled' : 'disabled'}`);

    } catch (error) {
      console.error('Failed to toggle strategy:', error);
      // 錯誤時恢復狀態
      setStrategies(prev => prev.map(strategy =>
        strategy.id === strategyId
          ? {
              ...strategy,
              status: strategy.status === 'enabled' ? 'disabled' : 'enabled'
            }
          : strategy
      ));
    } finally {
      setToggling(null);
    }
  };

  // 獲取狀態顯示
  const getStatusDisplay = (status: Strategy['status']) => {
    switch (status) {
      case 'enabled':
        return {
          badge: <SquareBadge status="success" size="sm">運行中</SquareBadge>,
          icon: PlayIcon,
          color: 'text-green-600',
          bgColor: 'bg-green-50'
        };
      case 'disabled':
        return {
          badge: <SquareBadge status="default" size="sm">已暫停</SquareBadge>,
          icon: PauseIcon,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50'
        };
      case 'error':
        return {
          badge: <SquareBadge status="error" size="sm">錯誤</SquareBadge>,
          icon: AlertTriangleIcon,
          color: 'text-red-600',
          bgColor: 'bg-red-50'
        };
    }
  };

  // 獲取信號操作顏色
  const getSignalColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return 'text-green-600 bg-green-100';
      case 'SELL':
        return 'text-red-600 bg-red-100';
      case 'HOLD':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <SquareCard>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">策略控制</h3>
          <SquareButton
            variant="outline"
            size="sm"
            icon={<SettingsIcon size={16} />}
          >
            策略設置
          </SquareButton>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {strategies.map((strategy) => {
            const statusDisplay = getStatusDisplay(strategy.status);
            const StatusIcon = statusDisplay.icon;

            return (
              <div
                key={strategy.id}
                className={`p-4 rounded-lg border transition-all duration-200 ${
                  strategy.status === 'enabled'
                    ? 'border-green-200 bg-green-50'
                    : strategy.status === 'error'
                    ? 'border-red-200 bg-red-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  {/* 左側：策略信息 */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-base font-medium text-gray-900">
                        {strategy.name.replace('Strategy', '')}
                      </h4>
                      {statusDisplay.badge}
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      {strategy.description}
                    </p>

                    {/* 性能指標 */}
                    <div className="flex items-center space-x-4 text-sm">
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-500">Sharpe:</span>
                        <span className={`font-medium ${
                          strategy.performance.sharpe_ratio > 1 ? 'text-green-600' : 'text-gray-600'
                        }`}>
                          {strategy.performance.sharpe_ratio.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-500">回報:</span>
                        <span className={`font-medium ${
                          strategy.performance.total_return > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {(strategy.performance.total_return * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-500">勝率:</span>
                        <span className={`font-medium ${
                          strategy.performance.win_rate > 0.6 ? 'text-green-600' :
                          strategy.performance.win_rate > 0.4 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {(strategy.performance.win_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 中間：最後信號 */}
                  {strategy.lastSignal && (
                    <div className="flex flex-col items-center mx-6">
                      <span className="text-xs text-gray-500 mb-1">最後信號</span>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${getSignalColor(strategy.lastSignal.action)}`}>
                        {strategy.lastSignal.action}
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        ${strategy.lastSignal.price.toFixed(2)}
                      </span>
                      <span className="text-xs text-gray-400">
                        {strategy.lastSignal.symbol}
                      </span>
                    </div>
                  )}

                  {/* 右側：切換按鈕 */}
                  <div className="flex items-center space-x-2">
                    <SquareButton
                      variant={strategy.status === 'enabled' ? 'primary' : 'outline'}
                      size="sm"
                      onClick={() => handleToggle(strategy.id)}
                      loading={toggling === strategy.id}
                      icon={
                        toggling === strategy.id ? null :
                        strategy.status === 'enabled' ?
                          <PauseIcon size={16} /> :
                          <PlayIcon size={16} />
                      }
                    >
                      {strategy.status === 'enabled' ? '暫停' : '啟動'}
                    </SquareButton>

                    {strategy.status === 'error' && (
                      <div className="flex items-center space-x-1 text-red-600">
                        <AlertTriangleIcon size={16} />
                        <span className="text-xs">需要檢查</span>
                      </div>
                    )}

                    {strategy.status === 'enabled' && (
                      <div className="flex items-center space-x-1 text-green-600">
                        <CheckCircleIcon size={16} />
                        <span className="text-xs">運行中</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 錯誤狀態詳情 */}
                {strategy.status === 'error' && (
                  <div className="mt-3 pt-3 border-t border-red-200">
                    <p className="text-sm text-red-600">
                      策略執行遇到錯誤，請檢查策略配置或聯繫技術支持。
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 批量操作 */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              共 {strategies.length} 個策略，
              {strategies.filter(s => s.status === 'enabled').length} 個運行中，
              {strategies.filter(s => s.status === 'disabled').length} 個已暫停
            </div>
            <div className="flex items-center space-x-2">
              <SquareButton
                variant="outline"
                size="sm"
                onClick={() => {
                  const disabledStrategies = strategies.filter(s => s.status === 'disabled');
                  disabledStrategies.forEach(s => handleToggle(s.id));
                }}
                disabled={strategies.filter(s => s.status === 'disabled').length === 0}
              >
                全部啟動
              </SquareButton>
              <SquareButton
                variant="outline"
                size="sm"
                onClick={() => {
                  const enabledStrategies = strategies.filter(s => s.status === 'enabled');
                  enabledStrategies.forEach(s => handleToggle(s.id));
                }}
                disabled={strategies.filter(s => s.status === 'enabled').length === 0}
              >
                全部暫停
              </SquareButton>
            </div>
          </div>
        </div>

        {/* 風險提示 */}
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start space-x-2">
            <AlertTriangleIcon className="w-4 h-4 text-yellow-600 mt-0.5" />
            <div>
              <p className="text-xs text-yellow-800">
                <strong>注意：</strong>啟動策略將開始實時交易。請確保已正確配置策略參數並了解相關風險。
              </p>
            </div>
          </div>
        </div>
      </div>
    </SquareCard>
  );
}