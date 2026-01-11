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
  TimeScale,
  ChartOptions,
  ChartData,
  AnimationOptions
} from 'chart.js'
import { Line, Bar, Scatter } from 'react-chartjs-2'
import { Card, Select, Space, Button, Switch, Tag, Slider, Row, Col, Tooltip as AntTooltip } from 'antd'
import {
  DownloadOutlined,
  LineChartOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  FullscreenOutlined,
  SyncOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { debounce } from 'lodash'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { IndicatorType, TechnicalIndicator, IndicatorCategory } from '../../../types/technical-indicators'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

// Chart data point interface
export interface ChartDataPoint {
  timestamp: Date
  value: number
  volume?: number
  high?: number
  low?: number
  open?: number
  close?: number
}

// Technical indicator data interface
export interface IndicatorData {
  id: string
  type: IndicatorType
  name: string
  data: number[]
  color?: string
  visible: boolean
  parameters: Record<string, any>
}

// Props interface
export interface TechnicalIndicatorChartProps {
  symbol: string
  timeframe: string
  indicators: IndicatorData[]
  priceData: ChartDataPoint[]
  height?: number
  showVolume?: boolean
  showSettings?: boolean
  realTime?: boolean
  theme?: 'light' | 'dark'
  onIndicatorChange?: (indicators: IndicatorData[]) => void
  exportOptions?: {
    enabled: boolean
    formats: ('png' | 'jpg' | 'svg')[]
  }
}

// High-performance animation configuration
const HIGH_PERFORMANCE_ANIMATION: AnimationOptions = {
  duration: 0, // Disable animations for real-time updates
  easing: 'linear',
  // Progressive rendering for large datasets
  onProgress: (animation) => {
    if (animation.currentStep > 0 && animation.currentStep < animation.numSteps) {
      // Cancel animation if too many updates
      if (animation.numSteps > 100) {
        return false
      }
    }
    return true
  }
}

// Optimized chart options for real-time data
const getOptimizedChartOptions = (isDarkMode: boolean): ChartOptions<'line'> => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  animation: false, // Disable for real-time performance
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 10,
        font: {
          size: 11,
          family: 'system-ui'
        },
        color: isDarkMode ? '#fff' : '#374151'
      }
    },
    title: {
      display: false
    },
    tooltip: {
      backgroundColor: isDarkMode ? 'rgba(0, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      cornerRadius: 8,
      titleFont: {
        size: 12,
        weight: 'bold'
      },
      bodyFont: {
        size: 11
      },
      callbacks: {
        label: function(context) {
          const value = context.parsed.y
          const indicator = context.dataset.label
          return `${indicator}: ${typeof value === 'number' ? value.toFixed(4) : value}`
        }
      }
    },
    // Performance optimization: Disable unused plugins
    filler: false,
    decimation: {
      enabled: true,
      algorithm: 'lttb', // Largest-Triangle-Three-Buckets algorithm
      samples: 1000
    }
  },
  scales: {
    x: {
      type: 'time' as const,
      time: {
        displayFormats: {
          second: 'HH:mm:ss',
          minute: 'HH:mm',
          hour: 'HH:mm',
          day: 'MM/dd'
        }
      },
      display: true,
      grid: {
        display: false, // Hide for performance
        drawBorder: false
      },
      ticks: {
        maxTicksLimit: 10, // Limit ticks for performance
        color: isDarkMode ? '#9CA3AF' : '#6B7280'
      }
    },
    y: {
      display: true,
      position: 'left' as const,
      grid: {
        color: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
        drawBorder: false
      },
      ticks: {
        maxTicksLimit: 8,
        color: isDarkMode ? '#9CA3AF' : '#6B7280',
        callback: function(value) {
          return typeof value === 'number' ? value.toFixed(2) : value
        }
      }
    }
  },
  // Performance optimizations
  parsing: false,
  normalized: true,
  elements: {
    point: {
      radius: 0, // Hide points for better performance with many data points
      hoverRadius: 4
    },
    line: {
      borderWidth: 1.5,
      tension: 0.1
    }
  }
})

// Volume chart options
const getVolumeChartOptions = (isDarkMode: boolean): ChartOptions<'bar'> => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    legend: {
      display: false
    },
    title: {
      display: false
    },
    tooltip: {
      backgroundColor: isDarkMode ? 'rgba(0, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.8)',
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
        color: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
        drawBorder: false
      },
      ticks: {
        color: isDarkMode ? '#9CA3AF' : '#6B7280'
      }
    }
  },
  elements: {
    bar: {
      borderWidth: 0
    }
  }
})

// Main component
const TechnicalIndicatorChart: React.FC<TechnicalIndicatorChartProps> = ({
  symbol,
  timeframe,
  indicators,
  priceData,
  height = 400,
  showVolume = true,
  showSettings = true,
  realTime = true,
  theme = 'light',
  onIndicatorChange,
  exportOptions = { enabled: true, formats: ['png', 'jpg'] }
}) => {
  const [isPlaying, setIsPlaying] = useState(realTime)
  const [showSettingsPanel, setShowSettingsPanel] = useState(false)
  const [maxDataPoints, setMaxDataPoints] = useState(1000)
  const [updateSpeed, setUpdateSpeed] = useState(1000) // ms
  const chartRef = useRef<ChartJS<'line'>>(null)
  const volumeChartRef = useRef<ChartJS<'bar'>>(null)
  const { isConnected, subscribe, unsubscribe } = useWebSocket()

  // Data point management with circular buffer
  const dataBufferRef = useRef<{
    priceData: ChartDataPoint[]
    indicatorData: Map<string, number[]>
  }>({
    priceData: [],
    indicatorData: new Map()
  })

  // Initialize data buffer
  useEffect(() => {
    dataBufferRef.current.priceData = priceData.slice(-maxDataPoints)
    indicators.forEach(indicator => {
      dataBufferRef.current.indicatorData.set(
        indicator.id,
        indicator.data.slice(-maxDataPoints)
      )
    })
  }, [priceData, indicators, maxDataPoints])

  // WebSocket subscription for real-time updates
  useEffect(() => {
    if (realTime && isConnected) {
      const channel = `chart.${symbol}.${timeframe}`

      const handleRealTimeUpdate = (data: any) => {
        // Optimized data update
        if (dataBufferRef.current.priceData.length >= maxDataPoints) {
          dataBufferRef.current.priceData.shift()
        }

        const newPoint: ChartDataPoint = {
          timestamp: new Date(data.timestamp),
          value: data.price,
          volume: data.volume,
          high: data.high,
          low: data.low,
          open: data.open,
          close: data.close
        }

        dataBufferRef.current.priceData.push(newPoint)

        // Update indicator data
        if (data.indicators) {
          Object.entries(data.indicators).forEach(([indicatorId, value]) => {
            const buffer = dataBufferRef.current.indicatorData.get(indicatorId)
            if (buffer) {
              if (buffer.length >= maxDataPoints) {
                buffer.shift()
              }
              buffer.push(value as number)
            }
          })
        }
      }

      subscribe(channel, handleRealTimeUpdate)

      return () => {
        unsubscribe(channel, handleRealTimeUpdate)
      }
    }
  }, [realTime, isConnected, symbol, timeframe, subscribe, unsubscribe, maxDataPoints])

  // Debounced chart update
  const debouncedChartUpdate = useCallback(
    debounce(() => {
      if (chartRef.current) {
        chartRef.current.update('none') // Update without animation
      }
      if (volumeChartRef.current) {
        volumeChartRef.current.update('none')
      }
    }, updateSpeed),
    [updateSpeed]
  )

  // Update charts when data changes
  useEffect(() => {
    debouncedChartUpdate()
  }, [dataBufferRef.current.priceData, debouncedChartUpdate])

  // Memoized price chart data
  const priceChartData = useMemo((): ChartData<'line'> => {
    const labels = dataBufferRef.current.priceData.map(d => d.timestamp)
    const datasets = [
      {
        label: `${symbol} Price`,
        data: dataBufferRef.current.priceData.map(d => d.value),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
        fill: false
      }
    ]

    // Add visible indicators
    indicators
      .filter(ind => ind.visible)
      .forEach(indicator => {
        const data = dataBufferRef.current.indicatorData.get(indicator.id) || []
        datasets.push({
          label: indicator.name,
          data,
          borderColor: indicator.color || '#10B981',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.1,
          fill: false,
          borderDash: indicator.type === IndicatorType.SMA ? [5, 5] : undefined
        })
      })

    return { labels, datasets }
  }, [symbol, indicators])

  // Memoized volume chart data
  const volumeChartData = useMemo((): ChartData<'bar'> => {
    const labels = dataBufferRef.current.priceData.map(d => d.timestamp)
    const volumes = dataBufferRef.current.priceData.map(d => d.volume || 0)

    // Color based on price movement
    const backgroundColors = volumes.map((_, i) => {
      if (i === 0) return 'rgba(156, 163, 175, 0.6)'
      const current = dataBufferRef.current.priceData[i]?.value || 0
      const previous = dataBufferRef.current.priceData[i - 1]?.value || 0
      return current >= previous
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
        borderWidth: 1
      }]
    }
  }, [])

  // Export chart function
  const handleExport = (format: string) => {
    const canvas = chartRef.current?.canvas
    if (canvas) {
      const url = canvas.toDataURL(`image/${format}`)
      const link = document.createElement('a')
      link.download = `${symbol}-${timeframe}-${Date.now()}.${format}`
      link.href = url
      link.click()
    }
  }

  // Toggle indicator visibility
  const toggleIndicator = (indicatorId: string) => {
    const updatedIndicators = indicators.map(ind =>
      ind.id === indicatorId ? { ...ind, visible: !ind.visible } : ind
    )
    onIndicatorChange?.(updatedIndicators)
  }

  // Current price and change
  const currentPrice = dataBufferRef.current.priceData.length > 0
    ? dataBufferRef.current.priceData[dataBufferRef.current.priceData.length - 1].value
    : 0
  const priceChange = dataBufferRef.current.priceData.length > 1
    ? ((currentPrice - dataBufferRef.current.priceData[dataBufferRef.current.priceData.length - 2].value) /
       dataBufferRef.current.priceData[dataBufferRef.current.priceData.length - 2].value) * 100
    : 0

  return (
    <Card
      className="technical-indicator-chart"
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-lg font-semibold">
              {symbol} - {timeframe}
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
                Real-time ({updateSpeed}ms)
              </span>
            </div>
          )}
        </div>
      }
      extra={
        <Space>
          <AntTooltip title="Chart Settings">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setShowSettingsPanel(!showSettingsPanel)}
            />
          </AntTooltip>

          <AntTooltip title="Toggle Real-time">
            <Button
              type="text"
              size="small"
              icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => setIsPlaying(!isPlaying)}
            />
          </AntTooltip>

          {showVolume && (
            <AntTooltip title="Toggle Volume">
              <Switch
                size="small"
                checked={showVolume}
                onChange={(checked) => {/* Handle toggle */}}
              />
            </AntTooltip>
          )}

          {exportOptions.enabled && (
            <Select
              size="small"
              style={{ width: 80 }}
              placeholder="Export"
              onSelect={handleExport}
            >
              {exportOptions.formats.map(format => (
                <Select.Option key={format} value={format}>
                  {format.toUpperCase()}
                </Select.Option>
              ))}
            </Select>
          )}
        </Space>
      }
    >
      {/* Settings Panel */}
      {showSettingsPanel && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Data Points: {maxDataPoints}
                </label>
                <Slider
                  min={100}
                  max={5000}
                  step={100}
                  value={maxDataPoints}
                  onChange={setMaxDataPoints}
                />
              </div>
            </Col>
            <Col span={12}>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Update Speed: {updateSpeed}ms
                </label>
                <Slider
                  min={100}
                  max={5000}
                  step={100}
                  value={updateSpeed}
                  onChange={setUpdateSpeed}
                />
              </div>
            </Col>
          </Row>

          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">
              Active Indicators
            </label>
            <Space wrap>
              {indicators.map(indicator => (
                <Tag
                  key={indicator.id}
                  color={indicator.visible ? indicator.color : 'default'}
                  closable={false}
                  onClick={() => toggleIndicator(indicator.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {indicator.name}
                  <InfoCircleOutlined className="ml-1" />
                </Tag>
              ))}
            </Space>
          </div>
        </div>
      )}

      {/* Price Chart */}
      <div style={{ height: showVolume ? height - 100 : height }}>
        <Line
          ref={chartRef}
          data={priceChartData}
          options={getOptimizedChartOptions(theme === 'dark')}
        />
      </div>

      {/* Volume Chart */}
      {showVolume && (
        <div style={{ height: 100, marginTop: 10 }}>
          <Bar
            ref={volumeChartRef}
            data={volumeChartData}
            options={getVolumeChartOptions(theme === 'dark')}
          />
        </div>
      )}
    </Card>
  )
}

export default TechnicalIndicatorChart