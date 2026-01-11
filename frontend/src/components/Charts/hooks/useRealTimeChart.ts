import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useToast } from '../../hooks/useToast';

// Real-time data point interface
export interface RealTimeDataPoint {
  timestamp: number;
  value: number;
  label?: string;
  metadata?: Record<string, any>;
}

// WebSocket configuration interface
interface RealTimeChartConfig {
  url?: string;
  channel?: string;
  maxDataPoints?: number;
  updateInterval?: number;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

// Return type for the hook
interface UseRealTimeChartReturn {
  data: RealTimeDataPoint[];
  isConnected: boolean;
  isPaused: boolean;
  error: string | null;
  lastUpdate: Date | null;
  pause: () => void;
  resume: () => void;
  clear: () => void;
  reconnect: () => void;
}

export const useRealTimeChart = (
  config: RealTimeChartConfig = {}
): UseRealTimeChartReturn => {
  const {
    url = process.env.REACT_APP_WS_URL || 'ws://localhost:3003',
    channel = 'chart-data',
    maxDataPoints = 100,
    updateInterval = 1000,
    autoReconnect = true,
    reconnectDelay = 3000
  } = config;

  const [data, setData] = useState<RealTimeDataPoint[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { addToast } = useToast();

  // Add new data point with buffer management
  const addDataPoint = useCallback((newPoint: RealTimeDataPoint) => {
    if (isPaused) return;

    setData(prevData => {
      const updatedData = [...prevData, newPoint];

      // Keep only the last maxDataPoints
      if (updatedData.length > maxDataPoints) {
        return updatedData.slice(-maxDataPoints);
      }

      return updatedData;
    });
    setLastUpdate(new Date());
  }, [isPaused, maxDataPoints]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (socketRef.current) {
        socketRef.current.close();
      }

      // Create new connection
      socketRef.current = io(url, {
        transports: ['websocket'],
        upgrade: false
      });

      // Connection events
      socketRef.current.on('connect', () => {
        setIsConnected(true);
        setError(null);
        addToast({
          type: 'success',
          message: '实时数据连接成功'
        });

        // Subscribe to channel
        socketRef.current?.emit('subscribe', { channel });
      });

      socketRef.current.on('disconnect', () => {
        setIsConnected(false);
        addToast({
          type: 'warning',
          message: '实时数据连接断开'
        });

        // Auto reconnect
        if (autoReconnect && !reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
            reconnectTimeoutRef.current = null;
          }, reconnectDelay);
        }
      });

      socketRef.current.on('connect_error', (err) => {
        setError(err.message);
        setIsConnected(false);
        addToast({
          type: 'error',
          message: `连接失败: ${err.message}`
        });
      });

      // Data event
      socketRef.current.on(channel, (newData: RealTimeDataPoint | RealTimeDataPoint[]) => {
        if (Array.isArray(newData)) {
          newData.forEach(point => addDataPoint(point));
        } else {
          addDataPoint(newData);
        }
      });

    } catch (err) {
      setError('Failed to establish connection');
      addToast({
        type: 'error',
        message: '建立连接失败'
      });
    }
  }, [url, channel, autoReconnect, reconnectDelay, addDataPoint, addToast]);

  // Initial connection
  useEffect(() => {
    connect();

    // Cleanup
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  // Pause data updates
  const pause = useCallback(() => {
    setIsPaused(true);
  }, []);

  // Resume data updates
  const resume = useCallback(() => {
    setIsPaused(false);
  }, []);

  // Clear all data
  const clear = useCallback(() => {
    setData([]);
    setLastUpdate(null);
  }, []);

  // Manual reconnect
  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    connect();
  }, [connect]);

  return {
    data,
    isConnected,
    isPaused,
    error,
    lastUpdate,
    pause,
    resume,
    clear,
    reconnect
  };
};