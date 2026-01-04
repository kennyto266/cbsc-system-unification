import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  ChartBarIcon,
  CogIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

import StrategySelector from '../components/StrategySelector';
import EconomicIndicators from '../components/EconomicIndicators';
import BacktestReport from '../components/BacktestReport';

interface BacktestConfig {
  strategy: {
    id: string | null;
    parameters: Record<string, any>;
  };
  timeframe: {
    start: string;
    end: string;
  };
  initialCapital: number;
  positionSizing: {
    method: 'fixed' | 'percentage' | 'volatility' | 'kelly';
    value: number;
  };
  riskManagement: {
    maxDrawdown: number;
    stopLoss: number;
    takeProfit: number;
  };
  benchmark: string;
  commission: number;
  slippage: number;
}

interface BacktestResult {
  report?: any;
  status: 'idle' | 'running' | 'completed' | 'error';
  error?: string;
  duration?: number;
}

export default function StrategyBacktest() {
  const [config, setConfig] = useState<BacktestConfig>({
    strategy: {
      id: null,
      parameters: {}
    },
    timeframe: {
      start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    initialCapital: 100000,
    positionSizing: {
      method: 'fixed',
      value: 0.1
    },
    riskManagement: {
      maxDrawdown: 20,
      stopLoss: 5,
      takeProfit: 10
    },
    benchmark: 'HSI',
    commission: 0.001,
    slippage: 0.0005
  });

  const [backtestResult, setBacktestResult] = useState<BacktestResult>({
    status: 'idle'
  });

  const [activeTab, setActiveTab] = useState<'strategy' | 'data' | 'parameters' | 'results'>('strategy');
  const [showReport, setShowReport] = useState(false);

  // Mock economic indicators data
  const [economicIndicators] = useState([
    {
      id: 'hibor',
      name: 'HIBOR Rate',
      currentValue: 4.75,
      previousValue: 4.65,
      change: 0.10,
      changePercent: 2.15,
      unit: '%',
      description: 'Hong Kong Interbank Offered Rate - 1 Month',
      lastUpdated: '2024-01-15',
      category: 'interest_rate' as const,
      trend: 'up' as const,
      historicalData: Array.from({ length: 365 }, (_, i) => ({
        date: new Date(Date.now() - (365 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 4.5 + Math.sin(i / 30) * 0.5 + Math.random() * 0.2
      })),
      thresholds: {
        high: 6.0,
        low: 2.0,
        optimal: { min: 3.0, max: 5.0 }
      }
    },
    {
      id: 'gdp_growth',
      name: 'GDP Growth',
      currentValue: 2.8,
      previousValue: 2.5,
      change: 0.3,
      changePercent: 12.0,
      unit: '%',
      description: 'Hong Kong GDP Growth Rate (Quarterly)',
      lastUpdated: '2024-01-10',
      category: 'economic_growth' as const,
      trend: 'up' as const,
      historicalData: Array.from({ length: 120 }, (_, i) => ({
        date: new Date(Date.now() - (120 - i) * 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 2.5 + Math.sin(i / 20) * 1.5 + Math.random() * 0.5
      }))
    },
    {
      id: 'visitor_arrivals',
      name: 'Visitor Arrivals',
      currentValue: 4.2,
      previousValue: 3.8,
      change: 0.4,
      changePercent: 10.53,
      unit: 'million',
      description: 'Monthly Visitor Arrivals to Hong Kong',
      lastUpdated: '2024-01-15',
      category: 'tourism' as const,
      trend: 'up' as const,
      historicalData: Array.from({ length: 60 }, (_, i) => ({
        date: new Date(Date.now() - (60 - i) * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 3.5 + i * 0.01 + Math.sin(i / 10) * 0.3 + Math.random() * 0.2
      }))
    }
  ]);

  const handleStrategySelect = (strategyId: string, parameters: Record<string, any>) => {
    setConfig(prev => ({
      ...prev,
      strategy: { id: strategyId, parameters }
    }));
  };

  const handleBacktest = async () => {
    if (!config.strategy.id) {
      alert('請先選擇策略');
      return;
    }

    setBacktestResult({ status: 'running' });
    setActiveTab('results');

    const startTime = Date.now();

    try {
      // Call real backend API
      const response = await fetch('http://localhost:3007/api/backtest/strategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: '0700.HK', // TODO: Allow user to select symbol
          strategy: {
            name: config.strategy.id,
            type: 'ma_cross',
            ...config.strategy.parameters
          },
          start_date: config.timeframe.start,
          end_date: config.timeframe.end,
          initial_capital: config.initialCapital
        })
      });

      const result = await response.json();

      if (!response.ok) {
        // Handle error responses
        throw new Error(result.detail || result.message || '回測失敗');
      }

      // Check data source
      if (result.data_source === 'yahoo_finance') {
        console.log('✅ 使用 Yahoo Finance 真實數據');
      }

      const duration = (Date.now() - startTime) / 1000;

      // Transform API response to match expected format
      const transformedReport = {
        id: `bt_${Date.now()}`,
        strategyName: result.data.strategy_name,
        strategy: {
          name: result.data.strategy_name,
          parameters: config.strategy.parameters,
          category: 'technical'
        },
        period: {
          start: result.data.start_date,
          end: result.data.end_date,
          duration: Math.ceil(
            (new Date(result.data.end_date).getTime() - new Date(result.data.start_date).getTime()) /
            (1000 * 60 * 60 * 24)
          )
        },
        metrics: {
          totalReturn: result.data.total_return / 100,
          annualizedReturn: result.data.annual_return / 100,
          maxDrawdown: result.data.max_drawdown / 100,
          sharpeRatio: result.data.sharpe_ratio,
          sortinoRatio: result.data.sharpe_ratio * 0.9, // Approximate
          calmarRatio: Math.abs(result.data.total_return / Math.abs(result.data.max_drawdown)),
          volatility: 0.1223, // Could calculate from returns
          winRate: result.data.win_rate / 100,
          profitFactor: result.data.profit_factor,
          averageWin: result.data.avg_profit,
          averageLoss: Math.abs(result.data.avg_loss),
          totalTrades: result.data.total_trades,
          winningTrades: result.data.profit_trades,
          losingTrades: result.data.loss_trades
        },
        equityCurve: [], // API doesn't return this yet
        trades: result.data.trades || [],
        monthlyReturns: [], // API doesn't return this yet
        riskMetrics: {
          beta: 1.0,
          alpha: result.data.total_return / 100 - 0.08,
          jensenAlpha: result.data.total_return / 100 - 0.08,
          treynorRatio: (result.data.total_return / 100) / 1.0,
          informationRatio: result.data.sharpe_ratio * 0.5
        },
        generatedAt: result.timestamp,
        dataQualityScore: result.data.data_quality_score,
        dataSource: result.data_source,
        reportFiles: {
          pdf: `/reports/bt_${Date.now()}.pdf`,
          excel: `/reports/bt_${Date.now()}.xlsx`,
          html: `/reports/bt_${Date.now()}.html`,
          json: `/reports/bt_${Date.now()}.json`
        }
      };

      setBacktestResult({
        status: 'completed',
        report: transformedReport,
        duration: duration
      });

    } catch (error: any) {
      console.error('Backtest error:', error);
      setBacktestResult({
        status: 'error',
        error: error.message || '回測失敗，請稍後再試'
      });
    }
  };

  const renderConfigPanel = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Backtest Configuration</h2>

      <div className="space-y-6">
        {/* Time Frame */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Backtest Period</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Start Date</label>
              <input
                type="date"
                value={config.timeframe.start}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  timeframe: { ...prev.timeframe, start: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={config.timeframe.end}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  timeframe: { ...prev.timeframe, end: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Initial Capital */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Initial Capital</label>
          <div className="relative">
            <span className="absolute left-3 top-2 text-gray-500">$</span>
            <input
              type="number"
              value={config.initialCapital}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                initialCapital: parseFloat(e.target.value)
              }))}
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Position Sizing */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Position Sizing</label>
          <select
            value={config.positionSizing.method}
            onChange={(e) => setConfig(prev => ({
              ...prev,
              positionSizing: { ...prev.positionSizing, method: e.target.value as any }
            }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
          >
            <option value="fixed">Fixed Size</option>
            <option value="percentage">Percentage of Capital</option>
            <option value="volatility">Volatility-Based</option>
            <option value="kelly">Kelly Criterion</option>
          </select>
          <div className="relative">
            <input
              type="number"
              step="0.01"
              value={config.positionSizing.value}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                positionSizing: { ...prev.positionSizing, value: parseFloat(e.target.value) }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={
                config.positionSizing.method === 'fixed' ? 'Number of shares' :
                config.positionSizing.method === 'percentage' ? 'Percentage (0-1)' :
                config.positionSizing.method === 'volatility' ? 'Risk per trade (%)' :
                'Kelly fraction multiplier'
              }
            />
          </div>
        </div>

        {/* Risk Management */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Risk Management</label>
          <div className="space-y-3">
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Max Drawdown (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.riskManagement.maxDrawdown}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  riskManagement: { ...prev.riskManagement, maxDrawdown: parseFloat(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Stop Loss (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.riskManagement.stopLoss}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  riskManagement: { ...prev.riskManagement, stopLoss: parseFloat(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Take Profit (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.riskManagement.takeProfit}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  riskManagement: { ...prev.riskManagement, takeProfit: parseFloat(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Trading Costs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Trading Costs</label>
          <div className="space-y-3">
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Commission (%)</label>
              <input
                type="number"
                step="0.001"
                value={config.commission}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  commission: parseFloat(e.target.value)
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Slippage (%)</label>
              <input
                type="number"
                step="0.001"
                value={config.slippage}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  slippage: parseFloat(e.target.value)
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Run Button */}
        <button
          onClick={handleBacktest}
          disabled={backtestResult.status === 'running' || !config.strategy.id}
          className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {backtestResult.status === 'running' ? (
            <>
              <ArrowPathIcon className="w-5 h-5 animate-spin" />
              <span>Running Backtest...</span>
            </>
          ) : (
            <>
              <PlayIcon className="w-5 h-5" />
              <span>Run Backtest</span>
            </>
          )}
        </button>

        {/* Status Messages */}
        {backtestResult.status === 'completed' && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 p-3 bg-green-50 text-green-800 rounded-md">
              <CheckCircleIcon className="w-5 h-5" />
              <span>回測成功完成！耗時 {backtestResult.duration?.toFixed(2)} 秒</span>
            </div>
            {backtestResult.report?.dataSource && (
              <div className="flex items-center space-x-2 p-3 bg-blue-50 text-blue-800 rounded-md">
                <CheckCircleIcon className="w-5 h-5" />
                <span>
                  數據源: {backtestResult.report.dataSource === 'yahoo_finance' ? 'Yahoo Finance (真實市場數據)' : '模擬數據'}
                  {backtestResult.report.dataQualityScore !== undefined && (
                    <span className="ml-2">· 數據質量: {(backtestResult.report.dataQualityScore * 100).toFixed(0)}%</span>
                  )}
                </span>
              </div>
            )}
          </div>
        )}

        {backtestResult.status === 'error' && (
          <div className="flex items-start space-x-2 p-3 bg-red-50 text-red-800 rounded-md">
            <ExclamationCircleIcon className="w-5 h-5 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium">回測失敗</p>
              <p className="text-sm mt-1">{backtestResult.error}</p>
              {backtestResult.error?.includes('Yahoo Finance') && (
                <p className="text-xs mt-2 text-red-600">
                  提示: 請檢查股票代碼是否正確（例如: 0700.HK, AAPL），或稍後再試。
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Strategy Backtesting</h1>
          <p className="mt-2 text-gray-600">
            Test your trading strategies with historical data and analyze performance metrics
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="flex -mb-px">
            {[
              { id: 'strategy', label: 'Select Strategy', icon: ChartBarIcon },
              { id: 'data', label: 'Economic Data', icon: DocumentTextIcon },
              { id: 'parameters', label: 'Parameters', icon: CogIcon },
              { id: 'results', label: 'Results', icon: ChartBarIcon }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Strategy/Config */}
          <div className="lg:col-span-2 space-y-8">
            {activeTab === 'strategy' && (
              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">Choose a Strategy</h2>
                <StrategySelector
                  selectedStrategy={config.strategy.id}
                  onStrategySelect={handleStrategySelect}
                />
              </div>
            )}

            {activeTab === 'data' && (
              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">Economic Indicators</h2>
                <EconomicIndicators indicators={economicIndicators} />
              </div>
            )}

            {activeTab === 'parameters' && renderConfigPanel()}

            {activeTab === 'results' && backtestResult.report && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Backtest Results</h2>
                  <button
                    onClick={() => setShowReport(!showReport)}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    {showReport ? 'Hide' : 'Show'} Full Report
                  </button>
                </div>
                {showReport ? (
                  <BacktestReport report={backtestResult.report} />
                ) : (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <span className="text-sm text-gray-500">Total Return</span>
                        <p className="text-2xl font-bold text-gray-900">
                          {(backtestResult.report.metrics.totalReturn * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Sharpe Ratio</span>
                        <p className="text-2xl font-bold text-gray-900">
                          {backtestResult.report.metrics.sharpeRatio.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Max Drawdown</span>
                        <p className="text-2xl font-bold text-red-600">
                          {(backtestResult.report.metrics.maxDrawdown * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Win Rate</span>
                        <p className="text-2xl font-bold text-gray-900">
                          {(backtestResult.report.metrics.winRate * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column - Config Panel (always visible) */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-8 space-y-6">
              {/* Current Configuration */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="font-medium text-gray-900 mb-4">Current Configuration</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-500">Strategy:</span>
                    <span className="ml-2 font-medium">
                      {config.strategy.id ? config.strategy.id : 'Not selected'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Period:</span>
                    <span className="ml-2 font-medium">
                      {config.timeframe.start} to {config.timeframe.end}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Capital:</span>
                    <span className="ml-2 font-medium">${config.initialCapital.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="font-medium text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => setActiveTab('strategy')}
                    className="w-full text-left px-4 py-2 bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Change Strategy
                  </button>
                  <button
                    onClick={() => setActiveTab('parameters')}
                    className="w-full text-left px-4 py-2 bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Adjust Parameters
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="w-full text-left px-4 py-2 bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Print Results
                  </button>
                </div>
              </div>

              {/* Help Tips */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Pro Tips</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Test multiple strategies to compare performance</li>
                  <li>• Consider economic indicators for fundamental strategies</li>
                  <li>• Use risk management settings to limit losses</li>
                  <li>• Validate results with out-of-sample testing</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}