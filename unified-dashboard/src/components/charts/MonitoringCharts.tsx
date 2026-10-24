import React, { useEffect, useRef } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { Card, Typography, Space } from 'antd'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const { Text } = Typography

// System Resource Chart Component
interface SystemResourceChartProps {
  timeRange: string
  metrics: Array<{
    name: string
    value: number
    unit: string
    status: 'normal' | 'warning' | 'critical'
    trend: number
  }>
  showLegend?: boolean
}

export const SystemResourceChart: React.FC<SystemResourceChartProps> = ({
  timeRange,
  metrics,
  showLegend = true,
}) => {
  const chartRef = useRef<ChartJS<'line'>>(null)

  // Generate time labels based on time range
  const generateTimeLabels = () => {
    const labels = []
    const now = new Date()
    let interval = 5 // minutes
    let count = 12

    switch (timeRange) {
      case '1h':
        interval = 5
        count = 12
        break
      case '6h':
        interval = 30
        count = 12
        break
      case '24h':
        interval = 120
        count = 12
        break
      case '7d':
        interval = 1440 // 24 hours
        count = 7
        break
      default:
        interval = 5
        count = 12
    }

    for (let i = count - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * interval * 60000)
      if (timeRange === '7d') {
        labels.push(time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      } else {
        labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
      }
    }

    return labels
  }

  // Generate mock data for demonstration
  const generateChartData = () => {
    const labels = generateTimeLabels()
    const datasets = metrics.map((metric, index) => {
      const baseValue = metric.value
      const colors = {
        normal: 'rgb(82, 196, 26)',
        warning: 'rgb(250, 173, 20)',
        critical: 'rgb(255, 77, 79)',
      }

      return {
        label: metric.name,
        data: labels.map(() => baseValue + Math.random() * 10 - 5),
        borderColor: colors[metric.status],
        backgroundColor: colors[metric.status] + '20',
        tension: 0.4,
        fill: true,
      }
    })

    return { labels, datasets }
  }

  const chartData = generateChartData()

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`,
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  }

  return (
    <div style={{ height: '300px' }}>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  )
}

// Alert Trend Chart Component
interface AlertTrendChartProps {
  timeRange: string
  showSeverityBreakdown?: boolean
}

export const AlertTrendChart: React.FC<AlertTrendChartProps> = ({
  timeRange,
  showSeverityBreakdown = true,
}) => {
  const generateTimeLabels = () => {
    const labels = []
    const now = new Date()
    let interval = 60 // minutes
    let count = 24

    switch (timeRange) {
      case '1h':
        interval = 5
        count = 12
        break
      case '6h':
        interval = 30
        count = 12
        break
      case '24h':
        interval = 120
        count = 12
        break
      case '7d':
        interval = 1440 // 24 hours
        count = 7
        break
      default:
        interval = 60
        count = 24
    }

    for (let i = count - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * interval * 60000)
      if (timeRange === '7d') {
        labels.push(time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      } else {
        labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
      }
    }

    return labels
  }

  const labels = generateTimeLabels()

  const chartData = {
    labels,
    datasets: showSeverityBreakdown
      ? [
          {
            label: '嚴重',
            data: labels.map(() => Math.floor(Math.random() * 3)),
            backgroundColor: 'rgba(255, 77, 79, 0.6)',
          },
          {
            label: '警告',
            data: labels.map(() => Math.floor(Math.random() * 8)),
            backgroundColor: 'rgba(250, 173, 20, 0.6)',
          },
          {
            label: '信息',
            data: labels.map(() => Math.floor(Math.random() * 15)),
            backgroundColor: 'rgba(24, 144, 255, 0.6)',
          },
        ]
      : [
          {
            label: '告警總數',
            data: labels.map(() => Math.floor(Math.random() * 20) + 5),
            backgroundColor: 'rgba(24, 144, 255, 0.6)',
            borderColor: 'rgba(24, 144, 255, 1)',
            borderWidth: 1,
          },
        ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showSeverityBreakdown,
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 5,
        },
      },
    },
  }

  return (
    <div style={{ height: '300px' }}>
      <Bar data={chartData} options={options} />
    </div>
  )
}

// Strategy Execution Chart Component
interface StrategyExecutionChartProps {
  strategies: Array<{
    id: string
    name: string
    status: string
    lastRun: string
    nextRun: string
    executions: number
    successRate: number
  }>
  timeRange: string
}

export const StrategyExecutionChart: React.FC<StrategyExecutionChartProps> = ({
  strategies,
  timeRange,
}) => {
  const generateTimeLabels = () => {
    const labels = []
    const now = new Date()
    let interval = 30 // minutes
    let count = 8

    switch (timeRange) {
      case '1h':
        interval = 5
        count = 12
        break
      case '6h':
        interval = 30
        count = 12
        break
      case '24h':
        interval = 120
        count = 12
        break
      case '7d':
        interval = 1440 // 24 hours
        count = 7
        break
      default:
        interval = 30
        count = 8
    }

    for (let i = count - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * interval * 60000)
      if (timeRange === '7d') {
        labels.push(time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      } else {
        labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
      }
    }

    return labels
  }

  const labels = generateTimeLabels()
  const colors = [
    'rgb(24, 144, 255)',
    'rgb(82, 196, 26)',
    'rgb(250, 173, 20)',
    'rgb(255, 77, 79)',
  ]

  const chartData = {
    labels,
    datasets: strategies.slice(0, 4).map((strategy, index) => ({
      label: strategy.name,
      data: labels.map(() => Math.floor(Math.random() * 100) + 20),
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '20',
      tension: 0.3,
      fill: true,
    })),
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `${value}ms`,
        },
      },
    },
  }

  return (
    <div style={{ height: '300px' }}>
      <Line data={chartData} options={options} />
    </div>
  )
}

// Network Latency Chart Component
interface NetworkLatencyChartProps {
  timeRange: string
  services: string[]
}

export const NetworkLatencyChart: React.FC<NetworkLatencyChartProps> = ({
  timeRange,
  services,
}) => {
  const generateTimeLabels = () => {
    const labels = []
    const now = new Date()
    let interval = 30 // minutes
    let count = 8

    switch (timeRange) {
      case '1h':
        interval = 5
        count = 12
        break
      case '6h':
        interval = 30
        count = 12
        break
      case '24h':
        interval = 120
        count = 12
        break
      case '7d':
        interval = 1440 // 24 hours
        count = 7
        break
      default:
        interval = 30
        count = 8
    }

    for (let i = count - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * interval * 60000)
      if (timeRange === '7d') {
        labels.push(time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      } else {
        labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
      }
    }

    return labels
  }

  const labels = generateTimeLabels()
  const colors = [
    'rgb(114, 46, 209)',
    'rgb(255, 87, 51)',
    'rgb(0, 201, 167)',
    'rgb(255, 184, 0)',
  ]

  const chartData = {
    labels,
    datasets: services.map((service, index) => ({
      label: service,
      data: labels.map(() => Math.floor(Math.random() * 50) + 10),
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '20',
      tension: 0.4,
      fill: false,
    })),
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `${value}ms`,
        },
      },
    },
  }

  return (
    <div style={{ height: '300px' }}>
      <Line data={chartData} options={options} />
    </div>
  )
}