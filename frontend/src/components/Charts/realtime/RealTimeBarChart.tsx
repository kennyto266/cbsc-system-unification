import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Chart as ChartType
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
import { RealTimeDataPoint, useRealTimeChart } from '../../hooks/useRealTimeChart'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../utils/chartThemes'
import { motion, AnimatePresence } from 'framer-motion'

// Register plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
)

// Extended props for RealTimeBarChart
export interface RealTimeBarChartProps extends Omit<BaseChartProps<'bar'>, 'type'> {
  // Real-time data props
  websocketUrl?: string
  channel?: string
  maxDataPoints?: number
  updateInterval?: number

  // Bar display props
  orientation?: 'vertical' | 'horizontal'
  dynamicSorting?: boolean
  sortBy?: 'value' | 'label' | 'change'
  sortOrder?: 'asc' | 'desc'

  // Data transformation props
  showChange?: boolean
  baselineValue?: number
  percentageMode?: boolean
  stackMode?: boolean

  // Animation props
  animationDuration?: number
  staggerAnimation?: boolean
  colorByValue?: boolean
  colorScale?: {
    positive: string
    negative: string
    neutral: string
  }

  // Interaction props
  enableZoom?: boolean
  enablePan?: boolean
  hoverEnabled?: boolean
  clickToDrillDown?: boolean

  // Display props
  showTopN?: number
  showValuesOnBars?: boolean
  barThickness?: number
  groupSpacing?: number

  // Callbacks
  onBarClick?: (data: any, index: number) => void
  onDataSorted?: (sortedData: any[]) => void
  onThresholdBreached?: (item: any, threshold: number) => void
}

const RealTimeBarChart: React.FC<RealTimeBarChartProps> = ({
  websocketUrl,
  channel = 'realtime-bars',
  maxDataPoints = 50,
  updateInterval = 1000,
  orientation = 'vertical',
  dynamicSorting = true,
  sortBy = 'value',
  sortOrder = 'desc',
  showChange = false,
  baselineValue = 0,
  percentageMode = false,
  stackMode = false,
  animationDuration = 500,
  staggerAnimation = true,
  colorByValue = true,
  colorScale = {
    positive: '#10b981',
    negative: '#ef4444',
    neutral: '#6b7280'
  },
  enableZoom = true,
  enablePan = true,
  hoverEnabled = true,
  clickToDrillDown = false,
  showTopN,
  showValuesOnBars = true,
  barThickness,
  groupSpacing = 0.2,
  onBarClick,
  onDataSorted,
  onThresholdBreached,
  className = '',
  theme = 'light',
  height = 400,
  onDataPointClick,
  ...rest
}) => {
  const chartRef = useRef<ChartType<'bar'>>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [selectedBar, setSelectedBar] = useState<number | null>(null)
  const [previousData, setPreviousData] = useState<Record<string, number>>({})
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

  // Process and sort data
  const processedData = useMemo(() => {
    const dataMap = new Map<string, any>()

    // Aggregate data by label
    realtimeData.forEach(point => {
      const key = point.label || 'Unknown'
      const existing = dataMap.get(key) || { label: key, value: 0, count: 0 }

      dataMap.set(key, {
        ...existing,
        value: existing.value + (point.value || 0),
        count: existing.count + 1,
        metadata: point.metadata || {}
      })
    })

    // Convert to array and calculate averages
    let data = Array.from(dataMap.values()).map(item => ({
      ...item,
      value: item.value / item.count,
      change: showChange && previousData[item.label]
        ? item.value - previousData[item.label]
        : 0,
      changePercent: showChange && previousData[item.label]
        ? ((item.value - previousData[item.label]) / previousData[item.label] * 100)
        : 0
    }))

    // Store current values for next change calculation
    const newPreviousData: Record<string, number> = {}
    data.forEach(item => {
      newPreviousData[item.label] = item.value
    })
    setPreviousData(newPreviousData)

    // Sort data if enabled
    if (dynamicSorting) {
      data.sort((a, b) => {
        let aValue: number, bValue: number

        switch (sortBy) {
          case 'change':
            aValue = Math.abs(a.change)
            bValue = Math.abs(b.change)
            break
          case 'label':
            aValue = a.label.localeCompare(b.label)
            bValue = 0
            break
          default:
            aValue = a.value
            bValue = b.value
        }

        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue
      })
    }

    // Limit to top N if specified
    if (showTopN && showTopN > 0) {
      data = data.slice(0, showTopN)
    }

    return data
  }, [realtimeData, dynamicSorting, sortBy, sortOrder, showChange, showTopN, previousData])

  // Notify about sorted data
  useEffect(() => {
    if (onDataSorted) {
      onDataSorted(processedData)
    }
  }, [processedData, onDataSorted])

  // Process data for Chart.js
  const chartData = useMemo<ChartData<'bar'>>(() => {
    const labels = processedData.map(d => d.label)
    const values = processedData.map(d => d.value)

    // Create datasets
    const datasets = []

    if (stackMode) {
      // Stack mode - split into positive and negative
      const positiveValues = values.map(v => Math.max(0, v))
      const negativeValues = values.map(v => Math.min(0, v))

      datasets.push({
        label: '正值',
        data: positiveValues,
        backgroundColor: colorScale.positive + '80',
        borderColor: colorScale.positive,
        borderWidth: 1,
        stack: 'stack0'
      })

      datasets.push({
        label: '負值',
        data: negativeValues.map(v => Math.abs(v)),
        backgroundColor: colorScale.negative + '80',
        borderColor: colorScale.negative,
        borderWidth: 1,
        stack: 'stack0'
      })
    } else {
      // Normal mode
      const backgroundColors = values.map((value, index) => {
        if (colorByValue) {
          const change = processedData[index].change
          if (change > 0) return colorScale.positive + '80'
          if (change < 0) return colorScale.negative + '80'
          return colorScale.neutral + '80'
        }
        return currentTheme.colors[index % currentTheme.colors.length] + '80'
      })

      const borderColors = values.map((value, index) => {
        if (colorByValue) {
          const change = processedData[index].change
          if (change > 0) return colorScale.positive
          if (change < 0) return colorScale.negative
          return colorScale.neutral
        }
        return currentTheme.colors[index % currentTheme.colors.length]
      })

      datasets.push({
        label: percentageMode ? '百分比 (%)' : '數值',
        data: values,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1
      })

      // Add change indicators if enabled
      if (showChange) {
        datasets.push({
          label: '變化',
          data: processedData.map(d => d.change),
          backgroundColor: 'transparent',
          borderColor: '#fbbf24',
          borderWidth: 2,
          type: 'line' as any,
          yAxisID: 'y1',
          order: 1
        })
      }
    }

    return { labels, datasets }
  }, [processedData, stackMode, colorByValue, showChange, percentageMode, currentTheme.colors, colorScale])

  // Animation variants
  const barVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  }

  // Handle bar click
  const handleBarClick = useCallback((event: any, elements: any[]) => {
    if (elements.length > 0) {
      const { index } = elements[0]
      setSelectedBar(index)

      if (onBarClick) {
        onBarClick(processedData[index], index)
      }

      if (onDataPointClick) {
        onDataPointClick(processedData[index], elements[0])
      }
    }
  }, [processedData, onBarClick, onDataPointClick])

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

  // Chart options
  const options: ChartOptions<'bar'> = useMemo(() => ({
    ...getChartJsDefaults(currentTheme),
    animation: {
      duration: animationDuration,
      stagger: staggerAnimation ? 50 : 0,
      onComplete: () => {
        if (chartRef.current) {
          // Check for threshold breaches
          processedData.forEach((item, index) => {
            if (onThresholdBreached && item.value > (baselineValue * 1.5)) {
              onThresholdBreached(item, baselineValue * 1.5)
            }
          })
        }
      }
    },
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: handleBarClick,
    plugins: {
      ...getChartJsDefaults(currentTheme).plugins,
      legend: {
        display: stackMode || showChange
      },
      tooltip: {
        ...getChartJsDefaults(currentTheme).plugins.tooltip,
        callbacks: {
          label: (context) => {
            const datasetLabel = context.dataset.label || ''
            const value = context.parsed.y

            if (percentageMode) {
              return `${datasetLabel}: ${value.toFixed(2)}%`
            }

            const item = processedData[context.dataIndex]
            if (showChange && datasetLabel !== '變化') {
              return [
                `${datasetLabel}: ${value.toFixed(4)}`,
                `變化: ${item.change.toFixed(4)} (${item.changePercent.toFixed(2)}%)`
              ]
            }

            return `${datasetLabel}: ${value.toFixed(4)}`
          }
        }
      },
      zoom: enableZoom ? {
        zoom: {
          wheel: {
            enabled: true
          },
          pinch: {
            enabled: true
          },
          mode: orientation === 'horizontal' ? 'y' : 'x'
        },
        pan: {
          enabled: enablePan,
          mode: orientation === 'horizontal' ? 'y' : 'x'
        }
      } : undefined,
      datalabels: showValuesOnBars ? {
        display: true,
        color: currentTheme.textColor,
        anchor: 'end',
        align: 'top',
        formatter: (value: number) => {
          return percentageMode ? `${value.toFixed(1)}%` : value.toFixed(2)
        }
      } : false
    },
    scales: {
      x: {
        type: 'category',
        grid: {
          display: false
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize - 2,
            family: currentTheme.fontFamily
          },
          maxRotation: orientation === 'horizontal' ? 0 : 45,
          minRotation: 0
        }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: {
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
            if (percentageMode) {
              return `${value}%`
            }
            return new Intl.NumberFormat('en-US', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 2
            }).format(value as number)
          }
        },
        border: {
          color: currentTheme.borderColor
        }
      },
      ...(showChange && {
        y1: {
          type: 'linear',
          position: 'right',
          grid: {
            display: false
          },
          ticks: {
            callback: (value) => `Δ${value}`
          }
        }
      })
    },
    layout: {
      padding: {
        top: showValuesOnBars ? 20 : 0
      }
    },
    elements: {
      bar: {
        borderWidth: 1,
        borderRadius: 4,
        hoverBackgroundColor: (context) => {
          const value = context.parsed.y
          return value > 0 ? colorScale.positive + 'cc' : colorScale.negative + 'cc'
        }
      }
    }
  }), [currentTheme, animationDuration, staggerAnimation, handleBarClick, enableZoom, enablePan, orientation, showValuesOnBars, percentageMode, showChange, processedData, onThresholdBreached, baselineValue, colorScale])

  return (
    <div className={`w-full ${className}`}>
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

        <div className="text-sm text-gray-500">
          更新時間: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '--'}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">錯誤: {error}</p>
        </div>
      )}

      {/* Chart */}
      <div style={{ height }} className="relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={`${processedData.length}-${isPaused}`}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={barVariants}
            transition={{ duration: 0.3 }}
          >
            <Bar
              ref={chartRef}
              data={chartData}
              options={options}
            />
          </motion.div>
        </AnimatePresence>

        {/* Selected Bar Details */}
        <AnimatePresence>
          {selectedBar !== null && processedData[selectedBar] && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-4 right-4 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10"
            >
              <button
                onClick={() => setSelectedBar(null)}
                className="absolute top-1 right-1 text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
              <h4 className="font-semibold text-sm mb-2">{processedData[selectedBar].label}</h4>
              <div className="text-xs space-y-1">
                <p>數值: {processedData[selectedBar].value.toFixed(4)}</p>
                {showChange && (
                  <>
                    <p>變化: {processedData[selectedBar].change.toFixed(4)}</p>
                    <p>變化%: {processedData[selectedBar].changePercent.toFixed(2)}%</p>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Summary Stats */}
      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">總計</span>
            <p className="font-semibold">
              {processedData.reduce((sum, item) => sum + item.value, 0).toFixed(4)}
            </p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">平均值</span>
            <p className="font-semibold">
              {processedData.length > 0
                ? (processedData.reduce((sum, item) => sum + item.value, 0) / processedData.length).toFixed(4)
                : '0'}
            </p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">最大值</span>
            <p className="font-semibold text-green-600">
              {processedData.length > 0
                ? Math.max(...processedData.map(d => d.value)).toFixed(4)
                : '0'}
            </p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">最小值</span>
            <p className="font-semibold text-red-600">
              {processedData.length > 0
                ? Math.min(...processedData.map(d => d.value)).toFixed(4)
                : '0'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealTimeBarChart