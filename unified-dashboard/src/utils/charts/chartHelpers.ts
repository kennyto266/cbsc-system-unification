import { Chart as ChartJS } from 'chart.js'

// Technical indicator calculations
export const calculateSMA = (data: number[], period: number): number[] => {
  const result: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / period)
    }
  }
  return result
}

export const calculateEMA = (data: number[], period: number): number[] => {
  const result: number[] = []
  const multiplier = 2 / (period + 1)

  if (data.length === 0) return result

  // Start with SMA for the first value
  let ema = data.slice(0, period).reduce((sum, val) => sum + val, 0) / period
  result.push(ema)

  for (let i = 1; i < data.length; i++) {
    ema = (data[i] - ema) * multiplier + ema
    result.push(ema)
  }

  return result
}

export const calculateRSI = (data: number[], period: number = 14): number[] => {
  const result: number[] = []
  let gains = 0
  let losses = 0

  // Calculate initial average gains and losses
  for (let i = 1; i <= period; i++) {
    const change = data[i] - data[i - 1]
    if (change > 0) {
      gains += change
    } else {
      losses -= change
    }
  }

  let avgGain = gains / period
  let avgLoss = losses / period
  let rs = avgGain / avgLoss
  result.push(100 - (100 / (1 + rs)))

  // Calculate subsequent RSI values
  for (let i = period + 1; i < data.length; i++) {
    const change = data[i] - data[i - 1]
    avgGain = (avgGain * (period - 1) + (change > 0 ? change : 0)) / period
    avgLoss = (avgLoss * (period - 1) + (change < 0 ? -change : 0)) / period
    rs = avgGain / avgLoss
    result.push(100 - (100 / (1 + rs)))
  }

  return result
}

export const calculateMACD = (
  data: number[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
) => {
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)

  // Align arrays
  const offset = slowPeriod - fastPeriod
  const macdLine = fastEMA.slice(offset).map((val, i) => val - slowEMA[i])

  const signalLine = calculateEMA(macdLine, signalPeriod)
  const histogram = macdLine.slice(signalPeriod - 1).map((val, i) => val - signalLine[i])

  return {
    macdLine,
    signalLine,
    histogram,
  }
}

export const calculateBollingerBands = (
  data: number[],
  period: number = 20,
  stdDev: number = 2
) => {
  const sma = calculateSMA(data, period)
  const upperBand: number[] = []
  const lowerBand: number[] = []

  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1)
    const mean = sma[i - period + 1]

    // Calculate standard deviation
    const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period
    const sd = Math.sqrt(variance)

    upperBand.push(mean + (sd * stdDev))
    lowerBand.push(mean - (sd * stdDev))
  }

  return {
    upperBand,
    middleBand: sma.slice(period - 1),
    lowerBand,
  }
}

export const calculateStochastic = (
  highData: number[],
  lowData: number[],
  closeData: number[],
  kPeriod: number = 14,
  dPeriod: number = 3
) => {
  const kPercent: number[] = []

  for (let i = kPeriod - 1; i < closeData.length; i++) {
    const highestHigh = Math.max(...highData.slice(i - kPeriod + 1, i + 1))
    const lowestLow = Math.min(...lowData.slice(i - kPeriod + 1, i + 1))
    const currentClose = closeData[i]

    const k = ((currentClose - lowestLow) / (highestHigh - lowestLow)) * 100
    kPercent.push(k)
  }

  const dPercent = calculateSMA(kPercent, dPeriod)

  return {
    kPercent,
    dPercent,
  }
}

export const calculateATR = (
  highData: number[],
  lowData: number[],
  closeData: number[],
  period: number = 14
): number[] => {
  const trueRanges: number[] = []
  const atr: number[] = []

  // Calculate True Range for each period
  for (let i = 1; i < highData.length; i++) {
    const high = highData[i]
    const low = lowData[i]
    const prevClose = closeData[i - 1]

    const tr1 = high - low
    const tr2 = Math.abs(high - prevClose)
    const tr3 = Math.abs(low - prevClose)

    trueRanges.push(Math.max(tr1, tr2, tr3))
  }

  // Calculate ATR using exponential moving average
  if (trueRanges.length > 0) {
    // Start with SMA for first ATR value
    const initialATR = trueRanges.slice(0, period).reduce((sum, tr) => sum + tr, 0) / period
    atr.push(initialATR)

    // Use EMA for subsequent values
    const multiplier = 2 / (period + 1)
    for (let i = period; i < trueRanges.length; i++) {
      const newATR = (trueRanges[i] - atr[i - period]) * multiplier + atr[i - period]
      atr.push(newATR)
    }
  }

  return atr
}

// Data transformation utilities
export const transformTimeSeriesData = (data: any[], xKey: string, yKey: string) => {
  return data.map(item => ({
    x: item[xKey],
    y: item[yKey],
  }))
}

export const aggregateTimeSeries = (
  data: Array<{ timestamp: Date; value: number }>,
  interval: 'minute' | 'hour' | 'day' | 'week' | 'month'
) => {
  const aggregated = new Map<string, { sum: number; count: number; values: number[] }>()

  data.forEach(item => {
    const date = new Date(item.timestamp)
    let key: string

    switch (interval) {
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
        const weekStart = new Date(date.setDate(date.getDate() - date.getDay()))
        key = `${weekStart.getFullYear()}-W${Math.ceil((date.getDate() - weekStart.getDate() + 1) / 7)}`
        break
      case 'month':
        key = `${date.getFullYear()}-${date.getMonth()}`
        break
      default:
        key = date.toISOString()
    }

    if (!aggregated.has(key)) {
      aggregated.set(key, { sum: 0, count: 0, values: [] })
    }

    const agg = aggregated.get(key)!
    agg.sum += item.value
    agg.count++
    agg.values.push(item.value)
  })

  return Array.from(aggregated.entries()).map(([key, data]) => ({
    timestamp: new Date(key),
    value: data.sum / data.count,
    high: Math.max(...data.values),
    low: Math.min(...data.values),
    volume: data.count,
  }))
}

export const resampleData = (
  data: Array<{ x: number; y: number }>,
  targetPoints: number
): Array<{ x: number; y: number }> => {
  if (data.length <= targetPoints) return data

  const step = Math.floor(data.length / targetPoints)
  const resampled: Array<{ x: number; y: number }> = []

  for (let i = 0; i < data.length; i += step) {
    resampled.push(data[i])
  }

  // Ensure we include the last point
  if (resampled[resampled.length - 1] !== data[data.length - 1]) {
    resampled.push(data[data.length - 1])
  }

  return resampled
}

// Chart utility functions
export const getChartMinMax = (data: Array<{ x: number; y: number }>) => {
  if (data.length === 0) return { minX: 0, maxX: 0, minY: 0, maxY: 0 }

  const xValues = data.map(d => d.x)
  const yValues = data.map(d => d.y)

  return {
    minX: Math.min(...xValues),
    maxX: Math.max(...xValues),
    minY: Math.min(...yValues),
    maxY: Math.max(...yValues),
  }
}

export const normalizeData = (
  data: Array<{ x: number; y: number }>,
  min: number,
  max: number
): Array<{ x: number; y: number }> => {
  const dataMin = Math.min(...data.map(d => d.y))
  const dataMax = Math.max(...data.map(d => d.y))
  const range = dataMax - dataMin

  if (range === 0) return data

  return data.map(d => ({
    x: d.x,
    y: ((d.y - dataMin) / range) * (max - min) + min,
  }))
}

export const detectOutliers = (
  data: number[],
  threshold: number = 1.5
): { outliers: number[]; cleaned: number[] } => {
  const sorted = [...data].sort((a, b) => a - b)
  const q1 = sorted[Math.floor(sorted.length * 0.25)]
  const q3 = sorted[Math.floor(sorted.length * 0.75)]
  const iqr = q3 - q1
  const lowerBound = q1 - threshold * iqr
  const upperBound = q3 + threshold * iqr

  const outliers: number[] = []
  const cleaned: number[] = []

  data.forEach((value, index) => {
    if (value < lowerBound || value > upperBound) {
      outliers.push(index)
    } else {
      cleaned.push(value)
    }
  })

  return { outliers, cleaned }
}

// Performance utilities
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export const memoize = <T extends (...args: any[]) => any>(func: T): T => {
  const cache = new Map<string, ReturnType<T>>()

  return ((...args: Parameters<T>): ReturnType<T> => {
    const key = JSON.stringify(args)
    if (cache.has(key)) {
      return cache.get(key)!
    }

    const result = func(...args)
    cache.set(key, result)
    return result
  }) as T
}