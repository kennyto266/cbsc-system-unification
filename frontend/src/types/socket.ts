/**
 * WebSocket related type definitions
 * Supports real-time communication for trading data and system notifications
 */

// Connection state enumeration
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

// Message types for WebSocket communication
export enum MessageType {
  // Market data
  PRICE_UPDATE = 'price_update',
  ORDER_BOOK = 'order_book',
  TRADE_DATA = 'trade_data',

  // Strategy execution
  STRATEGY_SIGNAL = 'strategy_signal',
  STRATEGY_EXECUTION = 'strategy_execution',
  STRATEGY_STATUS = 'strategy_status',

  // System alerts
  SYSTEM_ALERT = 'system_alert',
  ERROR_NOTIFICATION = 'error_notification',
  WARNING = 'warning',

  // User activity
  USER_ACTIVITY = 'user_activity',
  SESSION_UPDATE = 'session_update',

  // Connection management
  HEARTBEAT = 'heartbeat',
  ACKNOWLEDGE = 'acknowledge',
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
}

// Base WebSocket message structure
export interface BaseMessage {
  id: string;
  type: MessageType;
  timestamp: number;
  data?: any;
}

// Market data messages
export interface PriceUpdateMessage extends BaseMessage {
  type: MessageType.PRICE_UPDATE;
  data: {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
    timestamp: number;
  };
}

export interface OrderBookMessage extends BaseMessage {
  type: MessageType.ORDER_BOOK;
  data: {
    symbol: string;
    bids: Array<[number, number]>;
    asks: Array<[number, number]>;
    timestamp: number;
  };
}

export interface TradeDataMessage extends BaseMessage {
  type: MessageType.TRADE_DATA;
  data: {
    symbol: string;
    price: number;
    quantity: number;
    side: 'buy' | 'sell';
    timestamp: number;
  };
}

// Strategy messages
export interface StrategySignalMessage extends BaseMessage {
  type: MessageType.STRATEGY_SIGNAL;
  data: {
    strategyId: string;
    signal: 'buy' | 'sell' | 'hold';
    symbol: string;
    confidence: number;
    parameters: Record<string, any>;
    timestamp: number;
  };
}

export interface StrategyExecutionMessage extends BaseMessage {
  type: MessageType.STRATEGY_EXECUTION;
  data: {
    strategyId: string;
    executionId: string;
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    price: number;
    status: 'pending' | 'executed' | 'failed';
    reason?: string;
    timestamp: number;
  };
}

export interface StrategyStatusMessage extends BaseMessage {
  type: MessageType.STRATEGY_STATUS;
  data: {
    strategyId: string;
    status: 'active' | 'paused' | 'stopped' | 'error';
    performance: {
      totalReturn: number;
      winRate: number;
      sharpeRatio: number;
      maxDrawdown: number;
    };
    timestamp: number;
  };
}

// System alert messages
export interface SystemAlertMessage extends BaseMessage {
  type: MessageType.SYSTEM_ALERT;
  data: {
    level: 'info' | 'warning' | 'error' | 'critical';
    message: string;
    details?: any;
    source: string;
    timestamp: number;
  };
}

// User activity messages
export interface UserActivityMessage extends BaseMessage {
  type: MessageType.USER_ACTIVITY;
  data: {
    userId: string;
    action: string;
    resource?: string;
    metadata?: Record<string, any>;
    timestamp: number;
  };
}

// WebSocket configuration
export interface WebSocketConfig {
  url: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  reconnectDelayMax?: number;
  heartbeatInterval?: number;
  heartbeatTimeout?: number;
  debug?: boolean;
  token?: string;
  protocols?: string[];
}

// Subscription configuration
export interface SubscriptionConfig {
  topic: string;
  params?: Record<string, any>;
  filter?: (message: BaseMessage) => boolean;
  throttle?: number;
  batch?: boolean;
  batchSize?: number;
}

// WebSocket service interface
export interface IWebSocketService {
  // Connection management
  connect(url?: string): Promise<void>;
  disconnect(): void;
  reconnect(): Promise<void>;

  // Subscription management
  subscribe<T = BaseMessage>(
    topic: string,
    callback: (message: T) => void,
    config?: Partial<SubscriptionConfig>
  ): string;
  unsubscribe(subscriptionId: string): void;
  unsubscribeAll(): void;

  // Message sending
  send<T = any>(type: MessageType, data: T): void;

  // State and status
  getConnectionState(): ConnectionState;
  isConnected(): boolean;
  isReconnecting(): boolean;

  // Event listeners
  on(event: 'connect' | 'disconnect' | 'error' | 'reconnect', callback: Function): void;
  off(event: 'connect' | 'disconnect' | 'error' | 'reconnect', callback: Function): void;

  // Utilities
  getSubscriptionIds(): string[];
  getConnectionMetrics(): ConnectionMetrics;
}

// Connection metrics for monitoring
export interface ConnectionMetrics {
  connectedAt?: number;
  disconnectedAt?: number;
  reconnectCount: number;
  messagesReceived: number;
  messagesSent: number;
  lastMessageAt?: number;
  averageLatency: number;
  errors: Array<{
    timestamp: number;
    message: string;
    code?: string;
  }>;
}

// WebSocket event types
export type WebSocketEvent =
  | 'connect'
  | 'disconnect'
  | 'error'
  | 'reconnect'
  | 'message'
  | 'ping'
  | 'pong';

// Message handler type
export type MessageHandler<T = any> = (message: T) => void;

// Error types
export enum WebSocketError {
  CONNECTION_FAILED = 'CONNECTION_FAILED',
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  SUBSCRIPTION_FAILED = 'SUBSCRIPTION_FAILED',
  MESSAGE_PARSE_ERROR = 'MESSAGE_PARSE_ERROR',
  HEARTBEAT_TIMEOUT = 'HEARTBEAT_TIMEOUT',
  MAX_RECONNECT_ATTEMPTS = 'MAX_RECONNECT_ATTEMPTS',
}

// Custom error class
export class WebSocketServiceError extends Error {
  constructor(
    public code: WebSocketError,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'WebSocketServiceError';
  }
}

// Type guards for message types
export const isPriceUpdateMessage = (message: BaseMessage): message is PriceUpdateMessage => {
  return message.type === MessageType.PRICE_UPDATE;
};

export const isOrderBookMessage = (message: BaseMessage): message is OrderBookMessage => {
  return message.type === MessageType.ORDER_BOOK;
};

export const isStrategySignalMessage = (message: BaseMessage): message is StrategySignalMessage => {
  return message.type === MessageType.STRATEGY_SIGNAL;
};

export const isStrategyExecutionMessage = (message: BaseMessage): message is StrategyExecutionMessage => {
  return message.type === MessageType.STRATEGY_EXECUTION;
};

export const isSystemAlertMessage = (message: BaseMessage): message is SystemAlertMessage => {
  return message.type === MessageType.SYSTEM_ALERT;
};