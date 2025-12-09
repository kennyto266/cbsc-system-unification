import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type {
  Strategy,
  StrategyListResponse,
  StrategyDetailResponse,
  CreateStrategyRequest,
  UpdateStrategyRequest,
  StrategyExecutionRequest,
  StrategyExecutionResult,
  StrategyOptimizationRequest,
  StrategyOptimizationResult,
  CBSCStrategyTemplate,
  BatchStrategyOperation,
  StrategySignal,
  PaginatedResponse
} from '@types/index'
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

export const strategiesApi = createApi({
  reducerPath: 'strategiesApi',
  baseQuery,
  tagTypes: ['Strategy', 'StrategyExecution', 'StrategySignal', 'StrategyTemplate'],
  endpoints: (builder) => ({
    // Strategy CRUD operations
    getStrategies: builder.query<StrategyListResponse, {
      page?: number;
      pageSize?: number;
      strategyType?: string;
      status?: string;
      isActive?: boolean;
    }>({
      query: ({
        page = 1,
        pageSize = 20,
        strategyType,
        status,
        isActive,
      }) => ({
        url: '/',
        params: {
          page,
          page_size: pageSize,
          strategy_type: strategyType,
          status,
          is_active: isActive,
        },
      }),
      providesTags: ['Strategy'],
    }),

    getStrategy: builder.query<StrategyDetailResponse, string>({
      query: (strategyId) => `/${strategyId}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    createStrategy: builder.mutation<Strategy, CreateStrategyRequest>({
      query: (strategy) => ({
        url: '/',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: ['Strategy'],
    }),

    updateStrategy: builder.mutation<Strategy, {
      strategyId: string;
      updates: UpdateStrategyRequest;
    }>({
      query: ({ strategyId, updates }) => ({
        url: `/${strategyId}`,
        method: 'PUT',
        body: updates,
      }),
      invalidatesTags: (result, error, { strategyId }) => [
        { type: 'Strategy', id: strategyId },
        'Strategy',
      ],
    }),

    deleteStrategy: builder.mutation<void, string>({
      query: (strategyId) => ({
        url: `/${strategyId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Strategy execution
    executeStrategy: builder.mutation<StrategyExecutionResult, {
      strategyId: string;
      request?: StrategyExecutionRequest;
    }>({
      query: ({ strategyId, request }) => ({
        url: `/${strategyId}/execute`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['StrategyExecution'],
    }),

    getExecutionResult: builder.query<StrategyExecutionResult, {
      strategyId: string;
      executionId: string;
    }>({
      query: ({ strategyId, executionId }) => `/${strategyId}/executions/${executionId}`,
      providesTags: (result, error, { executionId }) => [
        { type: 'StrategyExecution', id: executionId },
      ],
    }),

    stopStrategyExecution: builder.mutation<any, {
      strategyId: string;
      executionId?: string;
    }>({
      query: ({ strategyId, executionId }) => ({
        url: `/${strategyId}/stop`,
        method: 'POST',
        params: executionId ? { execution_id: executionId } : {},
      }),
      invalidatesTags: ['StrategyExecution'],
    }),

    // Strategy signals
    getStrategySignals: builder.query<{ signals: StrategySignal[] }, {
      strategyId: string;
      limit?: number;
      startTime?: string;
      endTime?: string;
      signalType?: string;
    }>({
      query: ({
        strategyId,
        limit = 100,
        startTime,
        endTime,
        signalType,
      }) => ({
        url: `/${strategyId}/signals`,
        params: {
          limit,
          start_time: startTime,
          end_time: endTime,
          signal_type: signalType,
        },
      }),
      providesTags: ['StrategySignal'],
    }),

    // Batch operations
    batchOperation: builder.mutation<any, BatchStrategyOperation>({
      query: (operation) => ({
        url: '/batch',
        method: 'POST',
        body: operation,
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Strategy templates
    getStrategyTemplates: builder.query<CBSCStrategyTemplate[], {
      category?: string;
    }>({
      query: ({ category }) => ({
        url: '/templates',
        params: { category },
      }),
      providesTags: ['StrategyTemplate'],
    }),

    getStrategyTemplate: builder.query<CBSCStrategyTemplate, string>({
      query: (templateId) => `/templates/${templateId}`,
      providesTags: (result, error, id) => [{ type: 'StrategyTemplate', id }],
    }),

    // Parameter optimization
    optimizeStrategyParameters: builder.mutation<StrategyOptimizationResult, {
      strategyId: string;
      request: StrategyOptimizationRequest;
    }>({
      query: ({ strategyId, request }) => ({
        url: `/${strategyId}/optimize`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Strategy'],
    }),
  }),
})

export const {
  // Strategy CRUD
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,

  // Strategy execution
  useExecuteStrategyMutation,
  useGetExecutionResultQuery,
  useStopStrategyExecutionMutation,

  // Strategy signals
  useGetStrategySignalsQuery,

  // Batch operations
  useBatchOperationMutation,

  // Strategy templates
  useGetStrategyTemplatesQuery,
  useGetStrategyTemplateQuery,

  // Parameter optimization
  useOptimizeStrategyParametersMutation,
} = strategiesApi

export default strategiesApi