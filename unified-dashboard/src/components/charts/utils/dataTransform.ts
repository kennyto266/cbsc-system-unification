import { TimeSeriesDataPoint } from '../types/chart.types'
import { DataUtils, ChartUtils } from './chartUtils'

// Data transformation configurations
export interface TransformationConfig {
  type: 'normalize' | 'smooth' | 'resample' | 'aggregate' | 'derivative' | 'cumulative'
  params?: Record<string, any>
}

// Data transformer class
export class DataTransformer {
  // Main transformation method
  static transform(
    data: TimeSeriesDataPoint[],
    transformations: TransformationConfig[]
  ): TimeSeriesDataPoint[] {
    let transformed = [...data]

    for (const transform of transformations) {
      transformed = this.applyTransformation(transformed, transform)
    }

    return transformed
  }

  // Apply single transformation
  private static applyTransformation(
    data: TimeSeriesDataPoint[],
    config: TransformationConfig
  ): TimeSeriesDataPoint[] {
    switch (config.type) {
      case 'normalize':
        return this.normalize(data, config.params)
      case 'smooth':
        return this.smooth(data, config.params)
      case 'resample':
        return this.resample(data, config.params)
      case 'aggregate':
        return this.aggregate(data, config.params)
      case 'derivative':
        return this.derivative(data)
      case 'cumulative':
        return this.cumulative(data)
      default:
        return data
    }
  }

  // Normalize data
  static normalize(
    data: TimeSeriesDataPoint[],
    params: { method?: 'minmax' | 'zscore' } = {}
  ): TimeSeriesDataPoint[] {
    const method = params.method || 'minmax'
    const values = data.map(d => d.value)

    let normalized: number[]

    if (method === 'minmax') {
      normalized = DataUtils.normalize(values)
    } else if (method === 'zscore') {
      const mean = values.reduce((a, b) => a + b, 0) / values.length
      const std = Math.sqrt(
        values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length
      )
      normalized = values.map(v => (v - mean) / std)
    } else {
      throw new Error(`Unknown normalization method: ${method}`)
    }

    return data.map((point, index) => ({
      ...point,
      value: normalized[index]
    }))
  }

  // Smooth data using moving average
  static smooth(
    data: TimeSeriesDataPoint[],
    params: { window?: number; method?: 'simple' | 'exponential' } = {}
  ): TimeSeriesDataPoint[] {
    const window = params.window || 5
    const method = params.method || 'simple'

    const values = data.map(d => d.value)
    let smoothed: number[]

    if (method === 'simple') {
      smoothed = DataUtils.movingAverage(values, window)
    } else if (method === 'exponential') {
      smoothed = this.exponentialMovingAverage(values, window)
    } else {
      throw new Error(`Unknown smoothing method: ${method}`)
    }

    return data.map((point, index) => ({
      ...point,
      value: smoothed[index] || point.value
    }))
  }

  // Exponential moving average
  private static exponentialMovingAverage(data: number[], period: number): number[] {
    const result: number[] = []
    const multiplier = 2 / (period + 1)

    if (data.length === 0) return result

    result[0] = data[0]
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    }

    return result
  }

  // Resample data to different intervals
  static resample(
    data: TimeSeriesDataPoint[],
    params: { interval: number; method?: 'average' | 'sum' | 'first' | 'last' }
  ): TimeSeriesDataPoint[] {
    const interval = params.interval
    const method = params.method || 'average'

    return DataUtils.resampleTimeSeries(data, interval).map(point => {
      // Apply resampling method
      if (method === 'sum' && point.value !== undefined) {
        // For sum, we need to recalculate based on original data
        const originalPoints = data.filter(p => {
          const pTime = new Date(p.timestamp).getTime()
          const pointTime = new Date(point.timestamp).getTime()
          return pTime >= pointTime && pTime < pointTime + interval
        })

        if (originalPoints.length > 0) {
          point.value = originalPoints.reduce((sum, p) => sum + (p.value || 0), 0)
          point.volume = originalPoints.reduce((sum, p) => sum + (p.volume || 0), 0)
        }
      }

      return point
    })
  }

  // Aggregate data by time period
  static aggregate(
    data: TimeSeriesDataPoint[],
    params: { period: 'minute' | 'hour' | 'day' | 'week' | 'month'; method?: 'average' | 'sum' | 'min' | 'max' }
  ): TimeSeriesDataPoint[] {
    const period = params.period
    const method = params.method || 'average'

    const aggregated = DataUtils.aggregateByPeriod(data, period)

    if (method === 'sum') {
      // Recalculate for sum method
      const grouped = new Map<string, TimeSeriesDataPoint[]>()

      data.forEach(point => {
        const date = new Date(point.timestamp)
        let key: string

        switch (period) {
          case 'minute':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}-${date.getMinutes()}`
            break
          case 'hour':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`
            break
          case 'day':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
            break
          case 'week':
            const weekStart = new Date(date)
            weekStart.setDate(date.getDate() - date.getDay())
            key = `${weekStart.getFullYear()}-W${Math.floor(weekStart.getTime() / (7 * 24 * 60 * 60 * 1000))}`
            break
          case 'month':
            key = `${date.getFullYear()}-${date.getMonth()}`
            break
        }

        if (!grouped.has(key)) {
          grouped.set(key, [])
        }
        grouped.get(key)!.push(point)
      })

      return Array.from(grouped.entries()).map(([key, points]) => ({
        timestamp: new Date(key),
        value: points.reduce((sum, p) => sum + p.value, 0),
        volume: points.reduce((sum, p) => sum + (p.volume || 0), 0)
      })).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    } else if (method === 'min' || method === 'max') {
      // Recalculate for min/max
      const grouped = new Map<string, TimeSeriesDataPoint[]>()

      data.forEach(point => {
        const date = new Date(point.timestamp)
        let key: string

        switch (period) {
          case 'minute':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}-${date.getMinutes()}`
            break
          case 'hour':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`
            break
          case 'day':
            key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
            break
          case 'week':
            const weekStart = new Date(date)
            weekStart.setDate(date.getDate() - date.getDay())
            key = `${weekStart.getFullYear()}-W${Math.floor(weekStart.getTime() / (7 * 24 * 60 * 60 * 1000))}`
            break
          case 'month':
            key = `${date.getFullYear()}-${date.getMonth()}`
            break
        }

        if (!grouped.has(key)) {
          grouped.set(key, [])
        }
        grouped.get(key)!.push(point)
      })

      return Array.from(grouped.entries()).map(([key, points]) => {
        const values = points.map(p => p.value)
        const value = method === 'min' ? Math.min(...values) : Math.max(...values)

        return {
          timestamp: new Date(key),
          value,
          volume: points.reduce((sum, p) => sum + (p.volume || 0), 0)
        }
      }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }

    return aggregated
  }

  // Calculate derivative (rate of change)
  static derivative(data: TimeSeriesDataPoint[]): TimeSeriesDataPoint[] {
    if (data.length < 2) return []

    const derivative: TimeSeriesDataPoint[] = []

    for (let i = 1; i < data.length; i++) {
      const prev = data[i - 1]
      const curr = data[i]

      const prevTime = new Date(prev.timestamp).getTime()
      const currTime = new Date(curr.timestamp).getTime()
      const timeDiff = (currTime - prevTime) / 1000 // Convert to seconds

      if (timeDiff > 0) {
        const rateOfChange = (curr.value - prev.value) / timeDiff
        derivative.push({
          ...curr,
          value: rateOfChange,
          metadata: {
            ...curr.metadata,
            originalValue: curr.value,
            timeDiff
          }
        })
      }
    }

    return derivative
  }

  // Calculate cumulative sum
  static cumulative(data: TimeSeriesDataPoint[]): TimeSeriesDataPoint[] {
    const cumulative: TimeSeriesDataPoint[] = []
    let sum = 0

    for (const point of data) {
      sum += point.value
      cumulative.push({
        ...point,
        value: sum,
        metadata: {
          ...point.metadata,
          incrementalValue: point.value
        }
      })
    }

    return cumulative
  }

  // Fill missing data points
  static fillMissing(
    data: TimeSeriesDataPoint[],
    params: { method?: 'linear' | 'forward' | 'backward' | 'zero'; interval?: number }
  ): TimeSeriesDataPoint[] {
    const method = params.method || 'linear'
    const interval = params.interval || 60000 // Default to 1 minute

    if (data.length < 2) return data

    const filled: TimeSeriesDataPoint[] = [data[0]]

    for (let i = 1; i < data.length; i++) {
      const prev = data[i - 1]
      const curr = data[i]

      const prevTime = new Date(prev.timestamp).getTime()
      const currTime = new Date(curr.timestamp).getTime()

      filled.push(curr)

      // Check for gaps
      if (currTime - prevTime > interval) {
        let fillTime = prevTime + interval

        while (fillTime < currTime) {
          let fillValue: number

          switch (method) {
            case 'linear':
              const ratio = (fillTime - prevTime) / (currTime - prevTime)
              fillValue = prev.value + (curr.value - prev.value) * ratio
              break
            case 'forward':
              fillValue = prev.value
              break
            case 'backward':
              fillValue = curr.value
              break
            case 'zero':
            default:
              fillValue = 0
              break
          }

          filled.push({
            timestamp: new Date(fillTime),
            value: fillValue,
            metadata: {
              filled: true,
              fillMethod: method
            }
          })

          fillTime += interval
        }
      }
    }

    return filled.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  }

  // Remove outliers
  static removeOutliers(
    data: TimeSeriesDataPoint[],
    params: { method?: 'iqr' | 'zscore'; threshold?: number }
  ): TimeSeriesDataPoint[] {
    const method = params.method || 'iqr'
    const threshold = params.threshold || 3

    if (method === 'iqr') {
      const { indices } = DataUtils.findOutliers(data.map(d => d.value))
      return data.filter((_, index) => !indices.includes(index))
    } else if (method === 'zscore') {
      const values = data.map(d => d.value)
      const mean = values.reduce((a, b) => a + b, 0) / values.length
      const std = Math.sqrt(
        values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length
      )

      return data.filter(point => {
        const zscore = Math.abs((point.value - mean) / std)
        return zscore <= threshold
      })
    }

    return data
  }

  // Clip data to range
  static clip(
    data: TimeSeriesDataPoint[],
    params: { min?: number; max?: number }
  ): TimeSeriesDataPoint[] {
    const { min, max } = params

    return data.map(point => ({
      ...point,
      value: Math.max(min || point.value, Math.min(max || point.value, point.value))
    }))
  }
}

// Export transformer utilities
export const transformData = DataTransformer.transform
export const normalizeData = DataTransformer.normalize
export const smoothData = DataTransformer.smooth
export const resampleData = DataTransformer.resample
export const aggregateData = DataTransformer.aggregate
export const derivativeData = DataTransformer.derivative
export const cumulativeData = DataTransformer.cumulative
export const fillMissingData = DataTransformer.fillMissing
export const removeOutliers = DataTransformer.removeOutliers
export const clipData = DataTransformer.clip