import React, { useMemo } from 'react'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js'
import { Pie } from 'react-chartjs-2'
import { Card, Select, Space, Button, Statistic } from 'antd'
import { DownloadOutlined, PieChartOutlined } from '@ant-design/icons'
import { Strategy } from '../../types'

// 註冊Chart.js組件
ChartJS.register(ArcElement, Tooltip, Legend)

interface AssetAllocationChartProps {
  strategies: Strategy[]
  totalValue?: number
  showDetails?: boolean
}

const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({
  strategies,
  totalValue = 100000,
  showDetails = true
}) => {
  // 計算每個策略的分配比例
  const allocationData = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')

    if (activeStrategies.length === 0) {
      return []
    }

    // 根據策略性能和風險級別計算權重
    const weights = activeStrategies.map(strategy => {
      const riskMultiplier = {
        low: 1.5,
        medium: 1.0,
        high: 0.7
      }[strategy.riskLevel]

      const performanceWeight = Math.max(0.1, strategy.performance.sharpeRatio / 2)
      return Math.pow(riskMultiplier * performanceWeight, 0.8)
    })

    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0)

    return activeStrategies.map((strategy, index) => ({
      name: strategy.name,
      value: (weights[index] / totalWeight) * 100,
      allocation: (weights[index] / totalWeight) * totalValue,
      performance: strategy.performance,
      type: strategy.type,
      riskLevel: strategy.riskLevel
    })).sort((a, b) => b.value - a.value)
  }, [strategies, totalValue])

  const chartData = useMemo(() => {
    const colors = [
      '#3B82F6', // blue
      '#10B981', // green
      '#FB923C', // orange
      '#9333EA', // purple
      '#EC4899', // pink
      '#06B6D4', // cyan
      '#F59E0B', // amber
      '#84CC16', // lime
      '#6366F1', // indigo
      '#14B8A6'  // teal
    ]

    return {
      labels: allocationData.map(item => item.name),
      datasets: [
        {
          data: allocationData.map(item => item.value),
          backgroundColor: colors.slice(0, allocationData.length),
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverBorderWidth: 3,
          hoverBorderColor: '#ffffff'
        }
      ]
    }
  }, [allocationData])

  const options: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12
          },
          generateLabels: function(chart) {
            const data = chart.data
            if (data.labels && data.datasets.length) {
              return data.labels.map((label, i) => {
                const dataset = data.datasets[0]
                const value = dataset.data[i] as number
                const item = allocationData[i]

                return {
                  text: `${label} (${value.toFixed(1)}%)`,
                  fillStyle: dataset.backgroundColor[i] as string,
                  hidden: false,
                  index: i
                }
              })
            }
            return []
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
        callbacks: {
          label: function(context) {
            const item = allocationData[context.dataIndex]
            return [
              `${context.label}: ${context.parsed.toFixed(2)}%`,
              `分配金額: $${item.allocation.toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
              `回報率: ${(item.performance.totalReturn * 100).toFixed(2)}%`,
              `夏普比率: ${item.performance.sharpeRatio.toFixed(2)}`
            ]
          }
        }
      }
    },
    onClick: (event, activeElements) => {
      if (activeElements.length > 0) {
        const index = activeElements[0].index
        const item = allocationData[index]
        console.log('點擊了策略:', item.name)
        // 可以添加點擊事件處理，例如跳轉到策略詳情頁
      }
    }
  }

  const handleExport = () => {
    const canvas = document.querySelector('.asset-allocation-chart canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `asset-allocation-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  // 計算績效統計
  const portfolioStats = useMemo(() => {
    if (allocationData.length === 0) {
      return { avgReturn: 0, avgSharpe: 0, totalRisk: 0 }
    }

    const weightedReturn = allocationData.reduce((sum, item) =>
      sum + (item.value / 100) * item.performance.totalReturn, 0
    )

    const weightedSharpe = allocationData.reduce((sum, item) =>
      sum + (item.value / 100) * item.performance.sharpeRatio, 0
    )

    const riskDistribution = allocationData.reduce((acc, item) => {
      acc[item.riskLevel] = (acc[item.riskLevel] || 0) + item.value
      return acc
    }, {} as Record<string, number>)

    return {
      weightedReturn,
      weightedSharpe,
      riskDistribution
    }
  }, [allocationData])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 主圖表 */}
      <div className="lg:col-span-2">
        <Card
          title="資產配置分布"
          className="asset-allocation-card"
          extra={
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              title="導出圖表"
            />
          }
        >
          <div className="asset-allocation-chart" style={{ height: '400px' }}>
            {allocationData.length > 0 ? (
              <Pie data={chartData} options={options} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">🥧</div>
                  <div>暫無活躍策略</div>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* 詳情面板 */}
      <div className="space-y-4">
        {/* 總覽統計 */}
        <Card title="投資組合概覽" size="small">
          <div className="space-y-3">
            <Statistic
              title="總價值"
              value={totalValue}
              prefix="$"
              precision={0}
              valueStyle={{ fontSize: '16px' }}
            />
            <Statistic
              title="預期年化回報"
              value={(portfolioStats.weightedReturn * 100)}
              suffix="%"
              precision={2}
              valueStyle={{
                fontSize: '16px',
                color: portfolioStats.weightedReturn >= 0 ? '#3f8600' : '#cf1322'
              }}
            />
            <Statistic
              title="加權夏普比率"
              value={portfolioStats.weightedSharpe}
              precision={2}
              valueStyle={{ fontSize: '16px' }}
            />
          </div>
        </Card>

        {/* 風險分布 */}
        <Card title="風險級別分布" size="small">
          <div className="space-y-2">
            {Object.entries(portfolioStats.riskDistribution).map(([risk, percentage]) => {
              const riskColors = {
                low: '#10B981',
                medium: '#F59E0B',
                high: '#EF4444'
              }
              const riskLabels = {
                low: '低風險',
                medium: '中風險',
                high: '高風險'
              }

              return (
                <div key={risk} className="flex items-center justify-between">
                  <span className="text-sm">{riskLabels[risk as keyof typeof riskLabels]}</span>
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-16 h-2 rounded-full bg-gray-200 relative"
                    >
                      <div
                        className="absolute inset-y-0 left-0 rounded-full"
                        style={{
                          width: `${percentage}%`,
                          backgroundColor: riskColors[risk as keyof typeof riskColors]
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium w-12 text-right">
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        {/* 策略列表 */}
        {showDetails && allocationData.length > 0 && (
          <Card title="策略詳情" size="small">
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {allocationData.map((item, index) => (
                <div key={index} className="border-b border-gray-100 pb-2 last:border-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {item.name}
                    </span>
                    <span className="text-sm text-gray-600">
                      {item.value.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>${item.allocation.toLocaleString('zh-TW', { maximumFractionDigits: 0 })}</span>
                    <span className={item.performance.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {(item.performance.totalReturn * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

export default AssetAllocationChart