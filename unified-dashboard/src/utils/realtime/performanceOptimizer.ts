// Performance optimization utilities for real-time charts

export interface PerformanceMetrics {
  frameRate: number
  renderTime: number
  updateCount: number
  memoryUsage: number
  dataPointsCount: number
  lastUpdateTime: number
  averageFrameTime: number
  droppedFrames: number
}

export interface OptimizationOptions {
  targetFPS?: number
  maxDataPoints?: number
  enableThrottling?: boolean
  throttleInterval?: number
  enableBatching?: boolean
  batchSize?: number
  enableVirtualization?: boolean
  virtualChunkSize?: number
  enableCompression?: boolean
  compressionThreshold?: number
}

// Frame rate monitor
export class FrameRateMonitor {
  private frames = 0
  private lastTime = performance.now()
  private fps = 0
  private frameTimeSum = 0
  private frameTimeCount = 0
  private droppedFrames = 0

  // Update frame rate calculation
  update(): number {
    const now = performance.now()
    const delta = now - this.lastTime

    this.frameTimeSum += delta
    this.frameTimeCount++

    // Calculate FPS every second
    if (delta >= 1000) {
      this.fps = Math.round((this.frames * 1000) / delta)
      this.frames = 0
      this.lastTime = now

      // Check for dropped frames
      const averageFrameTime = this.frameTimeSum / this.frameTimeCount
      if (averageFrameTime > 16.67) { // Target 60fps
        this.droppedFrames++
      }

      this.frameTimeSum = 0
      this.frameTimeCount = 0
    }

    this.frames++
    return this.fps
  }

  // Get current metrics
  getMetrics(): { fps: number; averageFrameTime: number; droppedFrames: number } {
    return {
      fps: this.fps,
      averageFrameTime: this.frameTimeCount > 0 ? this.frameTimeSum / this.frameTimeCount : 0,
      droppedFrames: this.droppedFrames
    }
  }

  // Reset metrics
  reset(): void {
    this.frames = 0
    this.lastTime = performance.now()
    this.fps = 0
    this.frameTimeSum = 0
    this.frameTimeCount = 0
    this.droppedFrames = 0
  }
}

// Data throttling utility
export class DataThrottler {
  private lastUpdate = 0
  private pendingUpdates: Array<() => void> = []
  private timer: NodeJS.Timeout | null = null

  constructor(private interval: number) {}

  // Throttle function execution
  throttle(fn: () => void): void {
    const now = performance.now()

    if (now - this.lastUpdate >= this.interval) {
      fn()
      this.lastUpdate = now
    } else {
      // Add to pending queue
      this.pendingUpdates.push(fn)

      if (!this.timer) {
        this.timer = setTimeout(() => {
          // Execute only the latest function
          if (this.pendingUpdates.length > 0) {
            const latestFn = this.pendingUpdates[this.pendingUpdates.length - 1]
            latestFn()
          }

          this.pendingUpdates = []
          this.timer = null
          this.lastUpdate = performance.now()
        }, this.interval - (now - this.lastUpdate))
      }
    }
  }

  // Clear pending updates
  clear(): void {
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
    this.pendingUpdates = []
  }

  // Update interval
  updateInterval(newInterval: number): void {
    this.interval = newInterval
    this.clear()
  }
}

// Data batching utility
export class DataBatcher<T> {
  private batch: T[] = []
  private timer: NodeJS.Timeout | null = null

  constructor(
    private batchSize: number,
    private flushCallback: (batch: T[]) => void,
    private maxWaitTime: number = 100
  ) {}

  // Add item to batch
  add(item: T): void {
    this.batch.push(item)

    if (this.batch.length >= this.batchSize) {
      this.flush()
    } else if (!this.timer) {
      this.timer = setTimeout(() => {
        this.flush()
      }, this.maxWaitTime)
    }
  }

  // Flush current batch
  flush(): void {
    if (this.batch.length > 0) {
      this.flushCallback(this.batch)
      this.batch = []
    }

    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }

  // Get current batch size
  size(): number {
    return this.batch.length
  }

  // Clear batch
  clear(): void {
    this.batch = []
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }
}

// Memory usage monitor
export class MemoryMonitor {
  private measurements: number[] = []
  private maxMeasurements = 100

  // Get current memory usage
  getCurrentUsage(): number {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize
    }
    return 0
  }

  // Record memory measurement
  record(): void {
    const usage = this.getCurrentUsage()
    this.measurements.push(usage)

    if (this.measurements.length > this.maxMeasurements) {
      this.measurements.shift()
    }
  }

  // Get average memory usage
  getAverage(): number {
    if (this.measurements.length === 0) return 0
    return this.measurements.reduce((sum, m) => sum + m, 0) / this.measurements.length
  }

  // Get memory trend
  getTrend(): 'increasing' | 'decreasing' | 'stable' {
    if (this.measurements.length < 10) return 'stable'

    const recent = this.measurements.slice(-5)
    const older = this.measurements.slice(-10, -5)

    const recentAvg = recent.reduce((sum, m) => sum + m, 0) / recent.length
    const olderAvg = older.reduce((sum, m) => sum + m, 0) / older.length

    const change = (recentAvg - olderAvg) / olderAvg

    if (change > 0.1) return 'increasing'
    if (change < -0.1) return 'decreasing'
    return 'stable'
  }

  // Check if memory usage is critical
  isCritical(threshold: number = 0.8): boolean {
    if (!performance.memory) return false
    return performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit > threshold
  }
}

// Virtual scrolling for large datasets
export class VirtualScroller<T> {
  private data: T[] = []
  private visibleStart = 0
  private visibleEnd = 0
  private itemHeight: number
  private containerHeight: number

  constructor(itemHeight: number, containerHeight: number) {
    this.itemHeight = itemHeight
    this.containerHeight = containerHeight
  }

  // Set data
  setData(data: T[]): void {
    this.data = data
    this.updateVisibleRange()
  }

  // Get visible items
  getVisibleItems(scrollTop: number = 0): T[] {
    this.updateVisibleRange(scrollTop)
    return this.data.slice(this.visibleStart, this.visibleEnd)
  }

  // Update visible range based on scroll position
  private updateVisibleRange(scrollTop: number = 0): void {
    const start = Math.floor(scrollTop / this.itemHeight)
    const visibleCount = Math.ceil(this.containerHeight / this.itemHeight)
    const bufferSize = Math.ceil(visibleCount * 0.5) // 50% buffer

    this.visibleStart = Math.max(0, start - bufferSize)
    this.visibleEnd = Math.min(this.data.length, start + visibleCount + bufferSize)
  }

  // Get total height
  getTotalHeight(): number {
    return this.data.length * this.itemHeight
  }

  // Get offset for visible items
  getOffset(): number {
    return this.visibleStart * this.itemHeight
  }

  // Scroll to index
  scrollToIndex(index: number): void {
    const scrollTop = index * this.itemHeight
    // Emit scroll event or update container scroll position
  }
}

// Chart performance optimizer
export class ChartPerformanceOptimizer {
  private frameMonitor = new FrameRateMonitor()
  private memoryMonitor = new MemoryMonitor()
  private throttler: DataThrottler
  private batcher: DataBatcher<any>
  private metrics: PerformanceMetrics
  private options: Required<OptimizationOptions>

  constructor(options: OptimizationOptions = {}) {
    this.options = {
      targetFPS: 60,
      maxDataPoints: 1000,
      enableThrottling: true,
      throttleInterval: 16, // ~60fps
      enableBatching: true,
      batchSize: 100,
      enableVirtualization: false,
      virtualChunkSize: 50,
      enableCompression: false,
      compressionThreshold: 500,
      ...options
    }

    this.throttler = new DataThrottler(this.options.throttleInterval)
    this.batcher = new DataBatcher(
      this.options.batchSize,
      (batch) => this.processBatch(batch),
      100
    )

    this.metrics = {
      frameRate: 0,
      renderTime: 0,
      updateCount: 0,
      memoryUsage: 0,
      dataPointsCount: 0,
      lastUpdateTime: 0,
      averageFrameTime: 0,
      droppedFrames: 0
    }
  }

  // Optimize data update
  optimizeUpdate(updateFn: () => void): void {
    if (this.options.enableThrottling) {
      this.throttler.throttle(() => {
        const startTime = performance.now()
        updateFn()
        const renderTime = performance.now() - startTime

        this.updateMetrics(renderTime)
      })
    } else {
      const startTime = performance.now()
      updateFn()
      const renderTime = performance.now() - startTime

      this.updateMetrics(renderTime)
    }
  }

  // Batch data updates
  batchUpdate(data: any): void {
    if (this.options.enableBatching) {
      this.batcher.add(data)
    } else {
      this.processBatch([data])
    }
  }

  // Process batched data
  private processBatch(batch: any[]): void {
    // Process batched updates together
    console.log(`Processing batch of ${batch.length} items`)
    this.metrics.updateCount++
  }

  // Optimize dataset size
  optimizeDataset(data: any[]): any[] {
    if (data.length <= this.options.maxDataPoints) {
      return data
    }

    // Simple sampling - keep every Nth point
    const samplingRate = Math.ceil(data.length / this.options.maxDataPoints)
    const optimized = []

    for (let i = 0; i < data.length; i += samplingRate) {
      optimized.push(data[i])
    }

    // Always keep the latest point
    if (optimized[optimized.length - 1] !== data[data.length - 1]) {
      optimized.push(data[data.length - 1])
    }

    this.metrics.dataPointsCount = optimized.length
    return optimized
  }

  // Compress data if needed
  compressData(data: any[]): any[] {
    if (!this.options.enableCompression || data.length < this.options.compressionThreshold) {
      return data
    }

    // Simple compression - aggregate multiple points into one
    const compressionRatio = 0.5
    const compressedSize = Math.floor(data.length * compressionRatio)
    const compressed = []

    for (let i = 0; i < compressedSize; i++) {
      const sourceIndex = Math.floor(i * (data.length / compressedSize))
      compressed.push(data[sourceIndex])
    }

    return compressed
  }

  // Update performance metrics
  private updateMetrics(renderTime: number): void {
    const frameMetrics = this.frameMonitor.getMetrics()
    this.memoryMonitor.record()

    this.metrics = {
      frameRate: frameMetrics.fps,
      renderTime,
      updateCount: this.metrics.updateCount + 1,
      memoryUsage: this.memoryMonitor.getCurrentUsage(),
      dataPointsCount: this.metrics.dataPointsCount,
      lastUpdateTime: Date.now(),
      averageFrameTime: frameMetrics.averageFrameTime,
      droppedFrames: frameMetrics.droppedFrames
    }
  }

  // Get current performance metrics
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }

  // Check if performance is degrading
  isPerformanceDegraded(): boolean {
    return (
      this.metrics.frameRate < this.options.targetFPS * 0.8 ||
      this.metrics.averageFrameTime > 16.67 * 1.5 ||
      this.memoryMonitor.isCritical()
    )
  }

  // Auto-adjust performance settings
  autoAdjust(): void {
    if (this.isPerformanceDegraded()) {
      // Reduce update frequency
      if (this.options.enableThrottling) {
        const newInterval = Math.min(this.options.throttleInterval * 1.5, 100)
        this.throttler.updateInterval(newInterval)
      }

      // Reduce batch size
      if (this.options.enableBatching) {
        this.options.batchSize = Math.max(this.options.batchSize * 0.8, 10)
      }

      // Reduce max data points
      this.options.maxDataPoints = Math.max(this.options.maxDataPoints * 0.9, 100)
    }
  }

  // Reset optimizer
  reset(): void {
    this.frameMonitor.reset()
    this.throttler.clear()
    this.batcher.clear()
    this.metrics = {
      frameRate: 0,
      renderTime: 0,
      updateCount: 0,
      memoryUsage: 0,
      dataPointsCount: 0,
      lastUpdateTime: 0,
      averageFrameTime: 0,
      droppedFrames: 0
    }
  }

  // Destroy optimizer
  destroy(): void {
    this.reset()
  }
}

// Performance optimization utilities
export const optimizeChartRendering = (chart: any, options: OptimizationOptions = {}): void => {
  const optimizer = new ChartPerformanceOptimizer(options)

  // Override chart update method
  const originalUpdate = chart.update
  chart.update = function(...args: any[]) {
    optimizer.optimizeUpdate(() => {
      originalUpdate.apply(this, args)
    })
  }

  // Auto-adjust performance
  setInterval(() => {
    optimizer.autoAdjust()
  }, 5000) // Check every 5 seconds
}

// Create performance monitor element
export const createPerformanceMonitor = (optimizer: ChartPerformanceOptimizer): HTMLElement => {
  const monitor = document.createElement('div')
  monitor.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    font-size: 12px;
    z-index: 9999;
  `

  const updateMonitor = () => {
    const metrics = optimizer.getMetrics()
    monitor.innerHTML = `
      FPS: ${metrics.frameRate}
      <br>Frame Time: ${metrics.averageFrameTime.toFixed(2)}ms
      <br>Updates: ${metrics.updateCount}
      <br>Memory: ${(metrics.memoryUsage / 1024 / 1024).toFixed(1)}MB
      <br>Data Points: ${metrics.dataPointsCount}
      <br>Dropped Frames: ${metrics.droppedFrames}
    `
  }

  setInterval(updateMonitor, 500)
  return monitor
}

export default ChartPerformanceOptimizer