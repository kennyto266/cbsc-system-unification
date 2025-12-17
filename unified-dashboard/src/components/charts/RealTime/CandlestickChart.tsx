import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
  Plugin
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { Card, Select, Space, Button, Switch, Tag, Slider, Row, Col, Radio } from 'antd'
import {
  DownloadOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  UndoOutlined,
  ExpandOutlined
} from '@ant-design/icons'
import { useWebSocket } from '../../../hooks/useWebSocket'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

// OHLC data interface
export interface OHLCData {
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// Chart types
export type ChartType = 'candlestick' | 'ohlc' | 'line' | 'area'

// Timeframe options
export interface TimeframeOption {
  label: string
  value: string
  milliseconds: number
}

const TIMEFRAME_OPTIONS: TimeframeOption[] = [
  { label: '1分', value: '1m', milliseconds: 60000 },
  { label: '5分', value: '5m', milliseconds: 300000 },
  { label: '15分', value: '15m', milliseconds: 900000 },
  { label: '30分', value: '30m', milliseconds: 1800000 },
  { label: '1小時', value: '1h', milliseconds: 3600000 },
  { label: '4小時', value: '4h', milliseconds: 14400000 },
  { label: '1天', value: '1d', milliseconds: 86400000 },
  { label: '1周', value: '1w', milliseconds: 604800000 }
]

// Candlestick plugin for Chart.js
const candlestickPlugin: Plugin<'bar'> = {
  id: 'candlestick',
  afterDraw: (chart) => {
    const { ctx, chartArea, scales, data } = chart
    if (!chartArea || !scales.x || !scales.y) return

    const meta = chart.getDatasetMeta(0)
    if (!meta || meta.hidden) return

    const bars = meta.data as any[]
    ctx.save()

    bars.forEach((bar, index) => {
      const { x, width } = bar
      const ohlc = data.datasets[0].data[index] as any

      if (!ohlc) return

      const { open, high, low, close } = ohlc
      const yScale = scales.y
      const barWidth = width * 0.8
      const wickWidth = 1

      // Determine color
      const isGreen = close > open
      const color = isGreen ? '#10B981' : '#EF4444'

      // Draw wick
      ctx.strokeStyle = color
      ctx.lineWidth = wickWidth
      ctx.beginPath()
      ctx.moveTo(x, yScale.getPixelForValue(high))
      ctx.lineTo(x, yScale.getPixelForValue(low))
      ctx.stroke()

      // Draw body
      ctx.fillStyle = isGreen ? color : `${color}20`
      ctx.strokeStyle = color
      ctx.lineWidth = 1

      const bodyTop = yScale.getPixelForValue(Math.max(open, close))
      const bodyBottom = yScale.getPixelForValue(Math.min(open, close))
      const bodyHeight = Math.abs(bodyBottom - bodyTop)

      if (isGreen) {
        ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight)
      } else {
        ctx.strokeRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight)
        ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight)
      }
    })

    ctx.restore()
  }
}

// Register plugin
ChartJS.register(candlestickPlugin)

// Props interface
export interface CandlestickChartProps {
  symbol: string
  data: OHLCData[]
  timeframe?: string
  chartType?: ChartType
  showVolume?: boolean
  showMA?: boolean
  maPeriods?: number[]
  height?: number
  realTime?: boolean
  theme?: 'light' | 'dark'
  onTimeframeChange?: (timeframe: string) => void
  onChartTypeChange?: (type: ChartType) => void
  onSymbolChange?: (symbol: string) => void
}

// Main component
const CandlestickChart: React.FC<CandlestickChartProps> = ({
  symbol,
  data,
  timeframe = '1h',
  chartType = 'candlestick',
  showVolume = true,
  showMA = true,
  maPeriods = [20, 50, 200],
  height = 400,
  realTime = true,
  theme = 'light',
  onTimeframeChange,
  onChartTypeChange,
  onSymbolChange
}) => {
  const [isPlaying, setIsPlaying] = useState(realTime)
  const [showSettings, setShowSettings] = useState(false)
  const [zoomLevel, setZoomLevel] = useState(100)
  const [chartData, setChartData] = useState<OHLCData[]>(data)
  const [selectedMA, setSelectedMA] = useState(maPeriods)
  const chartRef = useRef<ChartJS>(null)
  const volumeChartRef = useRef<ChartJS>(null)
  const { isConnected, subscribe, unsubscribe } = useWebSocket()

  // Calculate Moving Averages
  const calculateMA = useCallback((data: OHLCData[], period: number): number[] => {
    const ma: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        ma.push(NaN)
      } else {
        const sum = data.slice(i - period + 1, i + 1)
          .reduce((acc, d) => acc + d.close, 0)
        ma.push(sum / period)
      }
    }
    return ma
  }, [])

  // Memoized MA data
  const maData = useMemo(() => {
    const result: Record<number, number[]> = {}
    selectedMA.forEach(period => {
      result[period] = calculateMA(chartData, period)
    })
    return result
  }, [chartData, selectedMA, calculateMA])

  // WebSocket subscription
  useEffect(() => {
    if (realTime && isConnected) {
      const channel = `ohlc.${symbol}.${timeframe}`

      const handleOHLCUpdate = (newData: OHLCData) => {
        setChartData(prevData => {
          const updated = [...prevData]
          const lastCandle = updated[updated.length - 1]

          // Update last candle if same timeframe, or add new
          const isNewCandle = !lastCandle ||
            newData.timestamp.getTime() - lastCandle.timestamp.getTime() >=
            TIMEFRAME_OPTIONS.find(t => t.value === timeframe)?.milliseconds!

          if (isNewCandle) {
            updated.push(newData)
            if (updated.length > 1000) {
              updated.shift() // Keep last 1000 candles
            }
          } else {
            updated[updated.length - 1] = newData
          }

          return updated
        })
      }

      subscribe(channel, handleOHLCUpdate)

      return () => {
        unsubscribe(channel, handleOHLCUpdate)
      }
    }
  }, [realTime, isConnected, symbol, timeframe, subscribe, unsubscribe])

  // Chart data preparation
  const chartDataForRender = useMemo(() => {
    const labels = chartData.map(d =>
      d.timestamp.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit'
      })
    )

    const datasets: any[] = []

    // OHLC/Candlestick data
    if (chartType === 'candlestick' || chartType === 'ohlc') {
      datasets.push({
        label: `${symbol} Price`,
        data: chartData.map(d => ({
          x: d.timestamp,
          o: d.open,
          h: d.high,
          l: d.low,
          c: d.close
        })),
        type: 'candlestick' as any,
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        barPercentage: 0.8,
        categoryPercentage: 0.9
      })
    } else if (chartType === 'line' || chartType === 'area') {
      datasets.push({
        label: `${symbol} Price`,
        data: chartData.map(d => d.close),
        borderColor: '#3B82F6',
        backgroundColor: chartType === 'area' ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
        fill: chartType === 'area'
      })
    }

    // Moving averages
    if (showMA) {
      const maColors = ['#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']
      selectedMA.forEach((period, index) => {
        const maValues = maData[period] || []
        if (maValues.length > 0) {
          datasets.push({
            label: `MA${period}`,
            data: maValues,
            borderColor: maColors[index % maColors.length],
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            pointRadius: 0,
            pointHoverRadius: 3,
            tension: 0.1
          })
        }
      })
    }

    return { labels, datasets }
  }, [chartData, chartType, showMA, selectedMA, maData, symbol])

  // Volume chart data
  const volumeChartData = useMemo(() => {
    const labels = chartData.map(d =>
      d.timestamp.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit'
      })
    )

    const volumes = chartData.map(d => d.volume)
    const maxVolume = Math.max(...volumes)

    // Color based on candle direction
    const backgroundColors = chartData.map((d, i) => {
      if (i === 0) return 'rgba(156, 163, 175, 0.6)'
      return d.close >= d.open
        ? 'rgba(16, 185, 129, 0.6)'
        : 'rgba(239, 68, 68, 0.6)'
    })

    return {
      labels,
      datasets: [{
        label: 'Volume',
        data: volumes,
        backgroundColor: backgroundColors,
        borderColor: backgroundColors.map(c => c.replace('0.6', '1')),
        borderWidth: 1,
        barPercentage: 0.8,
        categoryPercentage: 0.9
      }]
    }
  }, [chartData])

  // Chart options
  const chartOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    animation: false, // Disable for performance
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 10,
          font: {
            size: 11
          },
          color: theme === 'dark' ? '#fff' : '#374151'
        }
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: function(context) {
            const index = context.dataIndex
            const candle = chartData[index]

            if (candle) {
              return [
                `O: ${candle.open.toFixed(2)}`,
                `H: ${candle.high.toFixed(2)}`,
                `L: ${candle.low.toFixed(2)}`,
                `C: ${candle.close.toFixed(2)}`,
                `V: ${candle.volume.toLocaleString()}`
              ]
            }

            return `${context.dataset.label}: ${context.parsed.y?.toFixed(2)}`
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        },
        ticks: {
          maxTicksLimit: 10,
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280'
        }
      },
      y: {
        display: true,
        position: 'left' as const,
        grid: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280',
          callback: function(value) {
            return `$${(value as number).toFixed(2)}`
          }
        }
      }
    }
  }

  // Volume chart options
  const volumeOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.8)',
        padding: 8,
        cornerRadius: 4,
        callbacks: {
          label: function(context) {
            return `Volume: ${(context.parsed.y as number).toLocaleString()}`
          }
        }
      }
    },
    scales: {
      x: {
        display: false
      },
      y: {
        display: true,
        position: 'right' as const,
        grid: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280'
        }
      }
    }
  }

  // Current price and change
  const currentPrice = chartData.length > 0 ? chartData[chartData.length - 1].close : 0
  const priceChange = chartData.length > 1
    ? ((currentPrice - chartData[chartData.length - 2].close) / chartData[chartData.length - 2].close) * 100
    : 0

  // Export chart
  const handleExport = () => {
    const canvas = chartRef.current?.canvas
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `${symbol}-${timeframe}-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  // Zoom controls
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 10, 200))
  }

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 10, 50))
  }

  const handleResetZoom = () => {
    setZoomLevel(100)
  }

  return (
    <Card
      className="candlestick-chart"
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-lg font-semibold">
              {symbol}
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold">
                ${currentPrice.toFixed(2)}
              </span>
              <Tag color={priceChange >= 0 ? 'green' : 'red'}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </Tag>
            </div>
          </div>
          {isPlaying && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500">
                Real-time
              </span>
            </div>
          )}
        </div>
      }
      extra={
        <Space>
          <Select
            value={timeframe}
            onChange={onTimeframeChange}
            style={{ width: 80 }}
            size="small"
          >
            {TIMEFRAME_OPTIONS.map(option => (
              <Select.Option key={option.value} value={option.value}>
                {option.label}
              </Select.Option>
            ))}
          </Select>

          <Radio.Group
            value={chartType}
            onChange={(e) => onChartTypeChange?.(e.target.value)}
            size="small"
          >
            <Radio.Button value="candlestick" icon={<BarChartOutlined />}>K</Radio.Button>
            <Radio.Button value="line" icon={<LineChartOutlined />}>L</Radio.Button>
          </Radio.Group>

          <Button
            type="text"
            size="small"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setIsPlaying(!isPlaying)}
          />

          <Button
            type="text"
            size="small"
            icon={<ZoomOutOutlined />}
            onClick={handleZoomOut}
          />

          <span className="text-sm">{zoomLevel}%</span>

          <Button
            type="text"
            size="small"
            icon={<ZoomInOutlined />}
            onClick={handleZoomIn}
          />

          <Button
            type="text"
            size="small"
            icon={<UndoOutlined />}
            onClick={handleResetZoom}
          />

          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          />
        </Space>
      }
    >
      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <label className="block text-sm font-medium mb-2">
                Moving Averages
              </label>
              <Space wrap>
                {[5, 10, 20, 50, 100, 200].map(period => (
                  <Button
                    key={period}
                    size="small"
                    type={selectedMA.includes(period) ? 'primary' : 'default'}
                    onClick={() => {
                      setSelectedMA(prev =>
                        prev.includes(period)
                          ? prev.filter(p => p !== period)
                          : [...prev, period]
                      )
                    }}
                  >
                    MA{period}
                  </Button>
                ))}
              </Space>
            </Col>
            <Col span={12}>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Show Volume
                </label>
                <Switch
                  checked={showVolume}
                  onChange={(checked) => {/* Handle toggle */}}
                />
              </div>
            </Col>
          </Row>
        </div>
      )}

      {/* Price Chart */}
      <div style={{ height: showVolume ? height - 100 : height }}>
        {chartType === 'candlestick' || chartType === 'ohlc' ? (
          <Bar
            ref={chartRef}
            data={chartDataForRender}
            options={chartOptions}
          />
        ) : (
          <Line
            ref={chartRef}
            data={chartDataForRender}
            options={chartOptions}
          />
        )}
      </div>

      {/* Volume Chart */}
      {showVolume && (
        <div style={{ height: 100, marginTop: 10 }}>
          <Bar
            ref={volumeChartRef}
            data={volumeChartData}
            options={volumeOptions}
          />
        </div>
      )}
    </Card>
  )
}

export default CandlestickChart