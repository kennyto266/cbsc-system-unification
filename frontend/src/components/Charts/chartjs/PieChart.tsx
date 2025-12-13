import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { ChartContainer } from '../common/ChartContainer';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend
);

// Data point interface
interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

// Props interface
interface PieChartProps {
  title?: string;
  subtitle?: string;
  data: DataPoint[];
  height?: number;
  className?: string;
  showLegend?: boolean;
  showTooltip?: boolean;
  animation?: boolean;
  theme?: 'light' | 'dark';
  onDataPointClick?: (pointIndex: number, value: DataPoint) => void;
  centerText?: {
    text: string;
    subtext?: string;
  };
  colors?: string[];
}

export const PieChart: React.FC<PieChartProps> = ({
  title,
  subtitle,
  data,
  height = 400,
  className = '',
  showLegend = true,
  showTooltip = true,
  animation = true,
  theme = 'light',
  onDataPointClick,
  centerText,
  colors
}) => {
  // Default color palette
  const defaultColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
    '#06b6d4', '#a855f7', '#f43f5e', '#22c55e', '#0ea5e9'
  ];

  // Generate chart data
  const chartData = useMemo(() => {
    const labels = data.map(d => d.label);
    const values = data.map(d => d.value);
    const backgroundColor = data.map((d, index) =>
      d.color || colors?.[index] || defaultColors[index % defaultColors.length]
    );

    return {
      labels,
      datasets: [{
        data: values,
        backgroundColor,
        borderColor: theme === 'dark' ? '#1f2937' : '#ffffff',
        borderWidth: 2,
        hoverOffset: 4
      }]
    };
  }, [data, colors, theme]);

  // Chart options
  const options = useMemo(() => {
    const isDark = theme === 'dark';
    const textColor = isDark ? '#e5e7eb' : '#374151';

    // Calculate total for percentage display
    const total = data.reduce((sum, d) => sum + d.value, 0);

    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: animation ? {
        animateRotate: true,
        animateScale: false,
        duration: 750,
        easing: 'easeInOutQuart'
      } : false,
      plugins: {
        legend: {
          display: showLegend,
          position: 'right' as const,
          labels: {
            color: textColor,
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12,
              weight: '500'
            },
            generateLabels: function(chart: any) {
              const data = chart.data;
              if (data.labels.length && data.datasets.length) {
                const dataset = data.datasets[0];
                const total = dataset.data.reduce((a: number, b: number) => a + b, 0);
                return data.labels.map((label: string, i: number) => {
                  const value = dataset.data[i];
                  const percentage = ((value / total) * 100).toFixed(1);
                  return {
                    text: `${label} (${percentage}%)`,
                    fillStyle: dataset.backgroundColor[i],
                    hidden: false,
                    index: i
                  };
                });
              }
              return [];
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
              const label = context.label || '';
              const value = context.parsed;
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: ${new Intl.NumberFormat('zh-CN', {
                style: 'decimal',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              }).format(value)} (${percentage}%)`;
            }
          }
        },
        // Center text plugin
        ...(centerText && {
          datalabels: {
            display: false
          },
          beforeDraw: function(chart: any) {
            const ctx = chart.ctx;
            const width = chart.width;
            const height = chart.height;

            ctx.restore();
            const fontSize = (height / 114).toFixed(2);
            ctx.font = `${fontSize * 2}em sans-serif`;
            ctx.textBaseline = 'middle';
            ctx.fillStyle = textColor;

            const text = centerText.text;
            const textX = Math.round((width - ctx.measureText(text).width) / 2);
            const textY = height / 2 - 20;

            ctx.fillText(text, textX, textY);

            if (centerText.subtext) {
              ctx.font = `${fontSize}em sans-serif`;
              const subtext = centerText.subtext;
              const subtextX = Math.round((width - ctx.measureText(subtext).width) / 2);
              const subtextY = height / 2 + 10;
              ctx.fillText(subtext, subtextX, subtextY);
            }

            ctx.save();
          }
        })
      },
      onClick: (event: any, elements: any[]) => {
        if (onDataPointClick && elements.length > 0) {
          const { index } = elements[0];
          const point = data[index];
          onDataPointClick(index, point);
        }
      }
    };
  }, [theme, showLegend, showTooltip, animation, centerText, data, onDataPointClick]);

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      className={className}
    >
      <div style={{ height }}>
        <Pie data={chartData} options={options} />
      </div>
    </ChartContainer>
  );
};