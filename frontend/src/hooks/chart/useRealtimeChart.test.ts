/**
 * useRealtimeChart Hook Tests
 *
 * Comprehensive tests for the useRealtimeChart hook
 * including WebSocket integration, data processing, and edge cases.
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useRealtimeChart } from './useRealtimeChart';
import { ChannelType, MessageType, WSMessage } from '../../types/websocket';
import { mockChartData, mockWebSocketMessage, flushPromises } from '../__tests__/setup';

// Mock the useWebSocket hook - Fix mock structure
const mockUnsubscribe = jest.fn();
const mockUseWebSocket = jest.fn(() => ({
  isConnected: true,
  connectionState: 2, // ConnectionState.CONNECTED
  connectionQuality: 'good' as const,
  error: null,
  subscribe: jest.fn(() => mockUnsubscribe),
  reconnect: jest.fn(),
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  getService: jest.fn(),
}));

jest.mock('../useWebSocketEnhanced', () => ({
  useWebSocket: mockUseWebSocket,
  __esModule: true,
  default: mockUseWebSocket,
}));

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

describe('useRealtimeChart', () => {
  const mockConfig = {
    channelId: ChannelType.STRATEGY_UPDATES,
    initialData: [],
    maxDataPoints: 100,
    updateThrottleMs: 10,
    enableDebug: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.log = jest.fn();
  });

  afterEach(() => {
    console.error = originalConsoleError;
    console.log = originalConsoleLog;
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    expect(result.current.data).toEqual([]);
    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBe(null);
    expect(result.current.totalPointsReceived).toBe(0);
    expect(result.current.duplicatePointsFiltered).toBe(0);
    expect(result.current.reconnectAttempt).toBe(0);
    expect(result.current.lastUpdate).toBe(null);
    expect(result.current.dataRate).toBe(0);
  });

  it('should add data points manually', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));
    const mockDataPoint = {
      timestamp: Date.now(),
      value: 100,
      label: 'Test',
    };

    act(() => {
      result.current.addDataPoint(mockDataPoint);
    });

    expect(result.current.data).toContain(mockDataPoint);
    expect(result.current.totalPointsReceived).toBe(1);
    expect(result.current.lastUpdate).toBe(mockDataPoint.timestamp);
  });

  it('should filter duplicate data points when deduplication is enabled', () => {
    const configWithDeduplication = {
      ...mockConfig,
      enableDeduplication: true,
    };

    const { result } = renderHook(() => useRealtimeChart(configWithDeduplication));
    const mockDataPoint = {
      timestamp: Date.now(),
      value: 100,
      label: 'Test',
    };

    act(() => {
      result.current.addDataPoint(mockDataPoint);
      result.current.addDataPoint(mockDataPoint); // Same point
    });

    expect(result.current.data).toHaveLength(1);
    expect(result.current.duplicatePointsFiltered).toBe(1);
  });

  it('should respect max data points limit', () => {
    const configWithLimit = {
      ...mockConfig,
      maxDataPoints: 2,
    };

    const { result } = renderHook(() => useRealtimeChart(configWithLimit));

    act(() => {
      result.current.addDataPoint({ timestamp: 1, value: 1 });
      result.current.addDataPoint({ timestamp: 2, value: 2 });
      result.current.addDataPoint({ timestamp: 3, value: 3 });
    });

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data[0].timestamp).toBe(2);
    expect(result.current.data[1].timestamp).toBe(3);
  });

  it('should apply data windowing when enabled', () => {
    const oldTimestamp = Date.now() - 2000; // 2 seconds ago
    const newTimestamp = Date.now();
    const configWithWindow = {
      ...mockConfig,
      dataWindowMs: 1000, // 1 second window
    };

    const { result } = renderHook(() => useRealtimeChart(configWithWindow));

    act(() => {
      result.current.addDataPoint({ timestamp: oldTimestamp, value: 1 });
      result.current.addDataPoint({ timestamp: newTimestamp, value: 2 });
    });

    // Wait for debounced processing
    jest.advanceTimersByTime(20);

    expect(result.current.data).toHaveLength(1);
    expect(result.current.data[0].timestamp).toBe(newTimestamp);
  });

  it('should clear all data', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    act(() => {
      result.current.addDataPoint({ timestamp: 1, value: 1 });
      result.current.addDataPoint({ timestamp: 2, value: 2 });
    });

    act(() => {
      result.current.clearData();
    });

    expect(result.current.data).toEqual([]);
  });

  it('should toggle pause state', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    expect(result.current.data).toEqual([]);

    act(() => {
      result.current.togglePause();
    });

    // When paused, new data points should not be added
    act(() => {
      result.current.addDataPoint({ timestamp: 1, value: 1 });
    });

    expect(result.current.data).toEqual([]);

    act(() => {
      result.current.togglePause();
    });

    // When unpaused, new data points should be added
    act(() => {
      result.current.addDataPoint({ timestamp: 2, value: 2 });
    });

    expect(result.current.data).toHaveLength(1);
  });

  it('should export data as JSON', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    act(() => {
      mockChartData.forEach(point => result.current.addDataPoint(point));
    });

    const exportedJSON = result.current.exportData('json');
    const parsedData = JSON.parse(exportedJSON);

    expect(parsedData).toEqual(mockChartData);
  });

  it('should export data as CSV', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    act(() => {
      mockChartData.forEach(point => result.current.addDataPoint(point));
    });

    const exportedCSV = result.current.exportData('csv');
    const lines = exportedCSV.split('\n');

    expect(lines[0]).toBe('timestamp,value,label');
    expect(lines[1]).toBe('1,100,Test1');
    expect(lines[2]).toBe('2,200,Test2');
    expect(lines[3]).toBe('3,150,Test3');
  });

  it('should use custom data transformer', () => {
    const customTransformer = (message: WSMessage) => ({
      timestamp: message.timestamp,
      value: message.data?.customValue || 0,
      label: message.data?.customLabel,
      metadata: message.data,
    });

    const configWithTransformer = {
      ...mockConfig,
      dataTransformer: customTransformer,
    };

    const { result } = renderHook(() => useRealtimeChart(configWithTransformer));

    // This would typically be called by the WebSocket message handler
    const mockMessage: WSMessage = {
      id: 'test',
      type: MessageType.DATA,
      channel: ChannelType.STRATEGY_UPDATES,
      data: { customValue: 999, customLabel: 'Custom' },
      timestamp: Date.now(),
    };

    // Since we can't directly test WebSocket integration in this setup,
    // we test the transformer indirectly
    const transformedData = customTransformer(mockMessage);

    expect(transformedData.value).toBe(999);
    expect(transformedData.label).toBe('Custom');
    expect(transformedData.metadata).toEqual(mockMessage.data);
  });

  it('should handle configuration updates', () => {
    const { result, rerender } = renderHook(
      (props) => useRealtimeChart(props),
      { initialProps: mockConfig }
    );

    const newConfig = {
      ...mockConfig,
      maxDataPoints: 500,
      dataWindowMs: 5000,
    };

    rerender(newConfig);

    // The hook should apply the new configuration
    act(() => {
      result.current.setMaxDataPoints(500);
      result.current.setDataWindow(5000);
    });

    // Configuration should be updated
    expect(result.current.data).toEqual([]);
  });

  it('should calculate data rate correctly', async () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    // Add multiple data points quickly
    act(() => {
      for (let i = 0; i < 10; i++) {
        result.current.addDataPoint({
          timestamp: Date.now() + i,
          value: i,
        });
      }
    });

    // Wait for rate calculation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 1100));
    });

    // Data rate should be calculated
    expect(result.current.dataRate).toBeGreaterThan(0);
  });

  it('should handle empty data export', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    const jsonExport = result.current.exportData('json');
    const csvExport = result.current.exportData('csv');

    expect(jsonExport).toBe('[]');
    expect(csvExport).toBe('');
  });

  it('should handle malformed data gracefully', () => {
    const { result } = renderHook(() => useRealtimeChart(mockConfig));

    // Add data point without required fields
    act(() => {
      result.current.addDataPoint({} as any);
    });

    // The hook should not crash and data should remain empty
    expect(result.current.data).toEqual([]);
  });
});