import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAppDispatch, useAppSelector } from '../../store'
import { fetchChartData, subscribeToRealTimeData } from '../../store/slices/chartDataSlice'

export interface ChartDataPoint {
  timestamp: string | Date
  value: number
  label?: string
  metadata?: Record<string, any>
}

export interface UseChartDataOptions {
  symbol?: string
  timeframe?: string
  indicator?: string
  startDate?: string | Date
  endDate?: string | Date
  limit?: number
  refreshInterval?: number
  autoRefresh?: boolean
  realTime?: boolean
  transform?: (data: any) => ChartDataPoint[]
  onError?: (error: Error) => void
}

export const useChartData = (options: UseChartDataOptions = {}) => {
  const {
    symbol = '',
    timeframe = '1d',
    indicator = '',
    startDate,
    endDate,
    limit = 100,
    refreshInterval = 60000, // 1 minute
    autoRefresh = false,
    realTime = false,
    transform,
    onError,
  } = options

  const dispatch = useAppDispatch()
  const { data, loading, error, lastUpdate } = useAppSelector(
    state => state.chartData[`${symbol}-${timeframe}-${indicator}`] || {}
  )

  const [processedData, setProcessedData] = useState<ChartDataPoint[]>([])
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Process raw data
  const processData = useCallback((rawData: any[]): ChartDataPoint[] => {
    if (!rawData || rawData.length === 0) return []

    try {
      if (transform) {
        return transform(rawData)
      }

      // Default transformation
      return rawData.map(item => ({
        timestamp: new Date(item.timestamp || item.time || item.date),
        value: parseFloat(item.value || item.price || item.close || 0),
        label: item.label,
        metadata: item.metadata,
      }))
    } catch (err) {
      console.error('Error processing chart data:', err)
      onError?.(err as Error)
      return []
    }
  }, [transform, onError])

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!symbol) return

    try {
      const result = await dispatch(
        fetchChartData({
          symbol,
          timeframe,
          indicator,
          startDate: startDate?.toISOString(),
          endDate: endDate?.toISOString(),
          limit,
        })
      ).unwrap()

      const processed = processData(result)
      setProcessedData(processed)
    } catch (err) {
      console.error('Error fetching chart data:', err)
      onError?.(err as Error)
    }
  }, [
    dispatch,
    symbol,
    timeframe,
    indicator,
    startDate,
    endDate,
    limit,
    processData,
    onError,
  ])

  // Setup real-time subscription
  useEffect(() => {
    if (realTime && symbol) {
      const unsubscribe = dispatch(
        subscribeToRealTimeData({
          symbol,
          timeframe,
          indicator,
          callback: (newData) => {
            const processed = processData([newData])
            setProcessedData(prev => [...prev, ...processed].slice(-limit))
          },
        })
      )

      return unsubscribe
    }
  }, [dispatch, realTime, symbol, timeframe, indicator, limit, processData])

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [autoRefresh, refreshInterval, fetchData])

  // Initial data fetch
  useEffect(() => {
    if (symbol) {
      fetchData()
    }
  }, [symbol, timeframe, indicator, startDate, endDate, limit, fetchData])

  // Calculate statistics
  const statistics = useMemo(() => {
    if (processedData.length === 0) return null

    const values = processedData.map(d => d.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const latest = values[values.length - 1]
    const first = values[0]
    const change = latest - first
    const changePercent = first !== 0 ? (change / first) * 100 : 0

    return {
      min,
      max,
      latest,
      change,
      changePercent,
      high: Math.max(...values.slice(1)), // Exclude first point
      low: Math.min(...values.slice(1)),
      average: values.reduce((sum, val) => sum + val, 0) / values.length,
      volume: processedData.reduce((sum, d) => sum + (d.metadata?.volume || 0), 0),
    }
  }, [processedData])

  // Manual refresh
  const refresh = useCallback(() => {
    fetchData()
  }, [fetchData])

  // Clear data
  const clear = useCallback(() => {
    setProcessedData([])
  }, [])

  // Append new data
  const appendData = useCallback((newPoints: ChartDataPoint | ChartDataPoint[]) => {
    const points = Array.isArray(newPoints) ? newPoints : [newPoints]
    setProcessedData(prev => [...prev, ...points].slice(-limit))
  }, [limit])

  return {
    data: processedData,
    rawData: data,
    loading,
    error,
    lastUpdate,
    statistics,
    refresh,
    clear,
    appendData,
  }
}