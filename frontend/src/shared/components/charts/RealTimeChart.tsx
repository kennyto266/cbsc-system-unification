import React, { useState, useEffect, useRef } from 'react';
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { DataPoint, ChartStats, RealTimeChartProps } from './types';

export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  title = '实时数据图表',
  dataSource,
  updateInterval = 1000,
  maxDataPoints = 50,
  height = 300,
  className
}) => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [isRunning, setIsRunning] = useState(true);
  const [lastValue, setLastValue] = useState<number>(0);
  const intervalRef = useRef<NodeJS.Timeout>();

  // Fetch data point
  const fetchDataPoint = async (): Promise<number> => {
    if (dataSource) {
      return await dataSource();
    }
    // Mock data generation
    return Math.random() * 100;
  };

  // Add new data point
  const addDataPoint = async () => {
    try {
      const value = await fetchDataPoint();
      const now = new Date();
      const timeString = now.toLocaleTimeString('zh-CN');

      setData(prevData => {
        const newPoint = { time: timeString, value };
        const updatedData = [...prevData, newPoint];

        // Keep only the last maxDataPoints
        if (updatedData.length > maxDataPoints) {
          return updatedData.slice(-maxDataPoints);
        }

        return updatedData;
      });

      setLastValue(value);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // Initialize with some data using dataSource or reasonable default
  useEffect(() => {
    const initializeData = async () => {
      const initialData: DataPoint[] = [];

      // Try to get initial value from dataSource
      let baseValue = 12.5; // Default fallback value
      if (dataSource) {
        try {
          baseValue = await dataSource();
        } catch (e) {
          console.warn('Failed to get initial data point, using default');
        }
      }

      // Generate initial data points around the base value
      for (let i = maxDataPoints - 10; i > 0; i--) {
        const now = new Date();
        now.setSeconds(now.getSeconds() - i);
        // Add small random fluctuation around base value
        const fluctuation = (Math.random() - 0.5) * 0.5;
        initialData.push({
          time: now.toLocaleTimeString('zh-CN'),
          value: baseValue + fluctuation
        });
      }
      setData(initialData);
      setLastValue(baseValue);
    };

    initializeData();
  }, [maxDataPoints, dataSource]);

  // Real-time updates
  useEffect(() => {
    if (isRunning) {
      addDataPoint(); // Add first point immediately

      intervalRef.current = setInterval(() => {
        addDataPoint();
      }, updateInterval);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, updateInterval]);

  const handleToggle = () => {
    setIsRunning(!isRunning);
  };

  const handleReset = () => {
    setData([]);
    setIsRunning(false);
  };

  // Calculate statistics
  const stats = React.useMemo((): ChartStats => {
    if (data.length === 0) return { avg: 0, min: 0, max: 0, trend: 'stable' };

    const values = data.map(d => d.value);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);

    // Calculate trend
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    const trend = secondAvg > firstAvg * 1.02 ? 'up' :
                  secondAvg < firstAvg * 0.98 ? 'down' : 'stable';

    return { avg, min, max, trend };
  }, [data]);

  const isDark = document.documentElement.classList.contains('dark');

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md ${className || ''}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">{title}</h3>
          <div className="flex items-center space-x-2">
            <span className={`text-xs px-2 py-1 rounded ${
              isRunning
                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
            }`}>
              {isRunning ? '运行中' : '已暂停'}
            </span>
            <button
              onClick={handleToggle}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label={isRunning ? 'Pause' : 'Play'}
            >
              {isRunning ? (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              )}
            </button>
            <button
              onClick={handleReset}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Reset"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
          <span>当前: {lastValue.toFixed(2)}</span>
          <span>平均: {stats.avg.toFixed(2)}</span>
          <span>最大: {stats.max.toFixed(2)}</span>
          <span>最小: {stats.min.toFixed(2)}</span>
        </div>
      </div>

      {/* Chart */}
      <div className="p-4">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10 }}
              interval="preserveStartEnd"
              stroke={isDark ? '#9ca3af' : '#6b7280'}
            />
            <YAxis
              tick={{ fontSize: 10 }}
              tickFormatter={(value) => value.toFixed(2)}
              domain={['dataMin - 0.5', 'dataMax + 0.5']}
              stroke={isDark ? '#9ca3af' : '#6b7280'}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#1f2937' : '#ffffff',
                border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                borderRadius: '6px',
                color: isDark ? '#e5e7eb' : '#111827'
              }}
              labelStyle={{ color: isDark ? '#f9fafb' : '#111827' }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#3b82f6' }}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RealTimeChart;
