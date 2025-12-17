import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

// WebSocket context type
interface WebSocketContextType {
  // Connection
  connect: () => void
  disconnect: () => void
  reconnect: () => void

  // Status
  isConnected: boolean
  isConnecting: boolean
  connectionStatus: ConnectionStatus
  lastError: Error | null

  // Subscriptions
  subscribe: (channel: string, callback: (data: any) => void) => string
  unsubscribe: (channel: string, subscriptionId: string) => void
  unsubscribeAll: (channel?: string) => void

  // Messaging
  send: (channel: string, data: any) => void
  sendRaw: (data: any) => void

  // Authentication
  authenticate: (token: string) => void
  isAuthenticated: boolean

  // Statistics
  getStats: () => WebSocketStats
}

// Connection status
export interface ConnectionStatus {
  state: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'
  lastConnected: Date | null
  lastDisconnected: Date | null
  reconnectAttempts: number
  maxReconnectAttempts: number
  reconnectInterval: number
}

// WebSocket statistics
export interface WebSocketStats {
  connectedAt: Date | null
  messagesReceived: number
  messagesSent: number
  bytesReceived: number
  bytesSent: number
  subscriptionsCount: number
  averageLatency: number
  lastPingTime: number
}

// Subscription info
interface Subscription {
  id: string
  channel: string
  callback: (data: any) => void
  createdAt: Date
  lastMessageAt?: Date
  messageCount: number
}

// Context
const WebSocketContext = createContext<WebSocketContextType | null>(null)

// WebSocket provider props
interface WebSocketProviderProps {
  children: React.ReactNode
  url?: string
  protocols?: string | string[]
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  authenticationToken?: string
  enableCompression?: boolean
  binaryType?: BinaryType
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Error) => void
  onMessage?: (event: MessageEvent) => void
}

// WebSocket provider component
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  url,
  protocols,
  autoConnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  heartbeatInterval = 30000,
  authenticationToken,
  enableCompression = true,
  binaryType = 'blob',
  onConnect,
  onDisconnect,
  onError,
  onMessage
}) => {
  const wsRef = useRef<WebSocket | null>(null)
  const subscriptionsRef = useRef<Map<string, Subscription>>(new Map())
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const pingStartTimeRef = useRef<number>(0)

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastError, setLastError] = useState<Error | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    state: 'disconnected',
    lastConnected: null,
    lastDisconnected: null,
    reconnectAttempts: 0,
    maxReconnectAttempts,
    reconnectInterval
  })
  const [stats, setStats] = useState<WebSocketStats>({
    connectedAt: null,
    messagesReceived: 0,
    messagesSent: 0,
    bytesReceived: 0,
    bytesSent: 0,
    subscriptionsCount: 0,
    averageLatency: 0,
    lastPingTime: 0
  })

  // Generate subscription ID
  const generateSubscriptionId = () => {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return
    }

    setIsConnecting(true)
    setLastError(null)
    setConnectionStatus(prev => ({
      ...prev,
      state: 'connecting'
    }))

    try {
      const wsUrl = url || process.env.REACT_APP_WS_URL || 'ws://localhost:3004/ws'
      wsRef.current = new WebSocket(wsUrl, protocols)

      // Configure WebSocket
      if (enableCompression) {
        // Note: WebSocket compression is typically configured at the server level
      }
      wsRef.current.binaryType = binaryType

      // Event handlers
      wsRef.current.onopen = (event) => {
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionStatus(prev => ({
          ...prev,
          state: 'connected',
          lastConnected: new Date(),
          reconnectAttempts: 0
        }))
        setStats(prev => ({
          ...prev,
          connectedAt: new Date()
        }))

        // Send authentication if token provided
        if (authenticationToken) {
          authenticate(authenticationToken)
        }

        // Start heartbeat
        startHeartbeat()

        // Resubscribe to all channels
        resubscribeAll()

        onConnect?.()
      }

      wsRef.current.onclose = (event) => {
        setIsConnected(false)
        setIsConnecting(false)
        setConnectionStatus(prev => ({
          ...prev,
          state: 'disconnected',
          lastDisconnected: new Date()
        }))

        stopHeartbeat()
        onDisconnect?.()

        // Auto-reconnect
        if (connectionStatus.reconnectAttempts < maxReconnectAttempts && event.code !== 1000) {
          setConnectionStatus(prev => ({
            ...prev,
            state: 'reconnecting',
            reconnectAttempts: prev.reconnectAttempts + 1
          }))

          reconnectTimerRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (event) => {
        const error = new Error(`WebSocket error: ${event}`)
        setLastError(error)
        onError?.(error)

        setConnectionStatus(prev => ({
          ...prev,
          state: 'error'
        }))
      }

      wsRef.current.onmessage = (event) => {
        // Update stats
        setStats(prev => ({
          ...prev,
          messagesReceived: prev.messagesReceived + 1,
          bytesReceived: prev.bytesReceived + (event.data as string).length
        }))

        // Handle pong response
        if (event.data === 'pong') {
          const latency = Date.now() - pingStartTimeRef.current
          setStats(prev => ({
            ...prev,
            lastPingTime: latency,
            averageLatency: (prev.averageLatency + latency) / 2
          }))
          return
        }

        // Parse message
        let data
        try {
          data = JSON.parse(event.data as string)
        } catch {
          data = event.data
        }

        // Route message to subscribers
        if (data && data.channel) {
          const channelSubscriptions = Array.from(subscriptionsRef.current.values())
            .filter(sub => sub.channel === data.channel)

          channelSubscriptions.forEach(subscription => {
            subscription.callback(data.data)
            subscription.lastMessageAt = new Date()
            subscription.messageCount++
          })
        }

        onMessage?.(event)
      }
    } catch (error) {
      setLastError(error instanceof Error ? error : new Error('Failed to create WebSocket'))
      setIsConnecting(false)
    }
  }, [url, protocols, enableCompression, binaryType, authenticationToken, connectionStatus.reconnectAttempts, maxReconnectAttempts, reconnectInterval, onConnect, onDisconnect, onError, onMessage])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    stopHeartbeat()

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
    setConnectionStatus(prev => ({
      ...prev,
      state: 'disconnected'
    }))
  }, [])

  // Reconnect to WebSocket
  const reconnect = useCallback(() => {
    disconnect()
    setTimeout(connect, 100)
  }, [disconnect, connect])

  // Subscribe to channel
  const subscribe = useCallback((channel: string, callback: (data: any) => void): string => {
    const subscriptionId = generateSubscriptionId()
    const subscription: Subscription = {
      id: subscriptionId,
      channel,
      callback,
      createdAt: new Date()
    }

    subscriptionsRef.current.set(subscriptionId, subscription)

    // Send subscription message if connected
    if (isConnected) {
      send('subscribe', { channel })
    }

    // Update stats
    setStats(prev => ({
      ...prev,
      subscriptionsCount: subscriptionsRef.current.size
    }))

    return subscriptionId
  }, [isConnected])

  // Unsubscribe from channel
  const unsubscribe = useCallback((channel: string, subscriptionId: string) => {
    const subscription = subscriptionsRef.current.get(subscriptionId)
    if (subscription && subscription.channel === channel) {
      subscriptionsRef.current.delete(subscriptionId)

      // Send unsubscribe message if connected
      if (isConnected) {
        send('unsubscribe', { channel })
      }

      // Update stats
      setStats(prev => ({
        ...prev,
        subscriptionsCount: subscriptionsRef.current.size
      }))
    }
  }, [isConnected])

  // Unsubscribe from all subscriptions
  const unsubscribeAll = useCallback((channel?: string) => {
    if (channel) {
      // Unsubscribe from specific channel
      const toRemove = Array.from(subscriptionsRef.current.values())
        .filter(sub => sub.channel === channel)

      toRemove.forEach(sub => {
        subscriptionsRef.current.delete(sub.id)
        if (isConnected) {
          send('unsubscribe', { channel })
        }
      })
    } else {
      // Unsubscribe from all
      subscriptionsRef.current.clear()
    }

    // Update stats
    setStats(prev => ({
      ...prev,
      subscriptionsCount: subscriptionsRef.current.size
    }))
  }, [isConnected])

  // Send message
  const send = useCallback((channel: string, data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ channel, data })
      wsRef.current.send(message)

      // Update stats
      setStats(prev => ({
        ...prev,
        messagesSent: prev.messagesSent + 1,
        bytesSent: prev.bytesSent + message.length
      }))
    }
  }, [])

  // Send raw message
  const sendRaw = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      wsRef.current.send(message)

      // Update stats
      setStats(prev => ({
        ...prev,
        messagesSent: prev.messagesSent + 1,
        bytesSent: prev.bytesSent + message.length
      }))
    }
  }, [])

  // Authenticate
  const authenticate = useCallback((token: string) => {
    send('auth', { token })
    setIsAuthenticated(true)
  }, [send])

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    stopHeartbeat()

    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        pingStartTimeRef.current = Date.now()
        wsRef.current.send('ping')
      }
    }, heartbeatInterval)
  }, [heartbeatInterval])

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current)
      heartbeatTimerRef.current = null
    }
  }, [])

  // Resubscribe to all channels
  const resubscribeAll = useCallback(() => {
    const channels = new Set<string>()
    Array.from(subscriptionsRef.current.values()).forEach(sub => {
      channels.add(sub.channel)
    })

    channels.forEach(channel => {
      send('subscribe', { channel })
    })
  }, [send])

  // Get statistics
  const getStats = useCallback((): WebSocketStats => {
    return { ...stats }
  }, [stats])

  // Auto-connect
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  // Context value
  const contextValue: WebSocketContextType = {
    connect,
    disconnect,
    reconnect,
    isConnected,
    isConnecting,
    connectionStatus,
    lastError,
    subscribe,
    unsubscribe,
    unsubscribeAll,
    send,
    sendRaw,
    authenticate,
    isAuthenticated,
    getStats
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  )
}

// Hook to use WebSocket context
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider')
  }
  return context
}

// Hook for subscribing to WebSocket channels
export const useWebSocketSubscription = (
  channel: string,
  callback: (data: any) => void,
  deps: React.DependencyList = []
) => {
  const { subscribe, unsubscribe } = useWebSocketContext()
  const subscriptionIdRef = useRef<string | null>(null)

  useEffect(() => {
    subscriptionIdRef.current = subscribe(channel, callback)

    return () => {
      if (subscriptionIdRef.current) {
        unsubscribe(channel, subscriptionIdRef.current)
      }
    }
  }, deps)

  return subscriptionIdRef.current
}

export default WebSocketProvider