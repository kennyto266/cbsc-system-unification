/**
 * WebSocket Service Unit Tests
 * Tests core WebSocket functionality including reconnection and error handling
 */

import { WebSocketService, createWebSocketService, WebSocketError } from '../websocket-service';
import { MessageType, ConnectionState, BaseMessage } from '@/types/socket';

// Mock Socket.io
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    connected: false,
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
    removeAllListeners: jest.fn(),
    once: jest.fn(),
  })),
}));

// Mock UUID
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'test-uuid-123'),
}));

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockSocket: any;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    mockSocket = {
      connected: false,
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      removeAllListeners: jest.fn(),
      once: jest.fn(),
    };

    const { io } = require('socket.io-client');
    io.mockReturnValue(mockSocket);

    service = new WebSocketService({
      url: 'ws://localhost:3004',
      debug: false,
      reconnectAttempts: 3,
      reconnectDelay: 100,
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    service.destroy();
  });

  describe('Connection Management', () => {
    it('should initialize with disconnected state', () => {
      expect(service.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
      expect(service.isConnected()).toBe(false);
      expect(service.isReconnecting()).toBe(false);
    });

    it('should connect successfully', async () => {
      // Simulate successful connection
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });

      await service.connect();

      expect(service.getConnectionState()).toBe(ConnectionState.CONNECTED);
      expect(service.isConnected()).toBe(true);
    });

    it('should handle connection failure', async () => {
      const error = new Error('Connection failed');
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect_error') {
          setTimeout(() => callback(error), 0);
        }
      });

      await expect(service.connect()).rejects.toThrow('Connection failed');
      expect(service.getConnectionState()).toBe(ConnectionState.ERROR);
    });

    it('should disconnect properly', async () => {
      // Connect first
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });
      await service.connect();

      // Then disconnect
      service.disconnect();

      expect(mockSocket.disconnect).toHaveBeenCalled();
      expect(service.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
    });

    it('should attempt reconnection on disconnect', async () => {
      jest.useFakeTimers();

      // Connect first
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });
      await service.connect();

      // Simulate disconnect
      mockSocket.connected = false;
      const disconnectCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'disconnect'
      )?.[1];
      if (disconnectCallback) {
        disconnectCallback('server disconnect');
      }

      expect(service.getConnectionState()).toBe(ConnectionState.RECONNECTING);

      // Fast-forward time for reconnection attempt
      jest.advanceTimersByTime(100);

      expect(mockSocket.disconnect).toHaveBeenCalled();

      jest.useRealTimers();
    });

    it('should stop reconnecting after max attempts', async () => {
      jest.useFakeTimers();

      service = new WebSocketService({
        url: 'ws://localhost:3004',
        reconnectAttempts: 2,
        reconnectDelay: 100,
      });

      // Mock connection to always fail
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect_error') {
          setTimeout(() => callback(new Error('Always fails')), 0);
        }
      });

      // Try to connect
      try {
        await service.connect();
      } catch (e) {
        // Expected to fail
      }

      // Fast-forward through reconnection attempts
      jest.advanceTimersByTime(100);
      jest.advanceTimersByTime(200);

      expect(service.getConnectionState()).toBe(ConnectionState.ERROR);

      jest.useRealTimers();
    });
  });

  describe('Subscription Management', () => {
    beforeEach(async () => {
      // Connect before testing subscriptions
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });
      await service.connect();
    });

    it('should subscribe to a topic', () => {
      const callback = jest.fn();
      const subscriptionId = service.subscribe('test-topic', callback);

      expect(subscriptionId).toBeTruthy();
      expect(service.getSubscriptionIds()).toContain(subscriptionId);
    });

    it('should receive messages for subscribed topic', () => {
      const callback = jest.fn();
      service.subscribe('price_update', callback);

      const message: BaseMessage = {
        id: 'msg-123',
        type: MessageType.PRICE_UPDATE,
        timestamp: Date.now(),
        data: { symbol: 'BTC', price: 50000 },
      };

      // Simulate receiving message
      const messageCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageCallback) {
        messageCallback(message);
      }

      expect(callback).toHaveBeenCalledWith(message);
    });

    it('should unsubscribe from a topic', () => {
      const callback = jest.fn();
      const subscriptionId = service.subscribe('test-topic', callback);

      service.unsubscribe(subscriptionId);

      expect(service.getSubscriptionIds()).not.toContain(subscriptionId);
    });

    it('should unsubscribe from all topics', () => {
      service.subscribe('topic1', jest.fn());
      service.subscribe('topic2', jest.fn());
      service.subscribe('topic3', jest.fn());

      expect(service.getSubscriptionIds()).toHaveLength(3);

      service.unsubscribeAll();

      expect(service.getSubscriptionIds()).toHaveLength(0);
    });

    it('should apply subscription filter', () => {
      const callback = jest.fn();
      service.subscribe('price_update', callback, {
        filter: (message: BaseMessage) => {
          return message.data.symbol === 'BTC';
        },
      });

      const btcMessage: BaseMessage = {
        id: 'msg-1',
        type: MessageType.PRICE_UPDATE,
        timestamp: Date.now(),
        data: { symbol: 'BTC', price: 50000 },
      };

      const ethMessage: BaseMessage = {
        id: 'msg-2',
        type: MessageType.PRICE_UPDATE,
        timestamp: Date.now(),
        data: { symbol: 'ETH', price: 3000 },
      };

      const messageCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageCallback) {
        messageCallback(btcMessage);
        messageCallback(ethMessage);
      }

      expect(callback).toHaveBeenCalledTimes(1);
      expect(callback).toHaveBeenCalledWith(btcMessage);
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });
      await service.connect();
    });

    it('should send messages when connected', () => {
      service.send(MessageType.HEARTBEAT, { timestamp: Date.now() });

      expect(mockSocket.emit).toHaveBeenCalledWith('message', expect.objectContaining({
        type: MessageType.HEARTBEAT,
        id: 'test-uuid-123',
        timestamp: expect.any(Number),
      }));
    });

    it('should queue messages when disconnected', () => {
      service.disconnect();
      service.send(MessageType.HEARTBEAT, { timestamp: Date.now() });

      expect(mockSocket.emit).not.toHaveBeenCalled();

      // Reconnect and verify queued message is sent
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect') {
          setTimeout(callback, 0);
          mockSocket.connected = true;
        }
      });

      service.connect().then(() => {
        expect(mockSocket.emit).toHaveBeenCalled();
      });
    });

    it('should handle heartbeat messages', () => {
      const heartbeatMessage: BaseMessage = {
        id: 'heartbeat-123',
        type: MessageType.HEARTBEAT,
        timestamp: Date.now(),
      };

      const messageCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageCallback) {
        messageCallback(heartbeatMessage);
      }

      // Should not pass heartbeat to regular subscribers
      expect(mockSocket.emit).not.toHaveBeenCalledWith(
        'message',
        expect.objectContaining({ type: MessageType.HEARTBEAT })
      );
    });
  });

  describe('Event Listeners', () => {
    it('should add and remove event listeners', () => {
      const connectHandler = jest.fn();
      const disconnectHandler = jest.fn();

      service.on('connect', connectHandler);
      service.on('disconnect', disconnectHandler);

      // Trigger events
      const connectCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'connect'
      )?.[1];
      if (connectCallback) {
        connectCallback();
      }
      expect(connectHandler).toHaveBeenCalled();

      const disconnectCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'disconnect'
      )?.[1];
      if (disconnectCallback) {
        disconnectCallback();
      }
      expect(disconnectHandler).toHaveBeenCalled();

      // Remove listeners
      service.off('connect', connectHandler);
      service.off('disconnect', disconnectHandler);
    });
  });

  describe('Connection Metrics', () => {
    it('should track connection metrics', () => {
      const metrics = service.getConnectionMetrics();

      expect(metrics).toHaveProperty('reconnectCount');
      expect(metrics).toHaveProperty('messagesReceived');
      expect(metrics).toHaveProperty('messagesSent');
      expect(metrics).toHaveProperty('averageLatency');
      expect(metrics).toHaveProperty('errors');
    });

    it('should update metrics on message send/receive', async () => {
      await service.connect();

      const initialMetrics = service.getConnectionMetrics();

      // Send message
      service.send(MessageType.HEARTBEAT, {});

      // Receive message
      const message: BaseMessage = {
        id: 'msg-123',
        type: MessageType.PRICE_UPDATE,
        timestamp: Date.now(),
      };

      const messageCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageCallback) {
        messageCallback(message);
      }

      const updatedMetrics = service.getConnectionMetrics();

      expect(updatedMetrics.messagesSent).toBe(initialMetrics.messagesSent + 1);
      expect(updatedMetrics.messagesReceived).toBe(initialMetrics.messagesReceived + 1);
    });
  });

  describe('Error Handling', () => {
    it('should handle service errors gracefully', async () => {
      const errorHandler = jest.fn();
      service.on('error', errorHandler);

      // Simulate connection error
      mockSocket.once.mockImplementation((event, callback) => {
        if (event === 'connect_error') {
          setTimeout(() => callback(new Error('Test error')), 0);
        }
      });

      try {
        await service.connect();
      } catch (e) {
        // Expected
      }

      expect(service.getConnectionState()).toBe(ConnectionState.ERROR);
    });

    it('should handle malformed messages', async () => {
      await service.connect();

      const callback = jest.fn();
      service.subscribe('test', callback);

      // Simulate malformed message
      const messageCallback = mockSocket.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageCallback) {
        // Send null/undefined
        messageCallback(null);
        messageCallback(undefined);
        // Send object without required fields
        messageCallback({});
      }

      // Should not crash
      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('Factory Functions', () => {
    it('should create WebSocket service through factory', () => {
      const config = {
        url: 'ws://test.com',
        debug: true,
      };

      const service = createWebSocketService(config);

      expect(service).toBeInstanceOf(WebSocketService);
    });

    it('should return existing service from getWebSocketService', () => {
      const config = {
        url: 'ws://test.com',
      };

      const service1 = createWebSocketService(config);
      const service2 = require('../websocket-service').getWebSocketService();

      expect(service1).toBe(service2);
    });
  });
});