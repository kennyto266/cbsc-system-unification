/**
 * Dashboard API Service
 * Redux Toolkit Query API slice for dashboard operations
 */

import { createApi } from '@reduxjs/toolkit/query/react';
import {
  baseQueryWithReauth,
  providesList,
  invalidatesList,
} from '../../api/baseQuery';
import type { PaginatedResponse, SearchParams } from '../../types/api';

// Dashboard API slice
export const dashboardApi = createApi({
  reducerPath: 'dashboardApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Dashboard', 'Widget', 'Layout', 'QuickAction', 'MarketOverview', 'Portfolio', 'Performance', 'CBSC'],
  keepUnusedDataFor: 30, // Keep dashboard data for 30 seconds
  endpoints: (builder) => ({
    // Get dashboard configuration
    getDashboardConfig: builder.query<any, {
      id?: string;
      userId?: string;
    }>({
      query: ({ id, userId }) => ({
        url: '/dashboard/config',
        params: { id, userId },
      }),
      providesTags: (result, error, { id }) => [{ type: 'Dashboard', id: id || 'default' }],
    }),

    // Save dashboard configuration
    saveDashboardConfig: builder.mutation<any, {
      config: any;
      id?: string;
    }>({
      query: ({ config, id }) => ({
        url: '/dashboard/config',
        method: 'POST',
        body: { config, id },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Dashboard', id: id || 'default' }],
    }),

    // Get dashboard widgets
    getWidgets: builder.query<any[], {
      dashboardId?: string;
      category?: string;
    }>({
      query: ({ dashboardId, category }) => ({
        url: '/dashboard/widgets',
        params: { dashboardId, category },
      }),
      providesTags: (result) => providesList(result || [], 'Widget'),
    }),

    // Add widget to dashboard
    addWidget: builder.mutation<any, {
      widget: any;
      dashboardId?: string;
    }>({
      query: ({ widget, dashboardId }) => ({
        url: '/dashboard/widgets',
        method: 'POST',
        body: { widget, dashboardId },
      }),
      invalidatesTags: (result, error, { dashboardId }) => [
        { type: 'Widget', id: 'LIST' },
        { type: 'Dashboard', id: dashboardId || 'default' },
      ],
    }),

    // Update widget
    updateWidget: builder.mutation<any, {
      id: string;
      widget: any;
    }>({
      query: ({ id, widget }) => ({
        url: `/dashboard/widgets/${id}`,
        method: 'PUT',
        body: widget,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Widget', id },
      ],
    }),

    // Remove widget
    removeWidget: builder.mutation<void, string>({
      query: (id) => ({
        url: `/dashboard/widgets/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Widget', id },
        { type: 'Widget', id: 'LIST' },
      ],
    }),

    // Get widget data
    getWidgetData: builder.query<any, {
      widgetId: string;
      params?: Record<string, any>;
    }>({
      query: ({ widgetId, params }) => ({
        url: `/dashboard/widgets/${widgetId}/data`,
        params,
      }),
      providesTags: (result, error, { widgetId }) => [{ type: 'Widget', id: `${widgetId}-data` }],
    }),

    // Get dashboard layout
    getLayout: builder.query<any, {
      dashboardId?: string;
    }>({
      query: ({ dashboardId }) => ({
        url: '/dashboard/layout',
        params: { dashboardId },
      }),
      providesTags: (result, error, { dashboardId }) => [{ type: 'Layout', id: dashboardId || 'default' }],
    }),

    // Save dashboard layout
    saveLayout: builder.mutation<any, {
      layout: any;
      dashboardId?: string;
    }>({
      query: ({ layout, dashboardId }) => ({
        url: '/dashboard/layout',
        method: 'POST',
        body: { layout, dashboardId },
      }),
      invalidatesTags: (result, error, { dashboardId }) => [{ type: 'Layout', id: dashboardId || 'default' }],
    }),

    // Get quick actions
    getQuickActions: builder.query<any[], {
      category?: string;
    }>({
      query: ({ category }) => ({
        url: '/dashboard/quick-actions',
        params: { category },
      }),
      providesTags: ['QuickAction'],
    }),

    // Execute quick action
    executeQuickAction: builder.mutation<any, {
      actionId: string;
      params?: Record<string, any>;
    }>({
      query: ({ actionId, params }) => ({
        url: `/dashboard/quick-actions/${actionId}/execute`,
        method: 'POST',
        body: params,
      }),
    }),

    // Get market overview
    getMarketOverview: builder.query<any, {
      markets?: string[];
      indices?: string[];
    }>({
      query: ({ markets, indices }) => ({
        url: '/dashboard/market-overview',
        params: { markets: markets?.join(','), indices: indices?.join(',') },
      }),
      providesTags: ['MarketOverview'],
    }),

    // Get portfolio summary
    getPortfolioSummary: builder.query<any, {
      portfolioId?: string;
    }>({
      query: ({ portfolioId }) => ({
        url: '/dashboard/portfolio-summary',
        params: { portfolioId },
      }),
      providesTags: ['Portfolio'],
    }),

    // Get performance metrics
    getPerformanceMetrics: builder.query<any, {
      period?: string;
      strategyIds?: string[];
    }>({
      query: ({ period, strategyIds }) => ({
        url: '/dashboard/performance-metrics',
        params: { period, strategyIds: strategyIds?.join(',') },
      }),
      providesTags: ['Performance'],
    }),

    // CBSC specific endpoints
    getCBSCTokenStatus: builder.query<any, void>({
      query: () => '/dashboard/cbsc/token-status',
      providesTags: ['CBSC'],
    }),

    refreshCBSCToken: builder.mutation<any, void>({
      query: () => ({
        url: '/dashboard/cbsc/refresh-token',
        method: 'POST',
      }),
      invalidatesTags: ['CBSC'],
    }),

    getCBSCSystemStatus: builder.query<any, void>({
      query: () => '/dashboard/cbsc/system-status',
      providesTags: ['CBSC'],
    }),

    getCBSCStrategies: builder.query<any[], {
      status?: string;
      limit?: number;
    }>({
      query: ({ status, limit = 10 }) => ({
        url: '/dashboard/cbsc/strategies',
        params: { status, limit },
      }),
      providesTags: ['CBSC'],
    }),

    getCBSCPerformance: builder.query<any, {
      period?: string;
      strategyId?: string;
    }>({
      query: ({ period, strategyId }) => ({
        url: '/dashboard/cbsc/performance',
        params: { period, strategyId },
      }),
      providesTags: ['CBSC', 'Performance'],
    }),

    getCBSCRiskMetrics: builder.query<any, {
      portfolioId?: string;
    }>({
      query: ({ portfolioId }) => ({
        url: '/dashboard/cbsc/risk-metrics',
        params: { portfolioId },
      }),
      providesTags: ['CBSC'],
    }),

    getCBSCAlerts: builder.query<any[], {
      severity?: string;
      limit?: number;
    }>({
      query: ({ severity, limit = 20 }) => ({
        url: '/dashboard/cbsc/alerts',
        params: { severity, limit },
      }),
      providesTags: ['CBSC'],
    }),

    acknowledgeCBSCAlert: builder.mutation<void, string>({
      query: (alertId) => ({
        url: `/dashboard/cbsc/alerts/${alertId}/acknowledge`,
        method: 'POST',
      }),
      invalidatesTags: ['CBSC'],
    }),

    getCBSCHistory: builder.query<any, {
      type: string;
      startDate?: string;
      endDate?: string;
      limit?: number;
    }>({
      query: ({ type, startDate, endDate, limit = 50 }) => ({
        url: '/dashboard/cbsc/history',
        params: { type, startDate, endDate, limit },
      }),
      providesTags: ['CBSC'],
    }),

    // Export dashboard
    exportDashboard: builder.mutation<string, {
      dashboardId?: string;
      format?: 'json' | 'pdf' | 'csv';
    }>({
      query: ({ dashboardId, format = 'json' }) => ({
        url: '/dashboard/export',
        method: 'POST',
        body: { dashboardId, format },
        responseHandler: (response) => response.text(),
      }),
    }),

    // Import dashboard
    importDashboard: builder.mutation<any, {
      file: File;
      format?: 'json';
    }>({
      query: ({ file, format = 'json' }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', format);

        return {
          url: '/dashboard/import',
          method: 'POST',
          body: formData,
          headers: {}, // Let browser set Content-Type for FormData
        };
      },
      invalidatesTags: ['Dashboard', 'Widget', 'Layout'],
    }),

    // Share dashboard
    shareDashboard: builder.mutation<any, {
      dashboardId: string;
      users: string[];
      permissions: string[];
    }>({
      query: ({ dashboardId, users, permissions }) => ({
        url: `/dashboard/${dashboardId}/share`,
        method: 'POST',
        body: { users, permissions },
      }),
      invalidatesTags: (result, error, { dashboardId }) => [{ type: 'Dashboard', id: dashboardId }],
    }),

    // Get shared dashboards
    getSharedDashboards: builder.query<any[], void>({
      query: () => '/dashboard/shared',
      providesTags: ['Dashboard'],
    }),
  }),
});

// Export hooks
export const {
  // Dashboard configuration
  useGetDashboardConfigQuery,
  useSaveDashboardConfigMutation,

  // Widget management
  useGetWidgetsQuery,
  useAddWidgetMutation,
  useUpdateWidgetMutation,
  useRemoveWidgetMutation,
  useGetWidgetDataQuery,

  // Layout management
  useGetLayoutQuery,
  useSaveLayoutMutation,

  // Quick actions
  useGetQuickActionsQuery,
  useExecuteQuickActionMutation,

  // Dashboard data
  useGetMarketOverviewQuery,
  useGetPortfolioSummaryQuery,
  useGetPerformanceMetricsQuery,

  // CBSC specific
  useGetCBSCTokenStatusQuery,
  useRefreshCBSCTokenMutation,
  useGetCBSCSystemStatusQuery,
  useGetCBSCStrategiesQuery,
  useGetCBSCPerformanceQuery,
  useGetCBSCRiskMetricsQuery,
  useGetCBSCAlertsQuery,
  useAcknowledgeCBSCAlertMutation,
  useGetCBSCHistoryQuery,

  // Import/Export
  useExportDashboardMutation,
  useImportDashboardMutation,

  // Sharing
  useShareDashboardMutation,
  useGetSharedDashboardsQuery,
} = dashboardApi;

// Utility hooks
export const useDashboardManagement = (dashboardId?: string) => {
  const { data: config, isLoading: configLoading } = useGetDashboardConfigQuery({ id: dashboardId });
  const { data: widgets, isLoading: widgetsLoading } = useGetWidgetsQuery({ dashboardId });
  const { data: layout, isLoading: layoutLoading } = useGetLayoutQuery({ dashboardId });

  return {
    config,
    widgets: widgets || [],
    layout,
    isLoading: configLoading || widgetsLoading || layoutLoading,
  };
};

export const useCBSCDashboard = () => {
  const { data: tokenStatus } = useGetCBSCTokenStatusQuery();
  const { data: systemStatus } = useGetCBSCSystemStatusQuery();
  const { data: strategies } = useGetCBSCStrategiesQuery({});
  const { data: performance } = useGetCBSCPerformanceQuery({});
  const { data: alerts } = useGetCBSCAlertsQuery({});

  return {
    tokenStatus,
    systemStatus,
    strategies: strategies || [],
    performance,
    alerts: alerts || [],
    hasValidToken: tokenStatus?.isValid || false,
  };
};