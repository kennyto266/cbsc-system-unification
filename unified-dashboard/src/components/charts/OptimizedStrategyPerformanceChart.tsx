import React, { useMemo, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { Card, Select, Space, Button, Skeleton } from 'antd'
import { DownloadOutlined, FullscreenOutlined } from '@ant-design/icons'
import OptimizedChartBase from './OptimizedChartBase'

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

interface OptimizedStrategyPerformanceChartProps {
  strategies: any[]
  timeRange?: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y'
  onTimeRangeChange?: (range: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y') => void
  lazy?: boolean
  visible?: boolean
}

const OptimizedStrategyPerformanceChart: React.FC<OptimizedStrategyPerformanceChartProps> = ({
  strategies,
  timeRange = '1M',
  onTimeRangeChange,
  lazy = true,
  visible = true
}) => {
  // 生成模擬的歷史數據 - 使用缓存优化
  const generateHistoricalData = useCallback((strategy: any, days: number) => {
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
  }, [])

  // 优化的图表数据
  const chartData = useMemo(() => {
    if (!strategies.length) return { labels: [], datasets: [] }

    const days = {
      '1D': 1,
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365
    }[timeRange] || 30

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
  }, [strategies, timeRange, generateHistoricalData])

  // 优化的图表选项
  const options: ChartOptions<'line'> = useMemo(() => ({
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
  }), [])

  const handleExport = useCallback(() => {
    const canvas = document.querySelector('canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `strategy-performance-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }, [])

  const handleFullscreen = useCallback(() => {
    const chartElement = document.querySelector('.chart-container')
    if (chartElement) {
      if ((chartElement as any).requestFullscreen) {
        (chartElement as any).requestFullscreen()
      }
    }
  }, [])

  const handleDataPointClick = useCallback((data: any) => {
    console.log('Data point clicked:', data)
  }, [])

  // 渲染图表内容
  const renderChart = useCallback(({ width, height, isIntersecting }: {
    width: number,
    height: number,
    isIntersecting: boolean
  }) => {
    if (!isIntersecting) {
      return (
        <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="text-center">
            <div className="text-6xl mb-4">📊</div>
            <div>图表加载中...</div>
          </div>
        </div>
      )
    }

    return strategies.length > 0 ? (
      <Line data={chartData} options={options} />
    ) : (
      <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="text-center text-gray-500">
          <div className="text-6xl mb-4">📊</div>
          <div>暂无策略数据</div>
        </div>
      </div>
    )
  }, [strategies.length, chartData, options])

  return (
    <OptimizedChartBase
      height={400}
      data={chartData}
      onDataPointClick={handleDataPointClick}
      lazy={lazy}
      className="performance-chart-card"
    >
      {({ width, height, isIntersecting }) => (
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
                title="导出图表"
              />
              <Button
                type="text"
                size="small"
                icon={<FullscreenOutlined />}
                onClick={handleFullscreen}
                title="全屏显示"
              />
            </Space>
          }
        >
          <div className="chart-container" style={{ height: '400px' }}>
            {isIntersecting ? (
              renderChart({ width, height, isIntersecting })
            ) : (
              <Skeleton active paragraph={{ rows: 10 }} />
            )}
          </div>
        </Card>
      )}
    </OptimizedChartBase>
  )
}

OptimizedStrategyPerformanceChart.displayName = 'OptimizedStrategyPerformanceChart'

export default OptimizedStrategyPerformanceChart