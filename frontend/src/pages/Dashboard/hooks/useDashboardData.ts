import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import {
  DashboardStats,
  Strategy,
  Trade,
  PerformanceData,
} from '../../../types/dashboard';
import { dashboardAPI } from '../../../services/dashboardAPI';

interface UseDashboardDataReturn {
  stats: DashboardStats | null;
  strategies: Strategy[];
  performanceData: PerformanceData[];
  trades: Trade[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useDashboardData = (
  period: string = '1M'
): UseDashboardDataReturn => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Fetch dashboard statistics
  const fetchStats = useCallback(async () => {
    try {
      const data = await dashboardAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setError(err as Error);
      toast.error('获取统计数据失败');
    }
  }, []);

  // Fetch strategies
  const fetchStrategies = useCallback(async () => {
    try {
      const { data } = await dashboardAPI.getStrategies({
        limit: 50,
        sortBy: 'return',
        sortOrder: 'desc',
      });
      setStrategies(data);
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
      setError(err as Error);
      toast.error('获取策略列表失败');
    }
  }, []);

  // Fetch performance data
  const fetchPerformanceData = useCallback(async () => {
    try {
      const data = await dashboardAPI.getPerformance({
        period,
      });
      setPerformanceData(data);
    } catch (err) {
      console.error('Failed to fetch performance data:', err);
      setError(err as Error);
      toast.error('获取绩效数据失败');
    }
  }, [period]);

  // Fetch recent trades
  const fetchTrades = useCallback(async () => {
    try {
      const { data } = await dashboardAPI.getTrades({
        limit: 20,
      });
      setTrades(data);
    } catch (err) {
      console.error('Failed to fetch trades:', err);
      setError(err as Error);
      toast.error('获取交易记录失败');
    }
  }, []);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchStats(),
        fetchStrategies(),
        fetchPerformanceData(),
        fetchTrades(),
      ]);
    } catch (err) {
      // Error handling is done in individual fetch functions
    } finally {
      setIsLoading(false);
    }
  }, [fetchStats, fetchStrategies, fetchPerformanceData, fetchTrades]);

  // Initial data fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Refetch function
  const refetch = useCallback(() => {
    fetchAllData();
  }, [fetchAllData]);

  return {
    stats,
    strategies,
    performanceData,
    trades,
    isLoading,
    error,
    refetch,
  };
};