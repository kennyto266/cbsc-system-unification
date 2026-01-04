/**
 * Economic Data Charts Component
 * 經濟數據圖表組件
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  Scatter,
  ScatterChart,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  Area,
  AreaChart
} from 'recharts';
import { format } from 'date-fns';
import { useEconomicData } from '../hooks/useEconomicData';

// Types
interface EconomicDataPoint {
  date: string;
  value: number;
  indicator?: string;
}

interface ChartData {
  hibor: EconomicDataPoint[];
  gdp: EconomicDataPoint[];
  pmi: EconomicDataPoint[];
  visitors: EconomicDataPoint[];
  unemployment: EconomicDataPoint[];
}

interface EconomicDataChartsProps {
  className?: string;
  timeRange?: { start: string; end: string };
  chartType?: 'timeSeries' | 'scatter' | 'heatmap' | 'correlation' | 'comparison';
  indicators?: string[];
}

const CHART_COLORS = {
  hibor: { primary: '#3B82F6', secondary: '#60A5FA', gradient: '#DBEAFE' },
  gdp: { primary: '#10B981', secondary: '#34D399', gradient: '#D1FAE5' },
  pmi: { primary: '#F59E0B', secondary: '#FCD34D', gradient: '#FEF3C7' },
  visitors: { primary: '#8B5CF6', secondary: '#A78BFA', gradient: '#EDE9FE' },
  unemployment: { primary: '#EF4444', secondary: '#F87171', gradient: '#FEE2E2' }
};

// Custom tooltip formatter
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-medium text-gray-900 mb-2">{label}</p>
        <p className="text-sm text-gray-600">Date: {format(new Date(data.date), 'yyyy-MM-dd')}</p>
        <p className="text-sm text-gray-600">Value: {data.value?.toFixed(4)}</p>
        {data.indicator && <p className="text-sm text-gray-600">Indicator: {data.indicator}</p>}
      </div>
    );
  }
  return null;
};

// Scatter Plot for correlation analysis
const CorrelationScatter = ({ data, xIndicator, yIndicator }: {
  data: ChartData;
  xIndicator: string;
  yIndicator: string;
}) => {
  const scatterData = useMemo(() => {
    if (!data[xIndicator] || !data[yIndicator]) return [];

    const xData = data[xIndicator];
    const yData = data[yIndicator];
    const minLength = Math.min(xData.length, yData.length);

    return Array.from({ length: minLength }, (_, index) => ({
      x: xData[index].value,
      y: yData[index].value,
      date: xData[index].date,
      xIndicator,
      yIndicator
    }));
  }, [data, xIndicator, yIndicator]);

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart data={scatterData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            name={xIndicator}
            type="number"
            stroke="#6B7280"
          />
          <YAxis
            dataKey="y"
            name={yIndicator}
            type="number"
            stroke="#6B7280"
          />
          <Tooltip
            content={<CustomTooltip label={`${xIndicator} vs ${yIndicator}`} />}
          />
          <Scatter
            fill={CHART_COLORS[xIndicator as keyof typeof CHART_COLORS]?.primary}
            dataKey="x"
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

// Comparison Chart for multiple indicators
const ComparisonChart = ({ data, indicators }: { data: ChartData; indicators: string[] }) => {
  const comparisonData = useMemo(() => {
    if (!data) return [];

    const selectedData = indicators.filter(indicator => data[indicator as keyof ChartData]);

    return selectedData.flatMap(indicator =>
      data[indicator as keyof ChartData]?.map(point => ({
        ...point,
        indicator
      }))
    );
  }, [data, indicators]);

  const uniqueDates = useMemo(() => {
    const allDates = comparisonData.map(d => d.date);
    return [...new Set(allDates)].sort();
  }, [comparisonData]);

  const groupedData = useMemo(() => {
    return uniqueDates.map(date => {
      const dateData: any = { date };
      indicators.forEach(indicator => {
        const point = data[indicator as keyof ChartData]?.find(p =>
          p.date === date
        );
        dateData[indicator] = point?.value || null;
      });
      return dateData;
    });
  }, [uniqueDates, indicators, data]);

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={groupedData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="date"
            stroke="#6B7280"
            tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          />
          <YAxis stroke="#6B7280" />
          <Tooltip content={<CustomTooltip label="Economic Indicators Comparison" />} />
          <Legend />
          {indicators.map((indicator, index) => (
            <Line
              key={indicator}
              type="monotone"
              dataKey={indicator}
              stroke={CHART_COLORS[indicator as keyof typeof CHART_COLORS]?.primary}
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name={indicator.toUpperCase()}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Heat Map (Simplified implementation using Bar chart)
const EconomicHeatmap = ({ data, indicators }: { data: ChartData; indicators: string[] }) => {
  const heatmapData = useMemo(() => {
    if (!data) return [];

    const latestData: any = {};
    indicators.forEach(indicator => {
      const points = data[indicator as keyof ChartData];
      if (points && points.length > 0) {
        latestData[indicator] = points[points.length - 1].value;
      }
    });

    return Object.entries(latestData).map(([indicator, value]) => ({
      indicator,
      value: value || 0,
      fill: CHART_COLORS[indicator as keyof typeof CHART_COLORS]?.primary
    }));
  }, [data, indicators]);

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={heatmapData} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis type="number" stroke="#6B7280" />
          <YAxis
            dataKey="indicator"
            type="category"
            stroke="#6B7280"
          />
          <Tooltip
            content={({ active, payload }: any) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                    <p className="font-medium text-gray-900">{payload[0].payload?.indicator}</p>
                    <p className="text-sm text-gray-600">Value: {payload[0].value?.toFixed(4)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Advanced Time Series with Annotations
const AdvancedTimeSeries = ({ data, indicators }: { data: ChartData; indicators: string[] }) => {
  const processedData = useMemo(() => {
    if (!data) return [];

    const allData: any[] = [];
    indicators.forEach(indicator => {
      const points = data[indicator as keyof ChartData] || [];
      points.forEach(point => {
        allData.push({
          ...point,
          indicator,
          date: new Date(point.date).getTime()
        });
      });
    });

    return allData.sort((a, b) => a.date - b.date);
  }, [data, indicators]);

  const signals = useMemo(() => {
    // Simulated signal data
    return [
      { date: new Date('2024-01-15').getTime(), indicator: 'hibor', type: 'buy', strength: 0.8 },
      { date: new Date('2024-02-01').getTime(), indicator: 'pmi', type: 'sell', strength: 0.6 },
      { date: new Date('2024-03-01').getTime(), indicator: 'gdp', type: 'buy', strength: 0.7 }
    ];
  }, []);

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={processedData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="date"
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          />
          <YAxis
            stroke="#6B7280"
            domain={['dataMin - 0.1', 'dataMax + 0.1']}
          />
          <Tooltip
            content={({ active, payload }: any) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                    <p className="font-medium text-gray-900">{data.indicator?.toUpperCase()}</p>
                    <p className="text-sm text-gray-600">Date: {format(data.date, 'yyyy-MM-dd')}</p>
                    <p className="text-sm text-gray-600">Value: {data.value?.toFixed(4)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />

          {indicators.map((indicator, index) => (
            <Line
              key={indicator}
              type="monotone"
              dataKey="value"
              stroke={CHART_COLORS[indicator as keyof typeof CHART_COLORS]?.primary}
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name={indicator.toUpperCase()}
              data={processedData.filter(d => d.indicator === indicator)}
            />
          ))}

          {/* Signal Markers */}
          {signals.map((signal, index) => (
            <ReferenceLine
              key={index}
              x={signal.date}
              stroke={signal.type === 'buy' ? '#10B981' : '#EF4444'}
              strokeWidth={2}
              strokeDasharray="5 5"
              label={`${signal.type.toUpperCase()} - ${signal.indicator.toUpperCase()}`}
              labelPosition="top"
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// Main Component
export default function EconomicDataCharts({
  className = '',
  timeRange,
  chartType = 'timeSeries',
  indicators = ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment']
}: EconomicDataChartsProps) {
  const { data, loading, error, fetchAllIndicators } = useEconomicData({
    autoFetch: true
  });

  const [xIndicator, setXIndicator] = useState('hibor');
  const [yIndicator, setYIndicator] = useState('gdp');

  useEffect(() => {
    if (timeRange && Object.keys(timeRange).length === 2) {
      fetchAllIndicators(timeRange);
    }
  }, [timeRange, fetchAllIndicators]);

  const renderChart = () => {
    switch (chartType) {
      case 'scatter':
        return (
          <div className="space-y-4">
            <div className="flex space-x-4 items-center">
              <label className="text-sm font-medium text-gray-700">X Axis:</label>
              <select
                value={xIndicator}
                onChange={(e) => setXIndicator(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {indicators.map(indicator => (
                  <option key={indicator} value={indicator}>
                    {indicator.toUpperCase()}
                  </option>
                ))}
              </select>
              <label className="text-sm font-medium text-gray-700">Y Axis:</label>
              <select
                value={yIndicator}
                onChange={(e) => setYIndicator(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {indicators.map(indicator => (
                  <option key={indicator} value={indicator}>
                    {indicator.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <CorrelationScatter data={data} xIndicator={xIndicator} yIndicator={yIndicator} />
          </div>
        );

      case 'heatmap':
        return <EconomicHeatmap data={data} indicators={indicators} />;

      case 'correlation':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Compare:</label>
              <select
                multiple
                value={indicators}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  // Update parent state if needed
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {indicators.map(indicator => (
                  <option key={indicator} value={indicator}>
                    {indicator.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <ComparisonChart data={data} indicators={indicators} />
          </div>
        );

      case 'comparison':
        return <ComparisonChart data={data} indicators={indicators} />;

      default:
        return <AdvancedTimeSeries data={data} indicators={indicators} />;
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading economic data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <div className="text-red-500 text-lg mb-2">⚠️</div>
          <p className="text-gray-600">Error loading data: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Chart Type Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-2">
          {['timeSeries', 'scatter', 'heatmap', 'correlation', 'comparison'].map((type) => (
            <button
              key={type}
              onClick={() => {/* Handle chart type change */}}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                chartType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type === 'timeSeries' && 'Time Series'}
              {type === 'scatter' && 'Scatter Plot'}
              {type === 'heatmap' && 'Heat Map'}
              {type === 'correlation' && 'Correlation'}
              {type === 'comparison' && 'Comparison'}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Display */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {renderChart()}
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Legend</h4>
        <div className="flex flex-wrap gap-4">
          {indicators.map(indicator => (
            <div key={indicator} className="flex items-center space-x-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: CHART_COLORS[indicator as keyof typeof CHART_COLORS]?.primary }}
              />
              <span className="text-sm text-gray-700">{indicator.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}