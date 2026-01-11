import { createApi } from '@reduxjs/toolkit/query/react'
import { baseApi } from './baseApi'
import {
  CreateStrategyRequest,
  UpdateStrategyRequest,
  StrategyPerformanceResponse,
  BacktestRequest,
  BacktestResponse,
  StrategyExecutionResponse,
  StartStrategyRequest,
  StopStrategyRequest,
  ManualOrderRequest,
  OrderResponse,
  PaginatedResponse,
  PaginationParams,
} from '../../types/api'
import { Strategy, StrategyType, StrategyStatus, RiskLevel } from '../../types'

// Strategies API slice
export const strategiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Strategy CRUD operations
    getStrategies: builder.query<PaginatedResponse<Strategy>, PaginationParams & {
      status?: StrategyStatus | 'all'
      type?: StrategyType | 'all'
      riskLevel?: RiskLevel | 'all'
      search?: string
    }>({
      query: (params) => ({
        url: '/strategies',
        params,
      }),
      providesTags: ['StrategyList'],
    }),

    getStrategy: builder.query<Strategy, string>({
      query: (id) => `/strategies/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    createStrategy: builder.mutation<Strategy, CreateStrategyRequest>({
      query: (strategy) => ({
        url: '/strategies',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: ['StrategyList'],
    }),

    updateStrategy: builder.mutation<Strategy, { id: string; updates: UpdateStrategyRequest }>({
      query: ({ id, updates }) => ({
        url: `/strategies/${id}`,
        method: 'PUT',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        'StrategyList',
        'StrategyPerformance',
      ],
    }),

    patchStrategy: builder.mutation<Strategy, { id: string; updates: Partial<UpdateStrategyRequest> }>({
      query: ({ id, updates }) => ({
        url: `/strategies/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        'StrategyList',
      ],
    }),

    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['StrategyList'],
    }),

    // Strategy performance
    getStrategyPerformance: builder.query<StrategyPerformanceResponse, {
      id: string
      period: string
    }>({
      query: ({ id, period }) => ({
        url: `/strategies/${id}/performance`,
        params: { period },
      }),
      providesTags: (result, error, { id }) => [{ type: 'StrategyPerformance', id }],
    }),

    getStrategyMetrics: builder.query({
      query: (id: string) => `/strategies/${id}/metrics`,
      providesTags: (result, error, id) => [{ type: 'StrategyPerformance', id }],
    }),

    // Strategy execution
    startStrategy: builder.mutation<StrategyExecutionResponse, StartStrategyRequest>({
      query: ({ strategyId, mode, allocation }) => ({
        url: `/strategies/${strategyId}/start`,
        method: 'POST',
        body: { mode, allocation },
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
        'StrategyExecution',
      ],
    }),

    stopStrategy: builder.mutation<StrategyExecutionResponse, StopStrategyRequest>({
      query: ({ strategyId, reason }) => ({
        url: `/strategies/${strategyId}/stop`,
        method: 'POST',
        body: { reason },
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
        'StrategyExecution',
      ],
    }),

    pauseStrategy: builder.mutation<StrategyExecutionResponse, { id: string }>({
      query: (id) => ({
        url: `/strategies/${id}/pause`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        'StrategyExecution',
      ],
    }),

    resumeStrategy: builder.mutation<StrategyExecutionResponse, { id: string }>({
      query: (id) => ({
        url: `/strategies/${id}/resume`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        'StrategyExecution',
      ],
    }),

    getExecutionStatus: builder.query<StrategyExecutionResponse, string>({
      query: (id) => `/strategies/${id}/execution/status`,
      providesTags: (result, error, id) => [{ type: 'StrategyExecution', id }],
    }),

    // Backtesting
    runBacktest: builder.mutation<BacktestResponse, BacktestRequest>({
      query: (request) => ({
        url: '/strategies/backtest',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Backtest'],
    }),

    getBacktestResult: builder.query<BacktestResponse, string>({
      query: (id) => `/strategies/backtest/${id}`,
      providesTags: (result, error, id) => [{ type: 'Backtest', id }],
    }),

    getBacktestList: builder.query<PaginatedResponse<BacktestResponse>, PaginationParams>({
      query: (params) => ({
        url: '/strategies/backtest',
        params,
      }),
      providesTags: ['Backtest'],
    }),

    deleteBacktest: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/backtest/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Backtest'],
    }),

    // Manual trading
    placeManualOrder: builder.mutation<OrderResponse, ManualOrderRequest>({
      query: (order) => ({
        url: '/strategies/manual/order',
        method: 'POST',
        body: order,
      }),
      invalidatesTags: ['StrategyExecution'],
    }),

    cancelOrder: builder.mutation<void, { orderId: string }>({
      query: ({ orderId }) => ({
        url: `/strategies/orders/${orderId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: ['StrategyExecution'],
    }),

    getOrders: builder.query<PaginatedResponse<OrderResponse>, PaginationParams & {
      strategyId?: string
      symbol?: string
      status?: string
    }>({
      query: (params) => ({
        url: '/strategies/orders',
        params,
      }),
      providesTags: ['StrategyExecution'],
    }),

    getOrder: builder.query<OrderResponse, string>({
      query: (id) => `/strategies/orders/${id}`,
      providesTags: ['StrategyExecution'],
    }),

    // Positions
    getPositions: builder.query<PaginatedResponse<any>, PaginationParams & {
      strategyId?: string
      symbol?: string
    }>({
      query: (params) => ({
        url: '/strategies/positions',
        params,
      }),
      providesTags: ['StrategyExecution'],
    }),

    closePosition: builder.mutation<void, { positionId: string }>({
      query: ({ positionId }) => ({
        url: `/strategies/positions/${positionId}/close`,
        method: 'POST',
      }),
      invalidatesTags: ['StrategyExecution'],
    }),

    // Strategy templates
    getStrategyTemplates: builder.query<PaginatedResponse<Strategy>, PaginationParams & {
      type?: StrategyType
    }>({
      query: (params) => ({
        url: '/strategies/templates',
        params,
      }),
      providesTags: ['StrategyList'],
    }),

    createFromTemplate: builder.mutation<Strategy, { templateId: string; name: string }>({
      query: ({ templateId, name }) => ({
        url: `/strategies/templates/${templateId}/create`,
        method: 'POST',
        body: { name },
      }),
      invalidatesTags: ['StrategyList'],
    }),

    // Strategy optimization
    optimizeStrategy: builder.mutation<any, {
      strategyId: string
      parameters: string[]
      objective: string
      constraints?: any
    }>({
      query: ({ strategyId, parameters, objective, constraints }) => ({
        url: `/strategies/${strategyId}/optimize`,
        method: 'POST',
        body: { parameters, objective, constraints },
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
      ],
    }),

    getOptimizationResults: builder.query<any, string>({
      query: (jobId) => `/strategies/optimization/${jobId}`,
      providesTags: ['Backtest'],
    }),

    // Risk management
    getRiskMetrics: builder.query<any, string>({
      query: (id) => `/strategies/${id}/risk`,
      providesTags: (result, error, id) => [{ type: 'StrategyPerformance', id }],
    }),

    updateRiskSettings: builder.mutation<any, {
      strategyId: string
      settings: any
    }>({
      query: ({ strategyId, settings }) => ({
        url: `/strategies/${strategyId}/risk`,
        method: 'PUT',
        body: settings,
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
      ],
    }),

    // Strategy logs
    getExecutionLogs: builder.query<PaginatedResponse<any>, {
      strategyId: string
      level?: string
      startTime?: string
      endTime?: string
      page?: number
      pageSize?: number
    }>({
      query: (params) => ({
        url: `/strategies/${params.strategyId}/logs`,
        params,
      }),
      providesTags: ['Log'],
    }),

    // Strategy comparison
    compareStrategies: builder.query<any, {
      strategies: string[]
      period: string
      metrics: string[]
    }>({
      query: ({ strategies, period, metrics }) => ({
        url: '/strategies/compare',
        method: 'POST',
        body: { strategies, period, metrics },
      }),
      providesTags: ['StrategyPerformance'],
    }),
    executeStrategy: builder.mutation<any, {
      strategyId: string;
      params?: any;
    }>({
      query: ({ strategyId, params }) => ({
        url: `/strategies/${strategyId}/execute`,
        method: 'POST',
        body: params || {},
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
        'StrategyExecution',
      ],
    }),
    batchOperation: builder.mutation<any, {
      strategyIds: string[];
      operation: 'start' | 'stop' | 'pause' | 'resume' | 'delete';
      params?: any;
    }>({
      query: ({ strategyIds, operation, params }) => ({
        url: '/strategies/batch',
        method: 'POST',
        body: { strategyIds, operation, params },
      }),
      invalidatesTags: ['StrategyList', 'StrategyExecution'],
    }),
  }),
})

// Export hooks
export const {
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  usePatchStrategyMutation,
  useDeleteStrategyMutation,
  useGetStrategyPerformanceQuery,
  useGetStrategyMetricsQuery,
  useStartStrategyMutation,
  useStopStrategyMutation,
  usePauseStrategyMutation,
  useResumeStrategyMutation,
  useGetExecutionStatusQuery,
  useRunBacktestMutation,
  useGetBacktestResultQuery,
  useGetBacktestListQuery,
  useDeleteBacktestMutation,
  usePlaceManualOrderMutation,
  useCancelOrderMutation,
  useGetOrdersQuery,
  useExecuteStrategyMutation,
  useBatchOperationMutation,
  useGetOrderQuery,
  useGetPositionsQuery,
  useClosePositionMutation,
  useGetStrategyTemplatesQuery,
  useCreateFromTemplateMutation,
  useOptimizeStrategyMutation,
  useGetOptimizationResultsQuery,
  useGetRiskMetricsQuery,
  useUpdateRiskSettingsMutation,
  useGetExecutionLogsQuery,
  useCompareStrategiesQuery,
} = strategiesApi

export default strategiesApi