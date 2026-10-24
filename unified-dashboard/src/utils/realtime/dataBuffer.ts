// Generic data buffer for real-time data management
export interface DataBufferOptions {
  maxSize: number
  enableCompression?: boolean
  compressionThreshold?: number
  enableDeduplication?: boolean
  deduplicationKey?: string
  enablePersistence?: boolean
  persistenceKey?: string
}

export interface BufferStats {
  size: number
  maxSize: number
  memoryUsage: number
  compressionRatio: number
  deduplicationHits: number
  overflowCount: number
}

export interface DataPoint<T = any> {
  timestamp: number
  data: T
  id?: string
  sequence?: number
}

// Circular buffer implementation for efficient memory usage
class CircularBuffer<T> {
  private buffer: (DataPoint<T> | null)[]
  private head = 0
  private tail = 0
  private size = 0
  private maxSize: number

  constructor(maxSize: number) {
    this.maxSize = maxSize
    this.buffer = new Array(maxSize).fill(null)
  }

  // Add item to buffer
  push(item: DataPoint<T>): void {
    this.buffer[this.tail] = item
    this.tail = (this.tail + 1) % this.maxSize

    if (this.size < this.maxSize) {
      this.size++
    } else {
      this.head = (this.head + 1) % this.maxSize
    }
  }

  // Get item at index
  get(index: number): DataPoint<T> | null {
    if (index >= this.size) return null
    const actualIndex = (this.head + index) % this.maxSize
    return this.buffer[actualIndex]
  }

  // Get all items
  getAll(): DataPoint<T>[] {
    const result: DataPoint<T>[] = []
    for (let i = 0; i < this.size; i++) {
      const item = this.get(i)
      if (item) result.push(item)
    }
    return result
  }

  // Get latest N items
  getLatest(count: number): DataPoint<T>[] {
    const result: DataPoint<T>[] = []
    const start = Math.max(0, this.size - count)
    for (let i = start; i < this.size; i++) {
      const item = this.get(i)
      if (item) result.push(item)
    }
    return result
  }

  // Clear buffer
  clear(): void {
    this.buffer.fill(null)
    this.head = 0
    this.tail = 0
    this.size = 0
  }

  // Get buffer size
  getSize(): number {
    return this.size
  }

  // Check if buffer is full
  isFull(): boolean {
    return this.size === this.maxSize
  }
}

// Real-time data buffer with advanced features
export class RealTimeDataBuffer<T = any> {
  private buffer: CircularBuffer<T>
  private options: Required<DataBufferOptions>
  private deduplicationCache = new Map<string, boolean>()
  private compressionStats = { original: 0, compressed: 0 }
  private overflowCount = 0
  private sequenceCounter = 0

  constructor(options: DataBufferOptions) {
    this.options = {
      enableCompression: false,
      compressionThreshold: 100,
      enableDeduplication: false,
      deduplicationKey: 'id',
      enablePersistence: false,
      persistenceKey: 'rt-buffer',
      ...options
    }

    this.buffer = new CircularBuffer<T>(this.options.maxSize)

    // Load from persistence if enabled
    if (this.options.enablePersistence) {
      this.loadFromPersistence()
    }
  }

  // Add data point to buffer
  add(data: T): void {
    const dataPoint: DataPoint<T> = {
      timestamp: Date.now(),
      data,
      sequence: ++this.sequenceCounter
    }

    // Check deduplication
    if (this.options.enableDeduplication) {
      const dedupKey = (data as any)[this.options.deduplicationKey]
      if (dedupKey && this.deduplicationCache.has(dedupKey)) {
        return // Skip duplicate
      }
      if (dedupKey) {
        this.deduplicationCache.set(dedupKey, true)
        // Limit cache size
        if (this.deduplicationCache.size > 1000) {
          const firstKey = this.deduplicationCache.keys().next().value
          this.deduplicationCache.delete(firstKey)
        }
      }
    }

    // Add to buffer
    this.buffer.push(dataPoint)

    // Track overflow
    if (this.buffer.isFull() && this.buffer.getSize() === this.options.maxSize) {
      this.overflowCount++
    }

    // Auto-compression
    if (this.options.enableCompression && this.buffer.getSize() >= this.options.compressionThreshold) {
      this.compress()
    }

    // Persist if enabled
    if (this.options.enablePersistence) {
      this.saveToPersistence()
    }
  }

  // Get data point by index
  get(index: number): DataPoint<T> | null {
    return this.buffer.get(index)
  }

  // Get all data points
  getAll(): DataPoint<T>[] {
    return this.buffer.getAll()
  }

  // Get latest N data points
  getLatest(count: number): DataPoint<T>[] {
    return this.buffer.getLatest(count)
  }

  // Get data points in time range
  getInRange(startTime: number, endTime: number): DataPoint<T>[] {
    const all = this.getAll()
    return all.filter(point =>
      point.timestamp >= startTime && point.timestamp <= endTime
    )
  }

  // Get latest data point
  getLatest(): DataPoint<T> | null {
    const latest = this.getLatest(1)
    return latest.length > 0 ? latest[0] : null
  }

  // Clear buffer
  clear(): void {
    this.buffer.clear()
    this.deduplicationCache.clear()
    this.compressionStats = { original: 0, compressed: 0 }
    this.overflowCount = 0
    this.sequenceCounter = 0

    if (this.options.enablePersistence) {
      this.saveToPersistence()
    }
  }

  // Compress old data points
  compress(): void {
    const all = this.getAll()
    if (all.length < 2) return

    // Simple compression: keep every Nth point for older data
    const compressionRatio = 0.5
    const compressedSize = Math.floor(all.length * compressionRatio)
    const keepCount = compressedSize

    // Keep the most recent points and sample older ones
    const recent = all.slice(-keepCount)
    const older = all.slice(0, -keepCount)
    const sampledOlder = older.filter((_, index) => index % 2 === 0)

    const compressed = [...sampledOlder, ...recent]

    // Update buffer with compressed data
    this.buffer.clear()
    compressed.forEach(point => this.buffer.push(point))

    // Update compression stats
    this.compressionStats.original = all.length
    this.compressionStats.compressed = compressed.length
  }

  // Get buffer statistics
  getStats(): BufferStats {
    const dataSize = JSON.stringify(this.getAll()).length
    const compressionRatio = this.compressionStats.original > 0 ?
      this.compressionStats.compressed / this.compressionStats.original : 1

    return {
      size: this.buffer.getSize(),
      maxSize: this.options.maxSize,
      memoryUsage: dataSize,
      compressionRatio,
      deduplicationHits: this.deduplicationCache.size,
      overflowCount: this.overflowCount
    }
  }

  // Update buffer options
  updateOptions(newOptions: Partial<DataBufferOptions>): void {
    this.options = { ...this.options, ...newOptions }

    // Recreate buffer if max size changed
    if (newOptions.maxSize && newOptions.maxSize !== this.options.maxSize) {
      const data = this.getAll()
      this.buffer = new CircularBuffer<T>(newOptions.maxSize)
      data.forEach(point => this.buffer.push(point))
    }
  }

  // Save to localStorage
  private saveToPersistence(): void {
    if (!this.options.enablePersistence) return

    try {
      const data = {
        buffer: this.getAll(),
        sequenceCounter: this.sequenceCounter,
        timestamp: Date.now()
      }
      localStorage.setItem(this.options.persistenceKey, JSON.stringify(data))
    } catch (err) {
      console.warn('Failed to save buffer to persistence:', err)
    }
  }

  // Load from localStorage
  private loadFromPersistence(): void {
    if (!this.options.enablePersistence) return

    try {
      const persisted = localStorage.getItem(this.options.persistenceKey)
      if (persisted) {
        const data = JSON.parse(persisted)

        // Check if data is not too old (e.g., older than 1 hour)
        const oneHour = 60 * 60 * 1000
        if (Date.now() - data.timestamp < oneHour) {
          this.sequenceCounter = data.sequenceCounter || 0
          data.buffer.forEach((point: DataPoint<T>) => {
            this.buffer.push(point)
          })
        }
      }
    } catch (err) {
      console.warn('Failed to load buffer from persistence:', err)
    }
  }

  // Export data for analysis
  export(format: 'json' | 'csv' = 'json'): string {
    const data = this.getAll()

    if (format === 'json') {
      return JSON.stringify(data, null, 2)
    } else if (format === 'csv') {
      if (data.length === 0) return ''

      const headers = Object.keys(data[0].data)
      const csv = [
        'timestamp,sequence,' + headers.join(','),
        ...data.map(point =>
          `${point.timestamp},${point.sequence},${headers.map(h =>
            JSON.stringify((point.data as any)[h])
          ).join(',')}`
        )
      ].join('\n')

      return csv
    }

    return ''
  }

  // Import data from external source
  import(data: DataPoint<T>[]): void {
    data.forEach(point => {
      this.buffer.push(point)
    })
  }

  // Destroy buffer and clean up
  destroy(): void {
    this.clear()
    if (this.options.enablePersistence) {
      localStorage.removeItem(this.options.persistenceKey)
    }
  }
}

// Factory function to create typed buffer
export function createDataBuffer<T>(
  options: DataBufferOptions
): RealTimeDataBuffer<T> {
  return new RealTimeDataBuffer<T>(options)
}

// Buffer pool for reusing buffers
export class BufferPool<T> {
  private pool: RealTimeDataBuffer<T>[] = []
  private factory: (options: DataBufferOptions) => RealTimeDataBuffer<T>

  constructor(
    factory: (options: DataBufferOptions) => RealTimeDataBuffer<T>,
    private poolSize = 5
  ) {
    this.factory = factory
  }

  // Acquire buffer from pool
  acquire(options: DataBufferOptions): RealTimeDataBuffer<T> {
    if (this.pool.length > 0) {
      const buffer = this.pool.pop()!
      buffer.updateOptions(options)
      return buffer
    }
    return this.factory(options)
  }

  // Release buffer back to pool
  release(buffer: RealTimeDataBuffer<T>): void {
    if (this.pool.length < this.poolSize) {
      buffer.clear()
      this.pool.push(buffer)
    } else {
      buffer.destroy()
    }
  }

  // Clear pool
  clear(): void {
    this.pool.forEach(buffer => buffer.destroy())
    this.pool = []
  }
}

export default RealTimeDataBuffer