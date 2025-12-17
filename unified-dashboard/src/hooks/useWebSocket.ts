/**
 * WebSocket Hook
 * Provides a convenient way to use WebSocket functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { wsService, MarketWS, StrategyWS, NotificationWS } from '../api/services/websocket'
import { MarketPrice, TradeData, OrderBookUpdate, StrategyUpdate } from '../types/market'
// Using local Notification type defined in uiSlice.ts

// Hook return type
interface UseWebSocketReturn {
  isConnected: boolean
  error: Error | null
  subscribe: <T = any>(channel: string, callback: (data: T) => void) => void
  unsubscribe: (channel: string, callback?: (data: any) => void) => void
  send: (data: any) => void
}

/**
 * Main WebSocket hook
 */
export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const callbacksRef = useRef(new Map<string, Set<Function>>())

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect()
      .then(() => {
        setIsConnected(true)
        setError(null)
      })
      .catch((err) => {
        setIsConnected(false)
        setError(err)
      })

    // Set up event listeners
    const handleOpen = () => {
      setIsConnected(true)
      setError(null)
    }

    const handleClose = () => {
      setIsConnected(false)
    }

    const handleError = (err: Error) => {
      setIsConnected(false)
      setError(err)
    }

    wsService.on('open', handleOpen)
    wsService.on('close', handleClose)
    wsService.on('error', handleError)

    // Cleanup
    return () => {
      wsService.off('open', handleOpen)
      wsService.off('close', handleClose)
      wsService.off('error', handleError)

      // Unsubscribe all channels
      callbacksRef.current.forEach((callbacks, channel) => {
        callbacks.forEach((callback) => {
          wsService.unsubscribe(channel, callback as any)
        })
      })
      callbacksRef.current.clear()
    }
  }, [])

  const subscribe = useCallback(<T = any>(channel: string, callback: (data: T) => void) => {
    wsService.subscribe(channel, callback)

    // Store callback for cleanup
    if (!callbacksRef.current.has(channel)) {
      callbacksRef.current.set(channel, new Set())
    }
    callbacksRef.current.get(channel)!.add(callback)
  }, [])

  const unsubscribe = useCallback((channel: string, callback?: (data: any) => void) => {
    wsService.unsubscribe(channel, callback)

    // Remove from stored callbacks
    if (callback && callbacksRef.current.has(channel)) {
      callbacksRef.current.get(channel)!.delete(callback)
      if (callbacksRef.current.get(channel)!.size === 0) {
        callbacksRef.current.delete(channel)
      }
    }
  }, [])

  const send = useCallback((data: any) => {
    wsService.send(data)
  }, [])

  return {
    isConnected,
    error,
    subscribe,
    unsubscribe,
    send,
  }
}

/**
 * Market data WebSocket hook
 */
export function useMarketData() {
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  const subscribePrices = useCallback((
    symbols: string[],
    callback: (prices: MarketPrice[]) => void
  ) => {
    MarketWS.subscribePrices(symbols, callback)
  }, [])

  const subscribeTrades = useCallback((
    symbol: string,
    callback: (trade: TradeData) => void
  ) => {
    MarketWS.subscribeTrades(symbol, callback)
  }, [])

  const subscribeDepth = useCallback((
    symbol: string,
    callback: (depth: OrderBookUpdate) => void
  ) => {
    MarketWS.subscribeDepth(symbol, callback)
  }, [])

  const unsubscribePrices = useCallback((symbols?: string[]) => {
    MarketWS.unsubscribePrices(symbols)
  }, [])

  const unsubscribeTrades = useCallback((symbol: string) => {
    MarketWS.unsubscribeTrades(symbol)
  }, [])

  const unsubscribeDepth = useCallback((symbol: string) => {
    MarketWS.unsubscribeDepth(symbol)
  }, [])

  return {
    isConnected,
    subscribePrices,
    subscribeTrades,
    subscribeDepth,
    unsubscribePrices,
    unsubscribeTrades,
    unsubscribeDepth,
  }
}

/**
 * Strategy WebSocket hook
 */
export function useStrategyWebSocket() {
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  const subscribeStrategyUpdates = useCallback((
    callback: (update: StrategyUpdate) => void
  ) => {
    StrategyWS.subscribeStrategyUpdates(callback)
  }, [])

  const subscribeStrategy = useCallback((
    strategyId: string,
    callback: (update: StrategyUpdate) => void
  ) => {
    StrategyWS.subscribeStrategy(strategyId, callback)
  }, [])

  const unsubscribeStrategyUpdates = useCallback(() => {
    StrategyWS.unsubscribeStrategyUpdates()
  }, [])

  const unsubscribeStrategy = useCallback((strategyId: string) => {
    StrategyWS.unsubscribeStrategy(strategyId)
  }, [])

  return {
    isConnected,
    subscribeStrategyUpdates,
    subscribeStrategy,
    unsubscribeStrategyUpdates,
    unsubscribeStrategy,
  }
}

/**
 * Notification WebSocket hook
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  useEffect(() => {
    if (isConnected) {
      NotificationWS.subscribe((notification: Notification) => {
        setNotifications((prev) => [notification, ...prev.slice(0, 99)]) // Keep last 100

        // Show browser notification if permission granted
        if (Notification.permission === 'granted') {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/favicon.ico',
          })
        }
      })
    }

    return () => {
      NotificationWS.unsubscribe()
    }
  }, [isConnected, subscribe, unsubscribe])

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  }
}

/**
 * Real-time data hook with automatic reconnection
 */
export function useRealTimeData<T = any>(
  channel: string,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const { subscribe, unsubscribe, isConnected, error } = useWebSocket()

  useEffect(() => {
    if (isConnected && channel) {
      const handler = (newData: T) => {
        setData(newData)
        setLastUpdate(new Date())
      }

      subscribe(channel, handler)

      return () => {
        unsubscribe(channel, handler)
      }
    }
  }, [isConnected, channel, subscribe, unsubscribe, ...dependencies])

  return {
    data,
    lastUpdate,
    isConnected,
    error,
  }
}

/**
 * WebSocket message history hook
 */
export function useWebSocketHistory(channel: string, maxMessages: number = 100) {
  const [messages, setMessages] = useState<any[]>([])
  const { subscribe, unsubscribe } = useWebSocket()

  useEffect(() => {
    if (channel) {
      const handler = (message: any) => {
        setMessages((prev) => {
          const newMessages = [message, ...prev]
          return newMessages.slice(0, maxMessages)
        })
      }

      subscribe(channel, handler)

      return () => {
        unsubscribe(channel, handler)
      }
    }
  }, [channel, subscribe, unsubscribe, maxMessages])

  const clearHistory = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    clearHistory,
  }
}

/**
 * Debounced WebSocket messages hook
 */
export function useDebouncedWebSocket<T = any>(
  channel: string,
  delay: number = 300
) {
  const [data, setData] = useState<T | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()
  const { subscribe, unsubscribe } = useWebSocket()

  useEffect(() => {
    if (channel) {
      const handler = (newData: T) => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }

        timeoutRef.current = setTimeout(() => {
          setData(newData)
        }, delay)
      }

      subscribe(channel, handler)

      return () => {
        unsubscribe(channel, handler)
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }
      }
    }
  }, [channel, subscribe, unsubscribe, delay])

  return data
}