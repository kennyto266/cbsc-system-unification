import { useEffect, useRef, useState, useCallback } from 'react'
import { useRealTimeChart } from '../../components/charts/RealTime/RealTimeChartProvider'
import { IndicatorType, IndicatorCategory } from '../../types/technical-indicators'
import { ChartDataPoint } from '../../components/charts/RealTime/RealTimeChartProvider'

// Technical indicator calculation function type
export type IndicatorCalculator = (data: ChartDataPoint[], options?: any) => number[]

// Technical indicator configuration
export interface TechnicalIndicatorConfig {
  type: IndicatorType
  name: string
  category: IndicatorCategory
  calculator: IndicatorCalculator
  defaultOptions?: Record<string, any>
  overlay?: boolean
  description?: string
}

// Technical indicator hook options
export interface UseTechnicalIndicatorsOptions {
  symbol: string
  timeframe: string
  indicators?: IndicatorType[]
  autoCalculate?: boolean
  calculationInterval?: number
  lookbackPeriod?: number
  onIndicatorUpdate?: (type: IndicatorType, values: number[]) => void
}

// Technical indicator hook return value
export interface UseTechnicalIndicatorsReturn {
  indicators: Map<IndicatorType, number[]>
  isCalculating: boolean
  error: Error | null
  calculateIndicator: (type: IndicatorType, options?: any) => number[] | null
  calculateAllIndicators: () => void
  getIndicatorValue: (type: IndicatorType, index?: number) => number | null
  getLatestValue: (type: IndicatorType) => number | null
  clearIndicators: () => void
  registerIndicator: (config: TechnicalIndicatorConfig) => void
  getAvailableIndicators: () => IndicatorType[]
}

// Built-in technical indicator calculations
const indicatorCalculators: Map<IndicatorType, IndicatorCalculator> = new Map([
  // Moving Averages
  [IndicatorType.SMA, (data, options = {}) => {
    const period = options.period || 20
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((sum, d) => sum + d.close, 0)
        result.push(sum / period)
      }
    }
    return result
  }],

  [IndicatorType.EMA, (data, options = {}) => {
    const period = options.period || 20
    const multiplier = 2 / (period + 1)
    const result: number[] = []

    if (data.length === 0) return result

    result[0] = data[0].close
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i].close - result[i - 1]) * multiplier + result[i - 1]
    }
    return result
  }],

  [IndicatorType.WMA, (data, options = {}) => {
    const period = options.period || 20
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        let sum = 0
        let weightSum = 0

        for (let j = 0; j < period; j++) {
          const weight = j + 1
          sum += data[i - j].close * weight
          weightSum += weight
        }

        result.push(sum / weightSum)
      }
    }
    return result
  }],

  // Oscillators
  [IndicatorType.RSI, (data, options = {}) => {
    const period = options.period || 14
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(NaN)
      } else {
        let gains = 0
        let losses = 0

        for (let j = i - period + 1; j <= i; j++) {
          const change = data[j].close - data[j - 1].close
          if (change > 0) {
            gains += change
          } else {
            losses -= change
          }
        }

        const avgGain = gains / period
        const avgLoss = losses / period
        const rs = avgGain / avgLoss
        result.push(100 - (100 / (1 + rs)))
      }
    }
    return result
  }],

  [IndicatorType.MACD, (data, options = {}) => {
    const fastPeriod = options.fastPeriod || 12
    const slowPeriod = options.slowPeriod || 26
    const signalPeriod = options.signalPeriod || 9

    const emaFast = indicatorCalculators.get(IndicatorType.EMA)!(data, { period: fastPeriod })
    const emaSlow = indicatorCalculators.get(IndicatorType.EMA)!(data, { period: slowPeriod })

    const macdLine = emaFast.map((fast, i) => fast - emaSlow[i])
    const signalLine = indicatorCalculators.get(IndicatorType.EMA)!(
      macdLine.map((val, i) => ({ close: val, timestamp: data[i].timestamp, open: val, high: val, low: val, volume: 0 })),
      { period: signalPeriod }
    )

    return macdLine.map((val, i) => val - signalLine[i])
  }],

  [IndicatorType.STOCH, (data, options = {}) => {
    const kPeriod = options.kPeriod || 14
    const dPeriod = options.dPeriod || 3
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < kPeriod - 1) {
        result.push(NaN)
      } else {
        const period = data.slice(i - kPeriod + 1, i + 1)
        const highestHigh = Math.max(...period.map(d => d.high))
        const lowestLow = Math.min(...period.map(d => d.low))

        const k = ((data[i].close - lowestLow) / (highestHigh - lowestLow)) * 100

        // Simple moving average for %D
        let dSum = 0
        let dCount = 0

        for (let j = i; j > i - dPeriod && j >= 0; j--) {
          const jPeriod = data.slice(Math.max(0, j - kPeriod + 1), j + 1)
          const jHighestHigh = Math.max(...jPeriod.map(d => d.high))
          const jLowestLow = Math.min(...jPeriod.map(d => d.low))
          const jK = ((data[j].close - jLowestLow) / (jHighestHigh - jLowestLow)) * 100

          dSum += jK
          dCount++
        }

        result.push(dCount > 0 ? dSum / dCount : k)
      }
    }
    return result
  }],

  // Volume indicators
  [IndicatorType.OBV, (data) => {
    const result: number[] = [data[0].volume]

    for (let i = 1; i < data.length; i++) {
      if (data[i].close > data[i - 1].close) {
        result.push(result[i - 1] + data[i].volume)
      } else if (data[i].close < data[i - 1].close) {
        result.push(result[i - 1] - data[i].volume)
      } else {
        result.push(result[i - 1])
      }
    }
    return result
  }],

  [IndicatorType.VWAP, (data) => {
    const result: number[] = []
    let cumulativeVolume = 0
    let cumulativeVolumePrice = 0

    for (let i = 0; i < data.length; i++) {
      cumulativeVolume += data[i].volume
      cumulativeVolumePrice += data[i].close * data[i].volume
      result.push(cumulativeVolumePrice / cumulativeVolume)
    }
    return result
  }],

  // Volatility indicators
  [IndicatorType.BB, (data, options = {}) => {
    const period = options.period || 20
    const stdDev = options.stdDev || 2
    const sma = indicatorCalculators.get(IndicatorType.SMA)!(data, { period })
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const periodData = data.slice(i - period + 1, i + 1)
        const mean = sma[i]

        const variance = periodData.reduce((sum, d) => {
          return sum + Math.pow(d.close - mean, 2)
        }, 0) / period

        const standardDeviation = Math.sqrt(variance)
        result.push(standardDeviation)
      }
    }
    return result
  }],

  [IndicatorType.ATR, (data, options = {}) => {
    const period = options.period || 14
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        result.push(data[i].high - data[i].low)
      } else if (i < period) {
        const tr = Math.max(
          data[i].high - data[i].low,
          Math.abs(data[i].high - data[i - 1].close),
          Math.abs(data[i].low - data[i - 1].close)
        )
        result.push(tr)
      } else {
        const tr = Math.max(
          data[i].high - data[i].low,
          Math.abs(data[i].high - data[i - 1].close),
          Math.abs(data[i].low - data[i - 1].close)
        )
        result.push((result[i - 1] * (period - 1) + tr) / period)
      }
    }
    return result
  }]
])

// Technical indicator hook
export const useTechnicalIndicators = (options: UseTechnicalIndicatorsOptions): UseTechnicalIndicatorsReturn => {
  const {
    symbol,
    timeframe,
    indicators: initialIndicators = [],
    autoCalculate = true,
    calculationInterval = 5000,
    lookbackPeriod = 200,
    onIndicatorUpdate
  } = options

  const chartContext = useRealTimeChart()
  const [indicators, setIndicators] = useState<Map<IndicatorType, number[]>>(new Map())
  const [isCalculating, setIsCalculating] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [availableIndicators, setAvailableIndicators] = useState<IndicatorType[]>(Object.values(IndicatorType))

  const calculationTimerRef = useRef<NodeJS.Timeout | null>(null)
  const customIndicatorsRef = useRef<Map<IndicatorType, TechnicalIndicatorConfig>>(new Map())

  // Get chart data
  const data = chartContext.getData(symbol, timeframe)

  // Calculate a single indicator
  const calculateIndicator = useCallback((type: IndicatorType, options?: any): number[] | null => {
    if (!data || data.length === 0) return null

    const calculator = indicatorCalculators.get(type) ||
                      customIndicatorsRef.current.get(type)?.calculator

    if (!calculator) {
      setError(new Error(`Unknown indicator: ${type}`))
      return null
    }

    try {
      setIsCalculating(true)
      setError(null)

      // Ensure we have enough data
      const period = options?.period || 20
      const requiredData = data.slice(-Math.max(lookbackPeriod, period))

      const values = calculator(requiredData, options)

      // Update indicators state
      setIndicators(prev => {
        const newIndicators = new Map(prev)
        newIndicators.set(type, values)
        return newIndicators
      })

      onIndicatorUpdate?.(type, values)
      return values
    } catch (err) {
      const error = err instanceof Error ? err : new Error(`Failed to calculate ${type}`)
      setError(error)
      return null
    } finally {
      setIsCalculating(false)
    }
  }, [data, lookbackPeriod, onIndicatorUpdate])

  // Calculate all configured indicators
  const calculateAllIndicators = useCallback(() => {
    initialIndicators.forEach(type => {
      calculateIndicator(type)
    })
  }, [initialIndicators, calculateIndicator])

  // Get indicator value at specific index
  const getIndicatorValue = useCallback((type: IndicatorType, index?: number): number | null => {
    const values = indicators.get(type)
    if (!values || values.length === 0) return null

    if (index === undefined) {
      return values[values.length - 1]
    }

    return index >= 0 && index < values.length ? values[index] : null
  }, [indicators])

  // Get latest indicator value
  const getLatestValue = useCallback((type: IndicatorType): number | null => {
    return getIndicatorValue(type)
  }, [getIndicatorValue])

  // Clear all indicators
  const clearIndicators = useCallback(() => {
    setIndicators(new Map())
  }, [])

  // Register custom indicator
  const registerIndicator = useCallback((config: TechnicalIndicatorConfig) => {
    customIndicatorsRef.current.set(config.type, config)

    // Add to available indicators
    setAvailableIndicators(prev => {
      if (!prev.includes(config.type)) {
        return [...prev, config.type]
      }
      return prev
    })
  }, [])

  // Get available indicators
  const getAvailableIndicatorsCallback = useCallback(() => {
    return availableIndicators
  }, [availableIndicators])

  // Auto-calculate indicators when data updates
  useEffect(() => {
    if (autoCalculate && data && data.length > 0) {
      if (calculationTimerRef.current) {
        clearTimeout(calculationTimerRef.current)
      }

      // Debounce calculation
      calculationTimerRef.current = setTimeout(() => {
        calculateAllIndicators()
      }, calculationInterval)
    }

    return () => {
      if (calculationTimerRef.current) {
        clearTimeout(calculationTimerRef.current)
      }
    }
  }, [data, autoCalculate, calculationInterval, calculateAllIndicators])

  // Initial calculation
  useEffect(() => {
    if (autoCalculate && initialIndicators.length > 0) {
      calculateAllIndicators()
    }
  }, []) // Run once on mount

  return {
    indicators,
    isCalculating,
    error,
    calculateIndicator,
    calculateAllIndicators,
    getIndicatorValue,
    getLatestValue,
    clearIndicators,
    registerIndicator,
    getAvailableIndicators: getAvailableIndicatorsCallback
  }
}

export default useTechnicalIndicators