/**
 * Custom Hook for Polling Task Progress
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { message } from 'antd';
import marketOptimizationApi from '../services/marketOptimizationApi';
import type { ProgressData, OptimizationResults } from '../types/market-optimization';

interface UseTaskPollingResult {
  progress: ProgressData | null;
  results: OptimizationResults | null;
  isLoading: boolean;
  error: string | null;
  startPolling: (taskId: string) => void;
  stopPolling: () => void;
  isPolling: boolean;
}

export const useTaskPolling = (pollInterval: number = 2000): UseTaskPollingResult => {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [results, setResults] = useState<OptimizationResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const taskIdRef = useRef<string | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback((taskId: string) => {
    taskIdRef.current = taskId;
    setIsPolling(true);
    setIsLoading(true);
    setError(null);

    // Initial fetch
    marketOptimizationApi.getProgress(taskId)
      .then((data) => {
        setProgress(data);

        if (data.status === 'completed') {
          // Task already completed, fetch results
          return marketOptimizationApi.getResults(taskId);
        } else if (data.status === 'failed') {
          throw new Error('Task failed');
        }
        return null;
      })
      .then((resultsData) => {
        if (resultsData) {
          setResults(resultsData);
          setIsLoading(false);
          setIsPolling(false);
        } else {
          // Start polling
          intervalRef.current = setInterval(async () => {
            try {
              const progressData = await marketOptimizationApi.getProgress(taskId);

              setProgress(progressData);

              if (progressData.status === 'completed') {
                const resultsData = await marketOptimizationApi.getResults(taskId);
                setResults(resultsData);
                setIsLoading(false);
                stopPolling();
                message.success('優化完成！');
              } else if (progressData.status === 'failed') {
                throw new Error('Task failed');
              }
            } catch (err: any) {
              setError(err.message || '獲取進度失敗');
              setIsLoading(false);
              stopPolling();
              message.error('優化失敗：' + (err.message || '未知錯誤'));
            }
          }, pollInterval);
        }
      })
      .catch((err: any) => {
        setError(err.message || '獲取任務狀態失敗');
        setIsLoading(false);
        message.error('錯誤：' + (err.message || '無法連接伺服器'));
      });
  }, [pollInterval, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    progress,
    results,
    isLoading,
    error,
    startPolling,
    stopPolling,
    isPolling
  };
};

export default useTaskPolling;
