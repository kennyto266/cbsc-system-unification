/**
 * WebSocket Context Provider
 * Provides WebSocket service to all child components
 */

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import {
  WebSocketService,
  getWebSocketService,
  WebSocketConfig,
  ConnectionState,
  ChannelType,
  WSMessage
} from '../services/websocket/WebSocketService';

interface WebSocketContextValue {
  // Service
  service: WebSocketService;

  // Connection state
  isConnected: boolean;
  connectionState: ConnectionState;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';

  // Methods
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (message: WSMessage) => boolean;
  subscribe: (channel: ChannelType, callback: (data: any) => void, filters?: Record<string, any>) => () => void;

  // Statistics
  getStats: () => any;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
  config?: WebSocketConfig;
  autoConnect?: boolean;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  config,
  autoConnect = true
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good');

  // Use ref to prevent re-creating service
  const serviceRef = useRef<WebSocketService>();

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
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      setConnectionState(ConnectionState.DISCONNECTED);
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
    service.addEventListener('onStateChange', handleStateChange);
    service.addEventListener('onLatencyUpdate', handleQualityChange);

    // Auto connect if enabled
    if (autoConnect && connectionState === ConnectionState.DISCONNECTED) {
      service.connect().catch(err => {
        console.error('Auto-connect failed:', err);
      });
    }

    // Cleanup
    return () => {
      service.removeEventListener('onConnect', handleConnect);
      service.removeEventListener('onDisconnect', handleDisconnect);
      service.removeEventListener('onStateChange', handleStateChange);
      service.removeEventListener('onLatencyUpdate', handleQualityChange);
    };
  }, [service, autoConnect, connectionState]);

  // Context value
  const value: WebSocketContextValue = {
    service,
    isConnected,
    connectionState,
    connectionQuality,
    connect: () => service.connect(),
    disconnect: () => service.disconnect(),
    send: (message) => service.send(message),
    subscribe: (channel, callback, filters) => service.subscribe(channel, callback, filters),
    getStats: () => service.getStats()
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

/**
 * Hook to use WebSocket context
 */
export const useWebSocketContext = (): WebSocketContextValue => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

/**
 * HOC to provide WebSocket context to component
 */
export const withWebSocket = <P extends object>(
  Component: React.ComponentType<P>
) => {
  return React.forwardRef<any, P>((props, ref) => (
    <WebSocketProvider>
      <Component {...props} ref={ref} />
    </WebSocketProvider>
  ));
};

export default WebSocketContext;