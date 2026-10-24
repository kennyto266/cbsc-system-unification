import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { baseApi } from './baseApi'
import {
  MarketDataRequest,
  MarketDataResponse,
  TickerResponse,
  OrderBookResponse,
  RecentTradesResponse,
  IndicatorRequest,
  IndicatorResponse
} from '../../types/api'

// Market API slice
export const marketApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Market Data endpoints
    getMarketData: builder.query<MarketDataResponse, MarketDataRequest>({
      query: (params) => ({
        url: '/market/data',
        params,
      }),
      providesTags: ['MarketData', 'OHLC'],
    }),

    getTicker: builder.query<TickerResponse, string>({
      query: (symbol) => ({
        url: `/market/ticker/${symbol}`,
      }),
      providesTags: ['Ticker'],
    }),

    getMultipleTickers: builder.query<TickerResponse[], string[]>({
      query: (symbols) => ({
        url: '/market/tickers',
        params: { symbols: symbols.join(',') },
      }),
      providesTags: ['Ticker'],
    }),

    getOrderBook: builder.query<OrderBookResponse, { symbol: string; limit?: number }>({
      query: ({ symbol, limit = 100 }) => ({
        url: `/market/orderbook/${symbol}`,
        params: { limit },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'MarketData', id: symbol }],
    }),

    getRecentTrades: builder.query<RecentTradesResponse, { symbol: string; limit?: number }>({
      query: ({ symbol, limit = 50 }) => ({
        url: `/market/trades/${symbol}`,
        params: { limit },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'MarketData', id: symbol }],
    }),

    getKlines: builder.query<MarketDataResponse, MarketDataRequest>({
      query: (params) => ({
        url: '/market/klines',
        params,
      }),
      providesTags: ['OHLC'],
    }),

    // Indicator endpoints
    getIndicator: builder.query<IndicatorResponse, IndicatorRequest>({
      query: ({ symbol, indicator, parameters, interval, limit }) => ({
        url: `/market/indicators/${symbol}/${indicator}`,
        params: { ...parameters, interval, limit },
      }),
      providesTags: ['Indicator'],
    }),

    getMultipleIndicators: builder.query<IndicatorResponse[], Array<IndicatorRequest>>({
      query: (requests) => ({
        url: '/market/indicators/batch',
        method: 'POST',
        body: { requests },
      }),
      providesTags: ['Indicator'],
    }),

    // Market statistics
    getMarketStats: builder.query({
      query: () => '/market/stats',
      providesTags: ['MarketData'],
    }),

    getSymbolInfo: builder.query({
      query: (symbol: string) => `/market/symbols/${symbol}`,
      providesTags: ['MarketData'],
    }),

    getAllSymbols: builder.query({
      query: () => '/market/symbols',
      providesTags: ['MarketData'],
    }),

    // WebSocket subscription endpoints
    subscribeToTicker: builder.mutation<void, { symbol: string }>({
      query: ({ symbol }) => ({
        url: '/market/subscribe',
        method: 'POST',
        body: {
          channel: 'ticker',
          symbol,
        },
      }),
      invalidatesTags: (result, error, { symbol }) => [{ type: 'Ticker', id: symbol }],
    }),

    subscribeToTrades: builder.mutation<void, { symbol: string }>({
      query: ({ symbol }) => ({
        url: '/market/subscribe',
        method: 'POST',
        body: {
          channel: 'trade',
          symbol,
        },
      }),
    }),

    subscribeToOrderBook: builder.mutation<void, { symbol: string }>({
      query: ({ symbol }) => ({
        url: '/market/subscribe',
        method: 'POST',
        body: {
          channel: 'orderbook',
          symbol,
        },
      }),
    }),

    subscribeToKline: builder.mutation<void, { symbol: string; interval: string }>({
      query: ({ symbol, interval }) => ({
        url: '/market/subscribe',
        method: 'POST',
        body: {
          channel: 'kline',
          symbol,
          interval,
        },
      }),
      invalidatesTags: ['OHLC'],
    }),

    unsubscribeFromChannel: builder.mutation<void, { channel: string; symbol?: string }>({
      query: ({ channel, symbol }) => ({
        url: '/market/unsubscribe',
        method: 'POST',
        body: {
          channel,
          symbol,
        },
      }),
    }),

    // Historical data
    getHistoricalData: builder.query<MarketDataResponse, MarketDataRequest>({
      query: (params) => ({
        url: '/market/history',
        params,
      }),
      providesTags: ['MarketData', 'OHLC'],
    }),

    // Market sentiment
    getMarketSentiment: builder.query({
      query: ({ symbol, period = '24h' }) => ({
        url: '/market/sentiment',
        params: { symbol, period },
      }),
      providesTags: ['MarketData'],
    }),

    getMarketHeatmap: builder.query({
      query: () => '/market/heatmap',
      providesTags: ['MarketData'],
    }),

    // Price alerts
    setPriceAlert: builder.mutation({
      query: ({ symbol, price, condition }) => ({
        url: '/market/alerts',
        method: 'POST',
        body: { symbol, price, condition },
      }),
      invalidatesTags: ['Alert'],
    }),

    getPriceAlerts: builder.query({
      query: () => '/market/alerts',
      providesTags: ['Alert'],
    }),

    removePriceAlert: builder.mutation({
      query: (alertId: string) => ({
        url: `/market/alerts/${alertId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Alert'],
    }),
  }),
})

// Export hooks
export const {
  useGetMarketDataQuery,
  useGetTickerQuery,
  useGetMultipleTickersQuery,
  useGetOrderBookQuery,
  useGetRecentTradesQuery,
  useGetKlinesQuery,
  useGetIndicatorQuery,
  useGetMultipleIndicatorsQuery,
  useGetMarketStatsQuery,
  useGetSymbolInfoQuery,
  useGetAllSymbolsQuery,
  useSubscribeToTickerMutation,
  useSubscribeToTradesMutation,
  useSubscribeToOrderBookMutation,
  useSubscribeToKlineMutation,
  useUnsubscribeFromChannelMutation,
  useGetHistoricalDataQuery,
  useGetMarketSentimentQuery,
  useGetMarketHeatmapQuery,
  useSetPriceAlertMutation,
  useGetPriceAlertsQuery,
  useRemovePriceAlertMutation,
} = marketApi

export default marketApi