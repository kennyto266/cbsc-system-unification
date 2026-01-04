import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { PerformanceData, PerformanceChartProps } from './types';

const mockData: PerformanceData[] = [
  { date: '2024-01', value: 100000, benchmark: 100000 },
  { date: '2024-02', value: 102000, benchmark: 101000 },
  { date: '2024-03', value: 105000, benchmark: 102000 },
  { date: '2024-04', value: 103000, benchmark: 103000 },
  { date: '2024-05', value: 108000, benchmark: 104000 },
  { date: '2024-06', value: 112000, benchmark: 105000 },
  { date: '2024-07', value: 115000, benchmark: 106000 },
  { date: '2024-08', value: 113000, benchmark: 107000 },
  { date: '2024-09', value: 118000, benchmark: 108000 },
  { date: '2024-10', value: 123500, benchmark: 109000 },
];

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data = mockData,
  height = 320,
  showBenchmark = true,
  title
}) => {
  // Simple dark mode detection
  const isDark = document.documentElement.classList.contains('dark');

  const formatCurrency = (value: number) => {
    return `¥${(value / 1000).toFixed(0)}K`;
  };

  // Calculate return percentage
  const calculateReturn = (current: number, initial: number) => {
    return ((current - initial) / initial * 100).toFixed(2);
  };

  const initialValue = data[0]?.value || 100000;

  // Transform data for percentage display
  const transformedData = data.map(item => ({
    ...item,
    return: parseFloat(calculateReturn(item.value, initialValue)),
    benchmarkReturn: item.benchmark ? parseFloat(calculateReturn(item.benchmark, initialValue)) : undefined
  }));

  return (
    <div className="w-full">
      {title && (
        <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">
          {title}
        </h3>
      )}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={transformedData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorBenchmark" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#9ca3af" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={isDark ? '#374151' : '#e5e7eb'}
              vertical={false}
            />
            <XAxis
              dataKey="date"
              stroke={isDark ? '#9ca3af' : '#6b7280'}
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke={isDark ? '#9ca3af' : '#6b7280'}
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}%`}
              domain={['dataMin - 1', 'dataMax + 1']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#1f2937' : '#ffffff',
                border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                borderRadius: '8px',
                color: isDark ? '#e5e7eb' : '#111827'
              }}
              formatter={(value: number, name: string) => {
                if (name === '策略收益') {
                  return [`${value}%`, '策略收益'];
                }
                if (name === '基准') {
                  return [`${value}%`, '基准'];
                }
                return [value, name];
              }}
              labelStyle={{ color: isDark ? '#f9fafb' : '#111827' }}
            />
            <Area
              type="monotone"
              dataKey="return"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorValue)"
              name="策略收益"
            />
            {showBenchmark && transformedData.some(d => d.benchmarkReturn !== undefined) && (
              <Line
                type="monotone"
                dataKey="benchmarkReturn"
                stroke="#9ca3af"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 5"
                name="基准"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart;
