import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartJSTooltip,
  Legend as ChartJSLegend,
  TimeScale,
} from 'chart.js'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  BarChart3,
  PieChart,
  Zap,
  Shield,
  DollarSign
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Progress } from '../ui/progress'
import { Grid } from '../square-ui/Grid'
import { MetricCard } from '../square-ui/MetricCard'
import { cn } from '../../lib/utils'
import { Strategy } from '../../types'

// 註冊Chart.js組件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartJSTooltip,
  ChartJSLegend,
  TimeScale
)

interface StrategyPerformanceChartProps {
  strategies: Strategy[]
  timeRange?: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y'
  onTimeRangeChange?: (range: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y') => void
}

const StrategyPerformanceChart: React.FC<StrategyPerformanceChartProps> = ({
  strategies,
  timeRange = '1M',
  onTimeRangeChange
}) => {
  // 生成模擬的歷史數據
  const generateHistoricalData = (strategy: Strategy, days: number) => {
    const data = []
    const baseValue = 10000
    let currentValue = baseValue
    const dailyReturn = strategy.performance.totalReturn / days

    for (let i = 0; i < days; i++) {
      const randomVolatility = (Math.random() - 0.5) * 0.02
      const dailyChange = dailyReturn / days + randomVolatility
      currentValue *= (1 + dailyChange)
      data.push({
        date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000),
        value: currentValue
      })
    }
    return data
  }

  const chartData = useMemo(() => {
    const days = {
      '1D': 1,
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365
    }[timeRange]

    const datasets = strategies.slice(0, 5).map((strategy, index) => {
      const colors = [
        'rgb(59, 130, 246)',  // blue
        'rgb(16, 185, 129)',  // green
        'rgb(251, 146, 60)',  // orange
        'rgb(147, 51, 234)',  // purple
        'rgb(236, 72, 153)'   // pink
      ]
      const historicalData = generateHistoricalData(strategy, days)

      return {
        label: strategy.name,
        data: historicalData.map(d => d.value),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '20',
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: colors[index % colors.length]
      }
    })

    const labels = strategies.length > 0
      ? generateHistoricalData(strategies[0], days).map(d =>
          d.date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' })
        )
      : []

    return { labels, datasets }
  }, [strategies, timeRange])

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12
          }
        }
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        titleFont: {
          size: 14
        },
        bodyFont: {
          size: 13
        },
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: $${context.parsed.y.toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
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
            return '$' + (value as number).toLocaleString('zh-TW', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0
            })
          }
        }
      }
    },
    elements: {
      point: {
        hoverRadius: 6
      }
    }
  }

  const handleExport = () => {
    // 導出圖表功能
    const canvas = document.querySelector('canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `strategy-performance-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  const handleFullscreen = () => {
    // 全屏顯示功能
    const chartElement = document.querySelector('.chart-container')
    if (chartElement) {
      if (chartElement.requestFullscreen) {
        chartElement.requestFullscreen()
      }
    }
  }

  return (
    <Card
      title="策略性能走勢"
      className="performance-chart-card"
      extra={
        <Space>
          <Select
            value={timeRange}
            onChange={onTimeRangeChange}
            style={{ width: 80 }}
            size="small"
          >
            <Select.Option value="1D">1日</Select.Option>
            <Select.Option value="1W">1週</Select.Option>
            <Select.Option value="1M">1月</Select.Option>
            <Select.Option value="3M">3月</Select.Option>
            <Select.Option value="6M">6月</Select.Option>
            <Select.Option value="1Y">1年</Select.Option>
          </Select>
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            title="導出圖表"
          />
          <Button
            type="text"
            size="small"
            icon={<FullscreenOutlined />}
            onClick={handleFullscreen}
            title="全屏顯示"
          />
        </Space>
      }
    >
      <div className="chart-container" style={{ height: '400px' }}>
        {strategies.length > 0 ? (
          <Line data={chartData} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <div>暫無策略數據</div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export default StrategyPerformanceChart
