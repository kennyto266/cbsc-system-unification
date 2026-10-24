import React, { createContext, useContext, useReducer, useEffect, useRef, useCallback } from 'react'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { IndicatorType, IndicatorCategory, TechnicalIndicator } from '../../../types/technical-indicators'

// Chart data interfaces
export interface ChartDataPoint {
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface IndicatorValue {
  id: string
  type: IndicatorType
  name: string
  value: number
  timestamp: Date
}

export interface ChartState {
  [symbol: string]: {
    [timeframe: string]: {
      data: ChartDataPoint[]
      indicators: IndicatorValue[]
      lastUpdate: Date
      subscribers: Set<string>
    }
  }
}

// Action types
type ActionType =
  | { type: 'ADD_DATA'; payload: { symbol: string; timeframe: string; data: ChartDataPoint } }
  | { type: 'ADD_INDICATOR'; payload: { symbol: string; timeframe: string; indicator: IndicatorValue } }
  | { type: 'SUBSCRIBE'; payload: { symbol: string; timeframe: string; subscriberId: string } }
  | { type: 'UNSUBSCRIBE'; payload: { symbol: string; timeframe: string; subscriberId: string } }
  | { type: 'CLEAR_DATA'; payload: { symbol: string; timeframe: string } }
  | { type: 'SET_HISTORY'; payload: { symbol: string; timeframe: string; data: ChartDataPoint[] } }

// Reducer
const chartReducer = (state: ChartState, action: ActionType): ChartState => {
  switch (action.type) {
    case 'ADD_DATA': {
      const { symbol, timeframe, data } = action.payload
      const key = `${symbol}-${timeframe}`

      if (!state[symbol]) {
        state[symbol] = {}
      }
      if (!state[symbol][timeframe]) {
        state[symbol][timeframe] = {
          data: [],
          indicators: [],
          lastUpdate: new Date(),
          subscribers: new Set()
        }
      }

      const chartData = state[symbol][timeframe]

      // Add new data point
      chartData.data.push(data)

      // Keep only last 1000 points for performance
      if (chartData.data.length > 1000) {
        chartData.data.shift()
      }

      chartData.lastUpdate = new Date()

      return { ...state }
    }

    case 'ADD_INDICATOR': {
      const { symbol, timeframe, indicator } = action.payload

      if (!state[symbol] || !state[symbol][timeframe]) {
        return state
      }

      const chartData = state[symbol][timeframe]

      // Update or add indicator value
      const existingIndex = chartData.indicators.findIndex(i => i.id === indicator.id)
      if (existingIndex >= 0) {
        chartData.indicators[existingIndex] = indicator
      } else {
        chartData.indicators.push(indicator)
      }

      // Keep only last 1000 indicator values per type
      chartData.indicators = chartData.indicators.filter(i => i.id !== indicator.id)
      chartData.indicators.push(indicator)

      return { ...state }
    }

    case 'SUBSCRIBE': {
      const { symbol, timeframe, subscriberId } = action.payload

      if (!state[symbol]) {
        state[symbol] = {}
      }
      if (!state[symbol][timeframe]) {
        state[symbol][timeframe] = {
          data: [],
          indicators: [],
          lastUpdate: new Date(),
          subscribers: new Set()
        }
      }

      state[symbol][timeframe].subscribers.add(subscriberId)

      return { ...state }
    }

    case 'UNSUBSCRIBE': {
      const { symbol, timeframe, subscriberId } = action.payload

      if (state[symbol] && state[symbol][timeframe]) {
        state[symbol][timeframe].subscribers.delete(subscriberId)

        // Clean up if no subscribers
        if (state[symbol][timeframe].subscribers.size === 0) {
          delete state[symbol][timeframe]
          if (Object.keys(state[symbol]).length === 0) {
            delete state[symbol]
          }
        }
      }

      return { ...state }
    }

    case 'CLEAR_DATA': {
      const { symbol, timeframe } = action.payload

      if (state[symbol] && state[symbol][timeframe]) {
        state[symbol][timeframe].data = []
        state[symbol][timeframe].indicators = []
        state[symbol][timeframe].lastUpdate = new Date()
      }

      return { ...state }
    }

    case 'SET_HISTORY': {
      const { symbol, timeframe, data } = action.payload

      if (!state[symbol]) {
        state[symbol] = {}
      }
      if (!state[symbol][timeframe]) {
        state[symbol][timeframe] = {
          data: [],
          indicators: [],
          lastUpdate: new Date(),
          subscribers: new Set()
        }
      }

      state[symbol][timeframe].data = data

      return { ...state }
    }

    default:
      return state
  }
}

// Context
const RealTimeChartContext = createContext<{
  state: ChartState
  subscribe: (symbol: string, timeframe: string, subscriberId: string) => void
  unsubscribe: (symbol: string, timeframe: string, subscriberId: string) => void
  getData: (symbol: string, timeframe: string) => ChartDataPoint[] | null
  getIndicators: (symbol: string, timeframe: string) => IndicatorValue[] | null
  clearData: (symbol: string, timeframe: string) => void
  setHistory: (symbol: string, timeframe: string, data: ChartDataPoint[]) => void
}>({
  state: {},
  subscribe: () => {},
  unsubscribe: () => {},
  getData: () => null,
  getIndicators: () => null,
  clearData: () => {},
  setHistory: () => {}
})

// Provider component
export const RealTimeChartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(chartReducer, {})
  const { isConnected, subscribe, unsubscribe: wsUnsubscribe } = useWebSocket()
  const wsSubscriptionsRef = useRef(new Set<string>())
  const subscribersRef = useRef(new Set<string>())

  // Subscribe to WebSocket for real-time data
  useEffect(() => {
    if (!isConnected) return

    // Get all unique symbol-timeframe pairs
    const pairs = new Set<string>()
    Object.entries(state).forEach(([symbol, timeframes]) => {
      Object.keys(timeframes).forEach(timeframe => {
        pairs.add(`${symbol}-${timeframe}`)
      })
    })

    // Subscribe to new pairs
    pairs.forEach(pair => {
      const [symbol, timeframe] = pair.split('-')
      const channel = `chart.${symbol}.${timeframe}`

      if (!wsSubscriptionsRef.current.has(channel)) {
        wsSubscriptionsRef.current.add(channel)

        const handler = (data: any) => {
          // Handle price data
          if (data.price) {
            dispatch({
              type: 'ADD_DATA',
              payload: {
                symbol,
                timeframe,
                data: {
                  timestamp: new Date(data.timestamp),
                  open: data.open,
                  high: data.high,
                  low: data.low,
                  close: data.price,
                  volume: data.volume
                }
              }
            })
          }

          // Handle indicator data
          if (data.indicators) {
            Object.entries(data.indicators).forEach(([id, value]) => {
              dispatch({
                type: 'ADD_INDICATOR',
                payload: {
                  symbol,
                  timeframe,
                  indicator: {
                    id,
                    type: id as IndicatorType, // Simplified
                    name: id,
                    value: value as number,
                    timestamp: new Date()
                  }
                }
              })
            })
          }
        }

        subscribe(channel, handler)
      }
    })

    // Unsubscribe from unused pairs
    wsSubscriptionsRef.current.forEach(channel => {
      const [symbol, timeframe] = channel.replace('chart.', '').split('.')
      const pair = `${symbol}-${timeframe}`

      if (!pairs.has(pair)) {
        wsSubscriptionsRef.current.delete(channel)
        wsUnsubscribe(channel, undefined)
      }
    })

    return () => {
      // Cleanup subscriptions on unmount
      wsSubscriptionsRef.current.forEach(channel => {
        wsUnsubscribe(channel, undefined)
      })
      wsSubscriptionsRef.current.clear()
    }
  }, [isConnected, state, subscribe, wsUnsubscribe])

  // Subscribe function
  const subscribeToChart = useCallback((symbol: string, timeframe: string, subscriberId: string) => {
    dispatch({
      type: 'SUBSCRIBE',
      payload: { symbol, timeframe, subscriberId }
    })

    subscribersRef.current.add(subscriberId)
  }, [])

  // Unsubscribe function
  const unsubscribeFromChart = useCallback((symbol: string, timeframe: string, subscriberId: string) => {
    dispatch({
      type: 'UNSUBSCRIBE',
      payload: { symbol, timeframe, subscriberId }
    })

    subscribersRef.current.delete(subscriberId)
  }, [])

  // Get data function
  const getChartData = useCallback((symbol: string, timeframe: string): ChartDataPoint[] | null => {
    return state[symbol]?.[timeframe]?.data || null
  }, [state])

  // Get indicators function
  const getChartIndicators = useCallback((symbol: string, timeframe: string): IndicatorValue[] | null => {
    return state[symbol]?.[timeframe]?.indicators || null
  }, [state])

  // Clear data function
  const clearChartData = useCallback((symbol: string, timeframe: string) => {
    dispatch({
      type: 'CLEAR_DATA',
      payload: { symbol, timeframe }
    })
  }, [])

  // Set history function
  const setChartHistory = useCallback((symbol: string, timeframe: string, data: ChartDataPoint[]) => {
    dispatch({
      type: 'SET_HISTORY',
      payload: { symbol, timeframe, data }
    })
  }, [])

  return (
    <RealTimeChartContext.Provider
      value={{
        state,
        subscribe: subscribeToChart,
        unsubscribe: unsubscribeFromChart,
        getData: getChartData,
        getIndicators: getChartIndicators,
        clearData: clearChartData,
        setHistory: setChartHistory
      }}
    >
      {children}
    </RealTimeChartContext.Provider>
  )
}

// Hook for using the context
export const useRealTimeChart = () => {
  const context = useContext(RealTimeChartContext)
  if (!context) {
    throw new Error('useRealTimeChart must be used within RealTimeChartProvider')
  }
  return context
}

// Hook for specific chart
export const useChart = (symbol: string, timeframe: string) => {
  const chartContext = useRealTimeChart()
  const subscriberId = useRef(`chart-${symbol}-${timeframe}-${Date.now()}`)

  // Auto-subscribe
  useEffect(() => {
    chartContext.subscribe(symbol, timeframe, subscriberId.current)

    return () => {
      chartContext.unsubscribe(symbol, timeframe, subscriberId.current)
    }
  }, [symbol, timeframe, chartContext])

  return {
    data: chartContext.getData(symbol, timeframe),
    indicators: chartContext.getIndicators(symbol, timeframe),
    clearData: () => chartContext.clearData(symbol, timeframe),
    setHistory: (data: ChartDataPoint[]) => chartContext.setHistory(symbol, timeframe, data)
  }
}

// Performance monitoring hook
export const useChartPerformance = (symbol: string, timeframe: string) => {
  const { getData } = useRealTimeChart()
  const metricsRef = useRef({
    updateCount: 0,
    lastUpdate: new Date(),
    avgUpdateInterval: 0,
    updateTimes: [] as number[]
  })

  useEffect(() => {
    const data = getData(symbol, timeframe)
    if (data && data.length > 0) {
      const now = Date.now()
      const lastPoint = data[data.length - 1]

      if (lastPoint.timestamp) {
        const updateInterval = now - lastPoint.timestamp.getTime()
        metricsRef.current.updateTimes.push(updateInterval)

        // Keep only last 100 intervals
        if (metricsRef.current.updateTimes.length > 100) {
          metricsRef.current.updateTimes.shift()
        }

        // Calculate average
        metricsRef.current.avgUpdateInterval =
          metricsRef.current.updateTimes.reduce((a, b) => a + b, 0) /
          metricsRef.current.updateTimes.length

        metricsRef.current.updateCount++
        metricsRef.current.lastUpdate = new Date()
      }
    }
  })

  return {
    updateCount: metricsRef.current.updateCount,
    lastUpdate: metricsRef.current.lastUpdate,
    avgUpdateInterval: metricsRef.current.avgUpdateInterval,
    updatesPerSecond: metricsRef.current.avgUpdateInterval > 0
      ? 1000 / metricsRef.current.avgUpdateInterval
      : 0
  }
}

export default RealTimeChartProvider