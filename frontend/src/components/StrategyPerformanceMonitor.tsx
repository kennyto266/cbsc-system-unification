/**
 * Strategy Performance Monitor Component
 * 策略性能監控組件
 */

import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ArrowPathIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Select } from './ui/Select';
import { Loading } from './ui/Loading';
import { Alert } from './ui/Alert';

import { PerformanceMetricsResponse } from '../types/strategyTypes';

interface StrategyPerformanceMonitorProps {
  strategyId: string;
  strategyName?: string;
  timeRange?: string;
  onTimeRangeChange?: (timeRange: string) => void;
  refreshInterval?: number; // Auto refresh interval in milliseconds
}

interface PerformanceSummary {
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  volatility: number;
  winRate: number;
  totalTrades: number;
  profitFactor: number;
}

export const StrategyPerformanceMonitor: React.FC<StrategyPerformanceMonitorProps> = ({
  strategyId,
  strategyName,
  timeRange = '1M',
  onTimeRangeChange,
  refreshInterval = 60000 // Default refresh every minute
}) => {
  const [performance, setPerformance] = useState<PerformanceMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Time range options
  const timeRangeOptions = [
    { value: '1D', label: '1天' },
    { value: '1W', label: '1周' },
    { value: '1M', label: '1月' },
    { value: '3M', label: '3月' },
    { value: '6M', label: '6月' },
    { value: '1Y', label: '1年' },
    { value: 'ALL', label: '全部' }
  ];

  // Load performance data
  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      setError(null);

      // This would be replaced with actual API call
      // const response = await strategyAPI.getStrategyPerformance(strategyId, { time_range: timeRange });

      // Mock data for demonstration
      const mockPerformance: PerformanceMetricsResponse = {
        strategy_id: strategyId,
        time_range: timeRange,
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: new Date().toISOString(),
        total_return: 0.125,
        annualized_return: 0.456,
        max_drawdown: -0.082,
        sharpe_ratio: 1.45,
        sortino_ratio: 2.01,
        volatility: 0.184,
        win_rate: 0.62,
        profit_factor: 1.78,
        total_trades: 156,
        winning_trades: 97,
        losing_trades: 59,
        average_win: 0.023,
        average_loss: -0.014,
        largest_win: 0.089,
        largest_loss: -0.045,
        calmar_ratio: 1.34,
        beta: 0.89,
        alpha: 0.234,
        information_ratio: 0.87
      };

      setPerformance(mockPerformance);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : '載入性能數據失敗');
    } finally {
      setLoading(false);
    }
  };

  // Initial load and refresh
  useEffect(() => {
    loadPerformanceData();
  }, [strategyId, timeRange]);

  // Auto refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(loadPerformanceData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, strategyId, timeRange]);

  // Format helpers
  const formatPercent = (value: number, decimals: number = 2) => {
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(Math.abs(value) * 100);
    return `${value >= 0 ? '+' : '-'}${formatted}%`;
  };

  const formatNumber = (value: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get color based on performance
  const getPerformanceColor = (value: number, inverse: boolean = false) => {
    const isPositive = inverse ? value < 0 : value > 0;
    return isPositive ? 'text-green-600 dark:text-green-400' : value < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400';
  };

  const getPerformanceBgColor = (value: number, inverse: boolean = false) => {
    const isPositive = inverse ? value < 0 : value > 0;
    return isPositive ? 'bg-green-100' : value < 0 ? 'bg-red-100' : 'bg-gray-100';
  };

  // Performance rating
  const getPerformanceRating = () => {
    if (!performance) return 'N/A';

    const score = (
      (performance.total_return > 0.1 ? 1 : 0) +
      (performance.sharpe_ratio > 1 ? 1 : 0) +
      (performance.win_rate > 0.6 ? 1 : 0) +
      (Math.abs(performance.max_drawdown) < 0.1 ? 1 : 0) +
      (performance.profit_factor > 1.5 ? 1 : 0)
    );

    if (score >= 4) return '優秀';
    if (score >= 3) return '良好';
    if (score >= 2) return '一般';
    return '較差';
  };

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case '優秀': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case '良好': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case '一般': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case '較差': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300';
    }
  };

  if (loading && !performance) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading size="lg" text="載入性能數據中..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        variant="error"
        title="載入失敗"
        description={error}
        action={
          <Button variant="outline" size="sm" onClick={loadPerformanceData}>
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            重試
          </Button>
        }
      />
    );
  }

  if (!performance) {
    return (
      <Alert
        variant="warning"
        title="無性能數據"
        description="此策略尚未執行或無性能數據"
      />
    );
  }

  const rating = getPerformanceRating();

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">性能監控</h3>
          {strategyName && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{strategyName}</p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <span className="text-sm text-gray-500 dark:text-gray-400">時間範圍:</span>
            <Select
              value={timeRange}
              onChange={(value) => onTimeRangeChange?.(value)}
              className="text-sm bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
            >
              {timeRangeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadPerformanceData}
            disabled={loading}
            className="w-full sm:w-auto"
          >
            <ArrowPathIcon className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Last Updated */}
      <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
        <CalendarIcon className="h-3 w-3 mr-1" />
        最後更新: {formatDate(lastUpdated)}
      </div>

      {/* Performance Rating */}
      <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
        <div className="flex items-center space-x-2">
          <ShieldCheckIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-900 dark:text-white">綜合評級:</span>
        </div>
        <Badge className={getRatingColor(rating)}>
          {rating}
        </Badge>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Return */}
        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">總收益</span>
            {performance.total_return >= 0 ? (
              <TrendingUpIcon className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDownIcon className="h-4 w-4 text-red-500" />
            )}
          </div>
          <div className={`text-2xl font-bold ${getPerformanceColor(performance.total_return)}`}>
            {formatPercent(performance.total_return)}
          </div>
        </Card>

        {/* Annualized Return */}
        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">年化收益</span>
            <CurrencyDollarIcon className="h-4 w-4 text-blue-500" />
          </div>
          <div className={`text-2xl font-bold ${getPerformanceColor(performance.annualized_return)}`}>
            {formatPercent(performance.annualized_return)}
          </div>
        </Card>

        {/* Max Drawdown */}
        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">最大回撤</span>
            <ExclamationTriangleIcon className="h-4 w-4 text-orange-500" />
          </div>
          <div className={`text-2xl font-bold ${getPerformanceColor(performance.max_drawdown, true)}`}>
            {formatPercent(performance.max_drawdown)}
          </div>
        </Card>

        {/* Sharpe Ratio */}
        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">夏普比率</span>
            <ChartBarIcon className="h-4 w-4 text-purple-500" />
          </div>
          <div className={`text-2xl font-bold ${getPerformanceColor(performance.sharpe_ratio)}`}>
            {formatNumber(performance.sharpe_ratio)}
          </div>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Return & Risk Metrics */}
        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">收益與風險指標</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">總收益:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.total_return)}`}>
                {formatPercent(performance.total_return)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">年化收益:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.annualized_return)}`}>
                {formatPercent(performance.annualized_return)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">最大回撤:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.max_drawdown, true)}`}>
                {formatPercent(performance.max_drawdown)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">波動率:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatPercent(performance.volatility)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">夏普比率:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.sharpe_ratio)}`}>
                {formatNumber(performance.sharpe_ratio)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">索提諾比率:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.sortino_ratio)}`}>
                {formatNumber(performance.sortino_ratio)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">卡瑪比率:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.calmar_ratio)}`}>
                {formatNumber(performance.calmar_ratio)}
              </span>
            </div>
          </div>
        </Card>

        {/* Trading Metrics */}
        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">交易統計</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">總交易次數:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {performance.total_trades}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">盈利交易:</span>
              <span className="text-sm font-medium text-green-600 dark:text-green-400">
                {performance.winning_trades}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">虧損交易:</span>
              <span className="text-sm font-medium text-red-600 dark:text-red-400">
                {performance.losing_trades}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">勝率:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.win_rate)}`}>
                {formatPercent(performance.win_rate)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">盈利因子:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.profit_factor)}`}>
                {formatNumber(performance.profit_factor)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">平均盈利:</span>
              <span className="text-sm font-medium text-green-600 dark:text-green-400">
                {formatPercent(performance.average_win)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">平均虧損:</span>
              <span className="text-sm font-medium text-red-600 dark:text-red-400">
                {formatPercent(Math.abs(performance.average_loss))}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Best/Worst Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">最佳表現</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">最大盈利:</span>
              <span className="text-sm font-medium text-green-600 dark:text-green-400">
                {formatPercent(performance.largest_win)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">連勝次數:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">--</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">平均持倉時間:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">--</span>
            </div>
          </div>
        </Card>

        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">風險指標</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">最大虧損:</span>
              <span className="text-sm font-medium text-red-600 dark:text-red-400">
                {formatPercent(Math.abs(performance.largest_loss))}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Beta:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatNumber(performance.beta)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Alpha:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.alpha)}`}>
                {formatPercent(performance.alpha)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">信息比率:</span>
              <span className={`text-sm font-medium ${getPerformanceColor(performance.information_ratio)}`}>
                {formatNumber(performance.information_ratio)}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default StrategyPerformanceMonitor;