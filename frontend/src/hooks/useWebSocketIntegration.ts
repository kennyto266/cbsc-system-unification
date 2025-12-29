/**
 * WebSocket Integration Hook
 * Integrates WebSocket with RTK Query and Redux store for real-time updates
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import {
  useInitWebSocketMutation,
  useSubscribeToStrategyMutation,
  useSubscribeToMarketDataMutation,
  useSubscribeToNotificationsMutation,
  useGetWebSocketStatusQuery
} from '../store/services';
import { WebSocketManager } from '../api/endpoints/realtimeApi';
import type { WebSocketConfig, WebSocketMessage } from '../types/api';

interface UseWebSocketIntegrationOptions {
  autoConnect?: boolean;
  subscriptions?: {
    strategies?: string[];
    marketData?: {
      symbols: string[];
      types?: string[];
    };
    notifications?: boolean;
    riskAlerts?: boolean;
  };
  onMessage?: (message: WebSocketMessage) => void;
}

export const useWebSocketIntegration = (options: UseWebSocketIntegrationOptions = {}) => {
  const dispatch = useAppDispatch();
  const { token } = useAppSelector(state => state.auth);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subscribedChannels, setSubscribedChannels] = useState<Set<string>>(new Set());

  const managerRef = useRef<WebSocketManager | null>(null);
  const subscriptionsRef = useRef<Map<string, Function[]>>(new Map());

  const { data: status } = useGetWebSocketStatusQuery(undefined, {
    pollingInterval: 30000, // Poll every 30 seconds
    skip: !token,
  });

  const [initWebSocket] = useInitWebSocketMutation();
  const [subscribeToStrategy] = useSubscribeToStrategyMutation();
  const [subscribeToMarketData] = useSubscribeToMarketDataMutation();
  const [subscribeToNotifications] = useSubscribeToNotificationsMutation();

  // Initialize WebSocket manager
  useEffect(() => {
    if (!managerRef.current && token) {
      managerRef.current = new WebSocketManager(dispatch);

      // Set up event handlers
      const config: WebSocketConfig = {
        url: process.env.REACT_APP_WS_URL || 'ws://localhost:3003/ws',
        protocols: ['ws'],
        reconnectInterval: 3000,
        maxReconnectAttempts: 5,
        heartbeatInterval: 30000,
        onConnect: () => {
          setIsConnected(true);
          setError(null);
          console.log('WebSocket connected');
          handleReconnect();
        },
        onDisconnect: () => {
          setIsConnected(false);
          setSubscribedChannels(new Set());
          console.log('WebSocket disconnected');
        },
        onError: (err) => {
          setError('WebSocket connection error');
          console.error('WebSocket error:', err);
        },
        onMessage: (message: WebSocketMessage) => {
          setLastMessage(message);
          handleWebSocketMessage(message);
          options.onMessage?.(message);
        },
      };

      if (options.autoConnect !== false) {
        managerRef.current.connect(config);
      }
    }

    return () => {
      managerRef.current?.disconnect();
      managerRef.current = null;
    };
  }, [dispatch, token, options.autoConnect, options.onMessage]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    const { type, data, channel } = message;

    // Call channel-specific handlers
    if (channel && subscriptionsRef.current.has(channel)) {
      const handlers = subscriptionsRef.current.get(channel)!;
      handlers.forEach(handler => handler(data));
    }

    // Call type-specific handlers
    if (subscriptionsRef.current.has(type)) {
      const handlers = subscriptionsRef.current.get(type)!;
      handlers.forEach(handler => handler(data));
    }
  }, []);

  // Handle reconnection and resubscription
  const handleReconnect = useCallback(() => {
    if (options.subscriptions && isConnected) {
      // Resubscribe to all channels
      if (options.subscriptions.strategies) {
        options.subscriptions.strategies.forEach(strategyId => {
          subscribeToStrategy({ strategyId });
          setSubscribedChannels(prev => new Set(prev).add(`strategy:${strategyId}`));
        });
      }

      if (options.subscriptions.marketData) {
        subscribeToMarketData({
          symbols: options.subscriptions.marketData.symbols,
          types: options.subscriptions.marketData.types,
        });
        setSubscribedChannels(prev => new Set(prev).add('market-data'));
      }

      if (options.subscriptions.notifications) {
        subscribeToNotifications({});
        setSubscribedChannels(prev => new Set(prev).add('notifications'));
      }
    }
  }, [options.subscriptions, isConnected, subscribeToStrategy, subscribeToMarketData, subscribeToNotifications]);

  // Subscribe to message types/channels
  const subscribe = useCallback((channel: string, handler: Function) => {
    if (!subscriptionsRef.current.has(channel)) {
      subscriptionsRef.current.set(channel, []);
    }
    subscriptionsRef.current.get(channel)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = subscriptionsRef.current.get(channel);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }, []);

  // Send message
  const send = useCallback((message: any) => {
    managerRef.current?.send(message);
  }, []);

  // Manual connect/disconnect
  const connect = useCallback(() => {
    if (managerRef.current && !isConnected) {
      const config: WebSocketConfig = {
        url: process.env.REACT_APP_WS_URL || 'ws://localhost:3003/ws',
        protocols: ['ws'],
        reconnectInterval: 3000,
        maxReconnectAttempts: 5,
        heartbeatInterval: 30000,
        onConnect: () => {
          setIsConnected(true);
          setError(null);
          handleReconnect();
        },
        onDisconnect: () => {
          setIsConnected(false);
          setSubscribedChannels(new Set());
        },
        onError: (err) => {
          setError('WebSocket connection error');
        },
      };
      managerRef.current.connect(config);
    }
  }, [isConnected, handleReconnect]);

  const disconnect = useCallback(() => {
    managerRef.current?.disconnect();
    setSubscribedChannels(new Set());
  }, []);

  return {
    isConnected,
    lastMessage,
    error,
    status,
    subscribedChannels,
    subscribe,
    send,
    connect,
    disconnect,
  };
};

// Strategy-specific WebSocket integration hook
export const useStrategyWebSocketIntegration = (strategyId: string) => {
  const ws = useWebSocketIntegration({
    subscriptions: {
      strategies: [strategyId],
    },
  });

  const [executionUpdates, setExecutionUpdates] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any | null>(null);

  useEffect(() => {
    const unsubscribeExecution = ws.subscribe('execution_update', (data: any) => {
      if (data.strategyId === strategyId) {
        setExecutionUpdates(prev => [data, ...prev.slice(0, 99)]); // Keep last 100 updates

        // Update performance if included
        if (data.performance) {
          setPerformance(data.performance);
        }
      }
    });

    const unsubscribeSignal = ws.subscribe('signal', (data: any) => {
      if (data.strategyId === strategyId) {
        setSignals(prev => [data, ...prev.slice(0, 99)]); // Keep last 100 signals
      }
    });

    const unsubscribePerformance = ws.subscribe('performance_update', (data: any) => {
      if (data.strategyId === strategyId) {
        setPerformance(data);
      }
    });

    return () => {
      unsubscribeExecution();
      unsubscribeSignal();
      unsubscribePerformance();
    };
  }, [ws.subscribe, strategyId]);

  const clearHistory = useCallback(() => {
    setExecutionUpdates([]);
    setSignals([]);
  }, []);

  return {
    ...ws,
    executionUpdates,
    signals,
    performance,
    clearHistory,
  };
};

// Market data WebSocket integration hook
export const useMarketDataWebSocketIntegration = (symbols: string[], types?: string[]) => {
  const ws = useWebSocketIntegration({
    subscriptions: {
      marketData: { symbols, types },
    },
  });

  const [marketData, setMarketData] = useState<Map<string, any>>(new Map());
  const [marketStatus, setMarketStatus] = useState<any>(null);

  useEffect(() => {
    const unsubscribe = ws.subscribe('market_update', (data: any) => {
      if (symbols.includes(data.symbol)) {
        setMarketData(prev => {
          const newMap = new Map(prev);
          newMap.set(data.symbol, {
            ...newMap.get(data.symbol),
            ...data,
            lastUpdate: new Date().toISOString(),
          });
          return newMap;
        });
      }
    });

    const unsubscribeStatus = ws.subscribe('market_status', (data: any) => {
      setMarketStatus(data);
    });

    return () => {
      unsubscribe();
      unsubscribeStatus();
    };
  }, [ws.subscribe, symbols]);

  const getMarketData = useCallback((symbol: string) => {
    return marketData.get(symbol);
  }, [marketData]);

  const subscribeSymbol = useCallback((symbol: string) => {
    if (!symbols.includes(symbol)) {
      symbols.push(symbol);
      ws.send({
        type: 'subscribe',
        channel: 'market',
        data: { symbols: [symbol], types }
      });
    }
  }, [symbols, types, ws]);

  const unsubscribeSymbol = useCallback((symbol: string) => {
    const index = symbols.indexOf(symbol);
    if (index > -1) {
      symbols.splice(index, 1);
      ws.send({
        type: 'unsubscribe',
        channel: 'market',
        data: { symbols: [symbol] }
      });
      setMarketData(prev => {
        const newMap = new Map(prev);
        newMap.delete(symbol);
        return newMap;
      });
    }
  }, [symbols, ws]);

  return {
    ...ws,
    marketData,
    marketStatus,
    getMarketData,
    subscribeSymbol,
    unsubscribeSymbol,
  };
};

// Notifications WebSocket integration hook
export const useNotificationsWebSocketIntegration = () => {
  const ws = useWebSocketIntegration({
    subscriptions: {
      notifications: true,
    },
  });

  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const unsubscribe = ws.subscribe('notification', (data: any) => {
      setNotifications(prev => [data, ...prev.slice(0, 49)]); // Keep last 50 notifications
      if (!data.read) {
        setUnreadCount(prev => prev + 1);
      }
    });

    const unsubscribeCount = ws.subscribe('notification_count', (data: any) => {
      setUnreadCount(data.count);
    });

    return () => {
      unsubscribe();
      unsubscribeCount();
    };
  }, [ws.subscribe]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
    ws.send({
      type: 'mark_read',
      data: { notificationId: id }
    });
  }, [ws]);

  return {
    ...ws,
    notifications,
    unreadCount,
    clearNotifications,
    markAsRead,
  };
};