import React, { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Card, Select, Space, Button, Radio } from 'antd'
import { DownloadOutlined, BarChartOutlined, SwapOutlined } from '@ant-design/icons'
import { Strategy } from '../../types'

// 註冊Chart.js組件
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

type MetricType = 'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'

interface StrategyComparisonChartProps {
  strategies: Strategy[]
  metric?: MetricType
  onMetricChange?: (metric: MetricType) => void
  sortBy?: 'name' | 'value'
  showTopN?: number
}

const metricConfig = {
  totalReturn: {
    label: '總回報率',
    formatter: (value: number) => `${(value * 100).toFixed(2)}%`,
    color: '#10B981',
    bgColor: 'rgba(16, 185, 129, 0.8)'
  },
  sharpeRatio: {
    label: '夏普比率',
    formatter: (value: number) => value.toFixed(2),
    color: '#3B82F6',
    bgColor: 'rgba(59, 130, 246, 0.8)'
  },
  maxDrawdown: {
    label: '最大回撤',
    formatter: (value: number) => `${(value * 100).toFixed(2)}%`,
    color: '#EF4444',
    bgColor: 'rgba(239, 68, 68, 0.8)'
  },
  winRate: {
    label: '勝率',
    formatter: (value: number) => `${(value * 100).toFixed(1)}%`,
    color: '#8B5CF6',
    bgColor: 'rgba(139, 92, 246, 0.8)'
  },
  profitFactor: {
    label: '盈利因子',
    formatter: (value: number) => value.toFixed(2),
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.8)'
  }
}

const StrategyComparisonChart: React.FC<StrategyComparisonChartProps> = ({
  strategies,
  metric = 'totalReturn',
  onMetricChange,
  sortBy = 'value',
  showTopN = 10
}) => {
  const chartData = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')

    if (activeStrategies.length === 0) {
      return { labels: [], datasets: [] }
    }

    // 根據選擇的指標提取數據
    let processedStrategies = activeStrategies.map(strategy => ({
      name: strategy.name,
      value: strategy.performance[metric],
      type: strategy.type,
      riskLevel: strategy.riskLevel,
      strategy: strategy
    }))

    // 排序
    if (sortBy === 'value') {
      processedStrategies.sort((a, b) => b.value - a.value)
    } else {
      processedStrategies.sort((a, b) => a.name.localeCompare(b.name))
    }

    // 限制顯示數量
    processedStrategies = processedStrategies.slice(0, showTopN)

    const labels = processedStrategies.map(s => s.name)
    const data = processedStrategies.map(s => s.value)
    const config = metricConfig[metric]

    // 根據風險級別設置不同顏色
    const colors = processedStrategies.map(s => {
      const riskColors = {
        low: 'rgba(16, 185, 129, 0.8)',    // green
        medium: 'rgba(245, 158, 11, 0.8)',  // amber
        high: 'rgba(239, 68, 68, 0.8)'      // red
      }
      return riskColors[s.riskLevel]
    })

    const borderColors = processedStrategies.map(s => {
      const riskBorderColors = {
        low: 'rgba(16, 185, 129, 1)',
        medium: 'rgba(245, 158, 11, 1)',
        high: 'rgba(239, 68, 68, 1)'
      }
      return riskBorderColors[s.riskLevel]
    })

    return {
      labels,
      datasets: [
        {
          label: config.label,
          data,
          backgroundColor: colors,
          borderColor: borderColors,
          borderWidth: 2,
          borderRadius: 4,
          barThickness: 'flex' as const,
          maxBarThickness: 40
        }
      ]
    }
  }, [strategies, metric, sortBy, showTopN])

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          title: function(context) {
            const strategy = strategies.find(s => s.name === context[0].label)
            if (strategy) {
              return `${strategy.name} (${strategy.type})`
            }
            return context[0].label
          },
          label: function(context) {
            const config = metricConfig[metric]
            const strategy = strategies.find(s => s.name === context.label)
            const riskLabels = {
              low: '低風險',
              medium: '中風險',
              high: '高風險'
            }

            return [
              `${config.label}: ${config.formatter(context.parsed.y)}`,
              ...(strategy ? [`風險級別: ${riskLabels[strategy.riskLevel]}`] : [])
            ]
          },
          afterLabel: function(context) {
            const strategy = strategies.find(s => s.name === context.label)
            if (strategy && metric !== 'totalReturn') {
              return [
                `總回報率: ${(strategy.performance.totalReturn * 100).toFixed(2)}%`,
                `夏普比率: ${strategy.performance.sharpeRatio.toFixed(2)}`
              ]
            }
            return []
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        },
        ticks: {
          maxRotation: 45,
          minRotation: 0,
          autoSkip: false,
          font: {
            size: 11
          }
        }
      },
      y: {
        display: true,
        position: 'left' as const,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            const config = metricConfig[metric]
            return config.formatter(value as number)
          }
        }
      }
    },
    onClick: (event, activeElements) => {
      if (activeElements.length > 0) {
        const index = activeElements[0].index
        const strategyName = chartData.labels[index]
        const strategy = strategies.find(s => s.name === strategyName)
        if (strategy) {
          console.log('點擊了策略:', strategy)
          // 可以添加點擊事件處理，例如顯示策略詳情
        }
      }
    }
  }

  const handleExport = () => {
    const canvas = document.querySelector('.comparison-chart canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `strategy-comparison-${metric}-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  const handleSortToggle = () => {
    // 切換排序方式
    const newSortBy = sortBy === 'name' ? 'value' : 'name'
    // 這裡需要調用父組件的回調函數來更新排序
    console.log('切換排序方式:', newSortBy)
  }

  return (
    <Card
      title="策略性能對比"
      className="comparison-chart-card"
      extra={
        <Space>
          <Radio.Group
            value={sortBy}
            size="small"
            onChange={(e) => {
              const newSortBy = e.target.value
              console.log('更改排序方式:', newSortBy)
              // 這裡需要調用父組件的回調函數
            }}
          >
            <Radio.Button value="name">名稱</Radio.Button>
            <Radio.Button value="value">數值</Radio.Button>
          </Radio.Group>
          <Select
            value={metric}
            onChange={onMetricChange}
            style={{ width: 120 }}
            size="small"
          >
            <Select.Option value="totalReturn">總回報率</Select.Option>
            <Select.Option value="sharpeRatio">夏普比率</Select.Option>
            <Select.Option value="maxDrawdown">最大回撤</Select.Option>
            <Select.Option value="winRate">勝率</Select.Option>
            <Select.Option value="profitFactor">盈利因子</Select.Option>
          </Select>
          <Select
            value={showTopN}
            onChange={(value) => {
              console.log('更改顯示數量:', value)
              // 這裡需要調用父組件的回調函數
            }}
            style={{ width: 70 }}
            size="small"
          >
            <Select.Option value={5}>前5</Select.Option>
            <Select.Option value={10}>前10</Select.Option>
            <Select.Option value={15}>前15</Select.Option>
            <Select.Option value={20}>前20</Select.Option>
          </Select>
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            title="導出圖表"
          />
        </Space>
      }
    >
      <div className="comparison-chart" style={{ height: '400px' }}>
        {chartData.labels.length > 0 ? (
          <Bar data={chartData} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <div>暫無活躍策略數據</div>
            </div>
          </div>
        )}
      </div>

      {/* 圖例 */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span className="text-gray-600">低風險</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-amber-500 rounded"></div>
            <span className="text-gray-600">中風險</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span className="text-gray-600">高風險</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default StrategyComparisonChart