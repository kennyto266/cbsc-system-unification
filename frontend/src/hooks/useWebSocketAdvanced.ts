/**
 * Advanced WebSocket Hook
 * Provides enhanced WebSocket functionality with connection management
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { throttle, debounce } from 'lodash';

import {
  IWebSocketService,
  ConnectionState,
  MessageType,
  BaseMessage,
  WebSocketConfig,
} from '@/types/socket';
import { createWebSocketService, getWebSocketService } from '@/services/socket';
import { createWebSocketManager, getWebSocketManager } from '@/services/websocket-manager';
import { RootState } from '@/store';
import {
  updateConnectionState,
  setConnectionMetrics,
  addRealtimeData,
  addConnectionError,
} from '@/store/slices/websocketSlice';

// Hook configuration
interface UseWebSocketAdvancedConfig {
  // Connection settings
  url?: string;
  token?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;

  // Performance settings
  enableThrottling?: boolean;
  throttleDelay?: number;
  enableBatching?: boolean;
  batchSize?: number;
  batchInterval?: number;

  // Feature flags
  enableCaching?: boolean;
  cacheSize?: number;
  enableRetry?: boolean;
  retryAttempts?: number;

  // Debug settings
  debug?: boolean;
  logLevel?: 'error' | 'warn' | 'info' | 'debug';
}

// Hook return value
interface UseWebSocketAdvancedReturn {
  // Connection management
  socket: IWebSocketService | null;
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  reconnect: () => Promise<void>;

  // Subscription management
  subscribe: <T = BaseMessage>(
    messageType: MessageType,
    callback: (message: T) => void,
    options?: SubscriptionOptions
  ) => string;
  unsubscribe: (subscriptionId: string) => void;
  unsubscribeAll: () => void;

  // Messaging
  send: <T = any>(type: MessageType, data: T) => boolean;
  broadcast: <T = any>(type: MessageType, data: T) => void;

  // Data access
  getMessageHistory: (type?: MessageType, limit?: number) => BaseMessage[];
  getCachedData: (key: string) => any;
  setCachedData: (key: string, data: any, ttl?: number) => void;

  // Metrics and status
  metrics: any;
  latency: number;
  messageRate: number;
  errorCount: number;

  // Utilities
  clearCache: () => void;
  reset: () => void;
}

// Subscription options
interface SubscriptionOptions {
  filter?: (message: BaseMessage) => boolean;
  transform?: (message: BaseMessage) => any;
  throttle?: number;
  debounce?: number;
  once?: boolean;
  cache?: boolean;
  cacheKey?: string;
}

// Cache entry
interface CacheEntry {
  data: any;
  timestamp: number;
  ttl?: number;
}

// Message batch
interface MessageBatch {
  messages: BaseMessage[];
  timestamp: number;
}

/**
 * Advanced WebSocket Hook with caching, batching, and performance optimizations
 */
export const useWebSocketAdvanced = (
  config: UseWebSocketAdvancedConfig = {}
): UseWebSocketAdvancedReturn => {
  const dispatch = useDispatch();
  const {
    connectionState: reduxConnectionState,
    metrics: reduxMetrics,
  } = useSelector((state: RootState) => state.websocket);

  // State
  const [socket, setSocket] = useState<IWebSocketService | null>(null);
  const [subscriptions, setSubscriptions] = useState<Map<string, {
    handler: Function;
    options: SubscriptionOptions;
    throttledHandler?: Function;
    debouncedHandler?: Function;
  } >>(new Map());
  const [cache, setCache] = useState<Map<string, CacheEntry>>(new Map());
  const [messageHistory, setMessageHistory] = useState<BaseMessage[]>([]);
  const [messageBatches, setMessageBatches] = useState<Map<string, MessageBatch>>(new Map()));
  const [metrics, setMetrics] = useState({
    latency: 0,
    messageRate: 0,
    errorCount: 0,
    lastMessageTime: 0,
  });

  // Refs
  const managerRef = useRef(getWebSocketManager());
  const messageCountRef = useRef(0);
  const messageRateTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Create service configuration
  const serviceConfig = useMemo<WebSocketConfig>(() => ({
    url: config.url || process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:3004',
    token: config.token || localStorage.getItem('auth_token') || undefined,
    reconnectAttempts: config.reconnectAttempts || 5,
    reconnectDelay: config.reconnectDelay || 1000,
    heartbeatInterval: config.heartbeatInterval || 30000,
    debug: config.debug || false,
  }), [config]);

  // Get or create WebSocket service
  const getOrCreateSocket = useCallback((): IWebSocketService => {
    let service = getWebSocketService();

    if (!service) {
      service = createWebSocketService(serviceConfig);
      setupServiceListeners(service);
    }

    return service;
  }, [serviceConfig]);

  // Setup service event listeners
  const setupServiceListeners = useCallback((service: IWebSocketService) => {
    // Connection events
    service.on('connect', () => {
      dispatch(updateConnectionState(ConnectionState.CONNECTED));
      setSocket(service);
    });

    service.on('disconnect', () => {
      dispatch(updateConnectionState(ConnectionState.DISCONNECTED));
    });

    service.on('error', (error: Error) => {
      dispatch(addConnectionError({
        message: error.message,
        code: error.name,
      }));
      setMetrics(prev => ({
        ...prev,
        errorCount: prev.errorCount + 1,
      }));
    });

    // Message handling
    service.on('message', (message: BaseMessage) => {
      handleIncomingMessage(message);
    });
  }, [dispatch]);

  // Handle incoming messages
  const handleIncomingMessage = useCallback((message: BaseMessage) => {
    // Update metrics
    messageCountRef.current++;
    const now = Date.now();
    setMetrics(prev => ({
      ...prev,
      lastMessageTime: now,
    }));

    // Add to history
    setMessageHistory(prev => {
      const newHistory = [...prev, message];
      // Keep only last 1000 messages
      if (newHistory.length > 1000) {
        return newHistory.slice(-1000);
      }
      return newHistory;
    });

    // Store in Redux
    dispatch(addRealtimeData({
      id: message.id,
      type: message.type,
      timestamp: message.timestamp,
      data: message.data,
    }));

    // Process subscriptions
    subscriptions.forEach((sub, id) => {
      if (message.type.toString() === sub.options.cacheKey || !sub.options.cacheKey) {
        // Apply filter if present
        if (sub.options.filter && !sub.options.filter(message)) {
          return;
        }

        // Transform message if transformer is provided
        const transformedMessage = sub.options.transform
          ? sub.options.transform(message)
          : message;

        // Handle throttling
        if (sub.options.throttle && sub.throttledHandler) {
          sub.throttledHandler(transformedMessage);
        }
        // Handle debouncing
        else if (sub.options.debounce && sub.debouncedHandler) {
          sub.debouncedHandler(transformedMessage);
        }
        // Direct call
        else {
          sub.handler(transformedMessage);
        }

        // Cache message if requested
        if (sub.options.cache && sub.options.cacheKey) {
          setCache(prev => {
            const newCache = new Map(prev);
            newCache.set(sub.options.cacheKey!, {
              data: transformedMessage,
              timestamp: now,
            });
            return newCache;
          });
        }

        // Remove subscription if it's a one-time handler
        if (sub.options.once) {
          subscriptions.delete(id);
          setSubscriptions(new Map(subscriptions));
        }
      }
    });
  }, [subscriptions, dispatch]);

  // Calculate message rate
  useEffect(() => {
    messageRateTimerRef.current = setInterval(() => {
      const rate = messageCountRef.current;
      messageCountRef.current = 0;
      setMetrics(prev => ({
        ...prev,
        messageRate: rate,
      }));
    }, 1000);

    return () => {
      if (messageRateTimerRef.current) {
        clearInterval(messageRateTimerRef.current);
      }
    };
  }, []);

  // Connect to WebSocket
  const connect = useCallback(async (): Promise<void> => {
    try {
      const service = getOrCreateSocket();
      await service.connect();
    } catch (error) {
      console.error('Failed to connect:', error);
      throw error;
    }
  }, [getOrCreateSocket]);

  // Disconnect from WebSocket
  const disconnect = useCallback((): void => {
    const service = getWebSocketService();
    if (service) {
      service.disconnect();
      setSocket(null);
    }
  }, []);

  // Reconnect to WebSocket
  const reconnect = useCallback(async (): Promise<void> => {
    const service = getWebSocketService();
    if (service) {
      await service.reconnect();
    }
  }, []);

  // Subscribe to message type
  const subscribe = useCallback(<T = BaseMessage>(
    messageType: MessageType,
    callback: (message: T) => void,
    options: SubscriptionOptions = {}
  ): string => {
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    let throttledHandler: Function | undefined;
    let debouncedHandler: Function | undefined;

    // Create throttled handler if needed
    if (options.throttle) {
      throttledHandler = throttle(callback, options.throttle);
    }

    // Create debounced handler if needed
    if (options.debounce) {
      debouncedHandler = debounce(callback, options.debounce);
    }

    const subscription = {
      handler: callback,
      options: {
        ...options,
        cacheKey: options.cacheKey || messageType.toString(),
      },
      throttledHandler,
      debouncedHandler,
    };

    setSubscriptions(prev => new Map(prev).set(subscriptionId, subscription));

    // Subscribe to socket if connected
    const service = getWebSocketService();
    if (service) {
      service.subscribe(messageType.toString(), (message: BaseMessage) => {
        handleIncomingMessage(message);
      });
    }

    return subscriptionId;
  }, [handleIncomingMessage]);

  // Unsubscribe from message type
  const unsubscribe = useCallback((subscriptionId: string): void => {
    setSubscriptions(prev => {
      const newSubs = new Map(prev);
      newSubs.delete(subscriptionId);
      return newSubs;
    });
  }, []);

  // Unsubscribe from all
  const unsubscribeAll = useCallback((): void => {
    setSubscriptions(new Map());
  }, []);

  // Send message
  const send = useCallback(<T = any>(type: MessageType, data: T): boolean => {
    const service = getWebSocketService();
    if (service && service.isConnected()) {
      service.send(type, data);
      return true;
    }
    return false;
  }, []);

  // Broadcast message
  const broadcast = useCallback(<T = any>(type: MessageType, data: T): void => {
    const manager = getWebSocketManager();
    if (manager) {
      manager.broadcast(type, data);
    } else {
      // Fallback to single connection
      send(type, data);
    }
  }, [send]);

  // Get message history
  const getMessageHistory = useCallback((
    type?: MessageType,
    limit?: number
  ): BaseMessage[] => {
    let history = messageHistory;

    // Filter by type if specified
    if (type) {
      history = history.filter(msg => msg.type === type);
    }

    // Apply limit if specified
    if (limit && limit > 0) {
      history = history.slice(-limit);
    }

    return history;
  }, [messageHistory]);

  // Get cached data
  const getCachedData = useCallback((key: string): any => {
    const entry = cache.get(key);
    if (!entry) {
      return null;
    }

    // Check TTL
    if (entry.ttl && Date.now() - entry.timestamp > entry.ttl) {
      setCache(prev => {
        const newCache = new Map(prev);
        newCache.delete(key);
        return newCache;
      });
      return null;
    }

    return entry.data;
  }, [cache]);

  // Set cached data
  const setCachedData = useCallback((
    key: string,
    data: any,
    ttl?: number
  ): void => {
    setCache(prev => {
      const newCache = new Map(prev);
      newCache.set(key, {
        data,
        timestamp: Date.now(),
        ttl,
      });

      // Limit cache size
      if (newCache.size > (config.cacheSize || 100)) {
        // Remove oldest entries
        const entries = Array.from(newCache.entries())
          .sort((a, b) => a[1].timestamp - b[1].timestamp);
        const toRemove = entries.slice(0, newCache.size - (config.cacheSize || 100));
        toRemove.forEach(([k]) => newCache.delete(k));
      }

      return newCache;
    });
  }, [config.cacheSize]);

  // Clear cache
  const clearCache = useCallback((): void => {
    setCache(new Map());
  }, []);

  // Reset hook state
  const reset = useCallback((): void => {
    unsubscribeAll();
    clearCache();
    setMessageHistory([]);
    setMetrics({
      latency: 0,
      messageRate: 0,
      errorCount: 0,
      lastMessageTime: 0,
    });
  }, [unsubscribeAll, clearCache]);

  // Auto-connect if enabled
  useEffect(() => {
    if (config.autoConnect !== false) {
      connect().catch(err => {
        console.error('Auto-connect failed:', err);
      });
    }
  }, [config.autoConnect, connect]);

  // Update metrics from Redux
  useEffect(() => {
    setMetrics(prev => ({
      ...prev,
      latency: reduxMetrics.averageLatency || 0,
      errorCount: reduxMetrics.errors?.length || 0,
    }));
  }, [reduxMetrics]);

  return {
    socket,
    connectionState: reduxConnectionState,
    isConnected: reduxConnectionState === ConnectionState.CONNECTED,
    isReconnecting: reduxConnectionState === ConnectionState.RECONNECTING,
    connect,
    disconnect,
    reconnect,
    subscribe,
    unsubscribe,
    unsubscribeAll,
    send,
    broadcast,
    getMessageHistory,
    getCachedData,
    setCachedData,
    metrics,
    latency: metrics.latency,
    messageRate: metrics.messageRate,
    errorCount: metrics.errorCount,
    clearCache,
    reset,
  };
};

export default useWebSocketAdvanced;