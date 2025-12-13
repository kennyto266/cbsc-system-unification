import React, { useRef, useEffect, useState } from 'react';
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
import { chartTheme, getSharpeRatioColor } from './ChartTheme';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Define strategy data interface
interface StrategyData {
  id: string;
  name: string;
  sharpeRatio: number;
  performance?: {
    sharpeRatio: number;
    totalReturn?: number;
    maxDrawdown?: number;
  };
}

interface SharpeRatioChartProps {
  strategies: StrategyData[];
  height?: number;
  showTitle?: boolean;
  interactive?: boolean;
  onBarClick?: (strategy: StrategyData) => void;
}

export const SharpeRatioChart: React.FC<SharpeRatioChartProps> = ({
  strategies,
  height = 300,
  showTitle = true,
  interactive = true,
  onBarClick
}) => {
  const chartRef = useRef<ChartJS<'bar'>>(null);
  const [selectedBar, setSelectedBar] = useState<string | null>(null);

  // Sort strategies by Sharpe ratio (descending)
  const sortedStrategies = [...strategies]
    .filter(s => s.performance?.sharpeRatio !== undefined && s.performance.sharpeRatio !== null)
    .sort((a, b) => (b.performance?.sharpeRatio || 0) - (a.performance?.sharpeRatio || 0))
    .slice(0, 10); // Top 10 strategies

  // Prepare chart data
  const chartData = {
    labels: sortedStrategies.map(s => s.name.length > 15 ? s.name.substring(0, 15) + '...' : s.name),
    datasets: [
      {
        label: 'Sharpe比率',
        data: sortedStrategies.map(s => s.performance?.sharpeRatio || 0),
        backgroundColor: sortedStrategies.map(s =>
          selectedBar === s.id ? '#2c3e50' : getSharpeRatioColor(s.performance?.sharpeRatio || 0)
        ),
        borderColor: sortedStrategies.map(s =>
          selectedBar === s.id ? '#1a1a1a' : 'rgba(0, 0, 0, 0.1)'
        ),
        borderWidth: selectedBar ? 2 : 1,
        borderRadius: 4,
        borderSkipped: false as const,
      }
    ]
  };

  // Chart options
  const options = {
    ...chartTheme.defaultOptions,
    plugins: {
      ...chartTheme.defaultOptions.plugins,
      title: {
        display: showTitle,
        text: '策略Sharpe比率排名 (Top 10)',
        font: {
          family: chartTheme.defaultOptions.plugins.legend.labels.font.family,
          size: 16,
          weight: 'bold' as const
        },
        color: '#2c3e50',
        padding: {
          top: 10,
          bottom: 30
        }
      },
      tooltip: {
        ...chartTheme.defaultOptions.plugins.tooltip,
        callbacks: {
          title: (context: any) => {
            const index = context[0].dataIndex;
            return sortedStrategies[index]?.name || '未知策略';
          },
          label: (context: any) => {
            const value = context.parsed.y;
            const strategy = sortedStrategies[context.dataIndex];
            const labels = [
              `Sharpe比率: ${value.toFixed(2)}`,
              strategy?.performance?.totalReturn ? `總回報: ${(strategy.performance.totalReturn * 100).toFixed(1)}%` : '',
              '≥ 1.5: 優秀 | 1.0-1.5: 良好 | 0.5-1.0: 一般 | < 0.5: 較差'
            ].filter(Boolean);
            return labels;
          }
        }
      }
    },
    scales: {
      x: {
        ...chartTheme.defaultOptions.scales.x,
        ticks: {
          ...chartTheme.defaultOptions.scales.x.ticks,
          maxRotation: 45,
          minRotation: 0
        }
      },
      y: {
        ...chartTheme.defaultOptions.scales.y,
        beginAtZero: true,
        title: {
          display: true,
          text: 'Sharpe比率',
          font: {
            family: chartTheme.defaultOptions.plugins.legend.labels.font.family,
            size: 13,
            weight: 'bold' as const
          },
          color: '#2c3e50'
        },
        suggestedMin: 0,
        suggestedMax: Math.max(...sortedStrategies.map(s => s.performance?.sharpeRatio || 0)) * 1.1 || 2
      }
    },
    onClick: interactive ? (event: any, elements: any[]) => {
      if (elements.length > 0 && onBarClick) {
        const index = elements[0].index;
        const strategy = sortedStrategies[index];
        if (strategy) {
          setSelectedBar(strategy.id);
          onBarClick(strategy);

          // Reset selection after 2 seconds
          setTimeout(() => setSelectedBar(null), 2000);
        }
      }
    } : undefined,
    onHover: interactive ? (event: any, elements: any[]) => {
      const canvas = chartRef.current?.canvas;
      if (canvas) {
        canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
      }
    } : undefined
  };

  // Update chart when data changes
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.update('none');
    }
  }, [strategies]);

  if (sortedStrategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-gray-500 text-sm">沒有可用的Sharpe比率數據</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div style={{ height: `${height}px` }}>
        <Bar ref={chartRef} data={chartData} options={options} />
      </div>

      {/* Chart Legend */}
      <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.success }}></div>
          <span className="text-gray-600">優秀 (≥1.5)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.primary }}></div>
          <span className="text-gray-600">良好 (1.0-1.5)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.warning }}></div>
          <span className="text-gray-600">一般 (0.5-1.0)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.danger }}></div>
          <span className="text-gray-600">較差 (&lt;0.5)</span>
        </div>
      </div>
    </div>
  );
};

export default SharpeRatioChart;