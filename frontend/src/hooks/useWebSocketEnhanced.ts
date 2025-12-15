/**
 * Enhanced WebSocket Hook
 * Provides advanced WebSocket functionality to React components
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  ConnectionState,
  ChannelType,
  WSMessage,
  WebSocketService,
  getWebSocketService,
  WebSocketConfig,
  MessageType
} from '../services/websocket/WebSocketService';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
  onMessage?: (message: WSMessage) => void;
}

export interface UseWebSocketReturn {
  // Connection
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (message: WSMessage) => boolean;

  // State
  isConnected: boolean;
  connectionState: ConnectionState;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
  error: any;

  // Subscriptions
  subscribe: (channel: ChannelType, callback: (data: any) => void, filters?: Record<string, any>) => () => void;

  // Service
  getService: () => WebSocketService;
}

export const useWebSocket = (
  config?: WebSocketConfig,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');
  const [error, setError] = useState<any>(null);

  // Use ref to maintain service instance across re-renders
  const serviceRef = useRef<WebSocketService | null>(null);
  const subscriptionsRef = useRef<Map<ChannelType, Set<() => void>>>(new Map());

  // Initialize service
  if (!serviceRef.current) {
    serviceRef.current = getWebSocketService(config);
  }

  const service = serviceRef.current;

  // Setup event listeners
  useEffect(() => {
    const handleConnect = () => {
      setIsConnected(true);
      setConnectionState(ConnectionState.CONNECTED);
      setError(null);
      options.onConnect?.();
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      setConnectionState(ConnectionState.DISCONNECTED);
      options.onDisconnect?.();
    };

    const handleError = (err: any) => {
      setError(err);
      setConnectionState(ConnectionState.ERROR);
      options.onError?.(err);
    };

    const handleStateChange = (oldState: ConnectionState, newState: ConnectionState) => {
      setConnectionState(newState);
      setIsConnected(newState === ConnectionState.CONNECTED);
    };

    const handleQualityChange = () => {
      setConnectionQuality(service.getConnectionQuality());
    };

    // Add listeners
    service.addEventListener('onConnect', handleConnect);
    service.addEventListener('onDisconnect', handleDisconnect);
    service.addEventListener('onError', handleError);
    service.addEventListener('onStateChange', handleStateChange);
    service.addEventListener('onLatencyUpdate', handleQualityChange);

    // Auto connect if enabled
    if (options.autoConnect !== false && connectionState === ConnectionState.DISCONNECTED) {
      service.connect().catch(err => {
        console.error('Auto-connect failed:', err);
      });
    }

    // Cleanup
    return () => {
      service.removeEventListener('onConnect', handleConnect);
      service.removeEventListener('onDisconnect', handleDisconnect);
      service.removeEventListener('onError', handleError);
      service.removeEventListener('onStateChange', handleStateChange);
      service.removeEventListener('onLatencyUpdate', handleQualityChange);
    };
  }, [service, options]);

  // Connect function
  const connect = useCallback(async () => {
    try {
      await service.connect();
    } catch (err) {
      setError(err);
      throw err;
    }
  }, [service]);

  // Disconnect function
  const disconnect = useCallback(() => {
    service.disconnect();
  }, [service]);

  // Send message function
  const send = useCallback((message: WSMessage) => {
    return service.send(message);
  }, [service]);

  // Subscribe function with automatic cleanup
  const subscribe = useCallback((
    channel: ChannelType,
    callback: (data: any) => void,
    filters?: Record<string, any>
  ) => {
    const unsubscribe = service.subscribe(channel, callback, filters);

    // Track subscription for cleanup
    if (!subscriptionsRef.current.has(channel)) {
      subscriptionsRef.current.set(channel, new Set());
    }
    subscriptionsRef.current.get(channel)!.add(unsubscribe);

    // Return enhanced unsubscribe that also removes from tracking
    return () => {
      unsubscribe();
      const channelSubs = subscriptionsRef.current.get(channel);
      if (channelSubs) {
        channelSubs.delete(unsubscribe);
        if (channelSubs.size === 0) {
          subscriptionsRef.current.delete(channel);
        }
      }
    };
  }, [service]);

  // Get service function
  const getService = useCallback(() => {
    return service;
  }, [service]);

  // Cleanup subscriptions on unmount
  useEffect(() => {
    return () => {
      subscriptionsRef.current.forEach(unsubs => {
        unsubs.forEach(unsub => unsub());
      });
      subscriptionsRef.current.clear();
    };
  }, []);

  return {
    connect,
    disconnect,
    send,
    isConnected,
    connectionState,
    connectionQuality,
    error,
    subscribe,
    getService
  };
};