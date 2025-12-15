/**
 * WebSocket related type definitions
 * Defines the structure for WebSocket messages, connection states, and service configurations
 */

// WebSocket message types
export enum MessageType {
  // Data messages
  DATA = 'data',
  STRATEGY_UPDATE = 'strategy_update',
  PRICE_FEED = 'price_feed',
  NOTIFICATION = 'notification',

  // Control messages
  PING = 'ping',
  PONG = 'pong',
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',

  // Connection messages
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  ERROR = 'error',

  // System messages
  HEARTBEAT = 'heartbeat',
  AUTH = 'auth',
  AUTH_SUCCESS = 'auth_success',
  AUTH_FAILED = 'auth_failed'
}

// WebSocket channel types
export enum ChannelType {
  STRATEGY_UPDATES = 'strategy-updates',
  PRICE_FEEDS = 'price-feeds',
  NOTIFICATIONS = 'notifications',
  PORTFOLIO_UPDATES = 'portfolio-updates',
  MARKET_DATA = 'market-data',
  SYSTEM_EVENTS = 'system-events'
}

// Connection states
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

// WebSocket message interface
export interface WSMessage {
  id: string;
  type: MessageType;
  channel?: ChannelType;
  data?: any;
  timestamp: number;
  userId?: string;
  sessionId?: string;
}

// Subscription request
export interface SubscriptionRequest {
  channel: ChannelType;
  filters?: Record<string, any>;
  throttleMs?: number;
}

// WebSocket configuration
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  connectionTimeout?: number;
  enableLogging?: boolean;
  authToken?: string;
  bufferSize?: number;
  throttleMessages?: boolean;
}

// Connection metrics
export interface ConnectionMetrics {
  connectedAt?: number;
  lastPingTime?: number;
  lastPongTime?: number;
  latency?: number;
  reconnectCount: number;
  messagesReceived: number;
  messagesSent: number;
  bytesReceived: number;
  bytesSent: number;
  errorCount: number;
}

// Cache configuration
export interface CacheConfig {
  maxSize: number;
  defaultTTL: number; // Time to live in milliseconds
  enablePersistence: boolean;
  persistenceKey?: string;
  cleanupInterval: number;
}

// Cached data entry
export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
  accessCount: number;
  lastAccessed: number;
}

// WebSocket event callbacks
export interface WebSocketEventCallbacks {
  onConnect?: () => void;
  onDisconnect?: (code: number, reason: string) => void;
  onError?: (error: Error | Event) => void;
  onMessage?: (message: WSMessage) => void;
  onReconnect?: (attempt: number) => void;
  onStateChange?: (oldState: ConnectionState, newState: ConnectionState) => void;
  onLatencyUpdate?: (latency: number) => void;
}

// Message queue entry
export interface QueuedMessage {
  message: WSMessage;
  timestamp: number;
  retries: number;
  priority: 'high' | 'normal' | 'low';
}

// Channel subscription
export interface ChannelSubscription {
  channel: ChannelType;
  callback: (data: any) => void;
  filters?: Record<string, any>;
  active: boolean;
  createdAt: number;
  lastMessage?: number;
}

// Reconnection strategy
export interface ReconnectStrategy {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
  jitter: boolean;
  onReconnecting?: (attempt: number, delay: number) => void;
  onFailed?: () => void;
}

// Network status information
export interface NetworkStatus {
  online: boolean;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

// WebSocket service interface
export interface IWebSocketService {
  connect(): Promise<void>;
  disconnect(): void;
  send(message: WSMessage): boolean;
  subscribe(channel: ChannelType, callback: (data: any) => void, filters?: Record<string, any>): () => void;
  unsubscribe(channel: ChannelType): void;
  getConnectionState(): ConnectionState;
  getConnectionMetrics(): ConnectionMetrics;
  getNetworkStatus(): NetworkStatus;
  getConnectionQuality(): 'excellent' | 'good' | 'fair' | 'poor';
  addEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void;
  removeEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void;
}

// TypeScript declaration for WebSocket with additional properties
interface EnhancedWebSocket extends WebSocket {
  binaryType?: string;
  bufferedAmount?: number;
  extensions?: string;
  protocol?: string;
}

// Message transformer function type
export type MessageTransformer = (message: WSMessage) => WSMessage | null;

// Authentication payload
export interface AuthPayload {
  token: string;
  userId?: string;
  clientId?: string;
  timestamp: number;
  signature?: string;
}

// Error types
export enum WebSocketErrorType {
  CONNECTION_FAILED = 'connection_failed',
  AUTHENTICATION_FAILED = 'authentication_failed',
  SUBSCRIPTION_FAILED = 'subscription_failed',
  MESSAGE_SEND_FAILED = 'message_send_failed',
  PARSER_ERROR = 'parser_error',
  TIMEOUT = 'timeout',
  NETWORK_ERROR = 'network_error'
}

// WebSocket error interface
export interface WebSocketError {
  type: WebSocketErrorType;
  message: string;
  code?: number;
  details?: any;
  timestamp: number;
}