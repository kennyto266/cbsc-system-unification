import { createApi } from '@reduxjs/toolkit/query/react'
import { baseQueryWithReauth, providesList } from '../baseQuery'

// Portfolio types
export interface PortfolioHolding {
  symbol: string
  name: string
  quantity: number
  averageCost: number
  currentPrice: number
  marketValue: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  weight: number
}

export interface PortfolioSummary {
  totalValue: number
  totalCost: number
  totalPnL: number
  totalPnLPercent: number
  dailyChange: number
  dailyChangePercent: number
  cash: number
  cashPercent: number
  holdingsCount: number
  lastUpdate: string
}

export interface PortfolioAnalytics {
  summary: PortfolioSummary
  holdings: PortfolioHolding[]
  performance: {
    daily: number
    weekly: number
    monthly: number
    ytd: number
  }
  risk: {
    volatility: number
    beta: number
    var: number
  }
  diversification: {
    sectors: Record<string, number>
    assetClasses: Record<string, number>
  }
}

export interface RebalanceRequest {
  targetAllocations: Record<string, number>
  threshold: number
}

// Portfolio API slice
export const portfolioApi = createApi({
  reducerPath: 'portfolioApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Portfolio', 'Holding'],
  keepUnusedDataFor: 60, // Keep data for 1 minute
  endpoints: (builder) => ({
    // Get portfolio overview/summary
    getPortfolioSummary: builder.query<PortfolioSummary, void>({
      query: () => '/analytics/portfolio/overview',
      providesTags: ['Portfolio'],
    }),

    // Get full portfolio analytics
    getPortfolioAnalytics: builder.query<PortfolioAnalytics, {
      includeCorrelations?: boolean
    }>({
      query: (params) => ({
        url: '/analytics/portfolio',
        params,
      }),
      providesTags: ['Portfolio', 'Holding'],
    }),

    // Get portfolio holdings
    getPortfolioHoldings: builder.query<PortfolioHolding[], void>({
      query: () => '/analytics/portfolio/holdings',
      providesTags: (result) => providesList(result || [], 'Holding'),
    }),

    // Get portfolio risk metrics
    getPortfolioRisk: builder.query<{
      volatility: number
      beta: number
      var: number
      cvar: number
      maxDrawdown: number
      sharpeRatio: number
    }, void>({
      query: () => '/analytics/portfolio/risk',
      providesTags: ['Portfolio'],
    }),

    // Get portfolio diversification analysis
    getPortfolioDiversification: builder.query<{
      sectors: Record<string, number>
      assetClasses: Record<string, number>
      geographic: Record<string, number>
      concentration: number
      recommendations: string[]
    }, void>({
      query: () => '/analytics/portfolio/diversification',
      providesTags: ['Portfolio'],
    }),

    // Rebalance portfolio
    rebalancePortfolio: builder.mutation<{
      success: boolean
      trades: Array<{
        symbol: string
        action: 'buy' | 'sell'
        quantity: number
        targetWeight: number
        currentWeight: number
      }>
    }, RebalanceRequest>({
      query: (data) => ({
        url: '/analytics/portfolio/rebalance',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Portfolio', 'Holding'],
    }),

    // Get portfolio performance history
    getPortfolioPerformance: builder.query<{
      date: string
      value: number
      returns: number
    }[], {
      period?: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'
      granularity?: 'daily' | 'weekly' | 'monthly'
    }>({
      query: (params) => ({
        url: '/analytics/portfolio/performance',
        params,
      }),
      providesTags: ['Portfolio'],
    }),
  }),
})

// Export hooks
export const {
  useGetPortfolioSummaryQuery,
  useGetPortfolioAnalyticsQuery,
  useGetPortfolioHoldingsQuery,
  useGetPortfolioRiskQuery,
  useGetPortfolioDiversificationQuery,
  useRebalancePortfolioMutation,
  useGetPortfolioPerformanceQuery,
} = portfolioApi
