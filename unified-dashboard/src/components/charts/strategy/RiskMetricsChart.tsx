import React, { useMemo, useCallback } from 'react'
import { Radar, Bar } from 'react-chartjs-2'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface RiskMetrics {
  sharpeRatio: number
  sortinoRatio: number
  maxDrawdown: number
  volatility: number
  var95: number // Value at Risk 95%
  skewness: number
  kurtosis: number
  beta: number
  alpha: number
  informationRatio: number
  calmarRatio: number
  winRate: number
  profitFactor: number
}

export interface StrategyRisk {
  id: string
  name: string
  metrics: RiskMetrics
  color: string
}

export interface RiskMetricsChartProps {
  strategies: StrategyRisk[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  chartType?: 'radar' | 'bar' | 'comparison'
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    grid?: string
    benchmark?: string
  }
  metrics?: Array<keyof RiskMetrics>
  normalizeValues?: boolean
  benchmarkValues?: Partial<RiskMetrics>
  onMetricClick?: (metric: keyof RiskMetrics, strategyId: string) => void
  animationDuration?: number
  maxStrategies?: number
}

export interface RiskMetricsChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const RiskMetricsChart = forwardRef<RiskMetricsChartRef, RiskMetricsChartProps>(({
  strategies,
  width,
  height = 400,
  title = 'Risk Metrics Analysis',
  subtitle,
  loading,
  error,
  chartType = 'radar',
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    grid: 'rgba(0, 0, 0, 0.05)',
    benchmark: '#95a5a6',
  },
  metrics = ['sharpeRatio', 'sortinoRatio', 'maxDrawdown', 'volatility', 'winRate', 'profitFactor'],
  normalizeValues = true,
  benchmarkValues,
  onMetricClick,
  animationDuration = 750,
  maxStrategies = 5,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Limit strategies to display
  const displayStrategies = useMemo(() => {
    return strategies.slice(0, maxStrategies)
  }, [strategies, maxStrategies])

  // Normalize metrics values for better visualization
  const normalizedMetrics = useMemo(() => {
    if (!normalizeValues) return { strategies: displayStrategies, benchmark: benchmarkValues }

    // Define min/max for normalization
    const ranges: Record<keyof RiskMetrics, { min: number; max: number; invert?: boolean }> = {
      sharpeRatio: { min: -2, max: 5 },
      sortinoRatio: { min: -2, max: 5 },
      maxDrawdown: { min: 0, max: 100, invert: true }, // Lower is better
      volatility: { min: 0, max: 100, invert: true }, // Lower is better
      var95: { min: 0, max: 20, invert: true }, // Lower is better
      skewness: { min: -3, max: 3 },
      kurtosis: { min: 0, max: 10 },
      beta: { min: 0, max: 3 },
      alpha: { min: -0.5, max: 1 },
      informationRatio: { min: -1, max: 2 },
      calmarRatio: { min: -5, max: 5 },
      winRate: { min: 0, max: 100 },
      profitFactor: { min: 0, max: 5 },
    }

    const normalizeValue = (value: number, metric: keyof RiskMetrics): number => {
      const range = ranges[metric]
      if (!range) return value

      const normalized = (value - range.min) / (range.max - range.min)
      return range.invert ? 1 - normalized : normalized
    }

    const normalizedStrategies = displayStrategies.map(strategy => ({
      ...strategy,
      metrics: Object.entries(strategy.metrics).reduce((acc, [key, value]) => {
        acc[key as keyof RiskMetrics] = normalizeValue(value, key as keyof RiskMetrics)
        return acc
      }, {} as RiskMetrics),
    }))

    const normalizedBenchmark = benchmarkValues
      ? Object.entries(benchmarkValues).reduce((acc, [key, value]) => {
          if (value !== undefined) {
            acc[key as keyof RiskMetrics] = normalizeValue(value, key as keyof RiskMetrics)
          }
          return acc
        }, {} as Partial<RiskMetrics>)
      : undefined

    return { strategies: normalizedStrategies, benchmark: normalizedBenchmark }
  }, [displayStrategies, benchmarkValues, normalizeValues])

  // Metric labels for display
  const metricLabels: Record<keyof RiskMetrics, string> = {
    sharpeRatio: 'Sharpe Ratio',
    sortinoRatio: 'Sortino Ratio',
    maxDrawdown: 'Max Drawdown',
    volatility: 'Volatility',
    var95: 'VaR (95%)',
    skewness: 'Skewness',
    kurtosis: 'Kurtosis',
    beta: 'Beta',
    alpha: 'Alpha',
    informationRatio: 'Information Ratio',
    calmarRatio: 'Calmar Ratio',
    winRate: 'Win Rate',
    profitFactor: 'Profit Factor',
  }

  // Transform data for radar chart
  const radarData = useMemo(() => {
    if (chartType !== 'radar') return null

    const labels = metrics.map(m => metricLabels[m] || m)
    const datasets = normalizedMetrics.strategies.map(strategy => ({
      label: strategy.name,
      data: metrics.map(m => strategy.metrics[m] || 0),
      borderColor: strategy.color,
      backgroundColor: strategy.color + '40',
      borderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
    }))

    if (normalizedMetrics.benchmark) {
      datasets.push({
        label: 'Benchmark',
        data: metrics.map(m => (normalizedMetrics.benchmark as any)?.[m] || 0),
        borderColor: colors.benchmark,
        backgroundColor: colors.benchmark + '40',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 3,
        pointHoverRadius: 5,
      })
    }

    return { labels, datasets }
  }, [chartType, metrics, normalizedMetrics, metricLabels, colors.benchmark])

  // Transform data for bar chart
  const barData = useMemo(() => {
    if (chartType !== 'bar') return null

    const labels = metrics.map(m => metricLabels[m] || m)
    const datasets = normalizedMetrics.strategies.map((strategy, index) => ({
      label: strategy.name,
      data: metrics.map(m => strategy.metrics[m] || 0),
      backgroundColor: strategy.color,
      borderColor: strategy.color,
      borderWidth: 1,
    }))

    return { labels, datasets }
  }, [chartType, metrics, normalizedMetrics, metricLabels])

  // Transform data for comparison chart
  const comparisonData = useMemo(() => {
    if (chartType !== 'comparison') return null

    const datasets = [
      {
        label: 'Sharpe Ratio',
        data: normalizedMetrics.strategies.map(s => s.metrics.sharpeRatio),
        backgroundColor: '#3498db',
      },
      {
        label: 'Max Drawdown',
        data: normalizedMetrics.strategies.map(s => s.metrics.maxDrawdown),
        backgroundColor: '#e74c3c',
      },
      {
        label: 'Win Rate',
        data: normalizedMetrics.strategies.map(s => s.metrics.winRate),
        backgroundColor: '#2ecc71',
      },
      {
        label: 'Profit Factor',
        data: normalizedMetrics.strategies.map(s => s.metrics.profitFactor),
        backgroundColor: '#f39c12',
      },
    ]

    return {
      labels: normalizedMetrics.strategies.map(s => s.name),
      datasets,
    }
  }, [chartType, normalizedMetrics])

  // Chart options based on type
  const chartOptions = useMemo(() => {
    const isDark = theme === 'dark'
    const textColor = isDark ? '#9ca3af' : '#374151'
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: animationDuration,
        easing: 'easeInOutQuart',
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
        },
        tooltip: {
          enabled: showTooltip,
        },
      },
    }

    if (chartType === 'radar') {
      return {
        ...baseOptions,
        scales: {
          r: {
            beginAtZero: true,
            max: 1,
            grid: {
              color: gridColor,
            },
            angleLines: {
              color: gridColor,
            },
            pointLabels: {
              color: textColor,
              font: {
                size: 10,
              },
            },
            ticks: {
              color: textColor,
              backdropColor: 'transparent',
            },
          },
        },
      }
    } else if (chartType === 'bar' || chartType === 'comparison') {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: textColor,
              font: {
                size: 11,
              },
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: gridColor,
            },
            ticks: {
              color: textColor,
              callback: (value: number) => {
                if (normalizeValues) {
                  return (value * 100).toFixed(0) + '%'
                }
                return chartUtils.formatNumber(value)
              },
            },
          },
        },
      }
    }

    return baseOptions
  }, [
    chartType,
    theme,
    showLegend,
    showTooltip,
    gridColor,
    textColor,
    normalizeValues,
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

  // Render based on chart type
  const renderChart = () => {
    if (chartType === 'radar' && radarData) {
      return (
        <Radar
          ref={chartRef}
          data={radarData}
          options={chartOptions}
        />
      )
    } else if ((chartType === 'bar' || chartType === 'comparison') && (barData || comparisonData)) {
      return (
        <Bar
          ref={chartRef}
          data={barData || comparisonData}
          options={chartOptions}
        />
      )
    }
    return null
  }

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      loading={loading}
      error={error}
      height={height}
      showZoom={false}
      showExportButton={true}
      refreshable={true}
      chartRef={chartRef}
    >
      {renderChart()}
    </ChartContainer>
  )
})

RiskMetricsChart.displayName = 'RiskMetricsChart'

export default RiskMetricsChart