import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { ChartContainer } from '../common/ChartContainer';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Data point interface
interface DataPoint {
  label: string;
  value: number;
  backgroundColor?: string;
  borderColor?: string;
}

// Dataset interface
interface Dataset {
  label: string;
  data: DataPoint[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  barPercentage?: number;
  categoryPercentage?: number;
}

// Props interface
interface BarChartProps {
  title?: string;
  subtitle?: string;
  datasets: Dataset[];
  height?: number;
  className?: string;
  horizontal?: boolean;
  stacked?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  animation?: boolean;
  theme?: 'light' | 'dark';
  onDataPointClick?: (datasetIndex: number, pointIndex: number, value: DataPoint) => void;
  yAxisConfig?: {
    label?: string;
    min?: number;
    max?: number;
    ticks?: {
      callback?: (value: number) => string;
    };
  };
  xAxisConfig?: {
    label?: string;
    ticks?: {
      callback?: (value: string) => string;
    };
  };
}

export const BarChart: React.FC<BarChartProps> = ({
  title,
  subtitle,
  datasets,
  height = 400,
  className = '',
  horizontal = false,
  stacked = false,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  animation = true,
  theme = 'light',
  onDataPointClick,
  yAxisConfig,
  xAxisConfig
}) => {
  // Generate chart data
  const chartData = useMemo(() => {
    // Get all unique labels
    const allLabels = new Set<string>();
    datasets.forEach(dataset => {
      dataset.data.forEach(point => {
        allLabels.add(point.label);
      });
    });

    const labels = Array.from(allLabels);

    // Transform datasets for Chart.js
    const chartDatasets = datasets.map((dataset, datasetIndex) => ({
      label: dataset.label,
      data: labels.map(label => {
        const point = dataset.data.find(p => p.label === label);
        return point ? point.value : 0;
      }),
      backgroundColor: dataset.backgroundColor || (theme === 'dark' ? '#60a5fa' : '#3b82f6'),
      borderColor: dataset.borderColor || (theme === 'dark' ? '#3b82f6' : '#1d4ed8'),
      borderWidth: dataset.borderWidth ?? 1,
      barPercentage: dataset.barPercentage ?? 0.8,
      categoryPercentage: dataset.categoryPercentage ?? 0.9
    }));

    return {
      labels,
      datasets: chartDatasets
    };
  }, [datasets, theme]);

  // Chart options
  const options = useMemo(() => {
    const isDark = theme === 'dark';
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#f3f4f6';

    return {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: horizontal ? 'y' as const : 'x' as const,
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
          stacked,
          grid: {
            display: showGrid,
            color: gridColor,
            drawBorder: false
          },
          ticks: {
            color: textColor,
            callback: xAxisConfig?.ticks?.callback
          },
          title: {
            display: !!xAxisConfig?.label,
            text: xAxisConfig?.label,
            color: textColor
          }
        },
        y: {
          stacked,
          title: {
            display: !!yAxisConfig?.label,
            text: yAxisConfig?.label,
            color: textColor
          },
          min: yAxisConfig?.min,
          max: yAxisConfig?.max,
          grid: {
            display: showGrid,
            color: gridColor,
            drawBorder: false
          },
          ticks: {
            color: textColor,
            callback: yAxisConfig?.ticks?.callback || function(value) {
              return new Intl.NumberFormat('zh-CN').format(value);
            }
          }
        }
      },
      onClick: (event: any, elements: any[]) => {
        if (onDataPointClick && elements.length > 0) {
          const { datasetIndex, index } = elements[0];
          const label = chartData.labels[index];
          const dataset = datasets[datasetIndex];
          const point = dataset.data.find(p => p.label === label);
          if (point) {
            onDataPointClick(datasetIndex, index, point);
          }
        }
      }
    };
  }, [
    theme,
    horizontal,
    stacked,
    showLegend,
    showTooltip,
    showGrid,
    animation,
    yAxisConfig,
    xAxisConfig,
    datasets,
    chartData,
    onDataPointClick
  ]);

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      className={className}
    >
      <div style={{ height }}>
        <Bar data={chartData} options={options} />
      </div>
    </ChartContainer>
  );
};