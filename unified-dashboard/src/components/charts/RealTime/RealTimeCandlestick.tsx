import React, { useEffect, useRef, useCallback, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'
import { useRealTimeChart } from './RealTimeChartProvider'
import { ChartDataPoint } from './RealTimeChartProvider'

// Real-time candlestick chart props
export interface RealTimeCandlestickProps {
  symbol: string
  timeframe: string
  height?: number
  width?: number
  showVolume?: boolean
  showTechnicalIndicators?: boolean
  maxDataPoints?: number
  updateInterval?: number
  theme?: 'light' | 'dark'
  autoScale?: boolean
  showCrosshair?: boolean
  showGrid?: boolean
  showLegend?: boolean
  onCandleClick?: (candle: ChartDataPoint) => void
  onDataUpdate?: (data: ChartDataPoint[]) => void
  className?: string
}

// Real-time candlestick chart component
export const RealTimeCandlestick: React.FC<RealTimeCandlestickProps> = ({
  symbol,
  timeframe,
  height = 400,
  width = 800,
  showVolume = true,
  showTechnicalIndicators = true,
  maxDataPoints = 1000,
  updateInterval = 1000,
  theme = 'light',
  autoScale = true,
  showCrosshair = true,
  showGrid = true,
  showLegend = true,
  onCandleClick,
  onDataUpdate,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const indicatorSeriesRefs = useRef<ISeriesApi<'Line'>[]>([])
  const { subscribe, unsubscribe, getData, getIndicators } = useRealTimeChart()
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

  // Chart theme colors
  const chartColors = {
    light: {
      background: '#ffffff',
      grid: 'rgba(0, 0, 0, 0.1)',
      text: 'rgba(0, 0, 0, 0.8)',
      candleUp: '#26a69a',
      candleDown: '#ef5350',
      volumeUp: 'rgba(38, 166, 154, 0.7)',
      volumeDown: 'rgba(239, 83, 80, 0.7)',
      crosshair: 'rgba(0, 0, 0, 0.5)',
      indicator1: '#2196f3',
      indicator2: '#ff9800',
      indicator3: '#9c27b0'
    },
    dark: {
      background: '#1e1e1e',
      grid: 'rgba(255, 255, 255, 0.1)',
      text: 'rgba(255, 255, 255, 0.8)',
      candleUp: '#00b894',
      candleDown: '#ff7675',
      volumeUp: 'rgba(0, 184, 148, 0.7)',
      volumeDown: 'rgba(255, 118, 117, 0.7)',
      crosshair: 'rgba(255, 255, 255, 0.5)',
      indicator1: '#74b9ff',
      indicator2: '#fdcb6e',
      indicator3: '#a29bfe'
    }
  }

  const colors = chartColors[theme]

  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return

    // Create chart
    const chart = createChart(containerRef.current, {
      width,
      height,
      layout: {
        background: { color: colors.background },
        textColor: colors.text,
        fontSize: 12,
        fontFamily: 'Arial, sans-serif'
      },
      grid: {
        vertLines: { color: showGrid ? colors.grid : 'transparent' },
        horzLines: { color: showGrid ? colors.grid : 'transparent' }
      },
      crosshair: {
        mode: showCrosshair ? 1 : 0,
        vertLine: {
          color: colors.crosshair,
          width: 1,
          style: 3
        },
        horzLine: {
          color: colors.crosshair,
          width: 1,
          style: 3
        }
      },
      rightPriceScale: {
        borderColor: colors.grid,
        textColor: colors.text
      },
      timeScale: {
        borderColor: colors.grid,
        textColor: colors.text,
        timeVisible: true,
        secondsVisible: false
      },
      overlayPriceScales: {
        ticksVisible: false,
        borderVisible: false
      }
    })

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: colors.candleUp,
      downColor: colors.candleDown,
      borderDownColor: colors.candleDown,
      borderUpColor: colors.candleUp,
      wickDownColor: colors.candleDown,
      wickUpColor: colors.candleUp
    })

    // Add volume series if enabled
    let volumeSeries: ISeriesApi<'Histogram'> | null = null
    if (showVolume) {
      volumeSeries = chart.addHistogramSeries({
        color: colors.volumeUp,
        priceFormat: {
          type: 'volume'
        },
        priceScaleId: 'volume',
        scaleMargins: {
          top: 0.8,
          bottom: 0
        }
      })

      // Configure volume scale
      chart.priceScale('volume').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0
        }
      })
    }

    // Store references
    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries

    // Handle click events
    chart.subscribeClick((param) => {
      if (param.time && onCandleClick) {
        const data = getData(symbol, timeframe)
        if (data) {
          const clickedCandle = data.find(d =>
            d.timestamp.getTime() === param.time * 1000
          )
          if (clickedCandle) {
            onCandleClick(clickedCandle)
          }
        }
      }
    })

    return () => {
      chart.remove()
      chartRef.current = null
      candlestickSeriesRef.current = null
      volumeSeriesRef.current = null
      indicatorSeriesRefs.current = []
    }
  }, [width, height, theme, showGrid, showCrosshair, showVolume])

  // Subscribe to real-time updates
  useEffect(() => {
    const subscriberId = `candlestick-chart-${symbol}-${timeframe}-${Date.now()}`

    subscribe(symbol, timeframe, subscriberId)

    return () => {
      unsubscribe(symbol, timeframe, subscriberId)
    }
  }, [symbol, timeframe, subscribe, unsubscribe])

  // Update chart with new data
  const updateChart = useCallback(() => {
    if (!chartRef.current || !candlestickSeriesRef.current || isUpdating) return

    setIsUpdating(true)
    const data = getData(symbol, timeframe)
    const indicators = getIndicators?.(symbol, timeframe) || []

    if (data && data.length > 0) {
      // Limit data points
      const limitedData = data.slice(-maxDataPoints)

      // Convert to candlestick data format
      const candlestickData: CandlestickData[] = limitedData.map(d => ({
        time: (d.timestamp.getTime() / 1000) as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close
      }))

      // Update candlestick series
      candlestickSeriesRef.current.setData(candlestickData)

      // Update volume series if enabled
      if (volumeSeriesRef.current && showVolume) {
        const volumeData = limitedData.map(d => ({
          time: (d.timestamp.getTime() / 1000) as Time,
          value: d.volume,
          color: d.close >= d.open ? colors.volumeUp : colors.volumeDown
        }))
        volumeSeriesRef.current.setData(volumeData)
      }

      // Update technical indicators
      if (showTechnicalIndicators && indicators.length > 0) {
        // Remove old indicator series
        indicatorSeriesRefs.current.forEach(series => {
          chartRef.current?.removeSeries(series)
        })
        indicatorSeriesRefs.current = []

        // Add new indicator series
        indicators.forEach((indicator, index) => {
          const indicatorSeries = chartRef.current!.addLineSeries({
            color: [colors.indicator1, colors.indicator2, colors.indicator3][index % 3],
            lineWidth: 1,
            title: indicator.name,
            priceScaleId: `indicator-${index}`
          })

          const indicatorData = limitedData.map(d => ({
            time: (d.timestamp.getTime() / 1000) as Time,
            value: indicator.value
          }))

          indicatorSeries.setData(indicatorData)
          indicatorSeriesRefs.current.push(indicatorSeries)
        })
      }

      // Auto scale if enabled
      if (autoScale) {
        chartRef.current.timeScale().fitContent()
      }

      setLastUpdate(new Date())
      onDataUpdate?.(limitedData)
    }

    setIsUpdating(false)
  }, [
    symbol,
    timeframe,
    getData,
    getIndicators,
    maxDataPoints,
    autoScale,
    showVolume,
    showTechnicalIndicators,
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

  return (
    <div className={`real-time-candlestick ${className}`}>
      <div ref={containerRef} style={{ width, height }} />
      {lastUpdate && (
        <div className="chart-status mt-2 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Last update: {lastUpdate.toLocaleTimeString()}
          </span>
          {isUpdating && (
            <span className="text-xs text-blue-500">
              Updating...
            </span>
          )}
          {showLegend && (
            <div className="flex items-center space-x-4 text-xs">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 mr-1"></div>
                <span>Up</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 mr-1"></div>
                <span>Down</span>
              </div>
              {showTechnicalIndicators && (
                <>
                  <div className="flex items-center">
                    <div className="w-3 h-1 bg-blue-500 mr-1"></div>
                    <span>MA</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-1 bg-orange-500 mr-1"></div>
                    <span>Signal</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default RealTimeCandlestick