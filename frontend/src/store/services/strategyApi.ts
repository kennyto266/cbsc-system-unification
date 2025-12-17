/**
 * Strategy Management API Service
 * Redux Toolkit Query API slice for strategy operations
 */

import { createApi } from '@reduxjs/toolkit/query/react';
import {
  baseQueryWithReauth,
  providesList,
  invalidatesList,
} from '../../api/baseQuery';
import type { Strategy } from '../../types/strategy';
import type { PaginatedResponse, SearchParams } from '../../types/api';

// Strategy API slice
export const strategyApi = createApi({
  reducerPath: 'strategyApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Strategy', 'Execution', 'Backtest', 'Signal', 'Performance'],
  keepUnusedDataFor: 60, // Keep data for 1 minute
  endpoints: (builder) => ({
    // Get strategies with pagination and filtering
    getStrategies: builder.query<PaginatedResponse<Strategy>, Partial<SearchParams> & {
      category?: string;
      status?: string;
      riskLevel?: string;
    }>({
      query: (params) => ({
        url: '/strategies',
        params,
      }),
      providesTags: (result) => providesList(result?.items || [], 'Strategy'),
      transformResponse: (response: any, meta, arg) => {
        // Transform backend response to frontend format
        return {
          items: response.strategies || response.data || [],
          total: response.total || response.count || 0,
          page: arg.page || 1,
          pageSize: arg.pageSize || 20,
          totalPages: Math.ceil((response.total || 0) / (arg.pageSize || 20)),
        };
      },
    }),

    // Get strategy details
    getStrategy: builder.query<Strategy, string>({
      query: (id) => `/strategies/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    // Create new strategy
    createStrategy: builder.mutation<Strategy, Partial<Strategy>>({
      query: (strategy) => ({
        url: '/strategies',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: [{ type: 'Strategy', id: 'LIST' }],
    }),

    // Update strategy
    updateStrategy: builder.mutation<Strategy, {
      id: string;
      data: Partial<Strategy>;
    }>({
      query: ({ id, data }) => ({
        url: `/strategies/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        { type: 'Strategy', id: 'LIST' },
      ],
    }),

    // Delete strategy
    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Strategy', id: 'LIST' }],
      onQueryStarted: async (id, { dispatch, queryFulfilled }) => {
        try {
          await queryFulfilled;
          // Clean up related state
          dispatch({
            type: 'strategy/removeStrategy',
            payload: id,
          });
        } catch (error) {
          console.error('Failed to delete strategy:', error);
        }
      },
    }),

    // Clone strategy
    cloneStrategy: builder.mutation<Strategy, {
      id: string;
      name: string;
      description?: string;
    }>({
      query: ({ id, name, description }) => ({
        url: `/strategies/${id}/clone`,
        method: 'POST',
        body: { name, description },
      }),
      invalidatesTags: [{ type: 'Strategy', id: 'LIST' }],
    }),

    // Get strategy parameters
    getStrategyParameters: builder.query<any, string>({
      query: (id) => `/strategies/${id}/parameters`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id: `${id}-parameters` }],
    }),

    // Update strategy parameters
    updateStrategyParameters: builder.mutation<any, {
      id: string;
      parameters: Record<string, any>;
    }>({
      query: ({ id, parameters }) => ({
        url: `/strategies/${id}/parameters`,
        method: 'PUT',
        body: { parameters },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id: `${id}-parameters` },
        { type: 'Strategy', id },
      ],
    }),

    // Execute strategy
    executeStrategy: builder.mutation<any, {
      id: string;
      config?: {
        startDate?: string;
        endDate?: string;
        initialCapital?: number;
        commission?: number;
        slippage?: number;
      };
    }>({
      query: ({ id, config }) => ({
        url: `/strategies/${id}/execute`,
        method: 'POST',
        body: config,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Execution', id },
        { type: 'Strategy', id },
      ],
    }),

    // Stop strategy execution
    stopExecution: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/${id}/stop`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Execution', id },
        { type: 'Strategy', id },
      ],
    }),

    // Get execution status
    getExecutionStatus: builder.query<any, string>({
      query: (id) => `/strategies/${id}/execution/status`,
      providesTags: (result, error, id) => [{ type: 'Execution', id }],
    }),

    // Get execution history
    getExecutionHistory: builder.query<any[], {
      id: string;
      limit?: number;
      offset?: number;
    }>({
      query: ({ id, limit = 50, offset = 0 }) => ({
        url: `/strategies/${id}/execution/history`,
        params: { limit, offset },
      }),
      providesTags: (result, error, { id }) => [{ type: 'Execution', id }],
    }),

    // Run backtest
    runBacktest: builder.mutation<any, {
      id: string;
      config: {
        startDate: string;
        endDate: string;
        initialCapital: number;
        commission?: number;
        slippage?: number;
        benchmark?: string;
      };
    }>({
      query: ({ id, config }) => ({
        url: `/strategies/${id}/backtest`,
        method: 'POST',
        body: config,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Backtest', id },
      ],
    }),

    // Get backtest results
    getBacktestResults: builder.query<any, string>({
      query: (id) => `/strategies/${id}/backtest/results`,
      providesTags: (result, error, id) => [{ type: 'Backtest', id }],
    }),

    // Get backtest history
    getBacktestHistory: builder.query<any[], {
      id: string;
      limit?: number;
    }>({
      query: ({ id, limit = 20 }) => ({
        url: `/strategies/${id}/backtest/history`,
        params: { limit },
      }),
      providesTags: (result, error, { id }) => [{ type: 'Backtest', id }],
    }),

    // Get strategy signals
    getSignals: builder.query<any[], {
      id: string;
      limit?: number;
      offset?: number;
      status?: string;
    }>({
      query: ({ id, limit = 100, offset = 0, status }) => ({
        url: `/strategies/${id}/signals`,
        params: { limit, offset, status },
      }),
      providesTags: (result, error, { id }) => [{ type: 'Signal', id }],
    }),

    // Generate strategy report
    generateReport: builder.mutation<any, {
      id: string;
      type: 'summary' | 'detailed' | 'performance';
      format?: 'pdf' | 'excel';
    }>({
      query: ({ id, type, format }) => ({
        url: `/strategies/${id}/report`,
        method: 'POST',
        body: { type, format },
      }),
    }),

    // Get strategy recommendations
    getRecommendations: builder.query<any[], {
      id?: string;
      category?: string;
      riskLevel?: string;
    }>({
      query: ({ id, category, riskLevel }) => ({
        url: '/strategies/recommendations',
        params: { id, category, riskLevel },
      }),
      providesTags: ['Strategy'],
    }),

    // Validate strategy
    validateStrategy: builder.mutation<any, Partial<Strategy>>({
      query: (strategy) => ({
        url: '/strategies/validate',
        method: 'POST',
        body: strategy,
      }),
    }),

    // Import strategy
    importStrategy: builder.mutation<Strategy, {
      file: File;
      format: 'json' | 'csv' | 'python';
      overwrite?: boolean;
    }>({
      query: ({ file, format, overwrite }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', format);
        if (overwrite !== undefined) {
          formData.append('overwrite', overwrite.toString());
        }

        return {
          url: '/strategies/import',
          method: 'POST',
          body: formData,
          headers: {}, // Let browser set Content-Type for FormData
        };
      },
      invalidatesTags: [{ type: 'Strategy', id: 'LIST' }],
    }),

    // Export strategy
    exportStrategy: builder.mutation<string, {
      id: string;
      format: 'json' | 'csv' | 'python';
      includeResults?: boolean;
    }>({
      query: ({ id, format, includeResults = false }) => ({
        url: `/strategies/${id}/export`,
        method: 'POST',
        body: { format, includeResults },
      }),
    }),

    // Get strategy statistics
    getStatistics: builder.query<any, {
      id?: string;
      period?: 'day' | 'week' | 'month' | 'year';
    }>({
      query: ({ id, period }) => ({
        url: '/strategies/statistics',
        params: { id, period },
      }),
      providesTags: ['Strategy', 'Performance'],
    }),

    // Compare strategies
    compareStrategies: builder.mutation<any, {
      ids: string[];
      metrics?: string[];
    }>({
      query: ({ ids, metrics }) => ({
        url: '/strategies/compare',
        method: 'POST',
        body: { strategyIds: ids, metrics },
      }),
    }),

    // Optimize strategy parameters
    optimizeParameters: builder.mutation<any, {
      id: string;
      parameters: string[];
      objective: string;
      constraints?: Record<string, any>;
    }>({
      query: ({ id, parameters, objective, constraints }) => ({
        url: `/strategies/${id}/optimize`,
        method: 'POST',
        body: { parameters, objective, constraints },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
      ],
    }),
  }),
});

// Export hooks
export const {
  // Strategy CRUD
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useCloneStrategyMutation,

  // Parameters
  useGetStrategyParametersQuery,
  useUpdateStrategyParametersMutation,

  // Execution
  useExecuteStrategyMutation,
  useStopExecutionMutation,
  useGetExecutionStatusQuery,
  useGetExecutionHistoryQuery,

  // Backtesting
  useRunBacktestMutation,
  useGetBacktestResultsQuery,
  useGetBacktestHistoryQuery,

  // Signals
  useGetSignalsQuery,

  // Reports and analytics
  useGenerateReportMutation,
  useGetRecommendationsQuery,
  useGetStatisticsQuery,

  // Utilities
  useValidateStrategyMutation,
  useImportStrategyMutation,
  useExportStrategyMutation,
  useCompareStrategiesMutation,
  useOptimizeParametersMutation,
} = strategyApi;

// Utility hooks
export const useStrategiesWithFilters = (filters: any) => {
  return useGetStrategiesQuery(filters, {
    selectFromResult: ({ data, isLoading, error }) => ({
      strategies: data?.items || [],
      total: data?.total || 0,
      isLoading,
      error,
      hasMore: (data?.page || 1) * (data?.pageSize || 20) < (data?.total || 0),
    }),
  });
};

export const useStrategyExecution = (id: string) => {
  const { data: status, isLoading: statusLoading } = useGetExecutionStatusQuery(id);
  const { data: history, isLoading: historyLoading } = useGetExecutionHistoryQuery({ id });

  return {
    status,
    history: history || [],
    isLoading: statusLoading || historyLoading,
    isRunning: status?.isRunning || false,
  };
};

export const useStrategyBacktest = (id: string) => {
  const { data: results, isLoading: resultsLoading } = useGetBacktestResultsQuery(id);
  const { data: history, isLoading: historyLoading } = useGetBacktestHistoryQuery({ id });

  return {
    results,
    history: history || [],
    isLoading: resultsLoading || historyLoading,
    hasResults: !!results,
  };
};