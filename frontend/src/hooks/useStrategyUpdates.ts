/**
 * Hook for managing real-time strategy updates via WebSocket
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { StrategyStatus } from '../components/Widgets/StrategyStatusWidget';

interface UseStrategyUpdatesOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxRetries?: number;
}

interface StrategyUpdateData {
  type: 'strategy_update' | 'strategy_status' | 'strategy_pnl' | 'strategy_execution';
  strategyId: string;
  timestamp: number;
  data: Partial<StrategyStatus>;
}

interface UseStrategyUpdatesReturn {
  strategies: StrategyStatus[];
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate: number | null;
  error: string | null;

  // Actions
  toggleStrategy: (strategyId: string) => void;
  refreshStrategy: (strategyId: string) => void;
  refreshAll: () => void;

  // Statistics
  getActiveCount: () => number;
  getTotalPnL: () => number;
  getWinRate: () => number;
}

export const useStrategyUpdates = (options: UseStrategyUpdatesOptions = {}): UseStrategyUpdatesReturn => {
  const {
    autoReconnect = true,
    reconnectInterval = 5000,
    maxRetries = 10
  } = options;

  const [strategies, setStrategies] = useState<StrategyStatus[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const retryCount = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { subscribe, unsubscribe, send, connectionState } = useWebSocket();

  // Handle strategy toggle
  const toggleStrategy = useCallback(async (strategyId: string) => {
    try {
      const strategy = strategies.find(s => s.id === strategyId);
      if (!strategy) return;

      // Send toggle command via WebSocket
      send({
        channel: 'strategies',
        type: 'toggle_strategy',
        payload: {
          strategyId,
          enabled: strategy.status !== 'active'
        }
      });

      // Optimistically update local state
      setStrategies(prev =>
        prev.map(s =>
          s.id === strategyId
            ? {
                ...s,
                status: s.status === 'active' ? 'paused' : 'active',
                isRunning: s.status !== 'active'
              }
            : s
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle strategy');
    }
  }, [strategies, send]);

  // Refresh single strategy
  const refreshStrategy = useCallback(async (strategyId: string) => {
    try {
      send({
        channel: 'strategies',
        type: 'refresh_strategy',
        payload: { strategyId }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh strategy');
    }
  }, [send]);

  // Refresh all strategies
  const refreshAll = useCallback(async () => {
    try {
      send({
        channel: 'strategies',
        type: 'refresh_all_strategies',
        payload: {}
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh strategies');
    }
  }, [send]);

  // Get active strategies count
  const getActiveCount = useCallback(() => {
    return strategies.filter(s => s.status === 'active').length;
  }, [strategies]);

  // Get total P&L
  const getTotalPnL = useCallback(() => {
    return strategies.reduce((sum, s) => sum + s.dailyPnL, 0);
  }, [strategies]);

  // Get win rate
  const getWinRate = useCallback(() => {
    const winningStrategies = strategies.filter(s => s.dailyPnL > 0).length;
    return strategies.length > 0 ? (winningStrategies / strategies.length) * 100 : 0;
  }, [strategies]);

  // Handle WebSocket messages
  const handleStrategyMessage = useCallback((data: StrategyUpdateData) => {
    const { type, strategyId, timestamp, data: updateData } = data;

    setLastUpdate(timestamp);

    switch (type) {
      case 'strategy_update':
      case 'strategy_status':
        setStrategies(prev =>
          prev.map(strategy =>
            strategy.id === strategyId
              ? { ...strategy, ...updateData, lastExecution: new Date(timestamp) }
              : strategy
          )
        );
        break;

      case 'strategy_pnl':
        setStrategies(prev =>
          prev.map(strategy =>
            strategy.id === strategyId
              ? { ...strategy, ...updateData }
              : strategy
          )
        );
        break;

      case 'strategy_execution':
        setStrategies(prev =>
          prev.map(strategy =>
            strategy.id === strategyId
              ? {
                  ...strategy,
                  lastExecution: new Date(timestamp),
                  ...updateData
                }
              : strategy
          )
        );
        break;
    }
  }, []);

  // Initialize strategies (mock data for now)
  useEffect(() => {
    // In a real implementation, this would fetch from an API
    const mockStrategies: StrategyStatus[] = [
      {
        id: '1',
        name: 'Momentum Trading Strategy',
        status: 'active',
        lastExecution: new Date(Date.now() - 60000),
        nextExecution: new Date(Date.now() + 300000),
        dailyPnL: 1250.50,
        totalReturn: 15.3,
        symbol: 'AAPL',
        isRunning: true
      },
      {
        id: '2',
        name: 'Mean Reversion Arbitrage',
        status: 'active',
        lastExecution: new Date(Date.now() - 120000),
        dailyPnL: 890.25,
        totalReturn: 8.7,
        symbol: 'MSFT',
        isRunning: true
      },
      {
        id: '3',
        name: 'Volatility Surface Trading',
        status: 'paused',
        lastExecution: new Date(Date.now() - 300000),
        dailyPnL: -150.75,
        totalReturn: -2.1,
        symbol: 'GOOGL',
        isRunning: false
      },
      {
        id: '4',
        name: 'Statistical Arbitrage',
        status: 'error',
        lastExecution: new Date(Date.now() - 600000),
        dailyPnL: 0,
        totalReturn: 5.2,
        error: 'Connection timeout',
        symbol: 'TSLA',
        isRunning: false
      }
    ];

    setStrategies(mockStrategies);
  }, []);

  // Subscribe to strategy updates
  useEffect(() => {
    const unsubscribe = subscribe('strategies', (message) => {
      if (message.type?.startsWith('strategy_')) {
        handleStrategyMessage(message as StrategyUpdateData);
      }
    });

    return unsubscribe;
  }, [subscribe, handleStrategyMessage]);

  // Handle connection status changes
  useEffect(() => {
    setIsConnected(connectionState === 'connected');
    setConnectionStatus(connectionState);

    if (connectionState === 'connected') {
      retryCount.current = 0;
      setError(null);
    } else if (connectionState === 'error' && autoReconnect && retryCount.current < maxRetries) {
      retryCount.current++;
      setError(`Connection failed. Retrying... (${retryCount.current}/${maxRetries})`);

      reconnectTimeoutRef.current = setTimeout(() => {
        // Attempt to reconnect
        setConnectionStatus('connecting');
      }, reconnectInterval);
    } else if (connectionState === 'error' && retryCount.current >= maxRetries) {
      setError('Max retry attempts reached. Please refresh the page.');
    }
  }, [connectionState, autoReconnect, reconnectInterval, maxRetries]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    strategies,
    isConnected,
    connectionStatus,
    lastUpdate,
    error,
    toggleStrategy,
    refreshStrategy,
    refreshAll,
    getActiveCount,
    getTotalPnL,
    getWinRate
  };
};