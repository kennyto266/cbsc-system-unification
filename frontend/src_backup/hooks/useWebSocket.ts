import { useState, useEffect, useRef, useCallback } from 'react';

interface UseWebSocketOptions {
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (event: MessageEvent) => void;
}

interface UseWebSocketReturn {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: MessageEvent | null;
  sendMessage: (message: string | object) => void;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    reconnectAttempts = 3,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    onConnect,
    onDisconnect,
    onError,
    onMessage
  } = options;

  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const manualDisconnectRef = useRef(false);

  const isConnected = connectionStatus === 'connected';

  const clearHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const clearReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    clearHeartbeat();

    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // Send heartbeat message
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        startHeartbeat(); // Schedule next heartbeat
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, clearHeartbeat]);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    manualDisconnectRef.current = false;
    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('connected');
        reconnectCountRef.current = 0;
        startHeartbeat();
        onConnect?.();
      };

      ws.onclose = (event) => {
        setConnectionStatus('disconnected');
        clearHeartbeat();
        onDisconnect?.();

        // Only attempt to reconnect if it wasn't a manual disconnect
        if (!manualDisconnectRef.current && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setConnectionStatus('error');
        onError?.(error);
      };

      ws.onmessage = (event) => {
        setLastMessage(event);
        onMessage?.(event);

        // Reset heartbeat on any message
        startHeartbeat();
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [url, reconnectAttempts, reconnectInterval, startHeartbeat, clearHeartbeat, onConnect, onDisconnect, onError, onMessage]);

  const disconnect = useCallback(() => {
    manualDisconnectRef.current = true;
    clearReconnect();
    clearHeartbeat();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
  }, [clearReconnect, clearHeartbeat]);

  const sendMessage = useCallback((message: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
    } else {
      console.warn('Cannot send message, WebSocket is not connected');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, pause operations
        clearHeartbeat();
      } else {
        // Page is visible, resume operations
        if (isConnected) {
          startHeartbeat();
        } else if (connectionStatus === 'disconnected') {
          // Try to reconnect when page becomes visible
          connect();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connectionStatus, isConnected, connect, startHeartbeat, clearHeartbeat]);

  return {
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    isConnected
  };
};