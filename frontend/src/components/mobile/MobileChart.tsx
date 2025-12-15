import React, { useRef, useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import { usePinchToZoom } from '../../hooks/useSwipeGesture';
import { clsx } from 'clsx';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement);

interface MobileChartProps {
  type: 'line' | 'bar' | 'pie' | 'doughnut';
  data: any;
  options?: any;
  className?: string;
  height?: number;
  width?: number;
  zoomable?: boolean;
  onZoom?: (scale: number) => void;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
}

/**
 * MobileChart - Mobile-friendly chart component with zoom support
 */
const MobileChart: React.FC<MobileChartProps> = ({
  type,
  data,
  options,
  className,
  height = 300,
  width,
  zoomable = true,
  onZoom,
  responsive = true,
  maintainAspectRatio = false,
}) => {
  const [scale, setScale] = useState(1);
  const [isInteracting, setIsInteracting] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [chartRef, setChartRef] = usePinchToZoom({
    minScale: 0.5,
    maxScale: 3,
    onZoomChange: (newScale) => {
      setScale(newScale);
      onZoom?.(newScale);
    },
  });

  // Default mobile-friendly options
  const defaultOptions = {
    responsive,
    maintainAspectRatio,
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
    plugins: {
      legend: {
        display: type === 'pie' || type === 'doughnut',
        position: 'bottom' as const,
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 12,
        },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
      },
    },
    scales: type === 'pie' || type === 'doughnut' ? {} : {
      x: {
        ticks: {
          font: {
            size: 11,
          },
          maxRotation: 45,
          minRotation: 0,
        },
        grid: {
          display: true,
          drawBorder: false,
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      y: {
        ticks: {
          font: {
            size: 11,
          },
        },
        grid: {
          display: true,
          drawBorder: false,
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart' as const,
    },
    elements: {
      point: {
        radius: 4,
        hitRadius: 10,
        hoverRadius: 6,
      },
      line: {
        borderWidth: 2,
        tension: 0.4,
      },
      bar: {
        borderWidth: 0,
      },
    },
  };

  // Merge custom options
  const chartOptions = {
    ...defaultOptions,
    ...options,
    plugins: {
      ...defaultOptions.plugins,
      ...(options?.plugins || {}),
    },
    scales: type === 'pie' || type === 'doughnut' ? {} : {
      ...defaultOptions.scales,
      ...(options?.scales || {}),
    },
  };

  // Handle touch interactions
  const handleTouchStart = () => {
    setIsInteracting(true);
  };

  const handleTouchEnd = () => {
    setIsInteracting(false);
  };

  // Chart components
  const renderChart = () => {
    const commonProps = {
      data,
      options: chartOptions,
      ref: (ref: any) => {
        setChartRef(ref?.chart?.canvas);
        if (options?.ref) {
          options.ref(ref);
        }
      },
    };

    switch (type) {
      case 'line':
        return <Line {...commonProps} />;
      case 'bar':
        return <Bar {...commonProps} />;
      case 'pie':
        return <Pie {...commonProps} />;
      case 'doughnut':
        return <Doughnut {...commonProps} />;
      default:
        return <Line {...commonProps} />;
    }
  };

  return (
    <div
      ref={containerRef}
      className={clsx(
        'relative w-full',
        isInteracting && 'cursor-grabbing',
        zoomable && 'touch-pan-y',
        className
      )}
      style={{
        height: typeof height === 'number' ? `${height}px` : height,
        width,
        transform: zoomable ? `scale(${scale})` : 'none',
        transformOrigin: 'center center',
        transition: isInteracting ? 'none' : 'transform 0.3s ease-out',
      }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {renderChart()}

      {/* Zoom indicator */}
      {zoomable && scale !== 1 && (
        <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
          {Math.round(scale * 100)}%
        </div>
      )}

      {/* Touch hint */}
      {zoomable && !isInteracting && (
        <div className="absolute bottom-2 left-2 text-xs text-gray-500">
          {scale === 1 && '捏合縮放'}
        </div>
      )}
    </div>
  );
};

export default MobileChart;

/**
 * Simple mobile chart card wrapper
 */
interface MobileChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}

export const MobileChartCard: React.FC<MobileChartCardProps> = ({
  title,
  subtitle,
  children,
  className,
  actions,
}) => {
  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 p-4', className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 ml-4">
            {actions}
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="w-full">
        {children}
      </div>
    </div>
  );
};