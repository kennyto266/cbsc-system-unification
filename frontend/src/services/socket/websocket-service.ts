/**
 * WebSocket Service Implementation
 * Provides real-time communication with automatic reconnection and error handling
 */

import { io, Socket } from 'socket.io-client';
import { v4 as uuidv4 } from 'uuid';

import {
  IWebSocketService,
  WebSocketConfig,
  ConnectionState,
  MessageType,
  BaseMessage,
  SubscriptionConfig,
  ConnectionMetrics,
  WebSocketEvent,
  MessageHandler,
  WebSocketError,
  WebSocketServiceError,
} from '@/types/socket';

/**
 * WebSocket Service Class
 * Implements all real-time communication features with automatic reconnection
 */
class WebSocketService implements IWebSocketService {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private subscriptions = new Map<string, {
    topic: string;
    handler: MessageHandler;
    config: SubscriptionConfig;
    lastMessage?: number;
  }>();
  private eventListeners = new Map<WebSocketEvent, Set<Function>>();
  private metrics: ConnectionMetrics = {
    reconnectCount: 0,
    messagesReceived: 0,
    messagesSent: 0,
    averageLatency: 0,
    errors: [],
  };
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private heartbeatTimeoutTimer: NodeJS.Timeout | null = null;
  private latencyMeasurements: number[] = [];
  private messageQueue: Array<{ type: MessageType; data: any }> = [];

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      reconnectDelayMax: 30000,
      heartbeatInterval: 30000,
      heartbeatTimeout: 5000,
      debug: false,
      protocols: [],
      ...config,
    };

    this.debug('WebSocket service initialized', config);
  }

  /**
   * Establish WebSocket connection
   */
  async connect(url?: string): Promise<void> {
    if (this.socket?.connected) {
      this.debug('Already connected');
      return;
    }

    if (this.connectionState === ConnectionState.CONNECTING) {
      this.debug('Connection already in progress');
      return;
    }

    const connectUrl = url || this.config.url;
    if (!connectUrl) {
      throw new WebSocketServiceError(
        WebSocketError.CONNECTION_FAILED,
        'WebSocket URL is required'
      );
    }

    this.updateConnectionState(ConnectionState.CONNECTING);

    try {
      // Clean up existing socket
      if (this.socket) {
        this.socket.removeAllListeners();
        this.socket.disconnect();
        this.socket = null;
      }

      // Create new socket connection
      this.socket = io(connectUrl, {
        auth: this.config.token ? { token: this.config.token } : undefined,
        protocols: this.config.protocols,
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        timeout: 20000,
        forceNew: true,
      });

      // Set up socket event handlers
      this.setupSocketHandlers();

      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new WebSocketServiceError(
            WebSocketError.CONNECTION_FAILED,
            'Connection timeout'
          ));
        }, 20000);

        this.socket!.once('connect', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.socket!.once('connect_error', (error) => {
          clearTimeout(timeout);
          reject(new WebSocketServiceError(
            WebSocketError.CONNECTION_FAILED,
            error.message
          ));
        });
      });

      this.updateConnectionState(ConnectionState.CONNECTED);
      this.metrics.connectedAt = Date.now();
      this.metrics.reconnectCount = 0;
      this.reconnectAttempts = 0;

      // Start heartbeat
      this.startHeartbeat();

      // Resend subscriptions
      this.resendSubscriptions();

      // Send queued messages
      this.flushMessageQueue();

      this.debug('Connected successfully');
      this.emitEvent('connect');
    } catch (error) {
      this.updateConnectionState(ConnectionState.ERROR);
      this.handleConnectionError(error as Error);
      throw error;
    }
  }

  /**
   * Disconnect WebSocket connection
   */
  disconnect(): void {
    if (!this.socket) {
      return;
    }

    this.debug('Disconnecting...');
    this.clearTimers();
    this.updateConnectionState(ConnectionState.DISCONNECTED);
    this.metrics.disconnectedAt = Date.now();

    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }

    this.emitEvent('disconnect');
  }

  /**
   * Reconnect to WebSocket
   */
  async reconnect(): Promise<void> {
    this.debug('Reconnecting...');
    await this.connect();
  }

  /**
   * Subscribe to a topic with callback
   */
  subscribe<T = BaseMessage>(
    topic: string,
    callback: (message: T) => void,
    config: Partial<SubscriptionConfig> = {}
  ): string {
    const subscriptionId = uuidv4();
    const subscriptionConfig: SubscriptionConfig = {
      topic,
      params: {},
      filter: null,
      throttle: 0,
      batch: false,
      batchSize: 10,
      ...config,
    };

    // Store subscription
    this.subscriptions.set(subscriptionId, {
      topic,
      handler: callback as MessageHandler,
      config: subscriptionConfig,
    });

    // Send subscription message if connected
    if (this.socket?.connected) {
      this.send(MessageType.SUBSCRIBE, {
        topic,
        params: subscriptionConfig.params,
      });
    }

    this.debug(`Subscribed to topic: ${topic}`, { subscriptionId, config });
    return subscriptionId;
  }

  /**
   * Unsubscribe from a topic
   */
  unsubscribe(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      return;
    }

    // Send unsubscribe message if connected
    if (this.socket?.connected) {
      this.send(MessageType.UNSUBSCRIBE, {
        topic: subscription.topic,
      });
    }

    // Remove subscription
    this.subscriptions.delete(subscriptionId);
    this.debug(`Unsubscribed from topic: ${subscription.topic}`, { subscriptionId });
  }

  /**
   * Unsubscribe from all topics
   */
  unsubscribeAll(): void {
    const subscriptionIds = Array.from(this.subscriptions.keys());
    subscriptionIds.forEach(id => this.unsubscribe(id));
  }

  /**
   * Send a message
   */
  send<T = any>(type: MessageType, data: T): void {
    const message: BaseMessage = {
      id: uuidv4(),
      type,
      timestamp: Date.now(),
      data,
    };

    if (this.socket?.connected) {
      this.socket.emit('message', message);
      this.metrics.messagesSent++;
      this.debug('Message sent', message);
    } else {
      // Queue message for later sending
      this.messageQueue.push({ type, data });
      this.debug('Message queued', message);
    }
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === ConnectionState.CONNECTED && this.socket?.connected === true;
  }

  /**
   * Check if reconnecting
   */
  isReconnecting(): boolean {
    return this.connectionState === ConnectionState.RECONNECTING;
  }

  /**
   * Add event listener
   */
  on(event: WebSocketEvent, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);
  }

  /**
   * Remove event listener
   */
  off(event: WebSocketEvent, callback: Function): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.eventListeners.delete(event);
      }
    }
  }

  /**
   * Get all subscription IDs
   */
  getSubscriptionIds(): string[] {
    return Array.from(this.subscriptions.keys());
  }

  /**
   * Get connection metrics
   */
  getConnectionMetrics(): ConnectionMetrics {
    return { ...this.metrics };
  }

  /**
   * Set up socket event handlers
   */
  private setupSocketHandlers(): void {
    if (!this.socket) {
      return;
    }

    // Connection events
    this.socket.on('connect', () => {
      this.debug('Socket connected');
    });

    this.socket.on('disconnect', (reason) => {
      this.debug('Socket disconnected', reason);
      this.updateConnectionState(ConnectionState.DISCONNECTED);
      this.clearTimers();
      this.emitEvent('disconnect');

      // Attempt reconnection if not intentional
      if (reason !== 'io client disconnect') {
        this.handleDisconnection();
      }
    });

    this.socket.on('connect_error', (error) => {
      this.debug('Connection error', error);
      this.metrics.errors.push({
        timestamp: Date.now(),
        message: error.message,
        code: 'CONNECT_ERROR',
      });
    });

    // Message handling
    this.socket.on('message', (message: BaseMessage) => {
      this.handleMessage(message);
    });

    // Heartbeat handling
    this.socket.on('ping', () => {
      this.emitEvent('ping');
      this.socket?.emit('pong');
    });

    this.socket.on('pong', () => {
      this.emitEvent('pong');
      this.updateLatency();
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: BaseMessage): void {
    this.metrics.messagesReceived++;
    this.metrics.lastMessageAt = Date.now();

    // Update subscription last message time
    this.subscriptions.forEach(sub => {
      if (this.matchesSubscription(message, sub.config)) {
        sub.lastMessage = Date.now();
      }
    });

    // Process message
    this.processMessage(message);
  }

  /**
   * Process message and route to subscribers
   */
  private processMessage(message: BaseMessage): void {
    // Handle system messages
    if (message.type === MessageType.HEARTBEAT) {
      this.handleHeartbeatResponse(message);
      return;
    }

    if (message.type === MessageType.ACKNOWLEDGE) {
      this.handleAcknowledgement(message);
      return;
    }

    // Route to subscribers
    this.subscriptions.forEach(sub => {
      if (this.matchesSubscription(message, sub.config)) {
        // Apply filter if present
        if (sub.config.filter && !sub.config.filter(message)) {
          return;
        }

        // Apply throttling if configured
        if (sub.config.throttle > 0 && sub.lastMessage) {
          const timeSinceLast = Date.now() - sub.lastMessage;
          if (timeSinceLast < sub.config.throttle) {
            return;
          }
        }

        // Call handler
        try {
          sub.handler(message);
        } catch (error) {
          console.error('Error in subscription handler:', error);
          this.metrics.errors.push({
            timestamp: Date.now(),
            message: 'Handler error',
            code: 'HANDLER_ERROR',
          });
        }
      }
    });

    this.emitEvent('message', message);
  }

  /**
   * Check if message matches subscription
   */
  private matchesSubscription(message: BaseMessage, config: SubscriptionConfig): boolean {
    // Simple topic matching - can be extended
    if (config.topic === '*') {
      return true;
    }

    // Check if message type matches topic
    return message.type.toString() === config.topic;
  }

  /**
   * Handle heartbeat response
   */
  private handleHeartbeatResponse(message: BaseMessage): void {
    this.debug('Heartbeat response received');
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
  }

  /**
   * Handle acknowledgement message
   */
  private handleAcknowledgement(message: BaseMessage): void {
    this.debug('Acknowledgement received', message);
  }

  /**
   * Start heartbeat mechanism
   */
  private startHeartbeat(): void {
    if (!this.config.heartbeatInterval) {
      return;
    }

    this.clearHeartbeatTimers();

    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.connected) {
        this.send(MessageType.HEARTBEAT, { timestamp: Date.now() });

        // Set timeout for response
        this.heartbeatTimeoutTimer = setTimeout(() => {
          this.handleHeartbeatTimeout();
        }, this.config.heartbeatTimeout!);
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Handle heartbeat timeout
   */
  private handleHeartbeatTimeout(): void {
    this.debug('Heartbeat timeout');
    this.metrics.errors.push({
      timestamp: Date.now(),
      message: 'Heartbeat timeout',
      code: 'HEARTBEAT_TIMEOUT',
    });

    // Force reconnection
    if (this.socket) {
      this.socket.disconnect();
    }
  }

  /**
   * Update connection latency measurement
   */
  private updateLatency(): void {
    const now = Date.now();
    // Simple latency calculation - can be improved
    this.latencyMeasurements.push(now - (this.metrics.lastMessageAt || now));

    // Keep only last 10 measurements
    if (this.latencyMeasurements.length > 10) {
      this.latencyMeasurements.shift();
    }

    // Calculate average
    this.metrics.averageLatency = this.latencyMeasurements.reduce((a, b) => a + b, 0) / this.latencyMeasurements.length;
  }

  /**
   * Handle disconnection and attempt reconnection
   */
  private handleDisconnection(): void {
    if (this.reconnectAttempts >= (this.config.reconnectAttempts || 5)) {
      this.debug('Max reconnection attempts reached');
      this.updateConnectionState(ConnectionState.ERROR);
      this.emitEvent('error', new WebSocketServiceError(
        WebSocketError.MAX_RECONNECT_ATTEMPTS,
        'Maximum reconnection attempts reached'
      ));
      return;
    }

    this.updateConnectionState(ConnectionState.RECONNECTING);
    this.reconnectAttempts++;

    // Calculate delay with exponential backoff
    const delay = Math.min(
      (this.config.reconnectDelay || 1000) * Math.pow(2, this.reconnectAttempts - 1),
      this.config.reconnectDelayMax || 30000
    );

    this.debug(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.metrics.reconnectCount++;
      this.reconnect().catch(error => {
        this.handleConnectionError(error);
      });
    }, delay);
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(error: Error): void {
    this.debug('Connection error', error);
    this.metrics.errors.push({
      timestamp: Date.now(),
      message: error.message,
      code: error.name,
    });

    this.emitEvent('error', error);

    // Attempt reconnection if not at max attempts
    if (this.reconnectAttempts < (this.config.reconnectAttempts || 5)) {
      this.handleDisconnection();
    }
  }

  /**
   * Resend all subscriptions after reconnection
   */
  private resendSubscriptions(): void {
    this.subscriptions.forEach(sub => {
      this.send(MessageType.SUBSCRIBE, {
        topic: sub.config.topic,
        params: sub.config.params,
      });
    });
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    const queue = [...this.messageQueue];
    this.messageQueue = [];

    queue.forEach(({ type, data }) => {
      this.send(type, data);
    });
  }

  /**
   * Update connection state
   */
  private updateConnectionState(state: ConnectionState): void {
    const oldState = this.connectionState;
    this.connectionState = state;

    if (oldState !== state) {
      this.debug('Connection state changed', { from: oldState, to: state });
    }
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    this.clearReconnectTimer();
    this.clearHeartbeatTimers();
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Clear heartbeat timers
   */
  private clearHeartbeatTimers(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
  }

  /**
   * Emit event to listeners
   */
  private emitEvent(event: WebSocketEvent, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args);
        } catch (error) {
          console.error('Error in event listener:', error);
        }
      });
    }
  }

  /**
   * Debug logging
   */
  private debug(message: string, data?: any): void {
    if (this.config.debug) {
      console.log(`[WebSocketService] ${message}`, data || '');
    }
  }

  /**
   * Cleanup method
   */
  destroy(): void {
    this.disconnect();
    this.subscriptions.clear();
    this.eventListeners.clear();
    this.messageQueue = [];
  }
}

// Export singleton instance
let webSocketServiceInstance: WebSocketService | null = null;

export const createWebSocketService = (config: WebSocketConfig): IWebSocketService => {
  if (webSocketServiceInstance) {
    webSocketServiceInstance.destroy();
  }
  webSocketServiceInstance = new WebSocketService(config);
  return webSocketServiceInstance;
};

export const getWebSocketService = (): IWebSocketService | null => {
  return webSocketServiceInstance;
};

export default WebSocketService;