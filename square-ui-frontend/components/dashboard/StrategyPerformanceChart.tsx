'use client';

import React from 'react';
import { SquareCard } from '@/components/ui';
import {
  TrendingUpIcon,
  TrendingDownIcon,
  ActivityIcon,
  AlertCircleIcon
} from 'lucide-react';
import { useStrategyPerformance } from '@/hooks/useRealTimeData';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';

// 註冊 Chart.js 組件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface StrategyPerformance {
  name: string;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  signal_count?: number;
}

interface StrategyPerformanceData {
  timestamp: string;
  strategies: StrategyPerformance[];
}

interface ChartDataPoint {
  time: string;
  value: number;
}

const StrategyPerformanceChart: React.FC = () => {
  const { data, isConnected, isUsingMock, lastUpdate } = useStrategyPerformance<StrategyPerformanceData>();

  // 處理歷史數據（實際應用中應從 WebSocket 或 API 獲取）
  const [historicalData, setHistoricalData] = useState<Record<string, ChartDataPoint[]>>({});

  // 當新數據到達時，更新歷史數據
  React.useEffect(() => {
    if (data && data.strategies) {
      const time = new Date(data.timestamp).toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });

      setHistoricalData(prev => {
        const newData = { ...prev };
        data.strategies.forEach(strategy => {
          if (!newData[strategy.name]) {
            newData[strategy.name] = [];
          }

          // 保留最近 20 個數據點
          const points = [...newData[strategy.name], { time, value: strategy.sharpe_ratio }];
          newData[strategy.name] = points.slice(-20);
        });
        return newData;
      });
    }
  }, [data]);

  // Sharpe 比率圖表配置
  const sharpeChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Sharpe 比率趨勢',
        color: '#374151',
        font: {
          size: 14,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Sharpe 比率',
          color: '#6B7280',
        },
        grid: {
          color: '#F3F4F6',
        },
      },
      x: {
        title: {
          display: true,
          text: '時間',
          color: '#6B7280',
        },
        grid: {
          color: '#F3F4F6',
        },
      },
    },
    elements: {
      line: {
        tension: 0.1,
      },
    },
  };

  // 準備 Sharpe 比率圖表數據
  const sharpeChartData = {
    labels: Object.values(historicalData)[0]?.map(p => p.time) || [],
    datasets: data?.strategies.map((strategy, index) => ({
      label: strategy.name,
      data: historicalData[strategy.name]?.map(p => p.value) || [],
      borderColor: [
        '#3B82F6', // blue
        '#10B981', // green
        '#F59E0B', // amber
        '#EF4444', // red
      ][index],
      backgroundColor: [
        'rgba(59, 130, 246, 0.1)',
        'rgba(16, 185, 129, 0.1)',
        'rgba(245, 158, 11, 0.1)',
        'rgba(239, 68, 68, 0.1)',
      ][index],
      borderWidth: 2,
    })) || [],
  };

  // 獲取顏色基於值
  const getValueColor = (value: number, threshold: number) => {
    if (value > threshold) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  // 獲取趨勢圖標
  const getTrendIcon = (value: number) => {
    return value > 0 ? TrendingUpIcon : TrendingDownIcon;
  };

  if (!data) {
    return (
      <SquareCard>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </SquareCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* 策略性能卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data.strategies.map((strategy, index) => (
          <SquareCard key={strategy.name}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-500 truncate">
                  {strategy.name.replace('Strategy', '')}
                </h3>
                <div
                  className={`p-2 rounded-full ${
                    strategy.sharpe_ratio > 1
                      ? 'bg-green-100 text-green-600'
                      : strategy.sharpe_ratio > 0
                      ? 'bg-yellow-100 text-yellow-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  <ActivityIcon className="w-4 h-4" />
                </div>
              </div>

              <div className="space-y-3">
                {/* Sharpe 比率 */}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Sharpe 比率</span>
                  <div className="flex items-center space-x-1">
                    <span className={`text-sm font-medium ${getValueColor(strategy.sharpe_ratio, 1)}`}>
                      {strategy.sharpe_ratio.toFixed(2)}
                    </span>
                    {React.createElement(getTrendIcon(strategy.sharpe_ratio), {
                      className: `w-3 h-3 ${getValueColor(strategy.sharpe_ratio, 0)}`,
                    })}
                  </div>
                </div>

                {/* 最大回撤 */}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">最大回撤</span>
                  <div className="flex items-center space-x-1">
                    <span className={`text-sm font-medium ${getValueColor(-strategy.max_drawdown, 0)}`}>
                      -{(strategy.max_drawdown * 100).toFixed(1)}%
                    </span>
                    <TrendingDownIcon className="w-3 h-3 text-red-500" />
                  </div>
                </div>

                {/* 總回報 */}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">總回報</span>
                  <div className="flex items-center space-x-1">
                    <span className={`text-sm font-medium ${getValueColor(strategy.total_return, 0)}`}>
                      {(strategy.total_return * 100).toFixed(1)}%
                    </span>
                    {React.createElement(getTrendIcon(strategy.total_return), {
                      className: `w-3 h-3 ${getValueColor(strategy.total_return, 0)}`,
                    })}
                  </div>
                </div>

                {/* 勝率 */}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">勝率</span>
                  <span className={`text-sm font-medium ${
                    strategy.win_rate > 0.6 ? 'text-green-600' :
                    strategy.win_rate > 0.4 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(strategy.win_rate * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </SquareCard>
        ))}
      </div>

      {/* Sharpe 比率趨勢圖 */}
      <SquareCard>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">策略表現趨勢</h3>
            <div className="flex items-center space-x-2">
              <div className={`px-2 py-1 text-xs rounded-full ${
                isConnected
                  ? 'bg-green-100 text-green-800'
                  : isUsingMock
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {isConnected ? '實時連接' : isUsingMock ? '模擬數據' : '離線'}
              </div>
              {lastUpdate && (
                <span className="text-xs text-gray-500">
                  更新: {lastUpdate.toLocaleTimeString('zh-TW')}
                </span>
              )}
            </div>
          </div>

          <div className="h-64">
            <Line data={sharpeChartData} options={sharpeChartOptions} />
          </div>
        </div>
      </SquareCard>

      {/* 風險提示 */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertCircleIcon className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800">風險提示</h4>
            <p className="text-xs text-yellow-700 mt-1">
              過往表現不保證未來回報。Sharpe 比率是風險調整後的收益指標，數值越高表示在相同風險下回報越好。
              最大回撤表示策略歷史上曾經出現的最大虧損百分比。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyPerformanceChart;