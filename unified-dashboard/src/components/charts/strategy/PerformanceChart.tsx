import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface PerformanceData {
  date: string | Date
  value: number
  benchmark?: number
  drawdown?: number
}

export interface StrategyPerformance {
  id: string
  name: string
  data: PerformanceData[]
  color: string
}

export interface PerformanceChartProps {
  strategies: StrategyPerformance[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  showBenchmark?: boolean
  showDrawdown?: boolean
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    background?: string
    grid?: string
    benchmark?: string
    drawdown?: string
  }
  chartType?: 'line' | 'area'
  relativePerformance?: boolean
  logScale?: boolean
  onStrategyToggle?: (strategyId: string) => void
  onDataPointClick?: (strategyId: string, data: PerformanceData, index: number) => void
  animationDuration?: number
}

export interface PerformanceChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const PerformanceChart = forwardRef<PerformanceChartRef, PerformanceChartProps>(({
  strategies,
  width,
  height = 400,
  title = 'Strategy Performance',
  subtitle,
  loading,
  error,
  timeRange,
  onTimeRangeChange,
  showBenchmark = true,
  showDrawdown = false,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    background: 'rgba(0, 0, 0, 0.05)',
    grid: 'rgba(0, 0, 0, 0.05)',
    benchmark: '#95a5a6',
    drawdown: '#e74c3c',
  },
  chartType = 'line',
  relativePerformance = false,
  logScale = false,
  onStrategyToggle,
  onDataPointClick,
  animationDuration = 1000,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Calculate performance metrics
  const performanceMetrics = useMemo(() => {
    return strategies.map(strategy => {
      const data = strategy.data
      if (!data || data.length < 2) return null

      const initialValue = data[0].value
      const finalValue = data[data.length - 1].value
      const totalReturn = ((finalValue - initialValue) / initialValue) * 100

      // Calculate max drawdown
      let maxDrawdown = 0
      let peak = initialValue

      for (const point of data) {
        if (point.value > peak) peak = point.value
        const drawdown = ((peak - point.value) / peak) * 100
        if (drawdown > maxDrawdown) maxDrawdown = drawdown
      }

      // Calculate Sharpe ratio (simplified)
      const returns = []
      for (let i = 1; i < data.length; i++) {
        returns.push((data[i].value - data[i - 1].value) / data[i - 1].value)
      }
      const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length
      const stdDev = Math.sqrt(
        returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
      )
      const sharpeRatio = avgReturn / stdDev * Math.sqrt(252) // Annualized

      return {
        strategyId: strategy.id,
        totalReturn,
        maxDrawdown,
        sharpeRatio,
        volatility: stdDev * Math.sqrt(252),
      }
    }).filter(Boolean)
  }, [strategies])

  // Transform performance data to chart format
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

    // Add strategy lines
    strategies.forEach(strategy => {
      const color = strategy.color
      const dataPoints = strategy.data.map(point => ({
        x: new Date(point.date).toLocaleDateString(),
        y: point.value,
      }))

      datasets.push({
        label: strategy.name,
        data: dataPoints,
        borderColor: color,
        backgroundColor: chartType === 'area' ? color + '20' : 'transparent',
        borderWidth: 2,
        fill: chartType === 'area',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      })
    })

    // Add benchmark line
    if (showBenchmark) {
      const benchmarkData = strategies[0]?.data.map(point => point.benchmark).filter(Boolean)
      if (benchmarkData && benchmarkData.length > 0) {
        datasets.push({
          label: 'Benchmark',
          data: strategies[0].data.map(point => ({
            x: new Date(point.date).toLocaleDateString(),
            y: point.benchmark,
          })),
          borderColor: colors.benchmark,
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 3,
        })
      }
    }

    // Add drawdown area if enabled
    if (showDrawdown) {
      const drawdownData = strategies[0]?.data.map(point => point.drawdown).filter(Boolean)
      if (drawdownData && drawdownData.length > 0) {
        datasets.push({
          label: 'Drawdown',
          data: strategies[0].data.map(point => ({
            x: new Date(point.date).toLocaleDateString(),
            y: point.drawdown || 0,
          })),
          borderColor: colors.drawdown,
          backgroundColor: colors.drawdown + '30',
          borderWidth: 1,
          fill: true,
          type: 'line',
          pointRadius: 0,
          pointHoverRadius: 3,
          yAxisID: 'y1',
        })
      }
    }

    return { labels, datasets }
  }, [
    strategies,
    showBenchmark,
    showDrawdown,
    chartType,
    colors,
  ])

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
              const value = chartUtils.formatNumber(context.parsed.y)

              if (datasetLabel === 'Drawdown') {
                const metric = performanceMetrics.find(m => m?.strategyId === strategies[0]?.id)
                return [
                  `${datasetLabel}: ${value}%`,
                  `Max DD: ${metric?.maxDrawdown.toFixed(2)}%`,
                ]
              }

              const strategyIndex = context.datasetIndex
              const strategy = strategies[strategyIndex]
              const metric = performanceMetrics.find(m => m?.strategyId === strategy?.id)

              return [
                `${datasetLabel}: ${value}`,
                `Return: ${metric?.totalReturn.toFixed(2)}%`,
                `Sharpe: ${metric?.sharpeRatio.toFixed(2)}`,
              ]
            },
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
          type: logScale ? 'logarithmic' : 'linear',
          position: 'left',
          grid: {
            display: showGrid,
            color: gridColor,
          },
          ticks: {
            color: textColor,
            callback: (value: number) => {
              if (logScale) {
                return value.toExponential(2)
              }
              return chartUtils.formatNumber(value)
            },
          },
        },
        ...(showDrawdown ? {
          y1: {
            type: 'linear',
            position: 'right',
            grid: {
              display: false,
            },
            ticks: {
              color: colors.drawdown,
              callback: (value: number) => `${value}%`,
            },
          },
        } : {}),
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onDataPointClick) {
          const { datasetIndex, index } = elements[0]
          const strategy = strategies[datasetIndex]
          if (strategy && strategy.data[index]) {
            onDataPointClick(strategy.id, strategy.data[index], index)
          }
        }
      },
    }
  }, [
    theme,
    showGrid,
    showLegend,
    showTooltip,
    logScale,
    showDrawdown,
    colors,
    strategies,
    performanceMetrics,
    onStrategyToggle,
    onDataPointClick,
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

PerformanceChart.displayName = 'PerformanceChart'

export default PerformanceChart