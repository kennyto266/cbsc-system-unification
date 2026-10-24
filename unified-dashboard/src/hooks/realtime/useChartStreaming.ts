import { useEffect, useRef, useState, useCallback } from 'react'
import { Chart, ChartConfiguration, ChartType } from 'chart.js'
import { ChartStreamingManager } from '../../utils/realtime/chartStreaming'
import { RealTimeDataBuffer } from '../../utils/realtime/dataBuffer'
import { ChartDataPoint } from '../../components/charts/RealTime/RealTimeChartProvider'

// Chart streaming hook options
export interface UseChartStreamingOptions {
  chart: Chart
  maxDataPoints?: number
  updateInterval?: number
  enableAnimation?: boolean
  enableCompression?: boolean
  enableThrottling?: boolean
  bufferSize?: number
  autoStart?: boolean
  onDataUpdate?: (data: ChartDataPoint[]) => void
  onBufferOverflow?: (overflowCount: number) => void
  onPerformanceWarning?: (metrics: any) => void
}

// Chart streaming hook return value
export interface UseChartStreamingReturn {
  // Control
  start: () => void
  stop: () => void
  pause: () => void
  resume: () => void
  clear: () => void

  // Data
  addData: (data: ChartDataPoint | ChartDataPoint[]) => void
  addDataPoint: (timestamp: number, value: number, volume?: number) => void
  getLatestData: () => ChartDataPoint[]
  getBufferData: () => ChartDataPoint[]
  getDataInRange: (startTime: number, endTime: number) => ChartDataPoint[]

  // Status
  isStreaming: boolean
  isPaused: boolean
  getStats: () => any
  getBufferStats: () => any

  // Configuration
  updateOptions: (options: Partial<UseChartStreamingOptions>) => void
}

// Chart streaming hook
export const useChartStreaming = (options: UseChartStreamingOptions): UseChartStreamingReturn => {
  const {
    chart,
    maxDataPoints = 1000,
    updateInterval = 1000,
    enableAnimation = false,
    enableCompression = false,
    enableThrottling = true,
    bufferSize = 1000,
    autoStart = true,
    onDataUpdate,
    onBufferOverflow,
    onPerformanceWarning
  } = options

  // Refs
  const streamingManagerRef = useRef<ChartStreamingManager | null>(null)
  const dataBufferRef = useRef<RealTimeDataBuffer | null>(null)
  const isInitializedRef = useRef(false)
  const lastUpdateRef = useRef(0)

  // State
  const [isStreaming, setIsStreaming] = useState(false)
  const [isPaused, setIsPaused] = useState(false)

  // Initialize streaming manager
  const initialize = useCallback(() => {
    if (isInitializedRef.current || !chart) return

    // Create streaming manager
    streamingManagerRef.current = new ChartStreamingManager(chart, {
      maxDataPoints,
      updateInterval,
      enableAnimation,
      onDataUpdate: (chart, data) => {
        onDataUpdate?.(data)

        // Add to buffer
        if (dataBufferRef.current) {
          data.forEach(point => {
            dataBufferRef.current!.add({
              timestamp: point.timestamp,
              data: point,
              sequence: 0
            })
          })
        }
      },
      onBufferOverflow: (overflowCount) => {
        onBufferOverflow?.(overflowCount)
        console.warn(`Chart buffer overflow: ${overflowCount} points dropped`)
      }
    })

    // Create data buffer
    dataBufferRef.current = new RealTimeDataBuffer({
      maxSize: bufferSize,
      enableCompression,
      enableDeduplication: true
    })

    isInitializedRef.current = true

    // Auto-start
    if (autoStart) {
      streamingManagerRef.current.start()
      setIsStreaming(true)
    }
  }, [
    chart,
    maxDataPoints,
    updateInterval,
    enableAnimation,
    bufferSize,
    enableCompression,
    autoStart,
    onDataUpdate,
    onBufferOverflow
  ])

  // Start streaming
  const start = useCallback(() => {
    if (!streamingManagerRef.current) {
      initialize()
    }

    if (streamingManagerRef.current) {
      streamingManagerRef.current.start()
      setIsStreaming(true)
      setIsPaused(false)
    }
  }, [initialize])

  // Stop streaming
  const stop = useCallback(() => {
    if (streamingManagerRef.current) {
      streamingManagerRef.current.stop()
      setIsStreaming(false)
      setIsPaused(false)
    }
  }, [])

  // Pause streaming
  const pause = useCallback(() => {
    if (streamingManagerRef.current && isStreaming) {
      streamingManagerRef.current.stop()
      setIsPaused(true)
    }
  }, [isStreaming])

  // Resume streaming
  const resume = useCallback(() => {
    if (streamingManagerRef.current && isPaused) {
      streamingManagerRef.current.start()
      setIsPaused(false)
    }
  }, [isPaused])

  // Clear data
  const clear = useCallback(() => {
    if (streamingManagerRef.current) {
      streamingManagerRef.current.clear()
    }
    if (dataBufferRef.current) {
      dataBufferRef.current.clear()
    }
  }, [])

  // Add data points
  const addData = useCallback((data: ChartDataPoint | ChartDataPoint[]) => {
    if (!streamingManagerRef.current) return

    const dataArray = Array.isArray(data) ? data : [data]

    // Throttle updates if enabled
    if (enableThrottling) {
      const now = Date.now()
      if (now - lastUpdateRef.current < updateInterval) {
        return
      }
      lastUpdateRef.current = now
    }

    dataArray.forEach(point => {
      streamingManagerRef.current!.addData({
        timestamp: point.timestamp.getTime(),
        value: point.close,
        volume: point.volume
      })
    })
  }, [enableThrottling, updateInterval])

  // Add single data point
  const addDataPoint = useCallback((timestamp: number, value: number, volume?: number) => {
    addData({
      timestamp: new Date(timestamp),
      open: value,
      high: value,
      low: value,
      close: value,
      volume: volume || 0
    })
  }, [addData])

  // Get latest data from chart
  const getLatestData = useCallback((): ChartDataPoint[] => {
    if (!chart || !chart.data || !chart.data.datasets || chart.data.datasets.length === 0) {
      return []
    }

    const dataset = chart.data.datasets[0]
    const labels = chart.data.labels || []

    return dataset.data.map((point, index) => ({
      timestamp: new Date(labels[index] as string),
      open: (point as any).y || (point as any).value || point,
      high: (point as any).y || (point as any).value || point,
      low: (point as any).y || (point as any).value || point,
      close: (point as any).y || (point as any).value || point,
      volume: 0
    }))
  }, [chart])

  // Get buffer data
  const getBufferData = useCallback((): ChartDataPoint[] => {
    if (!dataBufferRef.current) return []

    return dataBufferRef.current.getAll().map(item => item.data as ChartDataPoint)
  }, [])

  // Get data in time range
  const getDataInRange = useCallback((startTime: number, endTime: number): ChartDataPoint[] => {
    if (!dataBufferRef.current) return []

    const bufferData = dataBufferRef.current.getAll()
    return bufferData
      .filter(item => item.timestamp >= startTime && item.timestamp <= endTime)
      .map(item => item.data as ChartDataPoint)
  }, [])

  // Get streaming statistics
  const getStats = useCallback(() => {
    if (!streamingManagerRef.current) {
      return {
        isStreaming: false,
        isPaused: false,
        updateInterval: 0,
        dataPointsPerSecond: 0
      }
    }

    const stats = streamingManagerRef.current.getStats()
    return {
      isStreaming: stats.isRunning,
      isPaused,
      updateInterval,
      dataPointsPerSecond: stats.dataPointsPerSecond,
      lastUpdateTime: stats.lastUpdateTime,
      bufferStats: stats.bufferStats
    }
  }, [isPaused, updateInterval])

  // Get buffer statistics
  const getBufferStats = useCallback(() => {
    if (!dataBufferRef.current) {
      return {
        size: 0,
        maxSize: 0,
        memoryUsage: 0,
        compressionRatio: 1
      }
    }

    return dataBufferRef.current.getStats()
  }, [])

  // Update streaming options
  const updateOptions = useCallback((newOptions: Partial<UseChartStreamingOptions>) => {
    if (streamingManagerRef.current) {
      streamingManagerRef.current.updateOptions({
        maxDataPoints: newOptions.maxDataPoints || maxDataPoints,
        updateInterval: newOptions.updateInterval || updateInterval,
        enableAnimation: newOptions.enableAnimation ?? enableAnimation
      })
    }

    if (dataBufferRef.current && newOptions.bufferSize) {
      dataBufferRef.current.updateOptions({
        maxSize: newOptions.bufferSize,
        enableCompression: newOptions.enableCompression ?? enableCompression
      })
    }
  }, [maxDataPoints, updateInterval, enableAnimation, enableCompression])

  // Monitor performance
  useEffect(() => {
    const interval = setInterval(() => {
      const stats = getStats()

      // Check for performance issues
      if (stats.dataPointsPerSecond < 30 || stats.bufferStats.overflowCount > 0) {
        onPerformanceWarning?.(stats)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [getStats, onPerformanceWarning])

  // Initialize on mount
  useEffect(() => {
    initialize()

    return () => {
      if (streamingManagerRef.current) {
        streamingManagerRef.current.destroy()
      }
      if (dataBufferRef.current) {
        dataBufferRef.current.destroy()
      }
    }
  }, [initialize])

  return {
    start,
    stop,
    pause,
    resume,
    clear,
    addData,
    addDataPoint,
    getLatestData,
    getBufferData,
    getDataInRange,
    isStreaming,
    isPaused,
    getStats,
    getBufferStats,
    updateOptions
  }
}

// Hook for streaming multiple charts
export const useMultiChartStreaming = (
  charts: Array<{ chart: Chart; id: string }>,
  options: UseChartStreamingOptions
) => {
  const streamingStatesRef = useRef<Map<string, UseChartStreamingReturn>>(new Map())

  // Initialize streaming for each chart
  useEffect(() => {
    charts.forEach(({ chart, id }) => {
      if (!streamingStatesRef.current.has(id)) {
        const streaming = useChartStreaming({
          ...options,
          chart
        })
        streamingStatesRef.current.set(id, streaming)
      }
    })
  }, [charts, options])

  // Control all charts
  const startAll = useCallback(() => {
    streamingStatesRef.current.forEach(streaming => streaming.start())
  }, [])

  const stopAll = useCallback(() => {
    streamingStatesRef.current.forEach(streaming => streaming.stop())
  }, [])

  const clearAll = useCallback(() => {
    streamingStatesRef.current.forEach(streaming => streaming.clear())
  }, [])

  // Add data to all charts
  const addDataToAll = useCallback((data: ChartDataPoint | ChartDataPoint[]) => {
    streamingStatesRef.current.forEach(streaming => streaming.addData(data))
  }, [])

  // Get statistics for all charts
  const getAllStats = useCallback(() => {
    const stats: Record<string, any> = {}
    streamingStatesRef.current.forEach((streaming, id) => {
      stats[id] = streaming.getStats()
    })
    return stats
  }, [])

  return {
    startAll,
    stopAll,
    clearAll,
    addDataToAll,
    getAllStats,
    getChartStreaming: (id: string) => streamingStatesRef.current.get(id)
  }
}

export default useChartStreaming