import { useState, useEffect, useRef, useCallback } from 'react'
import {
  DataSubscription,
  WebSocketMessage,
  DataStreamConfig,
  ChartDataState,
  DataMetrics
} from '../types/data.types'
import { TimeSeriesDataPoint } from '../types/chart.types'

interface UseRealTimeDataOptions {
  url: string
  subscriptions: DataSubscription[]
  bufferSize?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onDataUpdate?: (subscriptionId: string, data: TimeSeriesDataPoint[]) => void
  onConnectionChange?: (isConnected: boolean) => void
  onError?: (error: Error) => void
}

interface UseRealTimeDataReturn {
  data: Record<string, TimeSeriesDataPoint[]>
  isConnected: boolean
  state: ChartDataState
  metrics: DataMetrics
  subscribe: (subscription: DataSubscription) => void
  unsubscribe: (subscriptionId: string) => void
  pause: () => void
  resume: () => void
  clearBuffer: (subscriptionId?: string) => void
}

// WebSocket manager for handling multiple subscriptions
class WebSocketManager {
  private ws: WebSocket | null = null
  private subscriptions: Map<string, DataSubscription> = new Map()
  private buffers: Map<string, TimeSeriesDataPoint[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000
  private isDestroyed = false
  private lastPingTime = 0
  private pingInterval: NodeJS.Timeout | null = null
  private messageQueue: WebSocketMessage[] = []

  // Metrics tracking
  private metrics: DataMetrics = {
    latency: 0,
    throughput: 0,
    errorRate: 0,
    bufferUtilization: 0,
    memoryUsage: 0,
    updateFrequency: 0
  }
  private messageCount = 0
  private lastThroughputCalculation = Date.now()

  constructor(
    private url: string,
    private options: {
      onMessage?: (message: WebSocketMessage) => void
      onConnectionChange?: (isConnected: boolean) => void
      onError?: (error: Error) => void
      maxReconnectAttempts?: number
      reconnectInterval?: number
    }
  ) {
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5
    this.reconnectInterval = options.reconnectInterval || 3000
  }

  connect() {
    if (this.isDestroyed || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      this.ws = new WebSocket(this.url)
      this.setupEventListeners()
    } catch (error) {
      this.options.onError?.(error as Error)
      this.scheduleReconnect()
    }
  }

  private setupEventListeners() {
    if (!this.ws) return

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.options.onConnectionChange?.(true)
      this.startPingInterval()

      // Resubscribe to all active subscriptions
      this.subscriptions.forEach(sub => {
        if (sub.isActive) {
          this.sendSubscription(sub)
        }
      })

      // Process queued messages
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift()
        if (message) {
          this.sendMessage(message)
        }
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage
        this.updateMetrics()
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      this.options.onConnectionChange?.(false)
      this.stopPingInterval()

      if (!this.isDestroyed && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      this.options.onError?.(new Error('WebSocket error'))
    }
  }

  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now()
        this.sendMessage({
          type: 'heartbeat',
          channel: 'ping',
          timestamp: this.lastPingTime
        })
      }
    }, 30000)
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private handleMessage(message: WebSocketMessage) {
    if (message.type === 'data' && message.channel && message.data) {
      const subscription = Array.from(this.subscriptions.values())
        .find(sub => sub.channel === message.channel)

      if (subscription && subscription.isActive) {
        const buffer = this.buffers.get(subscription.id) || []
        const dataPoint = this.transformToDataPoint(message.data, subscription)

        // Add to buffer with size limit
        const newBuffer = [...buffer, dataPoint]
        if (newBuffer.length > (subscription.bufferSize || 1000)) {
          newBuffer.shift()
        }

        this.buffers.set(subscription.id, newBuffer)
        subscription.lastUpdate = new Date()

        this.options.onMessage?.(message)
      }
    }
  }

  private transformToDataPoint(data: any, subscription: DataSubscription): TimeSeriesDataPoint {
    // Transform raw data to TimeSeriesDataPoint format
    if (data.timestamp && typeof data.timestamp === 'number') {
      return {
        timestamp: new Date(data.timestamp),
        value: data.value || data.price || data.close || 0,
        volume: data.volume,
        metadata: {
          ...data,
          subscriptionId: subscription.id,
          symbol: subscription.symbol,
          indicator: subscription.indicator
        }
      }
    }

    return {
      timestamp: new Date(),
      value: 0,
      metadata: data
    }
  }

  private updateMetrics() {
    this.messageCount++
    const now = Date.now()
    const elapsed = now - this.lastThroughputCalculation

    if (elapsed >= 1000) {
      this.metrics.throughput = (this.messageCount * 1000) / elapsed
      this.messageCount = 0
      this.lastThroughputCalculation = now
    }
  }

  private scheduleReconnect() {
    setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1))
  }

  subscribe(subscription: DataSubscription) {
    this.subscriptions.set(subscription.id, subscription)

    if (!this.buffers.has(subscription.id)) {
      this.buffers.set(subscription.id, [])
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN && subscription.isActive) {
      this.sendSubscription(subscription)
    }
  }

  unsubscribe(subscriptionId: string) {
    const subscription = this.subscriptions.get(subscriptionId)
    if (subscription) {
      subscription.isActive = false

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({
          type: 'subscription',
          channel: subscription.channel,
          timestamp: Date.now(),
          id: subscriptionId,
          data: { action: 'unsubscribe' }
        })
      }

      this.subscriptions.delete(subscriptionId)
      this.buffers.delete(subscriptionId)
    }
  }

  private sendSubscription(subscription: DataSubscription) {
    this.sendMessage({
      type: 'subscription',
      channel: subscription.channel,
      timestamp: Date.now(),
      id: subscription.id,
      data: {
        action: 'subscribe',
        symbol: subscription.symbol,
        indicator: subscription.indicator,
        timeframe: subscription.timeframe,
        bufferSize: subscription.bufferSize
      }
    })
  }

  private sendMessage(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(message)
    }
  }

  getBuffer(subscriptionId: string): TimeSeriesDataPoint[] {
    return this.buffers.get(subscriptionId) || []
  }

  clearBuffer(subscriptionId?: string) {
    if (subscriptionId) {
      this.buffers.delete(subscriptionId)
    } else {
      this.buffers.clear()
    }
  }

  getMetrics(): DataMetrics {
    // Calculate buffer utilization
    let totalBufferSize = 0
    let maxTotalSize = 0

    this.subscriptions.forEach(sub => {
      const buffer = this.buffers.get(sub.id) || []
      totalBufferSize += buffer.length
      maxTotalSize += sub.bufferSize || 1000
    })

    this.metrics.bufferUtilization = maxTotalSize > 0 ? (totalBufferSize / maxTotalSize) * 100 : 0

    return { ...this.metrics }
  }

  destroy() {
    this.isDestroyed = true
    this.stopPingInterval()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.subscriptions.clear()
    this.buffers.clear()
    this.messageQueue = []
  }
}

export function useRealTimeData(options: UseRealTimeDataOptions): UseRealTimeDataReturn {
  const [data, setData] = useState<Record<string, TimeSeriesDataPoint[]>>({})
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const wsManagerRef = useRef<WebSocketManager>()
  const [state, setState] = useState<ChartDataState>({
    isLive: false,
    isPaused: false,
    lastUpdate: new Date(),
    updateCount: 0,
    errorCount: 0,
    buffer: {
      size: 0,
      maxSize: 0,
      utilization: 0
    }
  })
  const [metrics, setMetrics] = useState<DataMetrics>({
    latency: 0,
    throughput: 0,
    errorRate: 0,
    bufferUtilization: 0,
    memoryUsage: 0,
    updateFrequency: 0
  })

  // Initialize WebSocket manager
  useEffect(() => {
    wsManagerRef.current = new WebSocketManager(options.url, {
      onMessage: (message) => {
        if (!isPaused && message.channel) {
          const subscription = options.subscriptions.find(s => s.channel === message.channel)
          if (subscription) {
            const buffer = wsManagerRef.current?.getBuffer(subscription.id) || []

            setData(prev => ({
              ...prev,
              [subscription.id]: buffer
            }))

            options.onDataUpdate?.(subscription.id, buffer)

            setState(prev => ({
              ...prev,
              isLive: true,
              lastUpdate: new Date(),
              updateCount: prev.updateCount + 1,
              buffer: {
                size: buffer.length,
                maxSize: subscription.bufferSize || 1000,
                utilization: (buffer.length / (subscription.bufferSize || 1000)) * 100
              }
            }))
          }
        }
      },
      onConnectionChange: setIsConnected,
      onError: (error) => {
        setState(prev => ({
          ...prev,
          errorCount: prev.errorCount + 1
        }))
        options.onError?.(error)
      },
      maxReconnectAttempts: options.maxReconnectAttempts,
      reconnectInterval: options.reconnectInterval
    })

    return () => {
      wsManagerRef.current?.destroy()
    }
  }, [options.url, options.maxReconnectAttempts, options.reconnectInterval])

  // Initialize subscriptions
  useEffect(() => {
    if (wsManagerRef.current) {
      options.subscriptions.forEach(subscription => {
        wsManagerRef.current?.subscribe(subscription)
      })
    }
  }, [options.subscriptions])

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsManagerRef.current) {
        const currentMetrics = wsManagerRef.current.getMetrics()
        setMetrics(currentMetrics)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const subscribe = useCallback((subscription: DataSubscription) => {
    wsManagerRef.current?.subscribe(subscription)
  }, [])

  const unsubscribe = useCallback((subscriptionId: string) => {
    wsManagerRef.current?.unsubscribe(subscriptionId)
    setData(prev => {
      const newData = { ...prev }
      delete newData[subscriptionId]
      return newData
    })
  }, [])

  const pause = useCallback(() => {
    setIsPaused(true)
    setState(prev => ({ ...prev, isPaused: true }))
  }, [])

  const resume = useCallback(() => {
    setIsPaused(false)
    setState(prev => ({ ...prev, isPaused: false }))
  }, [])

  const clearBuffer = useCallback((subscriptionId?: string) => {
    wsManagerRef.current?.clearBuffer(subscriptionId)
    if (subscriptionId) {
      setData(prev => {
        const newData = { ...prev }
        delete newData[subscriptionId]
        return newData
      })
    } else {
      setData({})
    }
  }, [])

  return {
    data,
    isConnected,
    state,
    metrics,
    subscribe,
    unsubscribe,
    pause,
    resume,
    clearBuffer
  }
}