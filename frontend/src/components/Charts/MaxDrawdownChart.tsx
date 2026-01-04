import React, { useRef, useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { chartTheme, getDrawdownColor, getStrategyColor } from './ChartTheme';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Define historical data interface
interface HistoricalData {
  date: string;
  drawdown: number;
}

interface StrategyData {
  id: string;
  name: string;
  type: string;
  historicalData?: HistoricalData[];
  performance?: {
    maxDrawdown: number;
  };
}

interface MaxDrawdownChartProps {
  strategies: StrategyData[];
  height?: number;
  showTitle?: boolean;
  showFill?: boolean;
  interactive?: boolean;
  timeRange?: '7d' | '30d' | '90d' | '180d';
  onStrategyClick?: (strategy: StrategyData) => void;
}

export const MaxDrawdownChart: React.FC<MaxDrawdownChartProps> = ({
  strategies,
  height = 350,
  showTitle = true,
  showFill = true,
  interactive = true,
  timeRange = '30d',
  onStrategyClick
}) => {
  const chartRef = useRef<ChartJS<'line'>>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

  // Generate mock historical data if not provided
  const generateHistoricalData = (strategy: StrategyData, days: number): HistoricalData[] => {
    const data: HistoricalData[] = [];
    const now = new Date();
    const baseDrawdown = strategy.performance?.maxDrawdown || 10;

    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Generate realistic drawdown pattern
      const randomFactor = 0.8 + Math.random() * 0.4; // 0.8 to 1.2
      const trendFactor = (days - i) / days; // Increasing trend over time
      const drawdown = Math.max(0, baseDrawdown * randomFactor * (1 - trendFactor * 0.3));

      data.push({
        date: date.toISOString().split('T')[0],
        drawdown: Math.round(drawdown * 100) / 100
      });
    }

    return data;
  };

  // Filter strategies with valid data
  const validStrategies = strategies
    .filter(s => {
      const hasData = s.historicalData && s.historicalData.length > 0;
      const hasPerformance = s.performance && s.performance.maxDrawdown !== undefined;
      return hasData || hasPerformance;
    })
    .slice(0, 6); // Limit to 6 strategies for better visibility

  // Get date range based on timeRange
  const getDaysFromRange = (range: string): number => {
    switch (range) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      case '180d': return 180;
      default: return 30;
    }
  };

  const days = getDaysFromRange(timeRange);

  // Prepare datasets for each strategy
  const datasets = validStrategies.map((strategy, index) => {
    const data = strategy.historicalData?.length
      ? strategy.historicalData.slice(-days)
      : generateHistoricalData(strategy, days);

    const strategyColor = getStrategyColor(strategy.type);
    const isSelected = selectedStrategy === strategy.id;

    return {
      label: strategy.name,
      data: data.map(d => d.drawdown),
      borderColor: isSelected ? '#2c3e50' : strategyColor,
      backgroundColor: isSelected
        ? 'rgba(44, 62, 80, 0.1)'
        : `${strategyColor}20`, // Add transparency
      borderWidth: isSelected ? 3 : 2,
      fill: showFill ? {
        target: 'origin' as const,
        above: isSelected
          ? 'rgba(44, 62, 80, 0.05)'
          : `${strategyColor}10` // Very light fill
      } : false,
      tension: 0.4,
      pointRadius: isSelected ? 5 : 3,
      pointHoverRadius: isSelected ? 7 : 5,
      pointBackgroundColor: isSelected ? '#2c3e50' : strategyColor,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: isSelected ? '#2c3e50' : strategyColor,
      pointHoverBorderWidth: 3,
      hidden: false
    };
  });

  // Get all unique dates from all strategies
  const allDates = new Set<string>();
  validStrategies.forEach(strategy => {
    const data = strategy.historicalData?.length
      ? strategy.historicalData.slice(-days)
      : generateHistoricalData(strategy, days);
    data.forEach(d => allDates.add(d.date));
  });

  const labels = Array.from(allDates).sort();

  // Chart data
  const chartData = {
    labels: labels.map(date => {
      const d = new Date(date);
      return d.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
    }),
    datasets: datasets
  };

  // Chart options
  const options = {
    ...chartTheme.defaultOptions,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      ...chartTheme.defaultOptions.plugins,
      title: {
        display: showTitle,
        text: `策略最大回撤趨勢 (${timeRange.toUpperCase()})`,
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
            const dateIndex = context[0].dataIndex;
            const date = Array.from(allDates).sort()[dateIndex];
            if (date) {
              const d = new Date(date);
              return d.toLocaleDateString('zh-TW', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              });
            }
            return '未知日期';
          },
          label: (context: any) => {
            const strategyName = context.dataset.label;
            const value = context.parsed.y;
            return `${strategyName}: ${value.toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        ...chartTheme.defaultOptions.scales.x,
        title: {
          display: true,
          text: '時間',
          font: {
            family: chartTheme.defaultOptions.plugins.legend.labels.font.family,
            size: 13,
            weight: 'bold' as const
          },
          color: '#2c3e50'
        }
      },
      y: {
        ...chartTheme.defaultOptions.scales.y,
        beginAtZero: true,
        max: 30, // Max 30% drawdown
        title: {
          display: true,
          text: '最大回撤 (%)',
          font: {
            family: chartTheme.defaultOptions.plugins.legend.labels.font.family,
            size: 13,
            weight: 'bold' as const
          },
          color: '#2c3e50'
        },
        ticks: {
          ...chartTheme.defaultOptions.scales.y.ticks,
          callback: (value: any) => `${value}%`
        }
      }
    },
    onClick: interactive ? (event: any, elements: any[]) => {
      if (elements.length > 0 && onStrategyClick) {
        const datasetIndex = elements[0].datasetIndex;
        const strategy = validStrategies[datasetIndex];
        if (strategy) {
          setSelectedStrategy(strategy.id === selectedStrategy ? null : strategy.id);
          onStrategyClick(strategy);
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

  // Update chart when data or selection changes
  useEffect(() => {
    const chart = chartRef.current;
    if (chart && typeof chart.update === 'function') {
      chart.update('none');
    }
  }, [strategies, selectedStrategy, timeRange]);

  if (validStrategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
          </div>
          <p className="text-gray-500 text-sm">沒有可用的回撤數據</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Time Range Selector */}
      {interactive && (
        <div className="mb-4 flex justify-center gap-2">
          {(['7d', '30d', '90d', '180d'] as const).map(range => (
            <button
              key={range}
              onClick={() => {
                // Note: This would typically update parent state
                // For now, it's just visual feedback
                console.log(`Time range changed to: ${range}`);
              }}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {range === '7d' ? '7天' :
               range === '30d' ? '30天' :
               range === '90d' ? '90天' : '180天'}
            </button>
          ))}
        </div>
      )}

      <div style={{ height: `${height}px` }}>
        <Line ref={chartRef} data={chartData} options={options} />
      </div>

      {/* Risk Level Legend */}
      <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.success }}></div>
          <span className="text-gray-600">低風險 (≤5%)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.warning }}></div>
          <span className="text-gray-600">中風險 (5-10%)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartTheme.danger }}></div>
          <span className="text-gray-600">高風險 (&gt;10%)</span>
        </div>
      </div>
    </div>
  );
};

export default MaxDrawdownChart;