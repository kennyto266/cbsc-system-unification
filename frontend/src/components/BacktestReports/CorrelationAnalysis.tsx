import React, { useState } from 'react';
import {
  ChartBarIcon,
  InformationCircleIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  BarChart,
  Bar
} from 'recharts';

interface CorrelationAnalysisProps {
  data: {
    economicIndicators: Array<{
      name: string;
      values: number[];
      dates: string[];
    }>;
    strategyReturns: number[];
    correlationMatrix: Record<string, number>;
  };
  className?: string;
}

const CorrelationAnalysis: React.FC<CorrelationAnalysisProps> = ({ data, className = '' }) => {
  const [selectedIndicator, setSelectedIndicator] = useState<string>(
    data.economicIndicators[0]?.name || ''
  );

  const formatNumber = (value: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const getCorrelationColor = (value: number) => {
    if (Math.abs(value) >= 0.7) return value >= 0 ? 'text-green-600' : 'text-red-600';
    if (Math.abs(value) >= 0.3) return value >= 0 ? 'text-blue-600' : 'text-orange-600';
    return 'text-gray-500';
  };

  const getCorrelationStrength = (value: number) => {
    const abs = Math.abs(value);
    if (abs >= 0.7) return 'Strong';
    if (abs >= 0.3) return 'Moderate';
    if (abs >= 0.1) return 'Weak';
    return 'Very Weak';
  };

  const getCorrelationDirection = (value: number) => {
    return value >= 0 ? 'Positive' : 'Negative';
  };

  const prepareScatterData = () => {
    const indicator = data.economicIndicators.find(ind => ind.name === selectedIndicator);
    if (!indicator || !data.strategyReturns) return [];

    const minLength = Math.min(indicator.values.length, data.strategyReturns.length);
    return Array.from({ length: minLength }, (_, i) => ({
      x: indicator.values[i],
      y: data.strategyReturns[i],
      date: indicator.dates[i]
    }));
  };

  const prepareBarData = () => {
    return Object.entries(data.correlationMatrix).map(([name, correlation]) => ({
      name,
      correlation,
      absCorrelation: Math.abs(correlation)
    }));
  };

  const calculatePValue = (correlation: number, n: number): number => {
    // Simplified p-value calculation for correlation
    const t = Math.abs(correlation) * Math.sqrt((n - 2) / (1 - correlation * correlation));
    // Approximation for p-value (would use t-distribution in practice)
    return t > 2.0 ? 0.05 : t > 1.5 ? 0.1 : 0.2;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium">
            {selectedIndicator}: {formatNumber(payload[0].value)}
          </p>
          <p className="text-sm">
            Return: {formatNumber(payload[1].value * 100, 2)}%
          </p>
          {payload[0].payload.date && (
            <p className="text-xs text-gray-500 mt-1">
              Date: {new Date(payload[0].payload.date).toLocaleDateString()}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const COLORS = {
    strong: '#10B981',
    moderate: '#3B82F6',
    weak: '#F59E0B',
    neutral: '#9CA3AF'
  };

  if (!data.economicIndicators || data.economicIndicators.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No correlation data available</h3>
        <p className="mt-1 text-sm text-gray-500">Economic indicators not available for this report.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <AcademicCapIcon className="w-5 h-5 text-gray-600" />
        <h2 className="text-xl font-semibold text-gray-900">Economic Data Correlation Analysis</h2>
      </div>

      {/* Correlation Matrix */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Correlation Coefficients</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.correlationMatrix).map(([indicator, correlation]) => (
            <div key={indicator} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">{indicator}</p>
                <p className="text-xs text-gray-500">
                  {getCorrelationStrength(correlation)} {getCorrelationDirection(correlation)}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-lg font-semibold ${getCorrelationColor(correlation)}`}>
                  {formatNumber(correlation)}
                </p>
                <p className="text-xs text-gray-500">
                  p {calculatePValue(correlation, data.strategyReturns.length) < 0.05 ? '< 0.05' : '> 0.05'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Correlation Visualization */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Correlation Visualization</h3>
          <select
            value={selectedIndicator}
            onChange={(e) => setSelectedIndicator(e.target.value)}
            className="block w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            {data.economicIndicators.map((indicator) => (
              <option key={indicator.name} value={indicator.name}>
                {indicator.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scatter Plot */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Scatter Plot</h4>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart data={prepareScatterData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="x"
                  name={selectedIndicator}
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  dataKey="y"
                  name="Return"
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${formatNumber(value * 100, 1)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Scatter
                  dataKey="y"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Correlation Bar Chart */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Correlation Heatmap</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={prepareBarData()} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  type="number"
                  domain={[-1, 1]}
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#6B7280"
                  tick={{ fontSize: 12 }}
                  width={100}
                />
                <Tooltip
                  formatter={(value: any) => [formatNumber(value), 'Correlation']}
                />
                <Bar dataKey="correlation">
                  {prepareBarData().map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.correlation >= 0.7 ? COLORS.strong :
                        entry.correlation >= 0.3 ? COLORS.moderate :
                        entry.correlation >= -0.3 ? COLORS.neutral :
                        entry.correlation >= -0.7 ? COLORS.weak :
                        COLORS.strong
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Statistical Analysis */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Statistical Significance</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Correlations with p-value &lt; 0.05 are considered statistically significant.
                The sample size (n) is {data.strategyReturns.length} data points.
              </p>
              <div className="mt-2 space-y-1">
                {Object.entries(data.correlationMatrix).map(([indicator, correlation]) => {
                  const pValue = calculatePValue(correlation, data.strategyReturns.length);
                  const isSignificant = pValue < 0.05;
                  return (
                    <p key={indicator} className="text-xs">
                      {indicator}: r = {formatNumber(correlation)}, p {isSignificant ? '< 0.05' : '> 0.05'}
                      {isSignificant && ' (significant)'}
                    </p>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CorrelationAnalysis;