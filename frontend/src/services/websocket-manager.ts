/**
 * WebSocket Manager
 * Manages multiple WebSocket connections and provides advanced features
 */

import { IWebSocketService, WebSocketConfig, createWebSocketService } from './socket';
import { MessageType, BaseMessage } from '@/types/socket';

// Manager configuration
export interface WebSocketManagerConfig {
  defaultConnection?: WebSocketConfig;
  connections?: Record<string, WebSocketConfig>;
  maxConnections?: number;
  enableConnectionPooling?: boolean;
  enableLoadBalancing?: boolean;
  debug?: boolean;
}

// Connection pool entry
interface ConnectionPoolEntry {
  service: IWebSocketService;
  config: WebSocketConfig;
  lastUsed: number;
  messageCount: number;
  isActive: boolean;
}

/**
 * WebSocket Manager Class
 * Manages multiple WebSocket connections with load balancing and pooling
 */
class WebSocketManager {
  private config: WebSocketManagerConfig;
  private connections = new Map<string, IWebSocketService>();
  private connectionPool: ConnectionPoolEntry[] = [];
  private defaultConnection: string | null = null;
  private messageHandlers = new Map<string, Set<(message: BaseMessage) => void>>();
  private debug: (message: string, data?: any) => void;

  constructor(config: WebSocketManagerConfig = {}) {
    this.config = {
      maxConnections: 10,
      enableConnectionPooling: true,
      enableLoadBalancing: false,
      debug: false,
      ...config,
    };

    this.debug = this.createDebugger();

    // Create default connection if provided
    if (this.config.defaultConnection) {
      this.defaultConnection = 'default';
      this.createConnection('default', this.config.defaultConnection);
    }

    // Create additional connections if provided
    if (this.config.connections) {
      Object.entries(this.config.connections).forEach(([name, config]) => {
        this.createConnection(name, config);
      });
    }

    this.debug('WebSocket Manager initialized', this.config);
  }

  /**
   * Create a new WebSocket connection
   */
  createConnection(name: string, config: WebSocketConfig): IWebSocketService {
    if (this.connections.has(name)) {
      throw new Error(`Connection '${name}' already exists`);
    }

    if (this.connections.size >= (this.config.maxConnections || 10)) {
      throw new Error('Maximum connections reached');
    }

    const service = createWebSocketService(config);
    this.connections.set(name, service);

    // Set up message forwarding
    service.on('message', (message: BaseMessage) => {
      this.forwardMessage(name, message);
    });

    this.debug(`Created connection: ${name}`, config);

    // Set as default if no default exists
    if (!this.defaultConnection) {
      this.defaultConnection = name;
    }

    return service;
  }

  /**
   * Get a WebSocket connection by name
   */
  getConnection(name?: string): IWebSocketService | null {
    const connectionName = name || this.defaultConnection;
    if (!connectionName) {
      return null;
    }

    return this.connections.get(connectionName) || null;
  }

  /**
   * Remove a WebSocket connection
   */
  removeConnection(name: string): void {
    const service = this.connections.get(name);
    if (service) {
      service.disconnect();
      this.connections.delete(name);
      this.debug(`Removed connection: ${name}`);

      // Update default if necessary
      if (this.defaultConnection === name) {
        this.defaultConnection = this.connections.size > 0
          ? this.connections.keys().next().value
          : null;
      }
    }
  }

  /**
   * Connect all or specific connections
   */
  async connectAll(): Promise<void> {
    const promises = Array.from(this.connections.values()).map(service =>
      service.connect().catch(error => {
        this.debug('Connection failed', error);
        return null;
      })
    );

    await Promise.all(promises);
  }

  /**
   * Disconnect all connections
   */
  disconnectAll(): void {
    this.connections.forEach(service => {
      service.disconnect();
    });
  }

  /**
   * Subscribe to a message type across all connections
   */
  subscribe<T = BaseMessage>(
    messageType: MessageType,
    handler: (message: T, connectionName: string) => void,
    connectionName?: string
  ): string {
    const handlerId = this.generateId();
    const wrappedHandler = (message: BaseMessage) => {
      if (message.type === messageType) {
        handler(message as T, connectionName || 'unknown');
      }
    };

    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }

    this.messageHandlers.get(messageType)!.add(wrappedHandler);

    // Subscribe to specific connection or all
    if (connectionName) {
      const service = this.connections.get(connectionName);
      if (service) {
        service.subscribe(messageType, wrappedHandler);
      }
    } else {
      this.connections.forEach(service => {
        service.subscribe(messageType, wrappedHandler);
      });
    }

    return handlerId;
  }

  /**
   * Unsubscribe from a message type
   */
  unsubscribe(handlerId: string, messageType?: MessageType): void {
    if (messageType) {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        handlers.forEach(handler => {
          // Remove from all connections
          this.connections.forEach(service => {
            service.off('message', handler);
          });
        });
        handlers.clear();
        this.messageHandlers.delete(messageType);
      }
    } else {
      // Remove from all message types
      this.messageHandlers.forEach((handlers, type) => {
        handlers.forEach(handler => {
          this.connections.forEach(service => {
            service.off('message', handler);
          });
        });
      });
      this.messageHandlers.clear();
    }
  }

  /**
   * Send a message through the best available connection
   */
  send<T = any>(type: MessageType, data: T, connectionName?: string): boolean {
    let service: IWebSocketService | null = null;

    if (connectionName) {
      service = this.connections.get(connectionName) || null;
    } else if (this.config.enableLoadBalancing) {
      service = this.selectBestConnection();
    } else {
      service = this.getConnection();
    }

    if (service && service.isConnected()) {
      service.send(type, data);
      this.updateConnectionStats(service);
      return true;
    }

    this.debug('Failed to send message - no available connection');
    return false;
  }

  /**
   * Broadcast a message to all connections
   */
  broadcast<T = any>(type: MessageType, data: T): void {
    this.connections.forEach(service => {
      if (service.isConnected()) {
        service.send(type, data);
        this.updateConnectionStats(service);
      }
    });
  }

  /**
   * Get connection statistics
   */
  getStats(): Record<string, any> {
    const stats: Record<string, any> = {
      totalConnections: this.connections.size,
      activeConnections: 0,
      totalMessagesReceived: 0,
      totalMessagesSent: 0,
      averageLatency: 0,
      connections: {},
    };

    let totalLatency = 0;
    let latencyCount = 0;

    this.connections.forEach((service, name) => {
      const metrics = service.getConnectionMetrics();
      const isConnected = service.isConnected();

      stats.connections[name] = {
        state: service.getConnectionState(),
        connected: isConnected,
        messagesReceived: metrics.messagesReceived,
        messagesSent: metrics.messagesSent,
        latency: metrics.averageLatency,
        errors: metrics.errors.length,
      };

      if (isConnected) {
        stats.activeConnections++;
      }

      stats.totalMessagesReceived += metrics.messagesReceived;
      stats.totalMessagesSent += metrics.messagesSent;

      if (metrics.averageLatency > 0) {
        totalLatency += metrics.averageLatency;
        latencyCount++;
      }
    });

    if (latencyCount > 0) {
      stats.averageLatency = totalLatency / latencyCount;
    }

    return stats;
  }

  /**
   * Get connection health status
   */
  getHealthStatus(): {
    status: 'healthy' | 'degraded' | 'unhealthy';
    issues: string[];
  } {
    const stats = this.getStats();
    const issues: string[] = [];

    // Check if we have any active connections
    if (stats.activeConnections === 0) {
      issues.push('No active connections');
    }

    // Check error rates
    Object.values(stats.connections).forEach((conn: any) => {
      if (conn.errors > 10) {
        issues.push(`High error count on connection`);
      }
      if (conn.latency > 1000) {
        issues.push(`High latency on connection`);
      }
    });

    // Check if default connection is available
    if (this.defaultConnection && !stats.connections[this.defaultConnection]?.connected) {
      issues.push('Default connection is not active');
    }

    // Determine overall status
    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    if (issues.length > 0) {
      status = issues.length > 2 ? 'unhealthy' : 'degraded';
    }

    return { status, issues };
  }

  /**
   * Select the best connection for load balancing
   */
  private selectBestConnection(): IWebSocketService | null {
    let bestConnection: IWebSocketService | null = null;
    let bestScore = -1;

    this.connections.forEach(service => {
      if (!service.isConnected()) {
        return;
      }

      const metrics = service.getConnectionMetrics();

      // Calculate score based on latency and message count
      const latencyScore = metrics.averageLatency > 0 ? 1000 / metrics.averageLatency : 100;
      const messageScore = metrics.messagesSent / (metrics.messagesReceived + 1);
      const score = latencyScore + messageScore;

      if (score > bestScore) {
        bestScore = score;
        bestConnection = service;
      }
    });

    return bestConnection;
  }

  /**
   * Update connection statistics for pooling
   */
  private updateConnectionStats(service: IWebSocketService): void {
    if (!this.config.enableConnectionPooling) {
      return;
    }

    // Find connection in pool
    const poolEntry = this.connectionPool.find(entry => entry.service === service);
    if (poolEntry) {
      poolEntry.lastUsed = Date.now();
      poolEntry.messageCount++;
      poolEntry.isActive = true;
    }
  }

  /**
   * Forward message to registered handlers
   */
  private forwardMessage(connectionName: string, message: BaseMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Create debug logger
   */
  private createDebugger() {
    return (message: string, data?: any) => {
      if (this.config.debug) {
        console.log(`[WebSocketManager] ${message}`, data || '');
      }
    };
  }

  /**
   * Cleanup method
   */
  destroy(): void {
    this.disconnectAll();
    this.connections.clear();
    this.messageHandlers.clear();
    this.connectionPool = [];
    this.defaultConnection = null;
  }
}

// Export singleton instance
let webSocketManagerInstance: WebSocketManager | null = null;

export const createWebSocketManager = (config?: WebSocketManagerConfig): WebSocketManager => {
  if (webSocketManagerInstance) {
    webSocketManagerInstance.destroy();
  }
  webSocketManagerInstance = new WebSocketManager(config);
  return webSocketManagerInstance;
};

export const getWebSocketManager = (): WebSocketManager | null => {
  return webSocketManagerInstance;
};

export default WebSocketManager;