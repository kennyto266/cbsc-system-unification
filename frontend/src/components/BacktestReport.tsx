import React, { useState } from 'react';
import {
  DocumentTextIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  ClockIcon,
  BanknotesIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  DocumentArrowDownIcon,
  ShareIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface BacktestMetrics {
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
}

interface Trade {
  date: string;
  type: 'buy' | 'sell';
  price: number;
  quantity: number;
  profit?: number;
  profitPercent?: number;
}

interface BacktestReport {
  id: string;
  strategyName: string;
  strategy: {
    name: string;
    parameters: Record<string, any>;
    category: string;
  };
  period: {
    start: string;
    end: string;
    duration: number;
  };
  metrics: BacktestMetrics;
  equityCurve: Array<{
    date: string;
    portfolioValue: number;
    benchmarkValue?: number;
  }>;
  trades: Trade[];
  monthlyReturns: Array<{
    month: string;
    return: number;
    benchmarkReturn?: number;
  }>;
  riskMetrics?: {
    beta?: number;
    alpha?: number;
    jensenAlpha?: number;
    treynorRatio?: number;
    informationRatio?: number;
  };
  generatedAt: string;
  reportFiles?: {
    pdf?: string;
    excel?: string;
    html?: string;
    json?: string;
  };
}

interface BacktestReportProps {
  report: BacktestReport;
  className?: string;
  showBenchmark?: boolean;
}

const COLORS = {
  primary: '#3B82F6',
  secondary: '#10B981',
  danger: '#EF4444',
  warning: '#F59E0B',
  info: '#8B5CF6',
  success: '#22C55E'
};

const CHART_COLORS = {
  portfolio: '#3B82F6',
  benchmark: '#10B981',
  drawdown: '#EF4444',
  profit: '#10B981',
  loss: '#EF4444'
};

export default function BacktestReport({
  report,
  className = '',
  showBenchmark = true
}: BacktestReportProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'trades' | 'risk'>('overview');

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
    }).format(value);
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
    if (key.includes('rate')) {
      return CheckCircleIcon;
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
      return value > 1 ? 'text-green-600' : value > 0 ? 'text-yellow-600' : 'text-red-600';
    }
    return 'text-gray-600';
  };

  const renderMetricCard = (label: string, value: number | string, unit: string = '', description?: string) => {
    const isNumber = typeof value === 'number';
    const color = isNumber ? getMetricColor(label, value as number) : 'text-gray-600';
    const Icon = isNumber ? getMetricIcon(label, value as number) : InformationCircleIcon;

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-500">{label}</span>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <div className={`text-2xl font-bold ${color}`}>
          {isNumber ? (
            unit === '%' ? formatPercent(value as number) :
            unit === '$' ? formatCurrency(value as number) :
            formatNumber(value as number)
          ) : value}
        </div>
        {description && (
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        )}
      </div>
    );
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Key Performance Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {renderMetricCard('Total Return', report.metrics.totalReturn, '%', 'Overall period return')}
          {renderMetricCard('Annualized Return', report.metrics.annualizedReturn, '%', 'Yearly equivalent return')}
          {renderMetricCard('Max Drawdown', report.metrics.maxDrawdown, '%', 'Worst peak-to-trough decline')}
          {renderMetricCard('Sharpe Ratio', report.metrics.sharpeRatio, '', 'Risk-adjusted returns')}
          {renderMetricCard('Win Rate', report.metrics.winRate, '%', 'Winning trades percentage')}
          {renderMetricCard('Profit Factor', report.metrics.profitFactor, '', 'Total profit / total loss')}
          {renderMetricCard('Total Trades', report.metrics.totalTrades, '', 'Number of executed trades')}
          {renderMetricCard('Volatility', report.metrics.volatility, '%', 'Annualized volatility')}
        </div>
      </div>

      {/* Strategy Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <span className="text-sm font-medium text-gray-500">Strategy</span>
            <p className="text-base text-gray-900">{report.strategy.name}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Category</span>
            <p className="text-base text-gray-900 capitalize">{report.strategy.category}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Parameters</span>
            <div className="mt-1">
              {Object.entries(report.strategy.parameters).map(([key, value]) => (
                <span key={key} className="inline-block bg-white px-2 py-1 rounded text-xs mr-1 mb-1">
                  {key}: {value}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {report.reportFiles && (
        <div className="flex flex-wrap gap-2">
          {report.reportFiles.pdf && (
            <button className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">
              <DocumentArrowDownIcon className="w-4 h-4" />
              <span>Download PDF</span>
            </button>
          )}
          {report.reportFiles.excel && (
            <button className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
              <DocumentArrowDownIcon className="w-4 h-4" />
              <span>Download Excel</span>
            </button>
          )}
          {report.reportFiles.html && (
            <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
              <EyeIcon className="w-4 h-4" />
              <span>View HTML Report</span>
            </button>
          )}
          <button className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
            <ShareIcon className="w-4 h-4" />
            <span>Share Report</span>
          </button>
        </div>
      )}
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      {/* Equity Curve */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Equity Curve</h3>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={report.equityCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #E5E7EB',
                    borderRadius: '0.375rem'
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  formatter={(value: any) => [formatCurrency(value), 'Portfolio Value']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="portfolioValue"
                  stroke={CHART_COLORS.portfolio}
                  strokeWidth={2}
                  dot={false}
                  name="Portfolio"
                />
                {showBenchmark && report.equityCurve[0]?.benchmarkValue && (
                  <Line
                    type="monotone"
                    dataKey="benchmarkValue"
                    stroke={CHART_COLORS.benchmark}
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray="5 5"
                    name="Benchmark"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Monthly Returns */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Returns</h3>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={report.monthlyReturns}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #E5E7EB',
                    borderRadius: '0.375rem'
                  }}
                  formatter={(value: any) => [formatPercent(value / 100), 'Return']}
                />
                <Bar dataKey="return" name="Portfolio Return">
                  {report.monthlyReturns.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.return >= 0 ? CHART_COLORS.profit : CHART_COLORS.loss}
                    />
                  ))}
                </Bar>
                {showBenchmark && report.monthlyReturns[0]?.benchmarkReturn && (
                  <Bar dataKey="benchmarkReturn" name="Benchmark Return" fill={CHART_COLORS.benchmark} opacity={0.6} />
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTradesTab = () => {
    const winningTrades = report.trades.filter(t => t.type === 'sell' && (t.profit || 0) > 0);
    const losingTrades = report.trades.filter(t => t.type === 'sell' && (t.profit || 0) < 0);

    return (
      <div className="space-y-6">
        {/* Trade Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {renderMetricCard('Total Trades', report.metrics.totalTrades, '', '')}
          {renderMetricCard('Winning Trades', report.metrics.winningTrades, '', '')}
          {renderMetricCard('Losing Trades', report.metrics.losingTrades, '', '')}
          {renderMetricCard('Average Win', report.metrics.averageWin, '$', 'Profit per winning trade')}
          {renderMetricCard('Average Loss', report.metrics.averageLoss, '$', 'Loss per losing trade')}
        </div>

        {/* Trade Distribution */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Trade Distribution</h3>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Winning Trades', value: report.metrics.winningTrades },
                        { name: 'Losing Trades', value: report.metrics.losingTrades }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      <Cell fill={CHART_COLORS.profit} />
                      <Cell fill={CHART_COLORS.loss} />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Trade Summary</h3>
            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Win Rate</span>
                <span className="font-medium">{formatPercent(report.metrics.winRate / 100)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Profit Factor</span>
                <span className="font-medium">{formatNumber(report.metrics.profitFactor)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Average Win</span>
                <span className="font-medium text-green-600">{formatCurrency(report.metrics.averageWin)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Average Loss</span>
                <span className="font-medium text-red-600">{formatCurrency(report.metrics.averageLoss)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Trades */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Trades</h3>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Profit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Return
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {report.trades.slice(0, 20).map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(trade.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          trade.type === 'buy'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(trade.price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(trade.quantity, 0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {trade.profit !== undefined ? (
                          <span className={trade.profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {formatCurrency(trade.profit)}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {trade.profitPercent !== undefined ? (
                          <span className={trade.profitPercent >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {formatPercent(trade.profitPercent / 100)}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {report.trades.length > 20 && (
              <div className="px-6 py-3 bg-gray-50 text-center text-sm text-gray-500">
                Showing first 20 of {report.trades.length} trades
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderRiskTab = () => (
    <div className="space-y-6">
      {/* Risk Metrics */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {renderMetricCard('Sortino Ratio', report.metrics.sortinoRatio, '', 'Downside risk-adjusted returns')}
          {renderMetricCard('Calmar Ratio', report.metrics.calmarRatio, '', 'Return/max drawdown ratio')}
          {renderMetricCard('Volatility', report.metrics.volatility, '%', 'Annualized standard deviation')}
        </div>
      </div>

      {/* Additional Risk Metrics */}
      {report.riskMetrics && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Risk Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {report.riskMetrics.beta !== undefined && renderMetricCard('Beta', report.riskMetrics.beta, '', 'Market sensitivity')}
            {report.riskMetrics.alpha !== undefined && renderMetricCard('Alpha', report.riskMetrics.alpha, '%', 'Excess return')}
            {report.riskMetrics.jensenAlpha !== undefined && renderMetricCard("Jensen's Alpha", report.riskMetrics.jensenAlpha, '', 'Risk-adjusted alpha')}
            {report.riskMetrics.treynorRatio !== undefined && renderMetricCard('Treynor Ratio', report.riskMetrics.treynorRatio, '', 'Return per unit of systematic risk')}
            {report.riskMetrics.informationRatio !== undefined && renderMetricCard('Information Ratio', report.riskMetrics.informationRatio, '', 'Active risk-adjusted return')}
          </div>
        </div>
      )}

      {/* Risk Analysis */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Risk Analysis</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>This strategy has a maximum drawdown of {formatPercent(report.metrics.maxDrawdown / 100)}.</p>
              {report.metrics.volatility > 0.2 && (
                <p className="mt-1">The volatility ({formatPercent(report.metrics.volatility / 100)}) indicates high price fluctuations.</p>
              )}
              {report.metrics.sharpeRatio < 1 && (
                <p className="mt-1">Sharpe ratio below 1.0 suggests suboptimal risk-adjusted returns.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`bg-gray-50 rounded-lg ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Backtest Report</h1>
            <p className="text-sm text-gray-500 mt-1">
              {report.strategyName} • {new Date(report.period.start).toLocaleDateString()} - {new Date(report.period.end).toLocaleDateString()}
            </p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <CalendarIcon className="w-4 h-4" />
            <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <nav className="flex -mb-px">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'performance', label: 'Performance', icon: ArrowTrendingUpIcon },
            { id: 'trades', label: 'Trades', icon: CurrencyDollarIcon },
            { id: 'risk', label: 'Risk', icon: ShieldCheckIcon }
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
      <div className="p-6">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'trades' && renderTradesTab()}
        {activeTab === 'risk' && renderRiskTab()}
      </div>
    </div>
  );
}