import React, { useEffect, useRef, useState, useMemo } from 'react';
import lazy, { Suspense } from 'react';
import { useRealTimeChart, RealTimeDataPoint } from '../hooks/useRealTimeChart';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'), { ssr: false });

// 数据流接口
interface DataStream {
  id: string;
  name: string;
  color: string;
  yaxis?: 'y' | 'y2' | 'y3';
}

// Props接口
interface RealTimeChartProps {
  title?: string;
  subtitle?: string;
  streams: DataStream[];
  maxDataPoints?: number;
  updateInterval?: number;
  height?: number;
  className?: string;
  theme?: 'light' | 'dark';
  yAxes?: Array<{
    title: string;
    side?: 'left' | 'right';
    position?: number;
    range?: [number, number];
  }>;
  onDataPointAdd?: (streamId: string, dataPoint: RealTimeDataPoint) => void;
  wsUrl?: string;
}

export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  title,
  subtitle,
  streams,
  maxDataPoints = 100,
  updateInterval = 1000,
  height = 400,
  className = '',
  theme = 'light',
  yAxes = [
    { title: '主轴', side: 'left' }
  ],
  onDataPointAdd,
  wsUrl
}) => {
  // 使用实时数据Hook
  const { data, isConnected, isPaused, error, lastUpdate, pause, resume, clear, reconnect } = useRealTimeChart({
    url: wsUrl,
    maxDataPoints,
    updateInterval
  });

  // 存储每个数据流的数据
  const [streamData, setStreamData] = useState<Map<string, RealTimeDataPoint[]>>(new Map());

  // 初始化数据流
  useEffect(() => {
    const initialData = new Map<string, RealTimeDataPoint[]>();
    streams.forEach(stream => {
      initialData.set(stream.id, []);
    });
    setStreamData(initialData);
  }, [streams]);

  // 更新流数据
  useEffect(() => {
    if (data.length === 0) return;

    // 获取最新的数据点
    const latestPoint = data[data.length - 1];

    // 更新每个流（实际应用中，数据点应该包含流ID）
    streams.forEach(stream => {
      setStreamData(prev => {
        const newData = new Map(prev);
        const currentData = newData.get(stream.id) || [];

        // 添加新数据点（这里模拟每个流都有自己的数据）
        const streamPoint: RealTimeDataPoint = {
          ...latestPoint,
          value: latestPoint.value * (1 + Math.random() * 0.2 - 0.1), // 添加一些随机变化
          metadata: {
            streamId: stream.id,
            ...latestPoint.metadata
          }
        };

        const updatedData = [...currentData, streamPoint];

        // 限制数据点数量
        if (updatedData.length > maxDataPoints) {
          updatedData.splice(0, updatedData.length - maxDataPoints);
        }

        newData.set(stream.id, updatedData);

        // 触发回调
        if (onDataPointAdd) {
          onDataPointAdd(stream.id, streamPoint);
        }

        return newData;
      });
    });
  }, [data, streams, maxDataPoints, onDataPointAdd]);

  // 构建Plotly数据
  const plotlyData = useMemo(() => {
    const traces: any[] = [];

    streams.forEach(stream => {
      const data = streamData.get(stream.id) || [];

      if (data.length === 0) return;

      traces.push({
        x: data.map(d => new Date(d.timestamp)),
        y: data.map(d => d.value),
        type: 'scatter',
        mode: 'lines',
        name: stream.name,
        line: {
          color: stream.color,
          width: 2
        },
        yaxis: stream.yaxis || 'y'
      });

      // 添加最新数据点的标记
      if (data.length > 0) {
        const lastPoint = data[data.length - 1];
        traces.push({
          x: [new Date(lastPoint.timestamp)],
          y: [lastPoint.value],
          type: 'scatter',
          mode: 'markers',
          name: `${stream.name} (最新)`,
          marker: {
            color: stream.color,
            size: 8,
            symbol: 'circle'
          },
          yaxis: stream.yaxis || 'y',
          showlegend: false
        });
      }
    });

    return traces;
  }, [streams, streamData]);

  // 图表布局
  const layout = useMemo(() => {
    const isDark = theme === 'dark';
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#f3f4f6';
    const bgColor = isDark ? '#1f2937' : '#ffffff';

    // 构建多个Y轴
    const yAxisConfig: any = {
      yaxis: {
        title: yAxes[0]?.title || '值',
        gridcolor: gridColor,
        showgrid: true,
        color: textColor,
        linecolor: textColor,
        mirror: true,
        range: yAxes[0]?.range
      }
    };

    // 添加额外的Y轴
    yAxes.slice(1).forEach((axis, index) => {
      yAxisConfig[`yaxis${index + 2}`] = {
        title: axis.title,
        gridcolor: gridColor,
        showgrid: false,
        color: textColor,
        linecolor: textColor,
        mirror: true,
        overlaying: 'y',
        side: axis.side || 'right',
        position: axis.position || (index + 1) * (1 / (yAxes.length)),
        range: axis.range,
        anchor: 'x'
      };
    });

    return {
      title: title ? {
        text: title,
        font: {
          color: textColor,
          size: 18
        }
      } : undefined,
      height,
      plot_bgcolor: bgColor,
      paper_bgcolor: bgColor,
      font: {
        color: textColor
      },
      showlegend: true,
      legend: {
        x: 0,
        y: 1,
        bgcolor: 'rgba(255,255,255,0)',
        bordercolor: 'rgba(255,255,255,0)',
        orientation: 'h'
      },
      xaxis: {
        type: 'date',
        gridcolor: gridColor,
        showgrid: true,
        color: textColor,
        linecolor: textColor,
        mirror: true
      },
      ...yAxisConfig,
      margin: {
        l: 60,
        r: 60,
        t: 40,
        b: 40
      },
      shapes: [
        // 添加当前时间线
        {
          type: 'line',
          x0: lastUpdate,
          y0: 0,
          x1: lastUpdate,
          y1: 1,
          xref: 'x',
          yref: 'paper',
          line: {
            color: '#ef4444',
            width: 2,
            dash: 'dash'
          }
        }
      ]
    };
  }, [theme, title, height, yAxes, lastUpdate]);

  // 配置选项
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'pan2d',
      'select2d',
      'lasso2d',
      'toggleSpikelines',
      'hoverClosestCartesian',
      'hoverCompareCartesian'
    ],
    toImageButtonOptions: {
      format: 'png',
      filename: `realtime-chart-${Date.now()}`,
      height: height,
      width: 1200,
      scale: 2
    },
    responsive: true
  }), [height]);

  return (
    <Suspense fallback={<div>Loading...</div>}>
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* 状态栏 */}
      <div className="px-6 pt-4 flex items-center justify-between">
        <div>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-4">
          {/* 连接状态 */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isConnected ? '已连接' : '已断开'}
            </span>
          </div>

          {/* 暂停状态 */}
          {isPaused && (
            <span className="text-sm text-yellow-600 dark:text-yellow-400">
              已暂停
            </span>
          )}

          {/* 最后更新时间 */}
          {lastUpdate && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              更新: {lastUpdate.toLocaleTimeString('zh-CN')}
            </span>
          )}

          {/* 控制按钮 */}
          <button
            onClick={isPaused ? resume : pause}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            {isPaused ? '继续' : '暂停'}
          </button>

          <button
            onClick={clear}
            className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            清空
          </button>

          {error && (
            <button
              onClick={reconnect}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              重连
            </button>
          )}
        </div>
      </div>

      {/* 图表容器 */}
      <div className="p-6 pt-0">
        {error ? (
          <div className="h-96 flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-500 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            </div>
          </div>
        ) : (
          <Plot
            data={plotlyData}
            layout={layout}
            config={config}
            className="w-full"
          />
        )}
      </div>
    </div>
  );
    </Suspense>
  );
};