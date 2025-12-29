import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { ChartDataState, DataSubscription, DataMetrics } from '../types/data.types'
import { useRealTimeData } from '../hooks/useRealTimeData'

// Context state interface
interface ChartDataContextState {
  subscriptions: Map<string, DataSubscription>
  data: Map<string, any[]>
  state: ChartDataState
  metrics: DataMetrics
  isConnected: boolean
}

// Context actions
type ChartDataContextAction =
  | { type: 'ADD_SUBSCRIPTION'; payload: DataSubscription }
  | { type: 'REMOVE_SUBSCRIPTION'; payload: string }
  | { type: 'UPDATE_SUBSCRIPTION'; payload: DataSubscription }
  | { type: 'SET_CONNECTION_STATUS'; payload: boolean }
  | { type: 'UPDATE_METRICS'; payload: DataMetrics }
  | { type: 'CLEAR_DATA'; payload?: string }
  | { type: 'PAUSE_SUBSCRIPTION'; payload: string }
  | { type: 'RESUME_SUBSCRIPTION'; payload: string }

// Initial state
const initialState: ChartDataContextState = {
  subscriptions: new Map(),
  data: new Map(),
  state: {
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
  },
  metrics: {
    latency: 0,
    throughput: 0,
    errorRate: 0,
    bufferUtilization: 0,
    memoryUsage: 0,
    updateFrequency: 0
  },
  isConnected: false
}

// Reducer function
function chartDataReducer(
  state: ChartDataContextState,
  action: ChartDataContextAction
): ChartDataContextState {
  switch (action.type) {
    case 'ADD_SUBSCRIPTION':
      return {
        ...state,
        subscriptions: new Map(state.subscriptions).set(action.payload.id, action.payload),
        data: new Map(state.data).set(action.payload.id, [])
      }

    case 'REMOVE_SUBSCRIPTION':
      const newSubscriptions = new Map(state.subscriptions)
      const newData = new Map(state.data)
      newSubscriptions.delete(action.payload)
      newData.delete(action.payload)
      return {
        ...state,
        subscriptions: newSubscriptions,
        data: newData
      }

    case 'UPDATE_SUBSCRIPTION':
      return {
        ...state,
        subscriptions: new Map(state.subscriptions).set(action.payload.id, action.payload)
      }

    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        isConnected: action.payload,
        state: {
          ...state.state,
          isLive: action.payload
        }
      }

    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: action.payload
      }

    case 'CLEAR_DATA':
      if (action.payload) {
        const clearedData = new Map(state.data)
        clearedData.delete(action.payload)
        return { ...state, data: clearedData }
      }
      return {
        ...state,
        data: new Map()
      }

    case 'PAUSE_SUBSCRIPTION':
      const pausedSubscriptions = new Map(state.subscriptions)
      const subscription = pausedSubscriptions.get(action.payload)
      if (subscription) {
        subscription.isActive = false
      }
      return {
        ...state,
        subscriptions: pausedSubscriptions,
        state: {
          ...state.state,
          isPaused: true
        }
      }

    case 'RESUME_SUBSCRIPTION':
      const resumedSubscriptions = new Map(state.subscriptions)
      const resumedSubscription = resumedSubscriptions.get(action.payload)
      if (resumedSubscription) {
        resumedSubscription.isActive = true
      }
      return {
        ...state,
        subscriptions: resumedSubscriptions,
        state: {
          ...state.state,
          isPaused: false
        }
      }

    default:
      return state
  }
}

// Create context
const ChartDataContext = createContext<{
  state: ChartDataContextState
  dispatch: React.Dispatch<ChartDataContextAction>
  actions: {
    subscribe: (subscription: DataSubscription) => void
    unsubscribe: (id: string) => void
    pauseSubscription: (id: string) => void
    resumeSubscription: (id: string) => void
    clearData: (id?: string) => void
    getSubscriptionData: (id: string) => any[]
    isConnected: boolean
  }
} | null>(null)

// Provider props
interface ChartDataProviderProps {
  children: ReactNode
  websocketUrl?: string
  maxReconnectAttempts?: number
  reconnectInterval?: number
  onConnectionChange?: (isConnected: boolean) => void
  onError?: (error: Error) => void
}

// Provider component
export function ChartDataProvider({
  children,
  websocketUrl = 'ws://localhost:8080/ws',
  maxReconnectAttempts,
  reconnectInterval,
  onConnectionChange,
  onError
}: ChartDataProviderProps) {
  const [state, dispatch] = useReducer(chartDataReducer, initialState)

  // Collect all active subscriptions for useRealTimeData
  const activeSubscriptions = Array.from(state.subscriptions.values())
    .filter(sub => sub.isActive)

  // Use real-time data hook
  const {
    data: realTimeData,
    isConnected,
    metrics,
    subscribe,
    unsubscribe,
    pause,
    resume,
    clearBuffer
  } = useRealTimeData({
    url: websocketUrl,
    subscriptions: activeSubscriptions,
    maxReconnectAttempts,
    reconnectInterval,
    onConnectionChange: (connected) => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: connected })
      onConnectionChange?.(connected)
    },
    onError
  })

  // Update data when real-time data changes
  useEffect(() => {
    Object.entries(realTimeData).forEach(([id, data]) => {
      dispatch({
        type: 'UPDATE_DATA',
        payload: { id, data }
      })
    })
  }, [realTimeData])

  // Update metrics
  useEffect(() => {
    dispatch({ type: 'UPDATE_METRICS', payload: metrics })
  }, [metrics])

  // Action creators
  const actions = {
    subscribe: (subscription: DataSubscription) => {
      dispatch({ type: 'ADD_SUBSCRIPTION', payload: subscription })
      subscribe(subscription)
    },

    unsubscribe: (id: string) => {
      dispatch({ type: 'REMOVE_SUBSCRIPTION', payload: id })
      unsubscribe(id)
    },

    pauseSubscription: (id: string) => {
      dispatch({ type: 'PAUSE_SUBSCRIPTION', payload: id })
      pause()
    },

    resumeSubscription: (id: string) => {
      dispatch({ type: 'RESUME_SUBSCRIPTION', payload: id })
      resume()
    },

    clearData: (id?: string) => {
      dispatch({ type: 'CLEAR_DATA', payload: id })
      clearBuffer(id)
    },

    getSubscriptionData: (id: string) => {
      return realTimeData[id] || state.data.get(id) || []
    },

    isConnected
  }

  const contextValue = {
    state,
    dispatch,
    actions
  }

  return (
    <ChartDataContext.Provider value={contextValue}>
      {children}
    </ChartDataContext.Provider>
  )
}

// Hook to use chart data context
export function useChartData() {
  const context = useContext(ChartDataContext)
  if (!context) {
    throw new Error('useChartData must be used within a ChartDataProvider')
  }
  return context
}

// Hook to subscribe to specific data
export function useChartSubscription(subscription: DataSubscription) {
  const { state, actions } = useChartData()

  useEffect(() => {
    // Subscribe if not already subscribed
    if (!state.subscriptions.has(subscription.id)) {
      actions.subscribe(subscription)
    }

    return () => {
      // Cleanup on unmount
      actions.unsubscribe(subscription.id)
    }
  }, [subscription.id])

  const data = actions.getSubscriptionData(subscription.id)
  const subscriptionState = state.subscriptions.get(subscription.id)

  return {
    data,
    isConnected: actions.isConnected,
    isActive: subscriptionState?.isActive ?? false,
    lastUpdate: subscriptionState?.lastUpdate,
    pause: () => actions.pauseSubscription(subscription.id),
    resume: () => actions.resumeSubscription(subscription.id),
    clear: () => actions.clearData(subscription.id)
  }
}

// Hook to manage multiple subscriptions
export function useMultipleChartSubscriptions(
  subscriptions: DataSubscription[]
) {
  const { state, actions } = useChartData()

  useEffect(() => {
    // Subscribe to all subscriptions
    subscriptions.forEach(subscription => {
      if (!state.subscriptions.has(subscription.id)) {
        actions.subscribe(subscription)
      }
    })

    return () => {
      // Cleanup all subscriptions
      subscriptions.forEach(subscription => {
        actions.unsubscribe(subscription.id)
      })
    }
  }, [subscriptions.map(s => s.id).join(',')])

  const dataMap = new Map<string, any[]>()
  subscriptions.forEach(sub => {
    dataMap.set(sub.id, actions.getSubscriptionData(sub.id))
  })

  return {
    dataMap,
    isConnected: actions.isConnected,
    getSubscription: (id: string) => state.subscriptions.get(id),
    pauseAll: () => subscriptions.forEach(sub => actions.pauseSubscription(sub.id)),
    resumeAll: () => subscriptions.forEach(sub => actions.resumeSubscription(sub.id)),
    clearAll: () => actions.clearData()
  }
}

// Export types
export type { ChartDataProviderProps, ChartDataContextState, ChartDataContextAction }