import { useState, useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

export interface RealTimeDataPoint {
  timestamp: string | Date
  value: number
  metadata?: Record<string, any>
}

export interface UseRealTimeDataOptions {
  initialData?: RealTimeDataPoint[]
  maxPoints?: number
  updateInterval?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
  bufferUpdates?: boolean
  bufferSize?: number
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Error) => void
  onData?: (data: RealTimeDataPoint) => void
}

export const useRealTimeData = (
  channel: string | null,
  options: UseRealTimeDataOptions = {}
) => {
  const {
    initialData = [],
    maxPoints = 100,
    updateInterval = 1000,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    bufferUpdates = false,
    bufferSize = 10,
    onConnect,
    onDisconnect,
    onError,
    onData,
  } = options

  const [data, setData] = useState<RealTimeDataPoint[]>(initialData)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const socketRef = useRef<Socket | null>(null)
  const bufferRef = useRef<RealTimeDataPoint[]>([])
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Add new data point
  const addDataPoint = useCallback((newPoint: RealTimeDataPoint) => {
    setData(prevData => {
      let updatedData = [...prevData, newPoint]

      // Limit data points
      if (maxPoints > 0 && updatedData.length > maxPoints) {
        updatedData = updatedData.slice(-maxPoints)
      }

      return updatedData
    })

    // Trigger callback
    onData?.(newPoint)
  }, [maxPoints, onData])

  // Process buffered updates
  const processBuffer = useCallback(() => {
    if (bufferRef.current.length > 0) {
      const points = bufferRef.current.splice(0)
      points.forEach(point => addDataPoint(point))
    }
  }, [addDataPoint])

  // Setup socket connection
  const setupSocket = useCallback(() => {
    if (!channel) return

    setIsConnecting(true)
    setError(null)

    // Create socket connection
    socketRef.current = io('/realtime', {
      transports: ['websocket'],
      upgrade: false,
      rememberUpgrade: false,
    })

    // Connection handlers
    socketRef.current.on('connect', () => {
      setIsConnected(true)
      setIsConnecting(false)
      setReconnectAttempts(0)
      onConnect?.()

      // Subscribe to channel
      socketRef.current?.emit('subscribe', { channel })
    })

    socketRef.current.on('disconnect', () => {
      setIsConnected(false)
      setIsConnecting(false)
      onDisconnect?.()
    })

    socketRef.current.on('error', (err) => {
      setError(err)
      setIsConnecting(false)
      onError?.(err)
    })

    // Data handler
    socketRef.current.on(`data:${channel}`, (newData: RealTimeDataPoint) => {
      if (bufferUpdates) {
        // Buffer updates and process them periodically
        bufferRef.current.push(newData)
        if (bufferRef.current.length >= bufferSize) {
          processBuffer()
        }
      } else {
        // Process updates immediately
        addDataPoint(newData)
      }
    })

    // Setup buffer processing interval
    if (bufferUpdates && !intervalRef.current) {
      intervalRef.current = setInterval(processBuffer, updateInterval)
    }
  }, [
    channel,
    bufferUpdates,
    bufferSize,
    updateInterval,
    onConnect,
    onDisconnect,
    onError,
    addDataPoint,
    processBuffer,
  ])

  // Reconnect logic
  const reconnect = useCallback(() => {
    if (reconnectAttempts < maxReconnectAttempts) {
      setReconnectAttempts(prev => prev + 1)
      setTimeout(setupSocket, reconnectInterval)
    } else {
      setError(new Error('Max reconnection attempts reached'))
    }
  }, [reconnectAttempts, maxReconnectAttempts, reconnectInterval, setupSocket])

  // Initial connection setup
  useEffect(() => {
    if (channel) {
      setupSocket()
    }

    return () => {
      // Cleanup
      if (socketRef.current) {
        socketRef.current.disconnect()
        socketRef.current = null
      }

      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }

      bufferRef.current = []
    }
  }, [channel, setupSocket])

  // Handle reconnection on disconnect
  useEffect(() => {
    if (!isConnected && !isConnecting && reconnectAttempts > 0) {
      reconnect()
    }
  }, [isConnected, isConnecting, reconnectAttempts, reconnect])

  // Manual methods
  const clearData = useCallback(() => {
    setData([])
    bufferRef.current = []
  }, [])

  const addManualData = useCallback((points: RealTimeDataPoint | RealTimeDataPoint[]) => {
    const pointsArray = Array.isArray(points) ? points : [points]
    pointsArray.forEach(point => addDataPoint(point))
  }, [addDataPoint])

  const subscribe = useCallback((newChannel: string) => {
    if (socketRef.current) {
      socketRef.current.emit('subscribe', { channel: newChannel })
    }
  }, [])

  const unsubscribe = useCallback((channelToUnsubscribe: string) => {
    if (socketRef.current) {
      socketRef.current.emit('unsubscribe', { channel: channelToUnsubscribe })
    }
  }, [])

  // Get latest data point
  const latestData = data.length > 0 ? data[data.length - 1] : null

  return {
    data,
    latestData,
    isConnected,
    isConnecting,
    error,
    reconnectAttempts,
    clearData,
    addManualData,
    subscribe,
    unsubscribe,
  }
}