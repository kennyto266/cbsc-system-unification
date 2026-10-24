import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface MACDData {
  timestamp: string | number | Date
  macdLine: number
  signalLine: number
  histogram: number
}

export interface MACDChartProps {
  data: MACDData[]
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
    macdLine: string
    signalLine: string
    positiveHistogram: string
    negativeHistogram: string
    grid?: string
  }
  parameters?: {
    fastPeriod?: number
    slowPeriod?: number
    signalPeriod?: number
  }
  showZeroLine?: boolean
  onSignalChange?: (signal: 'bullish' | 'bearish' | 'neutral', index: number) => void
  animationDuration?: number
}

export interface MACDChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const MACDChart = forwardRef<MACDChartRef, MACDChartProps>(({
  data,
  width,
  height = 300,
  title = 'MACD',
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
    macdLine: '#2196F3',
    signalLine: '#FF9800',
    positiveHistogram: '#4CAF50',
    negativeHistogram: '#F44336',
    grid: 'rgba(0, 0, 0, 0.05)',
  },
  parameters = {
    fastPeriod: 12,
    slowPeriod: 26,
    signalPeriod: 9,
  },
  showZeroLine = true,
  onSignalChange,
  animationDuration = 750,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Analyze MACD signals
  const signals = useMemo(() => {
    if (!data || data.length < 2) return []

    return data.map((item, index) => {
      if (index === 0) return 'neutral'

      const prevItem = data[index - 1]
      const currentCross = item.macdLine - item.signalLine
      const prevCross = prevItem.macdLine - prevItem.signalLine

      if (prevCross < 0 && currentCross >= 0) {
        return 'bullish' // MACD crosses above signal line
      } else if (prevCross > 0 && currentCross <= 0) {
        return 'bearish' // MACD crosses below signal line
      }
      return 'neutral'
    })
  }, [data])

  // Transform MACD data to chart format
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const labels = data.map(item => {
      const date = new Date(item.timestamp)
      return date.toLocaleDateString()
    })

    return {
      labels,
      datasets: [
        {
          label: 'MACD Line',
          data: data.map(item => item.macdLine),
          borderColor: colors.macdLine,
          backgroundColor: 'transparent',
          borderWidth: 2,
          type: 'line',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.1,
        },
        {
          label: 'Signal Line',
          data: data.map(item => item.signalLine),
          borderColor: colors.signalLine,
          backgroundColor: 'transparent',
          borderWidth: 2,
          type: 'line',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.1,
        },
        {
          label: 'Histogram',
          data: data.map(item => item.histogram),
          backgroundColor: data.map(item =>
            item.histogram >= 0 ? colors.positiveHistogram : colors.negativeHistogram
          ),
          borderColor: 'transparent',
          borderWidth: 0,
          type: 'bar',
          barPercentage: 0.8,
        },
      ],
    }
  }, [data, colors])

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
        },
        tooltip: {
          enabled: showTooltip,
          callbacks: {
            title: (context: any) => {
              const dataIndex = context[0]?.dataIndex
              const item = data[dataIndex]
              if (!item) return ''
              const date = new Date(item.timestamp)
              return date.toLocaleString()
            },
            label: (context: any) => {
              const dataIndex = context.dataIndex
              const item = data[dataIndex]
              if (!item) return ''

              const value = chartUtils.formatNumber(context.parsed.y)
              const label = context.dataset.label

              if (label === 'Histogram') {
                const signal = signals[dataIndex]
                const signalText = signal === 'bullish' ? '(Bullish)' :
                                 signal === 'bearish' ? '(Bearish)' : '(Neutral)'
                return `${label}: ${value} ${signalText}`
              }

              return `${label}: ${value}`
            },
          },
        },
        annotation: showZeroLine ? {
          annotations: {
            zeroLine: {
              type: 'line',
              yMin: 0,
              yMax: 0,
              borderColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
              borderWidth: 1,
              borderDash: [5, 5],
            },
          },
        } : undefined,
      },
      scales: {
        x: {
          type: 'time',
          time: {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MM/dd',
              week: 'MM/dd',
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
            callback: (value: number) => {
              if (Math.abs(value) < 0.01) {
                return value.toFixed(4)
              }
              return value.toFixed(3)
            },
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onSignalChange) {
          const dataIndex = elements[0].index
          const signal = signals[dataIndex]
          if (signal) {
            onSignalChange(signal as 'bullish' | 'bearish' | 'neutral', dataIndex)
          }
        }
      },
    }
  }, [
    theme,
    showGrid,
    showLegend,
    showTooltip,
    showZeroLine,
    colors,
    data,
    signals,
    onSignalChange,
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

  // Generate subtitle with parameters
  const generatedSubtitle = useMemo(() => {
    if (subtitle) return subtitle
    return `(${parameters.fastPeriod}, ${parameters.slowPeriod}, ${parameters.signalPeriod})`
  }, [subtitle, parameters])

  return (
    <ChartContainer
      title={title}
      subtitle={generatedSubtitle}
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
        type="bar"
        data={chartData}
        options={chartOptions}
        loading={loading}
        error={error}
      />
    </ChartContainer>
  )
})

MACDChart.displayName = 'MACDChart'

export default MACDChart