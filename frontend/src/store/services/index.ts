/**
 * API Services Index
 * Central export point for all API services
 */

// Export all API services
export { authApi } from './authApi';
export { strategyApi } from './strategyApi';
export { userApi } from './userApi';
export { dashboardApi } from './dashboardApi';
export { marketDataApi } from './marketDataApi';

// Re-export realtime API from existing location
export { realtimeApi } from '../../api/endpoints/realtimeApi';

// Export utility hooks from authApi
export { useAuthState, useAuthActions } from './authApi';
export { useStrategiesWithFilters, useStrategyExecution, useStrategyBacktest } from './strategyApi';
export { useUsersWithFilters, useUserManagement } from './userApi';
export { useDashboardManagement, useCBSCDashboard } from './dashboardApi';
export { useMarketData, useMarketWatchlist } from './marketDataApi';