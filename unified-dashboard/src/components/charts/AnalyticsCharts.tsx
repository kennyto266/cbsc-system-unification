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
  RadialLinearScale,
  ArcElement,
} from 'chart.js'
import { Line, Bar, Pie, Radar } from 'react-chartjs-2'
import { Card, Typography, Space } from 'antd'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale
)

const { Text } = Typography

// Performance Analytics Chart Component
interface PerformanceAnalyticsChartProps {
  timeRange: string
  strategy: string
  benchmark: string
}

export const PerformanceAnalyticsChart: React.FC<PerformanceAnalyticsChartProps> = ({
  timeRange,
  strategy,
  benchmark,
}) => {
  const chartRef = useRef<ChartJS<'line'>>(null)

  // Generate date labels
  const generateDateLabels = () => {
    const labels = []
    const now = new Date()
    let days = 30

    switch (timeRange) {
      case '1M':
        days = 30
        break
      case '3M':
        days = 90
        break
      case '6M':
        days = 180
        break
      case '1Y':
        days = 365
        break
      case 'ALL':
        days = 730
        break
    }

    for (let i = days; i >= 0; i -= Math.max(1, Math.floor(days / 50))) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    }

    return labels
  }

  const labels = generateDateLabels()

  // Generate mock performance data
  const generatePerformanceData = () => {
    let portfolioValue = 100000
    let benchmarkValue = 100000

    return labels.map(() => {
      const portfolioReturn = (Math.random() - 0.48) * 0.03 // Slight positive bias
      const benchmarkReturn = (Math.random() - 0.5) * 0.025

      portfolioValue *= (1 + portfolioReturn)
      benchmarkValue *= (1 + benchmarkReturn)

      return {
        portfolio: portfolioValue,
        benchmark: benchmarkValue,
      }
    })
  }

  const performanceData = generatePerformanceData()

  const chartData = {
    labels,
    datasets: [
      {
        label: '策略組合',
        data: performanceData.map(d => d.portfolio),
        borderColor: 'rgb(24, 144, 255)',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        tension: 0.4,
        fill: true,
        borderWidth: 2,
      },
      {
        label: benchmark,
        data: performanceData.map(d => d.benchmark),
        borderColor: 'rgb(150, 150, 150)',
        backgroundColor: 'rgba(150, 150, 150, 0.1)',
        tension: 0.4,
        fill: true,
        borderDash: [5, 5],
        borderWidth: 2,
      },
    ],
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
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y
            const baseValue = context.datasetIndex === 0 ? 100000 : 100000
            const returnPercent = ((value - baseValue) / baseValue * 100).toFixed(2)
            return `${context.dataset.label}: ¥${value.toFixed(2)} (${returnPercent}%)`
          },
        },
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        ticks: {
          callback: (value: any) => `¥${(value / 1000).toFixed(0)}K`,
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
    <div style={{ height: '400px' }}>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  )
}

// Risk Analysis Chart Component
interface RiskAnalysisChartProps {
  timeRange: string
  strategy: string
}

export const RiskAnalysisChart: React.FC<RiskAnalysisChartProps> = ({
  timeRange,
  strategy,
}) => {
  const labels = ['-5%', '-4%', '-3%', '-2%', '-1%', '0%', '1%', '2%', '3%', '4%', '5%']

  const chartData = {
    labels,
    datasets: [
      {
        label: '收益分布',
        data: [5, 8, 15, 25, 35, 20, 28, 20, 12, 6, 3],
        backgroundColor: labels.map(label =>
          label.startsWith('-') ? 'rgba(255, 77, 79, 0.6)' : 'rgba(82, 196, 26, 0.6)'
        ),
        borderColor: labels.map(label =>
          label.startsWith('-') ? 'rgba(255, 77, 79, 1)' : 'rgba(82, 196, 26, 1)'
        ),
        borderWidth: 1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: '頻率',
        },
      },
      x: {
        title: {
          display: true,
          text: '日收益率',
        },
      },
    },
  }

  return (
    <div style={{ height: '400px' }}>
      <Bar data={chartData} options={options} />
    </div>
  )
}

// Sector Allocation Chart Component
interface SectorAllocationChartProps {
  data: Array<{
    sector: string
    allocation: number
    performance: number
  }>
  showDetails?: boolean
}

export const SectorAllocationChart: React.FC<SectorAllocationChartProps> = ({
  data,
  showDetails = false,
}) => {
  const chartData = {
    labels: data.map(d => d.sector),
    datasets: [
      {
        data: data.map(d => d.allocation),
        backgroundColor: [
          'rgba(24, 144, 255, 0.8)',
          'rgba(82, 196, 26, 0.8)',
          'rgba(250, 173, 20, 0.8)',
          'rgba(255, 87, 51, 0.8)',
          'rgba(114, 46, 209, 0.8)',
        ],
        borderColor: [
          'rgba(24, 144, 255, 1)',
          'rgba(82, 196, 26, 1)',
          'rgba(250, 173, 20, 1)',
          'rgba(255, 87, 51, 1)',
          'rgba(114, 46, 209, 1)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const dataIndex = context.dataIndex
            const allocation = data[dataIndex].allocation
            const performance = data[dataIndex].performance
            return [
              `配置比例: ${allocation}%`,
              `收益率: ${performance > 0 ? '+' : ''}${performance}%`,
            ]
          },
        },
      },
    },
  }

  return (
    <div>
      <div style={{ height: showDetails ? '250px' : '300px' }}>
        <Pie data={chartData} options={options} />
      </div>
      {showDetails && (
        <div className="mt-4 space-y-2">
          {data.map((sector, index) => (
            <div key={index} className="flex justify-between items-center">
              <Space>
                <div
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: chartData.datasets[0].backgroundColor[index],
                  }}
                />
                <Text>{sector.sector}</Text>
              </Space>
              <Space>
                <Text>{sector.allocation}%</Text>
                <Text className={sector.performance > 0 ? 'text-green-600' : 'text-red-600'}>
                  {sector.performance > 0 ? '+' : ''}{sector.performance}%
                </Text>
              </Space>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Correlation Matrix Chart Component
interface CorrelationMatrixChartProps {
  strategies: Array<{ id: string; name: string }>
  timeRange: string
}

export const CorrelationMatrixChart: React.FC<CorrelationMatrixChartProps> = ({
  strategies,
  timeRange,
}) => {
  // Generate correlation matrix data
  const generateCorrelationMatrix = () => {
    const matrix = []
    const labels = strategies.map(s => s.name)

    for (let i = 0; i < strategies.length; i++) {
      const row = []
      for (let j = 0; j < strategies.length; j++) {
        if (i === j) {
          row.push(1.0)
        } else {
          // Generate realistic correlation values
          const correlation = 0.3 + Math.random() * 0.6
          row.push(Number(correlation.toFixed(2)))
        }
      }
      matrix.push(row)
    }

    return { labels, matrix }
  }

  const { labels, matrix } = generateCorrelationMatrix()

  const chartData = {
    labels,
    datasets: labels.map((label, i) => ({
      label,
      data: matrix[i],
      backgroundColor: 'rgba(24, 144, 255, 0.6)',
      borderColor: 'rgba(24, 144, 255, 1)',
      borderWidth: 1,
    })),
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.r
            return `相關性: ${value}`
          },
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 0.2,
        },
      },
    },
  }

  return (
    <div style={{ height: '400px' }}>
      <Radar data={chartData} options={options} />
    </div>
  )
}

// Drawdown Chart Component
interface DrawdownChartProps {
  timeRange: string
  strategy: string
  showRecoveryTime?: boolean
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({
  timeRange,
  strategy,
  showRecoveryTime = false,
}) => {
  const generateDateLabels = () => {
    const labels = []
    const now = new Date()
    let days = 180

    switch (timeRange) {
      case '1M':
        days = 30
        break
      case '3M':
        days = 90
        break
      case '6M':
        days = 180
        break
      case '1Y':
        days = 365
        break
      case 'ALL':
        days = 730
        break
    }

    for (let i = days; i >= 0; i -= Math.max(1, Math.floor(days / 100))) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    }

    return labels
  }

  const labels = generateDateLabels()

  // Generate mock drawdown data
  const generateDrawdownData = () => {
    let drawdown = 0
    let inDrawdown = false
    const data = []

    for (let i = 0; i < labels.length; i++) {
      if (!inDrawdown && Math.random() < 0.1) {
        inDrawdown = true
        drawdown = -Math.random() * 0.15 - 0.05
      }

      if (inDrawdown) {
        drawdown = Math.max(0, drawdown + Math.random() * 0.02)
        if (drawdown === 0) {
          inDrawdown = false
        }
      } else {
        drawdown = Math.max(0, drawdown - Math.random() * 0.01)
      }

      data.push(drawdown * 100)
    }

    return data
  }

  const drawdownData = generateDrawdownData()

  const chartData = {
    labels,
    datasets: [
      {
        label: '回撤',
        data: drawdownData,
        borderColor: 'rgb(255, 77, 79)',
        backgroundColor: 'rgba(255, 77, 79, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `回撤: ${context.parsed.y.toFixed(2)}%`
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: '回撤 (%)',
        },
        ticks: {
          callback: (value: any) => `${value}%`,
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