import { useState, useEffect, useRef, useCallback } from 'react'
import { ChartPerformanceMetrics } from '../types/chart.types'

interface UseChartPerformanceOptions {
  enableFPSMonitoring?: boolean
  enableMemoryMonitoring?: boolean
  enableRenderTimeTracking?: boolean
  onPerformanceAlert?: (metrics: ChartPerformanceMetrics) => void
  fpsThreshold?: number
  memoryThreshold?: number // MB
  renderTimeThreshold?: number // ms
}

interface UseChartPerformanceReturn {
  metrics: ChartPerformanceMetrics
  startRenderTracking: () => void
  endRenderTracking: () => void
  getAverageRenderTime: () => number
  getFPS: () => number
  getMemoryUsage: () => number
  resetMetrics: () => void
}

// FPS Monitor
class FPSMonitor {
  private frames = 0
  private lastTime = performance.now()
  private fps = 0
  private isRunning = false

  start() {
    if (this.isRunning) return
    this.isRunning = true
    this.tick()
  }

  stop() {
    this.isRunning = false
  }

  private tick = () => {
    if (!this.isRunning) return

    this.frames++
    const currentTime = performance.now()

    if (currentTime >= this.lastTime + 1000) {
      this.fps = Math.round((this.frames * 1000) / (currentTime - this.lastTime))
      this.frames = 0
      this.lastTime = currentTime
    }

    requestAnimationFrame(this.tick)
  }

  getFPS() {
    return this.fps
  }
}

// Memory Monitor
class MemoryMonitor {
  private samples: number[] = []
  private maxSamples = 60
  private interval: NodeJS.Timeout | null = null

  start() {
    if (this.interval) return

    this.interval = setInterval(() => {
      const memory = this.getMemoryUsage()
      this.samples.push(memory)

      if (this.samples.length > this.maxSamples) {
        this.samples.shift()
      }
    }, 1000)
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval)
      this.interval = null
    }
  }

  private getMemoryUsage(): number {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return memory.usedJSHeapSize / (1024 * 1024) // Convert to MB
    }
    return 0
  }

  getCurrentMemory(): number {
    return this.getMemoryUsage()
  }

  getAverageMemory(): number {
    if (this.samples.length === 0) return 0
    return this.samples.reduce((a, b) => a + b, 0) / this.samples.length
  }

  getPeakMemory(): number {
    return Math.max(...this.samples, 0)
  }
}

// Render Time Tracker
class RenderTimeTracker {
  private samples: number[] = []
  private maxSamples = 100
  private startTime: number = 0
  private isTracking = false

  startTracking() {
    this.startTime = performance.now()
    this.isTracking = true
  }

  endTracking(): number {
    if (!this.isTracking) return 0

    const endTime = performance.now()
    const renderTime = endTime - this.startTime
    this.isTracking = false

    this.samples.push(renderTime)
    if (this.samples.length > this.maxSamples) {
      this.samples.shift()
    }

    return renderTime
  }

  getAverageRenderTime(): number {
    if (this.samples.length === 0) return 0
    return this.samples.reduce((a, b) => a + b, 0) / this.samples.length
  }

  getMaxRenderTime(): number {
    return Math.max(...this.samples, 0)
  }

  getRenderTimePercentile(p: number): number {
    if (this.samples.length === 0) return 0
    const sorted = [...this.samples].sort((a, b) => a - b)
    const index = Math.floor(sorted.length * (p / 100))
    return sorted[index] || 0
  }
}

export function useChartPerformance(options: UseChartPerformanceOptions = {}): UseChartPerformanceReturn {
  const {
    enableFPSMonitoring = true,
    enableMemoryMonitoring = true,
    enableRenderTimeTracking = true,
    onPerformanceAlert,
    fpsThreshold = 30,
    memoryThreshold = 100, // MB
    renderTimeThreshold = 16 // ms (60fps)
  } = options

  const [metrics, setMetrics] = useState<ChartPerformanceMetrics>({
    renderTime: 0,
    updateCount: 0,
    lastUpdate: new Date(),
    fps: 0,
    memoryUsage: 0,
    dataPointsCount: 0
  })

  const fpsMonitorRef = useRef<FPSMonitor>()
  const memoryMonitorRef = useRef<MemoryMonitor>()
  const renderTrackerRef = useRef<RenderTimeTracker>()
  const updateCountRef = useRef(0)
  const dataPointsCountRef = useRef(0)

  // Initialize monitors
  useEffect(() => {
    if (enableFPSMonitoring) {
      fpsMonitorRef.current = new FPSMonitor()
      fpsMonitorRef.current.start()
    }

    if (enableMemoryMonitoring) {
      memoryMonitorRef.current = new MemoryMonitor()
      memoryMonitorRef.current.start()
    }

    if (enableRenderTimeTracking) {
      renderTrackerRef.current = new RenderTimeTracker()
    }

    return () => {
      fpsMonitorRef.current?.stop()
      memoryMonitorRef.current?.stop()
    }
  }, [enableFPSMonitoring, enableMemoryMonitoring, enableRenderTimeTracking])

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const newMetrics: ChartPerformanceMetrics = {
        renderTime: renderTrackerRef.current?.getAverageRenderTime() || 0,
        updateCount: updateCountRef.current,
        lastUpdate: new Date(),
        fps: fpsMonitorRef.current?.getFPS() || 0,
        memoryUsage: memoryMonitorRef.current?.getCurrentMemory() || 0,
        dataPointsCount: dataPointsCountRef.current
      }

      setMetrics(newMetrics)

      // Check for performance alerts
      if (onPerformanceAlert) {
        if (newMetrics.fps < fpsThreshold) {
          onPerformanceAlert({
            ...newMetrics,
            renderTime: newMetrics.renderTime
          })
        }

        if (newMetrics.memoryUsage > memoryThreshold) {
          onPerformanceAlert({
            ...newMetrics,
            memoryUsage: newMetrics.memoryUsage
          })
        }

        if (newMetrics.renderTime > renderTimeThreshold) {
          onPerformanceAlert({
            ...newMetrics,
            renderTime: newMetrics.renderTime
          })
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [onPerformanceAlert, fpsThreshold, memoryThreshold, renderTimeThreshold])

  const startRenderTracking = useCallback(() => {
    if (renderTrackerRef.current) {
      renderTrackerRef.current.startTracking()
    }
  }, [])

  const endRenderTracking = useCallback(() => {
    updateCountRef.current++
    return renderTrackerRef.current?.endTracking() || 0
  }, [])

  const getAverageRenderTime = useCallback(() => {
    return renderTrackerRef.current?.getAverageRenderTime() || 0
  }, [])

  const getFPS = useCallback(() => {
    return fpsMonitorRef.current?.getFPS() || 0
  }, [])

  const getMemoryUsage = useCallback(() => {
    return memoryMonitorRef.current?.getCurrentMemory() || 0
  }, [])

  const resetMetrics = useCallback(() => {
    updateCountRef.current = 0
    dataPointsCountRef.current = 0
    setMetrics({
      renderTime: 0,
      updateCount: 0,
      lastUpdate: new Date(),
      fps: 0,
      memoryUsage: 0,
      dataPointsCount: 0
    })
  }, [])

  // Function to update data points count
  const updateDataPointsCount = useCallback((count: number) => {
    dataPointsCountRef.current = count
  }, [])

  // Expose data points count updater through ref
  useEffect(() => {
    (metrics as any).updateDataPointsCount = updateDataPointsCount
  }, [updateDataPointsCount])

  return {
    metrics,
    startRenderTracking,
    endRenderTracking,
    getAverageRenderTime,
    getFPS,
    getMemoryUsage,
    resetMetrics
  }
}