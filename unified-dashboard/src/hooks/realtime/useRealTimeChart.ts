import { useEffect, useRef, useState, useCallback } from 'react'
import { useRealTimeChart } from '../../components/charts/RealTime/RealTimeChartProvider'
import { ChartDataPoint } from '../../components/charts/RealTime/RealTimeChartProvider'

// Real-time chart hook options
export interface UseRealTimeChartOptions {
  symbol: string
  timeframe: string
  maxDataPoints?: number
  autoSubscribe?: boolean
  updateInterval?: number
  onDataUpdate?: (data: ChartDataPoint[]) => void
  onError?: (error: Error) => void
}

// Real-time chart hook return value
export interface UseRealTimeChartReturn {
  data: ChartDataPoint[] | null
  isLoading: boolean
  error: Error | null
  lastUpdate: Date | null
  subscribe: () => void
  unsubscribe: () => void
  clearData: () => void
  refresh: () => void
  getLatestPoint: () => ChartDataPoint | null
  getDataPoint: (timestamp: Date) => ChartDataPoint | null
  getPreviousPoint: (timestamp: Date) => ChartDataPoint | null
  getNextPoint: (timestamp: Date) => ChartDataPoint | null
  calculateReturns: (period: number) => number | null
  calculateVolatility: (period: number) => number | null
  calculateMovingAverage: (period: number) => number | null
  calculateRSI: (period: number) => number | null
}

// Real-time chart hook
export const useRealTimeChart = (options: UseRealTimeChartOptions): UseRealTimeChartReturn => {
  const {
    symbol,
    timeframe,
    maxDataPoints = 1000,
    autoSubscribe = true,
    updateInterval = 1000,
    onDataUpdate,
    onError
  } = options

  const chartContext = useRealTimeChart()
  const subscriberIdRef = useRef<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // Generate unique subscriber ID
  const getSubscriberId = useCallback(() => {
    if (!subscriberIdRef.current) {
      subscriberIdRef.current = `hook-${symbol}-${timeframe}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
    return subscriberIdRef.current
  }, [symbol, timeframe])

  // Subscribe to chart data
  const subscribe = useCallback(() => {
    try {
      setIsLoading(true)
      setError(null)

      const id = getSubscriberId()
      chartContext.subscribe(symbol, timeframe, id)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to subscribe')
      setError(error)
      onError?.(error)
    } finally {
      setIsLoading(false)
    }
  }, [symbol, timeframe, chartContext, getSubscriberId, onError])

  // Unsubscribe from chart data
  const unsubscribe = useCallback(() => {
    if (subscriberIdRef.current) {
      chartContext.unsubscribe(symbol, timeframe, subscriberIdRef.current)
      subscriberIdRef.current = null
    }
  }, [symbol, timeframe, chartContext])

  // Clear chart data
  const clearData = useCallback(() => {
    chartContext.clearData(symbol, timeframe)
  }, [symbol, timeframe, chartContext])

  // Refresh data
  const refresh = useCallback(() => {
    clearData()
    subscribe()
  }, [clearData, subscribe])

  // Get chart data
  const data = chartContext.getData(symbol, timeframe)

  // Limit data points
  const limitedData = data ? data.slice(-maxDataPoints) : null

  // Get latest data point
  const getLatestPoint = useCallback((): ChartDataPoint | null => {
    if (!limitedData || limitedData.length === 0) return null
    return limitedData[limitedData.length - 1]
  }, [limitedData])

  // Get data point by timestamp
  const getDataPoint = useCallback((timestamp: Date): ChartDataPoint | null => {
    if (!limitedData) return null

    return limitedData.find(point =>
      point.timestamp.getTime() === timestamp.getTime()
    ) || null
  }, [limitedData])

  // Get previous data point
  const getPreviousPoint = useCallback((timestamp: Date): ChartDataPoint | null => {
    if (!limitedData) return null

    const index = limitedData.findIndex(point =>
      point.timestamp.getTime() === timestamp.getTime()
    )

    return index > 0 ? limitedData[index - 1] : null
  }, [limitedData])

  // Get next data point
  const getNextPoint = useCallback((timestamp: Date): ChartDataPoint | null => {
    if (!limitedData) return null

    const index = limitedData.findIndex(point =>
      point.timestamp.getTime() === timestamp.getTime()
    )

    return index < limitedData.length - 1 ? limitedData[index + 1] : null
  }, [limitedData])

  // Calculate returns
  const calculateReturns = useCallback((period: number): number | null => {
    if (!limitedData || limitedData.length <= period) return null

    const current = limitedData[limitedData.length - 1].close
    const previous = limitedData[limitedData.length - 1 - period].close

    return (current - previous) / previous
  }, [limitedData])

  // Calculate volatility (standard deviation of returns)
  const calculateVolatility = useCallback((period: number): number | null => {
    if (!limitedData || limitedData.length <= period) return null

    const returns: number[] = []
    for (let i = 1; i <= period; i++) {
      const current = limitedData[limitedData.length - i].close
      const previous = limitedData[limitedData.length - i - 1].close
      returns.push((current - previous) / previous)
    }

    const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length

    return Math.sqrt(variance)
  }, [limitedData])

  // Calculate moving average
  const calculateMovingAverage = useCallback((period: number): number | null => {
    if (!limitedData || limitedData.length < period) return null

    const sum = limitedData
      .slice(-period)
      .reduce((sum, point) => sum + point.close, 0)

    return sum / period
  }, [limitedData])

  // Calculate RSI
  const calculateRSI = useCallback((period: number = 14): number | null => {
    if (!limitedData || limitedData.length <= period) return null

    let gains = 0
    let losses = 0

    for (let i = limitedData.length - period; i < limitedData.length; i++) {
      const change = limitedData[i].close - limitedData[i - 1].close
      if (change > 0) {
        gains += change
      } else {
        losses -= change
      }
    }

    const avgGain = gains / period
    const avgLoss = losses / period
    const rs = avgGain / avgLoss

    return 100 - (100 / (1 + rs))
  }, [limitedData])

  // Auto-subscribe
  useEffect(() => {
    if (autoSubscribe) {
      subscribe()
    }

    return () => {
      unsubscribe()
    }
  }, [autoSubscribe, subscribe, unsubscribe])

  // Set up data update interval
  useEffect(() => {
    if (!updateInterval || updateInterval <= 0) return

    const interval = setInterval(() => {
      if (limitedData && limitedData.length > 0) {
        setLastUpdate(new Date())
        onDataUpdate?.(limitedData)
      }
    }, updateInterval)

    return () => clearInterval(interval)
  }, [updateInterval, limitedData, onDataUpdate])

  // Update last update time when data changes
  useEffect(() => {
    if (limitedData && limitedData.length > 0) {
      setLastUpdate(new Date())
      setIsLoading(false)
    }
  }, [limitedData])

  return {
    data: limitedData,
    isLoading,
    error,
    lastUpdate,
    subscribe,
    unsubscribe,
    clearData,
    refresh,
    getLatestPoint,
    getDataPoint,
    getPreviousPoint,
    getNextPoint,
    calculateReturns,
    calculateVolatility,
    calculateMovingAverage,
    calculateRSI
  }
}

export default useRealTimeChart