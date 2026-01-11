import React, { useMemo } from 'react';
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
  Legend,
  Brush,
} from 'recharts';
import { PerformanceData } from '../../../types/dashboard';
import Card from '../../../components/ui/Card';
import { formatCurrency, formatPercentage } from '../../../utils/formatters';

interface PerformanceChartProps {
  data: PerformanceData[];
  period: string;
  title?: string;
  showBenchmark?: boolean;
  showDrawdown?: boolean;
}

// Custom tooltip for the chart
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="text-sm font-semibold text-gray-900 mb-2">{`日期: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${entry.name.includes('收益率')
              ? formatPercentage(entry.value)
              : formatCurrency(entry.value)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Format date based on period
const formatDate = (dateStr: string, period: string) => {
  const date = new Date(dateStr);

  switch (period) {
    case '1D':
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    case '1W':
      return date.toLocaleDateString('zh-CN', { weekday: 'short', month: 'numeric', day: 'numeric' });
    case '1M':
    case '3M':
      return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
    case '6M':
    case '1Y':
    case 'ALL':
      return date.toLocaleDateString('zh-CN', { year: '2-digit', month: 'numeric' });
    default:
      return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
  }
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  period,
  title = '策略收益曲线',
  showBenchmark = true,
  showDrawdown = true,
}) => {
  // Process data for chart
  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      dateFormatted: formatDate(item.date, period),
      returnRate: item.value * 100, // Convert to percentage
      benchmarkRate: item.benchmark ? item.benchmark * 100 : null,
      drawdownPercent: item.drawdown ? item.drawdown * 100 : null,
    }));
  }, [data, period]);

  // Calculate Y-axis domain
  const yDomain = useMemo(() => {
    if (!chartData.length) return [0, 100];

    const allValues = chartData.flatMap(d => [
      d.returnRate,
      d.benchmarkRate,
    ].filter(v => v !== null));

    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const padding = (maxValue - minValue) * 0.1;

    return [minValue - padding, maxValue + padding];
  }, [chartData]);

  return (
    <Card className="h-full" title={title}>
      <div className="h-full flex flex-col">
        {/* Chart Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            {showBenchmark && (
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">策略收益</span>
              </div>
            )}
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">基准</span>
            </div>
          </div>
          {showDrawdown && (
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">回撤</span>
            </div>
          )}
        </div>

        {/* Chart Container */}
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorReturn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorBenchmark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#9ca3af" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

              <XAxis
                dataKey="dateFormatted"
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                domain={yDomain}
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
              />

              <Tooltip content={<CustomTooltip />} />

              {/* Main Performance Line */}
              <Area
                type="monotone"
                dataKey="returnRate"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorReturn)"
                name="策略收益率"
              />

              {/* Benchmark Line */}
              {showBenchmark && chartData.some(d => d.benchmarkRate !== null) && (
                <Line
                  type="monotone"
                  dataKey="benchmarkRate"
                  stroke="#9ca3af"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                  name="基准收益率"
                />
              )}

              {/* Drawdown Area */}
              {showDrawdown && chartData.some(d => d.drawdownPercent !== null) && (
                <Area
                  type="monotone"
                  dataKey="drawdownPercent"
                  stroke="#ef4444"
                  strokeWidth={1}
                  fill="url(#colorDrawdown)"
                  fillOpacity={0.5}
                  name="回撤"
                />
              )}

              {/* Brush for zooming */}
              <Brush
                dataKey="dateFormatted"
                height={30}
                stroke="#3b82f6"
                fill="#f3f4f6"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Summary */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">期间收益</p>
              <p className="font-semibold text-gray-900">
                {chartData.length > 0
                  ? formatPercentage((chartData[chartData.length - 1].returnRate - chartData[0].returnRate) / 100)
                  : '0%'
                }
              </p>
            </div>
            <div>
              <p className="text-gray-500">年化收益</p>
              <p className="font-semibold text-gray-900">
                {chartData.length > 1
                  ? formatPercentage(chartData[chartData.length - 1].returnRate / 100)
                  : '0%'
                }
              </p>
            </div>
            <div>
              <p className="text-gray-500">最大回撤</p>
              <p className="font-semibold text-red-600">
                {chartData.length > 0
                  ? formatPercentage(Math.min(...chartData.map(d => d.drawdownPercent || 0)) / 100)
                  : '0%'
                }
              </p>
            </div>
            <div>
              <p className="text-gray-500">胜率</p>
              <p className="font-semibold text-gray-900">
                {chartData.length > 0
                  ? formatPercentage((chartData.filter(d => d.returnRate > 0).length / chartData.length))
                  : '0%'
                }
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};