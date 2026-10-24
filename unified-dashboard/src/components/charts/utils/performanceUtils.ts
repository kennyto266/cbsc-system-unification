import { ChartPerformanceMetrics } from '../types/chart.types'

// Performance monitoring utilities
export class PerformanceMonitor {
  private static metrics: Map<string, PerformanceEntry> = new Map()
  private static observers: PerformanceObserver[] = []

  // Start monitoring
  static start(name: string): void {
    if (typeof performance !== 'undefined' && performance.mark) {
      performance.mark(`${name}-start`)
    }
  }

  // End monitoring and get duration
  static end(name: string): number {
    if (typeof performance !== 'undefined' && performance.mark && performance.measure) {
      try {
        performance.mark(`${name}-end`)
        performance.measure(name, `${name}-start`, `${name}-end`)

        const entries = performance.getEntriesByName(name, 'measure')
        if (entries.length > 0) {
          const duration = entries[entries.length - 1].duration
          this.metrics.set(name, entries[entries.length - 1])
          return duration
        }
      } catch (error) {
        console.warn('Performance monitoring failed:', error)
      }
    }
    return 0
  }

  // Get all metrics
  static getMetrics(): Map<string, PerformanceEntry> {
    return new Map(this.metrics)
  }

  // Clear all metrics
  static clear(): void {
    this.metrics.clear()
    if (typeof performance !== 'undefined' && performance.clearMarks) {
      performance.clearMarks()
      performance.clearMeasures()
    }
  }

  // Monitor FPS
  static createFPSMonitor(callback: (fps: number) => void): () => void {
    let frameCount = 0
    let lastTime = performance.now()
    let animationId: number

    const calculateFPS = (currentTime: number) => {
      frameCount++

      if (currentTime >= lastTime + 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime))
        callback(fps)
        frameCount = 0
        lastTime = currentTime
      }

      animationId = requestAnimationFrame(calculateFPS)
    }

    animationId = requestAnimationFrame(calculateFPS)

    return () => {
      cancelAnimationFrame(animationId)
    }
  }

  // Monitor memory usage
  static getMemoryUsage(): {
    used: number
    total: number
    limit: number
  } | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      }
    }
    return null
  }

  // Monitor long tasks
  static createLongTaskMonitor(callback: (task: PerformanceEntry) => void): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) { // Tasks longer than 50ms
              callback(entry)
            }
          }
        })

        observer.observe({ entryTypes: ['longtask'] })
        this.observers.push(observer)
      } catch (error) {
        console.warn('Long task monitoring not supported:', error)
      }
    }
  }

  // Clean up observers
  static cleanup(): void {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
  }
}

// Chart performance optimizer
export class ChartOptimizer {
  // Debounce function for performance
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout

    return function executedFunction(...args: Parameters<T>) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }

      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }

  // Throttle function for performance
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean

    return function executedFunction(...args: Parameters<T>) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }

  // Memoize expensive calculations
  static memoize<T extends (...args: any[]) => any>(func: T): T {
    const cache = new Map()

    return ((...args: Parameters<T>) => {
      const key = JSON.stringify(args)

      if (cache.has(key)) {
        return cache.get(key)
      }

      const result = func(...args)
      cache.set(key, result)
      return result
    }) as T
  }

  // Batch DOM updates
  static batchDOMUpdates(updates: (() => void)[]): void {
    // Use requestAnimationFrame to batch updates
    requestAnimationFrame(() => {
      updates.forEach(update => update())
    })
  }

  // Virtual scrolling helper
  static calculateVisibleItems(
    scrollTop: number,
    containerHeight: number,
    itemHeight: number,
    totalItems: number,
    buffer: number = 5
  ): {
    startIndex: number
    endIndex: number
    offsetY: number
  } {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer)
    const endIndex = Math.min(
      totalItems - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + buffer
    )
    const offsetY = startIndex * itemHeight

    return { startIndex, endIndex, offsetY }
  }

  // Level of Detail (LOD) calculation
  static calculateLOD(
    zoomLevel: number,
    baseDataPoints: number,
    maxDataPoints: number
  ): {
    sampleRate: number
    dataPointsToShow: number
  } {
    // Calculate how many data points to show based on zoom level
    const dataPointsToShow = Math.min(
      Math.floor(baseDataPoints * Math.sqrt(zoomLevel)),
      maxDataPoints
    )

    // Calculate sample rate
    const sampleRate = Math.max(1, Math.floor(baseDataPoints / dataPointsToShow))

    return {
      sampleRate,
      dataPointsToShow
    }
  }

  // Optimize data for rendering
  static optimizeDataForRendering<T>(
    data: T[],
    maxPoints: number,
    getKey: (item: T) => number | string = (item) => (item as any).timestamp
  ): T[] {
    if (data.length <= maxPoints) {
      return data
    }

    const step = Math.ceil(data.length / maxPoints)
    const optimized: T[] = []

    // Always include first and last points
    optimized.push(data[0])

    // Sample intermediate points
    for (let i = step; i < data.length - step; i += step) {
      optimized.push(data[i])
    }

    optimized.push(data[data.length - 1])

    return optimized
  }

  // Progressive rendering helper
  static createProgressiveRenderer<T>(
    items: T[],
    renderBatch: (batch: T[], done: boolean) => void,
    batchSize: number = 50,
    delay: number = 16
  ): void {
    let index = 0

    const renderNextBatch = () => {
      const batch = items.slice(index, index + batchSize)
      const done = index + batchSize >= items.length

      renderBatch(batch, done)

      index += batchSize

      if (!done) {
        setTimeout(renderNextBatch, delay)
      }
    }

    renderNextBatch()
  }

  // Resource cleanup helper
  static createCleanupManager(): {
    addCleanup: (cleanup: () => void) => void
    cleanup: () => void
  } {
    const cleanupTasks: (() => void)[] = []

    return {
      addCleanup: (cleanup: () => void) => {
        cleanupTasks.push(cleanup)
      },
      cleanup: () => {
        cleanupTasks.forEach(task => {
          try {
            task()
          } catch (error) {
            console.error('Cleanup task failed:', error)
          }
        })
        cleanupTasks.length = 0
      }
    }
  }
}

// Performance metrics collector
export class MetricsCollector {
  private metrics: ChartPerformanceMetrics = {
    renderTime: 0,
    updateCount: 0,
    lastUpdate: new Date(),
    fps: 0,
    memoryUsage: 0,
    dataPointsCount: 0
  }

  private renderTimes: number[] = []
  private maxSamples = 100

  // Record render time
  recordRenderTime(time: number): void {
    this.renderTimes.push(time)

    if (this.renderTimes.length > this.maxSamples) {
      this.renderTimes.shift()
    }

    this.metrics.renderTime = this.getAverageRenderTime()
    this.metrics.updateCount++
    this.metrics.lastUpdate = new Date()
  }

  // Update FPS
  updateFPS(fps: number): void {
    this.metrics.fps = fps
  }

  // Update memory usage
  updateMemoryUsage(): void {
    const memory = PerformanceMonitor.getMemoryUsage()
    if (memory) {
      this.metrics.memoryUsage = memory.used / (1024 * 1024) // Convert to MB
    }
  }

  // Update data points count
  updateDataPointsCount(count: number): void {
    this.metrics.dataPointsCount = count
  }

  // Get current metrics
  getMetrics(): ChartPerformanceMetrics {
    return { ...this.metrics }
  }

  // Get average render time
  private getAverageRenderTime(): number {
    if (this.renderTimes.length === 0) return 0
    return this.renderTimes.reduce((a, b) => a + b, 0) / this.renderTimes.length
  }

  // Get render time percentile
  getRenderTimePercentile(p: number): number {
    if (this.renderTimes.length === 0) return 0
    const sorted = [...this.renderTimes].sort((a, b) => a - b)
    const index = Math.floor(sorted.length * (p / 100))
    return sorted[index] || 0
  }

  // Reset metrics
  reset(): void {
    this.metrics = {
      renderTime: 0,
      updateCount: 0,
      lastUpdate: new Date(),
      fps: 0,
      memoryUsage: 0,
      dataPointsCount: 0
    }
    this.renderTimes = []
  }

  // Check performance health
  getHealthStatus(): {
    status: 'good' | 'warning' | 'critical'
    issues: string[]
  } {
    const issues: string[] = []

    if (this.metrics.fps < 30) {
      issues.push('Low FPS detected')
    }

    if (this.metrics.renderTime > 16) {
      issues.push('Slow render time')
    }

    if (this.metrics.memoryUsage > 100) {
      issues.push('High memory usage')
    }

    let status: 'good' | 'warning' | 'critical' = 'good'
    if (issues.length >= 2) {
      status = 'critical'
    } else if (issues.length > 0) {
      status = 'warning'
    }

    return { status, issues }
  }
}

// All performance utilities are already exported as individual exports above