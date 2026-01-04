import React, { useState } from 'react';
import {
  DocumentTextIcon,
  ChartBarIcon,
  AcademicCapIcon,
  ArrowsRightLeftIcon,
  DocumentArrowDownIcon,
  ShareIcon,
  EyeIcon,
  CalendarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts';

import PerformanceMetrics from './PerformanceMetrics';
import CorrelationAnalysis from './CorrelationAnalysis';
import ContributionBreakdown from './ContributionBreakdown';
import ReportExporter from '../ExportTools/ReportExporter';

interface EconomicData {
  indicators: Array<{
    name: string;
    values: number[];
  }>;
  correlation: Record<string, number>;
}

interface StrategyComparison {
  name: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  correlation: number;
  volatility?: number;
  winRate?: number;
}

interface EconomicBacktestReport {
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
  economicData?: EconomicData;
  strategyComparison?: StrategyComparison[];
  contributionBreakdown?: Array<{
    factor: string;
    contribution: number;
    weight: number;
  }>;
  equityCurve?: Array<{
    date: string;
    portfolioValue: number;
    benchmarkValue?: number;
  }>;
  trades?: Array<{
    date: string;
    type: 'buy' | 'sell';
    price: number;
    quantity: number;
    profit?: number;
    profitPercent?: number;
  }>;
  generatedAt: string;
}

interface EconomicBacktestReportsProps {
  report: EconomicBacktestReport;
  className?: string;
}

const EconomicBacktestReports: React.FC<EconomicBacktestReportsProps> = ({
  report,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'performance' | 'correlation' | 'contributions' | 'comparison'>('performance');
  const [showExportModal, setShowExportModal] = useState(false);

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

  // Prepare correlation data
  const correlationData = report.economicData ? {
    economicIndicators: report.economicData.indicators.map(indicator => ({
      ...indicator,
      dates: report.equityCurve?.map(point => point.date) || []
    })),
    strategyReturns: report.equityCurve?.map((point, index) => {
      if (index === 0) return 0;
      return (point.portfolioValue - report.equityCurve![index - 1].portfolioValue) / report.equityCurve![index - 1].portfolioValue;
    }) || [],
    correlationMatrix: report.economicData.correlation
  } : null;

  // Prepare comparison radar data
  const radarData = report.strategyComparison ?
    report.strategyComparison.map(strategy => ({
      strategy: strategy.name,
      return: strategy.totalReturn * 100,
      sharpe: strategy.sharpeRatio * 20, // Scale for visibility
      stability: (1 + strategy.maxDrawdown) * 100, // Convert drawdown to stability
      correlation: strategy.correlation * 100
    })) : [];

  // Render performance tab
  const renderPerformanceTab = () => (
    <div className="space-y-6">
      <PerformanceMetrics metrics={report.metrics} />

      {/* Economic Indicators Overview */}
      {report.economicData && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Key Economic Indicators</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {report.economicData.indicators.slice(0, 6).map((indicator, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-3">
                <h4 className="text-sm font-medium text-gray-700">{indicator.name}</h4>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {indicator.values[indicator.values.length - 1]?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">
                  Previous: {indicator.values[indicator.values.length - 2]?.toFixed(2) || 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Render correlation tab
  const renderCorrelationTab = () => (
    <div className="space-y-6">
      {correlationData ? (
        <CorrelationAnalysis data={correlationData} />
      ) : (
        <div className="text-center py-8">
          <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No correlation data available</h3>
        </div>
      )}
    </div>
  );

  // Render contributions tab
  const renderContributionsTab = () => (
    <div className="space-y-6">
      {report.contributionBreakdown ? (
        <ContributionBreakdown data={report.contributionBreakdown} />
      ) : (
        <div className="text-center py-8">
          <ArrowsRightLeftIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No contribution data available</h3>
        </div>
      )}
    </div>
  );

  // Render comparison tab
  const renderComparisonTab = () => (
    <div className="space-y-6">
      {report.strategyComparison && report.strategyComparison.length > 0 ? (
        <>
          {/* Comparison Table */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Compare with other strategies</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Strategy
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sharpe
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Max DD
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Correlation
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {report.strategyComparison.map((strategy, index) => (
                    <tr key={index} className={strategy.name === report.strategy.name ? 'bg-blue-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {strategy.name}
                        {strategy.name === report.strategy.name && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Current
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={strategy.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatPercent(strategy.totalReturn)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(strategy.sharpeRatio)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="text-red-600">
                          {formatPercent(strategy.maxDrawdown)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(strategy.correlation)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Radar Chart Comparison */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Multi-Metric Comparison</h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E5E7EB" />
                <PolarAngleAxis dataKey="strategy" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar
                  name={report.strategyComparison[0]?.name || 'Strategy 1'}
                  dataKey="return"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.3}
                />
                <Radar
                  name={report.strategyComparison[1]?.name || 'Strategy 2'}
                  dataKey="sharpe"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.3}
                />
                <Radar
                  name={report.strategyComparison[2]?.name || 'Strategy 3'}
                  dataKey="stability"
                  stroke="#F59E0B"
                  fill="#F59E0B"
                  fillOpacity={0.3}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Correlation Matrix */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Correlation Matrix</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-xs font-medium text-gray-500"></th>
                    {report.strategyComparison.map((strategy, index) => (
                      <th key={index} className="px-4 py-2 text-xs font-medium text-gray-500 text-center">
                        {strategy.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.strategyComparison.map((strategy1, i) => (
                    <tr key={i}>
                      <td className="px-4 py-2 text-xs font-medium text-gray-900">
                        {strategy1.name}
                      </td>
                      {report.strategyComparison!.map((strategy2, j) => (
                        <td key={j} className="px-4 py-2 text-center">
                          <span className={`inline-flex items-center justify-center w-12 h-8 rounded text-xs font-medium ${
                            i === j ? 'bg-gray-100 text-gray-600' :
                            Math.abs(strategy1.correlation) >= 0.7 ? 'bg-red-100 text-red-800' :
                            Math.abs(strategy1.correlation) >= 0.3 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {formatNumber(i === j ? 1 : strategy1.correlation)}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-8">
          <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No comparison strategies available</h3>
        </div>
      )}
    </div>
  );

  return (
    <div className={`bg-gray-50 rounded-lg ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Economic Strategy Backtest Report</h1>
            <p className="text-sm text-gray-500 mt-1">
              {report.strategyName} • {new Date(report.period.start).toLocaleDateString()} - {new Date(report.period.end).toLocaleDateString()}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <CalendarIcon className="w-4 h-4" />
              <span>Duration: {formatNumber(report.period.duration)} days</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <ClockIcon className="w-4 h-4" />
              <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
            </div>
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <DocumentArrowDownIcon className="w-4 h-4" />
              <span>Export Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <nav className="flex -mb-px">
          {[
            { id: 'performance', label: 'Performance', icon: ChartBarIcon },
            { id: 'correlation', label: 'Correlation Analysis', icon: AcademicCapIcon },
            { id: 'contributions', label: 'Contributions', icon: ArrowTrendingUpIcon },
            { id: 'comparison', label: 'Strategy Comparison', icon: UserGroupIcon }
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
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'correlation' && renderCorrelationTab()}
        {activeTab === 'contributions' && renderContributionsTab()}
        {activeTab === 'comparison' && renderComparisonTab()}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <ReportExporter
          report={report}
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
};

export default EconomicBacktestReports;