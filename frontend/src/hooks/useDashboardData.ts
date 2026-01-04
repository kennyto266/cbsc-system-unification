/**
 * Custom hook for Dashboard data management
 * Handles data fetching, caching, and real-time updates
 */

import { useEffect, useCallback, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import {
  fetchDashboardStats,
  fetchSystemHealth,
  fetchPerformanceData,
  fetchRecentAlerts,
  refreshDashboard,
  selectDashboardStats,
  selectSystemHealth,
  selectPerformanceData,
  selectAlerts,
  selectDashboardLoading,
  selectDashboardRefreshing,
  selectDashboardError,
  selectDashboardPreferences,
  setTimeRange,
  toggleAutoRefresh,
  setRefreshInterval,
  loadPreferences,
} from '../store/slices/dashboardSlice';

// Dashboard data interface
interface UseDashboardDataResult {
  // Data
  stats: ReturnType<typeof selectDashboardStats>;
  health: ReturnType<typeof selectSystemHealth>;
  performanceData: ReturnType<typeof selectPerformanceData>;
  alerts: ReturnType<typeof selectAlerts>;

  // UI State
  isLoading: ReturnType<typeof selectDashboardLoading>;
  isRefreshing: ReturnType<typeof selectDashboardRefreshing>;
  error: ReturnType<typeof selectDashboardError>;
  preferences: ReturnType<typeof selectDashboardPreferences>;

  // Actions
  setTimeRange: (range: string) => void;
  toggleAutoRefresh: () => void;
  setRefreshInterval: (interval: number) => void;
  refresh: () => void;
  refetch: () => Promise<void>;
}

/**
 * Hook for managing dashboard data
 * @param timeRange - Time range for performance data (default: '1M')
 */
export const useDashboardData = (timeRange: string = '1M'): UseDashboardDataResult => {
  const dispatch = useAppDispatch();

  // Selectors
  const stats = useAppSelector(selectDashboardStats);
  const health = useAppSelector(selectSystemHealth);
  const performanceData = useAppSelector(selectPerformanceData);
  const alerts = useAppSelector(selectAlerts);
  const isLoading = useAppSelector(selectDashboardLoading);
  const isRefreshing = useAppSelector(selectDashboardRefreshing);
  const error = useAppSelector(selectDashboardError);
  const preferences = useAppSelector(selectDashboardPreferences);

  // Track if this is the initial mount
  const isInitialMount = useRef(true);

  /**
   * Fetch all dashboard data
   */
  const fetchAllData = useCallback(async () => {
    try {
      await Promise.all([
        dispatch(fetchDashboardStats()),
        dispatch(fetchSystemHealth()),
        dispatch(fetchPerformanceData(timeRange)),
        dispatch(fetchRecentAlerts(10)),
      ]);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  }, [dispatch, timeRange]);

  /**
   * Refresh dashboard data
   */
  const refresh = useCallback(() => {
    dispatch(refreshDashboard());
  }, [dispatch]);

  /**
   * Refetch data (alias for fetchAllData)
   */
  const refetch = useCallback(async () => {
    await fetchAllData();
  }, [fetchAllData]);

  // Initial data fetch
  useEffect(() => {
    // Load preferences from localStorage
    dispatch(loadPreferences());

    if (isInitialMount.current) {
      fetchAllData();
      isInitialMount.current = false;
    }
  }, [dispatch, fetchAllData]);

  // Auto-refresh based on preferences
  useEffect(() => {
    if (!preferences.autoRefresh) return;

    const interval = setInterval(() => {
      refresh();
    }, preferences.refreshInterval);

    return () => clearInterval(interval);
  }, [preferences.autoRefresh, preferences.refreshInterval, refresh]);

  return {
    // Data
    stats,
    health,
    performanceData,
    alerts,

    // UI State
    isLoading,
    isRefreshing,
    error,
    preferences,

    // Actions
    setTimeRange: (range: string) => dispatch(setTimeRange(range)),
    toggleAutoRefresh: () => dispatch(toggleAutoRefresh()),
    setRefreshInterval: (interval: number) => dispatch(setRefreshInterval(interval)),
    refresh,
    refetch,
  };
};

export default useDashboardData;
