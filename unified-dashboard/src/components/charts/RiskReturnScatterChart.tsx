import React, { useMemo, useCallback } from 'react'
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ScatterController
} from 'chart.js'
import { Scatter } from 'react-chartjs-2'
import { Card, Select, Space, Button, Switch } from 'antd'
import { DownloadOutlined, DotChartOutlined } from '@ant-design/icons'
import { Strategy, StrategyType, RiskLevel } from '../../types'

// 註冊Chart.js組件
ChartJS.register(
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ScatterController
)

interface StrategyPoint {
  x: number  // 風險 (最大回撤)
  y: number  // 收益 (總回報率)
  strategy: Strategy
}

interface RiskReturnScatterChartProps {
  strategies: Strategy[]
  showQuadrants?: boolean
  showEfficientFrontier?: boolean
  filterType?: StrategyType | 'all'
  onFilterChange?: (type: StrategyType | 'all') => void
}

const RiskReturnScatterChart: React.FC<RiskReturnScatterChartProps> = ({
  strategies,
  showQuadrants = true,
  showEfficientFrontier = true,
  filterType = 'all',
  onFilterChange
}) => {
  const chartData = useMemo(() => {
    let filteredStrategies = strategies.filter(s => s.status === 'active')

    // 類型過濾
    if (filterType !== 'all') {
      filteredStrategies = filteredStrategies.filter(s => s.type === filterType)
    }

    const points: StrategyPoint[] = filteredStrategies.map(strategy => ({
      x: Math.abs(strategy.performance.maxDrawdown) * 100,  // 風險 (回撤百分比)
      y: strategy.performance.totalReturn * 100,           // 收益 (回報百分比)
      strategy
    }))

    // 按類型和風險級別分組
    const groupedPoints = {
      sentiment: points.filter(p => p.strategy.type === 'sentiment'),
      technical: points.filter(p => p.strategy.type === 'technical'),
      momentum: points.filter(p => p.strategy.type === 'momentum'),
      mean_reversion: points.filter(p => p.strategy.type === 'mean_reversion'),
      arbitrage: points.filter(p => p.strategy.type === 'arbitrage')
    }

    const typeColors = {
      sentiment: '#3B82F6',    // blue
      technical: '#10B981',    // green
      momentum: '#F59E0B',     // amber
      mean_reversion: '#9333EA', // purple
      arbitrage: '#EC4899'     // pink
    }

    const datasets = Object.entries(groupedPoints)
      .filter(([_, points]) => points.length > 0)
      .map(([type, points]) => ({
        label: {
          sentiment: '情感策略',
          technical: '技術策略',
          momentum: '動量策略',
          mean_reversion: '均值回歸',
          arbitrage: '套利策略'
        }[type as StrategyType],
        data: points.map(p => ({ x: p.x, y: p.y, strategy: p.strategy })),
        backgroundColor: typeColors[type as StrategyType] + '80',
        borderColor: typeColors[type as StrategyType],
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'circle' as const
      }))

    // 有效前沿線 (模擬)
    const efficientFrontier = showEfficientFrontier ? generateEfficientFrontier(points) : []

    if (efficientFrontier.length > 0) {
      datasets.push({
        label: '有效前沿',
        data: efficientFrontier.map(p => ({ x: p.x, y: p.y })),
        borderColor: '#DC2626',
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 0,
        showLine: true,
        fill: false,
        tension: 0.4,
        borderDash: [5, 5]
      })
    }

    return { datasets }
  }, [strategies, filterType, showEfficientFrontier])

  // 生成模擬的有效前沿線
  const generateEfficientFrontier = (points: StrategyPoint[]) => {
    if (points.length < 2) return []

    const sortedPoints = [...points].sort((a, b) => a.x - b.x)
    const frontier = []

    // 簡單的有效前沿算法
    for (let i = 0; i < sortedPoints.length; i++) {
      let isEfficient = true
      for (let j = 0; j < sortedPoints.length; j++) {
        if (i !== j && sortedPoints[j].x <= sortedPoints[i].x && sortedPoints[j].y >= sortedPoints[i].y) {
          isEfficient = false
          break
        }
      }
      if (isEfficient) {
        frontier.push(sortedPoints[i])
      }
    }

    return frontier
  }

  const options: ChartOptions<'scatter'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'point' as const,
      intersect: false
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
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
        callbacks: {
          title: function(context) {
            const point = context[0].raw as any
            if (point.strategy) {
              return point.strategy.name
            }
            return context[0].dataset.label
          },
          label: function(context) {
            const point = context.raw as any
            if (point.strategy) {
              const riskLabels = {
                low: '低風險',
                medium: '中風險',
                high: '高風險'
              }
              return [
                `風險 (最大回撤): ${context.parsed.x.toFixed(2)}%`,
                `收益 (年化回報): ${context.parsed.y.toFixed(2)}%`,
                `夏普比率: ${point.strategy.performance.sharpeRatio.toFixed(2)}`,
                `勝率: ${(point.strategy.performance.winRate * 100).toFixed(1)}%`,
                `風險級別: ${riskLabels[point.strategy.riskLevel]}`
              ]
            }
            return []
          }
        }
      }
    },
    scales: {
      x: {
        type: 'linear' as const,
        position: 'bottom' as const,
        title: {
          display: true,
          text: '風險 (最大回撤 %)',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: showQuadrants ? function(context) {
            if (context.tick.value === 0) return 'rgba(0, 0, 0, 0.3)'
            return 'rgba(0, 0, 0, 0.05)'
          } : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            return `${value}%`
          }
        }
      },
      y: {
        type: 'linear' as const,
        position: 'left' as const,
        title: {
          display: true,
          text: '收益 (年化回報 %)',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: showQuadrants ? function(context) {
            if (context.tick.value === 0) return 'rgba(0, 0, 0, 0.3)'
            return 'rgba(0, 0, 0, 0.05)'
          } : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            return `${value}%`
          }
        }
      }
    },
    annotation: showQuadrants ? {
      annotations: {
        quadrant1: {
          type: 'box',
          xMin: 0,
          xMax: 'max',
          yMin: 0,
          yMax: 'max',
          backgroundColor: 'rgba(34, 197, 94, 0.05)',
          borderColor: 'transparent'
        },
        quadrant2: {
          type: 'box',
          xMin: 'min',
          xMax: 0,
          yMin: 0,
          yMax: 'max',
          backgroundColor: 'rgba(251, 191, 36, 0.05)',
          borderColor: 'transparent'
        },
        quadrant3: {
          type: 'box',
          xMin: 'min',
          xMax: 0,
          yMin: 'min',
          yMax: 0,
          backgroundColor: 'rgba(239, 68, 68, 0.05)',
          borderColor: 'transparent'
        },
        quadrant4: {
          type: 'box',
          xMin: 0,
          xMax: 'max',
          yMin: 'min',
          yMax: 0,
          backgroundColor: 'rgba(156, 163, 175, 0.05)',
          borderColor: 'transparent'
        }
      }
    } : undefined,
    onClick: (event, activeElements) => {
      if (activeElements.length > 0) {
        const element = activeElements[0]
        const dataset = chartData.datasets[element.datasetIndex]
        const point = dataset.data[element.index] as any
        if (point.strategy) {
          console.log('點擊了策略:', point.strategy)
          // 可以添加點擊事件處理，例如顯示策略詳情
        }
      }
    }
  }

  const handleExport = () => {
    const canvas = document.querySelector('.risk-return-scatter-chart canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `risk-return-scatter-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  // 計算統計信息
  const statistics = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')
    if (activeStrategies.length === 0) {
      return { avgRisk: 0, avgReturn: 0, bestStrategy: null, worstStrategy: null }
    }

    const points = activeStrategies.map(s => ({
      strategy: s,
      risk: Math.abs(s.performance.maxDrawdown) * 100,
      return: s.performance.totalReturn * 100
    }))

    const avgRisk = points.reduce((sum, p) => sum + p.risk, 0) / points.length
    const avgReturn = points.reduce((sum, p) => sum + p.return, 0) / points.length

    const bestStrategy = points.reduce((best, current) =>
      current.return > best.return ? current : best
    ).strategy

    const worstStrategy = points.reduce((worst, current) =>
      current.return < worst.return ? current : worst
    ).strategy

    return { avgRisk, avgReturn, bestStrategy, worstStrategy }
  }, [strategies])

  return (
    <Card
      title="風險收益散點圖"
      className="risk-return-scatter-card"
      extra={
        <Space>
          <Select
            value={filterType}
            onChange={onFilterChange}
            style={{ width: 120 }}
            size="small"
          >
            <Select.Option value="all">全部類型</Select.Option>
            <Select.Option value="sentiment">情感策略</Select.Option>
            <Select.Option value="technical">技術策略</Select.Option>
            <Select.Option value="momentum">動量策略</Select.Option>
            <Select.Option value="mean_reversion">均值回歸</Select.Option>
            <Select.Option value="arbitrage">套利策略</Select.Option>
          </Select>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">象限</span>
            <Switch
              size="small"
              checked={showQuadrants}
              onChange={(checked) => {
                console.log('切換象限顯示:', checked)
                // 這裡需要調用父組件的回調函數
              }}
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">前沿</span>
            <Switch
              size="small"
              checked={showEfficientFrontier}
              onChange={(checked) => {
                console.log('切換有效前沿:', checked)
                // 這裡需要調用父組件的回調函數
              }}
            />
          </div>
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
      <div className="risk-return-scatter-chart" style={{ height: '500px' }}>
        {chartData.datasets.some(d => d.data.length > 0) ? (
          <Scatter data={chartData} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📈</div>
              <div>暫無活躍策略數據</div>
            </div>
          </div>
        )}
      </div>

      {/* 統計信息 */}
      {statistics.bestStrategy && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div className="text-center">
              <div className="text-gray-500">平均風險</div>
              <div className="font-semibold text-lg">{statistics.avgRisk.toFixed(2)}%</div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">平均收益</div>
              <div className="font-semibold text-lg text-green-600">{statistics.avgReturn.toFixed(2)}%</div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">最佳策略</div>
              <div className="font-semibold text-sm truncate" title={statistics.bestStrategy?.name}>
                {statistics.bestStrategy?.name}
              </div>
              <div className="text-xs text-green-600">
                {statistics.bestStrategy && (statistics.bestStrategy.performance.totalReturn * 100).toFixed(2)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">最差策略</div>
              <div className="font-semibold text-sm truncate" title={statistics.worstStrategy?.name}>
                {statistics.worstStrategy?.name}
              </div>
              <div className="text-xs text-red-600">
                {statistics.worstStrategy && (statistics.worstStrategy.performance.totalReturn * 100).toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

export default RiskReturnScatterChart