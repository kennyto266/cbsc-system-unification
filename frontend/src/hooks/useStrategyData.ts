import { useState, useEffect, useCallback } from 'react';
import { Strategy, PerformanceMetrics, PerformanceSummary, ApiResponse, StrategyListResponse } from '../types/index';

interface UseStrategyDataOptions {
  apiUrl: string;
  refreshInterval?: number;
  autoRefresh?: boolean;
}

export const useStrategyData = ({
  apiUrl,
  refreshInterval = 30000,
  autoRefresh = true
}: UseStrategyDataOptions) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performance, setPerformance] = useState<Record<string, PerformanceMetrics>>({});
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Generic API request handler
  const apiRequest = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> => {
    try {
      const response = await fetch(`${apiUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data: data.data || data,
        timestamp: new Date().toISOString(),
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error(`API request failed for ${endpoint}:`, err);
      return {
        success: false,
        error: errorMessage,
        timestamp: new Date().toISOString(),
      };
    }
  }, [apiUrl]);

  // Fetch strategies
  const fetchStrategies = useCallback(async () => {
    try {
      const result = await apiRequest<StrategyListResponse>('/strategies');

      if (result.success && result.data) {
        setStrategies(result.data.strategies || []);
        setError(null);
      } else {
        throw new Error(result.error || 'Failed to fetch strategies');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch strategies';
      setError(errorMessage);
      console.error('Failed to fetch strategies:', err);
    }
  }, [apiRequest]);

  // Fetch performance metrics
  const fetchPerformanceMetrics = useCallback(async () => {
    try {
      const result = await apiRequest<Record<string, PerformanceMetrics>>('/performance/summary');

      if (result.success && result.data) {
        setPerformance(result.data.strategies || {});
        setError(null);
      } else {
        throw new Error(result.error || 'Failed to fetch performance metrics');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch performance metrics';
      setError(errorMessage);
      console.error('Failed to fetch performance metrics:', err);
    }
  }, [apiRequest]);

  // Fetch performance summary
  const fetchPerformanceSummary = useCallback(async () => {
    try {
      const result = await apiRequest<PerformanceSummary>('/performance/summary');

      if (result.success && result.data) {
        // Calculate summary from the data
        const strategies = result.data.strategies || {};
        const strategyArray = Object.values(strategies) as PerformanceMetrics[];

        if (strategyArray.length > 0) {
          const avgSharpe = strategyArray.reduce((sum, p) => sum + p.sharpeRatio, 0) / strategyArray.length;
          const avgReturn = strategyArray.reduce((sum, p) => sum + p.annualReturn, 0) / strategyArray.length;

          const bestPerformer = strategyArray.reduce((best, current) =>
            current.sharpeRatio > best.sharpeRatio ? current : best
          );

          const worstPerformer = strategyArray.reduce((worst, current) =>
            current.sharpeRatio < worst.sharpeRatio ? current : worst
          );

          const summary: PerformanceSummary = {
            totalStrategies: strategyArray.length,
            activeStrategies: strategyArray.length, // This should come from strategy status
            averageSharpeRatio: avgSharpe,
            averageReturn: avgReturn,
            bestPerforming: {
              strategyId: bestPerformer.strategy_id,
              strategyName: bestPerformer.strategy_id,
              sharpeRatio: bestPerformer.sharpeRatio,
            },
            worstPerforming: {
              strategyId: worstPerformer.strategy_id,
              strategyName: worstPerformer.strategy_id,
              sharpeRatio: worstPerformer.sharpeRatio,
            },
          };

          setPerformanceSummary(summary);
        }
        setError(null);
      } else {
        throw new Error(result.error || 'Failed to fetch performance summary');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch performance summary';
      setError(errorMessage);
      console.error('Failed to fetch performance summary:', err);
    }
  }, [apiRequest]);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchStrategies(),
        fetchPerformanceMetrics(),
        fetchPerformanceSummary(),
      ]);
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  }, [fetchStrategies, fetchPerformanceMetrics, fetchPerformanceSummary]);

  // Update strategy parameters
  const updateStrategyParameters = useCallback(async (
    strategyId: string,
    parameters: Record<string, any>
  ): Promise<boolean> => {
    try {
      const result = await apiRequest(`/strategies/${strategyId}/parameters`, {
        method: 'POST',
        body: JSON.stringify({ parameters }),
      });

      if (result.success) {
        // Update local strategies state
        setStrategies(prev =>
          prev.map(strategy =>
            strategy.id === strategyId
              ? { ...strategy, parameters }
              : strategy
          )
        );
        return true;
      } else {
        throw new Error(result.error || 'Failed to update parameters');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update parameters';
      setError(errorMessage);
      console.error('Failed to update strategy parameters:', err);
      return false;
    }
  }, [apiRequest]);

  // Get strategy signals
  const getStrategySignals = useCallback(async (strategyId: string) => {
    try {
      const result = await apiRequest(`/strategies/${strategyId}/signals`);

      if (result.success) {
        return result.data?.signals || [];
      } else {
        throw new Error(result.error || 'Failed to fetch signals');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch signals';
      setError(errorMessage);
      console.error('Failed to fetch strategy signals:', err);
      return [];
    }
  }, [apiRequest]);

  // Validate strategy data
  const validateStrategyData = useCallback(async (strategyId: string, data: Record<string, any>) => {
    try {
      const result = await apiRequest(`/strategies/${strategyId}/validate`, {
        method: 'POST',
        body: JSON.stringify({ data }),
      });

      return result.success ? result.data : null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to validate data';
      setError(errorMessage);
      console.error('Failed to validate strategy data:', err);
      return null;
    }
  }, [apiRequest]);

  // Manual refetch
  const refetch = useCallback(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Initial data load
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || refreshInterval <= 0) return;

    const interval = setInterval(() => {
      fetchAllData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAllData]);

  return {
    strategies,
    performance,
    performanceSummary,
    loading,
    error,
    lastUpdate,
    refetch,
    updateStrategyParameters,
    getStrategySignals,
    validateStrategyData,
    fetchStrategies,
    fetchPerformanceMetrics,
  };
};