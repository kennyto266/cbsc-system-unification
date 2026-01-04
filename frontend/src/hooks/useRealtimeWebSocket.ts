/**
 * Phase 8.1 WebSocket實時推送系統 - React WebSocket Hook
 * React WebSocket Hook for Real-time Push System
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setUserNotification } from '../store/slices/notificationsSlice';

// Types
export interface WebSocketMessage {
  stream_type: string;
  message_type: string;
  data: any;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SubscriptionOptions {
  filters?: Record<string, any>;
  frequencyLimit?: number;
  onError?: (error: Error) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
  subscriptions: Set<string>;
}

// WebSocket connection class
class WebSocketConnection {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private subscriptions: Set<string> = new Set();
  private messageHandlers: Map<string, (msg: any) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isManualClose = false;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.isManualClose = false;
        const wsUrl = `${this.url}?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected', event.code, event.reason);
          this.ws = null;

          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect().catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscriptions.clear();
    this.messageHandlers.clear();
  }

  private handleMessage(message: WebSocketMessage) {
    // Handle system messages
    if (message.stream_type === 'system') {
      switch (message.message_type) {
        case 'connection_established':
          console.log('Connection established:', message.data);
          break;
        case 'authentication_success':
          console.log('Authentication successful:', message.data);
          break;
        case 'error':
          console.error('WebSocket error:', message.data);
          break;
        case 'pong':
          // Heartbeat response
          break;
      }
    }

    // Call specific message handlers
    const handler = this.messageHandlers.get(message.stream_type);
    if (handler) {
      handler(message);
    }

    // Handle subscriptions confirmations
    if (message.message_type === 'subscription_confirmed') {
      this.subscriptions.add(message.data.stream);
      console.log(`Subscribed to ${message.data.stream}`);
    } else if (message.message_type === 'unsubscription_confirmed') {
      this.subscriptions.delete(message.data.stream);
      console.log(`Unsubscribed from ${message.data.stream}`);
    }
  }

  subscribe(streamType: string, options: SubscriptionOptions = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    // Store message handler
    if (options.onMessage) {
      this.messageHandlers.set(streamType, options.onMessage);
    }

    // Send subscription request
    const request = {
      type: 'subscribe',
      stream_type: streamType,
      filters: options.filters || {},
      frequency_limit: options.frequencyLimit
    };

    this.ws.send(JSON.stringify(request));
  }

  unsubscribe(streamType: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    // Remove message handler
    this.messageHandlers.delete(streamType);

    // Send unsubscribe request
    const request = {
      type: 'unsubscribe',
      stream_type: streamType
    };

    this.ws.send(JSON.stringify(request));
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }
}

// Hook factory
export function createWebSocketHook(wsUrl: string) {
  const connections = new Map<string, WebSocketConnection>();

  return function useWebSocket(options: SubscriptionOptions = {}) {
    const [state, setState] = useState<WebSocketState>({
      isConnected: false,
      isConnecting: false,
      error: null,
      lastMessage: null,
      subscriptions: new Set()
    });

    const connectionRef = useRef<WebSocketConnection | null>(null);
    const dispatch = useDispatch();

    // Get auth token from Redux
    const token = useSelector((state: RootState) => state.auth.token);
    const userId = useSelector((state: RootState) => state.auth.user?.id);

    // Connect to WebSocket
    const connect = useCallback(async () => {
      if (!token) {
        setState(prev => ({
          ...prev,
          error: 'No authentication token available'
        }));
        return;
      }

      setState(prev => ({
        ...prev,
        isConnecting: true,
        error: null
      }));

      try {
        // Get or create connection
        let connection = connections.get(userId || 'default');
        if (!connection) {
          connection = new WebSocketConnection(wsUrl, token);
          connections.set(userId || 'default', connection);
        }

        // Set up message handler for notifications
        const handleNotification = (message: WebSocketMessage) => {
          if (message.stream_type === 'system_notifications' ||
              message.stream_type === 'user_alerts') {
            dispatch(setUserNotification({
              id: message.data.notification_id,
              type: message.data.type,
              title: message.data.title,
              message: message.data.message,
              timestamp: message.timestamp,
              actionRequired: message.data.action_required,
              actionUrl: message.data.action_url
            }));
          }
        };

        // Connect
        await connection.connect();
        connectionRef.current = connection;

        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          subscriptions: new Set(connection.getSubscriptions())
        }));

        // Set up default notification handler
        connection.subscribe('system_notifications', {
          onMessage: handleNotification
        });

      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error: error instanceof Error ? error.message : 'Connection failed'
        }));

        if (options.onError) {
          options.onError(error instanceof Error ? error : new Error('Connection failed'));
        }
      }
    }, [token, userId, dispatch, options.onError]);

    // Disconnect
    const disconnect = useCallback(() => {
      if (connectionRef.current) {
        connectionRef.current.disconnect();
        connectionRef.current = null;
      }

      setState(prev => ({
        ...prev,
        isConnected: false,
        subscriptions: new Set()
      }));
    }, []);

    // Subscribe to stream
    const subscribe = useCallback((streamType: string, opts: SubscriptionOptions = {}) => {
      if (!connectionRef.current) {
        console.warn('Cannot subscribe: WebSocket not connected');
        return;
      }

      try {
        connectionRef.current.subscribe(streamType, {
          ...opts,
          onMessage: (message) => {
            setState(prev => ({
              ...prev,
              lastMessage: message
            }));

            if (opts.onMessage) {
              opts.onMessage(message);
            }
          }
        });

        setState(prev => ({
          ...prev,
          subscriptions: new Set(prev.subscriptions).add(streamType)
        }));

      } catch (error) {
        console.error('Failed to subscribe:', error);
      }
    }, []);

    // Unsubscribe from stream
    const unsubscribe = useCallback((streamType: string) => {
      if (!connectionRef.current) {
        return;
      }

      connectionRef.current.unsubscribe(streamType);

      setState(prev => {
        const newSubs = new Set(prev.subscriptions);
        newSubs.delete(streamType);
        return {
          ...prev,
          subscriptions: newSubs
        };
      });
    }, []);

    // Send ping
    const ping = useCallback(() => {
      if (connectionRef.current) {
        connectionRef.current.sendPing();
      }
    }, []);

    // Auto-connect and cleanup
    useEffect(() => {
      if (token) {
        connect();
      }

      return () => {
        disconnect();
      };
    }, [token, connect, disconnect]);

    // Heartbeat
    useEffect(() => {
      if (!state.isConnected) return;

      const interval = setInterval(() => {
        ping();
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(interval);
    }, [state.isConnected, ping]);

    return {
      ...state,
      connect,
      disconnect,
      subscribe,
      unsubscribe,
      ping,
      connection: connectionRef.current
    };
  };
}

// Create hook with default URL
export const useRealtimeWebSocket = createWebSocketHook(
  import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws'
);

// Specialized hooks
export function useStrategyExecution() {
  const { subscribe, unsubscribe, lastMessage, ...rest } = useRealtimeWebSocket();

  const subscribeToStrategy = useCallback((strategyId: string, options?: SubscriptionOptions) => {
    subscribe('strategy_execution', {
      filters: { strategy_id: strategyId },
      ...options
    });
  }, [subscribe]);

  const unsubscribeFromStrategy = useCallback(() => {
    unsubscribe('strategy_execution');
  }, [unsubscribe]);

  return {
    ...rest,
    lastMessage,
    subscribeToStrategy,
    unsubscribeFromStrategy
  };
}

export function useRiskMonitoring() {
  const { subscribe, unsubscribe, lastMessage, ...rest } = useRealtimeWebSocket();

  const subscribeToRisk = useCallback((portfolioId?: string, options?: SubscriptionOptions) => {
    subscribe('risk_monitoring', {
      filters: portfolioId ? { portfolio_id: portfolioId } : {},
      ...options
    });
  }, [subscribe]);

  const unsubscribeFromRisk = useCallback(() => {
    unsubscribe('risk_monitoring');
  }, [unsubscribe]);

  return {
    ...rest,
    lastMessage,
    subscribeToRisk,
    unsubscribeFromRisk
  };
}

export function usePerformanceMetrics() {
  const { subscribe, unsubscribe, lastMessage, ...rest } = useRealtimeWebSocket();

  const subscribeToPerformance = useCallback((strategyId?: string, options?: SubscriptionOptions) => {
    subscribe('performance_metrics', {
      filters: strategyId ? { strategy_id: strategyId } : {},
      ...options
    });
  }, [subscribe]);

  const unsubscribeFromPerformance = useCallback(() => {
    unsubscribe('performance_metrics');
  }, [unsubscribe]);

  return {
    ...rest,
    lastMessage,
    subscribeToPerformance,
    unsubscribeFromPerformance
  };
}

export function useMarketData() {
  const { subscribe, unsubscribe, lastMessage, ...rest } = useRealtimeWebSocket();

  const subscribeToSymbols = useCallback((symbols: string[], options?: SubscriptionOptions) => {
    subscribe('market_data', {
      filters: { symbols },
      ...options
    });
  }, [subscribe]);

  const unsubscribeFromMarketData = useCallback(() => {
    unsubscribe('market_data');
  }, [unsubscribe]);

  return {
    ...rest,
    lastMessage,
    subscribeToSymbols,
    unsubscribeFromMarketData
  };
}

export function useSystemNotifications() {
  const { subscribe, unsubscribe, lastMessage, ...rest } = useRealtimeWebSocket();

  // System notifications are subscribed by default in useWebSocket
  return {
    ...rest,
    lastMessage: lastMessage?.stream_type === 'system_notifications' ? lastMessage : null,
    subscribeToNotifications: () => {}, // Already subscribed
    unsubscribeFromNotifications: () => unsubscribe('system_notifications')
  };
}