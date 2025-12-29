// Chart utility functions for data visualization

export interface ChartDataPoint {
  x: number | string | Date
  y: number
  label?: string
  color?: string
}

export interface TimeSeriesData {
  timestamp: Date | number | string
  value: number
  volume?: number
}

// Data transformation utilities
export const transformTimeSeriesData = (
  data: any[],
  xField: string,
  yField: string,
  dateFormat?: string
): ChartDataPoint[] => {
  return data.map(item => ({
    x: item[xField],
    y: item[yField],
    label: item.label || ''
  }))
}

export const aggregateTimeSeries = (
  data: TimeSeriesData[],
  interval: 'minute' | 'hour' | 'day' | 'week' | 'month'
): TimeSeriesData[] => {
  if (data.length === 0) return []

  const intervalMs = {
    minute: 60 * 1000,
    hour: 60 * 60 * 1000,
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000
  }[interval]

  const aggregated = new Map<number, { sum: number; count: number; volume: number }>()

  data.forEach(point => {
    const timestamp = new Date(point.timestamp).getTime()
    const bucketStart = Math.floor(timestamp / intervalMs) * intervalMs

    if (!aggregated.has(bucketStart)) {
      aggregated.set(bucketStart, { sum: 0, count: 0, volume: 0 })
    }

    const bucket = aggregated.get(bucketStart)!
    bucket.sum += point.value
    bucket.count += 1
    bucket.volume += point.volume || 0
  })

  return Array.from(aggregated.entries()).map(([timestamp, data]) => ({
    timestamp: new Date(timestamp),
    value: data.sum / data.count,
    volume: data.volume
  })).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
}

export const resampleData = (
  data: ChartDataPoint[],
  maxPoints: number,
  method: 'average' | 'max' | 'min' | 'first' | 'last' = 'average'
): ChartDataPoint[] => {
  if (data.length <= maxPoints) return data

  const step = Math.ceil(data.length / maxPoints)
  const resampled: ChartDataPoint[] = []

  for (let i = 0; i < data.length; i += step) {
    const bucket = data.slice(i, i + step)

    let yValue: number
    switch (method) {
      case 'average':
        yValue = bucket.reduce((sum, p) => sum + p.y, 0) / bucket.length
        break
      case 'max':
        yValue = Math.max(...bucket.map(p => p.y))
        break
      case 'min':
        yValue = Math.min(...bucket.map(p => p.y))
        break
      case 'first':
        yValue = bucket[0].y
        break
      case 'last':
        yValue = bucket[bucket.length - 1].y
        break
      default:
        yValue = bucket[0].y
    }

    resampled.push({
      x: bucket[Math.floor(bucket.length / 2)].x,
      y: yValue,
      label: bucket[Math.floor(bucket.length / 2)].label
    })
  }

  return resampled
}

// Statistical utilities
export const calculateMovingAverage = (
  data: number[],
  window: number,
  method: 'simple' | 'exponential' = 'simple'
): number[] => {
  if (method === 'simple') {
    const result: number[] = []
    for (let i = window - 1; i < data.length; i++) {
      const sum = data.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / window)
    }
    return result
  } else {
    // Exponential moving average
    const result: number[] = []
    const multiplier = 2 / (window + 1)
    let ema = data[0]
    result.push(ema)

    for (let i = 1; i < data.length; i++) {
      ema = (data[i] - ema) * multiplier + ema
      result.push(ema)
    }
    return result
  }
}

export const calculateStandardDeviation = (data: number[]): number => {
  const mean = data.reduce((sum, val) => sum + val, 0) / data.length
  const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length
  return Math.sqrt(variance)
}

export const calculatePercentiles = (
  data: number[],
  percentiles: number[]
): Record<string, number> => {
  const sorted = [...data].sort((a, b) => a - b)
  const result: Record<string, number> = {}

  percentiles.forEach(p => {
    const index = (p / 100) * (sorted.length - 1)
    const lower = Math.floor(index)
    const upper = Math.ceil(index)
    const weight = index % lower

    if (lower === upper) {
      result[`p${p}`] = sorted[lower]
    } else {
      result[`p${p}`] = sorted[lower] * (1 - weight) + sorted[upper] * weight
    }
  })

  return result
}

export const detectOutliers = (
  data: number[],
  method: 'iqr' | 'zscore' = 'iqr',
  threshold: number = 1.5
): { indices: number[]; values: number[] } => {
  const indices: number[] = []
  const values: number[] = []

  if (method === 'iqr') {
    const sorted = [...data].sort((a, b) => a - b)
    const q1 = sorted[Math.floor(sorted.length * 0.25)]
    const q3 = sorted[Math.floor(sorted.length * 0.75)]
    const iqr = q3 - q1
    const lowerBound = q1 - threshold * iqr
    const upperBound = q3 + threshold * iqr

    data.forEach((value, index) => {
      if (value < lowerBound || value > upperBound) {
        indices.push(index)
        values.push(value)
      }
    })
  } else {
    // Z-score method
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length
    const stdDev = calculateStandardDeviation(data)

    data.forEach((value, index) => {
      const zscore = Math.abs((value - mean) / stdDev)
      if (zscore > threshold) {
        indices.push(index)
        values.push(value)
      }
    })
  }

  return { indices, values }
}

// Color utilities
export const generateColorPalette = (
  baseColor: string,
  count: number,
  variation: 'lightness' | 'hue' | 'saturation' = 'lightness'
): string[] => {
  const colors: string[] = []

  if (variation === 'lightness') {
    // Vary lightness
    for (let i = 0; i < count; i++) {
      const hsl = hexToHsl(baseColor)
      hsl.l = 0.2 + (0.6 * i) / (count - 1) // Range from 20% to 80%
      colors.push(hslToHex(hsl))
    }
  } else if (variation === 'hue') {
    // Vary hue
    for (let i = 0; i < count; i++) {
      const hsl = hexToHsl(baseColor)
      hsl.h = (hsl.h + (360 * i) / count) % 360
      colors.push(hslToHex(hsl))
    }
  } else {
    // Vary saturation
    for (let i = 0; i < count; i++) {
      const hsl = hexToHsl(baseColor)
      hsl.s = 0.3 + (0.7 * i) / (count - 1) // Range from 30% to 100%
      colors.push(hslToHex(hsl))
    }
  }

  return colors
}

const hexToHsl = (hex: string): { h: number; s: number; l: number } => {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
    }
  }

  return { h: h * 360, s, l }
}

const hslToHex = (hsl: { h: number; s: number; l: number }): string => {
  const h = hsl.h / 360
  const s = hsl.s
  const l = hsl.l

  const hue2rgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1/6) return p + (q - p) * 6 * t
    if (t < 1/2) return q
    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
    return p
  }

  let r, g, b

  if (s === 0) {
    r = g = b = l
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
  }

  const toHex = (x: number) => {
    const hex = Math.round(x * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

// Format utilities
export const formatNumber = (
  value: number,
  options: {
    decimals?: number
    prefix?: string
    suffix?: string
    thousandsSeparator?: string
    abbreviate?: boolean
  } = {}
): string => {
  const {
    decimals = 2,
    prefix = '',
    suffix = '',
    thousandsSeparator = ',',
    abbreviate = false
  } = options

  let formattedValue: string

  if (abbreviate) {
    const abs = Math.abs(value)
    if (abs >= 1e9) {
      formattedValue = (value / 1e9).toFixed(decimals) + 'B'
    } else if (abs >= 1e6) {
      formattedValue = (value / 1e6).toFixed(decimals) + 'M'
    } else if (abs >= 1e3) {
      formattedValue = (value / 1e3).toFixed(decimals) + 'K'
    } else {
      formattedValue = value.toFixed(decimals)
    }
  } else {
    formattedValue = value.toFixed(decimals)
  }

  // Add thousands separator
  if (!abbreviate) {
    const parts = formattedValue.split('.')
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator)
    formattedValue = parts.join('.')
  }

  return prefix + formattedValue + suffix
}

export const formatPercentage = (
  value: number,
  decimals: number = 2,
  showSign: boolean = false
): string => {
  const formatted = formatNumber(value * 100, { decimals })
  const sign = showSign && value > 0 ? '+' : ''
  return `${sign}${formatted}%`
}

export const formatDate = (
  date: Date | number | string,
  format: string = 'YYYY-MM-DD'
): string => {
  const d = new Date(date)

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

// Performance utilities
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let lastCall = 0

  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      func(...args)
    }
  }
}

export const memoize = <T extends (...args: any[]) => any>(
  func: T,
  keyGenerator?: (...args: Parameters<T>) => string
): T => {
  const cache = new Map<string, ReturnType<T>>()

  return ((...args: Parameters<T>) => {
    const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args)

    if (cache.has(key)) {
      return cache.get(key)!
    }

    const result = func(...args)
    cache.set(key, result)
    return result
  }) as T
}

// Export all utilities
export default {
  // Data transformation
  transformTimeSeriesData,
  aggregateTimeSeries,
  resampleData,

  // Statistical
  calculateMovingAverage,
  calculateStandardDeviation,
  calculatePercentiles,
  detectOutliers,

  // Colors
  generateColorPalette,

  // Formatting
  formatNumber,
  formatPercentage,
  formatDate,

  // Performance
  debounce,
  throttle,
  memoize
}