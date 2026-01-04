import React from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface PerformanceMetricsProps {
  metrics: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    sortinoRatio: number;
    calmarRatio: number;
    volatility: number;
    winRate: number;
    profitFactor: number;
    averageWin: number;
    averageLoss: number;
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
  };
  className?: string;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics, className = '' }) => {
  const formatNumber = (value: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(Math.abs(value));
  };

  const formatPercent = (value: number) => {
    return `${formatNumber(value * 100, 2)}%`;
  };

  const getMetricIcon = (key: string, value: number) => {
    if (key.includes('return') || key.includes('alpha')) {
      return value >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon;
    }
    if (key.includes('drawdown') || key.includes('loss')) {
      return ArrowTrendingDownIcon;
    }
    if (key.includes('sharpe') || key.includes('ratio')) {
      return ShieldCheckIcon;
    }
    if (key.includes('win') || key.includes('profit')) {
      return CurrencyDollarIcon;
    }
    return ChartBarIcon;
  };

  const getMetricColor = (key: string, value: number) => {
    if (key.includes('return') || key.includes('alpha')) {
      return value >= 0 ? 'text-green-600' : 'text-red-600';
    }
    if (key.includes('drawdown') || key.includes('loss')) {
      return 'text-red-600';
    }
    if (key.includes('sharpe') || key.includes('ratio')) {
      if (key === 'sharpeRatio' || key === 'sortinoRatio' || key === 'calmarRatio') {
        return value > 1.5 ? 'text-green-600' : value > 1 ? 'text-yellow-600' : value > 0 ? 'text-red-400' : 'text-red-600';
      }
      return value > 1 ? 'text-green-600' : value > 0 ? 'text-yellow-600' : 'text-red-600';
    }
    if (key.includes('rate')) {
      return value > 0.5 ? 'text-green-600' : value > 0.3 ? 'text-yellow-600' : 'text-red-600';
    }
    return 'text-gray-600';
  };

  const getMetricDescription = (key: string) => {
    const descriptions: Record<string, string> = {
      totalReturn: 'Total portfolio return',
      annualizedReturn: 'Annualized return rate',
      maxDrawdown: 'Maximum peak-to-trough decline',
      sharpeRatio: 'Risk-adjusted return measure',
      sortinoRatio: 'Downside risk-adjusted return',
      calmarRatio: 'Return to maximum drawdown ratio',
      volatility: 'Annualized volatility',
      winRate: 'Percentage of profitable trades',
      profitFactor: 'Total profit divided by total loss',
      averageWin: 'Average profit from winning trades',
      averageLoss: 'Average loss from losing trades',
      totalTrades: 'Total number of trades executed',
      winningTrades: 'Number of profitable trades',
      losingTrades: 'Number of losing trades'
    };
    return descriptions[key] || '';
  };

  const renderMetric = (key: string, label: string, value: number, unit: string = '') => {
    const Icon = getMetricIcon(key, value);
    const color = getMetricColor(key, value);
    const formattedValue = unit === '%' ? formatPercent(value) :
                          unit === '$' ? (value >= 0 ? formatCurrency(value) : `(${formatCurrency(value)})`) :
                          formatNumber(value);

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-500">{label}</span>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <div className={`text-2xl font-bold ${color}`}>
          {formattedValue}
        </div>
        <p className="text-xs text-gray-500 mt-1">{getMetricDescription(key)}</p>
      </div>
    );
  };

  const metricGroups = [
    {
      title: 'Returns',
      metrics: [
        { key: 'totalReturn', label: 'Total Return', unit: '%' },
        { key: 'annualizedReturn', label: 'Annualized Return', unit: '%' },
        { key: 'maxDrawdown', label: 'Max Drawdown', unit: '%' }
      ]
    },
    {
      title: 'Risk-Adjusted Metrics',
      metrics: [
        { key: 'sharpeRatio', label: 'Sharpe Ratio' },
        { key: 'sortinoRatio', label: 'Sortino Ratio' },
        { key: 'calmarRatio', label: 'Calmar Ratio' },
        { key: 'volatility', label: 'Volatility', unit: '%' }
      ]
    },
    {
      title: 'Trading Statistics',
      metrics: [
        { key: 'winRate', label: 'Win Rate', unit: '%' },
        { key: 'profitFactor', label: 'Profit Factor' },
        { key: 'averageWin', label: 'Average Win', unit: '$' },
        { key: 'averageLoss', label: 'Average Loss', unit: '$' }
      ]
    },
    {
      title: 'Trade Count',
      metrics: [
        { key: 'totalTrades', label: 'Total Trades' },
        { key: 'winningTrades', label: 'Winning Trades' },
        { key: 'losingTrades', label: 'Losing Trades' }
      ]
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <ChartBarIcon className="w-5 h-5 text-gray-600" />
        <h2 className="text-xl font-semibold text-gray-900">Performance Metrics</h2>
      </div>

      {metricGroups.map((group) => (
        <div key={group.title}>
          <h3 className="text-sm font-medium text-gray-700 mb-3">{group.title}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {group.metrics.map(({ key, label, unit }) => (
              <div key={key}>
                {renderMetric(key, label, metrics[key as keyof typeof metrics] as number, unit)}
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Performance Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Performance Summary</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                This strategy achieved <span className="font-semibold">{formatPercent(metrics.totalReturn)}</span> total return
                with a Sharpe ratio of <span className="font-semibold">{formatNumber(metrics.sharpeRatio)}</span>.
                The maximum drawdown was <span className="font-semibold">{formatPercent(metrics.maxDrawdown)}</span>,
                and the win rate was <span className="font-semibold">{formatPercent(metrics.winRate)}</span>.
              </p>
              {metrics.sharpeRatio < 1 && (
                <p className="mt-2 text-amber-600">
                  ⚠️ The Sharpe ratio is below 1.0, indicating suboptimal risk-adjusted returns.
                </p>
              )}
              {metrics.maxDrawdown < -0.15 && (
                <p className="mt-2 text-amber-600">
                  ⚠️ The maximum drawdown exceeds 15%, which indicates significant risk.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMetrics;