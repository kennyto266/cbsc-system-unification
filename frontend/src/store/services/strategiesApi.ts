import { api } from '../api';
import { StrategyData } from '../../features/strategies/types';

// Tag types for cache invalidation
const STRATEGY_TAG = 'Strategy' as const;
const STRATEGIES_LIST_TAG = 'StrategiesList' as const;

// Define the strategies API slice
export const strategiesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    // Get all strategies
    getStrategies: builder.query<StrategyData[], void>({
      query: () => '/strategies',
      providesTags: [STRATEGIES_LIST_TAG],
    }),

    // Get strategy by ID
    getStrategyById: builder.query<StrategyData, string>({
      query: (id) => `/strategies/${id}`,
      providesTags: (result, error, id) => 
        result ? [{ type: STRATEGY_TAG, id }] : []
      ,
    }),

    // Create new strategy
    createStrategy: builder.mutation<StrategyData, Partial<StrategyData>>({
      query: (strategyData) => ({
        url: '/strategies',
        method: 'POST',
        body: strategyData,
      }),
      invalidatesTags: [STRATEGIES_LIST_TAG],
    }),

    // Update strategy
    updateStrategy: builder.mutation<StrategyData, { id: string } & Partial<StrategyData>>({
      query: ({ id, ...strategyData }) => ({
        url: `/strategies/${id}`,
        method: 'PUT',
        body: strategyData,
      }),
      invalidatesTags: (result, error, { id }) => 
        error ? [] : [{ type: STRATEGY_TAG, id }, STRATEGIES_LIST_TAG]
      ,
    }),

    // Delete strategy
    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [STRATEGIES_LIST_TAG],
    }),

    // Toggle strategy active status
    toggleStrategy: builder.mutation<StrategyData, { id: string; isActive: boolean }>({
      query: ({ id, isActive }) => ({
        url: `/strategies/${id}/toggle`,
        method: 'PATCH',
        body: { isActive },
      }),
      invalidatesTags: (result, error, { id }) => 
        error ? [] : [{ type: STRATEGY_TAG, id }]
      ,
    }),

    // Batch control strategies
    batchControlStrategies: builder.mutation<
      { success: boolean; results: Array<{ strategyId: string; success: boolean }> },
      { strategyIds: string[]; operation: string }
    >({
      query: ({ strategyIds, operation }) => ({
        url: '/strategies/batch',
        method: 'POST',
        body: { strategyIds, operation },
      }),
      invalidatesTags: [STRATEGIES_LIST_TAG],
    }),
  }),
});

// Export hooks
export const {
  useGetStrategiesQuery,
  useGetStrategyByIdQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useToggleStrategyMutation,
  useBatchControlStrategiesMutation,
} = strategiesApi;
