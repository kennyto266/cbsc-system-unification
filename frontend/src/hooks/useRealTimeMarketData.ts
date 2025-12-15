import { useState, useEffect, useCallback } from 'react'
import { ChannelType } from '../types/websocket'
import { useWebSocketService } from './useWebSocketService'

interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: string
  timestamp: string
}

interface UseRealTimeMarketDataOptions {
  symbols?: string[]
  autoSubscribe?: boolean
  onUpdate?: (data: MarketData) => void
}

interface UseRealTimeMarketDataReturn {
  data: Map<string, MarketData>
  isConnected: boolean
  lastUpdate: number
  subscribe: (symbols: string[]) => void
  unsubscribe: (symbols: string[]) => void
  refresh: () => void
}

export const useRealTimeMarketData = ({
  symbols = [],
  autoSubscribe = true,
  onUpdate
}: UseRealTimeMarketDataOptions = {}): UseRealTimeMarketDataReturn => {
  const [data, setData] = useState<Map<string, MarketData>>(new Map())
  const [lastUpdate, setLastUpdate] = useState(0)

  const { isConnected, subscribe, send } = useWebSocketService({
    autoConnect: true,
    channels: autoSubscribe ? [ChannelType.PRICE_FEEDS] : []
  })

  // Subscribe to symbols
  const subscribeToSymbols = useCallback((symbolsToSubscribe: string[]) => {
    if (isConnected && symbolsToSubscribe.length > 0) {
      send('subscribe_symbols', { symbols: symbolsToSubscribe })
    }
  }, [isConnected, send])

  // Unsubscribe from symbols
  const unsubscribeFromSymbols = useCallback((symbolsToUnsubscribe: string[]) => {
    if (isConnected && symbolsToUnsubscribe.length > 0) {
      send('unsubscribe_symbols', { symbols: symbolsToUnsubscribe })
    }
  }, [isConnected, send])

  // Handle price updates
  useEffect(() => {
    const unsubscribe = subscribe(ChannelType.PRICE_FEEDS, (marketData: any) => {
      if (marketData && marketData.symbol) {
        const newData: MarketData = {
          symbol: marketData.symbol,
          price: marketData.price,
          change: marketData.change || 0,
          changePercent: marketData.changePercent || 0,
          volume: marketData.volume || '0',
          timestamp: marketData.timestamp || new Date().toISOString()
        }

        setData(prevData => {
          const updated = new Map(prevData)
          updated.set(marketData.symbol, newData)
          return updated
        })

        setLastUpdate(Date.now())
        onUpdate?.(newData)
      }
    })

    return unsubscribe
  }, [subscribe, onUpdate])

  // Auto-subscribe to initial symbols
  useEffect(() => {
    if (autoSubscribe && symbols.length > 0 && isConnected) {
      subscribeToSymbols(symbols)
    }
  }, [autoSubscribe, symbols, isConnected, subscribeToSymbols])

  // Refresh data
  const refresh = useCallback(() => {
    const currentSymbols = Array.from(data.keys())
    if (currentSymbols.length > 0) {
      subscribeToSymbols(currentSymbols)
    }
  }, [data, subscribeToSymbols])

  return {
    data,
    isConnected,
    lastUpdate,
    subscribe: subscribeToSymbols,
    unsubscribe: unsubscribeFromSymbols,
    refresh
  }
}