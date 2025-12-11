/**
 * useStrategyDataEnhanced Hook
 * 增強版策略數據管理Hook，集成新的API服務和實時功能
 *
 * Task #002: API接口集成和數據獲取
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import strategyDataService, {
  StrategyPerformance,
  StrategyConfig,
  StrategyDetail,
  PerformanceSummary
} from '../services/strategyDataService';
import { getWebSocketService } from '../services/websocketService';
import { Strategy, PerformanceMetrics } from '../types/index';

// Hook state interface
interface UseStrategyDataEnhancedState {
  strategies: Strategy[];
  performances: StrategyPerformance[];
  selectedStrategy: StrategyDetail | null;
  performanceSummary: PerformanceSummary | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  autoRefreshEnabled: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

// Hook options interface
interface UseStrategyDataEnhancedOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableWebSocket?: boolean;
  initialStrategyName?: string;
}

// Custom hook for enhanced strategy data management
export function useStrategyDataEnhanced(options: UseStrategyDataEnhancedOptions = {}) {
  const {
    autoRefresh = true,
    refreshInterval = 10000, // 10 seconds as per Task #002
    enableWebSocket = true,
    initialStrategyName
  } = options;

  // State management
  const [state, setState] = useState<UseStrategyDataEnhancedState>({
    strategies: [],
    performances: [],
    selectedStrategy: null,
    performanceSummary: null,
    loading: false,
    error: null,
    lastUpdated: null,
    autoRefreshEnabled: autoRefresh,
    connectionStatus: 'disconnected'
  });

  // Refs for managing intervals and subscriptions
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const wsServiceRef = useRef<any>(null);
  const mountedRef = useRef(true);

  // Update state safely
  const updateState = useCallback((updates: Partial<UseStrategyDataEnhancedState>) => {
    if (mountedRef.current) {
      setState(prev => ({ ...prev, ...updates }));
    }
  }, []);

  // Error handler
  const handleError = useCallback((error: Error | string, context: string) => {
    const errorMessage = error instanceof Error ? error.message : error;
    console.error(`Error in ${context}:`, error);
    updateState({
      error: `${context}: ${errorMessage}`,
      loading: false
    });
  }, [updateState]);

  // Transform strategy config to Strategy type
  const transformStrategy = useCallback((config: StrategyConfig): Strategy => {
    return {
      id: config.name,
      name: config.name,
      type: config.strategy_type,
      status: config.enabled ? 'active' : 'inactive',
      parameters: config.parameters,
      description: config.description,
      created_at: config.created_at,
      updated_at: config.updated_at,
      performance: null // Will be populated separately
    };
  }, []);

  // Fetch strategy list
  const fetchStrategies = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });

      const response = await strategyDataService.getStrategyList();
      const transformedStrategies = response.strategies.map(transformStrategy);

      updateState({
        strategies: transformedStrategies,
        loading: false,
        lastUpdated: new Date()
      });

      return transformedStrategies;
    } catch (error) {
      handleError(error as Error, 'Failed to fetch strategies');
      return [];
    }
  }, [updateState, handleError, transformStrategy]);

  // Fetch performance data
  const fetchPerformances = useCallback(async (strategyName?: string) => {
    try {
      updateState({ loading: true, error: null });

      const performances = await strategyDataService.getStrategyPerformance(strategyName);

      updateState({
        performances,
        loading: false,
        lastUpdated: new Date()
      });

      return performances;
    } catch (error) {
      handleError(error as Error, 'Failed to fetch performances');
      return [];
    }
  }, [updateState, handleError]);

  // Fetch strategy details
  const fetchStrategyDetail = useCallback(async (strategyName: string) => {
    try {
      updateState({ loading: true, error: null });

      const detail = await strategyDataService.getStrategyDetail(strategyName);

      updateState({
        selectedStrategy: detail,
        loading: false,
        lastUpdated: new Date()
      });

      return detail;
    } catch (error) {
      handleError(error as Error, 'Failed to fetch strategy details');
      return null;
    }
  }, [updateState, handleError]);

  // Fetch performance summary
  const fetchPerformanceSummary = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });

      const summary = await strategyDataService.getPerformanceSummary();

      updateState({
        performanceSummary: summary,
        loading: false,
        lastUpdated: new Date()
      });

      return summary;
    } catch (error) {
      handleError(error as Error, 'Failed to fetch performance summary');
      return null;
    }
  }, [updateState, handleError]);

  // Toggle strategy status (enable/disable)
  const toggleStrategy = useCallback(async (strategyName: string, enabled: boolean) => {
    try {
      updateState({ loading: true, error: null });

      await strategyDataService.toggleStrategy(strategyName, enabled);

      // Refresh relevant data
      await Promise.all([
        fetchStrategies(),
        fetchPerformances()
      ]);

      // If this strategy is currently selected, refresh its details
      if (state.selectedStrategy?.name === strategyName) {
        await fetchStrategyDetail(strategyName);
      }

      updateState({ loading: false });
    } catch (error) {
      handleError(error as Error, `Failed to toggle strategy ${strategyName}`);
    }
  }, [state.selectedStrategy, fetchStrategies, fetchPerformances, fetchStrategyDetail, handleError]);

  // Refresh all data
  const refreshAllData = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });

      await Promise.all([
        fetchStrategies(),
        fetchPerformances(),
        fetchPerformanceSummary()
      ]);

      updateState({ loading: false });
    } catch (error) {
      handleError(error as Error, 'Failed to refresh data');
    }
  }, [fetchStrategies, fetchPerformances, fetchPerformanceSummary, handleError]);

  // Setup auto-refresh
  const setupAutoRefresh = useCallback(() => {
    if (!autoRefresh || refreshInterval <= 0) {
      return;
    }

    // Clear existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    // Setup new interval
    refreshIntervalRef.current = setInterval(() => {
      refreshAllData();
    }, refreshInterval);

    // Also setup service-level auto-refresh
    strategyDataService.setupAutoRefresh('all', refreshAllData, refreshInterval);
  }, [autoRefresh, refreshInterval, refreshAllData]);

  // Setup WebSocket listeners
  const setupWebSocketListeners = useCallback(() => {
    if (!enableWebSocket) {
      return;
    }

    const wsService = getWebSocketService();
    wsServiceRef.current = wsService;

    // Update connection status
    const updateConnectionStatus = () => {
      const status = wsService.getConnectionStatus();
      updateState({ connectionStatus: status as 'connected' | 'disconnected' | 'connecting' });
    };

    // Listen for connection events
    wsService.on('connect', updateConnectionStatus);
    wsService.on('disconnect', updateConnectionStatus);

    // Listen for real-time updates
    const handleMessage = (data: any) => {
      switch (data.type) {
        case 'strategy_update':
          // Refresh strategies when update received
          fetchStrategies();
          break;
        case 'performance_update':
          // Refresh performance data when update received
          fetchPerformances();
          break;
        case 'error':
          handleError(data.data.message || 'WebSocket error', 'Real-time update');
          break;
      }
    };

    wsService.on('message', handleMessage);

    // Subscribe to relevant channels
    wsService.subscribeToPerformance();
    wsService.requestCurrentState();

    // Initial status update
    updateConnectionStatus();

    return () => {
      wsService.off('connect', updateConnectionStatus);
      wsService.off('disconnect', updateConnectionStatus);
      wsService.off('message', handleMessage);
    };
  }, [enableWebSocket, fetchStrategies, fetchPerformances, handleError]);

  // Initialize data
  const initialize = useCallback(async () => {
    try {
      updateState({ loading: true, error: null });

      // Fetch initial data
      const [strategies, performances, summary] = await Promise.all([
        fetchStrategies(),
        fetchPerformances(),
        fetchPerformanceSummary()
      ]);

      // Load initial strategy if specified
      if (initialStrategyName && strategies.length > 0) {
        const strategy = strategies.find(s => s.name === initialStrategyName);
        if (strategy) {
          await fetchStrategyDetail(initialStrategyName);
        }
      }

      updateState({ loading: false });
    } catch (error) {
      handleError(error as Error, 'Failed to initialize data');
    }
  }, [initialStrategyName, fetchStrategies, fetchPerformances, fetchPerformanceSummary, fetchStrategyDetail, handleError]);

  // Toggle auto-refresh
  const toggleAutoRefresh = useCallback(() => {
    const newState = !state.autoRefreshEnabled;
    updateState({ autoRefreshEnabled: newState });

    if (newState) {
      setupAutoRefresh();
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
      strategyDataService.stopAutoRefresh('all');
    }
  }, [state.autoRefreshEnabled, setupAutoRefresh]);

  // Clear cache
  const clearCache = useCallback(() => {
    strategyDataService.clearCache();
  }, []);

  // Get cache statistics
  const getCacheStats = useCallback(() => {
    return strategyDataService.getCacheStats();
  }, []);

  // Health check
  const healthCheck = useCallback(async () => {
    return await strategyDataService.healthCheck();
  }, []);

  // Effects
  useEffect(() => {
    // Initialize on mount
    initialize();

    // Setup WebSocket listeners
    const cleanupWS = setupWebSocketListeners();

    // Setup auto-refresh
    setupAutoRefresh();

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;

      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }

      strategyDataService.stopAutoRefresh('all');

      if (cleanupWS) {
        cleanupWS();
      }
    };
  }, []); // Only run once on mount

  // Return state and actions
  return {
    // State
    ...state,

    // Actions
    fetchStrategies,
    fetchPerformances,
    fetchStrategyDetail,
    fetchPerformanceSummary,
    toggleStrategy,
    refreshAllData,
    toggleAutoRefresh,
    clearCache,
    getCacheStats,
    healthCheck,

    // Legacy compatibility - transform performances to old format
    performance: state.performances.reduce((acc, perf) => {
      acc[perf.name] = {
        strategy_id: perf.name,
        sharpeRatio: perf.sharpe_ratio,
        maxDrawdown: perf.max_drawdown,
        totalReturn: perf.total_return,
        winRate: perf.win_rate,
        daily_pnl: perf.daily_pnl || 0,
        volatility: perf.volatility || 0,
        calmar_ratio: perf.calmar_ratio || 0,
        profit_factor: perf.profit_factor || 0,
        last_updated: perf.last_updated
      } as PerformanceMetrics;
      return acc;
    }, {} as Record<string, PerformanceMetrics>)
  };
}

// Export types for external use
export type {
  UseStrategyDataEnhancedState,
  UseStrategyDataEnhancedOptions
};

// Export hook as default
export default useStrategyDataEnhanced;