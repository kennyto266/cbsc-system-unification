/**
 * Economic Signal Detection Utilities
 * 經濟信號檢測工具函數
 */

import { EconomicSignal } from '../components/EconomicSignalMarkers'

export interface EconomicDataPoint {
  date: string
  value: number
  indicator?: string
}

export interface SignalThreshold {
  indicator: string
  type: 'buy' | 'sell' | 'neutral' | 'warning' | 'opportunity'
  operator: '>' | '<' | '=' | '>=' | '<=' | 'between' | 'outside'
  value: number | [number, number]
  strength: number // Base strength for this threshold
  description: string
  category: 'interest_rate' | 'economic_growth' | 'employment' | 'tourism' | 'inflation'
}

export interface SignalDetectionConfig {
  thresholds: SignalThreshold[]
  minDataPoints: number
  lookbackPeriod: number // Number of previous data points to consider
  strengthMultiplier: number // Multiplier for strength based on deviation from threshold
  confidenceThreshold: number // Minimum confidence to generate a signal
}

// Default signal detection configuration
export const DEFAULT_SIGNAL_CONFIG: SignalDetectionConfig = {
  thresholds: [
    // HIBOR Thresholds
    {
      indicator: 'hibor',
      type: 'warning',
      operator: '>',
      value: 6.0,
      strength: 0.8,
      description: 'HIBOR rate exceeds 6%, indicating high interest rate environment',
      category: 'interest_rate'
    },
    {
      indicator: 'hibor',
      type: 'opportunity',
      operator: '<',
      value: 3.0,
      strength: 0.7,
      description: 'HIBOR rate below 3%, indicating favorable borrowing conditions',
      category: 'interest_rate'
    },

    // GDP Thresholds
    {
      indicator: 'gdp',
      type: 'warning',
      operator: '<',
      value: 2.0,
      strength: 0.9,
      description: 'GDP growth below 2%, indicating economic slowdown',
      category: 'economic_growth'
    },
    {
      indicator: 'gdp',
      type: 'buy',
      operator: '>',
      value: 4.0,
      strength: 0.7,
      description: 'GDP growth above 4%, indicating strong economic expansion',
      category: 'economic_growth'
    },

    // PMI Thresholds
    {
      indicator: 'pmi',
      type: 'warning',
      operator: '<',
      value: 50.0,
      strength: 0.8,
      description: 'PMI below 50, indicating economic contraction',
      category: 'economic_growth'
    },
    {
      indicator: 'pmi',
      type: 'buy',
      operator: '>',
      value: 55.0,
      strength: 0.7,
      description: 'PMI above 55, indicating strong economic expansion',
      category: 'economic_growth'
    },

    // Visitor Arrivals Thresholds
    {
      indicator: 'visitors',
      type: 'warning',
      operator: '<',
      value: 100000, // 100K visitors
      strength: 0.6,
      description: 'Visitor arrivals below 100K, indicating tourism sector weakness',
      category: 'tourism'
    },
    {
      indicator: 'visitors',
      type: 'opportunity',
      operator: '>',
      value: 200000, // 200K visitors
      strength: 0.7,
      description: 'Visitor arrivals above 200K, indicating strong tourism performance',
      category: 'tourism'
    },

    // Unemployment Thresholds
    {
      indicator: 'unemployment',
      type: 'warning',
      operator: '>',
      value: 4.0,
      strength: 0.8,
      description: 'Unemployment above 4%, indicating labor market weakness',
      category: 'employment'
    },
    {
      indicator: 'unemployment',
      type: 'buy',
      operator: '<',
      value: 3.0,
      strength: 0.6,
      description: 'Unemployment below 3%, indicating strong labor market',
      category: 'employment'
    }
  ],
  minDataPoints: 3,
  lookbackPeriod: 5,
  strengthMultiplier: 1.5,
  confidenceThreshold: 0.5
}

/**
 * Detect economic signals based on threshold analysis
 */
export function detectEconomicSignals(
  data: Record<string, EconomicDataPoint[]>,
  config: SignalDetectionConfig = DEFAULT_SIGNAL_CONFIG
): EconomicSignal[] {
  const signals: EconomicSignal[] = []
  const now = new Date()

  Object.entries(data).forEach(([indicator, dataPoints]) => {
    if (dataPoints.length < config.minDataPoints) {
      return // Skip if insufficient data points
    }

    // Sort data points by date (newest first)
    const sortedData = dataPoints.sort((a, b) =>
      new Date(b.date).getTime() - new Date(a.date).getTime()
    )

    // Get the most recent data point
    const currentPoint = sortedData[0]
    const currentValue = currentPoint.value

    // Get previous data points for trend analysis
    const previousPoints = sortedData.slice(1, config.lookbackPeriod + 1)

    // Check each threshold for this indicator
    config.thresholds
      .filter(threshold => threshold.indicator === indicator)
      .forEach(threshold => {
        if (evaluateThreshold(currentValue, threshold)) {
          const signal = createSignal(
            currentPoint,
            previousPoints,
            threshold,
            config
          )
          signals.push(signal)
        }
      })
  })

  // Sort signals by strength and confidence
  return signals.sort((a, b) => {
    const scoreA = a.strength * a.confidence
    const scoreB = b.strength * b.confidence
    return scoreB - scoreA
  })
}

/**
 * Evaluate if a value meets the threshold condition
 */
function evaluateThreshold(value: number, threshold: SignalThreshold): boolean {
  switch (threshold.operator) {
    case '>':
      return value > (threshold.value as number)
    case '<':
      return value < (threshold.value as number)
    case '>=':
      return value >= (threshold.value as number)
    case '<=':
      return value <= (threshold.value as number)
    case '=':
      return value === (threshold.value as number)
    case 'between':
      const [min, max] = threshold.value as [number, number]
      return value >= min && value <= max
    case 'outside':
      const [low, high] = threshold.value as [number, number]
      return value < low || value > high
    default:
      return false
  }
}

/**
 * Create an economic signal from data point and threshold
 */
function createSignal(
  currentPoint: EconomicDataPoint,
  previousPoints: EconomicDataPoint[],
  threshold: SignalThreshold,
  config: SignalDetectionConfig
): EconomicSignal {
  const currentValue = currentPoint.value
  const previousValue = previousPoints.length > 0 ? previousPoints[0].value : undefined

  // Calculate deviation from threshold
  const deviation = calculateDeviation(currentValue, threshold)

  // Calculate strength based on threshold strength and deviation
  const strength = Math.min(1, threshold.strength + (deviation * config.strengthMultiplier))

  // Calculate confidence based on data consistency and trend
  const confidence = calculateConfidence(currentPoint, previousPoints, threshold, config)

  // Create signal ID
  const signalId = `${threshold.indicator}-${threshold.type}-${new Date(currentPoint.date).getTime()}`

  return {
    id: signalId,
    date: currentPoint.date,
    indicator: threshold.indicator,
    type: threshold.type,
    strength,
    confidence,
    value: currentValue,
    previousValue,
    threshold: typeof threshold.value === 'number' ? threshold.value : undefined,
    description: threshold.description,
    category: threshold.category,
    metadata: {
      deviation: deviation,
      trend: calculateTrend(previousPoints),
      dataPoints: previousPoints.length + 1,
      triggeredBy: 'threshold_analysis'
    },
    createdAt: new Date().toISOString()
  }
}

/**
 * Calculate deviation from threshold
 */
function calculateDeviation(value: number, threshold: SignalThreshold): number {
  if (typeof threshold.value === 'number') {
    const diff = Math.abs(value - threshold.value)
    // Normalize deviation based on the threshold value
    return diff / Math.max(threshold.value, 1)
  }
  return 0
}

/**
 * Calculate confidence based on data consistency and trend
 */
function calculateConfidence(
  currentPoint: EconomicDataPoint,
  previousPoints: EconomicDataPoint[],
  threshold: SignalThreshold,
  config: SignalDetectionConfig
): number {
  let confidence = 0.5 // Base confidence

  // Increase confidence based on data availability
  const totalDataPoints = previousPoints.length + 1
  if (totalDataPoints >= config.minDataPoints) {
    confidence += 0.1
  }

  // Increase confidence if trend supports the signal
  const trend = calculateTrend(previousPoints)
  if ((threshold.type === 'buy' || threshold.type === 'opportunity') && trend > 0) {
    confidence += 0.2
  } else if ((threshold.type === 'sell' || threshold.type === 'warning') && trend < 0) {
    confidence += 0.2
  }

  // Increase confidence based on data consistency
  const consistency = calculateDataConsistency([...previousPoints, currentPoint])
  confidence += consistency * 0.2

  return Math.min(1, confidence)
}

/**
 * Calculate trend from previous data points
 */
function calculateTrend(previousPoints: EconomicDataPoint[]): number {
  if (previousPoints.length < 2) {
    return 0
  }

  let totalChange = 0
  let validChanges = 0

  for (let i = 0; i < previousPoints.length - 1; i++) {
    const current = previousPoints[i].value
    const previous = previousPoints[i + 1].value

    if (previous !== 0) {
      const change = (current - previous) / previous
      totalChange += change
      validChanges++
    }
  }

  return validChanges > 0 ? totalChange / validChanges : 0
}

/**
 * Calculate data consistency (inverse of volatility)
 */
function calculateDataConsistency(dataPoints: EconomicDataPoint[]): number {
  if (dataPoints.length < 2) {
    return 1
  }

  const values = dataPoints.map(point => point.value)
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length

  // Calculate standard deviation
  const squaredDiffs = values.map(val => Math.pow(val - mean, 2))
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length
  const stdDev = Math.sqrt(variance)

  // Convert to consistency (inverse of normalized standard deviation)
  const normalizedStdDev = stdDev / mean
  return Math.max(0, 1 - normalizedStdDev)
}

/**
 * Create mock signals for testing purposes
 */
export function createMockSignals(count: number = 5): EconomicSignal[] {
  const mockSignals: EconomicSignal[] = []
  const indicators = ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment']
  const types: Array<'buy' | 'sell' | 'neutral' | 'warning' | 'opportunity'> = ['buy', 'sell', 'warning', 'opportunity']
  const categories: Array<'interest_rate' | 'economic_growth' | 'employment' | 'tourism' | 'inflation'> = [
    'interest_rate', 'economic_growth', 'employment', 'tourism', 'inflation'
  ]

  for (let i = 0; i < count; i++) {
    const indicator = indicators[Math.floor(Math.random() * indicators.length)]
    const type = types[Math.floor(Math.random() * types.length)]
    const category = categories[Math.floor(Math.random() * categories.length)]
    const value = Math.random() * 10
    const strength = Math.random() * 0.5 + 0.5 // 0.5 to 1
    const confidence = Math.random() * 0.4 + 0.6 // 0.6 to 1

    const signal: EconomicSignal = {
      id: `mock-signal-${i}`,
      date: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
      indicator,
      type,
      strength,
      confidence,
      value,
      previousValue: value + (Math.random() - 0.5) * 2,
      threshold: type === 'warning' ? value * 1.1 : value * 0.9,
      description: `Mock ${type} signal for ${indicator.toUpperCase()} with ${Math.round(strength * 100)}% strength`,
      category,
      metadata: {
        deviation: Math.random() * 0.2,
        trend: (Math.random() - 0.5) * 0.1,
        dataPoints: Math.floor(Math.random() * 10) + 3,
        triggeredBy: 'mock_generator'
      },
      createdAt: new Date().toISOString()
    }

    mockSignals.push(signal)
  }

  return mockSignals.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}

/**
 * Filter signals by time period
 */
export function filterSignalsByTime(
  signals: EconomicSignal[],
  timePeriod: 'hour' | 'day' | 'week' | 'month'
): EconomicSignal[] {
  const now = new Date()
  const timeMap = {
    hour: 60 * 60 * 1000,
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000
  }

  const timeLimit = timeMap[timePeriod]

  return signals.filter(signal => {
    const signalDate = new Date(signal.date)
    return (now.getTime() - signalDate.getTime()) <= timeLimit
  })
}

/**
 * Group signals by category
 */
export function groupSignalsByCategory(signals: EconomicSignal[]): Record<string, EconomicSignal[]> {
  return signals.reduce((groups, signal) => {
    const category = signal.category
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(signal)
    return groups
  }, {} as Record<string, EconomicSignal[]>)
}

/**
 * Calculate signal statistics
 */
export function calculateSignalStatistics(signals: EconomicSignal[]) {
  const stats = {
    total: signals.length,
    byType: {} as Record<string, number>,
    byCategory: {} as Record<string, number>,
    averageStrength: 0,
    averageConfidence: 0,
    highConfidence: 0,
    recent: 0
  }

  signals.forEach(signal => {
    // Count by type
    stats.byType[signal.type] = (stats.byType[signal.type] || 0) + 1

    // Count by category
    stats.byCategory[signal.category] = (stats.byCategory[signal.category] || 0) + 1

    // Accumulate strength and confidence
    stats.averageStrength += signal.strength
    stats.averageConfidence += signal.confidence

    // Count high confidence signals
    if (signal.confidence > 0.8) {
      stats.highConfidence++
    }

    // Count recent signals (last 24 hours)
    const now = new Date()
    const signalDate = new Date(signal.date)
    if ((now.getTime() - signalDate.getTime()) < 24 * 60 * 60 * 1000) {
      stats.recent++
    }
  })

  // Calculate averages
  if (signals.length > 0) {
    stats.averageStrength /= signals.length
    stats.averageConfidence /= signals.length
  }

  return stats
}