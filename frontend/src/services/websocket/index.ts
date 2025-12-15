/**
 * WebSocket Service Module Index
 * Exports all WebSocket related functionality
 */

// Core services
export { WebSocketService, getWebSocketService } from './WebSocketService';
export { EnhancedWebSocketService, enhancedWS } from './EnhancedWebSocketService';

// Legacy manager
export { WebSocketManager, wsManager } from '../websocketManager';

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

// Hooks
export { useWebSocketService } from '../../hooks/useWebSocketService';
export { useRealTimeMarketData } from '../../hooks/useRealTimeMarketData';
export { useRealTimeStrategyUpdates } from '../../hooks/useRealTimeStrategyUpdates';

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