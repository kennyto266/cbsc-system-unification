import React from 'react';
import { Strategy, PerformanceMetrics } from '../../types/strategy';

interface StrategyCardProps {
  strategy: Strategy;
  onSelect: (strategy: Strategy) => void;
  isSelected: boolean;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onSelect,
  isSelected
}) => {
  const getPerformanceColor = (sharpeRatio: number | undefined): string => {
    if (!sharpeRatio) return 'text-gray-500';
    if (sharpeRatio >= 1.5) return 'text-green-600';
    if (sharpeRatio >= 0.8) return 'text-blue-600';
    if (sharpeRatio >= 0.3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceGrade = (sharpeRatio: number | undefined): string => {
    if (!sharpeRatio) return 'N/A';
    if (sharpeRatio >= 1.5) return 'S';
    if (sharpeRatio >= 1.0) return 'A';
    if (sharpeRatio >= 0.8) return 'B';
    if (sharpeRatio >= 0.5) return 'C';
    if (sharpeRatio >= 0.3) return 'D';
    return 'F';
  };

  const getPerformanceGradeColor = (sharpeRatio: number | undefined): string => {
    if (!sharpeRatio) return 'bg-gray-100 text-gray-500';
    if (sharpeRatio >= 1.5) return 'bg-green-100 text-green-800';
    if (sharpeRatio >= 1.0) return 'bg-blue-100 text-blue-800';
    if (sharpeRatio >= 0.8) return 'bg-indigo-100 text-indigo-800';
    if (sharpeRatio >= 0.5) return 'bg-yellow-100 text-yellow-800';
    if (sharpeRatio >= 0.3) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSignalColor = (signalType: string): string => {
    switch (signalType) {
      case 'buy':
      case 'extreme_bullish':
      case 'golden_cross':
        return 'text-green-600';
      case 'sell':
      case 'extreme_bearish':
      case 'death_cross':
        return 'text-red-600';
      case 'hold':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getSignalIcon = (signalType: string): string => {
    switch (signalType) {
      case 'buy':
        return '▲';
      case 'sell':
        return '▼';
      case 'hold':
        return '▶';
      case 'extreme_bullish':
        return '⬆';
      case 'extreme_bearish':
        return '⬇';
      case 'golden_cross':
        return '✦';
      case 'death_cross':
        return '✧';
      default:
        return '○';
    }
  };

  const formatPercentage = (value: number | undefined): string => {
    if (value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined) return 'N/A';
    return value.toFixed(decimals);
  };

  const isDataFresh = (lastUpdated?: Date): boolean => {
    if (!lastUpdated) return false;
    const now = new Date();
    const diffMinutes = (now.getTime() - lastUpdated.getTime()) / (1000 * 60);
    return diffMinutes < 5; // 数据在5分钟内算新鲜
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border-2 transition-all duration-200 cursor-pointer hover:shadow-md ${
        isSelected ? 'border-blue-500 shadow-md' : 'border-gray-200'
      }`}
      onClick={() => onSelect(strategy)}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-gray-900 text-sm leading-tight">
            {strategy.name}
          </h3>
          <div className="flex items-center space-x-2">
            {/* Status Badge */}
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(strategy.status)}`}>
              {strategy.status === 'active' ? '运行中' : strategy.status === 'inactive' ? '已停止' : strategy.status}
            </span>

            {/* Performance Grade */}
            {strategy.performance && (
              <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${getPerformanceGradeColor(strategy.performance.sharpeRatio)}`}>
                {getPerformanceGrade(strategy.performance.sharpeRatio)}
              </span>
            )}
          </div>
        </div>

        {/* Strategy Type */}
        <div className="text-xs text-gray-500 mb-1">
          {strategy.type.replace('_', ' ').toUpperCase()}
        </div>

        {/* Description */}
        <p className="text-xs text-gray-600 line-clamp-2">
          {strategy.description}
        </p>
      </div>

      {/* Performance Metrics */}
      <div className="p-4">
        {strategy.performance ? (
          <div className="space-y-3">
            {/* Key Metrics Row */}
            <div className="grid grid-cols-2 gap-3">
              {/* Sharpe Ratio */}
              <div>
                <div className="text-xs text-gray-500 mb-1">夏普比率</div>
                <div className={`text-lg font-bold ${getPerformanceColor(strategy.performance.sharpeRatio)}`}>
                  {formatNumber(strategy.performance.sharpeRatio)}
                </div>
              </div>

              {/* Total Return */}
              <div>
                <div className="text-xs text-gray-500 mb-1">总回报率</div>
                <div className={`text-lg font-bold ${
                  (strategy.performance.totalReturn || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatPercentage(strategy.performance.totalReturn)}
                </div>
              </div>
            </div>

            {/* Secondary Metrics */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <div className="text-gray-500">年化收益</div>
                <div className="font-medium">
                  {formatPercentage(strategy.performance.annualReturn)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">最大回撤</div>
                <div className="font-medium text-red-600">
                  {formatPercentage(strategy.performance.maxDrawdown)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">胜率</div>
                <div className="font-medium">
                  {formatPercentage(strategy.performance.winRate)}
                </div>
              </div>
            </div>

            {/* Data Quality Indicator */}
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">数据质量</span>
              <div className="flex items-center">
                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className={`h-2 rounded-full ${
                      (strategy.performance.dataQualityScore || 0) >= 80 ? 'bg-green-500' :
                      (strategy.performance.dataQualityScore || 0) >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${strategy.performance.dataQualityScore || 0}%` }}
                  ></div>
                </div>
                <span className="text-gray-700">
                  {Math.round(strategy.performance.dataQualityScore || 0)}%
                </span>
              </div>
            </div>

            {/* Last Updated */}
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">最后更新</span>
              <span className={`flex items-center ${
                isDataFresh(strategy.performance.lastUpdated) ? 'text-green-600' : 'text-gray-500'
              }`}>
                {isDataFresh(strategy.performance.lastUpdated) && (
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                )}
                {strategy.performance.lastUpdated ?
                  new Date(strategy.performance.lastUpdated).toLocaleTimeString() :
                  'N/A'
                }
              </span>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="text-gray-400 mb-2">
              <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500">暂无绩效数据</p>
          </div>
        )}

        {/* Latest Signal */}
        {strategy.latestSignal && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">最新信号</span>
              <span className={`flex items-center text-sm font-medium ${getSignalColor(strategy.latestSignal.type)}`}>
                <span className="mr-1">{getSignalIcon(strategy.latestSignal.type)}</span>
                {strategy.latestSignal.type.replace('_', ' ').toUpperCase()}
                <span className="ml-2 text-xs text-gray-400">
                  强度: {Math.round(strategy.latestSignal.strength)}%
                </span>
              </span>
            </div>
            {strategy.latestSignal.timestamp && (
              <div className="text-xs text-gray-400 mt-1">
                {new Date(strategy.latestSignal.timestamp).toLocaleString()}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">
            {strategy.category.replace('_', ' ')}
          </span>
          <button
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(strategy);
            }}
          >
            查看详情 →
          </button>
        </div>
      </div>
    </div>
  );
};