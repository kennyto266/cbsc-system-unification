import React, { useMemo, useCallback } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface TimeSeriesData {
  timestamp: string | number | Date
  value: number
  label?: string
  metadata?: Record<string, any>
}

export interface TimeSeriesChartProps {
  data: TimeSeriesData[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  chartType?: 'line' | 'bar' | 'area'
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    line?: string
    background?: string
    grid?: string
  }
  onDataPointClick?: (data: TimeSeriesData, index: number) => void
  smoothing?: number // 0-1 for tension
  fillArea?: boolean
  showDataPoints?: boolean
  dataPointRadius?: number
  annotations?: Array<{
    x: string | number | Date
    y: number
    label?: string
    color?: string
    type?: 'line' | 'circle' | 'arrow'
  }>
  indicators?: Array<{
    name: string
    data: number[]
    color: string
    lineWidth?: number
    dashArray?: number[]
  }>
}

export interface TimeSeriesChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const TimeSeriesChart = forwardRef<TimeSeriesChartRef, TimeSeriesChartProps>(({
  data,
  width,
  height = 400,
  title,
  subtitle,
  loading,
  error,
  timeRange,
  onTimeRangeChange,
  chartType = 'line',
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    line: '#3B82F6',
    background: 'rgba(59, 130, 246, 0.1)',
    grid: 'rgba(0, 0, 0, 0.05)',
  },
  onDataPointClick,
  smoothing = 0.4,
  fillArea = false,
  showDataPoints = false,
  dataPointRadius = 4,
  annotations = [],
  indicators = [],
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Transform time series data to chart format
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const labels = data.map(item => {
      const date = new Date(item.timestamp)
      return date.toLocaleDateString()
    })

    const datasets = [
      {
        label: title || 'Time Series',
        data: data.map(item => ({
          x: item.timestamp,
          y: item.value,
          label: item.label,
          metadata: item.metadata,
        })),
        borderColor: colors.line,
        backgroundColor: fillArea ? colors.background : 'transparent',
        borderWidth: 2,
        fill: fillArea,
        tension: smoothing,
        pointRadius: showDataPoints ? dataPointRadius : 0,
        pointHoverRadius: dataPointRadius + 2,
        pointBackgroundColor: colors.line,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        type: chartType,
      },
      ...indicators.map(indicator => ({
        label: indicator.name,
        data: indicator.data.map((value, index) => ({
          x: data[index]?.timestamp,
          y: value,
        })),
        borderColor: indicator.color,
        backgroundColor: 'transparent',
        borderWidth: indicator.lineWidth || 2,
        borderDash: indicator.dashArray,
        tension: 0.1,
        type: 'line' as const,
        pointRadius: 0,
        pointHoverRadius: 3,
      })),
    ]

    return { labels, datasets }
  }, [data, title, colors, chartType, smoothing, fillArea, showDataPoints, dataPointRadius, indicators])

  // Chart options
  const chartOptions = useMemo(() => {
    const isDark = theme === 'dark'
    const textColor = isDark ? '#9ca3af' : '#374151'
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'

    return {
      responsive: true,
      maintainAspectRatio: false,
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
            padding: 20,
          },
        },
        tooltip: {
          enabled: showTooltip,
          mode: 'index',
          intersect: false,
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

              const value = chartUtils.formatNumber(item.value)
              const label = item.label || context.dataset.label || 'Value'
              return `${label}: ${value}`
            },
            afterLabel: (context: any) => {
              const dataIndex = context.dataIndex
              const item = data[dataIndex]
              if (!item || !item.metadata) return []

              return Object.entries(item.metadata).map(([key, val]) => {
                return `${key}: ${val}`
              })
            },
          },
        },
        annotation: {
          annotations: annotations.map((ann, index) => ({
            type: ann.type || 'line',
            xMin: ann.x,
            xMax: ann.x,
            yMin: ann.y,
            yMax: ann.y,
            borderColor: ann.color || '#ff0000',
            borderWidth: 2,
            label: ann.label ? {
              content: ann.label,
              enabled: true,
              position: 'top',
            } : undefined,
          })),
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
            autoSkipPadding: 20,
          },
        },
        y: {
          grid: {
            display: showGrid,
            color: gridColor,
          },
          ticks: {
            color: textColor,
            callback: (value: number) => {
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
              if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
              return value.toFixed(2)
            },
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onDataPointClick) {
          const dataIndex = elements[0].index
          const dataPoint = data[dataIndex]
          if (dataPoint) {
            onDataPointClick(dataPoint, dataIndex)
          }
        }
      },
      elements: {
        line: {
          borderWidth: 2,
        },
      },
    }
  }, [theme, showLegend, showGrid, showTooltip, colors, data, annotations, onDataPointClick])

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
        type={chartType}
        data={chartData}
        options={chartOptions}
        loading={loading}
        error={error}
      />
    </ChartContainer>
  )
})

TimeSeriesChart.displayName = 'TimeSeriesChart'

export default TimeSeriesChart