import React, { forwardRef, useEffect, useRef } from 'react';
import { Chart as ChartJS, ChartConfiguration, ChartOptions } from 'chart.js';
import { motion } from 'framer-motion';

// Base chart component wrapper for all chart types
interface BaseChartProps {
  type: ChartJS['config']['type'];
  data: ChartJS['config']['data'];
  options?: ChartJS['config']['options'];
  className?: string;
  width?: number;
  height?: number;
  onDataPointClick?: (event: any, elements: any[]) => void;
  animation?: boolean;
  theme?: 'light' | 'dark';
}

// Forward ref to allow direct chart access
const BaseChart = forwardRef<HTMLCanvasElement, BaseChartProps>(({
  type,
  data,
  options = {},
  className = '',
  width,
  height,
  onDataPointClick,
  animation = true,
  theme = 'light'
}, ref) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  // Merge refs
  const setRefs = (element: HTMLCanvasElement) => {
    canvasRef.current = element;
    if (typeof ref === 'function') {
      ref(element);
    } else if (ref) {
      ref.current = element;
    }
  };

  useEffect(() => {
    if (!canvasRef.current) return;

    // Destroy existing chart
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    // Default options based on theme
    const defaultOptions: ChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      animation: animation ? {
        duration: 750,
        easing: 'easeInOutQuart'
      } : false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: theme === 'dark' ? '#e5e7eb' : '#374151',
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12,
              weight: '500'
            }
          }
        },
        tooltip: {
          enabled: true,
          backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
          titleColor: theme === 'dark' ? '#e5e7eb' : '#111827',
          bodyColor: theme === 'dark' ? '#e5e7eb' : '#374151',
          borderColor: theme === 'dark' ? '#4b5563' : '#e5e7eb',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += new Intl.NumberFormat('zh-CN', {
                  style: 'decimal',
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                }).format(context.parsed.y);
              }
              return label;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: true,
            color: theme === 'dark' ? '#374151' : '#f3f4f6',
            drawBorder: false
          },
          ticks: {
            color: theme === 'dark' ? '#9ca3af' : '#6b7280'
          }
        },
        y: {
          grid: {
            display: true,
            color: theme === 'dark' ? '#374151' : '#f3f4f6',
            drawBorder: false
          },
          ticks: {
            color: theme === 'dark' ? '#9ca3af' : '#6b7280',
            callback: function(value) {
              return new Intl.NumberFormat('zh-CN', {
                style: 'decimal',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
              }).format(value);
            }
          }
        }
      },
      onClick: (event, elements) => {
        if (onDataPointClick && elements.length > 0) {
          onDataPointClick(event, elements);
        }
      }
    };

    // Merge with custom options
    const mergedOptions = {
      ...defaultOptions,
      ...options,
      plugins: {
        ...defaultOptions.plugins,
        ...(options.plugins || {})
      }
    };

    // Create new chart
    const config: ChartConfiguration = {
      type,
      data,
      options: mergedOptions
    };

    chartRef.current = new ChartJS(canvasRef.current, config);

    // Cleanup
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [type, data, options, animation, theme, onDataPointClick]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`relative ${className}`}
      style={{ width, height }}
    >
      <canvas ref={setRefs} />
    </motion.div>
  );
});

BaseChart.displayName = 'BaseChart';

export default BaseChart;