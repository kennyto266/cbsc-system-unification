/**
 * Market Data API Service
 * Redux Toolkit Query API slice for market data operations
 */

import { createApi } from '@reduxjs/toolkit/query/react';
import {
  baseQueryWithReauth,
  providesList,
} from '../../api/baseQuery';
import type { PaginatedResponse } from '../../types/api';

// Market data API slice
export const marketDataApi = createApi({
  reducerPath: 'marketDataApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['MarketData', 'Instrument', 'OHLC', 'Ticker', 'Index', 'News', 'EconomicCalendar', 'TechnicalIndicator'],
  keepUnusedDataFor: 10, // Keep market data for 10 seconds only
  endpoints: (builder) => ({
    // Get market overview
    getMarketOverview: builder.query<any, {
      region?: string;
      sectors?: string[];
    }>({
      query: ({ region, sectors }) => ({
        url: '/market/overview',
        params: { region, sectors: sectors?.join(',') },
      }),
      providesTags: ['MarketData'],
    }),

    // Get instrument details
    getInstrument: builder.query<any, string>({
      query: (symbol) => `/market/instruments/${symbol}`,
      providesTags: (result, error, symbol) => [{ type: 'Instrument', id: symbol }],
    }),

    // Search instruments
    searchInstruments: builder.query<PaginatedResponse<any>, {
      query: string;
      type?: string;
      exchange?: string;
      limit?: number;
    }>({
      query: ({ query, type, exchange, limit = 20 }) => ({
        url: '/market/instruments/search',
        params: { q: query, type, exchange, limit },
      }),
      providesTags: (result) => providesList(result?.items || [], 'Instrument'),
    }),

    // Get real-time ticker data
    getTicker: builder.query<any, string[]>({
      query: (symbols) => ({
        url: '/market/ticker',
        params: { symbols: symbols.join(',') },
      }),
      providesTags: ['Ticker'],
    }),

    // Get OHLC data
    getOHLC: builder.query<any[], {
      symbol: string;
      interval: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M';
      startDate: string;
      endDate: string;
      limit?: number;
    }>({
      query: ({ symbol, interval, startDate, endDate, limit = 500 }) => ({
        url: `/market/ohlc/${symbol}`,
        params: { interval, start: startDate, end: endDate, limit },
      }),
      providesTags: (result, error, { symbol, interval }) => [
        { type: 'OHLC', id: `${symbol}-${interval}` }
      ],
    }),

    // Get market depth
    getMarketDepth: builder.query<any, {
      symbol: string;
      depth?: number;
    }>({
      query: ({ symbol, depth = 20 }) => ({
        url: `/market/depth/${symbol}`,
        params: { depth },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'MarketData', id: `depth-${symbol}` }],
    }),

    // Get recent trades
    getRecentTrades: builder.query<any[], {
      symbol: string;
      limit?: number;
    }>({
      query: ({ symbol, limit = 100 }) => ({
        url: `/market/trades/${symbol}`,
        params: { limit },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'MarketData', id: `trades-${symbol}` }],
    }),

    // Get market statistics
    getMarketStats: builder.query<any, {
      symbol?: string;
      period?: string;
    }>({
      query: ({ symbol, period }) => ({
        url: '/market/stats',
        params: { symbol, period },
      }),
      providesTags: ['MarketData'],
    }),

    // Get sector performance
    getSectorPerformance: builder.query<any[], {
      market?: string;
      period?: string;
    }>({
      query: ({ market, period = '1d' }) => ({
        url: '/market/sectors/performance',
        params: { market, period },
      }),
      providesTags: ['MarketData'],
    }),

    // Get index constituents
    getIndexConstituents: builder.query<any[], {
      index: string;
      limit?: number;
    }>({
      query: ({ index, limit = 100 }) => ({
        url: `/market/index/${index}/constituents`,
        params: { limit },
      }),
      providesTags: (result, error, { index }) => [{ type: 'Index', id: index }],
    }),

    // Get market movers
    getMarketMovers: builder.query<any, {
      market?: string;
      type?: 'gainers' | 'losers' | 'most_active';
      limit?: number;
    }>({
      query: ({ market, type = 'gainers', limit = 20 }) => ({
        url: '/market/movers',
        params: { market, type, limit },
      }),
      providesTags: ['MarketData'],
    }),

    // Get market news
    getMarketNews: builder.query<any[], {
      symbols?: string[];
      categories?: string[];
      limit?: number;
      offset?: number;
    }>({
      query: ({ symbols, categories, limit = 20, offset = 0 }) => ({
        url: '/market/news',
        params: {
          symbols: symbols?.join(','),
          categories: categories?.join(','),
          limit,
          offset,
        },
      }),
      providesTags: ['News'],
    }),

    // Get economic calendar
    getEconomicCalendar: builder.query<any[], {
      startDate?: string;
      endDate?: string;
      importance?: string[];
      countries?: string[];
      limit?: number;
    }>({
      query: ({ startDate, endDate, importance, countries, limit = 50 }) => ({
        url: '/market/calendar/economic',
        params: {
          start: startDate,
          end: endDate,
          importance: importance?.join(','),
          countries: countries?.join(','),
          limit,
        },
      }),
      providesTags: ['EconomicCalendar'],
    }),

    // Get earnings calendar
    getEarningsCalendar: builder.query<any[], {
      startDate?: string;
      endDate?: string;
      symbols?: string[];
      limit?: number;
    }>({
      query: ({ startDate, endDate, symbols, limit = 50 }) => ({
        url: '/market/calendar/earnings',
        params: {
          start: startDate,
          end: endDate,
          symbols: symbols?.join(','),
          limit,
        },
      }),
      providesTags: ['EconomicCalendar'],
    }),

    // Get technical indicators
    getTechnicalIndicators: builder.query<any, {
      symbol: string;
      indicators: string[];
      interval?: string;
      period?: number;
    }>({
      query: ({ symbol, indicators, interval = '1d', period = 20 }) => ({
        url: `/market/technical/${symbol}`,
        params: {
          indicators: indicators.join(','),
          interval,
          period,
        },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'TechnicalIndicator', id: symbol }],
    }),

    // Calculate custom technical indicator
    calculateTechnicalIndicator: builder.mutation<any, {
      symbol: string;
      indicator: string;
      params: Record<string, any>;
      data?: any[];
    }>({
      query: ({ symbol, indicator, params, data }) => ({
        url: `/market/technical/${symbol}/calculate`,
        method: 'POST',
        body: { indicator, params, data },
      }),
    }),

    // Get market sentiment
    getMarketSentiment: builder.query<any, {
      symbol?: string;
      market?: string;
    }>({
      query: ({ symbol, market }) => ({
        url: '/market/sentiment',
        params: { symbol, market },
      }),
      providesTags: ['MarketData'],
    }),

    // Get insider trades
    getInsiderTrades: builder.query<any[], {
      symbol?: string;
      limit?: number;
      offset?: number;
    }>({
      query: ({ symbol, limit = 20, offset = 0 }) => ({
        url: '/market/insider-trades',
        params: { symbol, limit, offset },
      }),
      providesTags: ['MarketData'],
    }),

    // Get institutional ownership
    getInstitutionalOwnership: builder.query<any, string>({
      query: (symbol) => `/market/institutional/${symbol}`,
      providesTags: (result, error, symbol) => [{ type: 'Instrument', id: `${symbol}-ownership` }],
    }),

    // Get short interest
    getShortInterest: builder.query<any, {
      symbol: string;
      period?: string;
    }>({
      query: ({ symbol, period }) => ({
        url: `/market/short-interest/${symbol}`,
        params: { period },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'Instrument', id: `${symbol}-short` }],
    }),

    // Get dividend history
    getDividendHistory: builder.query<any[], {
      symbol: string;
      startDate?: string;
      endDate?: string;
    }>({
      query: ({ symbol, startDate, endDate }) => ({
        url: `/market/dividends/${symbol}`,
        params: { start: startDate, end: endDate },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'Instrument', id: `${symbol}-dividends` }],
    }),

    // Get corporate actions
    getCorporateActions: builder.query<any[], {
      symbol?: string;
      types?: string[];
      startDate?: string;
      endDate?: string;
      limit?: number;
    }>({
      query: ({ symbol, types, startDate, endDate, limit = 50 }) => ({
        url: '/market/corporate-actions',
        params: {
          symbol,
          types: types?.join(','),
          start: startDate,
          end: endDate,
          limit,
        },
      }),
      providesTags: ['MarketData'],
    }),

    // Get market holidays
    getMarketHolidays: builder.query<any[], {
      market?: string;
      year?: number;
    }>({
      query: ({ market, year }) => ({
        url: '/market/holidays',
        params: { market, year },
      }),
      providesTags: ['MarketData'],
    }),

    // Get market hours
    getMarketHours: builder.query<any, {
      market?: string;
      date?: string;
    }>({
      query: ({ market, date }) => ({
        url: '/market/hours',
        params: { market, date },
      }),
      providesTags: ['MarketData'],
    }),
  }),
});

// Export hooks
export const {
  // Market overview and instruments
  useGetMarketOverviewQuery,
  useGetInstrumentQuery,
  useSearchInstrumentsQuery,
  useGetTickerQuery,

  // Price data
  useGetOHLCQuery,
  useGetMarketDepthQuery,
  useGetRecentTradesQuery,

  // Market statistics
  useGetMarketStatsQuery,
  useGetSectorPerformanceQuery,
  useGetMarketMoversQuery,

  // Indices
  useGetIndexConstituentsQuery,

  // News and calendar
  useGetMarketNewsQuery,
  useGetEconomicCalendarQuery,
  useGetEarningsCalendarQuery,

  // Technical analysis
  useGetTechnicalIndicatorsQuery,
  useCalculateTechnicalIndicatorMutation,

  // Market sentiment and analytics
  useGetMarketSentimentQuery,
  useGetInsiderTradesQuery,
  useGetInstitutionalOwnershipQuery,
  useGetShortInterestQuery,

  // Dividends and corporate actions
  useGetDividendHistoryQuery,
  useGetCorporateActionsQuery,

  // Market information
  useGetMarketHolidaysQuery,
  useGetMarketHoursQuery,
} = marketDataApi;

// Utility hooks
export const useMarketData = (symbol: string) => {
  const { data: instrument, isLoading: instrumentLoading } = useGetInstrumentQuery(symbol);
  const { data: ticker, isLoading: tickerLoading } = useGetTickerQuery([symbol]);
  const { data: ohlc, isLoading: ohlcLoading } = useGetOHLCQuery({
    symbol,
    interval: '1d',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    endDate: new Date().toISOString(),
  });
  const { data: depth, isLoading: depthLoading } = useGetMarketDepthQuery({ symbol });
  const { data: technical, isLoading: technicalLoading } = useGetTechnicalIndicatorsQuery({
    symbol,
    indicators: ['RSI', 'MACD', 'SMA', 'EMA'],
  });

  return {
    instrument,
    ticker: ticker?.[0],
    ohlc,
    depth,
    technical,
    isLoading: instrumentLoading || tickerLoading || ohlcLoading || depthLoading || technicalLoading,
  };
};

export const useMarketWatchlist = (symbols: string[]) => {
  const { data: tickers, isLoading: tickersLoading } = useGetTickerQuery(symbols);
  const { data: movers, isLoading: moversLoading } = useGetMarketMoversQuery({});
  const { data: overview, isLoading: overviewLoading } = useGetMarketOverviewQuery({});

  return {
    tickers: tickers || [],
    movers,
    overview,
    isLoading: tickersLoading || moversLoading || overviewLoading,
  };
};