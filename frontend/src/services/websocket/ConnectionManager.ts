/**
 * WebSocket Connection Manager
 * Manages WebSocket connection lifecycle with automatic reconnection and state tracking
 */

import {
  ConnectionState,
  WebSocketConfig,
  ConnectionMetrics,
  WebSocketEventCallbacks,
  NetworkStatus,
  WebSocketError,
  WebSocketErrorType,
  MessageType,
  WSMessage
} from '../../types/websocket';

export class ConnectionManager {
  private ws: WebSocket | null = null;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private config: WebSocketConfig;
  private metrics: ConnectionMetrics;
  private eventListeners: Map<keyof WebSocketEventCallbacks, Set<Function>>;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private connectionTimer: NodeJS.Timeout | null = null;
  private pingStartTime: number = 0;
  private isManualDisconnect: boolean = false;
  private messageQueue: WSMessage[] = [];

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      connectionTimeout: 10000,
      enableLogging: true,
      bufferSize: 1000,
      throttleMessages: false,
      ...config
    };

    this.metrics = {
      reconnectCount: 0,
      messagesReceived: 0,
      messagesSent: 0,
      bytesReceived: 0,
      bytesSent: 0,
      errorCount: 0
    };

    this.eventListeners = new Map();
    Object.keys({} as WebSocketEventCallbacks).forEach(key => {
      this.eventListeners.set(key as keyof WebSocketEventCallbacks, new Set());
    });

    // Monitor network status
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleNetworkOnline);
      window.addEventListener('offline', this.handleNetworkOffline);
    }
  }

  /**
   * Establish WebSocket connection
   */
  async connect(): Promise<void> {
    if (this.state === ConnectionState.CONNECTING || this.state === ConnectionState.CONNECTED) {
      return;
    }

    this.setState(ConnectionState.CONNECTING);
    this.isManualDisconnect = false;

    try {
      // Clear any existing reconnect timer
      this.clearReconnectTimer();

      // Create new WebSocket connection
      const wsUrl = this.buildWebSocketUrl();
      this.ws = new WebSocket(wsUrl, this.config.protocols);

      // Set up connection timeout
      if (this.config.connectionTimeout) {
        this.connectionTimer = setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            this.handleError(new WebSocketError({
              type: WebSocketErrorType.TIMEOUT,
              message: 'Connection timeout',
              timestamp: Date.now()
            }));
          }
        }, this.config.connectionTimeout);
      }

      // Set up WebSocket event handlers
      this.ws.onopen = this.handleOpen;
      this.ws.onclose = this.handleClose;
      this.ws.onerror = this.handleErrorEvent;
      this.ws.onmessage = this.handleMessage;

      // Wait for connection to complete
      return new Promise((resolve, reject) => {
        const onConnect = () => {
          this.removeEventListener('onConnect', onConnect);
          this.removeEventListener('onError', onError);
          resolve();
        };
        const onError = (error: WebSocketError) => {
          this.removeEventListener('onConnect', onConnect);
          this.removeEventListener('onError', onError);
          reject(error);
        };
        this.addEventListener('onConnect', onConnect);
        this.addEventListener('onError', onError);
      });

    } catch (error) {
      this.handleError(new WebSocketError({
        type: WebSocketErrorType.CONNECTION_FAILED,
        message: error instanceof Error ? error.message : 'Connection failed',
        details: error,
        timestamp: Date.now()
      }));
      throw error;
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.isManualDisconnect = true;
    this.clearAllTimers();

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
    this.messageQueue = [];
  }

  /**
   * Send message through WebSocket
   */
  send(message: WSMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      // Queue message if not connected
      if (this.messageQueue.length < (this.config.bufferSize || 1000)) {
        this.messageQueue.push(message);
        this.log('Message queued:', message.type);
      } else {
        this.log('Message queue full, dropping message:', message.type);
      }
      return false;
    }

    try {
      const messageStr = JSON.stringify(message);
      this.ws.send(messageStr);

      // Update metrics
      this.metrics.messagesSent++;
      this.metrics.bytesSent += new Blob([messageStr]).size;

      return true;
    } catch (error) {
      this.handleError(new WebSocketError({
        type: WebSocketErrorType.MESSAGE_SEND_FAILED,
        message: error instanceof Error ? error.message : 'Failed to send message',
        details: error,
        timestamp: Date.now()
      }));
      return false;
    }
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Get connection metrics
   */
  getMetrics(): ConnectionMetrics {
    return { ...this.metrics };
  }

  /**
   * Get network status
   */
  getNetworkStatus(): NetworkStatus {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      return {
        online: navigator.onLine,
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData
      };
    }
    return {
      online: typeof navigator !== 'undefined' ? navigator.onLine : true
    };
  }

  /**
   * Get connection quality based on metrics
   */
  getConnectionQuality(): 'excellent' | 'good' | 'fair' | 'poor' {
    const latency = this.metrics.latency || 0;
    const reconnectRate = this.metrics.reconnectCount / Math.max(1, this.metrics.messagesReceived);

    if (latency < 50 && reconnectRate < 0.01) return 'excellent';
    if (latency < 150 && reconnectRate < 0.05) return 'good';
    if (latency < 300 && reconnectRate < 0.1) return 'fair';
    return 'poor';
  }

  /**
   * Add event listener
   */
  addEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.add(callback);
    }
  }

  /**
   * Remove event listener
   */
  removeEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen = () => {
    this.clearConnectionTimer();
    this.setState(ConnectionState.CONNECTED);

    // Update metrics
    this.metrics.connectedAt = Date.now();
    this.metrics.reconnectCount = 0;

    // Send authentication if token provided
    if (this.config.authToken) {
      this.send({
        id: this.generateMessageId(),
        type: MessageType.AUTH,
        data: {
          token: this.config.authToken,
          timestamp: Date.now()
        },
        timestamp: Date.now()
      });
    }

    // Flush queued messages
    this.flushMessageQueue();

    // Start heartbeat
    this.startHeartbeat();

    // Emit connect event
    this.emit('onConnect');
  };

  /**
   * Handle WebSocket close event
   */
  private handleClose = (event: CloseEvent) => {
    this.clearConnectionTimer();
    this.clearHeartbeatTimer();

    this.log('WebSocket closed:', event.code, event.reason);
    this.emit('onDisconnect', event.code, event.reason);

    // Attempt reconnection if not manual disconnect
    if (!this.isManualDisconnect && this.state !== ConnectionState.DISCONNECTED) {
      this.setState(ConnectionState.RECONNECTING);
      this.scheduleReconnect();
    } else {
      this.setState(ConnectionState.DISCONNECTED);
    }

    this.ws = null;
  };

  /**
   * Handle WebSocket error event
   */
  private handleErrorEvent = (event: Event) => {
    this.handleError(new WebSocketError({
      type: WebSocketErrorType.NETWORK_ERROR,
      message: 'WebSocket error occurred',
      details: event,
      timestamp: Date.now()
    }));
  };

  /**
   * Handle incoming message
   */
  private handleMessage = (event: MessageEvent) => {
    try {
      // Update metrics
      this.metrics.messagesReceived++;
      this.metrics.bytesReceived += new Blob([event.data]).size;

      const message: WSMessage = JSON.parse(event.data);

      // Handle special message types
      switch (message.type) {
        case MessageType.PONG:
          this.handlePongMessage();
          break;
        case MessageType.PING:
          this.handlePingMessage();
          break;
        default:
          this.emit('onMessage', message);
      }
    } catch (error) {
      this.handleError(new WebSocketError({
        type: WebSocketErrorType.PARSER_ERROR,
        message: error instanceof Error ? error.message : 'Failed to parse message',
        details: { data: event.data },
        timestamp: Date.now()
      }));
    }
  };

  /**
   * Handle ping message
   */
  private handlePingMessage(): void {
    // Respond with pong
    this.send({
      id: this.generateMessageId(),
      type: MessageType.PONG,
      timestamp: Date.now()
    });
  }

  /**
   * Handle pong message
   */
  private handlePongMessage(): void {
    if (this.pingStartTime > 0) {
      const latency = Date.now() - this.pingStartTime;
      this.metrics.latency = latency;
      this.metrics.lastPongTime = Date.now();
      this.pingStartTime = 0;

      this.emit('onLatencyUpdate', latency);
    }
  }

  /**
   * Handle errors
   */
  private handleError(error: WebSocketError): void {
    this.metrics.errorCount++;
    this.log('WebSocket error:', error.message);
    this.emit('onError', error);

    if (this.state !== ConnectionState.DISCONNECTED) {
      this.setState(ConnectionState.ERROR);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.metrics.reconnectCount >= (this.config.reconnectAttempts || 5)) {
      this.log('Max reconnection attempts reached');
      this.setState(ConnectionState.ERROR);
      return;
    }

    const delay = Math.min(
      (this.config.reconnectDelay || 1000) * Math.pow(2, this.metrics.reconnectCount),
      30000
    );

    this.log(`Scheduling reconnect in ${delay}ms (attempt ${this.metrics.reconnectCount + 1})`);
    this.emit('onReconnect', this.metrics.reconnectCount + 1);

    this.reconnectTimer = setTimeout(async () => {
      try {
        this.metrics.reconnectCount++;
        await this.connect();
      } catch (error) {
        this.scheduleReconnect();
      }
    }, delay);
  }

  /**
   * Start heartbeat
   */
  private startHeartbeat(): void {
    if (this.config.heartbeatInterval) {
      this.heartbeatTimer = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.pingStartTime = Date.now();
          this.metrics.lastPingTime = this.pingStartTime;

          this.send({
            id: this.generateMessageId(),
            type: MessageType.PING,
            timestamp: this.pingStartTime
          });
        }
      }, this.config.heartbeatInterval);
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  /**
   * Set connection state
   */
  private setState(newState: ConnectionState): void {
    const oldState = this.state;
    this.state = newState;
    this.log('State changed:', oldState, '->', newState);
    this.emit('onStateChange', oldState, newState);
  }

  /**
   * Emit event to listeners
   */
  private emit<K extends keyof WebSocketEventCallbacks>(
    event: K,
    ...args: any[]
  ): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error('Error in event listener:', error);
        }
      });
    }
  }

  /**
   * Clear all timers
   */
  private clearAllTimers(): void {
    this.clearReconnectTimer();
    this.clearHeartbeatTimer();
    this.clearConnectionTimer();
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Clear heartbeat timer
   */
  private clearHeartbeatTimer(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Clear connection timer
   */
  private clearConnectionTimer(): void {
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer);
      this.connectionTimer = null;
    }
  }

  /**
   * Handle network online event
   */
  private handleNetworkOnline = () => {
    if (this.state === ConnectionState.DISCONNECTED && !this.isManualDisconnect) {
      this.log('Network restored, attempting to reconnect...');
      this.connect().catch(error => {
        this.log('Failed to reconnect after network restore:', error);
      });
    }
  };

  /**
   * Handle network offline event
   */
  private handleNetworkOffline = () => {
    this.log('Network disconnected');
    this.setState(ConnectionState.DISCONNECTED);
  };

  /**
   * Build WebSocket URL with authentication
   */
  private buildWebSocketUrl(): string {
    const url = new URL(this.config.url);

    if (this.config.authToken) {
      url.searchParams.set('token', this.config.authToken);
    }

    return url.toString();
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Log message if logging enabled
   */
  private log(...args: any[]): void {
    if (this.config.enableLogging) {
      console.log('[ConnectionManager]', ...args);
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.disconnect();

    // Remove network event listeners
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleNetworkOnline);
      window.removeEventListener('offline', this.handleNetworkOffline);
    }

    // Clear all event listeners
    this.eventListeners.forEach(listeners => listeners.clear());
    this.eventListeners.clear();
  }
}