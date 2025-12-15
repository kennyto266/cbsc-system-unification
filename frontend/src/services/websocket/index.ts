/**
 * WebSocket Service Module Index
 * Exports all WebSocket related functionality
 */

// Core service
export { WebSocketService, getWebSocketService } from './WebSocketService';

// Managers
export { ConnectionManager } from './ConnectionManager';
export { MessageQueue } from './MessageQueue';
export { CacheManager } from './CacheManager';
export {
  ReconnectionStrategy,
  ReconnectionStrategies,
  NetworkAwareReconnectionStrategy,
  AdaptiveReconnectionStrategy
} from './ReconnectStrategy';

// Types
export type {
  IWebSocketService,
  WebSocketConfig,
  WebSocketEventCallbacks,
  ConnectionMetrics,
  NetworkStatus,
  SubscriptionRequest,
  MessageTransformer,
  AuthPayload
} from '../../types/websocket';

export {
  MessageType,
  ChannelType,
  ConnectionState,
  WebSocketErrorType
} from '../../types/websocket';