// Web Worker for processing large indicator datasets
// 用于处理大量指标数据的 Web Worker

interface IndicatorData {
  id: string
  values: number[]
  timestamps: number[]
  metadata?: any
}

interface ProcessIndicatorDataMessage {
  type: 'PROCESS_INDICATOR_DATA'
  payload: {
    indicators: IndicatorData[]
    operation: 'aggregate' | 'smooth' | 'resample' | 'calculate-signals'
    params?: any
  }
}

interface CalculateIndicatorPerformanceMessage {
  type: 'CALCULATE_PERFORMANCE'
  payload: {
    indicatorId: string
    priceData: number[]
    signals: Array<{
      timestamp: number
      type: 'buy' | 'sell'
      price: number
    }>
  }
}

interface FilterIndicatorsMessage {
  type: 'FILTER_INDICATORS'
  payload: {
    indicators: IndicatorData[]
    filters: {
      dateRange?: [number, number]
      valueRange?: [number, number]
      tags?: string[]
    }
  }
}

type WorkerMessage = ProcessIndicatorDataMessage | CalculateIndicatorPerformanceMessage | FilterIndicatorsMessage

// 数据聚合函数
function aggregateData(data: number[], windowSize: number): number[] {
  const result: number[] = []
  for (let i = 0; i < data.length; i += windowSize) {
    const window = data.slice(i, i + windowSize)
    const avg = window.reduce((sum, val) => sum + val, 0) / window.length
    result.push(avg)
  }
  return result
}

// 数据平滑函数（移动平均）
function smoothData(data: number[], period: number): number[] {
  const result: number[] = []
  for (let i = period - 1; i < data.length; i++) {
    const window = data.slice(i - period + 1, i + 1)
    const avg = window.reduce((sum, val) => sum + val, 0) / period
    result.push(avg)
  }
  // 填充前面空缺的值
  return [...new Array(period - 1).fill(data[0]), ...result]
}

// 数据重采样
function resampleData(
  timestamps: number[],
  values: number[],
  targetInterval: number
): { timestamps: number[]; values: number[] } {
  const result: { timestamps: number[]; values: number[] } = {
    timestamps: [],
    values: []
  }

  let lastTimestamp = timestamps[0]
  let accumulator = 0
  let count = 0

  for (let i = 0; i < timestamps.length; i++) {
    if (timestamps[i] - lastTimestamp >= targetInterval) {
      if (count > 0) {
        result.timestamps.push(lastTimestamp)
        result.values.push(accumulator / count)
      }
      lastTimestamp = timestamps[i]
      accumulator = values[i]
      count = 1
    } else {
      accumulator += values[i]
      count++
    }
  }

  // 添加最后一个数据点
  if (count > 0) {
    result.timestamps.push(lastTimestamp)
    result.values.push(accumulator / count)
  }

  return result
}

// 计算信号
function calculateSignals(values: number[], params: any): Array<{ index: number; type: 'buy' | 'sell' }> {
  const signals: Array<{ index: number; type: 'buy' | 'sell' }> = []
  const { overbought = 70, oversold = 30 } = params

  for (let i = 1; i < values.length; i++) {
    // 简单的RSI信号逻辑
    if (values[i - 1] <= oversold && values[i] > oversold) {
      signals.push({ index: i, type: 'buy' })
    } else if (values[i - 1] >= overbought && values[i] < overbought) {
      signals.push({ index: i, type: 'sell' })
    }
  }

  return signals
}

// 计算性能指标
function calculatePerformance(
  priceData: number[],
  signals: Array<{ timestamp: number; type: 'buy' | 'sell'; price: number }>
) {
  let totalReturn = 0
  let maxDrawdown = 0
  let peak = 0
  let winCount = 0
  let lossCount = 0
  let totalWin = 0
  let totalLoss = 0

  let position = null
  let entryPrice = 0

  for (let i = 0; i < priceData.length; i++) {
    const currentPrice = priceData[i]

    // 更新峰值和最大回撤
    if (totalReturn > peak) {
      peak = totalReturn
    }
    const drawdown = peak - totalReturn
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown
    }

    // 处理信号
    const signal = signals.find(s => s.timestamp <= i)
    if (signal) {
      if (signal.type === 'buy' && !position) {
        position = 'long'
        entryPrice = currentPrice
      } else if (signal.type === 'sell' && position === 'long') {
        const returns = (currentPrice - entryPrice) / entryPrice
        totalReturn += returns

        if (returns > 0) {
          winCount++
          totalWin += returns
        } else {
          lossCount++
          totalLoss += Math.abs(returns)
        }

        position = null
      }
    }
  }

  const winRate = winCount + lossCount > 0 ? winCount / (winCount + lossCount) : 0
  const profitFactor = totalLoss > 0 ? totalWin / totalLoss : 0
  const sharpeRatio = totalReturn / (maxDrawdown || 0.01) // 简化的夏普比率

  return {
    totalReturn,
    maxDrawdown,
    winRate,
    profitFactor,
    sharpeRatio,
    totalSignals: signals.length
  }
}

// 过滤指标数据
function filterIndicators(
  indicators: IndicatorData[],
  filters: {
    dateRange?: [number, number]
    valueRange?: [number, number]
    tags?: string[]
  }
): IndicatorData[] {
  return indicators.filter(indicator => {
    // 日期范围过滤
    if (filters.dateRange) {
      const [start, end] = filters.dateRange
      const inRange = indicator.timestamps.some(t => t >= start && t <= end)
      if (!inRange) return false
    }

    // 数值范围过滤
    if (filters.valueRange) {
      const [min, max] = filters.valueRange
      const hasValueInRange = indicator.values.some(v => v >= min && v <= max)
      if (!hasValueInRange) return false
    }

    // 标签过滤
    if (filters.tags && filters.tags.length > 0) {
      const indicatorTags = indicator.metadata?.tags || []
      const hasMatchingTag = filters.tags.some(tag => indicatorTags.includes(tag))
      if (!hasMatchingTag) return false
    }

    return true
  })
}

// 主消息处理
self.onmessage = (event: MessageEvent<WorkerMessage>) => {
  const { type, payload } = event.data

  try {
    switch (type) {
      case 'PROCESS_INDICATOR_DATA': {
        const { indicators, operation, params } = payload
        const processedIndicators = indicators.map(indicator => {
          let processedValues = [...indicator.values]
          let processedTimestamps = [...indicator.timestamps]

          switch (operation) {
            case 'aggregate':
              processedValues = aggregateData(processedValues, params?.windowSize || 5)
              processedTimestamps = processedTimestamps.filter((_, i) =>
                i % (params?.windowSize || 5) === 0
              )
              break

            case 'smooth':
              processedValues = smoothData(processedValues, params?.period || 5)
              break

            case 'resample':
              const resampled = resampleData(
                processedTimestamps,
                processedValues,
                params?.interval || 60000
              )
              processedTimestamps = resampled.timestamps
              processedValues = resampled.values
              break

            case 'calculate-signals':
              const signals = calculateSignals(processedValues, params)
              return {
                ...indicator,
                values: processedValues,
                timestamps: processedTimestamps,
                signals
              }
          }

          return {
            ...indicator,
            values: processedValues,
            timestamps: processedTimestamps
          }
        })

        self.postMessage({
          type: 'PROCESSING_COMPLETE',
          payload: processedIndicators
        })
        break
      }

      case 'CALCULATE_PERFORMANCE': {
        const { indicatorId, priceData, signals } = payload
        const performance = calculatePerformance(priceData, signals)

        self.postMessage({
          type: 'PERFORMANCE_CALCULATED',
          payload: {
            indicatorId,
            performance
          }
        })
        break
      }

      case 'FILTER_INDICATORS': {
        const filteredIndicators = filterIndicators(payload.indicators, payload.filters)

        self.postMessage({
          type: 'FILTERING_COMPLETE',
          payload: filteredIndicators
        })
        break
      }

      default:
        throw new Error(`Unknown message type: ${type}`)
    }
  } catch (error) {
    self.postMessage({
      type: 'ERROR',
      payload: {
        error: error instanceof Error ? error.message : 'Unknown error',
        originalMessage: event.data
      }
    })
  }
}

// 导出类型供外部使用
export type { IndicatorData, WorkerMessage }