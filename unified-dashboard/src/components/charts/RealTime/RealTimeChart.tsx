import React, { useEffect, useRef, useCallback, useState } from 'react'
import { Chart, ChartConfiguration, ChartOptions } from 'chart.js'
import { useRealTimeChart } from './RealTimeChartProvider'
import { ChartDataPoint } from './RealTimeChartProvider'
import { ChartTheme, defaultChartTheme } from '../index'

// Real-time chart props interface
export interface RealTimeChartProps {
  symbol: string
  timeframe: string
  chartType: 'line' | 'candlestick' | 'bar' | 'area'
  height?: number
  width?: number
  theme?: ChartTheme
  maxDataPoints?: number
  updateInterval?: number
  showCrosshair?: boolean
  showGrid?: boolean
  showLegend?: boolean
  autoScale?: boolean
  onAnimation?: boolean
  onChartClick?: (point: ChartDataPoint) => void
  onDataUpdate?: (data: ChartDataPoint[]) => void
  className?: string
}

// Real-time chart component
export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  symbol,
  timeframe,
  chartType = 'line',
  height = 400,
  width = 800,
  theme = defaultChartTheme,
  maxDataPoints = 1000,
  updateInterval = 1000,
  showCrosshair = true,
  showGrid = true,
  showLegend = true,
  autoScale = true,
  onAnimation = true,
  onChartClick,
  onDataUpdate,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const { subscribe, unsubscribe, getData, getIndicators } = useRealTimeChart()
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

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
    const indicators = getIndicators?.(symbol, timeframe) || []

    // Configure chart based on type
    const config: ChartConfiguration = getChartConfig(chartType, data, indicators, theme)

    // Create new chart
    chartRef.current = new Chart(ctx, config)

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
        chartRef.current = null
      }
    }
  }, [symbol, timeframe, chartType, theme])

  // Subscribe to real-time updates
  useEffect(() => {
    const subscriberId = `realtime-chart-${symbol}-${timeframe}-${Date.now()}`

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
      chartRef.current.data.datasets[0].data = limitedData.map(d => ({
        x: d.timestamp,
        y: d.close
      }))

      // Update indicators if available
      const indicators = getIndicators?.(symbol, timeframe) || []
      indicators.forEach((indicator, index) => {
        const datasetIndex = index + 1
        if (chartRef.current.data.datasets[datasetIndex]) {
          chartRef.current.data.datasets[datasetIndex].data = limitedData.map(d => ({
            x: d.timestamp,
            y: indicator.value
          }))
        }
      })

      // Auto scale if enabled
      if (autoScale) {
        chartRef.current.options.scales.y.min = undefined
        chartRef.current.options.scales.y.max = undefined
      }

      // Update chart with animation
      chartRef.current.update('none')
      setLastUpdate(new Date())

      // Notify parent
      onDataUpdate?.(limitedData)
    }

    setIsUpdating(false)
  }, [symbol, timeframe, getData, getIndicators, maxDataPoints, autoScale, onDataUpdate])

  // Set up real-time updates
  useEffect(() => {
    const interval = setInterval(updateChart, updateInterval)

    return () => {
      clearInterval(interval)
    }
  }, [updateChart, updateInterval])

  // Handle chart click
  const handleChartClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!chartRef.current || !onChartClick) return

    const canvasPosition = Chart.helpers.getRelativePosition(event, chartRef.current)
    const dataX = chartRef.current.scales.x.getValueForPixel(canvasPosition.x)
    const dataY = chartRef.current.scales.y.getValueForPixel(canvasPosition.y)

    const chartData = getData(symbol, timeframe)
    if (chartData && chartData.length > 0) {
      const nearestPoint = chartData.reduce((prev, curr) => {
        return Math.abs(curr.timestamp.getTime() - dataX) < Math.abs(prev.timestamp.getTime() - dataX) ? curr : prev
      })

      onChartClick(nearestPoint)
    }
  }, [chartRef, onChartClick, getData, symbol, timeframe])

  return (
    <div className={`real-time-chart ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleChartClick}
        style={{ cursor: 'crosshair' }}
      />
      {lastUpdate && (
        <div className="chart-status">
          <span className="text-xs text-gray-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </span>
          {isUpdating && (
            <span className="ml-2 text-xs text-blue-500">
              Updating...
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// Helper function to get chart configuration
const getChartConfig = (
  type: string,
  data: ChartDataPoint[] | null,
  indicators: any[],
  theme: ChartTheme
): ChartConfiguration => {
  const chartData = data || []

  const baseConfig: ChartConfiguration = {
    type: type === 'area' ? 'line' : type,
    data: {
      labels: chartData.map(d => d.timestamp),
      datasets: [
        {
          label: 'Price',
          data: chartData.map(d => ({ x: d.timestamp, y: d.close })),
          borderColor: theme.primaryColor,
          backgroundColor: type === 'area' ? `${theme.primaryColor}20` : theme.backgroundColor,
          borderWidth: 2,
          fill: type === 'area',
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: theme.primaryColor,
          pointBorderColor: theme.primaryColor
        },
        ...indicators.map((indicator, index) => ({
          label: indicator.name,
          data: chartData.map(d => ({ x: d.timestamp, y: indicator.value })),
          borderColor: generateIndicatorColor(index),
          backgroundColor: 'transparent',
          borderWidth: 1,
          fill: false,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 3
        }))
      ]
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
          display: true,
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
          enabled: true,
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
        },
        crosshair: {
          line: {
            color: theme.gridColor,
            width: 1,
            dashPattern: [5, 5]
          },
          sync: {
            enabled: true,
            group: 1
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
            color: theme.gridColor,
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
            color: theme.gridColor,
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

  return baseConfig
}

// Generate different colors for indicators
const generateIndicatorColor = (index: number): string => {
  const colors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
  ]
  return colors[index % colors.length]
}

export default RealTimeChart