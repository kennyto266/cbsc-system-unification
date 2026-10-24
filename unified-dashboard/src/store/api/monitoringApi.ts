import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type {
  SystemStatus,
  MarketData,
  WebSocketMessage,
  Strategy,
  StrategyExecutionResult
} from '@types/index'
import type { RootState } from '../index'

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: '/api/monitoring',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('content-type', 'application/json')
    return headers
  },
})

export const monitoringApi = createApi({
  reducerPath: 'monitoringApi',
  baseQuery,
  tagTypes: ['SystemStatus', 'MarketData', 'Monitoring'],
  endpoints: (builder) => ({
    // System status and health
    getSystemStatus: builder.query<SystemStatus, void>({
      query: () => '/status',
      providesTags: ['SystemStatus'],
    }),

    getHealthCheck: builder.query<{
      status: 'healthy' | 'unhealthy';
      timestamp: string;
      version: string;
      checks: Record<string, { status: string }>;
    }, void>({
      query: () => '/health',
      providesTags: ['SystemStatus'],
    }),

    // Market data
    getMarketData: builder.query<Record<string, MarketData>, {
      symbols?: string[];
      includeHistory?: boolean;
      historyDays?: number;
    }>({
      query: ({ symbols, includeHistory = false, historyDays = 7 }) => ({
        url: '/market-data',
        params: {
          symbols: symbols?.join(','),
          include_history: includeHistory,
          history_days: historyDays,
        },
      }),
      providesTags: ['MarketData'],
    }),

    getMarketDataBySymbol: builder.query<MarketData, {
      symbol: string;
      includeHistory?: boolean;
      historyDays?: number;
    }>({
      query: ({ symbol, includeHistory = false, historyDays = 7 }) => ({
        url: `/market-data/${symbol}`,
        params: {
          include_history: includeHistory,
          history_days: historyDays,
        },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'MarketData', id: symbol }],
    }),

    // Active strategies monitoring
    getActiveStrategies: builder.query<Strategy[], void>({
      query: () => '/active-strategies',
      providesTags: ['Monitoring'],
    }),

    getStrategyExecutionLogs: builder.query<Array<{
      executionId: string;
      strategyId: string;
      timestamp: string;
      level: 'info' | 'warning' | 'error' | 'debug';
      message: string;
      details?: any;
    }>, {
      strategyId?: string;
      executionId?: string;
      level?: string;
      limit?: number;
      startTime?: string;
      endTime?: string;
    }>({
      query: ({
        strategyId,
        executionId,
        level,
        limit = 100,
        startTime,
        endTime,
      }) => ({
        url: '/execution-logs',
        params: {
          strategy_id: strategyId,
          execution_id: executionId,
          level,
          limit,
          start_time: startTime,
          end_time: endTime,
        },
      }),
    }),

    // Performance metrics
    getPerformanceMetrics: builder.query<{
      totalStrategies: number;
      activeStrategies: number;
      totalExecutions: number;
      runningExecutions: number;
      completedExecutions: number;
      failedExecutions: number;
      averageExecutionTime: number;
      successRate: number;
      last24hStats: {
        executions: number;
        signals: number;
        errors: number;
      };
    }, {
      timeRange?: '1h' | '24h' | '7d' | '30d';
    }>({
      query: ({ timeRange = '24h' }) => ({
        url: '/performance-metrics',
        params: { time_range: timeRange },
      }),
      providesTags: ['Monitoring'],
    }),

    // Alerts and notifications
    getActiveAlerts: builder.query<Array<{
      id: string;
      type: 'error' | 'warning' | 'info';
      title: string;
      message: string;
      strategyId?: string;
      executionId?: string;
      timestamp: string;
      acknowledged: boolean;
      severity: 'low' | 'medium' | 'high' | 'critical';
    }>, {
      severity?: string;
      acknowledged?: boolean;
      limit?: number;
    }>({
      query: ({ severity, acknowledged, limit = 50 }) => ({
        url: '/alerts',
        params: {
          severity,
          acknowledged,
          limit,
        },
      }),
    }),

    acknowledgeAlert: builder.mutation<void, {
      alertId: string;
    }>({
      query: ({ alertId }) => ({
        url: `/alerts/${alertId}/acknowledge`,
        method: 'POST',
      }),
      invalidatesTags: ['Monitoring'],
    }),

    dismissAlert: builder.mutation<void, {
      alertId: string;
    }>({
      query: ({ alertId }) => ({
        url: `/alerts/${alertId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Monitoring'],
    }),

    // Resource monitoring
    getResourceUsage: builder.query<{
      cpu: {
        usage: number;
        cores: number;
        loadAverage: number[];
      };
      memory: {
        used: number;
        total: number;
        usage: number;
        available: number;
      };
      disk: {
        used: number;
        total: number;
        usage: number;
        available: number;
      };
      network: {
        bytesIn: number;
        bytesOut: number;
        packetsIn: number;
        packetsOut: number;
      };
    }, {
      timeRange?: '1h' | '24h' | '7d';
    }>({
      query: ({ timeRange = '1h' }) => ({
        url: '/resource-usage',
        params: { time_range: timeRange },
      }),
      providesTags: ['SystemStatus'],
    }),

    // WebSocket connection info
    getWebSocketInfo: builder.query<{
      connected: boolean;
      subscriptions: string[];
      lastMessage?: string;
      connectionTime?: string;
      reconnectCount: number;
    }, void>({
      query: () => '/websocket-info',
      providesTags: ['Monitoring'],
    }),

    subscribeToUpdates: builder.mutation<void, {
      subscriptions: string[];
    }>({
      query: ({ subscriptions }) => ({
        url: '/subscribe',
        method: 'POST',
        body: { subscriptions },
      }),
    }),

    unsubscribeFromUpdates: builder.mutation<void, {
      subscriptions: string[];
    }>({
      query: ({ subscriptions }) => ({
        url: '/unsubscribe',
        method: 'POST',
        body: { subscriptions },
      }),
    }),
  }),
})

export const {
  // System status and health
  useGetSystemStatusQuery,
  useGetHealthCheckQuery,

  // Market data
  useGetMarketDataQuery,
  useGetMarketDataBySymbolQuery,

  // Active strategies monitoring
  useGetActiveStrategiesQuery,
  useGetStrategyExecutionLogsQuery,

  // Performance metrics
  useGetPerformanceMetricsQuery,

  // Alerts and notifications
  useGetActiveAlertsQuery,
  useAcknowledgeAlertMutation,
  useDismissAlertMutation,

  // Resource monitoring
  useGetResourceUsageQuery,

  // WebSocket connection info
  useGetWebSocketInfoQuery,
  useSubscribeToUpdatesMutation,
  useUnsubscribeFromUpdatesMutation,
} = monitoringApi

export default monitoringApi