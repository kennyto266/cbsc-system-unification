import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import {
  Maximize2, Minimize2, RotateCw, Download, Share2,
  TrendingUp, TrendingDown, Minus
} from 'lucide-react';
import GestureRecognizer, { GestureCallbacks } from '../Gesture/GestureRecognizer';
import { clsx } from 'clsx';

interface DataPoint {
  name: string;
  value: number;
  value2?: number;
  timestamp?: number;
}

interface MobileOptimizedChartProps {
  // Data and configuration
  data: DataPoint[];
  type?: 'line' | 'area' | 'bar' | 'pie';
  title?: string;
  subtitle?: string;
  height?: number;
  width?: number;

  // Styling
  colors?: string[];
  backgroundColor?: string;
  gridColor?: string;
  textColor?: string;

  // Mobile optimizations
  enableGestures?: boolean;
  enableFullscreen?: boolean;
  enableZoom?: boolean;
  enablePan?: boolean;
  adaptiveRendering?: boolean;

  // Simplified mode for very small screens
  simplified?: boolean;
  showTrendIndicator?: boolean;
  showMinMax?: boolean;

  // Callbacks
  onDataPointClick?: (point: DataPoint, index: number) => void;
  onZoomChange?: (zoomLevel: number) => void;
  onFullscreenToggle?: (isFullscreen: boolean) => void;
}

interface TrendIndicator {
  direction: 'up' | 'down' | 'neutral';
  percentage: number;
}

/**
 * MobileOptimizedChart - Touch-friendly, responsive chart component
 */
const MobileOptimizedChart: React.FC<MobileOptimizedChartProps> = ({
  data,
  type = 'line',
  title,
  subtitle,
  height = 300,
  width,

  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
  backgroundColor = '#ffffff',
  gridColor = '#e5e7eb',
  textColor = '#6b7280',

  enableGestures = true,
  enableFullscreen = true,
  enableZoom = true,
  enablePan = true,
  adaptiveRendering = true,

  simplified = false,
  showTrendIndicator = true,
  showMinMax = true,

  onDataPointClick,
  onZoomChange,
  onFullscreenToggle,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [selectedPoint, setSelectedPoint] = useState<DataPoint | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [trend, setTrend] = useState<TrendIndicator | null>(null);

  // Calculate trend indicator
  useEffect(() => {
    if (!showTrendIndicator || data.length < 2) {
      setTrend(null);
      return;
    }

    const firstValue = data[0].value;
    const lastValue = data[data.length - 1].value;
    const percentage = ((lastValue - firstValue) / firstValue) * 100;

    let direction: 'up' | 'down' | 'neutral';
    if (percentage > 1) direction = 'up';
    else if (percentage < -1) direction = 'down';
    else direction = 'neutral';

    setTrend({
      direction,
      percentage: Math.abs(percentage),
    });
  }, [data, showTrendIndicator]);

  // Get min and max values
  const getValueRange = useCallback(() => {
    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    return { min, max };
  }, [data]);

  // Simplified data for very small screens
  const getSimplifiedData = useCallback((fullData: DataPoint[]): DataPoint[] => {
    if (fullData.length <= 5) return fullData;

    // Sample data points - show first, middle, last, and max/min points
    const result: DataPoint[] = [];
    const { min, max } = getValueRange();

    // Always include first and last
    result.push(fullData[0]);
    result.push(fullData[fullData.length - 1]);

    // Include min and max points if they're not already included
    const minIndex = fullData.findIndex(d => d.value === min);
    const maxIndex = fullData.findIndex(d => d.value === max);

    if (minIndex > 0 && minIndex < fullData.length - 1) {
      result.push(fullData[minIndex]);
    }
    if (maxIndex > 0 && maxIndex < fullData.length - 1 && maxIndex !== minIndex) {
      result.push(fullData[maxIndex]);
    }

    // Sort by timestamp or index
    return result.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
  }, [getValueRange]);

  // Handle gesture callbacks
  const gestureCallbacks: GestureCallbacks = {
    onDoubleTap: () => {
      if (enableFullscreen) {
        toggleFullscreen();
      }
    },
    onPinch: (scale) => {
      if (enableZoom) {
        const newZoom = Math.max(0.5, Math.min(3, zoomLevel * scale));
        setZoomLevel(newZoom);
        onZoomChange?.(newZoom);
      }
    },
    onPan: (delta) => {
      if (enablePan) {
        setPanOffset(prev => ({
          x: prev.x + delta.x,
          y: prev.y + delta.y,
        }));
      }
    },
    onTap: (point) => {
      // Handle tap on chart elements
      if (chartRef.current) {
        const rect = chartRef.current.getBoundingClientRect();
        const x = point.x - rect.left;
        const y = point.y - rect.top;

        // This is a simplified version - in production, you'd want to
        // properly calculate which data point was tapped
        const dataIndex = Math.floor((x / rect.width) * data.length);
        if (dataIndex >= 0 && dataIndex < data.length) {
          const selectedDataPoint = data[dataIndex];
          setSelectedPoint(selectedDataPoint);
          onDataPointClick?.(selectedDataPoint, dataIndex);
          setShowTooltip(true);

          // Auto-hide tooltip after 3 seconds
          setTimeout(() => setShowTooltip(false), 3000);
        }
      }
    },
  };

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    const newFullscreen = !isFullscreen;
    setIsFullscreen(newFullscreen);
    onFullscreenToggle?.(newFullscreen);

    // Enter/exit fullscreen API
    if (!isFullscreen && chartRef.current?.requestFullscreen) {
      chartRef.current.requestFullscreen();
    } else if (isFullscreen && document.exitFullscreen) {
      document.exitFullscreen();
    }
  }, [isFullscreen, onFullscreenToggle]);

  // Reset zoom and pan
  const resetView = useCallback(() => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
    onZoomChange?.(1);
  }, [onZoomChange]);

  // Download chart
  const downloadChart = useCallback(() => {
    if (!chartRef.current) return;

    // In production, you'd use html2canvas or similar library
    console.log('Downloading chart...');
    alert('圖表下載功能開發中...');
  }, []);

  // Share chart
  const shareChart = useCallback(async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: title || 'CBSC 策略圖表',
          text: subtitle || '查看我的策略表現',
          url: window.location.href,
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      // Fallback - copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('連結已複製到剪貼板');
    }
  }, [title, subtitle]);

  // Render chart based on type
  const renderChart = () => {
    const chartData = simplified && data.length > 10 ? getSimplifiedData(data) : data;

    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 5, bottom: 5, left: 5 },
    };

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: 'none',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={colors[0]}
              fill={colors[0]}
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: 'none',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            />
            <Bar dataKey="value" fill={colors[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => entry.name}
              outerRadius={80}
              fill={colors[0]}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                fontSize: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: 'none',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            />
          </PieChart>
        );

      default: // line
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: textColor }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: 'none',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={colors[0]}
              strokeWidth={2}
              dot={{ r: 3, fill: colors[0] }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        );
    }
  };

  return (
    <div
      ref={chartRef}
      className={clsx(
        'relative bg-white rounded-lg shadow-sm',
        isFullscreen && 'fixed inset-0 z-50 bg-gray-900 bg-opacity-95',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 truncate">{subtitle}</p>
            )}
          </div>

          {/* Trend indicator */}
          {trend && (
            <div className={clsx(
              'flex items-center gap-1 px-2 py-1 rounded-full text-sm',
              trend.direction === 'up' && 'bg-green-100 text-green-700',
              trend.direction === 'down' && 'bg-red-100 text-red-700',
              trend.direction === 'neutral' && 'bg-gray-100 text-gray-700'
            )}>
              {trend.direction === 'up' && <TrendingUp className="w-4 h-4" />}
              {trend.direction === 'down' && <TrendingDown className="w-4 h-4" />}
              {trend.direction === 'neutral' && <Minus className="w-4 h-4" />}
              {trend.percentage.toFixed(1)}%
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center gap-1 ml-2">
            {enableFullscreen && (
              <button
                onClick={toggleFullscreen}
                className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200"
                aria-label={isFullscreen ? "退出全屏" : "全屏"}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}
            <button
              onClick={resetView}
              className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200"
              aria-label="重置視圖"
            >
              <RotateCw className="w-4 h-4" />
            </button>
            <button
              onClick={downloadChart}
              className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200"
              aria-label="下載"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={shareChart}
              className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200"
              aria-label="分享"
            >
              <Share2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Min/Max indicators */}
        {showMinMax && !simplified && (
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>最低: {getValueRange().min.toFixed(2)}</span>
            <span>最高: {getValueRange().max.toFixed(2)}</span>
          </div>
        )}
      </div>

      {/* Chart content */}
      <div
        className="relative overflow-hidden"
        style={{
          height: isFullscreen ? 'calc(100vh - 120px)' : height,
          width: width || '100%',
        }}
      >
        {enableGestures ? (
          <GestureRecognizer
            callbacks={gestureCallbacks}
            config={{
              swipeThreshold: 30,
              swipeVelocityThreshold: 300,
              pinchThreshold: 10,
            }}
          >
            <ResponsiveContainer width="100%" height="100%">
              {renderChart()}
            </ResponsiveContainer>
          </GestureRecognizer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        )}

        {/* Zoom indicator */}
        {zoomLevel !== 1 && (
          <div className="absolute top-2 left-2 px-2 py-1 bg-black bg-opacity-50 text-white text-xs rounded">
            縮放: {(zoomLevel * 100).toFixed(0)}%
          </div>
        )}
      </div>

      {/* Custom tooltip */}
      <AnimatePresence>
        {showTooltip && selectedPoint && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg p-3 z-10"
          >
            <div className="font-medium text-gray-900">{selectedPoint.name}</div>
            <div className="text-2xl font-bold text-blue-600">
              {selectedPoint.value.toFixed(2)}
            </div>
            {selectedPoint.timestamp && (
              <div className="text-xs text-gray-500">
                {new Date(selectedPoint.timestamp).toLocaleString('zh-TW')}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Simplified mode indicator */}
      {simplified && (
        <div className="absolute top-2 right-2 px-2 py-1 bg-blue-500 text-white text-xs rounded">
          簡化模式
        </div>
      )}
    </div>
  );
};

export default MobileOptimizedChart;