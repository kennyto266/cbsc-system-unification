/**
 * Core WebSocket Service
 * Main service that combines all WebSocket functionality
 */

import {
  IWebSocketService,
  WebSocketConfig,
  ConnectionState,
  ConnectionMetrics,
  NetworkStatus,
  WebSocketEventCallbacks,
  WSMessage,
  MessageType,
  ChannelType,
  SubscriptionRequest,
  WebSocketError
} from '../../types/websocket';

import { ConnectionManager } from './ConnectionManager';
import { MessageQueue } from './MessageQueue';
import { CacheManager } from './CacheManager';
import { ReconnectionStrategy, ReconnectionStrategies, NetworkAwareReconnectionStrategy } from './ReconnectStrategy';

export class WebSocketService implements IWebSocketService {
  private connectionManager: ConnectionManager;
  private messageQueue: MessageQueue;
  private cacheManager: CacheManager;
  private reconnectStrategy: ReconnectionStrategy;
  private subscriptions: Map<ChannelType, Set<(data: any) => void>> = new Map();
  private subscriptionFilters: Map<ChannelType, Record<string, any>> = new Map();
  private config: WebSocketConfig;
  private isDestroyed = false;
  private messageTransformer?: (message: WSMessage) => WSMessage | null;

  constructor(config: WebSocketConfig) {
    this.config = config;

    // Initialize connection manager
    this.connectionManager = new ConnectionManager(config);
    this.setupConnectionEvents();

    // Initialize message queue
    this.messageQueue = new MessageQueue(
      async (message: WSMessage) => {
        return this.connectionManager.send(message);
      },
      {
        maxSize: config.bufferSize || 1000,
        batchSize: 10,
        batchInterval: 100
      }
    );

    // Initialize cache manager
    this.cacheManager = new CacheManager({
      maxSize: 500,
      defaultTTL: 300000, // 5 minutes
      enablePersistence: true,
      persistenceKey: 'websocket_cache'
    });

    // Initialize reconnection strategy
    this.reconnectStrategy = new NetworkAwareReconnectionStrategy({
      maxAttempts: config.reconnectAttempts || 5,
      baseDelay: config.reconnectDelay || 1000,
      maxDelay: 30000,
      onReconnecting: (attempt: number, delay: number) => {
        console.log(`[WebSocket] Reconnection attempt ${attempt} in ${delay}ms`);
      },
      onFailed: () => {
        console.error('[WebSocket] All reconnection attempts failed');
      }
    });
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.isDestroyed) {
      throw new Error('Service has been destroyed');
    }

    try {
      await this.connectionManager.connect();
    } catch (error) {
      throw new WebSocketError({
        type: 'CONNECTION_FAILED' as any,
        message: error instanceof Error ? error.message : 'Connection failed',
        details: error,
        timestamp: Date.now()
      });
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.isDestroyed) {
      return;
    }

    this.reconnectStrategy.stop();
    this.connectionManager.disconnect();
    this.messageQueue.clear();
    this.subscriptions.clear();
    this.subscriptionFilters.clear();
  }

  /**
   * Send message through WebSocket
   */
  send(message: WSMessage): boolean {
    if (this.isDestroyed) {
      return false;
    }

    // Add timestamp if not present
    if (!message.timestamp) {
      message.timestamp = Date.now();
    }

    // Add message ID if not present
    if (!message.id) {
      message.id = this.generateMessageId();
    }

    // Apply message transformer if present
    if (this.messageTransformer) {
      const transformed = this.messageTransformer(message);
      if (!transformed) {
        return false;
      }
      message = transformed;
    }

    // Queue message for sending
    const priority = this.getMessagePriority(message.type);
    return this.messageQueue.enqueue(message, priority);
  }

  /**
   * Subscribe to a channel
   */
  subscribe(
    channel: ChannelType,
    callback: (data: any) => void,
    filters?: Record<string, any>
  ): () => void {
    // Add subscription
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());
    }
    this.subscriptions.get(channel)!.add(callback);

    // Store filters
    if (filters) {
      this.subscriptionFilters.set(channel, filters);
    }

    // Send subscription request
    const subscriptionRequest: SubscriptionRequest = {
      channel,
      filters,
      throttleMs: 100
    };

    this.send({
      id: this.generateMessageId(),
      type: MessageType.SUBSCRIBE,
      channel,
      data: subscriptionRequest,
      timestamp: Date.now()
    });

    // Return unsubscribe function
    return () => this.unsubscribe(channel, callback);
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: ChannelType, callback?: (data: any) => void): void {
    const callbacks = this.subscriptions.get(channel);
    if (!callbacks) {
      return;
    }

    // Remove specific callback or all callbacks
    if (callback) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.subscriptions.delete(channel);
        this.subscriptionFilters.delete(channel);
      }
    } else {
      callbacks.clear();
      this.subscriptions.delete(channel);
      this.subscriptionFilters.delete(channel);
    }

    // Send unsubscribe request if no more callbacks
    if (!this.subscriptions.has(channel)) {
      this.send({
        id: this.generateMessageId(),
        type: MessageType.UNSUBSCRIBE,
        channel,
        data: { channel },
        timestamp: Date.now()
      });
    }
  }

  /**
   * Get connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionManager.getState();
  }

  /**
   * Get connection metrics
   */
  getConnectionMetrics(): ConnectionMetrics {
    return this.connectionManager.getMetrics();
  }

  /**
   * Get network status
   */
  getNetworkStatus(): NetworkStatus {
    return this.connectionManager.getNetworkStatus();
  }

  /**
   * Get connection quality
   */
  getConnectionQuality(): 'excellent' | 'good' | 'fair' | 'poor' {
    return this.connectionManager.getConnectionQuality();
  }

  /**
   * Add event listener
   */
  addEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    this.connectionManager.addEventListener(event, callback);
  }

  /**
   * Remove event listener
   */
  removeEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    this.connectionManager.removeEventListener(event, callback);
  }

  /**
   * Set message transformer
   */
  setMessageTransformer(transformer: (message: WSMessage) => WSMessage | null): void {
    this.messageTransformer = transformer;
  }

  /**
   * Get cache manager instance
   */
  getCacheManager(): CacheManager {
    return this.cacheManager;
  }

  /**
   * Get service statistics
   */
  getStats() {
    return {
      connection: {
        state: this.getConnectionState(),
        quality: this.getConnectionQuality(),
        metrics: this.getConnectionMetrics()
      },
      queue: this.messageQueue.getStats(),
      cache: this.cacheManager.getStats(),
      subscriptions: {
        total: Array.from(this.subscriptions.values()).reduce((sum, set) => sum + set.size, 0),
        channels: Array.from(this.subscriptions.keys())
      },
      reconnection: this.reconnectStrategy.getStats()
    };
  }

  /**
   * Destroy the service and cleanup resources
   */
  destroy(): void {
    if (this.isDestroyed) {
      return;
    }

    this.isDestroyed = true;

    // Disconnect
    this.disconnect();

    // Destroy components
    this.connectionManager.destroy();
    this.messageQueue.destroy();
    this.cacheManager.destroy();
    this.reconnectStrategy.stop();

    // Clear references
    this.subscriptions.clear();
    this.subscriptionFilters.clear();
  }

  /**
   * Set up connection event handlers
   */
  private setupConnectionEvents(): void {
    this.connectionManager.addEventListener('onConnect', () => {
      console.log('[WebSocket] Connected successfully');
      this.reconnectStrategy.reset();
    });

    this.connectionManager.addEventListener('onDisconnect', () => {
      console.log('[WebSocket] Disconnected');
      // Handle reconnection
      if (!this.isDestroyed) {
        this.handleReconnection();
      }
    });

    this.connectionManager.addEventListener('onMessage', (message: WSMessage) => {
      this.handleIncomingMessage(message);
    });

    this.connectionManager.addEventListener('onError', (error: WebSocketError) => {
      console.error('[WebSocket] Error:', error);
    });
  }

  /**
   * Handle incoming messages
   */
  private handleIncomingMessage(message: WSMessage): void {
    // Cache message data
    if (message.data && message.channel) {
      const cacheKey = `${message.channel}:${JSON.stringify(message.data)}`;
      this.cacheManager.set(cacheKey, message.data, 60000); // 1 minute TTL
    }

    // Route to subscribers
    if (message.channel && this.subscriptions.has(message.channel)) {
      const callbacks = this.subscriptions.get(message.channel)!;
      const filters = this.subscriptionFilters.get(message.channel);

      callbacks.forEach(callback => {
        try {
          // Apply filters if present
          if (filters && !this.matchesFilters(message.data, filters)) {
            return;
          }

          callback(message.data);
        } catch (error) {
          console.error('[WebSocket] Callback error:', error);
        }
      });
    }
  }

  /**
   * Handle reconnection
   */
  private async handleReconnection(): Promise<void> {
    try {
      await this.reconnectStrategy.start(async () => {
        await this.connectionManager.connect();

        // Resubscribe to all channels
        this.resubscribeAllChannels();
      });
    } catch (error) {
      console.error('[WebSocket] Reconnection failed:', error);
    }
  }

  /**
   * Resubscribe to all channels after reconnection
   */
  private resubscribeAllChannels(): void {
    this.subscriptions.forEach((callbacks, channel) => {
      const filters = this.subscriptionFilters.get(channel);

      this.send({
        id: this.generateMessageId(),
        type: MessageType.SUBSCRIBE,
        channel,
        data: {
          channel,
          filters,
          throttleMs: 100
        },
        timestamp: Date.now()
      });
    });
  }

  /**
   * Check if data matches filters
   */
  private matchesFilters(data: any, filters: Record<string, any>): boolean {
    for (const [key, value] of Object.entries(filters)) {
      if (data[key] !== value) {
        return false;
      }
    }
    return true;
  }

  /**
   * Get message priority
   */
  private getMessagePriority(type: MessageType): 'high' | 'normal' | 'low' {
    switch (type) {
      case MessageType.PING:
      case MessageType.PONG:
      case MessageType.AUTH:
      case MessageType.SUBSCRIBE:
      case MessageType.UNSUBSCRIBE:
        return 'high';
      case MessageType.ERROR:
      case MessageType.DISCONNECT:
        return 'high';
      case MessageType.DATA:
      case MessageType.NOTIFICATION:
        return 'normal';
      default:
        return 'low';
    }
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Create singleton instance
let webSocketService: WebSocketService | null = null;

export const getWebSocketService = (config?: WebSocketConfig): WebSocketService => {
  if (!webSocketService) {
    const defaultConfig: WebSocketConfig = {
      url: process.env.REACT_APP_WS_URL || 'ws://localhost:3004/ws',
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      enableLogging: true
    };

    webSocketService = new WebSocketService(config || defaultConfig);
  }
  return webSocketService;
};

export default WebSocketService;