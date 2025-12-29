import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface BollingerBandsData {
  timestamp: string | number | Date
  price: number
  upperBand: number
  middleBand: number
  lowerBand: number
}

export interface BollingerBandsChartProps {
  data: BollingerBandsData[]
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
    price: string
    upperBand: string
    middleBand: string
    lowerBand: string
    fill: string
    grid?: string
  }
  parameters?: {
    period?: number
    standardDeviations?: number
  }
  showPriceLine?: boolean
  fillBands?: boolean
  fillOpacity?: number
  onBandTouch?: (band: 'upper' | 'lower', price: number, index: number) => void
  animationDuration?: number
  lineWidth?: number
}

export interface BollingerBandsChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const BollingerBandsChart = forwardRef<BollingerBandsChartRef, BollingerBandsChartProps>(({
  data,
  width,
  height = 400,
  title = 'Bollinger Bands',
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
    price: '#2196F3',
    upperBand: '#F44336',
    middleBand: '#FFC107',
    lowerBand: '#4CAF50',
    fill: 'rgba(33, 150, 243, 0.1)',
    grid: 'rgba(0, 0, 0, 0.05)',
  },
  parameters = {
    period: 20,
    standardDeviations: 2,
  },
  showPriceLine = true,
  fillBands = true,
  fillOpacity = 0.1,
  onBandTouch,
  animationDuration = 750,
  lineWidth = 2,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Detect band touches
  const bandTouches = useMemo(() => {
    if (!data) return []

    return data.map((item, index) => {
      const tolerance = 0.001 // Small tolerance for floating point comparison
      if (Math.abs(item.price - item.upperBand) < item.price * tolerance) {
        return { type: 'upper', price: item.price, index }
      } else if (Math.abs(item.price - item.lowerBand) < item.price * tolerance) {
        return { type: 'lower', price: item.price, index }
      }
      return null
    }).filter(Boolean) as Array<{ type: 'upper' | 'lower', price: number, index: number }>
  }, [data])

  // Calculate bandwidth and position
  const bandMetrics = useMemo(() => {
    if (!data || data.length === 0) return { bandwidth: [], position: [] }

    return data.reduce((acc, item) => {
      const bandwidth = ((item.upperBand - item.lowerBand) / item.middleBand) * 100
      const position = ((item.price - item.lowerBand) / (item.upperBand - item.lowerBand)) * 100

      acc.bandwidth.push(bandwidth)
      acc.position.push(position)
      return acc
    }, { bandwidth: [] as number[], position: [] as number[] })
  }, [data])

  // Transform Bollinger Bands data to chart format
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const labels = data.map(item => {
      const date = new Date(item.timestamp)
      return date.toLocaleDateString()
    })

    const datasets = []

    // Add upper band
    datasets.push({
      label: 'Upper Band',
      data: data.map(item => item.upperBand),
      borderColor: colors.upperBand,
      backgroundColor: 'transparent',
      borderWidth: lineWidth,
      type: 'line',
      pointRadius: 0,
      pointHoverRadius: 3,
      tension: 0.1,
    })

    // Add middle band (SMA)
    datasets.push({
      label: 'Middle Band (SMA)',
      data: data.map(item => item.middleBand),
      borderColor: colors.middleBand,
      backgroundColor: 'transparent',
      borderWidth: lineWidth,
      type: 'line',
      pointRadius: 0,
      pointHoverRadius: 3,
      tension: 0.1,
    })

    // Add lower band with fill
    datasets.push({
      label: 'Lower Band',
      data: data.map(item => item.lowerBand),
      borderColor: colors.lowerBand,
      backgroundColor: fillBands ? colors.fill + Math.round(fillOpacity * 255).toString(16) : 'transparent',
      borderWidth: lineWidth,
      type: 'line',
      pointRadius: 0,
      pointHoverRadius: 3,
      tension: 0.1,
      fill: fillBands ? '-1' : false, // Fill to previous dataset (middle band)
    })

    // Add fill between upper and middle bands
    if (fillBands) {
      datasets.unshift({
        label: 'Upper Fill',
        data: data.map(item => item.upperBand),
        borderColor: 'transparent',
        backgroundColor: colors.fill + Math.round(fillOpacity * 255).toString(16),
        borderWidth: 0,
        type: 'line',
        pointRadius: 0,
        fill: '-1', // Fill to middle band
      })
    }

    // Add price line
    if (showPriceLine) {
      datasets.push({
        label: 'Price',
        data: data.map(item => item.price),
        borderColor: colors.price,
        backgroundColor: 'transparent',
        borderWidth: lineWidth + 1,
        type: 'line',
        pointRadius: 0,
        pointHoverRadius: 3,
        tension: 0.1,
      })
    }

    // Mark band touches
    if (bandTouches.length > 0) {
      const touchData = bandTouches.map(touch => ({
        x: data[touch.index].timestamp,
        y: touch.price,
      }))

      datasets.push({
        label: 'Band Touches',
        data: touchData,
        backgroundColor: touch.type === 'upper' ? colors.upperBand : colors.lowerBand,
        borderColor: '#fff',
        borderWidth: 2,
        type: 'scatter',
        pointRadius: 6,
        pointHoverRadius: 8,
      })
    }

    return { labels, datasets }
  }, [
    data,
    colors,
    showPriceLine,
    fillBands,
    fillOpacity,
    lineWidth,
    bandTouches,
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

              const label = context.dataset.label
              const value = chartUtils.formatNumber(context.parsed.y)

              if (label === 'Price') {
                const distance = item.price - item.middleBand
                const distancePercent = (Math.abs(distance) / (item.upperBand - item.lowerBand)) * 100
                return [
                  `${label}: ${value}`,
                  `Distance from SMA: ${chartUtils.formatNumber(distance)} (${distancePercent.toFixed(1)}%)`,
                ]
              }

              if (label.includes('Band')) {
                const bandwidth = bandMetrics.bandwidth[dataIndex]
                if (label.includes('Upper') || label.includes('Lower')) {
                  return [
                    `${label}: ${value}`,
                    `Bandwidth: ${bandwidth?.toFixed(2)}%`,
                  ]
                }
              }

              return `${label}: ${value}`
            },
          },
        },
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
            callback: (value: number) => chartUtils.formatNumber(value),
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onBandTouch) {
          const dataIndex = elements[0].index
          const touch = bandTouches.find(t => t.index === dataIndex)
          if (touch) {
            onBandTouch(touch.type, touch.price, dataIndex)
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
    data,
    bandMetrics,
    bandTouches,
    onBandTouch,
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
    return `Period: ${parameters.period} | StdDev: ${parameters.standardDeviations}`
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
        type="line"
        data={chartData}
        options={chartOptions}
        loading={loading}
        error={error}
      />
    </ChartContainer>
  )
})

BollingerBandsChart.displayName = 'BollingerBandsChart'

export default BollingerBandsChart