import React, { createContext, useContext, useRef, useEffect, useCallback, useState } from 'react'
import { useWebSocket } from '../../../hooks/useWebSocket'

// Data buffer for managing streaming data
interface DataBuffer<T> {
  data: T[]
  maxSize: number
  subscribers: Set<string>
  lastUpdate: Date
}

// Streaming data provider context
interface StreamingDataContextType {
  // Subscribe to a data stream
  subscribe: <T>(
    key: string,
    callback: (data: T) => void,
    bufferSize?: number
  ) => string

  // Unsubscribe from a data stream
  unsubscribe: (key: string, subscriberId: string) => void

  // Get latest data
  getLatestData: <T>(key: string) => T | null

  // Get historical data
  getHistoricalData: <T>(key: string, limit?: number) => T[]

  // Clear buffer
  clearBuffer: (key: string) => void

  // Get buffer info
  getBufferInfo: (key: string) => {
    size: number
    maxSize: number
    lastUpdate: Date | null
    subscriberCount: number
  } | null
}

const StreamingDataContext = createContext<StreamingDataContextType>({
  subscribe: () => '',
  unsubscribe: () => {},
  getLatestData: () => null,
  getHistoricalData: () => [],
  clearBuffer: () => {},
  getBufferInfo: () => null
})

// Streaming data provider props
interface StreamingDataProviderProps {
  children: React.ReactNode
  bufferSize?: number
  enableCompression?: boolean
  enableDeduplication?: boolean
  throttleInterval?: number
}

// Streaming data provider component
export const StreamingDataProvider: React.FC<StreamingDataProviderProps> = ({
  children,
  bufferSize = 1000,
  enableCompression = false,
  enableDeduplication = true,
  throttleInterval = 100
}) => {
  const { isConnected, subscribe, unsubscribe: wsUnsubscribe } = useWebSocket()
  const buffersRef = useRef<Map<string, DataBuffer<any>>>(new Map())
  const subscribersRef = useRef<Map<string, { key: string; callback: any }>>(new Map())
  const [stats, setStats] = useState({
    totalBuffers: 0,
    totalSubscribers: 0,
    totalMessages: 0
  })

  // Throttled update function
  const throttledUpdate = useRef<Map<string, any>>(new Map())

  // Process incoming data
  const processData = useCallback((key: string, data: any) => {
    if (!buffersRef.current.has(key)) {
      return
    }

    const buffer = buffersRef.current.get(key)!

    // Deduplication
    if (enableDeduplication) {
      const lastData = buffer.data[buffer.data.length - 1]
      if (lastData && JSON.stringify(lastData) === JSON.stringify(data)) {
        return
      }
    }

    // Add new data
    buffer.data.push(data)
    buffer.lastUpdate = new Date()

    // Maintain buffer size
    if (buffer.data.length > buffer.maxSize) {
      buffer.data.shift()
    }

    // Notify all subscribers
    buffer.subscribers.forEach(subscriberId => {
      const subscriber = subscribersRef.current.get(subscriberId)
      if (subscriber && subscriber.callback) {
        // Throttle updates for performance
        if (throttleInterval > 0) {
          if (!throttledUpdate.current.has(subscriberId)) {
            throttledUpdate.current.set(subscriberId, data)
            setTimeout(() => {
              const subscriberData = throttledUpdate.current.get(subscriberId)
              if (subscriberData) {
                subscriber.callback(subscriberData)
                throttledUpdate.current.delete(subscriberId)
              }
            }, throttleInterval)
          }
        } else {
          subscriber.callback(data)
        }
      }
    })

    // Update stats
    setStats(prev => ({
      ...prev,
      totalMessages: prev.totalMessages + 1
    }))
  }, [enableDeduplication, throttleInterval])

  // Subscribe to WebSocket channels for various data types
  useEffect(() => {
    if (!isConnected) return

    // Subscribe to market data channels
    const marketDataHandler = (data: any) => {
      if (data.symbol && data.price) {
        processData(`price-${data.symbol}`, {
          symbol: data.symbol,
          price: data.price,
          volume: data.volume,
          timestamp: data.timestamp || Date.now(),
          change: data.change,
          changePercent: data.changePercent
        })
      }
    }

    // Subscribe to technical indicator channels
    const indicatorHandler = (data: any) => {
      if (data.symbol && data.indicator) {
        processData(`indicator-${data.symbol}-${data.indicator}`, {
          symbol: data.symbol,
          indicator: data.indicator,
          value: data.value,
          timestamp: data.timestamp || Date.now(),
          parameters: data.parameters
        })
      }
    }

    // Subscribe to order book channels
    const orderBookHandler = (data: any) => {
      if (data.symbol && data.bids && data.asks) {
        processData(`orderbook-${data.symbol}`, {
          symbol: data.symbol,
          bids: data.bids,
          asks: data.asks,
          timestamp: data.timestamp || Date.now(),
          spread: data.spread
        })
      }
    }

    // Subscribe to trade channels
    const tradeHandler = (data: any) => {
      if (data.symbol && data.price && data.size) {
        processData(`trades-${data.symbol}`, {
          symbol: data.symbol,
          price: data.price,
          size: data.size,
          side: data.side,
          timestamp: data.timestamp || Date.now(),
          tradeId: data.tradeId
        })
      }
    }

    // Subscribe to channels
    subscribe('market.data', marketDataHandler)
    subscribe('indicator.data', indicatorHandler)
    subscribe('orderbook.data', orderBookHandler)
    subscribe('trade.data', tradeHandler)

    return () => {
      wsUnsubscribe('market.data', marketDataHandler)
      wsUnsubscribe('indicator.data', indicatorHandler)
      wsUnsubscribe('orderbook.data', orderBookHandler)
      wsUnsubscribe('trade.data', tradeHandler)
    }
  }, [isConnected, subscribe, wsUnsubscribe, processData])

  // Subscribe to a data stream
  const subscribeToStream = useCallback(<T,>(
    key: string,
    callback: (data: T) => void,
    maxBufferSize: number = bufferSize
  ): string => {
    const subscriberId = `${key}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    // Create buffer if it doesn't exist
    if (!buffersRef.current.has(key)) {
      buffersRef.current.set(key, {
        data: [],
        maxSize: maxBufferSize,
        subscribers: new Set(),
        lastUpdate: new Date()
      })
    }

    // Add subscriber
    const buffer = buffersRef.current.get(key)!
    buffer.subscribers.add(subscriberId)
    subscribersRef.current.set(subscriberId, { key, callback })

    // Update stats
    setStats(prev => ({
      ...prev,
      totalBuffers: buffersRef.current.size,
      totalSubscribers: prev.totalSubscribers + 1
    }))

    return subscriberId
  }, [bufferSize])

  // Unsubscribe from a data stream
  const unsubscribeFromStream = useCallback((key: string, subscriberId: string) => {
    const buffer = buffersRef.current.get(key)
    if (buffer) {
      buffer.subscribers.delete(subscriberId)

      // Clean up buffer if no subscribers
      if (buffer.subscribers.size === 0) {
        buffersRef.current.delete(key)
      }
    }

    subscribersRef.current.delete(subscriberId)

    // Update stats
    setStats(prev => ({
      ...prev,
      totalBuffers: buffersRef.current.size,
      totalSubscribers: Math.max(0, prev.totalSubscribers - 1)
    }))
  }, [])

  // Get latest data
  const getLatestData = useCallback(<T,>(key: string): T | null => {
    const buffer = buffersRef.current.get(key)
    if (buffer && buffer.data.length > 0) {
      return buffer.data[buffer.data.length - 1]
    }
    return null
  }, [])

  // Get historical data
  const getHistoricalData = useCallback(<T,>(key: string, limit?: number): T[] => {
    const buffer = buffersRef.current.get(key)
    if (buffer) {
      return limit ? buffer.data.slice(-limit) : [...buffer.data]
    }
    return []
  }, [])

  // Clear buffer
  const clearBuffer = useCallback((key: string) => {
    const buffer = buffersRef.current.get(key)
    if (buffer) {
      buffer.data = []
      buffer.lastUpdate = new Date()
    }
  }, [])

  // Get buffer info
  const getBufferInfo = useCallback((key: string) => {
    const buffer = buffersRef.current.get(key)
    if (buffer) {
      return {
        size: buffer.data.length,
        maxSize: buffer.maxSize,
        lastUpdate: buffer.lastUpdate,
        subscriberCount: buffer.subscribers.size
      }
    }
    return null
  }, [])

  // Context value
  const contextValue: StreamingDataContextType = {
    subscribe: subscribeToStream,
    unsubscribe: unsubscribeFromStream,
    getLatestData,
    getHistoricalData,
    clearBuffer,
    getBufferInfo
  }

  return (
    <StreamingDataContext.Provider value={contextValue}>
      {children}
      {/* Debug info - remove in production */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 right-4 bg-black bg-opacity-75 text-white p-2 rounded text-xs">
          <div>Buffers: {stats.totalBuffers}</div>
          <div>Subscribers: {stats.totalSubscribers}</div>
          <div>Messages: {stats.totalMessages}</div>
        </div>
      )}
    </StreamingDataContext.Provider>
  )
}

// Hook to use streaming data provider
export const useStreamingData = () => {
  const context = useContext(StreamingDataContext)
  if (!context) {
    throw new Error('useStreamingData must be used within StreamingDataProvider')
  }
  return context
}

// Hook to subscribe to specific data stream
export const useDataStream = <T,>(
  key: string,
  callback: (data: T) => void,
  bufferSize?: number
) => {
  const { subscribe, unsubscribe } = useStreamingData()
  const subscriberIdRef = useRef<string | null>(null)

  useEffect(() => {
    subscriberIdRef.current = subscribe(key, callback, bufferSize)

    return () => {
      if (subscriberIdRef.current) {
        unsubscribe(key, subscriberIdRef.current)
      }
    }
  }, [key, callback, bufferSize, subscribe, unsubscribe])
}

// Hook to get latest data
export const useLatestData = <T,>(key: string) => {
  const { getLatestData } = useStreamingData()
  const [data, setData] = useState<T | null>(null)

  useEffect(() => {
    setData(getLatestData<T>(key))
  }, [key, getLatestData])

  // Set up subscription to auto-update
  useDataStream(key, (newData: T) => {
    setData(newData)
  })

  return data
}

export default StreamingDataProvider