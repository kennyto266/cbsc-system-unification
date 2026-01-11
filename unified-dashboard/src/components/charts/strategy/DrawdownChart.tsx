import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface DrawdownData {
  date: string | Date
  value: number
  drawdown: number
  underwaterPeriod?: number
}

export interface StrategyDrawdown {
  id: string
  name: string
  data: DrawdownData[]
  color: string
}

export interface DrawdownChartProps {
  strategies: StrategyDrawdown[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    grid?: string
    zeroLine?: string
  }
  chartType?: 'area' | 'line'
  showUnderwaterPeriods?: boolean
  showRecoveryPeriods?: boolean
  onStrategyToggle?: (strategyId: string) => void
  onDrawdownPeriodClick?: (strategyId: string, startIndex: number, endIndex: number) => void
  animationDuration?: number
}

export interface DrawdownChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const DrawdownChart = forwardRef<DrawdownChartRef, DrawdownChartProps>(({
  strategies,
  width,
  height = 300,
  title = 'Strategy Drawdown',
  subtitle,
  loading,
  error,
  timeRange,
  onTimeRangeChange,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    grid: 'rgba(0, 0, 0, 0.05)',
    zeroLine: 'rgba(231, 76, 60, 0.5)',
  },
  chartType = 'area',
  showUnderwaterPeriods = true,
  showRecoveryPeriods = false,
  onStrategyToggle,
  onDrawdownPeriodClick,
  animationDuration = 750,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Calculate drawdown statistics
  const drawdownStats = useMemo(() => {
    return strategies.map(strategy => {
      const data = strategy.data
      if (!data || data.length === 0) return null

      const drawdowns = data.map(d => d.drawdown || 0)
      const maxDrawdown = Math.max(...drawdowns)
      const avgDrawdown = drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length

      // Calculate underwater periods
      let underwaterPeriods: Array<{ start: number; end: number; depth: number }> = []
      let currentPeriod: { start: number; depth: number } | null = null

      data.forEach((point, index) => {
        if (point.drawdown && point.drawdown > 0) {
          if (!currentPeriod) {
            currentPeriod = { start: index, depth: point.drawdown }
          } else {
            currentPeriod.depth = Math.max(currentPeriod.depth, point.drawdown)
          }
        } else if (currentPeriod) {
          underwaterPeriods.push({
            start: currentPeriod.start,
            end: index - 1,
            depth: currentPeriod.depth,
          })
          currentPeriod = null
        }
      })

      // Handle if period extends to end
      if (currentPeriod) {
        underwaterPeriods.push({
          start: currentPeriod.start,
          end: data.length - 1,
          depth: currentPeriod.depth,
        })
      }

      // Calculate recovery periods
      const recoveryPeriods = underwaterPeriods
        .map(period => {
          const peakValue = data[period.start].value
          for (let i = period.end + 1; i < data.length; i++) {
            if (data[i].value >= peakValue) {
              return { start: period.end, end: i, duration: i - period.end }
            }
          }
          return null
        })
        .filter(Boolean) as Array<{ start: number; end: number; duration: number }>

      const avgRecoveryTime = recoveryPeriods.length > 0
        ? recoveryPeriods.reduce((sum, p) => sum + p.duration, 0) / recoveryPeriods.length
        : 0

      return {
        strategyId: strategy.id,
        maxDrawdown,
        avgDrawdown,
        underwaterPeriods: underwaterPeriods.length,
        avgRecoveryTime,
      }
    }).filter(Boolean)
  }, [strategies])

  // Transform drawdown data to chart format
  const chartData = useMemo(() => {
    if (!strategies || strategies.length === 0) {
      return { labels: [], datasets: [] }
    }

    // Get all unique dates
    const allDates = new Set<string>()
    strategies.forEach(strategy => {
      strategy.data.forEach(point => {
        allDates.add(new Date(point.date).toLocaleDateString())
      })
    })
    const labels = Array.from(allDates).sort()

    const datasets = []

    // Add drawdown areas for each strategy
    strategies.forEach(strategy => {
      datasets.push({
        label: strategy.name,
        data: strategy.data.map(point => ({
          x: new Date(point.date).toLocaleDateString(),
          y: point.drawdown || 0,
        })),
        borderColor: strategy.color,
        backgroundColor: chartType === 'area' ? strategy.color + '40' : 'transparent',
        borderWidth: 2,
        fill: chartType === 'area',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      })
    })

    // Add underwater period annotations if enabled
    if (showUnderwaterPeriods) {
      // This would be handled in the chart options as annotations
    }

    return { labels, datasets }
  }, [
    strategies,
    chartType,
    showUnderwaterPeriods,
  ])

  // Generate underwater period annotations
  const underwaterAnnotations = useMemo(() => {
    if (!showUnderwaterPeriods) return {}

    const annotations: any = {}

    strategies.forEach((strategy, strategyIndex) => {
      const data = strategy.data
      let currentPeriod: { start: number; depth: number } | null = null
      let periodCount = 0

      data.forEach((point, index) => {
        if (point.drawdown && point.drawdown > 0) {
          if (!currentPeriod) {
            currentPeriod = { start: index, depth: point.drawdown }
          } else {
            currentPeriod.depth = Math.max(currentPeriod.depth, point.drawdown)
          }
        } else if (currentPeriod) {
          // End of underwater period
          annotations[`underwater_${strategyId}_${periodCount}`] = {
            type: 'box',
            xMin: data[currentPeriod.start].date,
            xMax: data[index - 1].date,
            yMin: 0,
            yMax: currentPeriod.depth,
            backgroundColor: `${strategy.color}20`,
            borderColor: strategy.color,
            borderWidth: 1,
            borderDash: [5, 5],
          }
          periodCount++
          currentPeriod = null
        }
      })
    })

    return annotations
  }, [strategies, showUnderwaterPeriods])

  // Chart options
  const chartOptions = useMemo(() => {
    const isDark = theme === 'dark'
    const textColor = isDark ? '#9ca3af' : '#374151'
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'

    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: animationDuration,
        easing: 'easeInOutQuart',
      },
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        legend: {
          display: showLegend,
          position: 'top',
          labels: {
            color: textColor,
            usePointStyle: true,
            padding: 15,
            font: {
              size: 11,
            },
          },
          onClick: (e: any, legendItem: any, legend: any) => {
            const index = legendItem.datasetIndex
            const strategy = strategies[index]
            if (strategy && onStrategyToggle) {
              onStrategyToggle(strategy.id)
            }
          },
        },
        tooltip: {
          enabled: showTooltip,
          callbacks: {
            title: (context: any) => {
              const date = context[0]?.label
              return date ? `Date: ${date}` : ''
            },
            label: (context: any) => {
              const datasetLabel = context.dataset.label
              const value = context.parsed.y
              const dataIndex = context.dataIndex
              const strategy = strategies[context.datasetIndex]

              const label = `${datasetLabel}: ${value.toFixed(2)}%`

              if (strategy && strategy.data[dataIndex]) {
                const point = strategy.data[dataIndex]
                if (point.underwaterPeriod) {
                  return [
                    label,
                    `Underwater: ${point.underwaterPeriod} periods`,
                  ]
                }
              }

              return label
            },
          },
        },
        annotation: {
          annotations: {
            zeroLine: {
              type: 'line',
              yMin: 0,
              yMax: 0,
              borderColor: colors.zeroLine,
              borderWidth: 2,
            },
            ...underwaterAnnotations,
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            displayFormats: {
              day: 'MM/dd',
              week: 'MM/dd',
              month: 'yyyy-MM',
            },
          },
          grid: {
            display: showGrid,
            color: gridColor,
          },
          ticks: {
            color: textColor,
            maxTicksLimit: 10,
            autoSkip: true,
          },
        },
        y: {
          position: 'right',
          grid: {
            display: showGrid,
            color: gridColor,
          },
          ticks: {
            color: textColor,
            callback: (value: number) => `${value}%`,
          },
          title: {
            display: true,
            text: 'Drawdown (%)',
            color: textColor,
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onDrawdownPeriodClick) {
          const { datasetIndex, index } = elements[0]
          const strategy = strategies[datasetIndex]
          if (strategy) {
            // Find the underwater period for this click
            const stats = drawdownStats[datasetIndex]
            if (stats) {
              onDrawdownPeriodClick(strategy.id, index - 5, index + 5) // Approximate period
            }
          }
        }
      },
    }
  }, [
    theme,
    showGrid,
    showLegend,
    showTooltip,
    colors,
    strategies,
    drawdownStats,
    underwaterAnnotations,
    onStrategyToggle,
    onDrawdownPeriodClick,
    animationDuration,
  ])

  // Chart ref methods
  useImperativeHandle(ref, () => ({
    exportChart: async (options?: any) => {
      if (chartRef.current) {
        // Implementation for exporting
        console.log('Exporting chart with options:', options)
      }
    },
    getChartInstance: () => chartRef.current?.getChartInstance(),
    update: () => chartRef.current?.update(),
    resetZoom: () => chartRef.current?.resetZoom(),
    zoomIn: () => chartRef.current?.zoomIn(),
    zoomOut: () => chartRef.current?.zoomOut(),
  }), [])

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      loading={loading}
      error={error}
      timeRange={timeRange}
      onTimeRangeChange={onTimeRangeChange}
      height={height}
      showZoom={true}
      showExportButton={true}
      refreshable={true}
      chartRef={chartRef}
    >
      <Chart
        ref={chartRef}
        type="line"
        data={chartData}
        options={chartOptions}
        loading={loading}
        error={error}
      />
    </ChartContainer>
  )
})

DrawdownChart.displayName = 'DrawdownChart'

export default DrawdownChart