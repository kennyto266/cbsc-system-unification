/**
 * WebSocket Service Module Exports
 * Central export point for all WebSocket related functionality
 */

export { default as WebSocketService } from './websocket-service';
export { createWebSocketService, getWebSocketService } from './websocket-service';
export * from '../websocket-manager';
export * from '../../types/socket';

// Re-export Socket.io client for direct usage if needed
export { io } from 'socket.io-client';