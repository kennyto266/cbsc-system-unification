/**
 * useChartExport Hook Tests
 *
 * Comprehensive tests for the useChartExport hook
 * including export functionality for different formats and chart types.
 */

import React from 'react';
import { renderHook, act, waitFor, cleanup } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useChartExport } from './useChartExport';

// Mock document.createElement to control element creation
const originalCreateElement = document.createElement;
const mockCanvas = {
  width: 800,
  height: 600,
  getContext: jest.fn((contextType: string) => {
    if (contextType === '2d') {
      return {
        scale: jest.fn(),
        drawImage: jest.fn(),
        fillRect: jest.fn(),
        fillStyle: '',
      };
    }
    return null;
  }),
  toBlob: jest.fn((callback) => {
    callback(new Blob(['mock-image'], { type: 'image/png' }));
  }),
  remove: jest.fn(),
};

const mockSVGElement = {
  querySelector: jest.fn(() => ({
    outerHTML: '<svg></svg>',
  })),
  offsetWidth: 800,
  offsetHeight: 600,
};

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

describe('useChartExport', () => {
  const mockRef = { current: null } as React.RefObject<HTMLCanvasElement>;
  const mockData = [
    { timestamp: 1, value: 100, label: 'Test1' },
    { timestamp: 2, value: 200, label: 'Test2' },
    { timestamp: 3, value: 150, label: 'Test3' },
  ];

  // Helper to create a fresh canvas mock
  const createMockCanvas = () => ({
    width: 800,
    height: 600,
    getContext: jest.fn((contextType: string) => {
      if (contextType === '2d') {
        return {
          scale: jest.fn(),
          drawImage: jest.fn(),
          fillRect: jest.fn(),
          fillStyle: '',
        };
      }
      return null;
    }),
    toBlob: jest.fn((callback) => {
      callback(new Blob(['mock-image'], { type: 'image/png' }));
    }),
    remove: jest.fn(),
  });

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    console.error = jest.fn();
    console.log = jest.fn();

    // Reset mock ref
    mockRef.current = null;

    // Mock createElement to return fresh canvas instances
    document.createElement = jest.fn((tagName: string) => {
      if (tagName === 'canvas') {
        return createMockCanvas() as any;
      }
      if (tagName === 'a') {
        // Create real DOM element but mock click
        const link = originalCreateElement.call(document, 'a') as HTMLAnchorElement;
        link.click = jest.fn();
        return link;
      }
      return originalCreateElement.call(document, tagName);
    }) as any;
  });

  afterEach(() => {
    cleanup(); // Clean up all rendered hooks
    jest.useRealTimers();
    console.error = originalConsoleError;
    console.log = originalConsoleLog;
    document.createElement = originalCreateElement;
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
    }));

    expect(result.current.isExporting).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.exportHistory).toEqual([]);
  });

  it('should export ChartJS canvas to PNG', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
      data: mockData,
    }));

    act(() => {
      result.current.exportToPNG();
    });

    // Wait for async operations
    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    // Check export was recorded in history
    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('png');
  });

  it('should export ChartJS canvas to JPG with custom options', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
      data: mockData,
    }));

    const options = {
      width: 1920,
      height: 1080,
      quality: 0.8,
      filename: 'custom-chart',
    };

    act(() => {
      result.current.exportToJPG(options);
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    // Check export was recorded in history with correct format
    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('jpg');
  });

  it('should handle custom export function', async () => {
    mockRef.current = mockCanvas as any;

    const customExportFunction = jest.fn().mockResolvedValue(
      new Blob(['custom-export'], { type: 'image/png' })
    );

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      customExportFunction,
    }));

    await act(async () => {
      try {
        await result.current.exportToPNG();
      } catch (e) { /* ignore */ }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(customExportFunction).toHaveBeenCalledWith('png', expect.any(Object));
    expect(result.current.exportHistory).toHaveLength(1);
  });

  it('should handle export errors', async () => {
    mockRef.current = null; // No chart element

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
    }));

    await act(async () => {
      try {
        await result.current.exportToPNG();
      } catch (e) {
        // Error expected - should be caught by hook
      }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    // The error should have been caught and stored in state
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Chart reference is null');
  });

  it('should prevent concurrent exports', async () => {
    mockRef.current = mockCanvas as any;

    // Make toBlob async to simulate export taking time
    mockCanvas.toBlob = jest.fn((callback) => {
      setTimeout(() => callback(new Blob(['mock-image'])), 100);
    }) as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    // Start first export (don't await)
    act(() => {
      result.current.exportToPNG();
    });

    // Immediately try to export again - should be rejected due to concurrent export
    await act(async () => {
      try {
        await result.current.exportToJPG();
      } catch (e) {
        // Error expected
      }
    });

    // Wait for the async operations to complete
    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    // The error should have been caught and stored in state
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Export already in progress');
  });

  it('should get chart as blob without downloading', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    let blob: Blob | null = null;

    await act(async () => {
      try {
        blob = await result.current.getChartBlob('png');
      } catch (e) {
        // ignore
      }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(blob).toBeInstanceOf(Blob);
    // getChartBlob calls performExport which adds to history
    expect(result.current.exportHistory).toHaveLength(1);
  });

  it('should clear export history', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    // Simulate some exports
    await act(async () => {
      try {
        await result.current.exportToPNG();
      } catch (e) { /* ignore */ }
      try {
        await result.current.exportToJPG();
      } catch (e) { /* ignore */ }
    });

    // Wait for async operations
    await waitFor(() => {
      expect(result.current.exportHistory.length).toBeGreaterThan(0);
    });

    act(() => {
      result.current.clearHistory();
    });

    expect(result.current.exportHistory).toEqual([]);
  });

  it('should use custom filename', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
      filename: 'my-custom-chart',
    }));

    await act(async () => {
      try {
        await result.current.exportToPNG();
      } catch (e) { /* ignore */ }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    const exportRecord = result.current.exportHistory[0];
    expect(exportRecord.filename).toMatch(/^my-custom-chart-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.png$/);
  });

  it('should handle empty data export', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      data: [],
    }));

    await act(async () => {
      try {
        await result.current.exportToCSV();
      } catch (e) { /* ignore */ }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.exportHistory).toHaveLength(1);
  });

  it('should handle unsupported chart types', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'unsupported' as any,
    }));

    await act(async () => {
      try {
        await result.current.exportToPNG();
      } catch (e) { /* ignore */ }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Unsupported chart type');
  });

  it('should apply scaling to canvas export', async () => {
    mockRef.current = mockCanvas as any;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    const mockScaledCanvas = {
      width: 1600,
      height: 1200,
      getContext: jest.fn(() => ({
        scale: jest.fn(),
        drawImage: jest.fn(),
      })),
      toBlob: jest.fn((callback) => {
        callback(new Blob(['mock-image'], { type: 'image/png' }));
      }),
      remove: jest.fn(),
    };

    // Mock createElement to return scaled canvas
    document.createElement = jest.fn((tagName: string) => {
      if (tagName === 'canvas') {
        return mockScaledCanvas as any;
      }
      if (tagName === 'a') {
        const link = originalCreateElement.call(document, 'a') as HTMLAnchorElement;
        link.click = jest.fn();
        return link;
      }
      return originalCreateElement.call(document, tagName);
    }) as any;

    await act(async () => {
      try {
        await result.current.exportToPNG({ scale: 2 });
      } catch (e) { /* ignore */ }
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(mockScaledCanvas.getContext).toHaveBeenCalled();
    expect(mockScaledCanvas.remove).toHaveBeenCalled();
  });
});
