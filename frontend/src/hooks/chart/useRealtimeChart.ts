/**
 * useRealtimeChart Hook
 *
 * A comprehensive hook for managing real-time chart data with WebSocket connections.
 * Handles data buffering, debouncing, automatic reconnection with exponential backoff,
 * data deduplication, and performance optimization with data windowing.
 *
 * @example
 * ```tsx
 * const MyChart = () => {
 *   const { data, isConnected, error } = useRealtimeChart({
 *     channelId: 'strategy-updates',
 *     initialData: [],
 *     maxDataPoints: 1000,
 *     updateThrottleMs: 100,
 *     reconnectAttempts: 5
 *   });
 *
 *   return (
 *     <Line data={data} options={{ responsive: true }} />
 *   );
 * };
 * ```
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useWebSocket } from '../useWebSocketEnhanced';
import { ChannelType, WSMessage, MessageType } from '../../types/websocket';

// Types for the hook
export interface ChartDataPoint {
  timestamp: number;
  value: number;
  label?: string;
  metadata?: Record<string, any>;
}

export interface RealtimeChartConfig {
  /** WebSocket channel to subscribe to */
  channelId: ChannelType;
  /** Initial data array */
  initialData?: ChartDataPoint[];
  /** Maximum number of data points to keep in memory */
  maxDataPoints?: number;
  /** Throttle updates to prevent too frequent renders */
  updateThrottleMs?: number;
  /** Enable data deduplication based on timestamp */
  enableDeduplication?: boolean;
  /** Time window for data retention in milliseconds */
  dataWindowMs?: number;
  /** WebSocket subscription filters */
  filters?: Record<string, any>;
  /** Custom data transformer function */
  dataTransformer?: (message: WSMessage) => ChartDataPoint | null;
  /** Callback when data is added */
  onDataAdd?: (data: ChartDataPoint) => void;
  /** Callback when data is removed */
  onDataRemove?: (removedCount: number) => void;
  /** Enable automatic reconnection */
  autoReconnect?: boolean;
  /** Maximum reconnection attempts */
  reconnectAttempts?: number;
  /** Initial reconnection delay in milliseconds */
  reconnectDelayMs?: number;
  /** Enable debug logging */
  enableDebug?: boolean;
}

export interface RealtimeChartState {
  /** Current chart data */
  data: ChartDataPoint[];
  /** Connection status */
  isConnected: boolean;
  /** Last error */
  error: Error | null;
  /** Number of data points received */
  totalPointsReceived: number;
  /** Number of duplicate points filtered out */
  duplicatePointsFiltered: number;
  /** Current reconnection attempt */
  reconnectAttempt: number;
  /** Connection quality */
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
  /** Last update timestamp */
  lastUpdate: number | null;
  /** Data rate in points per second */
  dataRate: number;
}

export interface RealtimeChartActions {
  /** Manually add data point */
  addDataPoint: (point: ChartDataPoint) => void;
  /** Clear all data */
  clearData: () => void;
  /** Set data window */
  setDataWindow: (windowMs: number) => void;
  /** Set max data points */
  setMaxDataPoints: (maxPoints: number) => void;
  /** Export current data */
  exportData: (format: 'json' | 'csv') => string;
  /** Pause/resume real-time updates */
  togglePause: () => void;
  /** Reconnect to WebSocket */
  reconnect: () => Promise<void>;
}

export interface UseRealtimeChartReturn extends RealtimeChartState, RealtimeChartActions {}

// Default configuration
const DEFAULT_CONFIG: Partial<RealtimeChartConfig> = {
  initialData: [],
  maxDataPoints: 1000,
  updateThrottleMs: 100,
  enableDeduplication: true,
  dataWindowMs: 3600000, // 1 hour
  autoReconnect: true,
  reconnectAttempts: 5,
  reconnectDelayMs: 1000,
  enableDebug: false,
};

// Utility functions
const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

const isDataPointEqual = (a: ChartDataPoint, b: ChartDataPoint): boolean => {
  return a.timestamp === b.timestamp && a.value === b.value;
};

const transformMessageToDataPoint = (message: WSMessage): ChartDataPoint | null => {
  try {
    // Default transformation logic
    if (message.type === MessageType.DATA || message.type === MessageType.STRATEGY_UPDATE) {
      const data = message.data;
      if (data && typeof data === 'object') {
        return {
          timestamp: data.timestamp || message.timestamp,
          value: typeof data.value === 'number' ? data.value : data.price || data.amount || 0,
          label: data.label || data.symbol || data.name,
          metadata: { ...data, timestamp: undefined, value: undefined, label: undefined }
        };
      }
    }
    return null;
  } catch (error) {
    console.error('Error transforming message to data point:', error);
    return null;
  }
};

/**
 * useRealtimeChart Hook
 *
 * @param config - Configuration object for the real-time chart
 * @returns Hook state and actions
 */
export const useRealtimeChart = (config: RealtimeChartConfig): UseRealtimeChartReturn => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  // State management
  const [data, setData] = useState<ChartDataPoint[]>(finalConfig.initialData || []);
  const [isPaused, setIsPaused] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [totalPointsReceived, setTotalPointsReceived] = useState(0);
  const [duplicatePointsFiltered, setDuplicatePointsFiltered] = useState(0);
  const [dataRate, setDataRate] = useState(0);

  // Refs for performance and cleanup
  const dataRef = useRef(data);
  const lastDataRateCalculation = useRef(Date.now());
  const recentDataPoints = useRef<ChartDataPoint[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout>();

  // Update ref when data changes
  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  // WebSocket connection
  const ws = useWebSocket(
    {
      // WebSocket config can be extended here
      reconnectAttempts: finalConfig.reconnectAttempts,
      reconnectDelay: finalConfig.reconnectDelayMs,
      enableLogging: finalConfig.enableDebug,
    },
    {
      autoConnect: finalConfig.autoReconnect,
      onConnect: () => {
        setReconnectAttempt(0);
        finalConfig.enableDebug && console.log('[useRealtimeChart] Connected to WebSocket');
      },
      onDisconnect: () => {
        finalConfig.enableDebug && console.log('[useRealtimeChart] Disconnected from WebSocket');
      },
      onError: (error) => {
        finalConfig.enableDebug && console.error('[useRealtimeChart] WebSocket error:', error);
      },
    }
  );

  // Data processing function with debouncing
  const processNewData = useCallback(
    debounce((newPoints: ChartDataPoint[]) => {
      if (isPaused || newPoints.length === 0) return;

      setData(prevData => {
        let updatedData = [...prevData];
        let removedCount = 0;
        let duplicateCount = 0;

        // Add new points with deduplication
        newPoints.forEach(newPoint => {
          // Check for duplicates if enabled
          if (finalConfig.enableDeduplication) {
            const isDuplicate = updatedData.some(existingPoint =>
              isDataPointEqual(existingPoint, newPoint)
            );
            if (isDuplicate) {
              duplicateCount++;
              return;
            }
          }

          updatedData.push(newPoint);
          finalConfig.onDataAdd?.(newPoint);
        });

        // Update duplicate count
        if (duplicateCount > 0) {
          setDuplicatePointsFiltered(prev => prev + duplicateCount);
        }

        // Apply data windowing if enabled
        if (finalConfig.dataWindowMs) {
          const cutoffTime = Date.now() - finalConfig.dataWindowMs;
          const beforeCount = updatedData.length;
          updatedData = updatedData.filter(point => point.timestamp > cutoffTime);
          removedCount += beforeCount - updatedData.length;
        }

        // Apply max data points limit
        if (finalConfig.maxDataPoints && updatedData.length > finalConfig.maxDataPoints) {
          const excessCount = updatedData.length - finalConfig.maxDataPoints;
          updatedData = updatedData.slice(excessCount);
          removedCount += excessCount;
        }

        // Sort by timestamp
        updatedData.sort((a, b) => a.timestamp - b.timestamp);

        // Notify about removed data
        if (removedCount > 0) {
          finalConfig.onDataRemove?.(removedCount);
        }

        return updatedData;
      });
    }, finalConfig.updateThrottleMs || 100),
    [isPaused, finalConfig]
  );

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message: WSMessage) => {
    if (isPaused) return;

    try {
      // Use custom transformer if provided, otherwise use default
      const dataPoint = finalConfig.dataTransformer
        ? finalConfig.dataTransformer(message)
        : transformMessageToDataPoint(message);

      if (dataPoint) {
        recentDataPoints.current.push(dataPoint);
        setTotalPointsReceived(prev => prev + 1);
        processNewData([dataPoint]);
      }
    } catch (error) {
      console.error('[useRealtimeChart] Error processing WebSocket message:', error);
    }
  }, [isPaused, finalConfig, processNewData]);

  // Subscribe to WebSocket channel
  useEffect(() => {
    if (ws.isConnected && finalConfig.channelId) {
      const unsubscribe = ws.subscribe(
        finalConfig.channelId,
        handleWebSocketMessage,
        finalConfig.filters
      );

      return () => {
        unsubscribe();
      };
    }
  }, [ws.isConnected, finalConfig.channelId, finalConfig.filters, handleWebSocketMessage, ws]);

  // Calculate data rate periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const timeDiff = now - lastDataRateCalculation.current;
      const pointCount = recentDataPoints.current.length;

      if (timeDiff > 0) {
        const rate = (pointCount / timeDiff) * 1000; // points per second
        setDataRate(rate);
        recentDataPoints.current = []; // Reset counter
        lastDataRateCalculation.current = now;
      }
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, []);

  // Update last update timestamp
  useEffect(() => {
    if (data.length > 0) {
      timeoutRef.current = setTimeout(() => {
        // This will run after the state update
      }, 0);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data]);

  // Manual actions
  const addDataPoint = useCallback((point: ChartDataPoint) => {
    processNewData([point]);
    setTotalPointsReceived(prev => prev + 1);
  }, [processNewData]);

  const clearData = useCallback(() => {
    setData([]);
    recentDataPoints.current = [];
  }, []);

  const setDataWindow = useCallback((windowMs: number) => {
    finalConfig.dataWindowMs = windowMs;
    // Trigger re-processing with new window
    processNewData([]);
  }, [finalConfig, processNewData]);

  const setMaxDataPoints = useCallback((maxPoints: number) => {
    finalConfig.maxDataPoints = maxPoints;
    // Trigger re-processing with new limit
    processNewData([]);
  }, [finalConfig, processNewData]);

  const exportData = useCallback((format: 'json' | 'csv'): string => {
    const exportData = dataRef.current;

    if (format === 'json') {
      return JSON.stringify(exportData, null, 2);
    } else if (format === 'csv') {
      const headers = ['timestamp', 'value', 'label'];
      const rows = exportData.map(point => [
        point.timestamp,
        point.value,
        point.label || ''
      ]);
      return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    return '';
  }, []);

  const togglePause = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  const reconnect = useCallback(async () => {
    try {
      await ws.reconnect();
    } catch (error) {
      console.error('[useRealtimeChart] Reconnection failed:', error);
    }
  }, [ws]);

  // Memoized return value
  const returnValue = useMemo<UseRealtimeChartReturn>(() => ({
    // State
    data,
    isConnected: ws.isConnected,
    error: ws.error,
    totalPointsReceived,
    duplicatePointsFiltered,
    reconnectAttempt,
    connectionQuality: ws.connectionQuality,
    lastUpdate: data.length > 0 ? data[data.length - 1].timestamp : null,
    dataRate,

    // Actions
    addDataPoint,
    clearData,
    setDataWindow,
    setMaxDataPoints,
    exportData,
    togglePause,
    reconnect,
  }), [
    data,
    ws.isConnected,
    ws.error,
    ws.connectionQuality,
    totalPointsReceived,
    duplicatePointsFiltered,
    reconnectAttempt,
    dataRate,
    addDataPoint,
    clearData,
    setDataWindow,
    setMaxDataPoints,
    exportData,
    togglePause,
    reconnect,
  ]);

  return returnValue;
};

// Export types for external use
export type {
  ChartDataPoint,
  RealtimeChartConfig,
  RealtimeChartState,
  RealtimeChartActions,
  UseRealtimeChartReturn
};