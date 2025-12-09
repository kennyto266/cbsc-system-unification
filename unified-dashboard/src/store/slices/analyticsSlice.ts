import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AnalyticsData, ChartData } from '@types/index'

const initialState: AnalyticsData | null = null

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setAnalyticsData: (state, action: PayloadAction<AnalyticsData>) => {
      return action.payload
    },
    updatePortfolioMetrics: (state, action: PayloadAction<Partial<AnalyticsData['portfolio']>>) => {
      if (state) {
        state.portfolio = { ...state.portfolio, ...action.payload }
      }
    },
    updateStrategyPerformance: (state, action: PayloadAction<{ strategyId: string; performance: any }>) => {
      if (state) {
        const { strategyId, performance } = action.payload
        const strategyIndex = state.strategies.findIndex(s => s.id === strategyId)
        if (strategyIndex !== -1) {
          state.strategies[strategyIndex].performance = performance
        }
      }
    },
    updateMarketConditions: (state, action: PayloadAction<Partial<AnalyticsData['market']>>) => {
      if (state) {
        state.market = { ...state.market, ...action.payload }
      }
    },
    addStrategyToAnalytics: (state, action: PayloadAction<any>) => {
      if (state) {
        state.strategies.push(action.payload)
      }
    },
    removeStrategyFromAnalytics: (state, action: PayloadAction<string>) => {
      if (state) {
        state.strategies = state.strategies.filter(s => s.id !== action.payload)
      }
    },
    clearAnalyticsData: () => {
      return null
    },
  },
})

export const {
  setAnalyticsData,
  updatePortfolioMetrics,
  updateStrategyPerformance,
  updateMarketConditions,
  addStrategyToAnalytics,
  removeStrategyFromAnalytics,
  clearAnalyticsData,
} = analyticsSlice.actions

export default analyticsSlice.reducer

// Selectors
export const selectAnalyticsData = (state: { analytics: AnalyticsData | null }) => state.analytics
export const selectPortfolioMetrics = (state: { analytics: AnalyticsData | null }) => state.analytics?.portfolio
export const selectStrategyAnalytics = (state: { analytics: AnalyticsData | null }) => state.analytics?.strategies
export const selectMarketConditions = (state: { analytics: AnalyticsData | null }) => state.analytics?.market
export const selectStrategyAnalyticsById = (state: { analytics: AnalyticsData | null }, id: string) =>
  state.analytics?.strategies.find(s => s.id === id)