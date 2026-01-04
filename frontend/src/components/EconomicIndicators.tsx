import React, { useState, useEffect } from 'react';
import {
  CurrencyDollarIcon,
  ChartBarIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  GlobeAltIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  InformationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
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
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts';

interface EconomicIndicator {
  id: string;
  name: string;
  currentValue: number;
  previousValue: number;
  change: number;
  changePercent: number;
  unit: string;
  description: string;
  lastUpdated: string;
  category: 'interest_rate' | 'economic_growth' | 'employment' | 'tourism' | 'manufacturing';
  trend: 'up' | 'down' | 'stable';
  historicalData: HistoricalDataPoint[];
  thresholds?: {
    high?: number;
    low?: number;
    optimal?: {
      min: number;
      max: number;
    };
  };
}

interface HistoricalDataPoint {
  date: string;
  value: number;
  [key: string]: any;
}

interface EconomicIndicatorsProps {
  indicators: EconomicIndicator[];
  className?: string;
}

const INDICATOR_COLORS = {
  interest_rate: {
    primary: '#3B82F6',
    gradient: ['#DBEAFE', '#3B82F6'],
    area: ['rgba(219, 234, 254, 0.3)', 'rgba(59, 130, 246, 0.1)']
  },
  economic_growth: {
    primary: '#10B981',
    gradient: ['#D1FAE5', '#10B981'],
    area: ['rgba(209, 250, 229, 0.3)', 'rgba(16, 185, 129, 0.1)']
  },
  employment: {
    primary: '#F59E0B',
    gradient: ['#FEF3C7', '#F59E0B'],
    area: ['rgba(254, 243, 199, 0.3)', 'rgba(245, 158, 11, 0.1)']
  },
  tourism: {
    primary: '#8B5CF6',
    gradient: ['#EDE9FE', '#8B5CF6'],
    area: ['rgba(237, 233, 254, 0.3)', 'rgba(139, 92, 246, 0.1)']
  },
  manufacturing: {
    primary: '#EF4444',
    gradient: ['#FEE2E2', '#EF4444'],
    area: ['rgba(254, 226, 226, 0.3)', 'rgba(239, 68, 68, 0.1)']
  }
};

export default function EconomicIndicators({
  indicators,
  className = ''
}: EconomicIndicatorsProps) {
  const [selectedIndicator, setSelectedIndicator] = useState<EconomicIndicator | null>(null);
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('area');

  const formatNumber = (value: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const formatLargeNumber = (value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toString();
  };

  const renderIndicatorCard = (indicator: EconomicIndicator) => {
    const Icon = getIndicatorIcon(indicator.id);
    const colors = INDICATOR_COLORS[indicator.category];
    const isPositive = indicator.change > 0;
    const isNegative = indicator.change < 0;

    return (
      <div
        key={indicator.id}
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 cursor-pointer transition-all hover:shadow-md ${
          selectedIndicator?.id === indicator.id ? 'ring-2 ring-blue-500' : ''
        }`}
        onClick={() => setSelectedIndicator(indicator)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${colors.primary}20` }}
            >
              <Icon className="w-5 h-5" style={{ color: colors.primary }} />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{indicator.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{indicator.description}</p>
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {indicator.unit === '%' ? `${formatNumber(indicator.currentValue)}%` :
               indicator.unit === 'million' ? formatLargeNumber(indicator.currentValue) :
               formatNumber(indicator.currentValue)}
            </div>

            <div className={`flex items-center space-x-1 text-sm mt-1 ${
              isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-500'
            }`}>
              {isPositive && <ArrowTrendingUpIcon className="w-4 h-4" />}
              {isNegative && <ArrowTrendingDownIcon className="w-4 h-4" />}
              <span>
                {isPositive && '+'}{indicator.changePercent > 0 ? `${formatNumber(indicator.changePercent)}%` :
                 `${formatNumber(indicator.change, 4)}`}
              </span>
            </div>
          </div>
        </div>

        {/* Mini Chart */}
        <div className="mt-4 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={indicator.historicalData.slice(-20)}>
              <defs>
                <linearGradient id={`gradient-${indicator.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.primary} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={colors.primary} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors.primary}
                strokeWidth={1.5}
                fill={`url(#gradient-${indicator.id})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Last Updated */}
        <div className="mt-3 text-xs text-gray-500">
          Last updated: {new Date(indicator.lastUpdated).toLocaleDateString()}
        </div>
      </div>
    );
  };

  const renderDetailChart = () => {
    if (!selectedIndicator) return null;

    const indicator = selectedIndicator;
    const colors = INDICATOR_COLORS[indicator.category];
    const data = indicator.historicalData;

    const renderChart = () => {
      switch (chartType) {
        case 'line':
          return (
            <LineChart data={data}>
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
                domain={['dataMin - 0.1', 'dataMax + 0.1']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #E5E7EB',
                  borderRadius: '0.375rem'
                }}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: any) => [
                  indicator.unit === '%' ? `${formatNumber(value)}%` :
                  indicator.unit === 'million' ? formatLargeNumber(value) :
                  formatNumber(value),
                  indicator.name
                ]}
              />
              {indicator.thresholds?.high && (
                <ReferenceLine
                  y={indicator.thresholds.high}
                  stroke="#EF4444"
                  strokeDasharray="5 5"
                  label="High"
                />
              )}
              {indicator.thresholds?.low && (
                <ReferenceLine
                  y={indicator.thresholds.low}
                  stroke="#EF4444"
                  strokeDasharray="5 5"
                  label="Low"
                />
              )}
              {indicator.thresholds?.optimal && (
                <>
                  <ReferenceLine
                    y={indicator.thresholds.optimal.min}
                    stroke="#10B981"
                    strokeDasharray="3 3"
                    strokeOpacity={0.5}
                  />
                  <ReferenceLine
                    y={indicator.thresholds.optimal.max}
                    stroke="#10B981"
                    strokeDasharray="3 3"
                    strokeOpacity={0.5}
                    label="Optimal Range"
                  />
                </>
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke={colors.primary}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: colors.primary }}
              />
            </LineChart>
          );

        case 'area':
          return (
            <AreaChart data={data}>
              <defs>
                <linearGradient id={`area-gradient-${indicator.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.primary} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={colors.primary} stopOpacity={0.05} />
                </linearGradient>
              </defs>
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
                domain={['dataMin - 0.1', 'dataMax + 0.1']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #E5E7EB',
                  borderRadius: '0.375rem'
                }}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: any) => [
                  indicator.unit === '%' ? `${formatNumber(value)}%` :
                  indicator.unit === 'million' ? formatLargeNumber(value) :
                  formatNumber(value),
                  indicator.name
                ]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors.primary}
                strokeWidth={2}
                fill={`url(#area-gradient-${indicator.id})`}
              />
            </AreaChart>
          );

        case 'bar':
          return (
            <BarChart data={data.slice(-30)}>
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
                domain={['dataMin - 0.1', 'dataMax + 0.1']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #E5E7EB',
                  borderRadius: '0.375rem'
                }}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: any) => [
                  indicator.unit === '%' ? `${formatNumber(value)}%` :
                  indicator.unit === 'million' ? formatLargeNumber(value) :
                  formatNumber(value),
                  indicator.name
                ]}
              />
              <Bar
                dataKey="value"
                fill={colors.primary}
                radius={[2, 2, 0, 0]}
              />
            </BarChart>
          );

        default:
          return null;
      }
    };

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">{indicator.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{indicator.description}</p>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={() => setChartType('area')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                chartType === 'area'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              Area
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                chartType === 'line'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              Line
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                chartType === 'bar'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              Bar
            </button>
          </div>
        </div>

        {/* Current Value with Change */}
        <div className="flex items-baseline space-x-4 mb-6">
          <span className="text-3xl font-bold text-gray-900">
            {indicator.unit === '%' ? `${formatNumber(indicator.currentValue)}%` :
             indicator.unit === 'million' ? formatLargeNumber(indicator.currentValue) :
             formatNumber(indicator.currentValue)}
          </span>
          <span className={`text-sm font-medium ${
            indicator.trend === 'up' ? 'text-green-600' :
            indicator.trend === 'down' ? 'text-red-600' : 'text-gray-500'
          }`}>
            {indicator.trend === 'up' && '↑'}
            {indicator.trend === 'down' && '↓'}
            {indicator.changePercent > 0 ? `${formatNumber(Math.abs(indicator.changePercent))}%` :
             `${formatNumber(Math.abs(indicator.change), 4)}`}
            vs last period
          </span>
        </div>

        {/* Chart */}
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>

        {/* Additional Info */}
        <div className="mt-4 flex items-start space-x-2 text-sm text-gray-600">
          <InformationCircleIcon className="w-4 h-4 mt-0.5" />
          <span>
            {indicator.thresholds?.optimal && (
              <span>
                Optimal range: {formatNumber(indicator.thresholds.optimal.min)} - {formatNumber(indicator.thresholds.optimal.max)}
              </span>
            )}
            {' • '}
            Last updated: {new Date(indicator.lastUpdated).toLocaleDateString()}
          </span>
        </div>
      </div>
    );
  };

  const getIndicatorIcon = (indicatorId: string) => {
    switch (indicatorId) {
      case 'hibor':
      case 'interest_rate':
        return CurrencyDollarIcon;
      case 'gdp':
      case 'gdp_growth':
        return TrendingUpIcon;
      case 'unemployment':
        return UserGroupIcon;
      case 'visitor_arrivals':
        return GlobeAltIcon;
      case 'pmi':
      case 'manufacturing':
        return BuildingOfficeIcon;
      default:
        return ChartBarIcon;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Indicator Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indicators.map(renderIndicatorCard)}
      </div>

      {/* Detailed Chart */}
      {selectedIndicator && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Detailed View</h2>
            <button
              onClick={() => setSelectedIndicator(null)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </div>
          {renderDetailChart()}
        </div>
      )}
    </div>
  );
}