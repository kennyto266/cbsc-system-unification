import { useState, useEffect, useRef } from 'react';

interface WebSocketMessage {
  type: 'government_data' | 'market_regime' | 'strategy_update';
  data: any;
  timestamp: string;
}

export function useWebSocket(url: string, options?: {
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const connect = () => {
    try {
      const ws = new WebSocket(url);
      setSocket(ws);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        options?.onOpen?.();
      };

      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(message);
        options?.onMessage?.(message);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setSocket(null);
        options?.onClose?.();

        // 嘗試重連
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
            connect();
          }, 1000 * Math.pow(2, reconnectAttempts.current)); // 指數退避
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        options?.onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (socket) {
        socket.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [url]);

  const sendMessage = (message: Omit<WebSocketMessage, 'timestamp'>) => {
    if (socket && isConnected) {
      const messageWithTimestamp = {
        ...message,
        timestamp: new Date().toISOString()
      };
      socket.send(JSON.stringify(messageWithTimestamp));
    }
  };

  return {
    socket,
    isConnected,
    lastMessage,
    sendMessage,
    connect
  };
}

export function useGovernmentWebSocket() {
  return useWebSocket('ws://localhost:3004/ws/government');
}

export function useMarketRegimeWebSocket() {
  return useWebSocket('ws://localhost:3004/ws/market-regime');
}