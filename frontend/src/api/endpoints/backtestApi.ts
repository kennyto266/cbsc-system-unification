import { createApi } from '@reduxjs/toolkit/query/react'
import { baseQueryWithReauth, providesList } from '../baseQuery'

// Backtest types
export interface BacktestConfig {
  strategyId: string
  symbols: string[]
  startDate: string
  endDate: string
  initialCapital: number
  commission?: number
  slippage?: number
  parameters?: Record<string, any>
}

export interface BacktestResult {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  strategyId: string
  symbols: string[]
  startDate: string
  endDate: string
  initialCapital: number
  finalValue?: number
  totalReturn?: number
  annualReturn?: number
  sharpeRatio?: number
  maxDrawdown?: number
  winRate?: number
  profitFactor?: number
  createdAt: string
  completedAt?: string
  error?: string
}

export interface BacktestProgress {
  backtestId: string
  status: string
  progress: number
  currentStep: string
  totalSteps: number
  completedSteps: number
  estimatedTimeRemaining?: number
}

// Backtest API slice
export const backtestApi = createApi({
  reducerPath: 'backtestApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Backtest'],
  keepUnusedDataFor: 30, // Keep data for 30 seconds
  endpoints: (builder) => ({
    // List backtests
    listBacktests: builder.query<BacktestResult[], {
      strategyId?: string
      status?: string
    }>({
      query: (params) => ({
        url: '/v2/backtests/',
        params,
      }),
      providesTags: (result) => providesList(result || [], 'Backtest'),
    }),

    // Get backtest details
    getBacktest: builder.query<BacktestResult, string>({
      query: (id) => `/v2/backtests/${id}`,
      providesTags: (result, error, id) => [{ type: 'Backtest', id }],
    }),

    // Create backtest
    createBacktest: builder.mutation<BacktestResult, BacktestConfig>({
      query: (data) => ({
        url: '/v2/backtests/',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Backtest', id: 'LIST' }],
    }),

    // Run backtest
    runBacktest: builder.mutation<void, string>({
      query: (id) => ({
        url: `/v2/backtests/${id}/run`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Backtest', id },
        { type: 'Backtest', id: 'LIST' },
      ],
    }),

    // Stop backtest
    stopBacktest: builder.mutation<void, string>({
      query: (id) => ({
        url: `/v2/backtests/${id}/stop`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Backtest', id },
      ],
    }),

    // Get backtest progress
    getBacktestProgress: builder.query<BacktestProgress, string>({
      query: (id) => `/v2/backtests/${id}/progress`,
      providesTags: (result, error, id) => [{ type: 'Backtest', id }],
    }),

    // Delete backtest
    deleteBacktest: builder.mutation<void, string>({
      query: (id) => ({
        url: `/v2/backtests/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Backtest', id: 'LIST' }],
    }),
  }),
})

// Export hooks
export const {
  useListBacktestsQuery,
  useGetBacktestQuery,
  useCreateBacktestMutation,
  useRunBacktestMutation,
  useStopBacktestMutation,
  useGetBacktestProgressQuery,
  useDeleteBacktestMutation,
} = backtestApi
