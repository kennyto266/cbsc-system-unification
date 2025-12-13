import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { ChartContainer } from '../common/ChartContainer';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
);

// Data point interface
interface DataPoint {
  x: number | string | Date;
  y: number;
  label?: string;
}

// Dataset interface
interface Dataset {
  label: string;
  data: DataPoint[];
  borderColor?: string;
  backgroundColor?: string;
  borderWidth?: number;
  tension?: number;
  fill?: boolean;
  pointRadius?: number;
  pointHoverRadius?: number;
  yAxisID?: string;
}

// Props interface
interface LineChartProps {
  title?: string;
  subtitle?: string;
  datasets: Dataset[];
  height?: number;
  className?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  animation?: boolean;
  theme?: 'light' | 'dark';
  timeAxis?: boolean;
  onDataPointClick?: (datasetIndex: number, pointIndex: number, value: DataPoint) => void;
  yAxisConfig?: {
    left?: {
      label?: string;
      min?: number;
      max?: number;
      ticks?: {
        callback?: (value: number) => string;
      };
    };
    right?: {
      label?: string;
      min?: number;
      max?: number;
      ticks?: {
        callback?: (value: number) => string;
      };
    };
  };
}

export const LineChart: React.FC<LineChartProps> = ({
  title,
  subtitle,
  datasets,
  height = 400,
  className = '',
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  animation = true,
  theme = 'light',
  timeAxis = false,
  onDataPointClick,
  yAxisConfig
}) => {
  // Generate chart data
  const chartData = useMemo(() => {
    // Get all unique x values
    const allXValues = new Set<string | number>();
    datasets.forEach(dataset => {
      dataset.data.forEach(point => {
        if (timeAxis && point.x instanceof Date) {
          allXValues.add(point.x.toISOString());
        } else {
          allXValues.add(String(point.x));
        }
      });
    });

    const labels = Array.from(allXValues).sort();

    // Transform datasets for Chart.js
    const chartDatasets = datasets.map((dataset, datasetIndex) => ({
      label: dataset.label,
      data: dataset.data.map(point => ({
        x: timeAxis && point.x instanceof Date ? point.x.toISOString() : point.x,
        y: point.y
      })),
      borderColor: dataset.borderColor || theme === 'dark' ? '#60a5fa' : '#3b82f6',
      backgroundColor: dataset.backgroundColor || (theme === 'dark' ? 'rgba(96, 165, 250, 0.1)' : 'rgba(59, 130, 246, 0.1)'),
      borderWidth: dataset.borderWidth || 2,
      tension: dataset.tension ?? 0.4,
      fill: dataset.fill ?? false,
      pointRadius: dataset.pointRadius ?? 3,
      pointHoverRadius: dataset.pointHoverRadius ?? 5,
      yAxisID: dataset.yAxisID || 'y'
    }));

    return {
      labels,
      datasets: chartDatasets
    };
  }, [datasets, theme, timeAxis]);

  // Chart options
  const options = useMemo(() => {
    const isDark = theme === 'dark';
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#f3f4f6';

    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: animation ? {
        duration: 750,
        easing: 'easeInOutQuart'
      } : false,
      interaction: {
        mode: 'index' as const,
        intersect: false
      },
      plugins: {
        legend: {
          display: showLegend,
          position: 'top' as const,
          labels: {
            color: textColor,
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12,
              weight: '500'
            }
          }
        },
        tooltip: {
          enabled: showTooltip,
          backgroundColor: isDark ? '#1f2937' : '#ffffff',
          titleColor: textColor,
          bodyColor: textColor,
          borderColor: isDark ? '#4b5563' : '#e5e7eb',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            title: function(context) {
              if (timeAxis) {
                const date = new Date(context[0].label);
                return format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
              }
              return context[0].label;
            },
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
          type: timeAxis ? 'time' : 'category',
          time: timeAxis ? {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MM-dd',
              month: 'yyyy-MM'
            }
          } : undefined,
          grid: {
            display: showGrid,
            color: gridColor,
            drawBorder: false
          },
          ticks: {
            color: textColor,
            maxRotation: 45,
            minRotation: 0
          }
        },
        y: {
          type: 'linear' as const,
          display: true,
          position: 'left' as const,
          title: {
            display: !!yAxisConfig?.left?.label,
            text: yAxisConfig?.left?.label,
            color: textColor
          },
          min: yAxisConfig?.left?.min,
          max: yAxisConfig?.left?.max,
          grid: {
            display: showGrid,
            color: gridColor,
            drawBorder: false
          },
          ticks: {
            color: textColor,
            callback: yAxisConfig?.left?.ticks?.callback || function(value) {
              return new Intl.NumberFormat('zh-CN').format(value);
            }
          }
        },
        ...(yAxisConfig?.right && {
          y1: {
            type: 'linear' as const,
            display: true,
            position: 'right' as const,
            title: {
              display: !!yAxisConfig.right.label,
              text: yAxisConfig.right.label,
              color: textColor
            },
            min: yAxisConfig.right.min,
            max: yAxisConfig.right.max,
            grid: {
              drawOnChartArea: false
            },
            ticks: {
              color: textColor,
              callback: yAxisConfig.right.ticks?.callback || function(value) {
                return new Intl.NumberFormat('zh-CN').format(value);
              }
            }
          }
        })
      },
      onClick: (event: any, elements: any[]) => {
        if (onDataPointClick && elements.length > 0) {
          const { datasetIndex, index } = elements[0];
          const dataset = datasets[datasetIndex];
          const point = dataset.data[index];
          onDataPointClick(datasetIndex, index, point);
        }
      }
    };
  }, [theme, showLegend, showTooltip, showGrid, animation, timeAxis, yAxisConfig, datasets, onDataPointClick]);

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      className={className}
    >
      <div style={{ height }}>
        <Line data={chartData} options={options} />
      </div>
    </ChartContainer>
  );
};