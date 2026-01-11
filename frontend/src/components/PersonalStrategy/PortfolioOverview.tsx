import React, { useState } from 'react';
import { UserPortfolio, DashboardMetrics } from '../../types/index';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface PortfolioOverviewProps {
  portfolio: UserPortfolio | null;
  metrics: DashboardMetrics;
  onTimeRangeChange: (range: '1d' | '1w' | '1m' | '3m') => void;
  currentRange: '1d' | '1w' | '1m' | '3m';
}

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({
  portfolio,
  metrics,
  onTimeRangeChange,
  currentRange
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getPortfolioHealthColor = (health: string) => {
    switch (health) {
      case 'excellent': return 'success';
      case 'good': return 'success';
      case 'fair': return 'warning';
      case 'poor': return 'error';
      default: return 'neutral';
    }
  };

  const getPortfolioHealthText = (health: string) => {
    switch (health) {
      case 'excellent': return '优秀';
      case 'good': return '良好';
      case 'fair': return '一般';
      case 'poor': return '较差';
      default: return '未知';
    }
  };

  const timeRangeOptions = [
    { value: '1d', label: '1天' },
    { value: '1w', label: '1周' },
    { value: '1m', label: '1月' },
    { value: '3m', label: '3月' }
  ];

  if (!portfolio) {
    return (
      <div className="mb-8">
        <Card className="p-6">
          <div className="text-center">
            <div className="text-neutral-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">暂无投资组合数据</h3>
            <p className="text-neutral-600">开始创建您的第一个个人策略组合</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <Card className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-neutral-900 mb-2">投资组合概览</h2>
            <div className="flex items-center space-x-4">
              <Badge variant={getPortfolioHealthColor(metrics.portfolioHealth)}>
                组合状态: {getPortfolioHealthText(metrics.portfolioHealth)}
              </Badge>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-neutral-600">实时更新</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {timeRangeOptions.map((option) => (
              <Button
                key={option.value}
                size="sm"
                variant={currentRange === option.value ? 'primary' : 'outline'}
                onClick={() => onTimeRangeChange(option.value as any)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Main Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Portfolio Value */}
          <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-primary-800">总资产价值</span>
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-2xl font-bold text-primary-900 mb-1">
              {formatCurrency(metrics.totalValue)}
            </div>
            <div className={`text-sm ${
              metrics.dailyChange >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {formatPercentage(metrics.dailyChangePercent)} ({formatCurrency(metrics.dailyChange)})
            </div>
          </div>

          {/* Total Return */}
          <div className="bg-gradient-to-br from-success-50 to-success-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-success-800">总收益率</span>
              <svg className="w-5 h-5 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className={`text-2xl font-bold text-success-900 mb-1 ${
              metrics.totalReturn >= 0 ? '' : 'text-error-900'
            }`}>
              {formatPercentage(metrics.totalReturn)}
            </div>
            <div className="text-sm text-success-700">
              自创建以来
            </div>
          </div>

          {/* Sharpe Ratio */}
          <div className="bg-gradient-to-br from-neutral-50 to-neutral-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-neutral-800">夏普比率</span>
              <svg className="w-5 h-5 text-neutral-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="text-2xl font-bold text-neutral-900 mb-1">
              {metrics.sharpeRatio.toFixed(2)}
            </div>
            <div className="text-sm text-neutral-700">
              风险调整收益
            </div>
          </div>

          {/* Active Strategies */}
          <div className="bg-gradient-to-br from-warning-50 to-warning-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-warning-800">活跃策略</span>
              <svg className="w-5 h-5 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="text-2xl font-bold text-warning-900 mb-1">
              {metrics.activeStrategies}
            </div>
            <div className="text-sm text-warning-700">
              个策略运行中
            </div>
          </div>
        </div>

        {/* Allocation and Performance Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Asset Allocation */}
          <div className="bg-neutral-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-neutral-900 mb-3">资金分配</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-neutral-600">已分配资金</span>
                <span className="text-sm font-medium text-neutral-900">
                  {formatCurrency(portfolio.allocatedCapital)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-neutral-600">可用现金</span>
                <span className="text-sm font-medium text-neutral-900">
                  {formatCurrency(portfolio.availableCash)}
                </span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(portfolio.allocatedCapital / portfolio.totalValue) * 100}%` }}
                ></div>
              </div>
              <div className="text-xs text-neutral-500">
                {((portfolio.allocatedCapital / portfolio.totalValue) * 100).toFixed(1)}% 资金已分配
              </div>
            </div>
          </div>

          {/* Portfolio Performance */}
          <div className="bg-neutral-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-neutral-900 mb-3">组合表现</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-neutral-600 mb-1">胜率</div>
                <div className="text-lg font-bold text-neutral-900">
                  {metrics.winRate.toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-600 mb-1">总信号数</div>
                <div className="text-lg font-bold text-neutral-900">
                  {metrics.totalSignals}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 pt-6 border-t border-neutral-200">
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline">
              重新平衡
            </Button>
            <Button size="sm" variant="outline">
              导出报告
            </Button>
            <Button size="sm" variant="outline">
              风险分析
            </Button>
            <Button size="sm" variant="outline">
              历史回测
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};