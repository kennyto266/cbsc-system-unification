/**
 * WebSocket Channel Hook
 * Provides easy subscription to WebSocket channels with state management
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChannelType } from '../types/websocket';
import { useWebSocket } from './useWebSocketEnhanced';

export interface UseWebSocketChannelOptions {
  autoSubscribe?: boolean;
  filters?: Record<string, any>;
  onMessage?: (data: any) => void;
  onError?: (error: any) => void;
  transform?: (data: any) => any;
  cacheKey?: string;
  cacheTTL?: number;
}

export interface UseWebSocketChannelReturn<T = any> {
  // Data
  data: T | null;
  lastMessage: any;
  history: any[];

  // State
  isLoading: boolean;
  isConnected: boolean;
  error: any;

  // Actions
  subscribe: () => void;
  unsubscribe: () => void;
  send: (data: any) => boolean;
  clearHistory: () => void;
  refresh: () => void;

  // Connection quality
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
}

export const useWebSocketChannel = <T = any>(
  channel: ChannelType,
  options: UseWebSocketChannelOptions = {}
): UseWebSocketChannelReturn<T> => {
  const {
    autoSubscribe = true,
    filters,
    onMessage,
    onError,
    transform,
    cacheKey,
    cacheTTL = 300000 // 5 minutes
  } = options;

  // State
  const [data, setData] = useState<T | null>(null);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  // Refs
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const wsServiceRef = useRef<any>(null);

  // Get WebSocket service
  const {
    isConnected,
    connectionQuality,
    subscribe: wsSubscribe,
    send: wsSend,
    getService
  } = useWebSocket({
    autoConnect: true,
    onError: (err) => {
      setError(err);
      onError?.(err);
    }
  });

  // Get service instance
  useEffect(() => {
    wsServiceRef.current = getService();
  }, [getService]);

  // Check cache on mount
  useEffect(() => {
    if (cacheKey && wsServiceRef.current) {
      const cacheManager = wsServiceRef.current.getCacheManager();
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        setData(cachedData);
        setIsLoading(false);
      }
    }
  }, [cacheKey]);

  // Subscribe to channel
  const subscribe = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
    }

    setIsLoading(true);
    setError(null);

    unsubscribeRef.current = wsSubscribe(channel, (messageData) => {
      try {
        // Transform data if transformer provided
        const transformedData = transform ? transform(messageData) : messageData;

        // Update state
        setData(transformedData);
        setLastMessage(messageData);
        setHistory(prev => [...prev.slice(-99), messageData]); // Keep last 100 messages
        setIsLoading(false);
        setError(null);

        // Cache the data
        if (cacheKey && wsServiceRef.current) {
          const cacheManager = wsServiceRef.current.getCacheManager();
          cacheManager.set(cacheKey, transformedData, cacheTTL);
        }

        // Call custom message handler
        onMessage?.(transformedData);
      } catch (err) {
        setError(err);
        setIsLoading(false);
        onError?.(err);
      }
    }, filters);
  }, [channel, filters, wsSubscribe, onMessage, onError, transform, cacheKey, cacheTTL]);

  // Unsubscribe from channel
  const unsubscribe = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
  }, []);

  // Send message to channel
  const send = useCallback((messageData: any) => {
    return wsSend({
      id: `channel_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'data' as any,
      channel,
      data: messageData,
      timestamp: Date.now()
    });
  }, [wsSend, channel]);

  // Clear message history
  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  // Refresh data (request current state)
  const refresh = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.send({
        id: `refresh_${Date.now()}`,
        type: 'request_state' as any,
        channel,
        timestamp: Date.now()
      });
    }
  }, [channel]);

  // Auto-subscribe on mount/connection
  useEffect(() => {
    if (autoSubscribe && isConnected) {
      subscribe();
    }

    return () => {
      unsubscribe();
    };
  }, [autoSubscribe, isConnected, subscribe, unsubscribe]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      unsubscribe();
    };
  }, [unsubscribe]);

  return {
    data,
    lastMessage,
    history,
    isLoading,
    isConnected,
    error,
    subscribe,
    unsubscribe,
    send,
    clearHistory,
    refresh,
    connectionQuality
  };
};

/**
 * Hook for subscribing to multiple channels
 */
export const useWebSocketChannels = (
  channels: Array<{
    channel: ChannelType;
    options?: UseWebSocketChannelOptions;
  }>
) => {
  const subscriptions = channels.map(({ channel, options }) => {
    return useWebSocketChannel(channel, options);
  });

  const isConnected = subscriptions.every(sub => sub.isConnected);
  const anyLoading = subscriptions.some(sub => sub.isLoading);
  const errors = subscriptions.filter(sub => sub.error).map(sub => sub.error);

  return {
    subscriptions,
    isConnected,
    isLoading: anyLoading,
    errors,
    subscribeAll: () => subscriptions.forEach(sub => sub.subscribe()),
    unsubscribeAll: () => subscriptions.forEach(sub => sub.unsubscribe()),
    clearAllHistory: () => subscriptions.forEach(sub => sub.clearHistory())
  };
};