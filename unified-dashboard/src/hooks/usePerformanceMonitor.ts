import { useCallback, useRef, useState, useEffect } from 'react'

interface PerformanceMetrics {
  [key: string]: number
}

interface UsePerformanceMonitorReturn {
  startMeasure: (name: string) => void
  endMeasure: (name: string) => number
  getMetrics: () => PerformanceMetrics
  clearMetrics: () => void
}

export const usePerformanceMonitor = (): UsePerformanceMonitorReturn => {
  const metricsRef = useRef<PerformanceMetrics>({})
  const startTimesRef = useRef<Record<string, number>>({})

  const startMeasure = useCallback((name: string) => {
    // 使用 Performance API 或 Date 作为后备
    if ('performance' in window && 'mark' in performance) {
      performance.mark(`${name}-start`)
    } else {
      startTimesRef.current[name] = Date.now()
    }
  }, [])

  const endMeasure = useCallback((name: string): number => {
    let duration = 0

    if ('performance' in window && 'mark' in performance && 'measure' in performance) {
      try {
        performance.mark(`${name}-end`)
        performance.measure(name, `${name}-start`, `${name}-end`)

        const entries = performance.getEntriesByName(name, 'measure')
        if (entries.length > 0) {
          duration = entries[entries.length - 1].duration
        }

        // 清理标记
        performance.clearMarks(`${name}-start`)
        performance.clearMarks(`${name}-end`)
        performance.clearMeasures(name)
      } catch (error) {
        console.warn('Performance API error:', error)
      }
    } else {
      const startTime = startTimesRef.current[name]
      if (startTime) {
        duration = Date.now() - startTime
        delete startTimesRef.current[name]
      }
    }

    // 记录指标
    if (duration > 0) {
      metricsRef.current[name] = duration
    }

    return duration
  }, [])

  const getMetrics = useCallback((): PerformanceMetrics => {
    return { ...metricsRef.current }
  }, [])

  const clearMetrics = useCallback((): void => {
    metricsRef.current = {}
    startTimesRef.current = {}
  }, [])

  return {
    startMeasure,
    endMeasure,
    getMetrics,
    clearMetrics
  }
}

// Hook for monitoring render performance
export function useRenderMonitor(componentName: string) {
  const renderCount = useRef(0)
  const lastRenderTime = useRef<number>(Date.now())
  const [renderMetrics, setRenderMetrics] = useState({
    count: 0,
    averageRenderTime: 0,
    totalRenderTime: 0
  })

  useEffect(() => {
    renderCount.current++
    const currentTime = Date.now()
    const renderTime = currentTime - lastRenderTime.current
    lastRenderTime.current = currentTime

    const totalRenderTime = renderMetrics.totalRenderTime + renderTime
    const averageRenderTime = totalRenderTime / renderCount.current

    setRenderMetrics({
      count: renderCount.current,
      averageRenderTime,
      totalRenderTime
    })
  })

  return renderMetrics
}

// Hook for monitoring FPS
export function useFPSMonitor() {
  const [fps, setFps] = useState(60)
  const fpsRef = useRef(60)
  const lastTimeRef = useRef(performance.now())
  const frameCountRef = useRef(0)

  useEffect(() => {
    let animationId: number

    const checkFPS = () => {
      frameCountRef.current++
      const currentTime = performance.now()

      if (currentTime >= lastTimeRef.current + 1000) {
        const currentFps = Math.round(
          (frameCountRef.current * 1000) / (currentTime - lastTimeRef.current)
        )

        fpsRef.current = currentFps
        setFps(currentFps)
        frameCountRef.current = 0
        lastTimeRef.current = currentTime
      }

      animationId = requestAnimationFrame(checkFPS)
    }

    animationId = requestAnimationFrame(checkFPS)

    return () => {
      cancelAnimationFrame(animationId)
    }
  }, [])

  return fps
}

// Hook for monitoring memory usage
export function useMemoryMonitor() {
  const [memoryInfo, setMemoryInfo] = useState<{
    usedJSHeapSize: number
    totalJSHeapSize: number
    jsHeapSizeLimit: number
  } | null>(null)

  useEffect(() => {
    const updateMemoryInfo = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory as PerformanceMemory
        setMemoryInfo({
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit
        })
      }
    }

    // Initial update
    updateMemoryInfo()

    // Update every 5 seconds
    const interval = setInterval(updateMemoryInfo, 5000)

    return () => clearInterval(interval)
  }, [])

  return memoryInfo
}

// Hook for monitoring network conditions
export function useNetworkMonitor() {
  const [networkInfo, setNetworkInfo] = useState<{
    effectiveType: string
    downlink: number
    rtt: number
    saveData: boolean
  } | null>(null)

  useEffect(() => {
    const updateNetworkInfo = () => {
      if ('connection' in navigator) {
        const connection = (navigator as any).connection as NetworkInformation
        setNetworkInfo({
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData
        })
      }
    }

    // Initial update
    updateNetworkInfo()

    // Listen for changes
    if ('connection' in navigator) {
      const connection = (navigator as any).connection as NetworkInformation
      connection.addEventListener('change', updateNetworkInfo)

      return () => {
        connection.removeEventListener('change', updateNetworkInfo)
      }
    }
  }, [])

  return networkInfo
}