import React, { useEffect, useRef, useCallback, useState } from 'react'
import { Chart, ChartConfiguration, ChartType, ChartOptions } from 'chart.js'
import { useRealTimeChart } from './RealTimeChartProvider'
import { ChartDataPoint } from './RealTimeChartProvider'
import { ChartTheme, defaultChartTheme } from '../index'

// Real-time volume chart props
export interface RealTimeVolumeChartProps {
  symbol: string
  timeframe: string
  height?: number
  width?: number
  theme?: ChartTheme
  maxDataPoints?: number
  updateInterval?: number
  showBuySell?: boolean
  showCumulative?: boolean
  showAverage?: boolean
  barSpacing?: number
  colors?: {
    buy?: string
    sell?: string
    total?: string
    average?: string
    cumulative?: string
  }
  onBarClick?: (point: ChartDataPoint) => void
  onDataUpdate?: (data: ChartDataPoint[]) => void
  className?: string
}

// Real-time volume chart component
export const RealTimeVolumeChart: React.FC<RealTimeVolumeChartProps> = ({
  symbol,
  timeframe,
  height = 150,
  width = 800,
  theme = defaultChartTheme,
  maxDataPoints = 500,
  updateInterval = 1000,
  showBuySell = true,
  showCumulative = false,
  showAverage = false,
  barSpacing = 0.8,
  colors = {
    buy: '#10B981',
    sell: '#EF4444',
    total: '#6B7280',
    average: '#F59E0B',
    cumulative: '#8B5CF6'
  },
  onBarClick,
  onDataUpdate,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const { subscribe, unsubscribe, getData } = useRealTimeChart()
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

    // Configure chart
    const config: ChartConfiguration = getVolumeChartConfig(
      data,
      theme,
      showBuySell,
      showCumulative,
      showAverage,
      barSpacing,
      colors
    )

    // Create new chart
    chartRef.current = new Chart(ctx, config)

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
        chartRef.current = null
      }
    }
  }, [symbol, timeframe, theme, showBuySell, showCumulative, showAverage, barSpacing, colors])

  // Subscribe to real-time updates
  useEffect(() => {
    const subscriberId = `volume-chart-${symbol}-${timeframe}-${Date.now()}`

    subscribe(symbol, timeframe, subscriberId)

    return () => {
      unsubscribe(symbol, timeframe, subscriberId)
    }
  }, [symbol, timeframe, subscribe, unsubscribe])

  // Process volume data
  const processVolumeData = useCallback((data: ChartDataPoint[] | null) => {
    if (!data || data.length === 0) return null

    const limitedData = data.slice(-maxDataPoints)

    // Calculate buy/sell volumes (simplified - in real implementation, this would use actual trade data)
    const processedData = limitedData.map((point, index) => {
      const prevPoint = index > 0 ? limitedData[index - 1] : point
      const priceChange = point.close - prevPoint.close

      // Simple heuristic: if price went up, more buying pressure
      const buyVolume = priceChange >= 0 ? point.volume * 0.6 : point.volume * 0.4
      const sellVolume = point.volume - buyVolume

      return {
        ...point,
        buyVolume,
        sellVolume,
        totalVolume: point.volume
      }
    })

    // Calculate cumulative volume
    let cumulative = 0
    const dataWithCumulative = processedData.map(point => {
      cumulative += point.totalVolume
      return {
        ...point,
        cumulativeVolume: cumulative
      }
    })

    // Calculate average volume
    const avgVolume = processedData.reduce((sum, p) => sum + p.totalVolume, 0) / processedData.length

    return {
      data: dataWithCumulative,
      averageVolume: avgVolume
    }
  }, [maxDataPoints])

  // Update chart with new data
  const updateChart = useCallback(() => {
    if (!chartRef.current || isUpdating) return

    setIsUpdating(true)
    const data = getData(symbol, timeframe)
    const processedData = processVolumeData(data)

    if (processedData && processedData.data.length > 0) {
      const labels = processedData.data.map(d => d.timestamp)
      const datasets = []

      // Add buy volume
      if (showBuySell) {
        datasets.push({
          label: 'Buy Volume',
          data: processedData.data.map(d => d.buyVolume),
          backgroundColor: colors.buy,
          borderColor: colors.buy,
          borderWidth: 0,
          barPercentage: barSpacing,
          categoryPercentage: barSpacing
        })

        // Add sell volume as negative value for stacked effect
        datasets.push({
          label: 'Sell Volume',
          data: processedData.data.map(d => -d.sellVolume),
          backgroundColor: colors.sell,
          borderColor: colors.sell,
          borderWidth: 0,
          barPercentage: barSpacing,
          categoryPercentage: barSpacing
        })
      } else {
        // Total volume only
        datasets.push({
          label: 'Volume',
          data: processedData.data.map(d => d.totalVolume),
          backgroundColor: colors.total,
          borderColor: colors.total,
          borderWidth: 0,
          barPercentage: barSpacing,
          categoryPercentage: barSpacing
        })
      }

      // Add average line
      if (showAverage) {
        datasets.push({
          label: 'Average Volume',
          data: Array(processedData.data.length).fill(processedData.averageVolume),
          type: 'line' as ChartType,
          borderColor: colors.average,
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          tension: 0
        })
      }

      // Add cumulative volume on second axis
      if (showCumulative) {
        datasets.push({
          label: 'Cumulative Volume',
          data: processedData.data.map(d => d.cumulativeVolume),
          type: 'line' as ChartType,
          borderColor: colors.cumulative,
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'y1',
          tension: 0
        })
      }

      // Update chart data
      chartRef.current.data.labels = labels
      chartRef.current.data.datasets = datasets

      // Update chart without animation for real-time feel
      chartRef.current.update('none')
      setLastUpdate(new Date())

      // Notify parent
      onDataUpdate?.(processedData.data)
    }

    setIsUpdating(false)
  }, [
    symbol,
    timeframe,
    getData,
    processVolumeData,
    showBuySell,
    showCumulative,
    showAverage,
    barSpacing,
    colors,
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
    if (!chartRef.current || !onBarClick) return

    const canvasPosition = Chart.helpers.getRelativePosition(event, chartRef.current)
    const dataX = chartRef.current.scales.x.getValueForPixel(canvasPosition.x)

    const data = getData(symbol, timeframe)
    if (data && data.length > 0) {
      const nearestPoint = data.reduce((prev, curr) => {
        return Math.abs(curr.timestamp.getTime() - dataX) < Math.abs(prev.timestamp.getTime() - dataX) ? curr : prev
      })

      onBarClick(nearestPoint)
    }
  }, [chartRef, onBarClick, getData, symbol, timeframe])

  return (
    <div className={`real-time-volume-chart ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleChartClick}
        style={{ cursor: 'pointer' }}
      />
      {lastUpdate && (
        <div className="chart-status mt-1 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </span>
          {isUpdating && (
            <span className="ml-2 text-xs text-blue-500">
              Updating...
            </span>
          )}
          {showBuySell && (
            <div className="flex items-center space-x-4 text-xs">
              <div className="flex items-center">
                <div className="w-3 h-3 mr-1" style={{ backgroundColor: colors.buy }}></div>
                <span>Buy</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 mr-1" style={{ backgroundColor: colors.sell }}></div>
                <span>Sell</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Helper function to get volume chart configuration
const getVolumeChartConfig = (
  data: ChartDataPoint[] | null,
  theme: ChartTheme,
  showBuySell: boolean,
  showCumulative: boolean,
  showAverage: boolean,
  barSpacing: number,
  colors: any
): ChartConfiguration => {
  const chartData = data || []

  const datasets = []

  // Configure datasets based on options
  if (showBuySell) {
    datasets.push(
      {
        label: 'Buy Volume',
        data: chartData.map(d => d.volume * 0.6), // Placeholder
        backgroundColor: colors.buy,
        borderColor: colors.buy,
        borderWidth: 0,
        barPercentage: barSpacing,
        categoryPercentage: barSpacing
      },
      {
        label: 'Sell Volume',
        data: chartData.map(d => d.volume * 0.4), // Placeholder
        backgroundColor: colors.sell,
        borderColor: colors.sell,
        borderWidth: 0,
        barPercentage: barSpacing,
        categoryPercentage: barSpacing
      }
    )
  } else {
    datasets.push({
      label: 'Volume',
      data: chartData.map(d => d.volume),
      backgroundColor: colors.total,
      borderColor: colors.total,
      borderWidth: 0,
      barPercentage: barSpacing,
      categoryPercentage: barSpacing
    })
  }

  if (showAverage) {
    const avgVolume = chartData.reduce((sum, d) => sum + d.volume, 0) / chartData.length
    datasets.push({
      label: 'Average Volume',
      data: Array(chartData.length).fill(avgVolume),
      type: 'line' as ChartType,
      borderColor: colors.average,
      backgroundColor: 'transparent',
      borderWidth: 1,
      pointRadius: 0,
      tension: 0
    })
  }

  const config: ChartConfiguration = {
    type: 'bar',
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
          display: false // Hide legend for volume chart
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
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              return `${label}: ${value.toFixed(0)}`
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
              hour: 'HH:mm'
            }
          },
          grid: {
            color: theme.gridColor,
            borderColor: theme.gridColor,
            drawBorder: false
          },
          ticks: {
            color: theme.textColor,
            font: {
              size: 10
            },
            maxRotation: 0
          }
        },
        y: {
          position: 'right',
          grid: {
            color: theme.gridColor,
            borderColor: theme.gridColor,
            drawBorder: false
          },
          ticks: {
            color: theme.textColor,
            font: {
              size: 10
            },
            callback: function(value) {
              return formatVolume(value as number)
            }
          }
        },
        ...(showCumulative && {
          y1: {
            type: 'linear',
            display: true,
            position: 'left',
            grid: {
              drawOnChartArea: false // Only show grid for primary axis
            },
            ticks: {
              color: theme.textColor,
              font: {
                size: 10
              },
              callback: function(value) {
                return formatVolume(value as number)
              }
            }
          }
        })
      }
    }
  }

  return config
}

// Format volume numbers
const formatVolume = (value: number): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toFixed(0)
}

export default RealTimeVolumeChart