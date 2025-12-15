import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Chart as ChartType
} from 'chart.js'
import { Scatter } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import chartjsPluginMatrix from 'chartjs-chart-matrix'
import zoomPlugin from 'chartjs-plugin-zoom'
import { RealTimeDataPoint, useRealTimeChart } from '../../hooks/useRealTimeChart'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../utils/chartThemes'
import { motion } from 'framer-motion'

// Register plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin,
  chartjsPluginMatrix
)

// Matrix data point
interface MatrixDataPoint {
  x: string
  y: string
  v: number
  metadata?: Record<string, any>
}

// Extended props for RealTimeHeatmap
export interface RealTimeHeatmapProps extends Omit<BaseChartProps<'scatter'>, 'type'> {
  // Real-time data props
  websocketUrl?: string
  channel?: string
  maxDataPoints?: number
  updateInterval?: number

  // Matrix configuration
  xLabels: string[]
  yLabels: string[]
  dataKey?: string

  // Color scale props
  colorScale?: {
    min: string
    mid: string
    max: string
  }
  valueRange?: {
    min: number
    max: number
  }
  diverging?: boolean
  centerValue?: number

  // Display props
  showLegend?: boolean
  showValues?: boolean
  valueFormat?: (value: number) => string
  cellSize?: number
  cellPadding?: number

  // Interaction props
  enableZoom?: boolean
  enablePan?: boolean
  hoverEnabled?: boolean
  clickToDrillDown?: boolean
  onCellClick?: (x: string, y: string, value: number) => void

  // Animation props
  animationDuration?: number
  staggerAnimation?: boolean

  // Rolling window props
  rollingWindow?: boolean
  windowSize?: number
  windowStep?: number

  // Aggregation props
  aggregationMethod?: 'average' | 'latest' | 'sum' | 'count'

  // Alert props
  showAlerts?: boolean
  alertThreshold?: {
    min?: number
    max?: number
  }
  onCellAlert?: (x: string, y: string, value: number) => void

  // Callbacks
  onDataUpdate?: (matrix: MatrixDataPoint[][]) => void
  onCorrelationChange?: (correlations: Record<string, number>) => void
}

const RealTimeHeatmap: React.FC<RealTimeHeatmapProps> = ({
  websocketUrl,
  channel = 'realtime-heatmap',
  maxDataPoints = 1000,
  updateInterval = 2000,
  xLabels,
  yLabels,
  dataKey = 'correlation',
  colorScale = {
    min: '#3b82f6',
    mid: '#ffffff',
    max: '#ef4444'
  },
  valueRange,
  diverging = false,
  centerValue = 0,
  showLegend = true,
  showValues = false,
  valueFormat = (v) => v.toFixed(3),
  cellSize = 40,
  cellPadding = 2,
  enableZoom = true,
  enablePan = true,
  hoverEnabled = true,
  clickToDrillDown = false,
  onCellClick,
  animationDuration = 500,
  staggerAnimation = true,
  rollingWindow = false,
  windowSize = 50,
  windowStep = 10,
  aggregationMethod = 'average',
  showAlerts = false,
  alertThreshold,
  onCellAlert,
  onDataUpdate,
  onCorrelationChange,
  className = '',
  theme = 'light',
  height = 400,
  onDataPointClick,
  ...rest
}) => {
  const chartRef = useRef<ChartType<'matrix'>>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [selectedCell, setSelectedCell] = useState<{ x: string; y: string; value: number } | null>(null)
  const [correlationMatrix, setCorrelationMatrix] = useState<number[][]>([])
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

  // Build correlation matrix from data
  const buildCorrelationMatrix = useCallback((data: RealTimeDataPoint[]) => {
    const matrix: number[][] = []
    const matrixData: MatrixDataPoint[][] = []

    // Initialize matrix
    for (let i = 0; i < yLabels.length; i++) {
      matrix[i] = []
      matrixData[i] = []
      for (let j = 0; j < xLabels.length; j++) {
        matrix[i][j] = 0
        matrixData[i][j] = {
          x: xLabels[j],
          y: yLabels[i],
          v: 0
        }
      }
    }

    // Process data points
    const dataMap = new Map<string, number[]>()

    data.forEach(point => {
      if (point.metadata && point.metadata[dataKey]) {
        const key = `${point.metadata.x || ''}-${point.metadata.y || ''}`
        if (!dataMap.has(key)) {
          dataMap.set(key, [])
        }
        dataMap.get(key)!.push(point.metadata[dataKey])
      }
    })

    // Apply rolling window if enabled
    if (rollingWindow && data.length > windowSize) {
      const windowedData = data.slice(-windowSize)
      // Rebuild dataMap with windowed data
      dataMap.clear()
      windowedData.forEach(point => {
        if (point.metadata && point.metadata[dataKey]) {
          const key = `${point.metadata.x || ''}-${point.metadata.y || ''}`
          if (!dataMap.has(key)) {
            dataMap.set(key, [])
          }
          dataMap.get(key)!.push(point.metadata[dataKey])
        }
      })
    }

    // Fill matrix with aggregated values
    dataMap.forEach((values, key) => {
      const [xKey, yKey] = key.split('-')
      const xIndex = xLabels.indexOf(xKey)
      const yIndex = yLabels.indexOf(yKey)

      if (xIndex !== -1 && yIndex !== -1) {
        let value: number

        switch (aggregationMethod) {
          case 'average':
            value = values.reduce((a, b) => a + b, 0) / values.length
            break
          case 'sum':
            value = values.reduce((a, b) => a + b, 0)
            break
          case 'count':
            value = values.length
            break
          case 'latest':
          default:
            value = values[values.length - 1]
            break
        }

        matrix[yIndex][xIndex] = value
        matrixData[yIndex][xIndex] = {
          x: xLabels[xIndex],
          y: yLabels[yIndex],
          v: value
        }

        // Check for alerts
        if (showAlerts && alertThreshold) {
          if ((alertThreshold.min && value < alertThreshold.min) ||
              (alertThreshold.max && value > alertThreshold.max)) {
            onCellAlert?.(xLabels[xIndex], yLabels[yIndex], value)
          }
        }
      }
    })

    // Auto-correlation (diagonal)
    for (let i = 0; i < Math.min(xLabels.length, yLabels.length); i++) {
      if (matrix[i][i] === 0) {
        matrix[i][i] = 1
        matrixData[i][i].v = 1
      }
    }

    setCorrelationMatrix(matrix)
    onDataUpdate?.(matrixData)

    // Calculate average correlations
    if (onCorrelationChange) {
      const correlations: Record<string, number> = {}
      xLabels.forEach((x, i) => {
        if (i < yLabels.length && x === yLabels[i]) {
          let sum = 0
          let count = 0
          for (let j = 0; j < xLabels.length; j++) {
            if (i !== j && matrix[i][j] !== 0) {
              sum += Math.abs(matrix[i][j])
              count++
            }
          }
          correlations[x] = count > 0 ? sum / count : 0
        }
      })
      onCorrelationChange(correlations)
    }

    return matrixData
  }, [xLabels, yLabels, dataKey, rollingWindow, windowSize, aggregationMethod, showAlerts, alertThreshold, onCellAlert, onDataUpdate, onCorrelationChange])

  // Process data for visualization
  const { matrixData, flatData, minValue, maxValue } = useMemo(() => {
    const matrixData = buildCorrelationMatrix(realtimeData)
    const flatData: any[] = []
    let min = Infinity
    let max = -Infinity

    for (let y = 0; y < yLabels.length; y++) {
      for (let x = 0; x < xLabels.length; x++) {
        const value = matrixData[y][x].v
        if (value !== 0) {
          min = Math.min(min, value)
          max = Math.max(max, value)
        }

        flatData.push({
          x: x,
          y: y,
          v: value,
          label: `${matrixData[y][x].x} vs ${matrixData[y][x].y}`,
          xLabel: matrixData[y][x].x,
          yLabel: matrixData[y][x].y
        })
      }
    }

    // Apply custom value range if provided
    const finalMin = valueRange?.min ?? min
    const finalMax = valueRange?.max ?? max

    return { matrixData, flatData, minValue: finalMin, maxValue: finalMax }
  }, [realtimeData, buildCorrelationMatrix, xLabels, yLabels, valueRange])

  // Generate color based on value
  const getColor = useCallback((value: number) => {
    if (diverging) {
      const normalized = (value - centerValue) / Math.max(Math.abs(maxValue - centerValue), Math.abs(minValue - centerValue))
      const clamped = Math.max(-1, Math.min(1, normalized))

      if (clamped < 0) {
        return interpolateColor(colorScale.min, colorScale.mid, Math.abs(clamped))
      } else {
        return interpolateColor(colorScale.mid, colorScale.max, clamped)
      }
    } else {
      const normalized = (value - minValue) / (maxValue - minValue)
      const clamped = Math.max(0, Math.min(1, normalized))
      return interpolateColor(colorScale.min, colorScale.max, clamped)
    }
  }, [colorScale, diverging, centerValue, minValue, maxValue])

  // Color interpolation
  const interpolateColor = (color1: string, color2: string, factor: number): string => {
    const c1 = hexToRgb(color1)
    const c2 = hexToRgb(color2)

    if (!c1 || !c2) return color1

    const r = Math.round(c1.r + (c2.r - c1.r) * factor)
    const g = Math.round(c1.g + (c2.g - c1.g) * factor)
    const b = Math.round(c1.b + (c2.b - c1.b) * factor)

    return `rgb(${r}, ${g}, ${b})`
  }

  // Hex to RGB conversion
  const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null
  }

  // Prepare chart data
  const chartData = useMemo<ChartData<'matrix'>>(() => ({
    datasets: [{
      label: '相關性',
      data: flatData,
      backgroundColor: (context: any) => {
        const value = context.dataset.data[context.dataIndex]?.v || 0
        return getColor(value)
      },
      borderColor: currentTheme.borderColor,
      borderWidth: 1,
      width: (ctx: any) => (cellSize - cellPadding * 2) * (ctx.chart.chartArea?.width / xLabels.length),
      height: (ctx: any) => (cellSize - cellPadding * 2) * (ctx.chart.chartArea?.height / yLabels.length)
    }]
  }), [flatData, getColor, currentTheme.borderColor, cellSize, cellPadding, xLabels.length, yLabels.length])

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

  // Handle cell click
  const handleCellClick = useCallback((event: any, elements: any[]) => {
    if (elements.length > 0) {
      const element = elements[0]
      const dataPoint = flatData[element.index]

      if (onCellClick) {
        onCellClick(dataPoint.xLabel, dataPoint.yLabel, dataPoint.v)
      }

      if (clickToDrillDown) {
        setSelectedCell({
          x: dataPoint.xLabel,
          y: dataPoint.yLabel,
          value: dataPoint.v
        })
      }

      if (onDataPointClick) {
        onDataPointClick(dataPoint, element)
      }
    }
  }, [flatData, onCellClick, clickToDrillDown, onDataPointClick])

  // Chart options
  const options: ChartOptions<'matrix'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: animationDuration,
      easing: 'easeInOutQuart',
      stagger: staggerAnimation ? 10 : 0
    },
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: handleCellClick,
    plugins: {
      legend: {
        display: showLegend,
        position: 'bottom',
        labels: {
          generateLabels: () => {
            const labels = []
            const steps = 5
            for (let i = 0; i <= steps; i++) {
              const value = minValue + (maxValue - minValue) * (i / steps)
              labels.push({
                text: valueFormat(value),
                fillStyle: getColor(value),
                strokeStyle: getColor(value),
                lineWidth: 0,
                hidden: false,
                index: i
              })
            }
            return labels
          }
        }
      },
      tooltip: {
        enabled: hoverEnabled,
        callbacks: {
          title: (context) => {
            const dataPoint = flatData[context[0].dataIndex]
            return `${dataPoint.yLabel} vs ${dataPoint.xLabel}`
          },
          label: (context) => {
            const value = context.dataset.data[context.dataIndex]?.v || 0
            return `相關性: ${valueFormat(value)}`
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
          mode: 'xy'
        },
        pan: {
          enabled: enablePan,
          mode: 'xy'
        }
      } : undefined
    },
    scales: {
      x: {
        type: 'category',
        labels: xLabels,
        offset: true,
        grid: {
          display: false
        },
        ticks: {
          display: true,
          font: {
            size: currentTheme.fontSize - 2
          }
        }
      },
      y: {
        type: 'category',
        labels: yLabels,
        offset: true,
        grid: {
          display: false
        },
        ticks: {
          display: true,
          font: {
            size: currentTheme.fontSize - 2
          }
        }
      }
    }
  }), [currentTheme, animationDuration, staggerAnimation, handleCellClick, showLegend, flatData, valueFormat, getColor, minValue, maxValue, hoverEnabled, enableZoom, enablePan, xLabels, yLabels])

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
        <Scatter
          ref={chartRef}
          data={chartData as any}
          options={options}
        />

        {/* Selected Cell Details */}
        <AnimatePresence>
          {selectedCell && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="absolute top-4 right-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10"
            >
              <button
                onClick={() => setSelectedCell(null)}
                className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
              <h4 className="font-semibold mb-2">單元格詳情</h4>
              <div className="text-sm space-y-1">
                <p>X: {selectedCell.x}</p>
                <p>Y: {selectedCell.y}</p>
                <p>值: {valueFormat(selectedCell.value)}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Statistics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400">最小值</div>
          <div className="text-lg font-semibold">{valueFormat(minValue)}</div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400">最大值</div>
          <div className="text-lg font-semibold">{valueFormat(maxValue)}</div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400">平均值</div>
          <div className="text-lg font-semibold">
            {valueFormat(flatData.reduce((sum, d) => sum + d.v, 0) / flatData.length)}
          </div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-500 dark:text-gray-400">數據點</div>
          <div className="text-lg font-semibold">{flatData.filter(d => d.v !== 0).length}</div>
        </div>
      </div>
    </div>
  )
}

export default RealTimeHeatmap