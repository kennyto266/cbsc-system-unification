import { useState, useEffect, useCallback, useRef } from 'react'
import { ChannelType, ConnectionState, ConnectionMetrics } from '../types/websocket'
import { enhancedWS } from '../services/websocket/EnhancedWebSocketService'

interface UseWebSocketServiceOptions {
  autoConnect?: boolean
  channels?: ChannelType[]
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Error) => void
}

interface UseWebSocketServiceReturn {
  isConnected: boolean
  connectionState: ConnectionState
  metrics: ConnectionMetrics
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown'
  subscribe: (channel: ChannelType, callback: (data: any) => void) => () => void
  unsubscribe: (channel: ChannelType) => void
  send: (type: string, data: any) => boolean
  getCachedData: <T>(channel: string, maxAge?: number) => T | null
  reconnect: () => Promise<void>
  disconnect: () => void
}

export const useWebSocketService = ({
  autoConnect = true,
  channels = [],
  onConnect,
  onDisconnect,
  onError
}: UseWebSocketServiceOptions = {}): UseWebSocketServiceReturn => {
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED)
  const [metrics, setMetrics] = useState<ConnectionMetrics>({
    reconnectCount: 0,
    messagesReceived: 0,
    messagesSent: 0,
    bytesReceived: 0,
    bytesSent: 0,
    errorCount: 0
  })
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor' | 'unknown'>('unknown')
  const subscriptions = useRef<Map<string, () => void>>(new Map())
  const mountedRef = useRef(true)

  // Check if connected
  const isConnected = connectionState === ConnectionState.CONNECTED

  // Subscribe to channel
  const subscribe = useCallback((channel: ChannelType, callback: (data: any) => void) => {
    const subscriptionKey = `${channel}_${Date.now()}`
    const unsubscribe = enhancedWS.subscribe(channel, callback)
    subscriptions.current.set(subscriptionKey, unsubscribe)
    return unsubscribe
  }, [])

  // Unsubscribe from channel
  const unsubscribe = useCallback((channel: ChannelType) => {
    enhancedWS.unsubscribe(channel)
  }, [])

  // Send message
  const send = useCallback((type: string, data: any) => {
    return enhancedWS.send({
      id: `msg_${Date.now()}`,
      type,
      data,
      timestamp: Date.now()
    })
  }, [])

  // Get cached data
  const getCachedData = useCallback(<T>(channel: string, maxAge?: number) => {
    return enhancedWS.getCachedData<T>(channel, maxAge)
  }, [])

  // Reconnect
  const reconnect = useCallback(async () => {
    try {
      await enhancedWS.connect()
    } catch (error) {
      console.error('Reconnection failed:', error)
    }
  }, [])

  // Disconnect
  const disconnect = useCallback(() => {
    // Clean up all subscriptions
    subscriptions.current.forEach(unsubscribe => unsubscribe())
    subscriptions.current.clear()
    enhancedWS.disconnect()
  }, [])

  // Update connection state
  useEffect(() => {
    const updateState = () => {
      if (mountedRef.current) {
        setConnectionState(enhancedWS.getConnectionState())
        setMetrics(enhancedWS.getConnectionMetrics())
        setConnectionQuality(enhancedWS.getConnectionQuality())
      }
    }

    const interval = setInterval(updateState, 1000)
    updateState()

    return () => {
      clearInterval(interval)
    }
  }, [])

  // Setup event listeners
  useEffect(() => {
    enhancedWS.addEventListener('onConnect', () => {
      onConnect?.()
    })

    enhancedWS.addEventListener('onDisconnect', () => {
      onDisconnect?.()
    })

    enhancedWS.addEventListener('onError', (error) => {
      onError?.(error as Error)
    })

    return () => {
      enhancedWS.removeEventListener('onConnect', onConnect || (() => {}))
      enhancedWS.removeEventListener('onDisconnect', onDisconnect || (() => {}))
      enhancedWS.removeEventListener('onError', onError || (() => {}))
    }
  }, [onConnect, onDisconnect, onError])

  // Auto-connect
  useEffect(() => {
    if (autoConnect && connectionState === ConnectionState.DISCONNECTED) {
      enhancedWS.connect().catch(console.error)
    }
  }, [autoConnect, connectionState])

  // Subscribe to default channels
  useEffect(() => {
    if (channels.length > 0 && isConnected) {
      channels.forEach(channel => {
        subscribe(channel, (data) => {
          console.log(`Received data from ${channel}:`, data)
        })
      })
    }
  }, [channels, isConnected, subscribe])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    connectionState,
    metrics,
    connectionQuality,
    subscribe,
    unsubscribe,
    send,
    getCachedData,
    reconnect,
    disconnect
  }
}