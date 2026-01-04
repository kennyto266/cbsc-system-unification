/**
 * useWebSocketEnhanced Hook Tests
 *
 * Comprehensive tests for the useWebSocketEnhanced hook including
 * connection management, subscriptions, and error handling.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useWebSocket, UseWebSocketOptions } from '../useWebSocketEnhanced';
import { WebSocketService, ConnectionState, ChannelType, MessageType } from '../../services/websocket/WebSocketService';

// Mock WebSocketService
jest.mock('../../services/websocket/WebSocketService', () => ({
  WebSocketService: jest.fn().mockImplementation(() => ({
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
    send: jest.fn().mockReturnValue(true),
    subscribe: jest.fn().mockReturnValue(jest.fn()),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    getConnectionQuality: jest.fn().mockReturnValue('good'),
  })),
  getWebSocketService: jest.fn(),
  ConnectionState: {
    DISCONNECTED: 'DISCONNECTED',
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    RECONNECTING: 'RECONNECTING',
    ERROR: 'ERROR',
  },
  ChannelType: {
    STRATEGY_UPDATES: 'STRATEGY_UPDATES',
    MARKET_DATA: 'MARKET_DATA',
    SYSTEM_ALERTS: 'SYSTEM_ALERTS',
    USER_NOTIFICATIONS: 'USER_NOTIFICATIONS',
  },
  MessageType: {
    CONNECT: 'CONNECT',
    DISCONNECT: 'DISCONNECT',
    DATA: 'DATA',
    ERROR: 'ERROR',
    PING: 'PING',
    PONG: 'PONG',
  },
}));

describe('useWebSocket', () => {
  let mockWebSocketService: jest.Mocked<WebSocketService>;

  beforeEach(() => {
    jest.clearAllMocks();

    // Create a fresh mock instance for each test
    mockWebSocketService = new WebSocketService() as jest.Mocked<WebSocketService>;
    mockWebSocketService.connect = jest.fn().mockResolvedValue(undefined);
    mockWebSocketService.disconnect = jest.fn();
    mockWebSocketService.send = jest.fn().mockReturnValue(true);
    mockWebSocketService.subscribe = jest.fn().mockReturnValue(jest.fn());
    mockWebSocketService.addEventListener = jest.fn();
    mockWebSocketService.removeEventListener = jest.fn();
    mockWebSocketService.getConnectionQuality = jest.fn().mockReturnValue('good');

    (require('../../services/websocket/WebSocketService').getWebSocketService as any).mockReturnValue(
      mockWebSocketService
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionState).toBe(ConnectionState.DISCONNECTED);
    expect(result.current.connectionQuality).toBe('good');
    expect(result.current.error).toBe(null);
    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
    expect(typeof result.current.send).toBe('function');
    expect(typeof result.current.subscribe).toBe('function');
    expect(typeof result.current.getService).toBe('function');
  });

  it('should use provided configuration', () => {
    const config = {
      url: 'ws://localhost:8080',
      reconnectAttempts: 5,
      reconnectInterval: 1000,
    };

    renderHook(() => useWebSocket(config));

    expect(
      require('../../services/websocket/WebSocketService').getWebSocketService
    ).toHaveBeenCalledWith(config);
  });

  it('should auto-connect when autoConnect is true', async () => {
    const options: UseWebSocketOptions = {
      autoConnect: true,
    };

    renderHook(() => useWebSocket(undefined, options));

    // Should attempt to connect
    await waitFor(() => {
      expect(mockWebSocketService.connect).toHaveBeenCalled();
    });
  });

  it('should not auto-connect when autoConnect is false', () => {
    const options: UseWebSocketOptions = {
      autoConnect: false,
    };

    renderHook(() => useWebSocket(undefined, options));

    expect(mockWebSocketService.connect).not.toHaveBeenCalled();
  });

  it('should call connect function', async () => {
    const { result } = renderHook(() => useWebSocket(undefined, { autoConnect: false }));

    await act(async () => {
      await result.current.connect();
    });

    expect(mockWebSocketService.connect).toHaveBeenCalled();
  });

  it('should handle connection error', async () => {
    const error = new Error('Connection failed');
    mockWebSocketService.connect.mockRejectedValue(error);

    const options: UseWebSocketOptions = {
      autoConnect: true,
      onError: jest.fn(),
    };

    const { result } = renderHook(() => useWebSocket(undefined, options));

    await waitFor(() => {
      expect(result.current.error).toBe(error);
      expect(options.onError).toHaveBeenCalledWith(error);
    });
  });

  it('should call disconnect function', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      result.current.disconnect();
    });

    expect(mockWebSocketService.disconnect).toHaveBeenCalled();
  });

  it('should send message', () => {
    const { result } = renderHook(() => useWebSocket());
    const message = {
      id: 'test',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { value: 123 },
      timestamp: Date.now(),
    };

    act(() => {
      const sent = result.current.send(message);
      expect(sent).toBe(true);
    });

    expect(mockWebSocketService.send).toHaveBeenCalledWith(message);
  });

  it('should subscribe to channel', () => {
    const { result } = renderHook(() => useWebSocket());
    const callback = jest.fn();
    const filters = { strategyId: '123' };

    act(() => {
      const unsubscribe = result.current.subscribe(
        ChannelType.STRATEGY_UPDATES,
        callback,
        filters
      );
      expect(typeof unsubscribe).toBe('function');
    });

    expect(mockWebSocketService.subscribe).toHaveBeenCalledWith(
      ChannelType.STRATEGY_UPDATES,
      callback,
      filters
    );
  });

  it('should track and clean up subscriptions on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());
    const callback1 = jest.fn();
    const callback2 = jest.fn();

    // Get subscription tracking
    let unsubscribe1: (() => void) | undefined;
    let unsubscribe2: (() => void) | undefined;

    act(() => {
      unsubscribe1 = mockWebSocketService.subscribe(
        ChannelType.STRATEGY_UPDATES,
        callback1
      );
      unsubscribe2 = mockWebSocketService.subscribe(
        ChannelType.MARKET_DATA,
        callback2
      );
    });

    // Mock subscription return values
    const mockUnsubscribe1 = jest.fn();
    const mockUnsubscribe2 = jest.fn();
    mockWebSocketService.subscribe
      .mockReturnValueOnce(mockUnsubscribe1)
      .mockReturnValueOnce(mockUnsubscribe2);

    unmount();

    // Subscriptions should be cleaned up
    expect(mockUnsubscribe1).toHaveBeenCalled();
    expect(mockUnsubscribe2).toHaveBeenCalled();
  });

  it('should handle connection events', () => {
    const options: UseWebSocketOptions = {
      onConnect: jest.fn(),
      onDisconnect: jest.fn(),
      onError: jest.fn(),
    };

    renderHook(() => useWebSocket(undefined, options));

    expect(mockWebSocketService.addEventListener).toHaveBeenCalledWith(
      'onConnect',
      expect.any(Function)
    );
    expect(mockWebSocketService.addEventListener).toHaveBeenCalledWith(
      'onDisconnect',
      expect.any(Function)
    );
    expect(mockWebSocketService.addEventListener).toHaveBeenCalledWith(
      'onError',
      expect.any(Function)
    );
    expect(mockWebSocketService.addEventListener).toHaveBeenCalledWith(
      'onStateChange',
      expect.any(Function)
    );
    expect(mockWebSocketService.addEventListener).toHaveBeenCalledWith(
      'onLatencyUpdate',
      expect.any(Function)
    );
  });

  it('should update connection state on connect', () => {
    const { result } = renderHook(() => useWebSocket(undefined, { autoConnect: false }));

    // Get the connect handler
    const connectHandler = mockWebSocketService.addEventListener.mock.calls.find(
      ([event]) => event === 'onConnect'
    )![1];

    act(() => {
      connectHandler();
    });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionState).toBe(ConnectionState.CONNECTED);
    expect(result.current.error).toBe(null);
  });

  it('should update connection state on disconnect', () => {
    const { result } = renderHook(() => useWebSocket());

    // Get the disconnect handler
    const disconnectHandler = mockWebSocketService.addEventListener.mock.calls.find(
      ([event]) => event === 'onDisconnect'
    )![1];

    act(() => {
      disconnectHandler();
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionState).toBe(ConnectionState.DISCONNECTED);
  });

  it('should update connection state on error', () => {
    const { result } = renderHook(() => useWebSocket());
    const error = new Error('Test error');

    // Get the error handler
    const errorHandler = mockWebSocketService.addEventListener.mock.calls.find(
      ([event]) => event === 'onError'
    )![1];

    act(() => {
      errorHandler(error);
    });

    expect(result.current.error).toBe(error);
    expect(result.current.connectionState).toBe(ConnectionState.ERROR);
  });

  it('should handle state changes', () => {
    const { result } = renderHook(() => useWebSocket());

    // Get the state change handler
    const stateChangeHandler = mockWebSocketService.addEventListener.mock.calls.find(
      ([event]) => event === 'onStateChange'
    )![1];

    act(() => {
      stateChangeHandler(ConnectionState.DISCONNECTED, ConnectionState.CONNECTING);
    });

    expect(result.current.connectionState).toBe(ConnectionState.CONNECTING);
    expect(result.current.isConnected).toBe(false);

    act(() => {
      stateChangeHandler(ConnectionState.CONNECTING, ConnectionState.CONNECTED);
    });

    expect(result.current.connectionState).toBe(ConnectionState.CONNECTED);
    expect(result.current.isConnected).toBe(true);
  });

  it('should update connection quality', () => {
    const { result } = renderHook(() => useWebSocket());
    mockWebSocketService.getConnectionQuality = jest.fn().mockReturnValue('excellent');

    // Get the quality change handler
    const qualityHandler = mockWebSocketService.addEventListener.mock.calls.find(
      ([event]) => event === 'onLatencyUpdate'
    )![1];

    act(() => {
      qualityHandler();
    });

    expect(result.current.connectionQuality).toBe('excellent');
  });

  it('should get service instance', () => {
    const { result } = renderHook(() => useWebSocket());

    const service = result.current.getService();

    expect(service).toBe(mockWebSocketService);
  });

  it('should clean up event listeners on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());

    unmount();

    expect(mockWebSocketService.removeEventListener).toHaveBeenCalledWith(
      'onConnect',
      expect.any(Function)
    );
    expect(mockWebSocketService.removeEventListener).toHaveBeenCalledWith(
      'onDisconnect',
      expect.any(Function)
    );
    expect(mockWebSocketService.removeEventListener).toHaveBeenCalledWith(
      'onError',
      expect.any(Function)
    );
    expect(mockWebSocketService.removeEventListener).toHaveBeenCalledWith(
      'onStateChange',
      expect.any(Function)
    );
    expect(mockWebSocketService.removeEventListener).toHaveBeenCalledWith(
      'onLatencyUpdate',
      expect.any(Function)
    );
  });

  it('should handle multiple subscriptions with cleanup', () => {
    const { result } = renderHook(() => useWebSocket());
    const callbacks = Array.from({ length: 3 }, () => jest.fn());

    const unsubscribes: (() => void)[] = [];

    // Mock subscription returns
    const mockUnsubscribes = callbacks.map(() => jest.fn());
    mockWebSocketService.subscribe
      .mockReturnValueOnce(mockUnsubscribes[0])
      .mockReturnValueOnce(mockUnsubscribes[1])
      .mockReturnValueOnce(mockUnsubscribes[2]);

    act(() => {
      unsubscribes.push(
        result.current.subscribe(ChannelType.STRATEGY_UPDATES, callbacks[0])
      );
      unsubscribes.push(
        result.current.subscribe(ChannelType.MARKET_DATA, callbacks[1])
      );
      unsubscribes.push(
        result.current.subscribe(ChannelType.STRATEGY_UPDATES, callbacks[2])
      );
    });

    expect(mockWebSocketService.subscribe).toHaveBeenCalledTimes(3);

    // Unsubscribe from one
    act(() => {
      unsubscribes[1]();
    });

    expect(mockUnsubscribes[1]).toHaveBeenCalled();

    // Cleanup should call remaining unsubscribes
    expect(mockUnsubscribes[0]).not.toHaveBeenCalled();
    expect(mockUnsubscribes[2]).not.toHaveBeenCalled();
  });

  it('should handle send failure', () => {
    mockWebSocketService.send.mockReturnValue(false);

    const { result } = renderHook(() => useWebSocket());
    const message = {
      id: 'test',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { value: 123 },
      timestamp: Date.now(),
    };

    act(() => {
      const sent = result.current.send(message);
      expect(sent).toBe(false);
    });
  });

  it('should work without WebSocket configuration', () => {
    const { result } = renderHook(() => useWebSocket(undefined));

    expect(result.current).toBeDefined();
    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
    expect(typeof result.current.send).toBe('function');
    expect(typeof result.current.subscribe).toBe('function');
  });
});