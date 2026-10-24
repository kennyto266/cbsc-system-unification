import { useEffect, useRef, useState, useCallback } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'

// WebSocket data hook options
export interface UseWebSocketDataOptions {
  url?: string
  channels: string[]
  reconnectInterval?: number
  maxReconnectAttempts?: number
  messageBuffer?: boolean
  bufferSize?: number
  enableCompression?: boolean
  onMessage?: (channel: string, data: any) => void
  onError?: (error: Error) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

// WebSocket data hook return value
export interface UseWebSocketDataReturn {
  isConnected: boolean
  isConnecting: boolean
  error: Error | null
  data: Map<string, any[]>
  lastMessage: Map<string, any>
  connectionAttempts: number
  connect: () => void
  disconnect: () => void
  subscribe: (channel: string, callback?: (data: any) => void) => () => void
  unsubscribe: (channel: string) => void
  sendMessage: (channel: string, data: any) => void
  clearChannelData: (channel: string) => void
  getChannelData: <T = any>(channel: string, limit?: number) => T[]
  getLatestData: <T = any>(channel: string) => T | null
  getConnectionStats: () => {
    connectedAt: Date | null
    messagesReceived: number
    messagesSent: number
    bytesReceived: number
    bytesSent: number
  }
}

// WebSocket data hook
export const useWebSocketData = (options: UseWebSocketDataOptions): UseWebSocketDataReturn => {
  const {
    channels: initialChannels = [],
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    messageBuffer = true,
    bufferSize = 1000,
    enableCompression = false,
    onMessage,
    onError,
    onConnect,
    onDisconnect
  } = options

  const wsContext = useWebSocket()
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const [data, setData] = useState<Map<string, any[]>>(new Map())
  const [lastMessage, setLastMessage] = useState<Map<string, any>>(new Map())

  // Refs for tracking
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map())
  const connectionStatsRef = useRef({
    connectedAt: null as Date | null,
    messagesReceived: 0,
    messagesSent: 0,
    bytesReceived: 0,
    bytesSent: 0
  })

  // Initialize data buffers for channels
  useEffect(() => {
    const newData = new Map(data)
    initialChannels.forEach(channel => {
      if (!newData.has(channel)) {
        newData.set(channel, [])
      }
    })
    setData(newData)
  }, [initialChannels])

  // Handle WebSocket connection
  const connect = useCallback(() => {
    if (wsContext.isConnected || isConnecting) return

    setIsConnecting(true)
    setError(null)
    setConnectionAttempts(prev => prev + 1)

    // The actual connection is handled by the useWebSocket hook
    // We just track the state here
  }, [wsContext.isConnected, isConnecting])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    // The actual disconnection is handled by the useWebSocket hook
    subscribersRef.current.clear()
  }, [])

  // Subscribe to a channel
  const subscribe = useCallback((channel: string, callback?: (data: any) => void) => {
    if (!subscribersRef.current.has(channel)) {
      subscribersRef.current.set(channel, new Set())
    }

    if (callback) {
      subscribersRef.current.get(channel)!.add(callback)
    }

    // Subscribe through WebSocket context
    wsContext.subscribe(channel, (data: any) => {
      handleChannelMessage(channel, data)
    })

    // Return unsubscribe function
    return () => {
      if (callback) {
        const subscribers = subscribersRef.current.get(channel)
        if (subscribers) {
          subscribers.delete(callback)
        }
      }
    }
  }, [wsContext])

  // Unsubscribe from a channel
  const unsubscribe = useCallback((channel: string) => {
    subscribersRef.current.delete(channel)
    wsContext.unsubscribe(channel, undefined)
  }, [wsContext])

  // Send message through WebSocket
  const sendMessage = useCallback((channel: string, data: any) => {
    const message = {
      channel,
      data,
      timestamp: Date.now()
    }

    // Update stats
    connectionStatsRef.current.messagesSent++
    connectionStatsRef.current.bytesSent += JSON.stringify(message).length

    // Send through WebSocket context
    // This would need to be implemented in the WebSocket context
    console.log('Sending message:', message)
  }, [])

  // Handle incoming channel message
  const handleChannelMessage = useCallback((channel: string, messageData: any) => {
    // Update stats
    connectionStatsRef.current.messagesReceived++
    connectionStatsRef.current.bytesReceived += JSON.stringify(messageData).length

    // Update last message
    setLastMessage(prev => {
      const newMap = new Map(prev)
      newMap.set(channel, messageData)
      return newMap
    })

    // Buffer data if enabled
    if (messageBuffer) {
      setData(prev => {
        const newData = new Map(prev)
        const channelData = newData.get(channel) || []

        // Add new data
        channelData.push({
          data: messageData,
          timestamp: new Date()
        })

        // Maintain buffer size
        if (channelData.length > bufferSize) {
          channelData.shift()
        }

        newData.set(channel, channelData)
        return newData
      })
    }

    // Notify subscribers
    const subscribers = subscribersRef.current.get(channel)
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(messageData)
        } catch (err) {
          console.error('Error in subscriber callback:', err)
        }
      })
    }

    // Notify parent
    onMessage?.(channel, messageData)
  }, [messageBuffer, bufferSize, onMessage])

  // Clear channel data
  const clearChannelData = useCallback((channel: string) => {
    setData(prev => {
      const newData = new Map(prev)
      newData.delete(channel)
      return newData
    })
  }, [])

  // Get channel data
  const getChannelData = useCallback(<T = any>(channel: string, limit?: number): T[] => {
    const channelData = data.get(channel) || []
    const processedData = channelData.map(item => item.data) as T[]

    if (limit && limit > 0) {
      return processedData.slice(-limit)
    }

    return processedData
  }, [data])

  // Get latest data from channel
  const getLatestData = useCallback(<T = any>(channel: string): T | null => {
    const channelData = data.get(channel)
    if (!channelData || channelData.length === 0) return null

    return channelData[channelData.length - 1].data as T
  }, [data])

  // Get connection statistics
  const getConnectionStats = useCallback(() => {
    return { ...connectionStatsRef.current }
  }, [])

  // Auto-subscribe to initial channels
  useEffect(() => {
    initialChannels.forEach(channel => {
      subscribe(channel)
    })

    return () => {
      initialChannels.forEach(channel => {
        unsubscribe(channel)
      })
    }
  }, [initialChannels, subscribe, unsubscribe])

  // Handle connection state changes
  useEffect(() => {
    if (wsContext.isConnected) {
      setIsConnecting(false)
      setConnectionAttempts(0)
      connectionStatsRef.current.connectedAt = new Date()
      onConnect?.()
    } else if (isConnecting) {
      // Handle connection errors
      if (connectionAttempts >= maxReconnectAttempts) {
        setError(new Error('Failed to connect after maximum attempts'))
        setIsConnecting(false)
      }
    } else {
      onDisconnect?.()
    }
  }, [wsContext.isConnected, isConnecting, connectionAttempts, maxReconnectAttempts, onConnect, onDisconnect])

  // Auto-reconnect
  useEffect(() => {
    if (!wsContext.isConnected && !isConnecting && connectionAttempts > 0 && connectionAttempts < maxReconnectAttempts) {
      const timer = setTimeout(() => {
        connect()
      }, reconnectInterval)

      return () => clearTimeout(timer)
    }
  }, [wsContext.isConnected, isConnecting, connectionAttempts, maxReconnectAttempts, reconnectInterval, connect])

  return {
    isConnected: wsContext.isConnected,
    isConnecting,
    error,
    data,
    lastMessage,
    connectionAttempts,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    clearChannelData,
    getChannelData,
    getLatestData,
    getConnectionStats
  }
}

export default useWebSocketData