import React, { useMemo, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

export interface RSIData {
  timestamp: string | number | Date
  rsi: number
}

export interface RSIChartProps {
  data: RSIData[]
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
    line: string
    overbought: string
    oversold: string
    neutral: string
    grid?: string
  }
  period?: number
  overboughtLevel?: number
  oversoldLevel?: number
  showZoneLabels?: boolean
  fillZones?: boolean
  onExtremeLevel?: (type: 'overbought' | 'oversold', value: number, index: number) => void
  animationDuration?: number
  lineWidth?: number
}

export interface RSIChartRef {
  exportChart: (options?: any) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const RSIChart = forwardRef<RSIChartRef, RSIChartProps>(({
  data,
  width,
  height = 200,
  title = 'RSI',
  subtitle,
  loading,
  error,
  timeRange,
  onTimeRangeChange,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  theme = 'light',
  colors = {
    line: '#2196F3',
    overbought: '#F44336',
    oversold: '#4CAF50',
    neutral: '#FFC107',
    grid: 'rgba(0, 0, 0, 0.05)',
  },
  period = 14,
  overboughtLevel = 70,
  oversoldLevel = 30,
  showZoneLabels = true,
  fillZones = true,
  onExtremeLevel,
  animationDuration = 500,
  lineWidth = 2,
}, ref) => {
  const chartRef = React.useRef<any>(null)

  // Detect extreme levels
  const extremeLevels = useMemo(() => {
    if (!data) return []

    return data.map((item, index) => {
      if (item.rsi >= overboughtLevel) {
        return { type: 'overbought', value: item.rsi, index }
      } else if (item.rsi <= oversoldLevel) {
        return { type: 'oversold', value: item.rsi, index }
      }
      return null
    }).filter(Boolean) as Array<{ type: 'overbought' | 'oversold', value: number, index: number }>
  }, [data, overboughtLevel, oversoldLevel])

  // Transform RSI data to chart format
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
        label: `RSI(${period})`,
        data: data.map(item => item.rsi),
        borderColor: colors.line,
        backgroundColor: fillZones ? data.map(item => {
          if (item.rsi >= overboughtLevel) return colors.overbought + '20'
          if (item.rsi <= oversoldLevel) return colors.oversold + '20'
          return 'transparent'
        }) : 'transparent',
        borderWidth: lineWidth,
        fill: fillZones ? { target: 'origin', above: colors.overbought + '20', below: colors.oversold + '20' } : false,
        type: 'line',
        pointRadius: 0,
        pointHoverRadius: 3,
        tension: 0.1,
      },
    ]

    // Add zone background datasets if fillZones is true
    if (fillZones) {
      // Overbought zone
      datasets.push({
        label: 'Overbought Zone',
        data: new Array(data.length).fill(overboughtLevel),
        borderColor: 'transparent',
        backgroundColor: colors.overbought + '10',
        borderWidth: 0,
        type: 'line',
        pointRadius: 0,
        fill: {
          target: 'origin',
          above: colors.overbought + '10',
        },
      })

      // Oversold zone
      datasets.push({
        label: 'Oversold Zone',
        data: new Array(data.length).fill(oversoldLevel),
        borderColor: 'transparent',
        backgroundColor: colors.oversold + '10',
        borderWidth: 0,
        type: 'line',
        pointRadius: 0,
        fill: {
          target: 'origin',
          below: colors.oversold + '10',
        },
      })
    }

    return { labels, datasets }
  }, [data, colors, period, overboughtLevel, oversoldLevel, fillZones, lineWidth])

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

              const value = item.rsi.toFixed(2)
              let zone = 'Neutral'
              if (item.rsi >= overboughtLevel) zone = 'Overbought'
              else if (item.rsi <= oversoldLevel) zone = 'Oversold'

              return [
                `RSI(${period}): ${value}`,
                `Zone: ${zone}`,
              ]
            },
          },
        },
        annotation: {
          annotations: {
            overboughtLine: {
              type: 'line',
              yMin: overboughtLevel,
              yMax: overboughtLevel,
              borderColor: colors.overbought,
              borderWidth: 1,
              borderDash: [5, 5],
              label: showZoneLabels ? {
                content: `Overbought (${overboughtLevel})`,
                enabled: true,
                position: 'end',
                backgroundColor: colors.overbought,
                color: 'white',
                font: {
                  size: 10,
                },
              } : undefined,
            },
            oversoldLine: {
              type: 'line',
              yMin: oversoldLevel,
              yMax: oversoldLevel,
              borderColor: colors.oversold,
              borderWidth: 1,
              borderDash: [5, 5],
              label: showZoneLabels ? {
                content: `Oversold (${oversoldLevel})`,
                enabled: true,
                position: 'end',
                backgroundColor: colors.oversold,
                color: 'white',
                font: {
                  size: 10,
                },
              } : undefined,
            },
            middleLine: {
              type: 'line',
              yMin: 50,
              yMax: 50,
              borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
              borderWidth: 1,
              borderDash: [2, 2],
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
          min: 0,
          max: 100,
          position: 'right',
          grid: {
            display: showGrid,
            color: gridColor,
          },
          ticks: {
            color: textColor,
            stepSize: 20,
            callback: (value: number) => value.toString(),
          },
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && onExtremeLevel) {
          const dataIndex = elements[0].index
          const extreme = extremeLevels.find(e => e.index === dataIndex)
          if (extreme) {
            onExtremeLevel(extreme.type, extreme.value, dataIndex)
          }
        }
      },
    }
  }, [
    theme,
    showGrid,
    showLegend,
    showTooltip,
    showZoneLabels,
    colors,
    data,
    period,
    overboughtLevel,
    oversoldLevel,
    extremeLevels,
    onExtremeLevel,
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

  // Generate subtitle with period
  const generatedSubtitle = useMemo(() => {
    if (subtitle) return subtitle
    return `Period: ${period} | OB: ${overboughtLevel} | OS: ${oversoldLevel}`
  }, [subtitle, period, overboughtLevel, oversoldLevel])

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

RSIChart.displayName = 'RSIChart'

export default RSIChart