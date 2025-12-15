/**
 * WebSocket Service Tests
 * Unit tests for WebSocket functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketService } from '../services/websocket/WebSocketService';
import { ConnectionState, MessageType, ChannelType } from '../types/websocket';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(public url: string) {}

  send(data: string) {
    // Mock send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
    }
  }

  // Helper method for testing
  open() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  message(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  error() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any;

describe('WebSocketService', () => {
  let service: WebSocketService;
  const mockConfig = {
    url: 'ws://localhost:3004/ws',
    reconnectAttempts: 3,
    reconnectDelay: 100,
    enableLogging: false
  };

  beforeEach(() => {
    service = new WebSocketService(mockConfig);
  });

  afterEach(() => {
    service.destroy();
  });

  it('should create service with default state', () => {
    expect(service.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
  });

  it('should connect successfully', async () => {
    const connectPromise = service.connect();

    // Simulate WebSocket opening
    const ws = (service as any).connectionManager.ws;
    ws.open();

    await connectPromise;

    expect(service.getConnectionState()).toBe(ConnectionState.CONNECTED);
  });

  it('should send messages when connected', async () => {
    await service.connect();

    // Mock WebSocket open
    const ws = (service as any).connectionManager.ws;
    ws.open();

    const message = {
      id: 'test-msg',
      type: MessageType.DATA,
      data: { test: 'data' },
      timestamp: Date.now()
    };

    const result = service.send(message);
    expect(result).toBe(true);
  });

  it('should queue messages when not connected', () => {
    const message = {
      id: 'test-msg',
      type: MessageType.DATA,
      data: { test: 'data' },
      timestamp: Date.now()
    };

    const result = service.send(message);
    expect(result).toBe(true); // Should return true as it's queued
  });

  it('should handle subscriptions correctly', () => {
    const callback = vi.fn();
    const unsubscribe = service.subscribe(ChannelType.STRATEGY_UPDATES, callback);

    expect(typeof unsubscribe).toBe('function');
  });

  it('should handle unsubscribe correctly', () => {
    const callback = vi.fn();
    const unsubscribe = service.subscribe(ChannelType.STRATEGY_UPDATES, callback);

    unsubscribe();

    // Should not error when unsubscribing
    expect(true).toBe(true);
  });

  it('should report connection quality', () => {
    const quality = service.getConnectionQuality();
    expect(['excellent', 'good', 'fair', 'poor']).toContain(quality);
  });

  it('should get network status', () => {
    const status = service.getNetworkStatus();
    expect(typeof status.online).toBe('boolean');
  });

  it('should get connection metrics', () => {
    const metrics = service.getConnectionMetrics();
    expect(typeof metrics.reconnectCount).toBe('number');
    expect(typeof metrics.messagesReceived).toBe('number');
    expect(typeof metrics.messagesSent).toBe('number');
  });
});

describe('WebSocket Message Handling', () => {
  let service: WebSocketService;

  beforeEach(() => {
    service = new WebSocketService({
      url: 'ws://localhost:3004/ws',
      enableLogging: false
    });
  });

  afterEach(() => {
    service.destroy();
  });

  it('should handle incoming messages correctly', async () => {
    const callback = vi.fn();
    service.subscribe(ChannelType.STRATEGY_UPDATES, callback);

    await service.connect();

    // Mock WebSocket and incoming message
    const ws = (service as any).connectionManager.ws;
    ws.open();

    const testMessage = {
      id: 'test-123',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { strategyId: 'test', status: 'active' },
      timestamp: Date.now()
    };

    ws.message(testMessage);

    expect(callback).toHaveBeenCalledWith({ strategyId: 'test', status: 'active' });
  });

  it('should filter messages based on subscription filters', async () => {
    const callback = vi.fn();
    const filters = { active: true };
    service.subscribe(ChannelType.STRATEGY_UPDATES, callback, filters);

    await service.connect();

    const ws = (service as any).connectionManager.ws;
    ws.open();

    // Message that matches filter
    ws.message({
      id: 'test-1',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { active: true, strategyId: 'test1' },
      timestamp: Date.now()
    });

    // Message that doesn't match filter
    ws.message({
      id: 'test-2',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { active: false, strategyId: 'test2' },
      timestamp: Date.now()
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith({ active: true, strategyId: 'test1' });
  });
});