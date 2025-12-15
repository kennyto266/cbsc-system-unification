import React, { useRef, useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { chartTheme, getStrategyColor } from './ChartTheme';

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
);

// Define strategy performance metrics
interface StrategyMetrics {
  id: string;
  name: string;
  type: string;
  performance?: {
    sharpeRatio: number;
    maxDrawdown: number;
    volatility: number;
    winRate: number;
    profitFactor: number;
    calmarRatio: number;
    totalReturn: number;
  };
}

interface StrategyRadarChartProps {
  strategies: StrategyMetrics[];
  height?: number;
  showTitle?: boolean;
  maxStrategies?: number;
  interactive?: boolean;
  onStrategySelect?: (strategy: StrategyMetrics) => void;
}

export const StrategyRadarChart: React.FC<StrategyRadarChartProps> = ({
  strategies,
  height = 400,
  showTitle = true,
  maxStrategies = 4,
  interactive = true,
  onStrategySelect
}) => {
  const chartRef = useRef<ChartJS<'radar'>>(null);
  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set());

  // Normalize metrics to 0-100 scale for radar chart
  const normalizeMetric = (value: number, metricType: string): number => {
    switch (metricType) {
      case 'sharpeRatio':
        // Sharpe ratio: 0-3 mapped to 0-100
        return Math.min(100, Math.max(0, (value / 3) * 100));

      case 'maxDrawdown':
        // Max drawdown: lower is better, 0-30% mapped to 100-0
        return Math.max(0, 100 - (value / 30) * 100);

      case 'volatility':
        // Volatility: 0-30% mapped to 0-100 (lower is generally better, but some volatility is good)
        return value <= 15 ? (value / 15) * 80 : 80 - ((value - 15) / 15) * 20;

      case 'winRate':
        // Win rate: 0-100% mapped to 0-100
        return Math.min(100, Math.max(0, value));

      case 'profitFactor':
        // Profit factor: 1-3 mapped to 0-100
        return Math.min(100, Math.max(0, ((value - 1) / 2) * 100));

      case 'calmarRatio':
        // Calmar ratio: 0-3 mapped to 0-100
        return Math.min(100, Math.max(0, (value / 3) * 100));

      case 'totalReturn':
        // Total return: -50% to 100% mapped to 0-100
        if (value < 0) return Math.max(0, 50 + value);
        return Math.min(100, 50 + (value / 2));

      default:
        return 50; // Default to middle value
    }
  };

  // Filter strategies with valid performance data
  const validStrategies = strategies
    .filter(s => s.performance && Object.keys(s.performance).length > 0)
    .slice(0, maxStrategies);

  // Calculate comprehensive score for sorting
  const calculateScore = (strategy: StrategyMetrics): number => {
    if (!strategy.performance) return 0;

    const { sharpeRatio, maxDrawdown, volatility, winRate, profitFactor, calmarRatio } = strategy.performance;

    // Weighted score calculation
    const score =
      (normalizeMetric(sharpeRatio, 'sharpeRatio') * 0.25) +
      (normalizeMetric(maxDrawdown, 'maxDrawdown') * 0.20) +
      (normalizeMetric(volatility, 'volatility') * 0.15) +
      (normalizeMetric(winRate, 'winRate') * 0.20) +
      (normalizeMetric(profitFactor, 'profitFactor') * 0.10) +
      (normalizeMetric(calmarRatio, 'calmarRatio') * 0.10);

    return score;
  };

  // Sort strategies by comprehensive score
  const sortedStrategies = [...validStrategies].sort((a, b) => calculateScore(b) - calculateScore(a));

  // Prepare radar data dimensions
  const dimensions = [
    { key: 'sharpeRatio', label: '夏普比率', description: '風險調整後收益' },
    { key: 'maxDrawdown', label: '回撤控制', description: '最大損失控制' },
    { key: 'volatility', label: '波動率優化', description: '收益穩定性' },
    { key: 'winRate', label: '勝率', description: '交易成功率' },
    { key: 'profitFactor', label: '盈利因子', description: '收益/損失比' },
    { key: 'calmarRatio', label: '卡瑪比率', description: '回撤調整收益' }
  ];

  // Prepare datasets for each strategy
  const datasets = sortedStrategies.map((strategy, index) => {
    const strategyColor = getStrategyColor(strategy.type);
    const isSelected = selectedStrategies.has(strategy.id);

    const data = dimensions.map(dim => {
      const value = strategy.performance?.[dim.key as keyof typeof strategy.performance] as number || 0;
      return normalizeMetric(value, dim.key);
    });

    return {
      label: strategy.name,
      data: data,
      borderColor: isSelected ? '#2c3e50' : strategyColor,
      backgroundColor: isSelected
        ? 'rgba(44, 62, 80, 0.2)'
        : `${strategyColor}40`, // Add transparency
      borderWidth: isSelected ? 3 : 2,
      pointRadius: isSelected ? 5 : 4,
      pointHoverRadius: isSelected ? 7 : 6,
      pointBackgroundColor: isSelected ? '#2c3e50' : strategyColor,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: isSelected ? '#2c3e50' : strategyColor,
      pointHoverBorderWidth: 3,
      hidden: false
    };
  });

  // Chart data
  const chartData = {
    labels: dimensions.map(dim => dim.label),
    datasets: datasets
  };

  // Chart options
  const options = {
    ...chartTheme.defaultOptions,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      ...chartTheme.defaultOptions.plugins,
      title: {
        display: showTitle,
        text: '策略多維度性能對比',
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
            const dataset = context[0].dataset;
            const strategy = sortedStrategies[context[0].datasetIndex];
            return strategy ? strategy.name : '未知策略';
          },
          label: (context: any) => {
            const dimension = dimensions[context.dataIndex];
            const value = context.parsed.r;
            const strategy = sortedStrategies[context.datasetIndex];
            const originalValue = strategy?.performance?.[dimension.key as keyof typeof strategy.performance] as number || 0;

            let displayValue = '';
            switch (dimension.key) {
              case 'winRate':
                displayValue = `${originalValue.toFixed(1)}%`;
                break;
              case 'maxDrawdown':
                displayValue = `${originalValue.toFixed(1)}%`;
                break;
              case 'totalReturn':
                displayValue = `${originalValue > 0 ? '+' : ''}${(originalValue * 100).toFixed(1)}%`;
                break;
              default:
                displayValue = originalValue.toFixed(2);
            }

            return `${dimension.label}: ${displayValue} (評分: ${value.toFixed(0)})`;
          },
          afterLabel: (context: any) => {
            const dimension = dimensions[context.dataIndex];
            return dimension.description;
          }
        }
      },
      legend: {
        position: 'top' as const,
        labels: {
          ...chartTheme.defaultOptions.plugins.legend.labels,
          usePointStyle: true,
          padding: 20
        }
      }
    },
    scales: {
      r: {
        beginAtZero: true,
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
          font: {
            size: 10
          },
          color: '#6c757d',
          backdropColor: 'transparent'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          lineWidth: 1
        },
        angleLines: {
          color: 'rgba(0, 0, 0, 0.1)',
          lineWidth: 1
        },
        pointLabels: {
          font: {
            size: 12,
            weight: 'bold' as const
          },
          color: '#2c3e50',
          padding: 15
        }
      }
    },
    onClick: interactive ? (event: any, elements: any[]) => {
      if (elements.length > 0 && onStrategySelect) {
        const datasetIndex = elements[0].datasetIndex;
        const strategy = sortedStrategies[datasetIndex];
        if (strategy) {
          const newSelected = new Set(selectedStrategies);
          if (newSelected.has(strategy.id)) {
            newSelected.delete(strategy.id);
          } else {
            newSelected.add(strategy.id);
          }
          setSelectedStrategies(newSelected);
          onStrategySelect(strategy);
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
  }, [strategies, selectedStrategies]);

  if (validStrategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <p className="text-gray-500 text-sm">沒有可用的策略對比數據</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div style={{ height: `${height}px` }}>
        <Radar ref={chartRef} data={chartData} options={options} />
      </div>

      {/* Strategy Score Ranking */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {sortedStrategies.map((strategy, index) => {
          const score = calculateScore(strategy);
          const isSelected = selectedStrategies.has(strategy.id);

          return (
            <div
              key={strategy.id}
              className={`p-3 rounded-lg border-2 transition-all cursor-pointer ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
              onClick={() => {
                if (interactive && onStrategySelect) {
                  const newSelected = new Set(selectedStrategies);
                  if (newSelected.has(strategy.id)) {
                    newSelected.delete(strategy.id);
                  } else {
                    newSelected.add(strategy.id);
                  }
                  setSelectedStrategies(newSelected);
                  onStrategySelect(strategy);
                }
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getStrategyColor(strategy.type) }}
                  ></div>
                  <span className="font-medium text-sm text-gray-900">
                    {strategy.name}
                  </span>
                </div>
                <span className="text-xs font-bold text-gray-500">
                  #{index + 1}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">綜合評分</span>
                <span className={`text-sm font-bold ${
                  score >= 80 ? 'text-green-600' :
                  score >= 60 ? 'text-blue-600' :
                  score >= 40 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {score.toFixed(0)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Metric Explanations */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        點擊圖表區域或策略卡片來高亮顯示特定策略 • 評分基於各維度綜合計算 (滿分100分)
      </div>
    </div>
  );
};

export default StrategyRadarChart;