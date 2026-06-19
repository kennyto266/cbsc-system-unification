import { Chart as ChartJS, ChartConfiguration, ChartData, ChartType } from 'chart.js'
import { Strategy, StrategyType, RiskLevel } from '../types'

// 圖表工具類
export class ChartUtils {
  // 策略類型映射到中文名稱
  static readonly STRATEGY_TYPE_LABELS: Record<StrategyType, string> = {
    [StrategyType.SENTIMENT]: '情感策略',
    [StrategyType.TECHNICAL]: '技術策略',
    [StrategyType.MOMENTUM]: '動量策略',
    [StrategyType.MEAN_REVERSION]: '均值回歸',
    [StrategyType.ARBITRAGE]: '套利策略'
  }

  // 風險級別映射到中文名稱
  static readonly RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
    [RiskLevel.LOW]: '低風險',
    [RiskLevel.MEDIUM]: '中風險',
    [RiskLevel.HIGH]: '高風險'
  }

  // 風險級別顏色配置
  static readonly RISK_COLORS: Record<RiskLevel, { bg: string; border: string }> = {
    [RiskLevel.LOW]: {
      bg: 'rgba(16, 185, 129, 0.8)',
      border: 'rgba(16, 185, 129, 1)'
    },
    [RiskLevel.MEDIUM]: {
      bg: 'rgba(245, 158, 11, 0.8)',
      border: 'rgba(245, 158, 11, 1)'
    },
    [RiskLevel.HIGH]: {
      bg: 'rgba(239, 68, 68, 0.8)',
      border: 'rgba(239, 68, 68, 1)'
    }
  }

  // 策略類型顏色配置
  static readonly STRATEGY_COLORS: Record<StrategyType, string> = {
    [StrategyType.SENTIMENT]: '#3B82F6',
    [StrategyType.TECHNICAL]: '#10B981',
    [StrategyType.MOMENTUM]: '#F59E0B',
    [StrategyType.MEAN_REVERSION]: '#9333EA',
    [StrategyType.ARBITRAGE]: '#EC4899'
  }

  // 格式化數字
  static formatNumber(value: number, decimals: number = 2): string {
    return new Intl.NumberFormat('zh-TW', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value)
  }

  // 格式化百分比
  static formatPercentage(value: number, decimals: number = 2): string {
    return `${this.formatNumber(value * 100, decimals)}%`
  }

  // 格式化貨幣
  static formatCurrency(value: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  // 生成時間序列標籤
  static generateTimeLabels(days: number): string[] {
    const labels = []
    const now = new Date()

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      labels.push(date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' }))
    }

    return labels
  }

  // 生成模擬的歷史數據
  static generateHistoricalData(baseValue: number, days: number, volatility: number = 0.02): number[] {
    const data = []
    let currentValue = baseValue

    for (let i = 0; i < days; i++) {
      const randomVolatility = (Math.random() - 0.5) * volatility
      const dailyChange = randomVolatility
      currentValue *= (1 + dailyChange)
      data.push(currentValue)
    }

    return data
  }

  // 計算投資組合權重
  static calculatePortfolioWeights(strategies: Strategy[]): Map<string, number> {
    const weights = new Map<string, number>()
    const activeStrategies = strategies.filter(s => s.status === 'active')

    if (activeStrategies.length === 0) {
      return weights
    }

    // 根據策略性能和風險級別計算權重
    const strategyWeights = activeStrategies.map(strategy => {
      const riskMultiplier = {
        low: 1.5,
        medium: 1.0,
        high: 0.7
      }[strategy.riskLevel]

      const performanceWeight = Math.max(0.1, strategy.performance.sharpeRatio / 2)
      return {
        id: strategy.id,
        weight: Math.pow(riskMultiplier * performanceWeight, 0.8)
      }
    })

    const totalWeight = strategyWeights.reduce((sum, item) => sum + item.weight, 0)

    strategyWeights.forEach(item => {
      weights.set(item.id, item.weight / totalWeight)
    })

    return weights
  }

  // 計算移動平均線
  static calculateSMA(data: number[], period: number): number[] {
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

  // 計算指數移動平均線
  static calculateEMA(data: number[], period: number): number[] {
    const result: number[] = []
    const multiplier = 2 / (period + 1)

    if (data.length === 0) return result

    result[0] = data[0]
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    }
    return result
  }

  // 計算RSI
  static calculateRSI(data: number[], period: number = 14): number[] {
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(NaN)
      } else {
        let gains = 0
        let losses = 0
        for (let j = i - period + 1; j <= i; j++) {
          const change = data[j] - data[j - 1]
          if (change > 0) gains += change
          else losses -= change
        }
        const avgGain = gains / period
        const avgLoss = losses / period
        const rs = avgGain / avgLoss
        result.push(100 - (100 / (1 + rs)))
      }
    }
    return result
  }

  // 計算布林帶
  static calculateBollingerBands(data: number[], period: number = 20, stdDev: number = 2): {
    upper: number[]
    middle: number[]
    lower: number[]
  } {
    const upper = []
    const middle = this.calculateSMA(data, period)
    const lower = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(NaN)
        lower.push(NaN)
      } else {
        const slice = data.slice(i - period + 1, i + 1)
        const mean = middle[i]
        const variance = slice.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / slice.length
        const standardDeviation = Math.sqrt(variance)

        upper.push(mean + stdDev * standardDeviation)
        lower.push(mean - stdDev * standardDeviation)
      }
    }

    return { upper, middle, lower }
  }

  // 生成顏色數組
  static generateColors(count: number, baseColors?: string[]): string[] {
    const colors = baseColors || [
      '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
      '#EC4899', '#06B6D4', '#84CC16', '#6366F1', '#14B8A6'
    ]

    const result: string[] = []
    for (let i = 0; i < count; i++) {
      result.push(colors[i % colors.length])
    }
    return result
  }

  // 導出圖表為圖片
  static async exportChart(
    canvas: HTMLCanvasElement,
    filename: string,
    options: {
      format?: 'png' | 'jpg' | 'webp'
      quality?: number
      backgroundColor?: string
    } = {}
  ): Promise<void> {
    const {
      format = 'png',
      quality = 0.92,
      backgroundColor = '#ffffff'
    } = options

    return new Promise((resolve, reject) => {
      try {
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('無法獲取canvas上下文'))
          return
        }

        // 保存原始背景
        const originalBg = canvas.style.backgroundColor
        canvas.style.backgroundColor = backgroundColor

        setTimeout(() => {
          const url = canvas.toDataURL(`image/${format}`, quality)
          const link = document.createElement('a')
          link.download = `${filename}.${format}`
          link.href = url
          link.click()

          // 恢復原始背景
          canvas.style.backgroundColor = originalBg
          resolve()
        }, 100)
      } catch (error) {
        reject(error)
      }
    })
  }

  // 創建響應式圖表配置
  static createResponsiveConfig(
    baseConfig: ChartConfiguration,
    breakpoint: 'mobile' | 'tablet' | 'desktop' = 'desktop'
  ): ChartConfiguration {
    const responsiveConfigs = {
      mobile: {
        maintainAspectRatio: false,
        aspectRatio: 1,
        plugins: {
          legend: {
            position: 'bottom' as const,
            labels: {
              font: { size: 10 },
              padding: 10
            }
          }
        },
        scales: {
          x: {
            ticks: { font: { size: 10 } },
            grid: { display: false }
          },
          y: {
            ticks: { font: { size: 10 } }
          }
        }
      },
      tablet: {
        maintainAspectRatio: false,
        aspectRatio: 16/9,
        plugins: {
          legend: {
            position: 'top' as const,
            labels: {
              font: { size: 12 },
              padding: 15
            }
          }
        },
        scales: {
          x: {
            ticks: { font: { size: 12 } }
          },
          y: {
            ticks: { font: { size: 12 } }
          }
        }
      },
      desktop: {
        maintainAspectRatio: false,
        aspectRatio: 21/9,
        plugins: {
          legend: {
            position: 'top' as const,
            labels: {
              font: { size: 14 },
              padding: 20
            }
          }
        },
        scales: {
          x: {
            ticks: { font: { size: 14 } }
          },
          y: {
            ticks: { font: { size: 14 } }
          }
        }
      }
    }

    return {
      ...baseConfig,
      options: {
        ...baseConfig.options,
        ...responsiveConfigs[breakpoint],
        plugins: {
          ...baseConfig.options?.plugins,
          ...responsiveConfigs[breakpoint].plugins
        },
        scales: {
          ...baseConfig.options?.scales,
          ...responsiveConfigs[breakpoint].scales
        }
      }
    }
  }

  // 計算圖表性能統計
  static calculateStats(data: number[]): {
    min: number
    max: number
    mean: number
    median: number
    stdDev: number
  } {
    const validData = data.filter(d => !isNaN(d) && isFinite(d))
    if (validData.length === 0) {
      return { min: 0, max: 0, mean: 0, median: 0, stdDev: 0 }
    }

    const sorted = [...validData].sort((a, b) => a - b)
    const min = sorted[0]
    const max = sorted[sorted.length - 1]
    const mean = validData.reduce((sum, val) => sum + val, 0) / validData.length
    const median = sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)]

    const variance = validData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / validData.length
    const stdDev = Math.sqrt(variance)

    return { min, max, mean, median, stdDev }
  }

  // 檢測圖表數據異常值
  static detectOutliers(data: number[], threshold: number = 1.5): {
    outliers: number[]
    cleanedData: number[]
    indices: number[]
  } {
    const stats = this.calculateStats(data)
    const q1 = stats.median - (stats.max - stats.median) / 2
    const q3 = stats.median + (stats.max - stats.median) / 2
    const iqr = q3 - q1
    const lowerBound = q1 - threshold * iqr
    const upperBound = q3 + threshold * iqr

    const outliers: number[] = []
    const indices: number[] = []
    const cleanedData = [...data]

    data.forEach((value, index) => {
      if (value < lowerBound || value > upperBound) {
        outliers.push(value)
        indices.push(index)
        cleanedData[index] = NaN
      }
    })

    return { outliers, cleanedData, indices }
  }
}

export default ChartUtils

// Re-export named utility functions from chartUtils.tsx for compatibility
// (many files import { transformTimeSeriesData, formatNumber, ... } from this module)
// Explicit .tsx extension to avoid self-reference circular import
export {
  transformTimeSeriesData,
  aggregateTimeSeries,
  resampleData,
  calculateMovingAverage,
  calculateStandardDeviation,
  calculatePercentiles,
  detectOutliers,
  generateColorPalette,
  formatNumber,
  formatPercentage,
  formatDate,
  debounce,
  throttle,
  memoize,
} from './chartUtils.tsx'