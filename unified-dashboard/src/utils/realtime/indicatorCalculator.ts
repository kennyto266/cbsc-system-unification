import { ChartDataPoint } from '../../components/charts/RealTime/RealTimeChartProvider'

// Technical indicator calculation utilities
export interface IndicatorResult {
  values: number[]
  metadata?: Record<string, any>
}

export interface IndicatorOptions {
  period?: number
  multiplier?: number
  fastPeriod?: number
  slowPeriod?: number
  signalPeriod?: number
  kPeriod?: number
  dPeriod?: number
  deviation?: number
  [key: string]: any
}

// Moving average calculations
export class MovingAverages {
  // Simple Moving Average (SMA)
  static sma(data: number[], period: number): number[] {
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

  // Exponential Moving Average (EMA)
  static ema(data: number[], period: number): number[] {
    const result: number[] = []
    const multiplier = 2 / (period + 1)

    if (data.length === 0) return result

    result[0] = data[0]
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    }
    return result
  }

  // Weighted Moving Average (WMA)
  static wma(data: number[], period: number): number[] {
    const result: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        let sum = 0
        let weightSum = 0

        for (let j = 0; j < period; j++) {
          const weight = j + 1
          sum += data[i - j] * weight
          weightSum += weight
        }

        result.push(sum / weightSum)
      }
    }
    return result
  }

  // Hull Moving Average (HMA)
  static hma(data: number[], period: number): number[] {
    const halfPeriod = Math.floor(period / 2)
    const sqrtPeriod = Math.floor(Math.sqrt(period))

    const wmaHalf = this.wma(data, halfPeriod)
    const wmaFull = this.wma(data, period)

    const rawHMA: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (isNaN(wmaHalf[i]) || isNaN(wmaFull[i])) {
        rawHMA.push(NaN)
      } else {
        rawHMA.push(2 * wmaHalf[i] - wmaFull[i])
      }
    }

    return this.wma(rawHMA, sqrtPeriod)
  }
}

// Oscillator calculations
export class Oscillators {
  // Relative Strength Index (RSI)
  static rsi(data: number[], period: number = 14): number[] {
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(NaN)
      } else {
        let gains = 0
        let losses = 0

        for (let j = i - period + 1; j <= i; j++) {
          const change = data[j] - data[j - 1]
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
  }

  // Stochastic Oscillator
  static stochastic(
    highs: number[],
    lows: number[],
    closes: number[],
    kPeriod: number = 14,
    dPeriod: number = 3
  ): { k: number[]; d: number[] } {
    const k: number[] = []
    const d: number[] = []

    for (let i = 0; i < closes.length; i++) {
      if (i < kPeriod - 1) {
        k.push(NaN)
      } else {
        const periodHighs = highs.slice(i - kPeriod + 1, i + 1)
        const periodLows = lows.slice(i - kPeriod + 1, i + 1)

        const highestHigh = Math.max(...periodHighs)
        const lowestLow = Math.min(...periodLows)

        const kValue = ((closes[i] - lowestLow) / (highestHigh - lowestLow)) * 100
        k.push(kValue)
      }
    }

    // Calculate %D as SMA of %K
    d.push(...MovingAverages.sma(k, dPeriod))

    return { k, d }
  }

  // MACD (Moving Average Convergence Divergence)
  static macd(
    data: number[],
    fastPeriod: number = 12,
    slowPeriod: number = 26,
    signalPeriod: number = 9
  ): { macd: number[]; signal: number[]; histogram: number[] } {
    const emaFast = MovingAverages.ema(data, fastPeriod)
    const emaSlow = MovingAverages.ema(data, slowPeriod)

    const macdLine = emaFast.map((fast, i) => fast - emaSlow[i])
    const signalLine = MovingAverages.ema(macdLine, signalPeriod)

    const histogram = macdLine.map((macd, i) => macd - signalLine[i])

    return { macd: macdLine, signal: signalLine, histogram }
  }

  // Williams %R
  static williamsR(
    highs: number[],
    lows: number[],
    closes: number[],
    period: number = 14
  ): number[] {
    const result: number[] = []

    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const periodHighs = highs.slice(i - period + 1, i + 1)
        const periodLows = lows.slice(i - period + 1, i + 1)

        const highestHigh = Math.max(...periodHighs)
        const lowestLow = Math.min(...periodLows)

        const williamsR = ((highestHigh - closes[i]) / (highestHigh - lowestLow)) * -100
        result.push(williamsR)
      }
    }
    return result
  }

  // Commodity Channel Index (CCI)
  static cci(
    highs: number[],
    lows: number[],
    closes: number[],
    period: number = 20
  ): number[] {
    const result: number[] = []

    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const typicalPrices: number[] = []
        for (let j = i - period + 1; j <= i; j++) {
          typicalPrices.push((highs[j] + lows[j] + closes[j]) / 3)
        }

        const sma = MovingAverages.sma(typicalPrices, period)[period - 1]
        const meanDeviation = typicalPrices.reduce((sum, tp) => sum + Math.abs(tp - sma), 0) / period

        const cci = (typicalPrices[typicalPrices.length - 1] - sma) / (0.015 * meanDeviation)
        result.push(cci)
      }
    }
    return result
  }
}

// Volume indicators
export class VolumeIndicators {
  // On-Balance Volume (OBV)
  static obv(closes: number[], volumes: number[]): number[] {
    const result: number[] = [volumes[0]]

    for (let i = 1; i < closes.length; i++) {
      if (closes[i] > closes[i - 1]) {
        result.push(result[i - 1] + volumes[i])
      } else if (closes[i] < closes[i - 1]) {
        result.push(result[i - 1] - volumes[i])
      } else {
        result.push(result[i - 1])
      }
    }
    return result
  }

  // Volume Weighted Average Price (VWAP)
  static vwap(data: ChartDataPoint[]): number[] {
    const result: number[] = []
    let cumulativeVolume = 0
    let cumulativeVolumePrice = 0

    for (let i = 0; i < data.length; i++) {
      const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3
      cumulativeVolume += data[i].volume
      cumulativeVolumePrice += typicalPrice * data[i].volume

      result.push(cumulativeVolumePrice / cumulativeVolume)
    }
    return result
  }

  // Money Flow Index (MFI)
  static mfi(
    highs: number[],
    lows: number[],
    closes: number[],
    volumes: number[],
    period: number = 14
  ): number[] {
    const result: number[] = []

    for (let i = 0; i < closes.length; i++) {
      if (i < period) {
        result.push(NaN)
      } else {
        let positiveMoneyFlow = 0
        let negativeMoneyFlow = 0

        for (let j = i - period + 1; j <= i; j++) {
          const typicalPrice = (highs[j] + lows[j] + closes[j]) / 3
          const rawMoneyFlow = typicalPrice * volumes[j]

          if (j > 0) {
            const previousTypicalPrice = (highs[j - 1] + lows[j - 1] + closes[j - 1]) / 3
            if (typicalPrice > previousTypicalPrice) {
              positiveMoneyFlow += rawMoneyFlow
            } else if (typicalPrice < previousTypicalPrice) {
              negativeMoneyFlow += rawMoneyFlow
            }
          }
        }

        const moneyRatio = positiveMoneyFlow / negativeMoneyFlow
        const mfi = 100 - (100 / (1 + moneyRatio))
        result.push(mfi)
      }
    }
    return result
  }
}

// Volatility indicators
export class VolatilityIndicators {
  // Bollinger Bands
  static bollingerBands(
    data: number[],
    period: number = 20,
    stdDev: number = 2
  ): { upper: number[]; middle: number[]; lower: number[] } {
    const middle = MovingAverages.sma(data, period)
    const upper: number[] = []
    const lower: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(NaN)
        lower.push(NaN)
      } else {
        const periodData = data.slice(i - period + 1, i + 1)
        const mean = middle[i]

        const variance = periodData.reduce((sum, d) => sum + Math.pow(d - mean, 2), 0) / period
        const standardDeviation = Math.sqrt(variance)

        upper.push(mean + (standardDeviation * stdDev))
        lower.push(mean - (standardDeviation * stdDev))
      }
    }

    return { upper, middle, lower }
  }

  // Average True Range (ATR)
  static atr(data: ChartDataPoint[], period: number = 14): number[] {
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
  }

  // Keltner Channels
  static keltnerChannels(
    data: ChartDataPoint[],
    period: number = 20,
    multiplier: number = 2
  ): { upper: number[]; middle: number[]; lower: number[] } {
    const closes = data.map(d => d.close)
    const trs = this.atr(data, period)
    const middle = MovingAverages.sma(closes, period)

    const upper: number[] = []
    const lower: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(NaN)
        lower.push(NaN)
      } else {
        upper.push(middle[i] + (trs[i] * multiplier))
        lower.push(middle[i] - (trs[i] * multiplier))
      }
    }

    return { upper, middle, lower }
  }
}

// Trend indicators
export class TrendIndicators {
  // Average Directional Index (ADX)
  static adx(
    highs: number[],
    lows: number[],
    closes: number[],
    period: number = 14
  ): { adx: number[]; plusDI: number[]; minusDI: number[] } {
    const result: { adx: number[]; plusDI: number[]; minusDI: number[] } = {
      adx: [],
      plusDI: [],
      minusDI: []
    }

    const upMoves: number[] = []
    const downMoves: number[] = []
    const plusDM: number[] = []
    const minusDM: number[] = []

    for (let i = 1; i < highs.length; i++) {
      const upMove = highs[i] - highs[i - 1]
      const downMove = lows[i - 1] - lows[i]

      upMoves.push(upMove > downMove && upMove > 0 ? upMove : 0)
      downMoves.push(downMove > upMove && downMove > 0 ? downMove : 0)

      plusDM.push(upMoves[i - 1] > downMoves[i - 1] ? upMoves[i - 1] : 0)
      minusDM.push(downMoves[i - 1] > upMoves[i - 1] ? downMoves[i - 1] : 0)
    }

    const tr = this.atr(
      highs.map((h, i) => ({ high: h, low: lows[i], close: closes[i], open: closes[i], timestamp: i, volume: 0 })),
      period
    )

    const plusDI = MovingAverages.ema(
      plusDM.map((dm, i) => (tr[i] > 0 ? (dm / tr[i]) * 100 : 0)),
      period
    )

    const minusDI = MovingAverages.ema(
      minusDM.map((dm, i) => (tr[i] > 0 ? (dm / tr[i]) * 100 : 0)),
      period
    )

    const dx = plusDI.map((plus, i) => {
      const minus = minusDI[i]
      const sum = plus + minus
      return sum > 0 ? Math.abs(plus - minus) / sum * 100 : 0
    })

    result.adx = MovingAverages.ema(dx, period)
    result.plusDI = plusDI
    result.minusDI = minusDI

    return result
  }

  // Parabolic SAR
  static psar(
    highs: number[],
    lows: number[],
    closes: number[],
    acceleration: number = 0.02,
    maximum: number = 0.2
  ): number[] {
    const result: number[] = []
    let psar = lows[0]
    let ep = highs[0]
    let af = acceleration
    let isUptrend = true

    for (let i = 0; i < highs.length; i++) {
      result.push(psar)

      if (isUptrend) {
        psar = psar + af * (ep - psar)

        if (lows[i] < psar) {
          isUptrend = false
          psar = ep
          ep = lows[i]
          af = acceleration
        } else {
          if (highs[i] > ep) {
            ep = highs[i]
            af = Math.min(af + acceleration, maximum)
          }
        }
      } else {
        psar = psar + af * (ep - psar)

        if (highs[i] > psar) {
          isUptrend = true
          psar = ep
          ep = highs[i]
          af = acceleration
        } else {
          if (lows[i] < ep) {
            ep = lows[i]
            af = Math.min(af + acceleration, maximum)
          }
        }
      }
    }

    return result
  }
}

// Main indicator calculator
export class IndicatorCalculator {
  // Calculate any indicator by type
  static calculate(
    type: string,
    data: ChartDataPoint[],
    options: IndicatorOptions = {}
  ): IndicatorResult {
    const closes = data.map(d => d.close)
    const highs = data.map(d => d.high)
    const lows = data.map(d => d.low)
    const volumes = data.map(d => d.volume)

    switch (type.toUpperCase()) {
      // Moving Averages
      case 'SMA':
        return { values: MovingAverages.sma(closes, options.period || 20) }
      case 'EMA':
        return { values: MovingAverages.ema(closes, options.period || 20) }
      case 'WMA':
        return { values: MovingAverages.wma(closes, options.period || 20) }
      case 'HMA':
        return { values: MovingAverages.hma(closes, options.period || 20) }

      // Oscillators
      case 'RSI':
        return { values: Oscillators.rsi(closes, options.period || 14) }
      case 'STOCH':
        const stoch = Oscillators.stochastic(highs, lows, closes, options.kPeriod, options.dPeriod)
        return { values: stoch.k, metadata: { signal: stoch.d } }
      case 'MACD':
        const macd = Oscillators.macd(closes, options.fastPeriod, options.slowPeriod, options.signalPeriod)
        return {
          values: macd.macd,
          metadata: { signal: macd.signal, histogram: macd.histogram }
        }
      case 'WILLIAMS_R':
        return { values: Oscillators.williamsR(highs, lows, closes, options.period || 14) }
      case 'CCI':
        return { values: Oscillators.cci(highs, lows, closes, options.period || 20) }

      // Volume Indicators
      case 'OBV':
        return { values: VolumeIndicators.obv(closes, volumes) }
      case 'VWAP':
        return { values: VolumeIndicators.vwap(data) }
      case 'MFI':
        return { values: VolumeIndicators.mfi(highs, lows, closes, volumes, options.period || 14) }

      // Volatility Indicators
      case 'BB':
        const bb = VolatilityIndicators.bollingerBands(closes, options.period || 20, options.deviation || 2)
        return {
          values: bb.middle,
          metadata: { upper: bb.upper, lower: bb.lower }
        }
      case 'ATR':
        return { values: VolatilityIndicators.atr(data, options.period || 14) }
      case 'KELTNER':
        const keltner = VolatilityIndicators.keltnerChannels(data, options.period || 20, options.multiplier || 2)
        return {
          values: keltner.middle,
          metadata: { upper: keltner.upper, lower: keltner.lower }
        }

      // Trend Indicators
      case 'ADX':
        const adx = TrendIndicators.adx(highs, lows, closes, options.period || 14)
        return {
          values: adx.adx,
          metadata: { plusDI: adx.plusDI, minusDI: adx.minusDI }
        }
      case 'PSAR':
        return { values: TrendIndicators.psar(highs, lows, closes, options.acceleration, options.maximum) }

      default:
        throw new Error(`Unknown indicator type: ${type}`)
    }
  }

  // Calculate multiple indicators
  static calculateMultiple(
    types: string[],
    data: ChartDataPoint[],
    options: IndicatorOptions = {}
  ): Map<string, IndicatorResult> {
    const results = new Map<string, IndicatorResult>()

    types.forEach(type => {
      try {
        results.set(type, this.calculate(type, data, options))
      } catch (error) {
        console.error(`Failed to calculate ${type}:`, error)
      }
    })

    return results
  }

  // Validate indicator options
  static validateOptions(type: string, options: IndicatorOptions): boolean {
    switch (type.toUpperCase()) {
      case 'SMA':
      case 'EMA':
      case 'WMA':
      case 'RSI':
      case 'WILLIAMS_R':
      case 'ATR':
        return options.period && options.period > 0 && options.period < 1000

      case 'MACD':
        return options.fastPeriod && options.slowPeriod && options.signalPeriod &&
               options.fastPeriod < options.slowPeriod && options.fastPeriod > 0 && options.slowPeriod < 1000

      case 'BB':
      case 'KELTNER':
        return options.period && options.period > 0 && options.period < 1000 &&
               options.deviation && options.deviation > 0 && options.deviation < 5

      case 'STOCH':
        return options.kPeriod && options.dPeriod && options.kPeriod > 0 && options.dPeriod > 0

      default:
        return true
    }
  }
}

export default IndicatorCalculator