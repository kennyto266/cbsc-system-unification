import { useState, useEffect, useCallback, useRef } from 'react'

interface UseRealTimeChartOptions {
  initialData?: Array<{ time: string; value: number }>
  updateInterval?: number
  maxDataPoints?: number
  autoStart?: boolean
}

interface UseRealTimeChartReturn {
  data: Array<{ time: string; value: number }>
  isRunning: boolean
  lastValue: number
  addDataPoint: (value: number) => void
  start: () => void
  stop: () => void
  reset: () => void
  setUpdateInterval: (interval: number) => void
}

export const useRealTimeChart = ({
  initialData = [],
  updateInterval = 1000,
  maxDataPoints = 50,
  autoStart = true
}: UseRealTimeChartOptions = {}): UseRealTimeChartReturn => {
  const [data, setData] = useState<Array<{ time: string; value: number }>>(initialData)
  const [isRunning, setIsRunning] = useState(autoStart)
  const [lastValue, setLastValue] = useState<number>(0)
  const intervalRef = useRef<NodeJS.Timeout>()
  const updateIntervalRef = useRef(updateInterval)

  // Add new data point
  const addDataPoint = useCallback((value: number) => {
    const now = new Date()
    const timeString = now.toLocaleTimeString('zh-CN')
    const newPoint = { time: timeString, value }

    setData(prevData => {
      const updatedData = [...prevData, newPoint]

      // Keep only the last maxDataPoints
      if (updatedData.length > maxDataPoints) {
        return updatedData.slice(-maxDataPoints)
      }

      return updatedData
    })

    setLastValue(value)
  }, [maxDataPoints])

  // Start real-time updates
  const start = useCallback(() => {
    if (!isRunning) {
      setIsRunning(true)
    }
  }, [isRunning])

  // Stop real-time updates
  const stop = useCallback(() => {
    if (isRunning) {
      setIsRunning(false)
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRunning])

  // Reset data
  const reset = useCallback(() => {
    setData([])
    setLastValue(0)
    setIsRunning(false)
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
  }, [])

  // Update interval
  const setUpdateInterval = useCallback((newInterval: number) => {
    updateIntervalRef.current = newInterval
    // Restart with new interval if running
    if (isRunning) {
      stop()
      start()
    }
  }, [isRunning, start, stop])

  // Effect for managing interval
  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => {
        // This should be replaced with actual data fetching
        // For now, it just emits a custom event that components can listen to
        window.dispatchEvent(new CustomEvent('realTimeChartUpdate', {
          detail: { addDataPoint }
        }))
      }, updateIntervalRef.current)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRunning, addDataPoint])

  return {
    data,
    isRunning,
    lastValue,
    addDataPoint,
    start,
    stop,
    reset,
    setUpdateInterval
  }
}