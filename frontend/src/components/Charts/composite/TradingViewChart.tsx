import React, { useState, useEffect, useMemo } from 'react'
import { Card } from '../../../components/ui/Card'
import { Button } from '../../../components/ui/Button'
import { Badge } from '../../../components/ui/Badge'
import {
  ArrowPathIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  ChartBarIcon,
  SunIcon,
  MoonIcon,
  EyeIcon,
  EyeSlashIcon,
  AdjustmentsHorizontalIcon,
  CameraIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline'

// Import chart components
import CandlestickChart from '../plotly/CandlestickChart'
import VolumeChart from '../plotly/VolumeChart'
import LineChart from '../chartjs/LineChart'
import { useRealtimeChart } from '../../../hooks/chart'
import type { OHLCDataPoint, TechnicalIndicator } from '../../../types/chart'

interface TradingViewChartProps {
  symbol?: string
  height?: number
  showVolume?: boolean
  enableRealtime?: boolean
  defaultIndicators?: TechnicalIndicator[]
  onTimeRangeChange?: (range: [Date, Date]) => void
}

const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol = 'BTC/USDT',
  height = 600,
  showVolume = true,
  enableRealtime = true,
  defaultIndicators = [],
  onTimeRangeChange
}) => {
  // State management
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [showTechnicalIndicators, setShowTechnicalIndicators] = useState(true)
  const [showVolumeBars, setShowVolumeBars] = useState(showVolume)
  const [chartType, setChartType] = useState<'candlestick' | 'line'>('candlestick')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [timeRange, setTimeRange] = useState<string>('1D')

  // Mock OHLC data generation
  const generateMockOHLCData = (count: number): OHLCDataPoint[] => {
    const data: OHLCDataPoint[] = []
    const now = new Date()
    let lastClose = 50000 // Starting price

    for (let i = count - 1; i >= 0; i--) {
      const timestamp = new Date(now)
      timestamp.setMinutes(timestamp.getMinutes() - i)

      const volatility = 0.02
      const trend = Math.sin(i * 0.1) * 0.01

      const open = lastClose * (1 + (Math.random() - 0.5) * volatility)
      const close = open * (1 + trend + (Math.random() - 0.5) * volatility)
      const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5)
      const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5)

      data.push({
        timestamp,
        open: Math.round(open * 2) / 2,
        high: Math.round(high * 2) / 2,
        low: Math.round(low * 2) / 2,
        close: Math.round(close * 2) / 2,
        volume: Math.round(Math.random() * 1000000 + 500000)
      })

      lastClose = close
    }

    return data
  }

  // Generate mock data based on time range
  const dataPoints = useMemo(() => {
    const ranges: Record<string, number> = {
      '1H': 60,
      '4H': 240,
      '1D': 1440,
      '1W': 10080,
      '1M': 43200
    }
    return ranges[timeRange] || 1440
  }, [timeRange])

  const ohlcData = useMemo(() => generateMockOHLCData(dataPoints), [dataPoints])
  const volumeData = useMemo(() => ohlcData.map(d => ({
    timestamp: d.timestamp,
    volume: d.volume
  })), [ohlcData])

  // Generate technical indicators
  const technicalIndicators: TechnicalIndicator[] = useMemo(() => {
    if (!showTechnicalIndicators) return []

    const prices = ohlcData.map(d => d.close)

    // Simple Moving Average (20)
    const sma20 = prices.map((_, i) => {
      if (i < 19) return null
      const sum = prices.slice(i - 19, i + 1).reduce((a, b) => a + b, 0)
      return sum / 20
    })

    // Simple Moving Average (50)
    const sma50 = prices.map((_, i) => {
      if (i < 49) return null
      const sum = prices.slice(i - 49, i + 1).reduce((a, b) => a + b, 0)
      return sum / 50
    })

    return [
      {
        name: 'MA20',
        data: sma20 as number[],
        type: 'overlay' as const,
        color: '#1890ff'
      },
      {
        name: 'MA50',
        data: sma50 as number[],
        type: 'overlay' as const,
        color: '#52c41a'
      }
    ]
  }, [ohlcData, showTechnicalIndicators])

  // Real-time data management
  const {
    data: realtimeData,
    isConnected,
    togglePause,
    isPaused,
    exportToCSV,
    exportToJSON
  } = useRealtimeChart({
    channelId: `market-data-${symbol}`,
    maxDataPoints: 1000,
    enableRealtime
  })

  // Chart dimensions
  const candlestickHeight = showVolumeBars ? height * 0.7 : height
  const volumeHeight = showVolumeBars ? height * 0.3 : 0

  // Toggle theme
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  // Toggle fullscreen
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  // Time range options
  const timeRanges = [
    { label: '1小时', value: '1H' },
    { label: '4小时', value: '4H' },
    { label: '1天', value: '1D' },
    { label: '1周', value: '1W' },
    { label: '1月', value: '1M' }
  ]

  return (
    <Card className={`${isFullscreen ? 'fixed inset-0 z-50 m-0' : ''} transition-all duration-300`}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {symbol}
              </h2>
              <Badge variant={isConnected ? 'success' : 'destructive'} className="text-xs">
                {isConnected ? '实时' : '离线'}
              </Badge>
              {isPaused && (
                <Badge variant="warning" className="text-xs">
                  已暂停
                </Badge>
              )}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">最后价格:</span>
                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                  ${ohlcData[ohlcData.length - 1]?.close.toLocaleString() || '--'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Time range selector */}
              <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                {timeRanges.map(range => (
                  <button
                    key={range.value}
                    onClick={() => setTimeRange(range.value)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      timeRange === range.value
                        ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              {/* Chart type selector */}
              <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setChartType('candlestick')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    chartType === 'candlestick'
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  K线
                </button>
                <button
                  onClick={() => setChartType('line')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    chartType === 'line'
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  线图
                </button>
              </div>

              {/* Action buttons */}
              <Button
                variant="outline"
                size="sm"
                onClick={togglePause}
              >
                {isPaused ? (
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                ) : (
                  <EyeSlashIcon className="h-4 w-4 mr-1" />
                )}
                {isPaused ? '继续' : '暂停'}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={toggleTheme}
              >
                {theme === 'light' ? (
                  <MoonIcon className="h-4 w-4" />
                ) : (
                  <SunIcon className="h-4 w-4" />
                )}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={toggleFullscreen}
              >
                {isFullscreen ? (
                  <ArrowsPointingInIcon className="h-4 w-4" />
                ) : (
                  <ArrowsPointingOutIcon className="h-4 w-4" />
                )}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Settings panel */}
        {showSettings && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <div className="grid grid-cols-3 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={showTechnicalIndicators}
                  onChange={(e) => setShowTechnicalIndicators(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">显示技术指标</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={showVolumeBars}
                  onChange={(e) => setShowVolumeBars(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">显示成交量</span>
              </label>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportToCSV}
                >
                  <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                  导出CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportToJSON}
                >
                  <CameraIcon className="h-4 w-4 mr-1" />
                  导出JSON
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Chart container */}
        <div className="flex-1 p-4" style={{ height: isFullscreen ? 'calc(100vh - 140px)' : `${height}px` }}>
          <div className="h-full space-y-2">
            {/* Main chart */}
            <div style={{ height: `${candlestickHeight}px` }}>
              {chartType === 'candlestick' ? (
                <CandlestickChart
                  data={ohlcData}
                  volume={showVolumeBars ? volumeData.map(d => d.volume) : undefined}
                  indicators={technicalIndicators}
                  theme={theme}
                  height={candlestickHeight}
                  onTimeRangeChange={onTimeRangeChange}
                />
              ) : (
                <LineChart
                  data={{
                    labels: ohlcData.map(d => d.timestamp),
                    datasets: [{
                      label: '价格',
                      data: ohlcData.map(d => d.close),
                      borderColor: theme === 'light' ? '#1890ff' : '#177ddc',
                      backgroundColor: theme === 'light' ? '#1890ff20' : '#177ddc20',
                      tension: 0.1,
                      fill: false
                    }, ...technicalIndicators.map(ind => ({
                      label: ind.name,
                      data: ind.data,
                      borderColor: ind.color,
                      backgroundColor: 'transparent',
                      borderDash: [5, 5],
                      tension: 0.1,
                      pointRadius: 0
                    }))]
                  }}
                  theme={theme}
                  height={candlestickHeight}
                  showPoints={false}
                />
              )}
            </div>

            {/* Volume chart */}
            {showVolumeBars && (
              <div style={{ height: `${volumeHeight}px` }}>
                <VolumeChart
                  data={volumeData}
                  theme={theme}
                  height={volumeHeight}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}

export default TradingViewChart