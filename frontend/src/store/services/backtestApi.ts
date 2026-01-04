// RTK Query API for Backtest operations
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Types for backtest operations
export interface BacktestConfig {
  strategy_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission: number;
  slippage: number;
  parameters?: Record<string, any>;
}

export interface BacktestStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface PerformanceMetrics {
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  avg_trade: number;
  total_trades: number;
  profitable_trades: number;
  losing_trades: number;
}

export interface TradeRecord {
  id: string;
  symbol: string;
  type: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  quantity: number;
  entry_time: string;
  exit_time: string;
  profit_loss: number;
  profit_loss_percent: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

export interface BacktestReport {
  id: string;
  config: BacktestConfig;
  status: BacktestStatus;
  performance: PerformanceMetrics;
  trades: TradeRecord[];
  equity_curve: EquityPoint[];
  metadata: {
    strategy_name: string;
    created_by: string;
    execution_time: number;
    data_points: number;
  };
}

export interface BacktestListItem {
  id: string;
  strategy_name: string;
  symbol: string;
  status: string;
  start_date: string;
  end_date: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  created_at: string;
}

export interface BacktestComparisonRequest {
  backtest_ids: string[];
}

export interface BacktestComparisonResponse {
  backtests: BacktestListItem[];
  comparison: {
    best_return: string;
    best_sharpe: string;
    lowest_drawdown: string;
    most_trades: string;
  };
}

export interface BacktestTemplate {
  id: string;
  name: string;
  description: string;
  config: Partial<BacktestConfig>;
  created_by: string;
  created_at: string;
}

// Create base query with auth header
const baseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as any).auth.token;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    headers.set('Content-Type', 'application/json');
    return headers;
  },
});

// Tag types for cache invalidation
const BACKTEST_TAG = 'Backtest';
const BACKTEST_LIST_TAG = 'BacktestList';
const BACKTEST_TEMPLATE_TAG = 'BacktestTemplate';

// Create backtest API
export const backtestApi = createApi({
  reducerPath: 'backtestApi',
  baseQuery,
  tagTypes: [BACKTEST_TAG, BACKTEST_LIST_TAG, BACKTEST_TEMPLATE_TAG],
  endpoints: (builder) => ({
    // Get all backtests
    getBacktests: builder.query<BacktestListItem[], { page?: number; limit?: number; status?: string }>({
      query: ({ page = 1, limit = 20, status } = {}) => {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
        });
        if (status) {
          params.append('status', status);
        }
        return `/backtests?${params.toString()}`;
      },
      providesTags: [BACKTEST_LIST_TAG],
    }),

    // Get backtest by ID
    getBacktestById: builder.query<BacktestReport, string>({
      query: (id) => `/backtests/${id}`,
      providesTags: (result, error, id) => [{ type: BACKTEST_TAG, id }],
    }),

    // Create new backtest
    createBacktest: builder.mutation<BacktestStatus, BacktestConfig>({
      query: (config) => ({
        url: '/backtests',
        method: 'POST',
        body: config,
      }),
      invalidatesTags: [BACKTEST_LIST_TAG],
    }),

    // Start backtest execution
    startBacktest: builder.mutation<BacktestStatus, string>({
      query: (id) => ({
        url: `/backtests/${id}/start`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        BACKTEST_LIST_TAG,
        { type: BACKTEST_TAG, id },
      ],
    }),

    // Stop running backtest
    stopBacktest: builder.mutation<BacktestStatus, string>({
      query: (id) => ({
        url: `/backtests/${id}/stop`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: BACKTEST_TAG, id },
      ],
    }),

    // Delete backtest
    deleteBacktest: builder.mutation<void, string>({
      query: (id) => ({
        url: `/backtests/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        BACKTEST_LIST_TAG,
        { type: BACKTEST_TAG, id },
      ],
    }),

    // Get backtest status (for polling)
    getBacktestStatus: builder.query<BacktestStatus, string>({
      query: (id) => `/backtests/${id}/status`,
      providesTags: (result, error, id) => [{ type: BACKTEST_TAG, id }],
    }),

    // Get backtest trades
    getBacktestTrades: builder.query<TradeRecord[], { id: string; limit?: number; offset?: number }>({
      query: ({ id, limit = 100, offset = 0 }) => {
        const params = new URLSearchParams({
          limit: limit.toString(),
          offset: offset.toString(),
        });
        return `/backtests/${id}/trades?${params.toString()}`;
      },
      providesTags: (result, error, { id }) => [{ type: BACKTEST_TAG, id }, 'Trades'],
    }),

    // Get backtest equity curve
    getBacktestEquityCurve: builder.query<EquityPoint[], string>({
      query: (id) => `/backtests/${id}/equity`,
      providesTags: (result, error, id) => [{ type: BACKTEST_TAG, id }, 'Equity'],
    }),

    // Compare multiple backtests
    compareBacktests: builder.mutation<BacktestComparisonResponse, BacktestComparisonRequest>({
      query: ({ backtest_ids }) => ({
        url: '/backtests/compare',
        method: 'POST',
        body: { backtest_ids },
      }),
    }),

    // Get backtest templates
    getBacktestTemplates: builder.query<BacktestTemplate[], void>({
      query: () => '/backtests/templates',
      providesTags: [BACKTEST_TEMPLATE_TAG],
    }),

    // Create backtest template
    createBacktestTemplate: builder.mutation<BacktestTemplate, Omit<BacktestTemplate, 'id' | 'created_at'>>({
      query: (template) => ({
        url: '/backtests/templates',
        method: 'POST',
        body: template,
      }),
      invalidatesTags: [BACKTEST_TEMPLATE_TAG],
    }),

    // Update backtest template
    updateBacktestTemplate: builder.mutation<BacktestTemplate, { id: string; data: Partial<BacktestTemplate> }>({
      query: ({ id, data }) => ({
        url: `/backtests/templates/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        BACKTEST_TEMPLATE_TAG,
        { type: BACKTEST_TEMPLATE_TAG, id },
      ],
    }),

    // Delete backtest template
    deleteBacktestTemplate: builder.mutation<void, string>({
      query: (id) => ({
        url: `/backtests/templates/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [BACKTEST_TEMPLATE_TAG],
    }),

    // Export backtest report
    exportBacktestReport: builder.mutation<Blob, { id: string; format: 'pdf' | 'csv' | 'json' }>({
      query: ({ id, format }) => ({
        url: `/backtests/${id}/export`,
        method: 'POST',
        body: { format },
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Clone backtest configuration
    cloneBacktest: builder.mutation<BacktestConfig, string>({
      query: (id) => ({
        url: `/backtests/${id}/clone`,
        method: 'POST',
      }),
    }),
  }),
});

// Export hooks for components
export const {
  useGetBacktestsQuery,
  useGetBacktestByIdQuery,
  useCreateBacktestMutation,
  useStartBacktestMutation,
  useStopBacktestMutation,
  useDeleteBacktestMutation,
  useGetBacktestStatusQuery,
  useGetBacktestTradesQuery,
  useGetBacktestEquityCurveQuery,
  useCompareBacktestsMutation,
  useGetBacktestTemplatesQuery,
  useCreateBacktestTemplateMutation,
  useUpdateBacktestTemplateMutation,
  useDeleteBacktestTemplateMutation,
  useExportBacktestReportMutation,
  useCloneBacktestMutation,
} = backtestApi;

// Export reducer and middleware for store configuration
export const backtestReducer = backtestApi.reducer;
export const backtestMiddleware = backtestApi.middleware;
