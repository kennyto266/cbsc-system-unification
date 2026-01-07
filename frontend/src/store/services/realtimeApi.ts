// RTK Query API for Real-time Market Data
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Helper to get env vars safely in both Jest and Vite
const getEnvVar = (key: string, defaultValue: string): string => {
  if (typeof process !== 'undefined' && process.env?.[key]) {
    return process.env[key];
  }
  try {
    const metaEnv = (0, eval)('typeof import.meta !== "undefined" ? import.meta.env : undefined');
    if (metaEnv?.[key]) return metaEnv[key];
  } catch {
    // Fall through
  }
  return defaultValue;
};

// Base URL configuration
const API_BASE_URL = getEnvVar('VITE_API_BASE_URL', '/api');
const WS_BASE_URL = getEnvVar('VITE_WS_BASE_URL', 'ws://localhost:8000');

// Types for real-time data
export interface MarketData {
  symbol: string;
  timestamp: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
  bid: number;
  ask: number;
}

export interface QuoteData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number;
  pe_ratio?: number;
  dividend_yield?: number;
}

export interface OHLCVData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingSignal {
  id: string;
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  type: 'buy' | 'sell' | 'hold';
  confidence: number;
  price: number;
  timestamp: string;
  status: 'pending' | 'executed' | 'cancelled' | 'expired';
  metadata: Record<string, any>;
}

export interface WebSocketSubscription {
  id: string;
  type: 'market_data' | 'signals' | 'strategy_updates' | 'system';
  symbols?: string[];
  active: boolean;
  connected: boolean;
}

export interface WebSocketStatus {
  connected: boolean;
  url: string;
  subscriptions: string[];
  last_message: string;
  connect_time?: string;
}

export interface RealTimeAlert {
  id: string;
  type: 'price' | 'volume' | 'signal' | 'system';
  severity: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: Record<string, any>;
}

export interface PriceAlert {
  id: string;
  symbol: string;
  condition: 'above' | 'below' | 'crosses';
  target_price: number;
  current_price: number;
  triggered: boolean;
  created_at: string;
  triggered_at?: string;
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  added_at: string;
  notes?: string;
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
const MARKET_DATA_TAG = 'MarketData';
const QUOTE_TAG = 'Quote';
const SIGNAL_TAG = 'Signal';
const ALERT_TAG = 'Alert';
const WATCHLIST_TAG = 'Watchlist';

// Create real-time API
export const realtimeApi = createApi({
  reducerPath: 'realtimeApi',
  baseQuery,
  tagTypes: [MARKET_DATA_TAG, QUOTE_TAG, SIGNAL_TAG, ALERT_TAG, WATCHLIST_TAG],
  endpoints: (builder) => ({
    // Get real-time market data for multiple symbols
    getMarketData: builder.query<MarketData[], string[]>({
      query: (symbols) => {
        const params = new URLSearchParams();
        symbols.forEach(s => params.append('symbols', s));
        return `/realtime/market?${params.toString()}`;
      },
      providesTags: (result, error, symbols) => [
        MARKET_DATA_TAG,
        ...symbols.map(s => ({ type: QUOTE_TAG, id: s } as const)),
      ],
      pollingInterval: 5000, // Poll every 5 seconds
    }),

    // Get quote data for a symbol
    getQuote: builder.query<QuoteData, string>({
      query: (symbol) => `/realtime/quote/${symbol}`,
      providesTags: (result, error, symbol) => [{ type: QUOTE_TAG, id: symbol }],
    }),

    // Get historical OHLCV data
    getOHLCV: builder.query<OHLCVData[], {
      symbol: string;
      interval: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
      start: string;
      end: string;
      limit?: number;
    }>({
      query: ({ symbol, interval, start, end, limit = 500 }) => {
        const params = new URLSearchParams({
          interval,
          start,
          end,
          limit: limit.toString(),
        });
        return `/realtime/ohlcv/${symbol}?${params.toString()}`;
      },
    }),

    // Get trading signals
    getTradingSignals: builder.query<TradingSignal[], {
      status?: string;
      limit?: number;
    }>({
      query: ({ status, limit = 50 } = {}) => {
        const params = new URLSearchParams({ limit: limit.toString() });
        if (status) {
          params.append('status', status);
        }
        return `/realtime/signals?${params.toString()}`;
      },
      providesTags: [SIGNAL_TAG],
    }),

    // Execute trading signal
    executeSignal: builder.mutation<{ executed: boolean; order_id?: string }, string>({
      query: (signalId) => ({
        url: `/realtime/signals/${signalId}/execute`,
        method: 'POST',
      }),
      invalidatesTags: [SIGNAL_TAG],
    }),

    // Cancel trading signal
    cancelSignal: builder.mutation<void, string>({
      query: (signalId) => ({
        url: `/realtime/signals/${signalId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: [SIGNAL_TAG],
    }),

    // Get WebSocket status
    getWebSocketStatus: builder.query<WebSocketStatus, void>({
      query: () => '/realtime/ws/status',
    }),

    // Get active WebSocket subscriptions
    getSubscriptions: builder.query<WebSocketSubscription[], void>({
      query: () => '/realtime/ws/subscriptions',
    }),

    // Subscribe to market data updates
    subscribeMarketData: builder.mutation<WebSocketSubscription, string[]>({
      query: (symbols) => ({
        url: '/realtime/ws/subscribe/market',
        method: 'POST',
        body: { symbols },
      }),
    }),

    // Subscribe to trading signals
    subscribeSignals: builder.mutation<WebSocketSubscription, void>({
      query: () => ({
        url: '/realtime/ws/subscribe/signals',
        method: 'POST',
      }),
    }),

    // Unsubscribe from updates
    unsubscribe: builder.mutation<void, string>({
      query: (subscriptionId) => ({
        url: `/realtime/ws/unsubscribe/${subscriptionId}`,
        method: 'POST',
      }),
    }),

    // Get real-time alerts
    getAlerts: builder.query<RealTimeAlert[], { unread_only?: boolean; limit?: number }>({
      query: ({ unread_only = false, limit = 50 } = {}) => {
        const params = new URLSearchParams({ limit: limit.toString() });
        if (unread_only) {
          params.append('unread_only', 'true');
        }
        return `/realtime/alerts?${params.toString()}`;
      },
      providesTags: [ALERT_TAG],
    }),

    // Mark alert as read
    markAlertRead: builder.mutation<void, string>({
      query: (alertId) => ({
        url: `/realtime/alerts/${alertId}/read`,
        method: 'POST',
      }),
      invalidatesTags: [ALERT_TAG],
    }),

    // Mark all alerts as read
    markAllAlertsRead: builder.mutation<void, void>({
      query: () => ({
        url: '/realtime/alerts/read-all',
        method: 'POST',
      }),
      invalidatesTags: [ALERT_TAG],
    }),

    // Delete alert
    deleteAlert: builder.mutation<void, string>({
      query: (alertId) => ({
        url: `/realtime/alerts/${alertId}`,
        method: 'DELETE',
      }),
      invalidatesTags: [ALERT_TAG],
    }),

    // Get price alerts
    getPriceAlerts: builder.query<PriceAlert[], void>({
      query: () => '/realtime/alerts/price',
      providesTags: [ALERT_TAG],
    }),

    // Create price alert
    createPriceAlert: builder.mutation<PriceAlert, Omit<PriceAlert, 'id' | 'current_price' | 'triggered' | 'created_at' | 'triggered_at'>>({
      query: (alert) => ({
        url: '/realtime/alerts/price',
        method: 'POST',
        body: alert,
      }),
      invalidatesTags: [ALERT_TAG],
    }),

    // Delete price alert
    deletePriceAlert: builder.mutation<void, string>({
      query: (alertId) => ({
        url: `/realtime/alerts/price/${alertId}`,
        method: 'DELETE',
      }),
      invalidatesTags: [ALERT_TAG],
    }),

    // Get watchlist
    getWatchlist: builder.query<WatchlistItem[], void>({
      query: () => '/realtime/watchlist',
      providesTags: [WATCHLIST_TAG],
    }),

    // Add to watchlist
    addToWatchlist: builder.mutation<WatchlistItem, { symbol: string; notes?: string }>({
      query: (data) => ({
        url: '/realtime/watchlist',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [WATCHLIST_TAG],
    }),

    // Remove from watchlist
    removeFromWatchlist: builder.mutation<void, string>({
      query: (symbol) => ({
        url: `/realtime/watchlist/${symbol}`,
        method: 'DELETE',
      }),
      invalidatesTags: [WATCHLIST_TAG],
    }),

    // Update watchlist notes
    updateWatchlistNotes: builder.mutation<WatchlistItem, { symbol: string; notes: string }>({
      query: ({ symbol, notes }) => ({
        url: `/realtime/watchlist/${symbol}/notes`,
        method: 'PATCH',
        body: { notes },
      }),
      invalidatesTags: [WATCHLIST_TAG],
    }),
  }),
});

// Export hooks for components
export const {
  useGetMarketDataQuery,
  useGetQuoteQuery,
  useGetOHLCVQuery,
  useGetTradingSignalsQuery,
  useExecuteSignalMutation,
  useCancelSignalMutation,
  useGetWebSocketStatusQuery,
  useGetSubscriptionsQuery,
  useSubscribeMarketDataMutation,
  useSubscribeSignalsMutation,
  useUnsubscribeMutation,
  useGetAlertsQuery,
  useMarkAlertReadMutation,
  useMarkAllAlertsReadMutation,
  useDeleteAlertMutation,
  useGetPriceAlertsQuery,
  useCreatePriceAlertMutation,
  useDeletePriceAlertMutation,
  useGetWatchlistQuery,
  useAddToWatchlistMutation,
  useRemoveFromWatchlistMutation,
  useUpdateWatchlistNotesMutation,
} = realtimeApi;

// Export reducer and middleware for store configuration
export const realtimeReducer = realtimeApi.reducer;
export const realtimeMiddleware = realtimeApi.middleware;

// Export WebSocket URL for direct WebSocket connections
export { WS_BASE_URL };
