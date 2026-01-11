import { useState, useEffect, useCallback } from 'react'
import { ChannelType } from '../types/websocket'
import { useWebSocketService } from './useWebSocketService'

interface StrategyUpdate {
  id: string
  name: string
  status: 'running' | 'stopped' | 'paused' | 'error'
  profit: number
  trades: number
  winRate: number
  lastSignal?: {
    type: 'BUY' | 'SELL'
    price: number
    timestamp: string
    symbol: string
  }
  performance?: {
    dailyReturn: number
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
  }
  timestamp: string
}

interface UseRealTimeStrategyUpdatesOptions {
  strategyIds?: string[]
  autoSubscribe?: boolean
  onUpdate?: (strategy: StrategyUpdate) => void
  onSignal?: (strategyId: string, signal: any) => void
}

interface UseRealTimeStrategyUpdatesReturn {
  strategies: Map<string, StrategyUpdate>
  signals: Array<{ strategyId: string; signal: any; timestamp: number }>
  isConnected: boolean
  lastUpdate: number
  subscribe: (strategyIds: string[]) => void
  unsubscribe: (strategyIds: string[]) => void
  refresh: () => void
}

export const useRealTimeStrategyUpdates = ({
  strategyIds = [],
  autoSubscribe = true,
  onUpdate,
  onSignal
}: UseRealTimeStrategyUpdatesOptions = {}): UseRealTimeStrategyUpdatesReturn => {
  const [strategies, setStrategies] = useState<Map<string, StrategyUpdate>>(new Map())
  const [signals, setSignals] = useState<Array<{ strategyId: string; signal: any; timestamp: number }>>([])
  const [lastUpdate, setLastUpdate] = useState(0)

  const { isConnected, subscribe, send, getCachedData } = useWebSocketService({
    autoConnect: true,
    channels: autoSubscribe ? [ChannelType.STRATEGY_UPDATES] : []
  })

  // Subscribe to strategy updates
  const subscribeToStrategies = useCallback((strategyIdsToSubscribe: string[]) => {
    if (isConnected && strategyIdsToSubscribe.length > 0) {
      send('subscribe_strategies', { strategy_ids: strategyIdsToSubscribe })
    }
  }, [isConnected, send])

  // Unsubscribe from strategy updates
  const unsubscribeFromStrategies = useCallback((strategyIdsToUnsubscribe: string[]) => {
    if (isConnected && strategyIdsToUnsubscribe.length > 0) {
      send('unsubscribe_strategies', { strategy_ids: strategyIdsToUnsubscribe })
    }
  }, [isConnected, send])

  // Handle strategy updates
  useEffect(() => {
    const unsubscribe = subscribe(ChannelType.STRATEGY_UPDATES, (update: any) => {
      if (update && update.id) {
        const strategyUpdate: StrategyUpdate = {
          id: update.id,
          name: update.name || `Strategy ${update.id}`,
          status: update.status || 'stopped',
          profit: update.profit || 0,
          trades: update.trades || 0,
          winRate: update.winRate || 0,
          lastSignal: update.lastSignal,
          performance: update.performance,
          timestamp: update.timestamp || new Date().toISOString()
        }

        setStrategies(prevStrategies => {
          const updated = new Map(prevStrategies)
          updated.set(update.id, strategyUpdate)
          return updated
        })

        setLastUpdate(Date.now())
        onUpdate?.(strategyUpdate)

        // Handle trading signals
        if (update.lastSignal) {
          const signalData = {
            strategyId: update.id,
            signal: update.lastSignal,
            timestamp: Date.now()
          }
          setSignals(prevSignals => [...prevSignals, signalData].slice(-100)) // Keep last 100 signals
          onSignal?.(update.id, update.lastSignal)
        }
      }
    })

    return unsubscribe
  }, [subscribe, onUpdate, onSignal])

  // Auto-subscribe to initial strategies
  useEffect(() => {
    if (autoSubscribe && strategyIds.length > 0 && isConnected) {
      subscribeToStrategies(strategyIds)
    }
  }, [autoSubscribe, strategyIds, isConnected, subscribeToStrategies])

  // Load cached data on mount
  useEffect(() => {
    const cachedData = getCachedData('strategy_updates')
    if (cachedData) {
      setStrategies(new Map(Object.entries(cachedData).map(([id, strategy]: [string, any]) => [id, {
        ...strategy,
        timestamp: new Date().toISOString()
      }])))
    }
  }, [getCachedData])

  // Refresh data
  const refresh = useCallback(() => {
    const currentStrategies = Array.from(strategies.keys())
    if (currentStrategies.length > 0) {
      subscribeToStrategies(currentStrategies)
    }
  }, [strategies, subscribeToStrategies])

  // Clear old signals (keep only signals from last hour)
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const oneHour = 60 * 60 * 1000
      setSignals(prevSignals => prevSignals.filter(s => now - s.timestamp < oneHour))
    }, 60000) // Check every minute

    return () => clearInterval(interval)
  }, [])

  return {
    strategies,
    signals,
    isConnected,
    lastUpdate,
    subscribe: subscribeToStrategies,
    unsubscribe: unsubscribeFromStrategies,
    refresh
  }
}