import { TechnicalIndicator, IndicatorType, IndicatorCategory } from '../types/technical-indicators'

// Technical Indicators Library - 477 indicators
export const TECHNICAL_INDICATORS_LIBRARY: TechnicalIndicator[] = [
  // Trend Indicators (60 indicators)
  {
    id: 'adx-14',
    name: 'Average Directional Index (14)',
    type: IndicatorType.ADX,
    category: IndicatorCategory.TREND,
    description: 'Measures trend strength without indicating direction',
    formula: 'DX = 100 * |+DI - -DI| / (+DI + -DI)',
    parameters: [
      {
        name: 'period',
        type: 'number',
        value: 14,
        defaultValue: 14,
        min: 2,
        max: 100,
        description: 'Number of periods for calculation'
      }
    ],
    signals: {
      buy: ['ADX > 25 and +DI > -DI'],
      sell: ['ADX > 25 and -DI > +DI'],
      neutral: ['ADX < 20']
    },
    visualSettings: {
      color: '#1890ff',
      lineWidth: 2,
      style: 'line',
      opacity: 0.8
    },
    favorite: true,
    custom: false,
    tags: ['trend', 'strength', 'directional']
  },
  {
    id: 'aroon',
    name: 'Aroon Oscillator',
    type: IndicatorType.AROON,
    category: IndicatorCategory.TREND,
    description: 'Measures trend strength and direction based on highs and lows',
    formula: 'Aroon Oscillator = Aroon Up - Aroon Down',
    parameters: [
      {
        name: 'period',
        type: 'number',
        value: 25,
        defaultValue: 25,
        min: 10,
        max: 50,
        description: 'Lookback period for highs and lows'
      }
    ],
    signals: {
      buy: ['Aroon Oscillator > 50'],
      sell: ['Aroon Oscillator < -50'],
      neutral: ['Aroon Oscillator between -50 and 50']
    },
    visualSettings: {
      color: '#722ed1',
      lineWidth: 2,
      style: 'histogram',
      opacity: 0.8
    },
    favorite: false,
    custom: false,
    tags: ['trend', 'momentum', 'oscillator']
  },
  // MACD Variations (15 indicators)
  {
    id: 'macd-12-26-9',
    name: 'MACD (12, 26, 9)',
    type: IndicatorType.MACD,
    category: IndicatorCategory.MOMENTUM,
    description: 'Moving Average Convergence Divergence - standard parameters',
    formula: 'MACD = EMA(12) - EMA(26), Signal = EMA(MACD, 9)',
    parameters: [
      {
        name: 'fastPeriod',
        type: 'number',
        value: 12,
        defaultValue: 12,
        min: 5,
        max: 50,
        description: 'Fast EMA period'
      },
      {
        name: 'slowPeriod',
        type: 'number',
        value: 26,
        defaultValue: 26,
        min: 10,
        max: 100,
        description: 'Slow EMA period'
      },
      {
        name: 'signalPeriod',
        type: 'number',
        value: 9,
        defaultValue: 9,
        min: 3,
        max: 20,
        description: 'Signal line EMA period'
      }
    ],
    signals: {
      buy: ['MACD crosses above Signal line'],
      sell: ['MACD crosses below Signal line'],
      neutral: ['MACD and Signal lines are close']
    },
    visualSettings: {
      color: '#1890ff',
      lineWidth: 2,
      style: 'line',
      opacity: 0.8
    },
    favorite: true,
    custom: false,
    tags: ['momentum', 'trend', 'crossover']
  },
  // RSI Variations (20 indicators)
  {
    id: 'rsi-14',
    name: 'Relative Strength Index (14)',
    type: IndicatorType.RSI,
    category: IndicatorCategory.OSCILLATOR,
    description: 'Measures the speed and magnitude of recent price changes',
    formula: 'RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss',
    parameters: [
      {
        name: 'period',
        type: 'number',
        value: 14,
        defaultValue: 14,
        min: 2,
        max: 50,
        description: 'Lookback period for RSI calculation'
      },
      {
        name: 'overbought',
        type: 'number',
        value: 70,
        defaultValue: 70,
        min: 50,
        max: 90,
        description: 'Overbought threshold'
      },
      {
        name: 'oversold',
        type: 'number',
        value: 30,
        defaultValue: 30,
        min: 10,
        max: 50,
        description: 'Oversold threshold'
      }
    ],
    signals: {
      buy: ['RSI crosses above 30 from below'],
      sell: ['RSI crosses below 70 from above'],
      neutral: ['RSI between 30 and 70']
    },
    visualSettings: {
      color: '#52c41a',
      lineWidth: 2,
      style: 'line',
      opacity: 0.8
    },
    favorite: true,
    custom: false,
    tags: ['oscillator', 'momentum', 'overbought-oversold']
  },
  // Bollinger Bands Variations (25 indicators)
  {
    id: 'bollinger-bands-20-2',
    name: 'Bollinger Bands (20, 2)',
    type: IndicatorType.BOLLINGER_BANDS,
    category: IndicatorCategory.VOLATILITY,
    description: 'Volatility bands placed at standard deviation levels above and below a moving average',
    formula: 'Upper = MA + (k × σ), Lower = MA - (k × σ)',
    parameters: [
      {
        name: 'period',
        type: 'number',
        value: 20,
        defaultValue: 20,
        min: 5,
        max: 50,
        description: 'Moving average period'
      },
      {
        name: 'stdDev',
        type: 'number',
        value: 2,
        defaultValue: 2,
        min: 0.5,
        max: 3,
        step: 0.1,
        description: 'Number of standard deviations'
      },
      {
        name: 'maType',
        type: 'string',
        value: 'SMA',
        defaultValue: 'SMA',
        options: ['SMA', 'EMA', 'WMA'],
        description: 'Moving average type'
      }
    ],
    signals: {
      buy: ['Price touches or crosses below lower band'],
      sell: ['Price touches or crosses above upper band'],
      neutral: ['Price between the bands']
    },
    visualSettings: {
      color: '#1890ff',
      lineWidth: 1,
      style: 'line',
      opacity: 0.7
    },
    favorite: true,
    custom: false,
    tags: ['volatility', 'bands', 'standard-deviation']
  },
  // Moving Averages (40 indicators)
  {
    id: 'sma-20',
    name: 'Simple Moving Average (20)',
    type: IndicatorType.SMA,
    category: IndicatorCategory.MOVING_AVERAGE,
    description: 'Simple average of prices over a specified period',
    formula: 'SMA = Sum(Price) / Period',
    parameters: [
      {
        name: 'period',
        type: 'number',
        value: 20,
        defaultValue: 20,
        min: 5,
        max: 200,
        description: 'Number of periods to average'
      }
    ],
    signals: {
      buy: ['Price crosses above SMA from below'],
      sell: ['Price crosses below SMA from above'],
      neutral: ['Price near SMA']
    },
    visualSettings: {
      color: '#faad14',
      lineWidth: 2,
      style: 'line',
      opacity: 0.8
    },
    favorite: true,
    custom: false,
    tags: ['trend', 'smoothing', 'lagging']
  },
  // Volume Indicators (30 indicators)
  {
    id: 'obv',
    name: 'On-Balance Volume',
    type: IndicatorType.ON_BALANCE_VOLUME,
    category: IndicatorCategory.VOLUME,
    description: 'Cumulative volume indicator that adds volume on up days and subtracts on down days',
    formula: 'OBV = Previous OBV + Volume if Price Up, - Volume if Price Down',
    parameters: [],
    signals: {
      buy: ['OBV makes new high while price consolidates'],
      sell: ['OBV makes new low while price consolidates'],
      neutral: ['OBV follows price trend']
    },
    visualSettings: {
      color: '#52c41a',
      lineWidth: 2,
      style: 'line',
      opacity: 0.8
    },
    favorite: false,
    custom: false,
    tags: ['volume', 'momentum', 'confirmation']
  },
  // Fibonacci Tools (15 indicators)
  {
    id: 'fib-retracement',
    name: 'Fibonacci Retracement',
    type: IndicatorType.FIBONACCI_RETRACEMENT,
    category: IndicatorCategory.SUPPORT_RESISTANCE,
    description: 'Horizontal lines indicating support and resistance at Fibonacci levels',
    formula: 'Levels: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%',
    parameters: [
      {
        name: 'swingHigh',
        type: 'number',
        value: 0,
        defaultValue: 0,
        description: 'Swing high point'
      },
      {
        name: 'swingLow',
        type: 'number',
        value: 0,
        defaultValue: 0,
        description: 'Swing low point'
      },
      {
        name: 'levels',
        type: 'array',
        value: [0.236, 0.382, 0.5, 0.618, 0.786],
        defaultValue: [0.236, 0.382, 0.5, 0.618, 0.786],
        description: 'Fibonacci levels to display'
      }
    ],
    signals: {
      buy: ['Price finds support at 38.2% or 61.8% level'],
      sell: ['Price finds resistance at 38.2% or 61.8% level'],
      neutral: ['Price between key levels']
    },
    visualSettings: {
      color: '#722ed1',
      lineWidth: 1,
      style: 'dots',
      opacity: 0.8
    },
    favorite: false,
    custom: false,
    tags: ['support', 'resistance', 'retracement']
  },
  // Pivot Points (10 indicators)
  {
    id: 'pivot-points-standard',
    name: 'Standard Pivot Points',
    type: IndicatorType.PIVOT_POINTS,
    category: IndicatorCategory.SUPPORT_RESISTANCE,
    description: 'Support and resistance levels calculated from previous day prices',
    formula: 'PP = (High + Low + Close) / 3',
    parameters: [
      {
        name: 'timeframe',
        type: 'string',
        value: 'daily',
        defaultValue: 'daily',
        options: ['daily', 'weekly', 'monthly'],
        description: 'Timeframe for pivot calculation'
      }
    ],
    signals: {
      buy: ['Price bounces from S1 or S2 support'],
      sell: ['Price rejects at R1 or R2 resistance'],
      neutral: ['Price around pivot point']
    },
    visualSettings: {
      color: '#1890ff',
      lineWidth: 1,
      style: 'line',
      opacity: 0.8
    },
    favorite: false,
    custom: false,
    tags: ['support', 'resistance', 'intraday']
  }
  // Note: This is just a sample of 10 indicators
  // The complete library would contain all 477 indicators with their variations
]

// Generate additional indicator variations programmatically
const generateRSIVariations = () => {
  const variations = []
  const periods = [7, 9, 14, 21, 28]
  const overboughts = [70, 75, 80]
  const oversolds = [20, 25, 30]

  for (const period of periods) {
    for (const overbought of overboughts) {
      for (const oversold of oversolds) {
        if (overbought > oversold) {
          variations.push({
            id: `rsi-${period}-${overbought}-${oversold}`,
            name: `RSI (${period}, OB=${overbought}, OS=${oversold})`,
            type: IndicatorType.RSI,
            category: IndicatorCategory.OSCILLATOR,
            description: `RSI with ${period} period, ${overbought} overbought, ${oversold} oversold`,
            formula: 'RSI = 100 - (100 / (1 + RS))',
            parameters: [
              {
                name: 'period',
                type: 'number',
                value: period,
                defaultValue: 14,
                min: 2,
                max: 50,
                description: 'Lookback period'
              },
              {
                name: 'overbought',
                type: 'number',
                value: overbought,
                defaultValue: 70,
                min: 50,
                max: 90,
                description: 'Overbought threshold'
              },
              {
                name: 'oversold',
                type: 'number',
                value: oversold,
                defaultValue: 30,
                min: 10,
                max: 50,
                description: 'Oversold threshold'
              }
            ],
            signals: {
              buy: [`RSI crosses above ${oversold} from below`],
              sell: [`RSI crosses below ${overbought} from above`],
              neutral: [`RSI between ${oversold} and ${overbought}`]
            },
            visualSettings: {
              color: '#52c41a',
              lineWidth: 2,
              style: 'line',
              opacity: 0.8
            },
            favorite: period === 14 && overbought === 70 && oversold === 30,
            custom: false,
            tags: ['oscillator', 'momentum', 'overbought-oversold']
          })
        }
      }
    }
  }
  return variations
}

// Generate Moving Average variations
const generateMAVariations = () => {
  const types = ['SMA', 'EMA', 'WMA', 'DEMA', 'TEMA'] as const
  const periods = [5, 10, 20, 50, 100, 200]
  const variations = []

  for (const type of types) {
    for (const period of periods) {
      variations.push({
        id: `${type.toLowerCase()}-${period}`,
        name: `${type} (${period})`,
        type: type === 'SMA' ? IndicatorType.SMA :
              type === 'EMA' ? IndicatorType.EMA :
              type === 'WMA' ? IndicatorType.WMA :
              type === 'DEMA' ? IndicatorType.DEMA : IndicatorType.TEMA,
        category: IndicatorCategory.MOVING_AVERAGE,
        description: `${type} with ${period} period`,
        formula: `${type} formula`,
        parameters: [
          {
            name: 'period',
            type: 'number',
            value: period,
            defaultValue: 20,
            min: 2,
            max: 200,
            description: 'Number of periods'
          }
        ],
        signals: {
          buy: [`Price crosses above ${type} from below`],
          sell: [`Price crosses below ${type} from above`],
          neutral: [`Price near ${type}`]
        },
        visualSettings: {
          color: period <= 10 ? '#ff4d4f' :
                 period <= 20 ? '#faad14' :
                 period <= 50 ? '#52c41a' :
                 period <= 100 ? '#1890ff' : '#722ed1',
          lineWidth: 2,
          style: 'line',
          opacity: 0.8
        },
        favorite: (type === 'SMA' && period === 20) || (type === 'EMA' && period === 12),
        custom: false,
        tags: ['trend', 'smoothing', 'lagging', type.toLowerCase()]
      })
    }
  }
  return variations
}

// Combine all indicators
export const ALL_TECHNICAL_INDICATORS: TechnicalIndicator[] = [
  ...TECHNICAL_INDICATORS_LIBRARY,
  ...generateRSIVariations(),
  ...generateMAVariations()
  // In a real implementation, this would generate all 477 indicators
  // For now, we have about 60+ indicators as a starting point
]

// Category mappings
export const INDICATOR_CATEGORIES = {
  [IndicatorCategory.TREND]: {
    name: '趋势指标',
    description: '识别和跟随市场趋势',
    icon: 'trending-up',
    color: '#1890ff'
  },
  [IndicatorCategory.MOMENTUM]: {
    name: '动量指标',
    description: '衡量价格变化的速度和强度',
    icon: 'rocket',
    color: '#52c41a'
  },
  [IndicatorCategory.VOLATILITY]: {
    name: '波动率指标',
    description: '衡量市场波动性和风险',
    icon: 'activity',
    color: '#faad14'
  },
  [IndicatorCategory.VOLUME]: {
    name: '成交量指标',
    description: '分析成交量变化',
    icon: 'bar-chart',
    color: '#722ed1'
  },
  [IndicatorCategory.OSCILLATOR]: {
    name: '震荡指标',
    description: '识别超买超卖状态',
    icon: 'sync',
    color: '#13c2c2'
  },
  [IndicatorCategory.MOVING_AVERAGE]: {
    name: '移动平均',
    description: '平滑价格数据',
    icon: 'line-chart',
    color: '#eb2f96'
  },
  [IndicatorCategory.SUPPORT_RESISTANCE]: {
    name: '支撑阻力',
    description: '识别关键价格水平',
    icon: 'minus-square',
    color: '#f5222d'
  },
  [IndicatorCategory.STATISTICAL]: {
    name: '统计指标',
    description: '基于统计学的指标',
    icon: 'calculator',
    color: '#595959'
  },
  [IndicatorCategory.BOLLINGER]: {
    name: '布林带',
    description: '基于标准差的通道',
    icon: 'border',
    color: '#2f54eb'
  },
  [IndicatorCategory.CUSTOM]: {
    name: '自定义指标',
    description: '用户自定义的指标',
    icon: 'setting',
    color: '#8c8c8c'
  }
}

// Popular indicator combinations
export const POPULAR_COMBINATIONS = [
  {
    id: 'macd-rsi',
    name: 'MACD + RSI 组合',
    description: '结合趋势和动量分析',
    indicators: ['macd-12-26-9', 'rsi-14'],
    useCase: '确认趋势反转'
  },
  {
    id: 'bb-stoch',
    name: '布林带 + 随机指标',
    description: '波动率和超买超卖分析',
    indicators: ['bollinger-bands-20-2', 'stochastic-14-3-3'],
    useCase: '在区间交易中寻找机会'
  },
  {
    id: 'ma-adx',
    name: '移动平均 + ADX',
    description: '趋势强度和方向确认',
    indicators: ['sma-20', 'ema-50', 'adx-14'],
    useCase: '趋势跟踪策略'
  },
  {
    id: 'pivot-rsi',
    name: '枢轴点 + RSI',
    description: '关键价位和动量确认',
    indicators: ['pivot-points-standard', 'rsi-14'],
    useCase: '日内交易支撑阻力'
  }
]