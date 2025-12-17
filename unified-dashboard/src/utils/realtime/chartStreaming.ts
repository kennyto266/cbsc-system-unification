import { Chart, ChartConfiguration, ChartType } from 'chart.js'
import { ChartDataPoint } from '../../components/charts/RealTime/RealTimeChartProvider'

// Chart streaming options
export interface ChartStreamingOptions {
  chart: Chart
  maxDataPoints?: number
  updateInterval?: number
  animationDuration?: number
  enableAnimation?: boolean
  bufferSize?: number
  onDataUpdate?: (chart: Chart, data: ChartDataPoint[]) => void
  onBufferOverflow?: (overflowCount: number) => void
}

// Chart streaming data
export interface ChartStreamData {
  timestamp: number
  value: number
  volume?: number
  metadata?: Record<string, any>
}

// Chart streaming buffer
class ChartStreamBuffer {
  private buffer: ChartStreamData[] = []
  private maxSize: number
  private overflowCount = 0

  constructor(maxSize: number = 1000) {
    this.maxSize = maxSize
  }

  // Add data to buffer
  add(data: ChartStreamData): void {
    this.buffer.push(data)

    // Maintain buffer size
    if (this.buffer.length > this.maxSize) {
      const removed = this.buffer.splice(0, this.buffer.length - this.maxSize)
      this.overflowCount += removed.length
    }
  }

  // Get data from buffer
  get(limit?: number): ChartStreamData[] {
    return limit ? this.buffer.slice(-limit) : [...this.buffer]
  }

  // Get latest data point
  getLatest(): ChartStreamData | null {
    return this.buffer.length > 0 ? this.buffer[this.buffer.length - 1] : null
  }

  // Clear buffer
  clear(): void {
    this.buffer = []
    this.overflowCount = 0
  }

  // Get buffer statistics
  getStats(): { size: number; maxSize: number; overflowCount: number } {
    return {
      size: this.buffer.length,
      maxSize: this.maxSize,
      overflowCount: this.overflowCount
    }
  }
}

// Chart streaming manager
export class ChartStreamingManager {
  private chart: Chart
  private options: Required<ChartStreamingOptions>
  private buffer: ChartStreamBuffer
  private updateTimer: NodeJS.Timeout | null = null
  private isRunning = false
  private lastUpdateTime = 0
  private frameId: number | null = null

  constructor(chart: Chart, options: ChartStreamingOptions) {
    this.chart = chart
    this.options = {
      maxDataPoints: 1000,
      updateInterval: 1000,
      animationDuration: 0,
      enableAnimation: false,
      bufferSize: 1000,
      onDataUpdate: () => {},
      onBufferOverflow: () => {},
      ...options
    }

    this.buffer = new ChartStreamBuffer(this.options.bufferSize)
  }

  // Start streaming
  start(): void {
    if (this.isRunning) return

    this.isRunning = true
    this.scheduleUpdate()
  }

  // Stop streaming
  stop(): void {
    this.isRunning = false

    if (this.updateTimer) {
      clearInterval(this.updateTimer)
      this.updateTimer = null
    }

    if (this.frameId) {
      cancelAnimationFrame(this.frameId)
      this.frameId = null
    }
  }

  // Add data point
  addData(data: ChartStreamData | ChartDataPoint): void {
    const streamData: ChartStreamData = {
      timestamp: data instanceof Date ? data.getTime() : data.timestamp,
      value: (data as any).value || (data as any).close || 0,
      volume: (data as any).volume,
      metadata: (data as any).metadata
    }

    this.buffer.add(streamData)
    this.options.onDataUpdate(this.chart, this.buffer.get() as ChartDataPoint[])

    // Handle buffer overflow
    const stats = this.buffer.getStats()
    if (stats.overflowCount > 0) {
      this.options.onBufferOverflow(stats.overflowCount)
    }
  }

  // Add multiple data points
  addDataPoints(dataPoints: (ChartStreamData | ChartDataPoint)[]): void {
    dataPoints.forEach(point => this.addData(point))
  }

  // Schedule next update
  private scheduleUpdate(): void {
    if (!this.isRunning) return

    const now = Date.now()
    const timeSinceLastUpdate = now - this.lastUpdateTime

    if (timeSinceLastUpdate >= this.options.updateInterval) {
      this.updateChart()
      this.lastUpdateTime = now
    }

    // Use requestAnimationFrame for smooth updates
    this.frameId = requestAnimationFrame(() => {
      this.updateTimer = setTimeout(() => this.scheduleUpdate(), 16) // ~60fps
    })
  }

  // Update chart with buffered data
  private updateChart(): void {
    const data = this.buffer.get(this.options.maxDataPoints)

    if (data.length === 0) return

    // Update chart data
    this.chart.data.labels = data.map(d => d.timestamp)

    // Update each dataset
    this.chart.data.datasets.forEach((dataset, index) => {
      if (index === 0) {
        // Primary dataset - price data
        dataset.data = data.map(d => ({
          x: d.timestamp,
          y: d.value
        }))
      } else if (index === 1 && data[0]?.volume) {
        // Secondary dataset - volume data
        dataset.data = data.map(d => ({
          x: d.timestamp,
          y: d.volume || 0
        }))
      }
    })

    // Update chart with minimal animation for real-time feel
    const updateMode = this.options.enableAnimation ? 'default' : 'none'
    this.chart.update(updateMode)
  }

  // Get current buffer data
  getBufferData(): ChartStreamData[] {
    return this.buffer.get()
  }

  // Get latest data point
  getLatestData(): ChartStreamData | null {
    return this.buffer.getLatest()
  }

  // Clear buffer and chart
  clear(): void {
    this.buffer.clear()
    this.chart.data.labels = []
    this.chart.data.datasets.forEach(dataset => {
      dataset.data = []
    })
    this.chart.update('none')
  }

  // Update streaming options
  updateOptions(newOptions: Partial<ChartStreamingOptions>): void {
    this.options = { ...this.options, ...newOptions }

    // Update buffer size if changed
    if (newOptions.bufferSize && newOptions.bufferSize !== this.buffer.getStats().maxSize) {
      this.buffer = new ChartStreamBuffer(newOptions.bufferSize)
    }
  }

  // Get streaming statistics
  getStats(): {
    isRunning: boolean
    lastUpdateTime: number
    bufferStats: { size: number; maxSize: number; overflowCount: number }
    updateInterval: number
    dataPointsPerSecond: number
  } {
    const bufferStats = this.buffer.getStats()
    const dataPointsPerSecond = bufferStats.size > 0 ?
      1000 / ((Date.now() - this.lastUpdateTime) || 1) : 0

    return {
      isRunning: this.isRunning,
      lastUpdateTime: this.lastUpdateTime,
      bufferStats,
      updateInterval: this.options.updateInterval,
      dataPointsPerSecond
    }
  }

  // Destroy streaming manager
  destroy(): void {
    this.stop()
    this.buffer.clear()
  }
}

// Utility functions for chart streaming

// Create streaming configuration for different chart types
export const createStreamingConfig = (
  type: ChartType,
  options: Partial<ChartStreamingOptions> = {}
): ChartConfiguration => {
  const baseConfig: ChartConfiguration = {
    type: type === 'candlestick' ? 'line' : type,
    data: {
      labels: [],
      datasets: [{
        label: 'Price',
        data: [],
        borderColor: '#3B82F6',
        backgroundColor: type === 'line' ? 'rgba(59, 130, 246, 0.1)' : '#3B82F6',
        borderWidth: 2,
        fill: type === 'line',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4
      }]
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      animation: false, // Disable animation for streaming
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MM/dd'
            }
          },
          ticks: {
            maxRotation: 0
          }
        },
        y: {
          position: 'right'
        }
      },
      elements: {
        point: {
          radius: 0,
          hoverRadius: 4
        }
      }
    }
  }

  // Add volume dataset for certain chart types
  if (['line', 'bar'].includes(type)) {
    baseConfig.data!.datasets!.push({
      label: 'Volume',
      data: [],
      borderColor: '#10B981',
      backgroundColor: 'rgba(16, 185, 129, 0.5)',
      borderWidth: 1,
      fill: true,
      yAxisID: 'y1',
      pointRadius: 0,
      pointHoverRadius: 3
    })

    // Add second y-axis for volume
    if (baseConfig.options?.scales) {
      baseConfig.options.scales.y1 = {
        type: 'linear',
        display: true,
        position: 'left',
        grid: {
          drawOnChartArea: false
        }
      }
    }
  }

  return baseConfig
}

// Batch data updates for performance
export const batchDataUpdates = (
  chart: Chart,
  updates: Array<{ datasetIndex: number; data: any[] }>,
  updateMode: 'none' | 'default' = 'none'
): void => {
  updates.forEach(({ datasetIndex, data }) => {
    if (chart.data.datasets[datasetIndex]) {
      chart.data.datasets[datasetIndex].data = data
    }
  })

  chart.update(updateMode)
}

// Throttled update function
export const createThrottledUpdate = (
  chart: Chart,
  interval: number = 16 // ~60fps
): (() => void) => {
  let lastUpdate = 0
  let pendingUpdate = false

  return () => {
    const now = Date.now()

    if (now - lastUpdate >= interval) {
      chart.update('none')
      lastUpdate = now
      pendingUpdate = false
    } else if (!pendingUpdate) {
      pendingUpdate = true
      setTimeout(() => {
        if (pendingUpdate) {
          chart.update('none')
          lastUpdate = Date.now()
          pendingUpdate = false
        }
      }, interval - (now - lastUpdate))
    }
  }
}

export default ChartStreamingManager