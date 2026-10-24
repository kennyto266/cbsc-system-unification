import React, { useEffect, useRef, useCallback, useState } from 'react'
import { Chart, ChartConfiguration, ChartOptions } from 'chart.js'
import { useRealTimeChart } from './RealTimeChartProvider'
import { ChartDataPoint } from './RealTimeChartProvider'
import { ChartTheme, defaultChartTheme } from '../index'

// Real-time line chart props
export interface RealTimeLineChartProps {
  symbol: string
  timeframe: string
  height?: number
  width?: number
  theme?: ChartTheme
  maxDataPoints?: number
  updateInterval?: number
  series: Array<{
    key: string
    label: string
    color?: string
    strokeWidth?: number
    fill?: boolean
    yAxisID?: string
  }>
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  showCrosshair?: boolean
  autoScale?: boolean
  smoothLine?: boolean
  fillArea?: boolean
  gradientFill?: boolean
  onDataUpdate?: (data: ChartDataPoint[]) => void
  onPointClick?: (point: ChartDataPoint, series: string) => void
  className?: string
}

// Real-time line chart component
export const RealTimeLineChart: React.FC<RealTimeLineChartProps> = ({
  symbol,
  timeframe,
  height = 300,
  width = 800,
  theme = defaultChartTheme,
  maxDataPoints = 1000,
  updateInterval = 1000,
  series = [{ key: 'close', label: 'Price' }],
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  showCrosshair = true,
  autoScale = true,
  smoothLine = true,
  fillArea = false,
  gradientFill = false,
  onDataUpdate,
  onPointClick,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const { subscribe, unsubscribe, getData } = useRealTimeChart()
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

  // Color palette for multiple series
  const colorPalette = [
    theme.primaryColor,
    theme.successColor,
    theme.warningColor,
    theme.dangerColor,
    theme.infoColor,
    '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#06B6D4'
  ]

  // Initialize chart
  useEffect(() => {
    if (!canvasRef.current) return

    const ctx = canvasRef.current.getContext('2d')
    if (!ctx) return

    // Destroy existing chart
    if (chartRef.current) {
      chartRef.current.destroy()
      chartRef.current = null
    }

    // Get initial data
    const data = getData(symbol, timeframe)

    // Configure chart
    const config: ChartConfiguration = getLineChartConfig(
      data,
      series,
      theme,
      showGrid,
      showLegend,
      showTooltip,
      smoothLine,
      fillArea,
      gradientFill,
      colorPalette
    )

    // Create new chart
    chartRef.current = new Chart(ctx, config)

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
        chartRef.current = null
      }
    }
  }, [symbol, timeframe, series, theme, showGrid, showLegend, showTooltip, smoothLine, fillArea, gradientFill])

  // Subscribe to real-time updates
  useEffect(() => {
    const subscriberId = `line-chart-${symbol}-${timeframe}-${Date.now()}`

    subscribe(symbol, timeframe, subscriberId)

    return () => {
      unsubscribe(symbol, timeframe, subscriberId)
    }
  }, [symbol, timeframe, subscribe, unsubscribe])

  // Update chart with new data
  const updateChart = useCallback(() => {
    if (!chartRef.current || isUpdating) return

    setIsUpdating(true)
    const data = getData(symbol, timeframe)

    if (data && data.length > 0) {
      // Limit data points
      const limitedData = data.slice(-maxDataPoints)

      // Update chart data
      chartRef.current.data.labels = limitedData.map(d => d.timestamp)

      // Update each series
      chartRef.current.data.datasets = series.map((s, index) => {
        const color = s.color || colorPalette[index % colorPalette.length]
        const seriesData = limitedData.map(d => {
          const value = (d as any)[s.key] || d.close || 0
          return {
            x: d.timestamp,
            y: value
          }
        })

        // Create gradient fill if enabled
        let backgroundColor = color
        if (gradientFill && (s.fill || fillArea)) {
          const ctx = canvasRef.current?.getContext('2d')
          if (ctx) {
            const gradient = ctx.createLinearGradient(0, 0, 0, height)
            gradient.addColorStop(0, color + '40') // Add transparency
            gradient.addColorStop(1, color + '00') // Fully transparent
            backgroundColor = gradient
          }
        }

        return {
          label: s.label,
          data: seriesData,
          borderColor: color,
          backgroundColor: (s.fill || fillArea) ? backgroundColor : 'transparent',
          borderWidth: s.strokeWidth || 2,
          fill: (s.fill || fillArea) ? true : false,
          tension: smoothLine ? 0.4 : 0,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: color,
          pointBorderColor: color,
          yAxisID: s.yAxisID || 'y'
        }
      })

      // Auto scale if enabled
      if (autoScale) {
        Object.keys(chartRef.current.scales).forEach(scaleId => {
          const scale = chartRef.current!.scales[scaleId]
          if (scale.options.min !== undefined) scale.options.min = undefined
          if (scale.options.max !== undefined) scale.options.max = undefined
        })
      }

      // Update chart without animation for real-time feel
      chartRef.current.update('none')
      setLastUpdate(new Date())

      // Notify parent
      onDataUpdate?.(limitedData)
    }

    setIsUpdating(false)
  }, [
    symbol,
    timeframe,
    getData,
    series,
    maxDataPoints,
    autoScale,
    smoothLine,
    fillArea,
    gradientFill,
    height,
    colorPalette,
    onDataUpdate
  ])

  // Set up real-time updates
  useEffect(() => {
    const interval = setInterval(updateChart, updateInterval)

    return () => {
      clearInterval(interval)
    }
  }, [updateChart, updateInterval])

  // Handle chart click
  const handleChartClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!chartRef.current || !onPointClick) return

    const canvasPosition = Chart.helpers.getRelativePosition(event, chartRef.current)
    const dataX = chartRef.current.scales.x.getValueForPixel(canvasPosition.x)
    const dataY = chartRef.current.scales.y.getValueForPixel(canvasPosition.y)

    const data = getData(symbol, timeframe)
    if (data && data.length > 0) {
      const nearestPoint = data.reduce((prev, curr) => {
        return Math.abs(curr.timestamp.getTime() - dataX) < Math.abs(prev.timestamp.getTime() - dataX) ? curr : prev
      })

      // Find closest series
      const clickedSeries = series.reduce((closest, s) => {
        const value = (nearestPoint as any)[s.key] || nearestPoint.close || 0
        const distance = Math.abs(value - dataY)
        return !closest || distance < closest.distance ? { series: s.key, distance } : closest
      }, null as { series: string; distance: number } | null)

      if (clickedSeries) {
        onPointClick(nearestPoint, clickedSeries.series)
      }
    }
  }, [chartRef, onPointClick, getData, symbol, timeframe, series])

  return (
    <div className={`real-time-line-chart ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleChartClick}
        style={{ cursor: onPointClick ? 'pointer' : 'default' }}
      />
      {lastUpdate && (
        <div className="chart-status mt-2 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </span>
          {isUpdating && (
            <span className="ml-2 text-xs text-blue-500">
              Updating...
            </span>
          )}
          {showLegend && series.length > 1 && (
            <div className="flex items-center space-x-4 text-xs">
              {series.map((s, index) => {
                const color = s.color || colorPalette[index % colorPalette.length]
                return (
                  <div key={s.key} className="flex items-center">
                    <div
                      className="w-3 h-0.5 mr-1"
                      style={{ backgroundColor: color }}
                    ></div>
                    <span>{s.label}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Helper function to get line chart configuration
const getLineChartConfig = (
  data: ChartDataPoint[] | null,
  series: RealTimeLineChartProps['series'],
  theme: ChartTheme,
  showGrid: boolean,
  showLegend: boolean,
  showTooltip: boolean,
  smoothLine: boolean,
  fillArea: boolean,
  gradientFill: boolean,
  colorPalette: string[]
): ChartConfiguration => {
  const chartData = data || []

  const datasets = series.map((s, index) => {
    const color = s.color || colorPalette[index % colorPalette.length]
    const seriesData = chartData.map(d => ({
      x: d.timestamp,
      y: (d as any)[s.key] || d.close || 0
    }))

    return {
      label: s.label,
      data: seriesData,
      borderColor: color,
      backgroundColor: fillArea ? `${color}40` : 'transparent',
      borderWidth: s.strokeWidth || 2,
      fill: fillArea,
      tension: smoothLine ? 0.4 : 0,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointBackgroundColor: color,
      pointBorderColor: color,
      yAxisID: s.yAxisID || 'y'
    }
  })

  const config: ChartConfiguration = {
    type: 'line',
    data: {
      labels: chartData.map(d => d.timestamp),
      datasets
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      animation: false, // Disable animation for real-time updates
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: showLegend && series.length > 1,
          position: 'top',
          labels: {
            color: theme.textColor,
            font: {
              size: 12
            },
            usePointStyle: true,
            padding: 20
          }
        },
        tooltip: {
          enabled: showTooltip,
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: theme.backgroundColor,
          bodyColor: theme.backgroundColor,
          borderColor: theme.gridColor,
          borderWidth: 1,
          cornerRadius: 4,
          displayColors: true,
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              return `${label}: ${value.toFixed(2)}`
            }
          }
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MM/dd'
            }
          },
          grid: {
            color: showGrid ? theme.gridColor : 'transparent',
            borderColor: theme.gridColor,
            drawBorder: true
          },
          ticks: {
            color: theme.textColor,
            font: {
              size: 11
            },
            maxRotation: 0
          }
        },
        y: {
          position: 'right',
          grid: {
            color: showGrid ? theme.gridColor : 'transparent',
            borderColor: theme.gridColor,
            drawBorder: true
          },
          ticks: {
            color: theme.textColor,
            font: {
              size: 11
            },
            callback: function(value) {
              return value.toFixed(2)
            }
          }
        }
      },
      elements: {
        point: {
          radius: 0,
          hoverRadius: 4
        }
      }
    }
  }

  return config
}

export default RealTimeLineChart