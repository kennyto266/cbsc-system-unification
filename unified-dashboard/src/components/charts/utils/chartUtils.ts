import { ChartTheme } from '../types/chart.types'
import { TimeSeriesDataPoint, HeatmapDataPoint } from '../types/chart.types'

// Color manipulation utilities
export class ColorUtils {
  // Convert hex to RGB
  static hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null
  }

  // Convert RGB to hex
  static rgbToHex(r: number, g: number, b: number): string {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
  }

  // Interpolate between two colors
  static interpolate(color1: string, color2: string, ratio: number): string {
    const c1 = this.hexToRgb(color1)
    const c2 = this.hexToRgb(color2)

    if (!c1 || !c2) return color1

    const r = Math.round(c1.r + (c2.r - c1.r) * ratio)
    const g = Math.round(c1.g + (c2.g - c1.g) * ratio)
    const b = Math.round(c1.b + (c2.b - c1.b) * ratio)

    return this.rgbToHex(r, g, b)
  }

  // Generate color palette
  static generatePalette(baseColor: string, count: number): string[] {
    const colors: string[] = []
    for (let i = 0; i < count; i++) {
      const ratio = i / Math.max(count - 1, 1)
      colors.push(this.interpolate(baseColor, '#FFFFFF', ratio * 0.5))
    }
    return colors
  }

  // Adjust color brightness
  static adjustBrightness(color: string, amount: number): string {
    const rgb = this.hexToRgb(color)
    if (!rgb) return color

    const r = Math.max(0, Math.min(255, rgb.r + amount))
    const g = Math.max(0, Math.min(255, rgb.g + amount))
    const b = Math.max(0, Math.min(255, rgb.b + amount))

    return this.rgbToHex(r, g, b)
  }
}

// Data processing utilities
export class DataUtils {
  // Normalize data to 0-1 range
  static normalize(data: number[]): number[] {
    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min

    if (range === 0) return data.map(() => 0)

    return data.map(value => (value - min) / range)
  }

  // Resample time series data
  static resampleTimeSeries(
    data: TimeSeriesDataPoint[],
    interval: number // milliseconds
  ): TimeSeriesDataPoint[] {
    if (data.length === 0) return []

    const resampled: TimeSeriesDataPoint[] = []
    let currentBucket = data[0].timestamp
    let bucketValues: number[] = []
    let bucketVolumes: number[] = []

    for (const point of data) {
      const pointTime = new Date(point.timestamp).getTime()
      const bucketTime = new Date(currentBucket).getTime()

      if (pointTime < bucketTime + interval) {
        bucketValues.push(point.value)
        if (point.volume) bucketVolumes.push(point.volume)
      } else {
        // Create aggregated point for the bucket
        if (bucketValues.length > 0) {
          resampled.push({
            timestamp: new Date(currentBucket),
            value: bucketValues.reduce((a, b) => a + b, 0) / bucketValues.length,
            volume: bucketVolumes.length > 0
              ? bucketVolumes.reduce((a, b) => a + b, 0)
              : undefined
          })
        }

        // Start new bucket
        currentBucket = new Date(Math.floor(pointTime / interval) * interval)
        bucketValues = [point.value]
        bucketVolumes = point.volume ? [point.volume] : []
      }
    }

    // Handle last bucket
    if (bucketValues.length > 0) {
      resampled.push({
        timestamp: new Date(currentBucket),
        value: bucketValues.reduce((a, b) => a + b, 0) / bucketValues.length,
        volume: bucketVolumes.length > 0
          ? bucketVolumes.reduce((a, b) => a + b, 0)
          : undefined
      })
    }

    return resampled
  }

  // Calculate moving average
  static movingAverage(data: number[], period: number): number[] {
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

  // Find outliers using IQR method
  static findOutliers(data: number[]): { outliers: number[]; indices: number[] } {
    const sorted = [...data].sort((a, b) => a - b)
    const q1 = sorted[Math.floor(sorted.length * 0.25)]
    const q3 = sorted[Math.floor(sorted.length * 0.75)]
    const iqr = q3 - q1
    const lowerBound = q1 - 1.5 * iqr
    const upperBound = q3 + 1.5 * iqr

    const outliers: number[] = []
    const indices: number[] = []

    data.forEach((value, index) => {
      if (value < lowerBound || value > upperBound) {
        outliers.push(value)
        indices.push(index)
      }
    })

    return { outliers, indices }
  }

  // Aggregate data by time period
  static aggregateByPeriod(
    data: TimeSeriesDataPoint[],
    period: 'minute' | 'hour' | 'day' | 'week' | 'month'
  ): TimeSeriesDataPoint[] {
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

    // Aggregate each group
    const aggregated: TimeSeriesDataPoint[] = []
    grouped.forEach((points, key) => {
      const values = points.map(p => p.value)
      const volumes = points.filter(p => p.volume).map(p => p.volume!)

      aggregated.push({
        timestamp: new Date(key),
        value: values.reduce((a, b) => a + b, 0) / values.length,
        volume: volumes.length > 0 ? volumes.reduce((a, b) => a + b, 0) : undefined
      })
    })

    return aggregated.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  }
}

// Chart formatting utilities
export class FormatUtils {
  // Format number with locale
  static formatNumber(value: number, locale: string = 'zh-CN', options?: Intl.NumberFormatOptions): string {
    return new Intl.NumberFormat(locale, options).format(value)
  }

  // Format currency
  static formatCurrency(value: number, currency: string = 'USD', locale: string = 'zh-CN'): string {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  // Format percentage
  static formatPercentage(value: number, decimals: number = 2): string {
    return `${(value * 100).toFixed(decimals)}%`
  }

  // Format date/time
  static formatDateTime(date: Date | string | number, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
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

  // Format duration
  static formatDuration(milliseconds: number): string {
    const seconds = Math.floor(milliseconds / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) {
      return `${days}天 ${hours % 24}小时`
    } else if (hours > 0) {
      return `${hours}小时 ${minutes % 60}分钟`
    } else if (minutes > 0) {
      return `${minutes}分钟 ${seconds % 60}秒`
    } else {
      return `${seconds}秒`
    }
  }

  // Format file size
  static formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`
  }
}

// Chart calculation utilities
export class ChartUtils {
  // Calculate chart dimensions
  static calculateDimensions(
    containerWidth: number,
    containerHeight: number,
    margins: { top: number; right: number; bottom: number; left: number }
  ) {
    return {
      width: containerWidth - margins.left - margins.right,
      height: containerHeight - margins.top - margins.bottom
    }
  }

  // Calculate nice domain for axis
  static calculateNiceDomain(min: number, max: number, tickCount: number = 5): [number, number] {
    const range = max - min
    const roughStep = range / (tickCount - 1)
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)))
    const normalizedStep = roughStep / magnitude

    let niceStep: number
    if (normalizedStep <= 1) niceStep = 1
    else if (normalizedStep <= 2) niceStep = 2
    else if (normalizedStep <= 5) niceStep = 5
    else niceStep = 10

    niceStep *= magnitude

    const niceMin = Math.floor(min / niceStep) * niceStep
    const niceMax = Math.ceil(max / niceStep) * niceStep

    return [niceMin, niceMax]
  }

  // Calculate optimal tick values
  static calculateTicks(min: number, max: number, count: number): number[] {
    const [niceMin, niceMax] = this.calculateNiceDomain(min, max, count)
    const step = (niceMax - niceMin) / (count - 1)

    const ticks = []
    for (let i = 0; i < count; i++) {
      ticks.push(niceMin + step * i)
    }

    return ticks
  }

  // Calculate pie chart angles
  static calculatePieAngles(data: Array<{ value: number }>): Array<{ startAngle: number; endAngle: number }> {
    const total = data.reduce((sum, item) => sum + item.value, 0)
    let currentAngle = -Math.PI / 2 // Start from top

    return data.map(item => {
      const proportion = item.value / total
      const angle = proportion * 2 * Math.PI
      const startAngle = currentAngle
      const endAngle = currentAngle + angle
      currentAngle = endAngle

      return { startAngle, endAngle }
    })
  }

  // Calculate arc path for pie/donut charts
  static createArcPath(
    x: number,
    y: number,
    radius: number,
    innerRadius: number,
    startAngle: number,
    endAngle: number
  ): string {
    const x1 = x + radius * Math.cos(startAngle)
    const y1 = y + radius * Math.sin(startAngle)
    const x2 = x + radius * Math.cos(endAngle)
    const y2 = y + radius * Math.sin(endAngle)

    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0

    if (innerRadius === 0) {
      // Pie slice
      return `M ${x} ${y} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`
    } else {
      // Donut slice
      const x3 = x + innerRadius * Math.cos(startAngle)
      const y3 = y + innerRadius * Math.sin(startAngle)
      const x4 = x + innerRadius * Math.cos(endAngle)
      const y4 = y + innerRadius * Math.sin(endAngle)

      return `
        M ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
        L ${x4} ${y4}
        A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x3} ${y3}
        Z
      `.replace(/\s+/g, ' ').trim()
    }
  }
}

// Chart theme utilities
export class ThemeUtils {
  // Get contrasting color
  static getContrastColor(backgroundColor: string): string {
    const rgb = ColorUtils.hexToRgb(backgroundColor)
    if (!rgb) return '#000000'

    // Calculate luminance
    const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255

    return luminance > 0.5 ? '#000000' : '#FFFFFF'
  }

  // Generate theme from base color
  static generateTheme(baseColor: string): ChartTheme {
    const rgb = ColorUtils.hexToRgb(baseColor) || { r: 59, g: 130, b: 246 }

    return {
      name: 'generated',
      colors: {
        primary: [
          baseColor,
          ColorUtils.adjustBrightness(baseColor, 20),
          ColorUtils.adjustBrightness(baseColor, -20),
          ColorUtils.adjustBrightness(baseColor, 40),
          ColorUtils.adjustBrightness(baseColor, -40)
        ],
        secondary: [
          '#6B7280',
          '#9CA3AF',
          '#D1D5DB'
        ],
        background: '#FFFFFF',
        foreground: '#1F2937',
        grid: 'rgba(0, 0, 0, 0.05)',
        tooltip: {
          background: 'rgba(0, 0, 0, 0.8)',
          foreground: '#FFFFFF',
          border: 'rgba(0, 0, 0, 0.8)'
        }
      },
      typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: {
          small: 12,
          medium: 14,
          large: 16
        }
      },
      spacing: {
        xs: 4,
        sm: 8,
        md: 16,
        lg: 24,
        xl: 32
      }
    }
  }
}

// All utilities are already exported as individual exports above