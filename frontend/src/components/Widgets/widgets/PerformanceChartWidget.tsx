import React, { useEffect, useRef } from 'react';
import { Widget } from '../../../types/widget';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface PerformanceChartWidgetProps {
  widget: Widget;
}

export function PerformanceChartWidget({ widget }: PerformanceChartWidgetProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartType, setChartType] = useState<'line' | 'area'>('area');
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m' | '1y'>('1m');

  // Generate mock data
  const generateData = (days: number) => {
    const data = [];
    let baseValue = 100000;
    const now = new Date();

    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Simulate market movements
      const change = (Math.random() - 0.48) * 0.03; // Slight upward bias
      baseValue = baseValue * (1 + change);

      // Add strategy returns
      const strategyReturn = baseValue * 0.0002 * i; // Strategy alpha

      data.push({
        date: date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' }),
        benchmark: baseValue,
        strategy: baseValue + strategyReturn,
        profit: ((baseValue + strategyReturn) / 100000 - 1) * 100,
      });
    }

    return data;
  };

  const [data, setData] = useState(() => generateData(30));

  // Update data when time range changes
  useEffect(() => {
    const days = {
      '1d': 1,
      '1w': 7,
      '1m': 30,
      '3m': 90,
      '1y': 365,
    }[timeRange];

    setData(generateData(days));
  }, [timeRange]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-2 shadow-lg">
          <p className="text-sm font-medium mb-1">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name === 'benchmark' ? '基準' : '策略'}:
              {' $' + entry.value.toFixed(2)}
            </p>
          ))}
          {payload[1] && (
            <p className="text-xs text-green-600 mt-1">
              收益率: {payload[1].payload.profit.toFixed(2)}%
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-full flex flex-col" ref={chartRef}>
      {/* Chart controls */}
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setChartType(chartType === 'line' ? 'area' : 'line')}
            className="text-xs px-2 py-1 rounded border hover:bg-muted"
          >
            {chartType === 'line' ? '面積圖' : '折線圖'}
          </button>
        </div>

        <div className="flex items-center gap-1">
          {(['1d', '1w', '1m', '3m', '1y'] as const).map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`text-xs px-2 py-1 rounded ${
                timeRange === range
                  ? 'bg-primary text-primary-foreground'
                  : 'border hover:bg-muted'
              }`}
            >
              {range === '1d' ? '1日' :
               range === '1w' ? '1周' :
               range === '1m' ? '1月' :
               range === '3m' ? '3月' : '1年'}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'line' ? (
            <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                domain={['dataMin - 5000', 'dataMax + 5000']}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                formatter={(value) => value === 'benchmark' ? '基準指數' : '策略表現'}
              />
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#94a3b8"
                strokeWidth={1}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="strategy"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          ) : (
            <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                domain={['dataMin - 5000', 'dataMax + 5000']}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                formatter={(value) => value === 'benchmark' ? '基準指數' : '策略表現'}
              />
              <Area
                type="monotone"
                dataKey="benchmark"
                stackId="1"
                stroke="#94a3b8"
                fill="#94a3b8"
                fillOpacity={0.3}
              />
              <Area
                type="monotone"
                dataKey="strategy"
                stackId="2"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-3 border-t">
        <div className="text-center">
          <div className="text-xs text-muted-foreground">總收益</div>
          <div className="text-sm font-semibold text-green-600">
            +{data[data.length - 1]?.profit.toFixed(2) || 0}%
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground">最大回撤</div>
          <div className="text-sm font-semibold text-red-600">
            -{Math.abs(Math.random() * 10).toFixed(2)}%
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground">夏普比率</div>
          <div className="text-sm font-semibold">
            {(1.5 + Math.random() * 0.5).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}