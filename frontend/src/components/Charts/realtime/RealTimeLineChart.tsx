import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale,
  Chart as ChartType
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
import annotationPlugin from 'chartjs-plugin-annotation'
import { RealTimeDataPoint, useRealTimeChart } from '../../hooks/useRealTimeChart'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../utils/chartThemes'
import debounce from 'lodash/debounce'

// Register plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale,
  zoomPlugin,
  annotationPlugin
)

// Extended props for RealTimeLineChart
export interface RealTimeLineChartProps extends Omit<BaseChartProps<'line'>, 'type'> {
  // Real-time data props
  websocketUrl?: string
  channel?: string
  maxDataPoints?: number
  updateInterval?: number

  // Performance optimization props
  enableDataBuffering?: boolean
  bufferSize?: number
  decimationEnabled?: boolean
  decimationThreshold?: number

  // Display props
  showStats?: boolean
  showAlerts?: boolean
  alertThresholds?: {
    upper?: number
    lower?: number
  }

  // Multi-series support
  seriesKey?: string
  compareMode?: boolean
  benchmarkData?: RealTimeDataPoint[]

  // Interaction props
  enableCrosshair?: boolean
  enableZoom?: boolean
  enablePan?: boolean
  zoomMode?: 'x' | 'y' | 'xy'

  // Animation props
  animationDuration?: number
  transitionDuration?: number

  // Callbacks
  onDataUpdate?: (data: RealTimeDataPoint[]) => void
  onAlertTriggered?: (type: 'upper' | 'lower', value: number) => void
}

const RealTimeLineChart: React.FC<RealTimeLineChartProps> = ({
  websocketUrl,
  channel = 'realtime-data',
  maxDataPoints = 1000,
  updateInterval = 100,
  enableDataBuffering = true,
  bufferSize = 100,
  decimationEnabled = true,
  decimationThreshold = 500,
  showStats = true,
  showAlerts = false,
  alertThresholds,
  seriesKey = 'value',
  compareMode = false,
  benchmarkData = [],
  enableCrosshair = true,
  enableZoom = true,
  enablePan = true,
  zoomMode = 'x',
  animationDuration = 0,
  transitionDuration = 75,
  onDataUpdate,
  onAlertTriggered,
  className = '',
  theme = 'light',
  height = 400,
  onDataPointClick,
  onLegendClick,
  ...rest
}) => {
  const chartRef = useRef<ChartType<'line'>>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [visibleRange, setVisibleRange] = useState<{ start: number; end: number } | null>(null)
  const currentTheme = getTheme(theme)

  // Real-time data hook
  const {
    data: realtimeData,
    isConnected,
    isPaused: hookPaused,
    error,
    lastUpdate,
    pause,
    resume,
    clear
  } = useRealTimeChart({
    url: websocketUrl,
    channel,
    maxDataPoints,
    updateInterval
  })

  // Combine real-time data with benchmark
  const combinedData = useMemo(() => {
    const result = realtimeData

    if (compareMode && benchmarkData.length > 0) {
      // Align benchmark data with real-time data
      const alignedBenchmark = benchmarkData.slice(-realtimeData.length)
      return {
        realtime: result,
        benchmark: alignedBenchmark
      }
    }

    return { realtime: result, benchmark: [] }
  }, [realtimeData, benchmarkData, compareMode])

  // Process data for Chart.js
  const chartData = useMemo<ChartData<'line'>>(() => {
    const labels = combinedData.realtime.map(d =>
      new Date(d.timestamp).toLocaleTimeString()
    )

    const datasets = []

    // Main data series
    if (combinedData.realtime.length > 0) {
      datasets.push({
        label: '策略淨值',
        data: combinedData.realtime.map(d => d[seriesKey] || d.value),
        borderColor: currentTheme.colors[0],
        backgroundColor: currentTheme.colors[0] + '20',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
        fill: false,
        decimation: decimationEnabled ? {
          enabled: true,
          algorithm: 'lttb',
          threshold: decimationThreshold
        } : undefined
      })
    }

    // Benchmark data series
    if (compareMode && combinedData.benchmark.length > 0) {
      datasets.push({
        label: '基準',
        data: combinedData.benchmark.map(d => d[seriesKey] || d.value),
        borderColor: currentTheme.colors[1],
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1,
        fill: false,
        borderDash: [5, 5]
      })
    }

    // Calculate and add moving averages
    if (combinedData.realtime.length >= 20) {
      const ma20 = calculateMovingAverage(combinedData.realtime.map(d => d[seriesKey] || d.value), 20)
      const ma50 = combinedData.realtime.length >= 50
        ? calculateMovingAverage(combinedData.realtime.map(d => d[seriesKey] || d.value), 50)
        : null

      datasets.push({
        label: 'MA20',
        data: ma20,
        borderColor: currentTheme.colors[2],
        backgroundColor: 'transparent',
        borderWidth: 1,
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0.1,
        fill: false
      })

      if (ma50) {
        datasets.push({
          label: 'MA50',
          data: ma50,
          borderColor: currentTheme.colors[3],
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0.1,
          fill: false
        })
      }
    }

    return { labels, datasets }
  }, [combinedData, currentTheme.colors, decimationEnabled, decimationThreshold, seriesKey])

  // Calculate moving average
  function calculateMovingAverage(data: number[], period: number): number[] {
    const result: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null as any)
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
        result.push(sum / period)
      }
    }
    return result
  }

  // Calculate statistics
  const stats = useMemo(() => {
    if (combinedData.realtime.length === 0) return null

    const values = combinedData.realtime.map(d => d[seriesKey] || d.value)
    const lastValue = values[values.length - 1]
    const firstValue = values[0]
    const change = lastValue - firstValue
    const changePercent = ((change / firstValue) * 100).toFixed(2)

    const max = Math.max(...values)
    const min = Math.min(...values)
    const avg = values.reduce((a, b) => a + b, 0) / values.length

    return {
      current: lastValue.toFixed(4),
      change: change.toFixed(4),
      changePercent,
      high: max.toFixed(4),
      low: min.toFixed(4),
      avg: avg.toFixed(4)
    }
  }, [combinedData.realtime, seriesKey])

  // Check for alerts
  useEffect(() => {
    if (showAlerts && alertThresholds && stats) {
      const currentValue = parseFloat(stats.current)

      if (alertThresholds.upper && currentValue > alertThresholds.upper) {
        onAlertTriggered?.('upper', currentValue)
      }

      if (alertThresholds.lower && currentValue < alertThresholds.lower) {
        onAlertTriggered?.('lower', currentValue)
      }
    }
  }, [stats, showAlerts, alertThresholds, onAlertTriggered])

  // Handle data updates
  useEffect(() => {
    if (onDataUpdate && combinedData.realtime.length > 0) {
      onDataUpdate(combinedData.realtime)
    }
  }, [combinedData.realtime, onDataUpdate])

  // Handle pause/resume
  const handlePauseToggle = useCallback(() => {
    if (isPaused || hookPaused) {
      resume()
      setIsPaused(false)
    } else {
      pause()
      setIsPaused(true)
    }
  }, [isPaused, hookPaused, pause, resume])

  // Debounced zoom handler
  const handleZoom = debounce((chart: ChartType) => {
    const { min, max } = chart.scales.x
    setVisibleRange({ start: min, end: max })
  }, 100)

  // Chart options
  const options: ChartOptions<'line'> = useMemo(() => ({
    ...getChartJsDefaults(currentTheme),
    animation: {
      duration: animationDuration,
      transition: {
        duration: transitionDuration
      }
    },
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDataPointClick) {
        const { datasetIndex, index } = elements[0]
        const dataset = chartData.datasets[datasetIndex]
        const point = {
          dataset,
          value: dataset.data[index],
          label: chartData.labels?.[index],
          datasetIndex,
          index
        }
        onDataPointClick(point, elements[0])
      }
    },
    plugins: {
      ...getChartJsDefaults(currentTheme).plugins,
      legend: {
        ...getChartJsDefaults(currentTheme).plugins.legend,
        onClick: (e, legendItem, legend) => {
          if (onLegendClick) {
            onLegendClick(legendItem, legend)
          } else {
            const index = legendItem.datasetIndex
            const chart = legend.chart
            const meta = chart.getDatasetMeta(index)
            meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null
            chart.update('none')
          }
        }
      },
      tooltip: {
        ...getChartJsDefaults(currentTheme).plugins.tooltip,
        callbacks: {
          title: (context) => {
            const dataIndex = context[0].dataIndex
            return combinedData.realtime[dataIndex]?.timestamp
              ? new Date(combinedData.realtime[dataIndex].timestamp).toLocaleString()
              : context[0].label
          },
          label: (context) => {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 4,
                maximumFractionDigits: 4
              }).format(context.parsed.y)
            }
            return label
          },
          afterLabel: (context) => {
            const dataIndex = context.dataIndex
            const dataPoint = combinedData.realtime[dataIndex]
            if (dataPoint?.metadata) {
              return Object.entries(dataPoint.metadata)
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n')
            }
            return ''
          }
        }
      },
      zoom: enableZoom ? {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true
          },
          mode: zoomMode,
          onZoom: handleZoom
        },
        pan: {
          enabled: enablePan,
          mode: zoomMode,
        }
      } : undefined,
      annotation: alertThresholds ? {
        annotations: {
          upperAlert: alertThresholds.upper ? {
            type: 'line' as const,
            yMin: alertThresholds.upper,
            yMax: alertThresholds.upper,
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 2,
            borderDash: [6, 6],
            label: {
              display: true,
              content: '上限警報',
              position: 'end' as const,
              backgroundColor: 'rgba(255, 99, 132, 0.8)'
            }
          } : undefined,
          lowerAlert: alertThresholds.lower ? {
            type: 'line' as const,
            yMin: alertThresholds.lower,
            yMax: alertThresholds.lower,
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 2,
            borderDash: [6, 6],
            label: {
              display: true,
              content: '下限警報',
              position: 'end' as const,
              backgroundColor: 'rgba(255, 99, 132, 0.8)'
            }
          } : undefined
        }
      } : undefined
    },
    scales: {
      x: {
        type: 'category',
        grid: {
          display: true,
          color: currentTheme.gridColor,
          borderDash: [2, 2]
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          },
          maxTicksLimit: 20
        },
        border: {
          color: currentTheme.borderColor
        }
      },
      y: {
        type: 'linear',
        position: 'right',
        grid: {
          display: true,
          color: currentTheme.gridColor,
          borderDash: [2, 2]
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          },
          callback: (value) => {
            return new Intl.NumberFormat('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            }).format(value as number)
          }
        },
        border: {
          color: currentTheme.borderColor
        }
      }
    },
    elements: {
      point: {
        hoverRadius: 6
      }
    }
  }), [currentTheme, chartData, onDataPointClick, onLegendClick, enableZoom, enablePan, zoomMode, alertThresholds, combinedData.realtime, handleZoom])

  return (
    <div className={`w-full ${className}`}>
      {/* Stats Panel */}
      {showStats && stats && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">當前值</span>
              <p className="font-semibold text-lg">{stats.current}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">漲跌</span>
              <p className={`font-semibold text-lg ${parseFloat(stats.changePercent) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {stats.change} ({stats.changePercent}%)
              </p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">最高</span>
              <p className="font-semibold text-lg">{stats.high}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">最低</span>
              <p className="font-semibold text-lg">{stats.low}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">平均</span>
              <p className="font-semibold text-lg">{stats.avg}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">更新時間</span>
              <p className="font-semibold text-lg">
                {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '--'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Control Bar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isConnected ? '已連接' : '未連接'}
            </span>
          </div>

          <button
            onClick={handlePauseToggle}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            {isPaused || hookPaused ? '恢復' : '暫停'}
          </button>

          <button
            onClick={clear}
            className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            清除數據
          </button>
        </div>

        {visibleRange && (
          <div className="text-sm text-gray-500">
            範圍: {new Date(visibleRange.start).toLocaleTimeString()} - {new Date(visibleRange.end).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">錯誤: {error}</p>
        </div>
      )}

      {/* Chart */}
      <div style={{ height }}>
        <Line
          ref={chartRef}
          data={chartData}
          options={options}
        />
      </div>
    </div>
  )
}

export default RealTimeLineChart