import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

// Enhanced data point with additional metadata
export interface EnhancedDataPoint {
  timestamp: number
  value: number
  label?: string
  metadata?: Record<string, any>
  id?: string
  batch?: number
}

// Data processing options
export interface DataProcessorOptions {
  // Buffer management
  bufferSize?: number
  maxDataPoints?: number

  // Performance optimization
  enableBatching?: boolean
  batchSize?: number
  batchTimeout?: number

  // Data reduction
  enableDecimation?: boolean
  decimationThreshold?: number
  decimationAlgorithm?: 'lttb' | 'min-max' | 'average'

  // Smoothing
  enableSmoothing?: boolean
  smoothingWindow?: number
  smoothingMethod?: 'sma' | 'ema' | 'weighted'

  // Memory management
  enableMemoryOptimization?: boolean
  gcThreshold?: number

  // Data validation
  enableValidation?: boolean
  valueRange?: { min?: number; max?: number }
  outlierDetection?: boolean
  outlierThreshold?: number
}

// Processed data result
export interface ProcessedData {
  data: EnhancedDataPoint[]
  stats: {
    count: number
    min: number
    max: number
    avg: number
    stdDev: number
    lastUpdate: number
  }
  performance: {
    processingTime: number
    memoryUsage: number
    droppedPoints: number
  }
}

// WebSocket configuration
interface WebSocketConfig {
  url?: string
  channel?: string
  autoReconnect?: boolean
  reconnectDelay?: number
  heartbeatInterval?: number
}

export const useRealTimeDataProcessor = (
  wsConfig: WebSocketConfig = {},
  processorOptions: DataProcessorOptions = {}
) => {
  // Configuration
  const {
    url = process.env.REACT_APP_WS_URL || 'ws://localhost:3003',
    channel = 'realtime-data',
    autoReconnect = true,
    reconnectDelay = 3000,
    heartbeatInterval = 30000
  } = wsConfig

  const {
    bufferSize = 1000,
    maxDataPoints = 10000,
    enableBatching = true,
    batchSize = 50,
    batchTimeout = 100,
    enableDecimation = true,
    decimationThreshold = 500,
    decimationAlgorithm = 'lttb',
    enableSmoothing = false,
    smoothingWindow = 5,
    smoothingMethod = 'sma',
    enableMemoryOptimization = true,
    gcThreshold = 0.8,
    enableValidation = true,
    valueRange,
    outlierDetection = false,
    outlierThreshold = 3
  } = processorOptions

  // State
  const [data, setData] = useState<EnhancedDataPoint[]>([])
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Refs
  const socketRef = useRef<Socket | null>(null)
  const bufferRef = useRef<EnhancedDataPoint[]>([])
  const batchTimerRef = useRef<NodeJS.Timeout | null>(null)
  const processingQueueRef = useRef<EnhancedDataPoint[][]>([])
  const statsRef = useRef({
    processingTime: 0,
    memoryUsage: 0,
    droppedPoints: 0,
    lastGC: Date.now()
  })

  // Performance monitoring
  const performanceMonitor = useCallback(() => {
    if (enableMemoryOptimization) {
      const memUsage = bufferRef.current.length / bufferSize
      if (memUsage > gcThreshold) {
        // Trigger garbage collection
        bufferRef.current = bufferRef.current.slice(-Math.floor(bufferSize * 0.7))
        statsRef.current.lastGC = Date.now()
      }
      statsRef.current.memoryUsage = memUsage
    }
  }, [bufferSize, gcThreshold, enableMemoryOptimization])

  // Data validation
  const validatePoint = useCallback((point: EnhancedDataPoint): boolean => {
    if (!enableValidation) return true

    // Check value range
    if (valueRange) {
      if (valueRange.min !== undefined && point.value < valueRange.min) return false
      if (valueRange.max !== undefined && point.value > valueRange.max) return false
    }

    // Check timestamp
    if (!point.timestamp || point.timestamp <= 0) return false

    return true
  }, [enableValidation, valueRange])

  // Outlier detection using Z-score
  const detectOutlier = useCallback((point: EnhancedDataPoint, data: EnhancedDataPoint[]): boolean => {
    if (!outlierDetection || data.length < 10) return false

    const values = data.map(d => d.value)
    const mean = values.reduce((a, b) => a + b, 0) / values.length
    const stdDev = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / values.length)

    const zScore = Math.abs((point.value - mean) / stdDev)
    return zScore > outlierThreshold
  }, [outlierDetection, outlierThreshold])

  // LTTB (Largest Triangle Three Buckets) decimation algorithm
  const lttbDecimation = useCallback((data: EnhancedDataPoint[], threshold: number): EnhancedDataPoint[] => {
    if (data.length <= threshold) return data

    const sampled: EnhancedDataPoint[] = []
    const bucketSize = (data.length - 2) / (threshold - 2)

    // Always include first and last points
    sampled[0] = data[0]
    sampled[threshold - 1] = data[data.length - 1]

    let a = 0

    for (let i = 0; i < threshold - 2; i++) {
      // Calculate bucket boundaries
      const avgRangeStart = Math.floor((i + 1) * bucketSize) + 1
      const avgRangeEnd = Math.floor((i + 2) * bucketSize) + 1

      // Average bucket
      let avgX = 0
      let avgY = 0
      const avgRangeLength = avgRangeEnd - avgRangeStart

      for (let j = avgRangeStart; j < avgRangeEnd && j < data.length; j++) {
        avgX += data[j].timestamp
        avgY += data[j].value
      }
      avgX /= avgRangeLength
      avgY /= avgRangeLength

      // Find the max area point
      const rangeStart = Math.floor(i * bucketSize) + 1
      const rangeEnd = Math.floor((i + 1) * bucketSize) + 1
      let maxArea = -1
      let maxAreaIndex = rangeStart

      for (let j = rangeStart; j < rangeEnd && j < data.length; j++) {
        const area = Math.abs(
          (data[a].timestamp - avgX) * (data[j].value - data[a].value) -
          (data[a].timestamp - data[j].timestamp) * (avgY - data[a].value)
        ) * 0.5

        if (area > maxArea) {
          maxArea = area
          maxAreaIndex = j
        }
      }

      sampled[i + 1] = data[maxAreaIndex]
      a = maxAreaIndex
    }

    return sampled
  }, [])

  // Data smoothing
  const smoothData = useCallback((data: EnhancedDataPoint[]): EnhancedDataPoint[] => {
    if (!enableSmoothing || data.length < smoothingWindow) return data

    const smoothed: EnhancedDataPoint[] = []
    const weights = smoothingMethod === 'ema'
      ? generateEmaWeights(smoothingWindow)
      : smoothingMethod === 'weighted'
      ? generateLinearWeights(smoothingWindow)
      : null

    for (let i = 0; i < data.length; i++) {
      if (i < smoothingWindow - 1) {
        smoothed.push(data[i])
      } else {
        const window = data.slice(i - smoothingWindow + 1, i + 1)
        let smoothedValue = 0

        if (weights) {
          // EMA or weighted moving average
          for (let j = 0; j < window.length; j++) {
            smoothedValue += window[j].value * weights[j]
          }
        } else {
          // Simple moving average
          smoothedValue = window.reduce((sum, point) => sum + point.value, 0) / window.length
        }

        smoothed.push({
          ...data[i],
          value: smoothedValue
        })
      }
    }

    return smoothed
  }, [enableSmoothing, smoothingWindow, smoothingMethod])

  // Generate EMA weights
  const generateEmaWeights = (period: number): number[] => {
    const weights = []
    const alpha = 2 / (period + 1)

    for (let i = 0; i < period; i++) {
      weights.push(alpha * Math.pow(1 - alpha, period - 1 - i))
    }

    return weights
  }

  // Generate linear weights
  const generateLinearWeights = (period: number): number[] => {
    const weights = []
    let sum = 0

    for (let i = 1; i <= period; i++) {
      weights.push(i)
      sum += i
    }

    return weights.map(w => w / sum)
  }

  // Process data batch
  const processDataBatch = useCallback((batch: EnhancedDataPoint[]): ProcessedData => {
    const startTime = performance.now()

    // Filter valid points
    let validData = batch.filter(point => {
      if (!validatePoint(point)) {
        statsRef.current.droppedPoints++
        return false
      }

      // Remove outliers
      if (detectOutlier(point, data)) {
        statsRef.current.droppedPoints++
        return false
      }

      return true
    })

    // Apply smoothing if enabled
    if (enableSmoothing) {
      validData = smoothData(validData)
    }

    // Apply decimation if needed
    if (enableDecimation && validData.length > decimationThreshold) {
      switch (decimationAlgorithm) {
        case 'lttb':
          validData = lttbDecimation(validData, decimationThreshold)
          break
        case 'min-max':
          validData = minMaxDecimation(validData, decimationThreshold)
          break
        case 'average':
          validData = averageDecimation(validData, decimationThreshold)
          break
      }
    }

    // Calculate statistics
    const values = validData.map(d => d.value)
    const count = values.length
    const min = count > 0 ? Math.min(...values) : 0
    const max = count > 0 ? Math.max(...values) : 0
    const avg = count > 0 ? values.reduce((a, b) => a + b, 0) / count : 0
    const stdDev = count > 1
      ? Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - avg, 2), 0) / count)
      : 0

    const processingTime = performance.now() - startTime
    statsRef.current.processingTime = processingTime

    return {
      data: validData,
      stats: {
        count,
        min,
        max,
        avg,
        stdDev,
        lastUpdate: Date.now()
      },
      performance: {
        processingTime,
        memoryUsage: statsRef.current.memoryUsage,
        droppedPoints: statsRef.current.droppedPoints
      }
    }
  }, [
    data,
    validatePoint,
    detectOutlier,
    enableSmoothing,
    smoothData,
    enableDecimation,
    decimationThreshold,
    decimationAlgorithm,
    lttbDecimation
  ])

  // Min-max decimation
  const minMaxDecimation = (data: EnhancedDataPoint[], threshold: number): EnhancedDataPoint[] => {
    if (data.length <= threshold) return data

    const bucketSize = Math.ceil(data.length / threshold)
    const sampled: EnhancedDataPoint[] = []

    for (let i = 0; i < data.length; i += bucketSize) {
      const bucket = data.slice(i, i + bucketSize)
      const minPoint = bucket.reduce((min, point) => point.value < min.value ? point : min, bucket[0])
      const maxPoint = bucket.reduce((max, point) => point.value > max.value ? point : max, bucket[0])

      sampled.push(minPoint)
      if (minPoint !== maxPoint) {
        sampled.push(maxPoint)
      }
    }

    return sampled.slice(0, threshold)
  }

  // Average decimation
  const averageDecimation = (data: EnhancedDataPoint[], threshold: number): EnhancedDataPoint[] => {
    if (data.length <= threshold) return data

    const bucketSize = Math.ceil(data.length / threshold)
    const sampled: EnhancedDataPoint[] = []

    for (let i = 0; i < data.length; i += bucketSize) {
      const bucket = data.slice(i, i + bucketSize)
      const avgValue = bucket.reduce((sum, point) => sum + point.value, 0) / bucket.length
      const avgTimestamp = bucket.reduce((sum, point) => sum + point.timestamp, 0) / bucket.length

      sampled.push({
        ...bucket[0],
        timestamp: avgTimestamp,
        value: avgValue
      })
    }

    return sampled
  }

  // Process queued data
  const processQueue = useCallback(() => {
    if (processingQueueRef.current.length === 0 || isProcessing) return

    setIsProcessing(true)

    const batch = processingQueueRef.current.shift()!
    const result = processDataBatch(batch)

    setProcessedData(result)

    // Update main data buffer
    setData(prevData => {
      const newData = [...prevData, ...result.data]
      if (newData.length > maxDataPoints) {
        return newData.slice(-maxDataPoints)
      }
      return newData
    })

    setIsProcessing(false)
  }, [isProcessing, processDataBatch, maxDataPoints])

  // Add data point to buffer
  const addDataPoint = useCallback((point: EnhancedDataPoint) => {
    if (!validatePoint(point)) {
      statsRef.current.droppedPoints++
      return
    }

    // Add to buffer
    bufferRef.current.push(point)

    // Batch processing
    if (enableBatching) {
      if (bufferRef.current.length >= batchSize) {
        const batch = bufferRef.current.splice(0, batchSize)
        processingQueueRef.current.push(batch)
        processQueue()
      }
    } else {
      processingQueueRef.current.push([point])
      processQueue()
    }

    performanceMonitor()
  }, [validatePoint, enableBatching, batchSize, processQueue, performanceMonitor])

  // WebSocket connection
  useEffect(() => {
    const connect = () => {
      try {
        socketRef.current = io(url, {
          transports: ['websocket'],
          upgrade: false
        })

        socketRef.current.on('connect', () => {
          setIsConnected(true)
          setError(null)
          socketRef.current?.emit('subscribe', { channel })
        })

        socketRef.current.on('disconnect', () => {
          setIsConnected(false)
          if (autoReconnect) {
            setTimeout(connect, reconnectDelay)
          }
        })

        socketRef.current.on('connect_error', (err) => {
          setError(err.message)
          setIsConnected(false)
        })

        socketRef.current.on(channel, (newData: EnhancedDataPoint | EnhancedDataPoint[]) => {
          if (Array.isArray(newData)) {
            newData.forEach(point => addDataPoint({
              ...point,
              id: `${point.timestamp}-${Math.random()}`
            }))
          } else {
            addDataPoint({
              ...newData,
              id: `${newData.timestamp}-${Math.random()}`
            })
          }
        })

        // Heartbeat
        const heartbeat = setInterval(() => {
          if (socketRef.current?.connected) {
            socketRef.current.emit('ping')
          }
        }, heartbeatInterval)

        return () => clearInterval(heartbeat)
      } catch (err) {
        setError('Failed to establish connection')
      }
    }

    connect()

    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
      if (batchTimerRef.current) {
        clearTimeout(batchTimerRef.current)
      }
    }
  }, [url, channel, autoReconnect, reconnectDelay, heartbeatInterval, addDataPoint])

  // Process any remaining batch on timeout
  useEffect(() => {
    if (enableBatching && bufferRef.current.length > 0) {
      batchTimerRef.current = setTimeout(() => {
        if (bufferRef.current.length > 0) {
          const batch = bufferRef.current.splice(0, bufferRef.current.length)
          processingQueueRef.current.push(batch)
          processQueue()
        }
      }, batchTimeout)
    }

    return () => {
      if (batchTimerRef.current) {
        clearTimeout(batchTimerRef.current)
      }
    }
  }, [data, enableBatching, batchTimeout, processQueue])

  // Clear data
  const clear = useCallback(() => {
    setData([])
    setProcessedData(null)
    bufferRef.current = []
    processingQueueRef.current = []
    statsRef.current = {
      processingTime: 0,
      memoryUsage: 0,
      droppedPoints: 0,
      lastGC: Date.now()
    }
  }, [])

  return {
    data,
    processedData,
    isConnected,
    isProcessing,
    error,
    clear,
    stats: statsRef.current
  }
}