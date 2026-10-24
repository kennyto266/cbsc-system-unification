import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface VolumeData {
  timestamp: string | number | Date
  volume: number
  price?: number // Optional price for coloring
  buyVolume?: number
  sellVolume?: number
}

export interface VolumeChartProps {
  data: VolumeData[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  chartType?: 'bar' | 'histogram'
  showGrid?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    up: string
    down: string
    neutral: string
    grid?: string
  }
  onBarClick?: (data: VolumeData, index: number) => void
  showMovingAverage?: boolean
  movingAveragePeriod?: number
  showValueLabel?: boolean
  stackedBars?: boolean // Show buy/sell volume stacked
  animationDuration?: number
}

export interface VolumeChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const VolumeChart = forwardRef<VolumeChartRef, VolumeChartProps>(({
  data,
  width,
  height = 200,
  title = 'Volume',
  subtitle,
  loading,
  error,
  timeRange,
  onTimeRangeChange,
  chartType = 'bar',
  showGrid = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    up: '#26a69a',
    down: '#ef5350',
    neutral: '#757575',
    grid: 'rgba(0, 0, 0, 0.05)',
  },
  onBarClick,
  showMovingAverage = false,
  movingAveragePeriod = 20,
  showValueLabel = false,
  stackedBars = false,
  animationDuration = 500,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Calculate moving average
  const movingAverage = useMemo(() => {
    if (!showMovingAverage || !data || data.length < movingAveragePeriod) {
      return []
    }

    const ma: number[] = []
    for (let i = movingAveragePeriod - 1; i < data.length; i++) {
      const sum = data.slice(i - movingAveragePeriod + 1, i + 1)
        .reduce((acc, item) => acc + item.volume, 0)
      ma.push(sum / movingAveragePeriod)
    }
    return ma
  }, [data, showMovingAverage, movingAveragePeriod])

  // Transform volume data to chart format
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const labels = data.map(item => {
      const date = new Date(item.timestamp)
      return date.toLocaleDateString()
    })

    // Determine bar colors based on price movement or buy/sell volume
    const getBarColor = (item: VolumeData, index: number) => {
      if (stackedBars && item.buyVolume !== undefined && item.sellVolume !== undefined) {
        return [colors.up, colors.down]
      }
      if (item.price) {
        // If we have price data, compare with previous price
        if (index === 0) return colors.neutral
        const prevPrice = data[index - 1].price
        return item.price >= prevPrice ? colors.up : colors.down
      }
      return colors.neutral
    }

    const datasets = []

    if (stackedBars && data.some(item => item.buyVolume !== undefined)) {
      // Create separate datasets for buy and sell volume
      datasets.push(
        {
          label: 'Buy Volume',
          data: data.map(item => item.buyVolume || 0),
          backgroundColor: colors.up,
          borderColor: colors.up,
          borderWidth: 0,
          type: 'bar',
          stack: 'volume',
        },
        {
          label: 'Sell Volume',
          data: data.map(item => item.sellVolume || 0),
          backgroundColor: colors.down,
          borderColor: colors.down,
          borderWidth: 0,
          type: 'bar',
          stack: 'volume',
        }
      )
    } else {
      // Single volume dataset
      datasets.push({
        label: 'Volume',
        data: data.map(item => item.volume),
        backgroundColor: data.map((item, index) => {
          const color = getBarColor(item, index)
          return Array.isArray(color) ? color[0] : color
        }),
        borderColor: data.map((item, index) => {
          const color = getBarColor(item, index)
          return Array.isArray(color) ? color[0] : color
        }),
        borderWidth: 0,
        type: 'bar',
      })
    }

    // Add moving average line
    if (showMovingAverage && movingAverage.length > 0) {
      datasets.push({
        label: `MA(${movingAveragePeriod})`,
        data: new Array(movingAveragePeriod - 1).fill(null).concat(movingAverage),
        borderColor: '#ff9800',
        backgroundColor: 'transparent',
        borderWidth: 2,
        type: 'line',
        pointRadius: 0,
        tension: 0.1,
      })
    }

    return { labels, datasets }
  }, [data, colors, stackedBars, showMovingAverage, movingAverage, movingAveragePeriod])

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
          display: stackedBars || showMovingAverage,
          position: 'top',
          labels: {
            color: textColor,
            usePointStyle: true,
            padding: 10,
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

              const volume = chartUtils.formatNumber(item.volume)
              const label = context.dataset.label || 'Volume'

              if (label.includes('Buy')) {
                return `Buy Volume: ${chartUtils.formatNumber(item.buyVolume || 0)}`
              } else if (label.includes('Sell')) {
                return `Sell Volume: ${chartUtils.formatNumber(item.sellVolume || 0)}`
              } else if (label.includes('MA')) {
                return `${label}: ${chartUtils.formatNumber(context.parsed.y)}`
              }

              return `${label}: ${volume}`
            },
          },
        },
        datalabels: showValueLabel ? {
          display: (context: any) => {
            // Show labels only for significant volumes
            return context.datasetIndex === 0 && context.parsed.y > 0
          },
          color: textColor,
          font: {
            size: 10,
          },
          formatter: (value: number) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toFixed(0)
          },
        } : false,
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
            maxTicksLimit: 8,
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
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
              if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
              return value.toFixed(0)
            },
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onBarClick) {
          const dataIndex = elements[0].index
          const barData = data[dataIndex]
          if (barData) {
            onBarClick(barData, dataIndex)
          }
        }
      },
    }
  }, [
    theme,
    showGrid,
    showTooltip,
    showValueLabel,
    colors,
    data,
    onBarClick,
    animationDuration,
    stackedBars,
    showMovingAverage,
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
      showZoom={false}
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

VolumeChart.displayName = 'VolumeChart'

export default VolumeChart