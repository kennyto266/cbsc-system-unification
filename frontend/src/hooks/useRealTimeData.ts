/**
 * Custom hook for Real-Time data subscriptions
 * Manages WebSocket connections and data streams
 */

import { useEffect, useCallback, useRef } from 'react';
import { wsManager, WSMessage } from '../services/websocketManager';

// Real-time price data interface
interface RealTimePrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: number;
}

// Real-time notification interface
interface RealTimeNotification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: number;
  data?: any;
}

// Hook result interface
interface UseRealTimeDataResult {
  // Real-time data
  realTimePrices: Record<string, RealTimePrice>;
  notifications: RealTimeNotification[];

  // Actions
  subscribeToPrices: (callback: (data: RealTimePrice) => void) => () => void;
  subscribeToNotifications: (callback: (data: RealTimeNotification) => void) => () => void;
  subscribeToSignals: (callback: (data: any) => void) => () => void;
  subscribeToStrategies: (callback: (data: any) => void) => () => void;

  // Connection status
  isConnected: boolean;
}

/**
 * Hook for managing real-time data subscriptions
 */
export const useRealTimeData = (): UseRealTimeDataResult => {
  const pricesRef = useRef<Record<string, RealTimePrice>>({});
  const notificationsRef = useRef<RealTimeNotification[]>([]);
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());

  /**
   * Subscribe to price updates
   */
  const subscribeToPrices = useCallback((callback: (data: RealTimePrice) => void) => {
    const key = 'price_update';

    if (!subscribersRef.current.has(key)) {
      subscribersRef.current.set(key, new Set());
    }

    subscribersRef.current.get(key)!.add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = subscribersRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          subscribersRef.current.delete(key);
        }
      }
    };
  }, []);

  /**
   * Subscribe to notifications
   */
  const subscribeToNotifications = useCallback((callback: (data: RealTimeNotification) => void) => {
    const key = 'notification';

    if (!subscribersRef.current.has(key)) {
      subscribersRef.current.set(key, new Set());
    }

    subscribersRef.current.get(key)!.add(callback);

    return () => {
      const callbacks = subscribersRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          subscribersRef.current.delete(key);
        }
      }
    };
  }, []);

  /**
   * Subscribe to trading signals
   */
  const subscribeToSignals = useCallback((callback: (data: any) => void) => {
    const key = 'trading_signal';

    if (!subscribersRef.current.has(key)) {
      subscribersRef.current.set(key, new Set());
    }

    subscribersRef.current.get(key)!.add(callback);

    return () => {
      const callbacks = subscribersRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          subscribersRef.current.delete(key);
        }
      }
    };
  }, []);

  /**
   * Subscribe to strategy updates
   */
  const subscribeToStrategies = useCallback((callback: (data: any) => void) => {
    const key = 'strategy_update';

    if (!subscribersRef.current.has(key)) {
      subscribersRef.current.set(key, new Set());
    }

    subscribersRef.current.get(key)!.add(callback);

    return () => {
      const callbacks = subscribersRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          subscribersRef.current.delete(key);
        }
      }
    };
  }, []);

  /**
   * Handle WebSocket messages
   */
  const handleWSMessage = useCallback((message: WSMessage) => {
    const { type, data } = message;

    // Update local state
    switch (type) {
      case 'price_update':
        pricesRef.current[data.symbol] = {
          ...data,
          timestamp: message.timestamp,
        };
        break;

      case 'notification':
        const notification: RealTimeNotification = {
          id: `notif-${Date.now()}-${Math.random()}`,
          type: data.type || 'info',
          message: data.message,
          timestamp: message.timestamp,
          data: data.data,
        };
        notificationsRef.current.unshift(notification);

        // Keep only last 50 notifications
        if (notificationsRef.current.length > 50) {
          notificationsRef.current = notificationsRef.current.slice(0, 50);
        }
        break;
    }

    // Notify subscribers
    const callbacks = subscribersRef.current.get(type);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const initWebSocket = async () => {
      try {
        await wsManager.connect();

        // Subscribe to all message types
        unsubscribe = wsManager.subscribe('*', handleWSMessage);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
      }
    };

    initWebSocket();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [handleWSMessage]);

  return {
    // Real-time data
    realTimePrices: pricesRef.current,
    notifications: notificationsRef.current,

    // Actions
    subscribeToPrices,
    subscribeToNotifications,
    subscribeToSignals,
    subscribeToStrategies,

    // Connection status
    isConnected: wsManager.isConnected(),
  };
};

export default useRealTimeData;
