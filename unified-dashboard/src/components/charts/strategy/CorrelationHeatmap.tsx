import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface CorrelationData {
  [strategyId: string]: {
    [strategyId: string]: number
  }
}

export interface StrategyInfo {
  id: string
  name: string
  color: string
}

export interface CorrelationHeatmapProps {
  correlationData: CorrelationData
  strategies: StrategyInfo[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    positive?: string
    negative?: string
    neutral?: string
  }
  colorScale?: 'diverging' | 'sequential'
  correlationRange?: { min: number; max: number }
  showValues?: boolean
  valueFormat?: 'decimal' | 'percentage'
  onCellClick?: (strategy1: string, strategy2: string, correlation: number) => void
  animationDuration?: number
  cellSize?: number
  fontSize?: number
}

export interface CorrelationHeatmapRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const CorrelationHeatmap = forwardRef<CorrelationHeatmapRef, CorrelationHeatmapProps>(({
  correlationData,
  strategies,
  width,
  height = 400,
  title = 'Strategy Correlation Matrix',
  subtitle,
  loading,
  error,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    positive: '#2ecc71',
    negative: '#e74c3c',
    neutral: '#95a5a6',
  },
  colorScale = 'diverging',
  correlationRange = { min: -1, max: 1 },
  showValues = true,
  valueFormat = 'decimal',
  onCellClick,
  animationDuration = 750,
  cellSize = 40,
  fontSize = 11,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Generate color for correlation value
  const getCorrelationColor = useCallback((value: number): string => {
    const { min, max } = correlationRange
    const normalized = (value - min) / (max - min)

    if (colorScale === 'diverging') {
      // Red for negative, white for neutral, green for positive
      if (value < 0) {
        const intensity = Math.abs(normalized * 2 - 1)
        return `rgba(231, 76, 60, ${intensity})`
      } else {
        const intensity = normalized * 2
        return `rgba(46, 204, 113, ${intensity})`
      }
    } else {
      // Sequential scale
      if (value > 0) {
        return `${colors.positive}${Math.round(normalized * 255).toString(16).padStart(2, '0')}`
      } else {
        return `${colors.negative}${Math.round(Math.abs(normalized) * 255).toString(16).padStart(2, '0')}`
      }
    }
  }, [colorScale, colors, correlationRange])

  // Format correlation value
  const formatValue = useCallback((value: number): string => {
    if (valueFormat === 'percentage') {
      return `${(value * 100).toFixed(1)}%`
    }
    return value.toFixed(3)
  }, [valueFormat])

  // Transform correlation data to chart format
  const chartData = useMemo(() => {
    if (!correlationData || !strategies || strategies.length === 0) {
      return { labels: [], datasets: [] }
    }

    const n = strategies.length
    const labels = strategies.map(s => s.name)
    const data: Array<{ x: number; y: number; v: number; c: string; l?: string }> = []

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        const value = correlationData[strategies[i].id]?.[strategies[j].id] || 0
        const color = getCorrelationColor(value)
        const label = showValues ? formatValue(value) : undefined

        data.push({
          x: j,
          y: i,
          v: value,
          c: color,
          l: label,
        })
      }
    }

    return {
      labels,
      datasets: [
        {
          label: 'Correlation',
          data: data,
          backgroundColor: data.map(d => d.c),
          borderWidth: 1,
          borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          width: (context: any) => {
            return cellSize - 2
          },
          height: (context: any) => {
            return cellSize - 2
          },
        },
      ],
    }
  }, [
    correlationData,
    strategies,
    getCorrelationColor,
    formatValue,
    showValues,
    theme,
    cellSize,
  ])

  // Chart options
  const chartOptions = useMemo(() => {
    const isDark = theme === 'dark'
    const textColor = isDark ? '#9ca3af' : '#374151'

    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: animationDuration,
        easing: 'easeInOutQuart',
      },
      plugins: {
        legend: {
          display: showLegend,
          position: 'bottom',
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
              const dataPoint = context[0]
              const i = dataPoint.dataIndex
              const n = strategies.length
              const row = Math.floor(i / n)
              const col = i % n
              return `${strategies[row]?.name} vs ${strategies[col]?.name}`
            },
            label: (context: any) => {
              const value = context.raw.v
              const formatted = formatValue(value)

              let interpretation = ''
              if (Math.abs(value) < 0.1) {
                interpretation = ' (No correlation)'
              } else if (Math.abs(value) < 0.3) {
                interpretation = ' (Low correlation)'
              } else if (Math.abs(value) < 0.7) {
                interpretation = ' (Moderate correlation)'
              } else {
                interpretation = ' (High correlation)'
              }

              return [
                `Correlation: ${formatted}`,
                interpretation,
              ]
            },
          },
        },
        datalabels: showValues ? {
          display: true,
          color: (context: any) => {
            const value = context.dataset.data[context.dataIndex]?.v || 0
            // Use white text for dark backgrounds, black for light
            return Math.abs(value) > 0.5 ? '#ffffff' : textColor
          },
          font: {
            size: fontSize,
            weight: 'bold',
          },
          formatter: (value: any, context: any) => {
            const correlationValue = context.dataset.data[context.dataIndex]?.v || 0
            return formatValue(correlationValue)
          },
        } : false,
      },
      scales: {
        x: {
          type: 'category',
          labels: strategies.map(s => s.name),
          grid: {
            display: showGrid,
          },
          ticks: {
            color: textColor,
            font: {
              size: fontSize,
            },
            maxRotation: 45,
            minRotation: 45,
          },
        },
        y: {
          type: 'category',
          labels: strategies.map(s => s.name),
          grid: {
            display: showGrid,
          },
          ticks: {
            color: textColor,
            font: {
              size: fontSize,
            },
          },
          reverse: true, // Matrix orientation
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onCellClick) {
          const element = elements[0]
          const dataIndex = element.index
          const n = strategies.length
          const row = Math.floor(dataIndex / n)
          const col = dataIndex % n

          const strategy1 = strategies[row]?.id
          const strategy2 = strategies[col]?.id
          const correlation = element.element.$context.raw.v

          if (strategy1 && strategy2) {
            onCellClick(strategy1, strategy2, correlation)
          }
        }
      },
      layout: {
        padding: {
          top: 20,
          right: 20,
          bottom: 20,
          left: 20,
        },
      },
    }
  }, [
    theme,
    showGrid,
    showLegend,
    showTooltip,
    showValues,
    fontSize,
    strategies,
    formatValue,
    onCellClick,
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
      height={height}
      showZoom={false}
      showExportButton={true}
      refreshable={false}
      chartRef={chartRef}
    >
      <Chart
        ref={chartRef}
        type="matrix"
        data={chartData}
        options={chartOptions}
        loading={loading}
        error={error}
      />
    </ChartContainer>
  )
})

CorrelationHeatmap.displayName = 'CorrelationHeatmap'

export default CorrelationHeatmap