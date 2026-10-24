import React, { createContext, useContext, useReducer, useEffect, useRef } from 'react'
import { StreamingDataProvider, useDataStream } from '../components/charts/RealTime/StreamingDataProvider'
import { useWebSocket } from '../hooks/useWebSocket'
import { IndicatorType } from '../types/technical-indicators'
import { ChartDataPoint } from '../components/charts/RealTime/RealTimeChartProvider'

// Real-time data context type
interface RealTimeDataContextType {
  // Market data
  subscribeToMarketData: (symbol: string, callback: (data: MarketData) => void) => () => void
  getMarketData: (symbol: string) => MarketData | null
  getHistoricalData: (symbol: string, from: Date, to: Date) => ChartDataPoint[]

  // Technical indicators
  subscribeToIndicators: (
    symbol: string,
    indicators: IndicatorType[],
    callback: (data: IndicatorData) => void
  ) => () => void
  getIndicators: (symbol: string, types: IndicatorType[]) => Map<IndicatorType, number>

  // Order book
  subscribeToOrderBook: (symbol: string, callback: (data: OrderBook) => void) => () => void
  getOrderBook: (symbol: string) => OrderBook | null

  // Trades
  subscribeToTrades: (symbol: string, callback: (data: Trade[]) => void) => () => void
  getRecentTrades: (symbol: string, limit?: number) => Trade[]

  // Status
  getConnectionStatus: () => ConnectionStatus
}

// Data types
export interface MarketData {
  symbol: string
  price: number
  bid: number
  ask: number
  volume: number
  high: number
  low: number
  open: number
  close: number
  change: number
  changePercent: number
  timestamp: Date
}

export interface IndicatorData {
  symbol: string
  type: IndicatorType
  value: number
  values?: number[]
  timestamp: Date
  parameters?: Record<string, any>
}

export interface OrderBookLevel {
  price: number
  size: number
  orders: number
}

export interface OrderBook {
  symbol: string
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
  spread: number
  timestamp: Date
}

export interface Trade {
  id: string
  symbol: string
  price: number
  size: number
  side: 'buy' | 'sell'
  timestamp: Date
}

export interface ConnectionStatus {
  connected: boolean
  connecting: boolean
  error: string | null
  lastConnected: Date | null
  reconnectAttempts: number
}

// Context
const RealTimeDataContext = createContext<RealTimeDataContextType | null>(null)

// Reducer for managing state
type ActionType =
  | { type: 'SET_MARKET_DATA'; payload: MarketData }
  | { type: 'SET_INDICATORS'; payload: IndicatorData }
  | { type: 'SET_ORDER_BOOK'; payload: OrderBook }
  | { type: 'ADD_TRADES'; payload: { symbol: string; trades: Trade[] } }
  | { type: 'SET_CONNECTION_STATUS'; payload: Partial<ConnectionStatus> }
  | { type: 'CLEAR_SYMBOL_DATA'; payload: string }

interface State {
  marketData: Map<string, MarketData>
  indicators: Map<string, Map<IndicatorType, IndicatorData>>
  orderBooks: Map<string, OrderBook>
  trades: Map<string, Trade[]>
  connectionStatus: ConnectionStatus
  historicalData: Map<string, ChartDataPoint[]>
}

const initialState: State = {
  marketData: new Map(),
  indicators: new Map(),
  orderBooks: new Map(),
  trades: new Map(),
  connectionStatus: {
    connected: false,
    connecting: false,
    error: null,
    lastConnected: null,
    reconnectAttempts: 0
  },
  historicalData: new Map()
}

const reducer = (state: State, action: ActionType): State => {
  switch (action.type) {
    case 'SET_MARKET_DATA':
      return {
        ...state,
        marketData: new Map(state.marketData).set(action.payload.symbol, action.payload)
      }

    case 'SET_INDICATORS':
      const symbolIndicators = state.indicators.get(action.payload.symbol) || new Map()
      symbolIndicators.set(action.payload.type, action.payload)
      return {
        ...state,
        indicators: new Map(state.indicators).set(action.payload.symbol, symbolIndicators)
      }

    case 'SET_ORDER_BOOK':
      return {
        ...state,
        orderBooks: new Map(state.orderBooks).set(action.payload.symbol, action.payload)
      }

    case 'ADD_TRADES':
      const existingTrades = state.trades.get(action.payload.symbol) || []
      const newTrades = [...existingTrades, ...action.payload.trades].slice(-1000) // Keep last 1000 trades
      return {
        ...state,
        trades: new Map(state.trades).set(action.payload.symbol, newTrades)
      }

    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: { ...state.connectionStatus, ...action.payload }
      }

    case 'CLEAR_SYMBOL_DATA':
      const newMarketData = new Map(state.marketData)
      const newIndicators = new Map(state.indicators)
      const newOrderBooks = new Map(state.orderBooks)
      const newTrades = new Map(state.trades)

      newMarketData.delete(action.payload)
      newIndicators.delete(action.payload)
      newOrderBooks.delete(action.payload)
      newTrades.delete(action.payload)

      return {
        ...state,
        marketData: newMarketData,
        indicators: newIndicators,
        orderBooks: newOrderBooks,
        trades: newTrades
      }

    default:
      return state
  }
}

// Real-time data provider component
export const RealTimeDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState)
  const { isConnected, subscribe, unsubscribe } = useWebSocket()
  const subscribersRef = useRef<Map<string, Set<Function>>>(new Map())

  // Initialize WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return

    // Market data subscription
    const marketDataHandler = (data: any) => {
      if (data.symbol && data.price) {
        const marketData: MarketData = {
          symbol: data.symbol,
          price: data.price,
          bid: data.bid,
          ask: data.ask,
          volume: data.volume,
          high: data.high,
          low: data.low,
          open: data.open,
          close: data.close,
          change: data.change,
          changePercent: data.changePercent,
          timestamp: new Date(data.timestamp || Date.now())
        }

        dispatch({ type: 'SET_MARKET_DATA', payload: marketData })

        // Notify subscribers
        const subscribers = subscribersRef.current.get(`market-${data.symbol}`)
        if (subscribers) {
          subscribers.forEach(callback => callback(marketData))
        }
      }
    }

    // Technical indicators subscription
    const indicatorsHandler = (data: any) => {
      if (data.symbol && data.type) {
        const indicatorData: IndicatorData = {
          symbol: data.symbol,
          type: data.type,
          value: data.value,
          values: data.values,
          timestamp: new Date(data.timestamp || Date.now()),
          parameters: data.parameters
        }

        dispatch({ type: 'SET_INDICATORS', payload: indicatorData })

        // Notify subscribers
        const subscribers = subscribersRef.current.get(`indicators-${data.symbol}`)
        if (subscribers) {
          subscribers.forEach(callback => callback(indicatorData))
        }
      }
    }

    // Order book subscription
    const orderBookHandler = (data: any) => {
      if (data.symbol && data.bids && data.asks) {
        const orderBook: OrderBook = {
          symbol: data.symbol,
          bids: data.bids,
          asks: data.asks,
          spread: data.spread,
          timestamp: new Date(data.timestamp || Date.now())
        }

        dispatch({ type: 'SET_ORDER_BOOK', payload: orderBook })

        // Notify subscribers
        const subscribers = subscribersRef.current.get(`orderbook-${data.symbol}`)
        if (subscribers) {
          subscribers.forEach(callback => callback(orderBook))
        }
      }
    }

    // Trades subscription
    const tradesHandler = (data: any) => {
      if (data.symbol && data.trades) {
        const trades: Trade[] = data.trades.map((t: any) => ({
          id: t.id,
          symbol: data.symbol,
          price: t.price,
          size: t.size,
          side: t.side,
          timestamp: new Date(t.timestamp || Date.now())
        }))

        dispatch({ type: 'ADD_TRADES', payload: { symbol: data.symbol, trades } })

        // Notify subscribers
        const subscribers = subscribersRef.current.get(`trades-${data.symbol}`)
        if (subscribers) {
          subscribers.forEach(callback => callback(trades))
        }
      }
    }

    // Subscribe to WebSocket channels
    subscribe('market.data', marketDataHandler)
    subscribe('indicator.data', indicatorsHandler)
    subscribe('orderbook.data', orderBookHandler)
    subscribe('trade.data', tradesHandler)

    return () => {
      unsubscribe('market.data', marketDataHandler)
      unsubscribe('indicator.data', indicatorsHandler)
      unsubscribe('orderbook.data', orderBookHandler)
      unsubscribe('trade.data', tradesHandler)
    }
  }, [isConnected, subscribe, unsubscribe])

  // Update connection status
  useEffect(() => {
    dispatch({
      type: 'SET_CONNECTION_STATUS',
      payload: {
        connected: isConnected,
        connecting: false,
        error: null
      }
    })
  }, [isConnected])

  // Context value
  const contextValue: RealTimeDataContextType = {
    // Market data
    subscribeToMarketData: (symbol: string, callback: (data: MarketData) => void) => {
      const key = `market-${symbol}`
      if (!subscribersRef.current.has(key)) {
        subscribersRef.current.set(key, new Set())
      }
      subscribersRef.current.get(key)!.add(callback)

      // Return current data if available
      const currentData = state.marketData.get(symbol)
      if (currentData) {
        callback(currentData)
      }

      return () => {
        const subscribers = subscribersRef.current.get(key)
        if (subscribers) {
          subscribers.delete(callback)
        }
      }
    },

    getMarketData: (symbol: string) => {
      return state.marketData.get(symbol) || null
    },

    getHistoricalData: (symbol: string, from: Date, to: Date) => {
      // This would typically fetch from an API
      return state.historicalData.get(symbol) || []
    },

    // Technical indicators
    subscribeToIndicators: (
      symbol: string,
      indicators: IndicatorType[],
      callback: (data: IndicatorData) => void
    ) => {
      const key = `indicators-${symbol}`
      if (!subscribersRef.current.has(key)) {
        subscribersRef.current.set(key, new Set())
      }
      subscribersRef.current.get(key)!.add(callback)

      // Send subscription request
      subscribe(`indicators.${symbol}`, { types: indicators })

      return () => {
        const subscribers = subscribersRef.current.get(key)
        if (subscribers) {
          subscribers.delete(callback)
        }
      }
    },

    getIndicators: (symbol: string, types: IndicatorType[]) => {
      const symbolIndicators = state.indicators.get(symbol)
      if (!symbolIndicators) return new Map()

      const result = new Map<IndicatorType, number>()
      types.forEach(type => {
        const indicator = symbolIndicators.get(type)
        if (indicator) {
          result.set(type, indicator.value)
        }
      })

      return result
    },

    // Order book
    subscribeToOrderBook: (symbol: string, callback: (data: OrderBook) => void) => {
      const key = `orderbook-${symbol}`
      if (!subscribersRef.current.has(key)) {
        subscribersRef.current.set(key, new Set())
      }
      subscribersRef.current.get(key)!.add(callback)

      // Send subscription request
      subscribe(`orderbook.${symbol}`, {})

      return () => {
        const subscribers = subscribersRef.current.get(key)
        if (subscribers) {
          subscribers.delete(callback)
        }
      }
    },

    getOrderBook: (symbol: string) => {
      return state.orderBooks.get(symbol) || null
    },

    // Trades
    subscribeToTrades: (symbol: string, callback: (data: Trade[]) => void) => {
      const key = `trades-${symbol}`
      if (!subscribersRef.current.has(key)) {
        subscribersRef.current.set(key, new Set())
      }
      subscribersRef.current.get(key)!.add(callback)

      // Send subscription request
      subscribe(`trades.${symbol}`, {})

      return () => {
        const subscribers = subscribersRef.current.get(key)
        if (subscribers) {
          subscribers.delete(callback)
        }
      }
    },

    getRecentTrades: (symbol: string, limit: number = 100) => {
      const trades = state.trades.get(symbol) || []
      return trades.slice(-limit)
    },

    // Status
    getConnectionStatus: () => state.connectionStatus
  }

  return (
    <StreamingDataProvider>
      <RealTimeDataContext.Provider value={contextValue}>
        {children}
      </RealTimeDataContext.Provider>
    </StreamingDataProvider>
  )
}

// Hook to use real-time data
export const useRealTimeData = () => {
  const context = useContext(RealTimeDataContext)
  if (!context) {
    throw new Error('useRealTimeData must be used within RealTimeDataProvider')
  }
  return context
}

// Hook for market data
export const useMarketData = (symbol: string) => {
  const { subscribeToMarketData, getMarketData } = useRealTimeData()
  const [data, setData] = useState<MarketData | null>(null)

  useEffect(() => {
    const unsubscribe = subscribeToMarketData(symbol, setData)
    return unsubscribe
  }, [symbol, subscribeToMarketData])

  return data || getMarketData(symbol)
}

// Hook for technical indicators
export const useTechnicalIndicators = (symbol: string, types: IndicatorType[]) => {
  const { subscribeToIndicators, getIndicators } = useRealTimeData()
  const [indicators, setIndicators] = useState<Map<IndicatorType, number>>(new Map())

  useEffect(() => {
    const unsubscribe = subscribeToIndicators(symbol, types, (data) => {
      setIndicators(prev => new Map(prev).set(data.type, data.value))
    })

    // Set initial values
    setIndicators(getIndicators(symbol, types))

    return unsubscribe
  }, [symbol, types, subscribeToIndicators, getIndicators])

  return indicators
}

// Hook for order book
export const useOrderBook = (symbol: string) => {
  const { subscribeToOrderBook, getOrderBook } = useRealTimeData()
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null)

  useEffect(() => {
    const unsubscribe = subscribeToOrderBook(symbol, setOrderBook)
    return unsubscribe
  }, [symbol, subscribeToOrderBook])

  return orderBook || getOrderBook(symbol)
}

// Hook for recent trades
export const useRecentTrades = (symbol: string, limit: number = 100) => {
  const { subscribeToTrades, getRecentTrades } = useRealTimeData()
  const [trades, setTrades] = useState<Trade[]>([])

  useEffect(() => {
    const unsubscribe = subscribeToTrades(symbol, setTrades)
    return unsubscribe
  }, [symbol, subscribeToTrades])

  return trades.length > 0 ? trades : getRecentTrades(symbol, limit)
}

export default RealTimeDataProvider