import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type {
  AnalyticsData,
  ReportConfig,
  ChartData
} from '@types/index'
import type { RootState } from '../index'

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: '/api/analytics',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('content-type', 'application/json')
    return headers
  },
})

export const analyticsApi = createApi({
  reducerPath: 'analyticsApi',
  baseQuery,
  tagTypes: ['Analytics', 'Report', 'Chart'],
  endpoints: (builder) => ({
    // Analytics dashboard data
    getAnalyticsData: builder.query<AnalyticsData, {
      timeRange?: '1d' | '1w' | '1m' | '3m' | '1y';
      strategies?: string[];
      includeBenchmark?: boolean;
    }>({
      query: ({
        timeRange = '1m',
        strategies,
        includeBenchmark = true,
      }) => ({
        url: '/dashboard',
        params: {
          time_range: timeRange,
          strategies: strategies?.join(','),
          include_benchmark: includeBenchmark,
        },
      }),
      providesTags: ['Analytics'],
    }),

    // Portfolio analytics
    getPortfolioPerformance: builder.query<ChartData, {
      timeRange?: '1d' | '1w' | '1m' | '3m' | '1y';
      benchmark?: string;
      includeDividends?: boolean;
    }>({
      query: ({
        timeRange = '1m',
        benchmark,
        includeDividends = true,
      }) => ({
        url: '/portfolio/performance',
        params: {
          time_range: timeRange,
          benchmark,
          include_dividends: includeDividends,
        },
      }),
      providesTags: ['Chart'],
    }),

    getPortfolioAllocation: builder.query<{
      byStrategy: Array<{ name: string; value: number; percentage: number }>;
      byAsset: Array<{ name: string; value: number; percentage: number }>;
      byRisk: Array<{ name: string; value: number; percentage: number }>;
    }, void>({
      query: () => '/portfolio/allocation',
      providesTags: ['Analytics'],
    }),

    getPortfolioMetrics: builder.query<{
      totalValue: number;
      totalReturn: number;
      annualizedReturn: number;
      volatility: number;
      sharpeRatio: number;
      maxDrawdown: number;
      calmarRatio: number;
      winRate: number;
      profitFactor: number;
      var95: number;
      cvar95: number;
      beta: number;
      alpha: number;
      correlation: number;
    }, {
      timeRange?: '1d' | '1w' | '1m' | '3m' | '1y';
    }>({
      query: ({ timeRange = '1m' }) => ({
        url: '/portfolio/metrics',
        params: { time_range: timeRange },
      }),
      providesTags: ['Analytics'],
    }),

    // Strategy analytics
    getStrategyComparison: builder.query<ChartData, {
      strategies: string[];
      timeRange?: '1d' | '1w' | '1m' | '3m' | '1y';
      metrics?: string[];
    }>({
      query: ({
        strategies,
        timeRange = '1m',
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown'],
      }) => ({
        url: '/strategies/comparison',
        params: {
          strategies: strategies.join(','),
          time_range: timeRange,
          metrics: metrics.join(','),
        },
      }),
      providesTags: ['Chart'],
    }),

    getStrategyAnalytics: builder.query<{
      performance: ChartData;
      signals: ChartData;
      riskMetrics: Record<string, number>;
      drawdownPeriods: Array<{
        start: string;
        end: string;
        depth: number;
        duration: number;
        recovery: number;
      }>;
      monthlyReturns: Array<{ month: string; return: number }>;
    }, {
      strategyId: string;
      timeRange?: '1d' | '1w' | '1m' | '3m' | '1y';
    }>({
      query: ({
        strategyId,
        timeRange = '1m',
      }) => ({
        url: `/strategies/${strategyId}`,
        params: { time_range: timeRange },
      }),
      providesTags: ['Analytics', 'Chart'],
    }),

    // Market analytics
    getMarketSentiment: builder.query<{
      overall: 'bullish' | 'bearish' | 'neutral';
      score: number;
      trends: Array<{
        period: string;
        sentiment: 'bullish' | 'bearish' | 'neutral';
        score: number;
        change: number;
      }>;
      factors: Array<{
        name: string;
        weight: number;
        value: number;
        impact: 'positive' | 'negative' | 'neutral';
      }>;
    }, {
      timeRange?: '1d' | '1w' | '1m';
    }>({
      query: ({ timeRange = '1w' }) => ({
        url: '/market/sentiment',
        params: { time_range: timeRange },
      }),
      providesTags: ['Analytics'],
    }),

    getMarketCorrelationMatrix: builder.query<ChartData, {
      assets: string[];
      timeRange?: '1m' | '3m' | '1y';
    }>({
      query: ({ assets, timeRange = '3m' }) => ({
        url: '/market/correlation',
        params: {
          assets: assets.join(','),
          time_range: timeRange,
        },
      }),
      providesTags: ['Chart'],
    }),

    // Risk analytics
    getRiskAnalysis: builder.query<{
      varAnalysis: {
        var95: number;
        var99: number;
        cvar95: number;
        cvar99: number;
        timeHorizon: string;
      };
      stressTest: Array<{
        scenario: string;
        impact: number;
        probability: number;
        description: string;
      }>;
      riskContribution: Array<{
        strategy: string;
        contribution: number;
        percentage: number;
      }>;
      concentrationRisk: {
        hhi: number;
        top10Concentration: number;
        diversificationRatio: number;
      };
    }, {
      portfolio?: string;
      timeRange?: '1m' | '3m' | '1y';
    }>({
      query: ({ portfolio, timeRange = '3m' }) => ({
        url: '/risk/analysis',
        params: {
          portfolio,
          time_range: timeRange,
        },
      }),
      providesTags: ['Analytics'],
    }),

    // Reports
    generateReport: builder.mutation<{
      reportId: string;
      downloadUrl: string;
      format: string;
      size: number;
    }, ReportConfig>({
      query: (config) => ({
        url: '/reports/generate',
        method: 'POST',
        body: config,
      }),
      invalidatesTags: ['Report'],
    }),

    getReportStatus: builder.query<{
      reportId: string;
      status: 'pending' | 'processing' | 'completed' | 'failed';
      progress: number;
      downloadUrl?: string;
      error?: string;
    }, string>({
      query: (reportId) => `/reports/${reportId}/status`,
      providesTags: (result, error, reportId) => [{ type: 'Report', id: reportId }],
    }),

    downloadReport: builder.query<Blob, string>({
      query: (reportId) => `/reports/${reportId}/download`,
      providesTags: (result, error, reportId) => [{ type: 'Report', id: reportId }],
    }),

    // Data export
    exportData: builder.mutation<{
      exportId: string;
      downloadUrl: string;
      format: string;
      records: number;
    }, {
      dataType: 'strategies' | 'signals' | 'executions' | 'performance';
      format: 'csv' | 'excel' | 'json';
      filters?: Record<string, any>;
      fields?: string[];
    }>({
      query: (exportConfig) => ({
        url: '/export',
        method: 'POST',
        body: exportConfig,
      }),
    }),

    // Custom charts and queries
    executeCustomQuery: builder.mutation<any, {
      query: string;
      parameters?: Record<string, any>;
    }>({
      query: ({ query, parameters }) => ({
        url: '/custom-query',
        method: 'POST',
        body: { query, parameters },
      }),
    }),

    getSavedQueries: builder.query<Array<{
      id: string;
      name: string;
      description: string;
      query: string;
      parameters: Record<string, any>;
      createdAt: string;
      updatedAt: string;
    }>, void>({
      query: () => '/saved-queries',
    }),

    saveQuery: builder.mutation<void, {
      name: string;
      description?: string;
      query: string;
      parameters?: Record<string, any>;
    }>({
      query: (queryData) => ({
        url: '/saved-queries',
        method: 'POST',
        body: queryData,
      }),
    }),
  }),
})

export const {
  // Analytics dashboard data
  useGetAnalyticsDataQuery,

  // Portfolio analytics
  useGetPortfolioPerformanceQuery,
  useGetPortfolioAllocationQuery,
  useGetPortfolioMetricsQuery,

  // Strategy analytics
  useGetStrategyComparisonQuery,
  useGetStrategyAnalyticsQuery,

  // Market analytics
  useGetMarketSentimentQuery,
  useGetMarketCorrelationMatrixQuery,

  // Risk analytics
  useGetRiskAnalysisQuery,

  // Reports
  useGenerateReportMutation,
  useGetReportStatusQuery,
  useDownloadReportQuery,

  // Data export
  useExportDataMutation,

  // Custom charts and queries
  useExecuteCustomQueryMutation,
  useGetSavedQueriesQuery,
  useSaveQueryMutation,
} = analyticsApi

export default analyticsApi