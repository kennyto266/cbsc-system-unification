import React, { useEffect, useRef, useMemo, useState, useCallback, forwardRef, useImperativeHandle } from 'react'
import { Chart as ChartJS, ChartConfiguration, Plugin } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'
import 'chartjs-chart-financial'

// Register Chart.js components
Chart.register(...registerables)

export interface OHLCData {
  timestamp: number | string | Date
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export interface CandlestickChartProps extends BaseChartProps {
  data: OHLCData[]
  volumeData?: OHLCData[]
  technicalIndicators?: Array<{
    type: 'SMA' | 'EMA' | 'MACD' | 'RSI' | 'BB' | 'STOCH' | 'ADX' | 'ATR'
    params?: any
    color?: string
    visible?: boolean
  }>
  timeRange?: {
    start: Date | number | string
    end: Date | number | string
  }
  showVolume?: boolean
  volumeHeight?: number // Percentage of chart height
  showGrid?: boolean
  showCrosshair?: boolean
  crosshairStyle?: {
    color?: string
    width?: number
    dash?: number[]
  }
  showTooltip?: boolean
  candlestickStyle?: {
    upColor?: string
    downColor?: string
    borderUpColor?: string
    borderDownColor?: string
    wickUpColor?: string
    wickDownColor?: string
  }
  onCandleClick?: (data: OHLCData, index: number) => void
  onTimeRangeChange?: (range: { start: Date; end: Date }) => void
  zoomEnabled?: boolean
  panEnabled?: boolean
}

// Technical indicator calculations
const calculateSMA = (data: OHLCData[], period: number): number[] => {
  const result: number[] = []
  for (let i = period - 1; i < data.length; i++) {
    const sum = data.slice(i - period + 1, i + 1).reduce((acc, d) => acc + d.close, 0)
    result.push(sum / period)
  }
  return result
}

const calculateEMA = (data: OHLCData[], period: number): number[] => {
  const result: number[] = []
  const multiplier = 2 / (period + 1)

  // Start with SMA
  let ema = data.slice(0, period).reduce((acc, d) => acc + d.close, 0) / period
  result.push(ema)

  for (let i = period; i < data.length; i++) {
    ema = (data[i].close - ema) * multiplier + ema
    result.push(ema)
  }

  return result
}

const calculateMACD = (data: OHLCData[], fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)
  const macdLine = fastEMA.map((val, i) => val - slowEMA[i + (slowPeriod - fastPeriod)])
  const signalLine = calculateEMA(
    [{ close: macdLine[0] }] as any,
    signalPeriod
  ).map((val, i) => (val * macdLine[i] + (signalPeriod - 1) * macdLine[i]) / signalPeriod)
  const histogram = macdLine.map((val, i) => val - signalLine[i])

  return { macdLine, signalLine, histogram }
}

const calculateRSI = (data: OHLCData[], period = 14): number[] => {
  const result: number[] = []
  let gains = 0
  let losses = 0

  // Calculate first average gain/loss
  for (let i = 1; i <= period; i++) {
    const change = data[i].close - data[i - 1].close
    if (change > 0) gains += change
    else losses -= change
  }

  let avgGain = gains / period
  let avgLoss = losses / period
  let rs = avgGain / avgLoss
  result.push(100 - (100 / (1 + rs)))

  // Calculate subsequent RSI values
  for (let i = period + 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    avgGain = (avgGain * (period - 1) + (change > 0 ? change : 0)) / period
    avgLoss = (avgLoss * (period - 1) + (change < 0 ? -change : 0)) / period
    rs = avgGain / avgLoss
    result.push(100 - (100 / (1 + rs)))
  }

  return result
}

const calculateBollingerBands = (data: OHLCData[], period = 20, stdDev = 2) => {
  const sma = calculateSMA(data, period)
  const upperBand: number[] = []
  const lowerBand: number[] = []

  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1)
    const mean = sma[i - period + 1]
    const variance = slice.reduce((acc, d) => acc + Math.pow(d.close - mean, 2), 0) / period
    const sd = Math.sqrt(variance)

    upperBand.push(mean + (sd * stdDev))
    lowerBand.push(mean - (sd * stdDev))
  }

  return { upperBand, middleBand: sma, lowerBand }
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  volumeData,
  technicalIndicators = [],
  timeRange,
  showVolume = true,
  volumeHeight = 25,
  showGrid = true,
  showCrosshair = true,
  crosshairStyle = {},
  showTooltip = true,
  candlestickStyle = {},
  onCandleClick,
  onTimeRangeChange,
  zoomEnabled = true,
  panEnabled = true,
  width = 800,
  height = 400,
  className = '',
  theme = 'light',
  responsive = true,
  animation = true,
  dataTestId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const volumeCanvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const volumeChartRef = useRef<Chart | null>(null)
  const [crosshairPos, setCrosshairPos] = useState<{ x: number; y: number } | null>(null)

  // Filter data by time range
  const filteredData = useMemo(() => {
    if (!timeRange) return data

    const start = new Date(timeRange.start).getTime()
    const end = new Date(timeRange.end).getTime()

    return data.filter(d => {
      const timestamp = new Date(d.timestamp).getTime()
      return timestamp >= start && timestamp <= end
    })
  }, [data, timeRange])

  // Calculate technical indicators
  const indicatorsData = useMemo(() => {
    const result: any = {}

    technicalIndicators.forEach(indicator => {
      if (!indicator.visible) return

      switch (indicator.type) {
        case 'SMA':
          result.SMA = calculateSMA(filteredData, indicator.params?.period || 20)
          break
        case 'EMA':
          result.EMA = calculateEMA(filteredData, indicator.params?.period || 20)
          break
        case 'MACD':
          result.MACD = calculateMACD(filteredData)
          break
        case 'RSI':
          result.RSI = calculateRSI(filteredData, indicator.params?.period || 14)
          break
        case 'BB':
          result.BB = calculateBollingerBands(
            filteredData,
            indicator.params?.period || 20,
            indicator.params?.stdDev || 2
          )
          break
      }
    })

    return result
  }, [filteredData, technicalIndicators])

  // Theme colors
  const themeColors = useMemo(() => {
    return theme === 'dark'
      ? {
          grid: 'rgba(255, 255, 255, 0.1)',
          text: 'rgba(255, 255, 255, 0.8)',
          background: '#1f1f1f',
          upColor: '#26a69a',
          downColor: '#ef5350',
          volumeUp: 'rgba(38, 166, 154, 0.5)',
          volumeDown: 'rgba(239, 83, 80, 0.5)'
        }
      : {
          grid: 'rgba(0, 0, 0, 0.1)',
          text: 'rgba(0, 0, 0, 0.8)',
          background: '#ffffff',
          upColor: '#26a69a',
          downColor: '#ef5350',
          volumeUp: 'rgba(38, 166, 154, 0.5)',
          volumeDown: 'rgba(239, 83, 80, 0.5)'
        }
  }, [theme])

  // Candlestick style
  const candleColors = useMemo(() => ({
    upColor: candlestickStyle.upColor || themeColors.upColor,
    downColor: candlestickStyle.downColor || themeColors.downColor,
    borderUpColor: candlestickStyle.borderUpColor || themeColors.upColor,
    borderDownColor: candlestickStyle.borderDownColor || themeColors.downColor,
    wickUpColor: candlestickStyle.wickUpColor || themeColors.upColor,
    wickDownColor: candlestickStyle.wickDownColor || themeColors.downColor
  }), [candlestickStyle, themeColors])

  // Prepare chart data
  const chartData = useMemo(() => {
    const datasets = [
      {
        label: 'Price',
        type: 'candlestick',
        data: filteredData.map(d => ({
          x: d.timestamp,
          o: d.open,
          h: d.high,
          l: d.low,
          c: d.close
        })),
        ...candleColors
      }
    ]

    // Add technical indicators
    technicalIndicators.forEach((indicator, index) => {
      if (!indicator.visible) return

      const color = indicator.color || `hsl(${index * 60}, 70%, 50%)`

      switch (indicator.type) {
        case 'SMA':
          if (indicatorsData.SMA) {
            datasets.push({
              label: `SMA(${indicator.params?.period || 20})`,
              type: 'line',
              data: indicatorsData.SMA.map((value, i) => ({
                x: filteredData[i + (indicator.params?.period || 20) - 1].timestamp,
                y: value
              })),
              borderColor: color,
              borderWidth: 2,
              fill: false,
              pointRadius: 0
            })
          }
          break
        case 'EMA':
          if (indicatorsData.EMA) {
            datasets.push({
              label: `EMA(${indicator.params?.period || 20})`,
              type: 'line',
              data: indicatorsData.EMA.map((value, i) => ({
                x: filteredData[i + (indicator.params?.period || 20) - 1].timestamp,
                y: value
              })),
              borderColor: color,
              borderWidth: 2,
              fill: false,
              pointRadius: 0
            })
          }
          break
        case 'BB':
          if (indicatorsData.BB) {
            datasets.push({
              label: 'BB Upper',
              type: 'line',
              data: indicatorsData.BB.upperBand.map((value, i) => ({
                x: filteredData[i + 19].timestamp,
                y: value
              })),
              borderColor: color,
              borderWidth: 1,
              fill: false,
              pointRadius: 0
            })
            datasets.push({
              label: 'BB Lower',
              type: 'line',
              data: indicatorsData.BB.lowerBand.map((value, i) => ({
                x: filteredData[i + 19].timestamp,
                y: value
              })),
              borderColor: color,
              borderWidth: 1,
              fill: '-1', // Fill to previous dataset
              backgroundColor: `${color}20`,
              pointRadius: 0
            })
          }
          break
      }
    })

    return { datasets }
  }, [filteredData, technicalIndicators, indicatorsData, candleColors])

  // Volume chart data
  const volumeChartData = useMemo(() => {
    if (!showVolume || !volumeData) return null

    return {
      datasets: [
        {
          label: 'Volume',
          type: 'bar',
          data: volumeData.map(d => ({
            x: d.timestamp,
            y: d.volume,
            backgroundColor: d.close >= d.open ? themeColors.volumeUp : themeColors.volumeDown
          }))
        }
      ]
    }
  }, [showVolume, volumeData, themeColors])

  // Chart configuration
  const chartConfig = useMemo(() => ({
    type: 'candlestick' as const,
    data: chartData,
    options: {
      responsive,
      maintainAspectRatio: false,
      animation: animation ? {
        duration: 1000,
        easing: 'easeInOutQuart'
      } : false,
      scales: {
        x: {
          type: 'time',
          time: {
            displayFormats: {
              hour: 'HH:mm',
              day: 'MM/dd',
              week: 'MM/dd',
              month: 'yyyy-MM'
            }
          },
          grid: {
            display: showGrid,
            color: themeColors.grid
          },
          ticks: {
            color: themeColors.text,
            font: {
              family: 'Inter, sans-serif',
              size: 10
            }
          }
        },
        y: {
          position: 'right',
          grid: {
            display: showGrid,
            color: themeColors.grid
          },
          ticks: {
            color: themeColors.text,
            font: {
              family: 'Inter, sans-serif',
              size: 10
            },
            callback: (value: number) => value.toFixed(2)
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: themeColors.text,
            font: {
              family: 'Inter, sans-serif',
              size: 12
            },
            usePointStyle: true
          }
        },
        tooltip: {
          enabled: showTooltip,
          mode: 'index' as const,
          intersect: false
        },
        crosshair: showCrosshair ? {
          line: {
            color: crosshairStyle.color || themeColors.grid,
            width: crosshairStyle.width || 1,
            dashPattern: crosshairStyle.dash || [5, 5]
          },
          sync: {
            enabled: true,
            group: 'candlestick'
          }
        } : false
      },
      interaction: {
        mode: 'index' as const,
        intersect: false
      },
      onHover: (event: any, activeElements: any[]) => {
        if (showCrosshair && activeElements.length > 0) {
          setCrosshairPos({
            x: activeElements[0].element.x,
            y: activeElements[0].element.y
          })
        } else {
          setCrosshairPos(null)
        }
      },
      onClick: (event: any, activeElements: any[]) => {
        if (activeElements.length > 0 && onCandleClick) {
          const dataIndex = activeElements[0].index
          onCandleClick(filteredData[dataIndex], dataIndex)
        }
      },
      zoom: zoomEnabled ? {
        zoom: {
          wheel: {
            enabled: true
          },
          pinch: {
            enabled: true
          },
          mode: 'x' as const
        },
        pan: {
          enabled: panEnabled,
          mode: 'x' as const
        },
        onZoomComplete: ({ chart }: { chart: Chart }) => {
          if (onTimeRangeChange) {
            const { min, max } = chart.scales.x
            onTimeRangeChange({
              start: new Date(min),
              end: new Date(max)
            })
          }
        }
      } : undefined
    }
  }), [chartData, responsive, animation, showGrid, showTooltip, showCrosshair, crosshairStyle, themeColors, zoomEnabled, panEnabled, onCandleClick, onTimeRangeChange])

  // Volume chart configuration
  const volumeChartConfig = useMemo(() => {
    if (!volumeChartData) return null

    return {
      type: 'bar' as const,
      data: volumeChartData,
      options: {
        responsive,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              displayFormats: {
                hour: 'HH:mm',
                day: 'MM/dd'
              }
            },
            grid: {
              display: false
            },
            ticks: {
              display: false
            }
          },
          y: {
            position: 'right',
            grid: {
              color: themeColors.grid
            },
            ticks: {
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 10
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: false
          }
        }
      }
    }
  }, [volumeChartData, responsive, themeColors])

  // Initialize charts
  useEffect(() => {
    if (!canvasRef.current) return

    const chart = new Chart(canvasRef.current, chartConfig)
    chartRef.current = chart

    // Initialize volume chart if enabled
    if (showVolume && volumeCanvasRef.current && volumeChartConfig) {
      const volumeChart = new Chart(volumeCanvasRef.current, volumeChartConfig)
      volumeChartRef.current = volumeChart
    }

    return () => {
      chart.destroy()
      if (volumeChartRef.current) {
        volumeChartRef.current.destroy()
      }
    }
  }, [chartConfig, showVolume, volumeChartConfig])

  const mainChartHeight = showVolume ? `${100 - volumeHeight}%` : '100%'

  return (
    <div
      className={`candlestick-chart-container ${className}`}
      data-testid={dataTestId}
      style={{ width, height }}
    >
      <div style={{ height: mainChartHeight, position: 'relative' }}>
        <canvas ref={canvasRef} />
        {showCrosshair && crosshairPos && (
          <div
            className="crosshair"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              pointerEvents: 'none'
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: crosshairPos.x,
                top: 0,
                bottom: 0,
                width: 1,
                backgroundColor: crosshairStyle.color || themeColors.grid
              }}
            />
            <div
              style={{
                position: 'absolute',
                top: crosshairPos.y,
                left: 0,
                right: 0,
                height: 1,
                backgroundColor: crosshairStyle.color || themeColors.grid
              }}
            />
          </div>
        )}
      </div>
      {showVolume && volumeData && (
        <div style={{ height: `${volumeHeight}%`, position: 'relative' }}>
          <canvas ref={volumeCanvasRef} />
        </div>
      )}
    </div>
  )
}

export default CandlestickChart