import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  Chart as ChartType
} from 'chart.js'
import { Radar } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import { RealTimeDataPoint, useRealTimeChart } from '../../hooks/useRealTimeChart'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../utils/chartThemes'
import { motion } from 'framer-motion'

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Extended props for RealTimeRadarChart
export interface RealTimeRadarChartProps extends Omit<BaseChartProps<'radar'>, 'type'> {
  // Real-time data props
  websocketUrl?: string
  channel?: string
  maxDataPoints?: number
  updateInterval?: number

  // Radar-specific props
  dimensions: Array<{
    key: string
    label: string
    min?: number
    max?: number
    unit?: string
  }>

  // Data aggregation props
  aggregationMethod?: 'average' | 'latest' | 'max' | 'min'
  smoothingEnabled?: boolean
  smoothingWindow?: number

  // Visual props
  fillArea?: boolean
  pointRadius?: number
  lineWidth?: number
  showGrid?: boolean
  gridLevels?: number

  // Comparison props
  showBenchmark?: boolean
  benchmarkData?: Record<string, number>
  benchmarkLabel?: string

  // Animation props
  animationDuration?: number
  pulseAnimation?: boolean
  transitionDuration?: number

  // Alert props
  showAlerts?: boolean
  alertThresholds?: Record<string, { min?: number; max?: number }>
  onDimensionAlert?: (dimension: string, value: number, threshold: number) => void

  // Interaction props
  enableHover?: boolean
  dimensionClickEnabled?: boolean
  onDimensionClick?: (dimension: string, value: number) => void

  // Display props
  showValues?: boolean
  showPercentage?: boolean
  normalizeValues?: boolean

  // Callbacks
  onScoreUpdate?: (scores: Record<string, number>) => void
  onOverallScoreChange?: (score: number) => void
}

const RealTimeRadarChart: React.FC<RealTimeRadarChartProps> = ({
  websocketUrl,
  channel = 'realtime-radar',
  maxDataPoints = 100,
  updateInterval = 2000,
  dimensions,
  aggregationMethod = 'latest',
  smoothingEnabled = false,
  smoothingWindow = 5,
  fillArea = true,
  pointRadius = 4,
  lineWidth = 2,
  showGrid = true,
  gridLevels = 5,
  showBenchmark = false,
  benchmarkData = {},
  benchmarkLabel = '基準',
  animationDuration = 750,
  pulseAnimation = true,
  transitionDuration = 300,
  showAlerts = false,
  alertThresholds,
  onDimensionAlert,
  enableHover = true,
  dimensionClickEnabled = false,
  onDimensionClick,
  showValues = true,
  showPercentage = false,
  normalizeValues = true,
  onScoreUpdate,
  onOverallScoreChange,
  className = '',
  theme = 'light',
  height = 400,
  onDataPointClick,
  ...rest
}) => {
  const chartRef = useRef<ChartType<'radar'>>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [dimensionScores, setDimensionScores] = useState<Record<string, number>>({})
  const [overallScore, setOverallScore] = useState<number>(0)
  const [alertedDimensions, setAlertedDimensions] = useState<Set<string>>(new Set())
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

  // Process and aggregate data
  const processedData = useMemo(() => {
    const scores: Record<string, number[]> = {}

    // Initialize scores array for each dimension
    dimensions.forEach(dim => {
      scores[dim.key] = []
    })

    // Aggregate data by dimension
    realtimeData.forEach(point => {
      if (point.metadata && typeof point.metadata === 'object') {
        Object.entries(point.metadata).forEach(([key, value]) => {
          const dimension = dimensions.find(d => d.key === key)
          if (dimension && typeof value === 'number') {
            scores[key].push(value)
          }
        })
      }
    })

    // Apply aggregation method
    const aggregatedScores: Record<string, number> = {}
    dimensions.forEach(dim => {
      const values = scores[dim.key]

      if (values.length === 0) {
        aggregatedScores[dim.key] = 0
      } else {
        switch (aggregationMethod) {
          case 'average':
            aggregatedScores[dim.key] = values.reduce((a, b) => a + b, 0) / values.length
            break
          case 'max':
            aggregatedScores[dim.key] = Math.max(...values)
            break
          case 'min':
            aggregatedScores[dim.key] = Math.min(...values)
            break
          case 'latest':
          default:
            aggregatedScores[dim.key] = values[values.length - 1]
            break
        }
      }
    })

    // Apply smoothing if enabled
    if (smoothingEnabled && smoothingWindow > 1) {
      dimensions.forEach(dim => {
        const values = scores[dim.key]
        if (values.length >= smoothingWindow) {
          const recent = values.slice(-smoothingWindow)
          aggregatedScores[dim.key] = recent.reduce((a, b) => a + b, 0) / recent.length
        }
      })
    }

    return aggregatedScores
  }, [realtimeData, dimensions, aggregationMethod, smoothingEnabled, smoothingWindow])

  // Normalize values if required
  const normalizedData = useMemo(() => {
    if (!normalizeValues) return processedData

    const normalized: Record<string, number> = {}
    dimensions.forEach(dim => {
      const value = processedData[dim.key] || 0
      const min = dim.min || 0
      const max = dim.max || 100

      // Normalize to 0-100 scale
      normalized[dim.key] = ((value - min) / (max - min)) * 100
    })

    return normalized
  }, [processedData, dimensions, normalizeValues])

  // Calculate overall score
  useEffect(() => {
    const scores = Object.values(normalizedData)
    const newOverallScore = scores.length > 0
      ? scores.reduce((sum, score) => sum + score, 0) / scores.length
      : 0

    setOverallScore(newOverallScore)
    setDimensionScores(normalizedData)

    onScoreUpdate?.(normalizedData)
    onOverallScoreChange?.(newOverallScore)

    // Check for alerts
    if (showAlerts && alertThresholds) {
      dimensions.forEach(dim => {
        const value = normalizeValues ? normalizedData[dim.key] : processedData[dim.key]
        const threshold = alertThresholds[dim.key]

        if (threshold && value !== undefined) {
          if ((threshold.min !== undefined && value < threshold.min) ||
              (threshold.max !== undefined && value > threshold.max)) {
            const alertKey = `${dim.key}-${value}`
            if (!alertedDimensions.has(alertKey)) {
              setAlertedDimensions(prev => new Set(prev).add(alertKey))
              onDimensionAlert?.(dim.key, value, threshold.min || threshold.max || 0)
            }
          }
        }
      })
    }
  }, [normalizedData, processedData, dimensions, normalizeValues, showAlerts, alertThresholds, onScoreUpdate, onOverallScoreChange, onDimensionAlert, alertedDimensions])

  // Prepare chart data
  const chartData = useMemo<ChartData<'radar'>>(() => {
    const labels = dimensions.map(d => d.label)

    // Main dataset
    const datasets = [
      {
        label: '當前評分',
        data: dimensions.map(d => normalizeValues ? normalizedData[d.key] : processedData[d.key] || 0),
        borderColor: currentTheme.colors[0],
        backgroundColor: fillArea ? currentTheme.colors[0] + '30' : 'transparent',
        borderWidth: lineWidth,
        pointRadius,
        pointHoverRadius: pointRadius + 2,
        pointBackgroundColor: currentTheme.colors[0],
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        tension: 0.1
      }
    ]

    // Benchmark dataset
    if (showBenchmark && Object.keys(benchmarkData).length > 0) {
      datasets.push({
        label: benchmarkLabel,
        data: dimensions.map(d => benchmarkData[d.key] || 0),
        borderColor: currentTheme.colors[1],
        backgroundColor: 'transparent',
        borderWidth: lineWidth,
        pointRadius: pointRadius - 1,
        pointHoverRadius: pointRadius + 1,
        pointBackgroundColor: currentTheme.colors[1],
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        borderDash: [5, 5],
        tension: 0.1
      })
    }

    return { labels, datasets }
  }, [dimensions, normalizedData, processedData, normalizeValues, showBenchmark, benchmarkData, benchmarkLabel, currentTheme.colors, fillArea, pointRadius, lineWidth])

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

  // Handle dimension click
  const handleChartClick = useCallback((event: any, elements: any[]) => {
    if (elements.length > 0) {
      const { index } = elements[0]
      const dimension = dimensions[index]
      const value = normalizeValues ? normalizedData[dimension.key] : processedData[dimension.key]

      if (dimensionClickEnabled && onDimensionClick) {
        onDimensionClick(dimension.key, value)
      }

      if (onDataPointClick) {
        onDataPointClick({ dimension, value }, elements[0])
      }
    }
  }, [dimensions, dimensionClickEnabled, onDimensionClick, onDataPointClick, normalizeValues, normalizedData, processedData])

  // Chart options
  const options: ChartOptions<'radar'> = useMemo(() => ({
    ...getChartJsDefaults(currentTheme),
    animation: {
      duration: animationDuration,
      easing: pulseAnimation ? 'easeInOutElastic' : 'easeInOutQuart',
      onComplete: () => {
        if (pulseAnimation && chartRef.current) {
          // Add pulse animation to points
          const meta = chartRef.current.getDatasetMeta(0)
          meta.data.forEach((point: any) => {
            if (point.active) {
              point.options.radius = pointRadius + 2
              setTimeout(() => {
                point.options.radius = pointRadius
                chartRef.current?.update('none')
              }, 500)
            }
          })
        }
      }
    },
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: enableHover
    },
    onClick: handleChartClick,
    plugins: {
      ...getChartJsDefaults(currentTheme).plugins,
      legend: {
        display: showBenchmark
      },
      tooltip: {
        ...getChartJsDefaults(currentTheme).plugins.tooltip,
        callbacks: {
          title: (context) => {
            return context[0].label
          },
          label: (context) => {
            const dimension = dimensions[context.dataIndex]
            const value = context.parsed.r
            const unit = dimension.unit || ''
            const displayValue = showPercentage
              ? `${value.toFixed(1)}%`
              : `${value.toFixed(2)} ${unit}`

            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            label += displayValue

            // Add benchmark comparison if available
            if (showBenchmark && context.datasetIndex === 0) {
              const benchmarkValue = benchmarkData[dimension.key] || 0
              const diff = value - benchmarkValue
              const diffPercent = benchmarkValue > 0 ? (diff / benchmarkValue * 100) : 0
              label += `\nvs 基準: ${diff > 0 ? '+' : ''}${diff.toFixed(2)} (${diffPercent > 0 ? '+' : ''}${diffPercent.toFixed(1)}%)`
            }

            return label
          }
        }
      }
    },
    scales: {
      r: {
        type: 'radial-linear',
        angleLines: {
          display: showGrid,
          color: currentTheme.gridColor
        },
        grid: {
          display: showGrid,
          color: currentTheme.gridColor,
          circular: true
        },
        pointLabels: {
          display: true,
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily,
            weight: 'bold'
          },
          padding: 15
        },
        ticks: {
          display: showValues,
          color: currentTheme.textColor,
          backdropColor: 'transparent',
          font: {
            size: currentTheme.fontSize - 2
          },
          callback: (value) => {
            return showPercentage ? `${value}%` : value.toFixed(0)
          }
        },
        min: 0,
        max: normalizeValues ? 100 : undefined,
        suggestedMin: 0,
        suggestedMax: normalizeValues ? 100 : undefined
      }
    },
    elements: {
      line: {
        tension: 0.1
      }
    }
  }), [currentTheme, animationDuration, pulseAnimation, handleChartClick, enableHover, showGrid, showValues, showPercentage, normalizeValues, showBenchmark, dimensions, benchmarkData, pointRadius])

  return (
    <div className={`w-full ${className}`}>
      {/* Header with Overall Score */}
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

        {/* Overall Score Display */}
        <motion.div
          key={overallScore}
          initial={{ scale: 1.2, opacity: 0.8 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="text-right"
        >
          <div className="text-sm text-gray-500 dark:text-gray-400">綜合評分</div>
          <div className="text-2xl font-bold" style={{
            color: overallScore >= 80 ? '#10b981' : overallScore >= 60 ? '#f59e0b' : '#ef4444'
          }}>
            {overallScore.toFixed(1)}
            {showPercentage && '%'}
          </div>
        </motion.div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">錯誤: {error}</p>
        </div>
      )}

      {/* Chart */}
      <div style={{ height }} className="relative">
        <Radar
          ref={chartRef}
          data={chartData}
          options={options}
        />
      </div>

      {/* Dimension Scores Table */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3">維度詳情</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {dimensions.map((dim, index) => {
            const value = normalizeValues ? normalizedData[dim.key] : processedData[dim.key] || 0
            const benchmark = benchmarkData[dim.key]
            const isAlerted = showAlerts && alertThresholds?.[dim.key] && (
              (alertThresholds[dim.key].min && value < alertThresholds[dim.key].min!) ||
              (alertThresholds[dim.key].max && value > alertThresholds[dim.key].max!)
            )

            return (
              <motion.div
                key={dim.key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                  isAlerted
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                    : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                } ${dimensionClickEnabled ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : ''}`}
                onClick={() => dimensionClickEnabled && onDimensionClick?.(dim.key, value)}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{dim.label}</span>
                  {isAlerted && (
                    <span className="text-red-500 text-xs">⚠</span>
                  )}
                </div>
                <div className="text-lg font-bold" style={{
                  color: currentTheme.colors[index % currentTheme.colors.length]
                }}>
                  {showPercentage ? `${value.toFixed(1)}%` : value.toFixed(2)}
                  <span className="text-xs text-gray-500 ml-1">{dim.unit || ''}</span>
                </div>
                {showBenchmark && benchmark !== undefined && (
                  <div className="text-xs text-gray-500">
                    基準: {showPercentage ? `${benchmark.toFixed(1)}%` : benchmark.toFixed(2)}
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Last Update Time */}
      <div className="mt-4 text-center text-sm text-gray-500">
        最後更新: {lastUpdate ? new Date(lastUpdate).toLocaleString() : '--'}
      </div>
    </div>
  )
}

export default RealTimeRadarChart