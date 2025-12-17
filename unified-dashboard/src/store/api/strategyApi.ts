import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { Strategy, StrategyType, StrategyStatus } from '../../types'
import type { RootState } from '../index'

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: '/api/strategies',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('content-type', 'application/json')
    return headers
  },
})

export const strategyApi = createApi({
  reducerPath: 'strategyApi',
  baseQuery,
  tagTypes: ['Strategy', 'StrategyExecution'],
  endpoints: (builder) => ({
    // Get all strategies with optional filters
    getStrategies: builder.query<Strategy[], {
      type?: StrategyType
      status?: StrategyStatus
      riskLevel?: string
      page?: number
      limit?: number
      sortBy?: string
      sortOrder?: 'asc' | 'desc'
    }>({
      query: ({
        type,
        status,
        riskLevel,
        page = 1,
        limit = 20,
        sortBy = 'createdAt',
        sortOrder = 'desc',
      }) => ({
        url: '',
        params: {
          type,
          status,
          risk_level: riskLevel,
          page,
          limit,
          sort_by: sortBy,
          sort_order: sortOrder,
        },
      }),
      providesTags: ['Strategy'],
    }),

    // Get strategy by ID
    getStrategyDetails: builder.query<Strategy, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    // Create new strategy
    createStrategy: builder.mutation<Strategy, Partial<Strategy>>({
      query: (strategy) => ({
        url: '',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Update strategy
    updateStrategy: builder.mutation<Strategy, {
      id: string
      strategy: Partial<Strategy>
    }>({
      query: ({ id, strategy }) => ({
        url: `/${id}`,
        method: 'PUT',
        body: strategy,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Strategy', id }],
    }),

    // Delete strategy
    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Update strategy status
    updateStrategyStatus: builder.mutation<Strategy, {
      id: string
      status: StrategyStatus
    }>({
      query: ({ id, status }) => ({
        url: `/${id}/status`,
        method: 'PATCH',
        body: { status },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Strategy', id }],
    }),

    // Get strategy execution history
    getStrategyExecutionHistory: builder.query<Array<{
      id: string
      timestamp: string
      signal: 'BUY' | 'SELL' | 'HOLD'
      price: number
      quantity: number
      status: 'SUCCESS' | 'FAILED' | 'PENDING'
      pnl?: number
    }>, {
      strategyId: string
      startTime?: string
      endTime?: string
      limit?: number
    }>({
      query: ({
        strategyId,
        startTime,
        endTime,
        limit = 100,
      }) => ({
        url: `/${strategyId}/executions`,
        params: {
          start_time: startTime,
          end_time: endTime,
          limit,
        },
      }),
      providesTags: ['StrategyExecution'],
    }),

    // Backtest strategy
    backtestStrategy: builder.mutation<{
      backtestId: string
      results: {
        totalReturn: number
        sharpeRatio: number
        maxDrawdown: number
        winRate: number
        profitFactor: number
        totalTrades: number
      }
    }, {
      strategyId: string
      startDate: string
      endDate: string
      initialCapital?: number
      parameters?: Record<string, any>
    }>({
      query: ({
        strategyId,
        startDate,
        endDate,
        initialCapital = 100000,
        parameters,
      }) => ({
        url: `/${strategyId}/backtest`,
        method: 'POST',
        body: {
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
          parameters,
        },
      }),
    }),

    // Get backtest results
    getBacktestResults: builder.query<{
      id: string
      status: 'running' | 'completed' | 'failed'
      progress?: number
      results?: {
        totalReturn: number
        sharpeRatio: number
        maxDrawdown: number
        winRate: number
        profitFactor: number
        totalTrades: number
        equity: Array<{ date: string; value: number }>
        trades: Array<{
          timestamp: string
          type: 'BUY' | 'SELL'
          price: number
          quantity: number
          pnl: number
        }>
      }
      error?: string
    }, string>({
      query: (backtestId) => `/backtests/${backtestId}`,
      providesTags: ['Strategy'],
    }),

    // Get strategy performance metrics
    getStrategyMetrics: builder.query<{
      dailyReturns: Array<{ date: string; return: number }>
      monthlyReturns: Array<{ month: string; return: number }>
      yearlyReturns: Array<{ year: string; return: number }>
      rollingMetrics: Array<{
        date: string
        sharpeRatio: number
        maxDrawdown: number
        volatility: number
      }>
      riskMetrics: {
        var: number
        cvar: number
        beta: number
        alpha: number
      }
    }, {
      strategyId: string
      period?: '1M' | '3M' | '6M' | '1Y' | 'ALL'
      benchmark?: string
    }>({
      query: ({
        strategyId,
        period = '1Y',
        benchmark,
      }) => ({
        url: `/${strategyId}/metrics`,
        params: {
          period,
          benchmark,
        },
      }),
    }),

    // Clone strategy
    cloneStrategy: builder.mutation<Strategy, {
      strategyId: string
      name: string
      description?: string
    }>({
      query: ({
        strategyId,
        name,
        description,
      }) => ({
        url: `/${strategyId}/clone`,
        method: 'POST',
        body: {
          name,
          description,
        },
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Export strategy configuration
    exportStrategy: builder.mutation<Blob, {
      strategyId: string
      format: 'json' | 'yaml'
    }>({
      query: ({
        strategyId,
        format,
      }) => ({
        url: `/${strategyId}/export`,
        method: 'POST',
        body: { format },
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Import strategy configuration
    importStrategy: builder.mutation<Strategy, {
      file: File
      name?: string
    }>({
      query: ({ file, name }) => {
        const formData = new FormData()
        formData.append('file', file)
        if (name) {
          formData.append('name', name)
        }

        return {
          url: '/import',
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['Strategy'],
    }),

    // Get strategy templates
    getStrategyTemplates: builder.query<Array<{
      id: string
      name: string
      description: string
      type: StrategyType
      parameters: Record<string, any>
      tags: string[]
    }>, void>({
      query: () => '/templates',
    }),

    // Create strategy from template
    createFromTemplate: builder.mutation<Strategy, {
      templateId: string
      name: string
      description?: string
      parameters?: Record<string, any>
    }>({
      query: ({
        templateId,
        name,
        description,
        parameters,
      }) => ({
        url: `/templates/${templateId}/create`,
        method: 'POST',
        body: {
          name,
          description,
          parameters,
        },
      }),
      invalidatesTags: ['Strategy'],
    }),
  }),
})

// Export hooks
export const {
  // Queries
  useGetStrategiesQuery,
  useGetStrategyDetailsQuery,
  useGetStrategyExecutionHistoryQuery,
  useGetBacktestResultsQuery,
  useGetStrategyMetricsQuery,
  useGetStrategyTemplatesQuery,

  // Mutations
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useUpdateStrategyStatusMutation,
  useBacktestStrategyMutation,
  useCloneStrategyMutation,
  useExportStrategyMutation,
  useImportStrategyMutation,
  useCreateFromTemplateMutation,
} = strategyApi

export default strategyApi