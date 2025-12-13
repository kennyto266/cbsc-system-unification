import React, { useMemo, memo } from 'react';
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

// Custom hook for data optimization
const useOptimizedData = (data: any[], maxPoints: number = 500) => {
  return useMemo(() => {
    if (!data || data.length <= maxPoints) {
      return data;
    }

    // Downsample data for better performance
    const step = Math.ceil(data.length / maxPoints);
    const optimized = [];

    for (let i = 0; i < data.length; i += step) {
      // Take average of points in this step
      let sum = 0;
      let count = 0;

      for (let j = i; j < Math.min(i + step, data.length); j++) {
        if (data[j].value !== null && data[j].value !== undefined) {
          sum += data[j].value;
          count++;
        }
      }

      if (count > 0) {
        optimized.push({
          ...data[i],
          value: sum / count,
        });
      }
    }

    return optimized;
  }, [data, maxPoints]);
};

// Memoized Tooltip component
const CustomTooltip = memo(({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="text-sm font-semibold text-gray-900 mb-2">{`日期: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
});

CustomTooltip.displayName = 'CustomTooltip';

interface OptimizedChartProps {
  data: any[];
  type?: 'line' | 'area';
  xKey: string;
  yKey: string;
  height?: number;
  strokeColor?: string;
  fillColor?: string;
  maxPoints?: number;
}

export const OptimizedChart: React.FC<OptimizedChartProps> = ({
  data,
  type = 'line',
  xKey,
  yKey,
  height = 300,
  strokeColor = '#3b82f6',
  fillColor = '#3b82f6',
  maxPoints = 500,
}) => {
  const optimizedData = useOptimizedData(data, maxPoints);

  return (
    <ResponsiveContainer width="100%" height={height}>
      {type === 'area' ? (
        <AreaChart
          data={optimizedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id={`color-${yKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={fillColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={fillColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey={xKey}
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={yKey}
            stroke={strokeColor}
            strokeWidth={2}
            fill={`url(#color-${yKey})`}
            animationDuration={1000}
            animationBegin={0}
          />
        </AreaChart>
      ) : (
        <LineChart
          data={optimizedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey={xKey}
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={strokeColor}
            strokeWidth={2}
            dot={false}
            animationDuration={1000}
            animationBegin={0}
          />
        </LineChart>
      )}
    </ResponsiveContainer>
  );
};

// Memoized version to prevent unnecessary re-renders
export default memo(OptimizedChart);