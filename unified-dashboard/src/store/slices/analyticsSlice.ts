import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

// Enhanced interfaces for analytics
interface PerformanceData {
  portfolioValue: number
  dailyReturn: number
  totalReturn: number
  volatility: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  alpha: number
  beta: number
  informationRatio: number
}

interface MarketData {
  dailyChange: number
  volume: number
  prices: Record<string, number>
}

interface BacktestResult {
  id: string
  strategyId: string
  startDate: string
  endDate: string
  initialValue: number
  finalValue: number
  totalReturn: number
  sharpeRatio: number
  maxDrawdown: number
  trades: number[]
}

interface AnalyticsState {
  // Basic metrics
  totalStrategies: number
  activeStrategies: number
  totalTrades: number
  successRate: number
  profitLoss: number

  // Enhanced data
  performanceData: PerformanceData | null
  marketData: MarketData | null
  backtestResults: BacktestResult[]
  riskMetrics: {
    var: number
    cvar: number
    correlationMatrix: number[][]
    beta: number
  } | null

  // Loading states
  loading: boolean
  error: string | null

  // Time range and filters
  timeRange: string
  benchmark: string
}

const initialState: AnalyticsState = {
  totalStrategies: 0,
  activeStrategies: 0,
  totalTrades: 0,
  successRate: 0,
  profitLoss: 0,
  performanceData: null,
  marketData: null,
  backtestResults: [],
  riskMetrics: null,
  loading: false,
  error: null,
  timeRange: '1y',
  benchmark: 'SPY',
}

// Async thunks
export const fetchAnalyticsData = createAsyncThunk(
  'analytics/fetchData',
  async ({ timeRange, benchmark }: { timeRange: string; benchmark: string }) => {
    // API call to fetch analytics data
    const response = await fetch(`/api/analytics?timeRange=${timeRange}&benchmark=${benchmark}`)
    if (!response.ok) {
      throw new Error('Failed to fetch analytics data')
    }
    return response.json()
  }
)

export const fetchBacktestResults = createAsyncThunk(
  'analytics/fetchBacktestResults',
  async (strategyId?: string) => {
    const url = strategyId ? `/api/backtest/${strategyId}` : '/api/backtest'
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to fetch backtest results')
    }
    return response.json()
  }
)

export const runBacktest = createAsyncThunk(
  'analytics/runBacktest',
  async (params: {
    strategyId: string
    startDate: string
    endDate: string
    initialValue: number
  }) => {
    const response = await fetch('/api/backtest/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    })
    if (!response.ok) {
      throw new Error('Failed to run backtest')
    }
    return response.json()
  }
)

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setAnalytics: (state, action) => {
      return { ...state, ...action.payload }
    },
    setTimeRange: (state, action: PayloadAction<string>) => {
      state.timeRange = action.payload
    },
    setBenchmark: (state, action: PayloadAction<string>) => {
      state.benchmark = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
    updateRealtimeData: (state, action) => {
      if (state.performanceData) {
        state.performanceData = {
          ...state.performanceData,
          ...action.payload,
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch analytics data
      .addCase(fetchAnalyticsData.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAnalyticsData.fulfilled, (state, action) => {
        state.loading = false
        state.performanceData = action.payload.performance
        state.marketData = action.payload.market
        state.riskMetrics = action.payload.risk
      })
      .addCase(fetchAnalyticsData.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch analytics data'
      })

      // Fetch backtest results
      .addCase(fetchBacktestResults.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBacktestResults.fulfilled, (state, action) => {
        state.loading = false
        state.backtestResults = action.payload
      })
      .addCase(fetchBacktestResults.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch backtest results'
      })

      // Run backtest
      .addCase(runBacktest.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(runBacktest.fulfilled, (state, action) => {
        state.loading = false
        state.backtestResults.push(action.payload)
      })
      .addCase(runBacktest.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to run backtest'
      })
  },
})

export const { setAnalytics, setTimeRange, setBenchmark, clearError, updateRealtimeData } = analyticsSlice.actions

// Selectors
export const selectAnalytics = (state: { analytics: AnalyticsState }) => state.analytics
export const selectPerformanceData = (state: { analytics: AnalyticsState }) => state.analytics.performanceData
export const selectBacktestResults = (state: { analytics: AnalyticsState }) => state.analytics.backtestResults

export default analyticsSlice.reducer
