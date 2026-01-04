/**
 * useChartExport Hook Tests
 *
 * Comprehensive tests for the useChartExport hook
 * including export functionality for different formats and chart types.
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useChartExport } from './useChartExport';
import { createMockRef, mockChartData, flushPromises } from '../__tests__/setup';

// Mock document.createElement to control element creation
const originalCreateElement = document.createElement;
const mockCanvas = {
  width: 800,
  height: 600,
  getContext: jest.fn(() => ({
    scale: jest.fn(),
    drawImage: jest.fn(),
    fillRect: jest.fn(),
    fillStyle: '',
  })),
  toBlob: jest.fn((callback, type, quality) => {
    callback(new Blob(['mock-image'], { type }));
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
  const mockRef = createMockRef();
  const mockData = mockChartData;

  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.log = jest.fn();

    // Reset mock ref
    mockRef.current = null;

    // Mock createElement
    document.createElement = jest.fn((tagName: string) => {
      if (tagName === 'canvas') {
        return mockCanvas;
      }
      if (tagName === 'a') {
        return {
          href: '',
          download: '',
          click: jest.fn(),
        } as any;
      }
      return originalCreateElement.call(document, tagName);
    });

    // Mock body methods - use writable to allow redefinition
    Object.defineProperty(document.body, 'appendChild', {
      value: jest.fn(),
      writable: true,
      configurable: true,
    });
    Object.defineProperty(document.body, 'removeChild', {
      value: jest.fn(),
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
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
    mockRef.current = mockCanvas;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
      data: mockData,
    }));

    act(() => {
      result.current.exportToPNG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(mockCanvas.toBlob).toHaveBeenCalledWith(
      expect.any(Function),
      'image/png',
      undefined
    );
    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('png');
  });

  it('should export ChartJS canvas to JPG with custom options', async () => {
    mockRef.current = mockCanvas;

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

    expect(mockCanvas.toBlob).toHaveBeenCalledWith(
      expect.any(Function),
      'image/jpeg',
      0.8
    );
  });

  it('should export SVG from Recharts component', async () => {
    mockRef.current = mockSVGElement;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'recharts',
    }));

    // Mock Image and btoa for SVG to canvas conversion
    global.Image = jest.fn() as any;
    global.btoa = jest.fn(() => 'mocked-base64');

    act(() => {
      result.current.exportToSVG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('svg');
  });

  it('should export data to CSV', async () => {
    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      data: mockData,
    }));

    const mockBlob = new Blob(['timestamp,value,label\n1,100,Test1\n2,200,Test2\n'], {
      type: 'text/csv',
    });

    // Mock the CSV export
    const originalExportDataToCSV = require('./useChartExport').exportDataToCSV;
    jest.doMock('./useChartExport', async () => {
      const actual = await jest.requireActual<typeof import('./useChartExport')>('./useChartExport');
      return {
        ...actual,
        exportDataToCSV: () => 'timestamp,value,label\n1,100,Test1\n2,200,Test2\n',
      };
    });

    act(() => {
      result.current.exportToCSV();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('csv');
  });

  it('should export data to JSON', async () => {
    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      data: mockData,
    }));

    act(() => {
      result.current.exportToJSON();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.exportHistory).toHaveLength(1);
    expect(result.current.exportHistory[0].format).toBe('json');
  });

  it('should handle custom export function', async () => {
    const customExportFunction = jest.fn().mockResolvedValue(
      new Blob(['custom-export'], { type: 'image/png' })
    );

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      customExportFunction,
    }));

    act(() => {
      result.current.exportToPNG();
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

    act(() => {
      result.current.exportToPNG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Chart reference is null');
  });

  it('should prevent concurrent exports', async () => {
    mockRef.current = mockCanvas;

    // Make toBlob async to simulate export taking time
    mockCanvas.toBlob = jest.fn((callback) => {
      setTimeout(() => callback(new Blob(['mock-image'])), 100);
    });

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    act(() => {
      result.current.exportToPNG();
    });

    // Try to export again before the first one finishes
    act(() => {
      result.current.exportToJPG();
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Export already in progress');
  });

  it('should get chart as blob without downloading', async () => {
    mockRef.current = mockCanvas;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    let blob: Blob | null = null;

    act(async () => {
      blob = await result.current.getChartBlob('png');
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(blob).toBeInstanceOf(Blob);
    expect(result.current.exportHistory).toHaveLength(0); // No history for getChartBlob
  });

  it('should clear export history', () => {
    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    // Simulate some exports
    act(() => {
      result.current.exportToPNG();
      result.current.exportToJPG();
    });

    expect(result.current.exportHistory.length).toBeGreaterThan(0);

    act(() => {
      result.current.clearHistory();
    });

    expect(result.current.exportHistory).toEqual([]);
  });

  it('should use custom filename', async () => {
    mockRef.current = mockCanvas;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
      filename: 'my-custom-chart',
    }));

    act(() => {
      result.current.exportToPNG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    const exportRecord = result.current.exportHistory[0];
    expect(exportRecord.filename).toMatch(/^my-custom-chart-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.png$/);
  });

  it('should handle empty data export', async () => {
    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      data: [],
    }));

    act(() => {
      result.current.exportToCSV();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.exportHistory).toHaveLength(1);
  });

  it('should handle unsupported chart types', async () => {
    mockRef.current = mockCanvas;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'unsupported' as any,
    }));

    act(() => {
      result.current.exportToPNG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('Unsupported chart type');
  });

  it('should handle SVG export for ChartJS (should fail)', async () => {
    mockRef.current = mockCanvas;

    const { result } = renderHook(() => useChartExport({
      chartRef: mockRef,
      chartType: 'chartjs',
    }));

    act(() => {
      result.current.exportToSVG();
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toContain('SVG export is not supported for Chart.js');
  });

  it('should apply scaling to canvas export', async () => {
    mockRef.current = mockCanvas;

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
      remove: jest.fn(),
    };

    // Mock createElement to return scaled canvas
    document.createElement = jest.fn((tagName: string) => {
      if (tagName === 'canvas') {
        return mockScaledCanvas;
      }
      return originalCreateElement.call(document, tagName);
    });

    act(() => {
      result.current.exportToPNG({ scale: 2 });
    });

    await waitFor(() => {
      expect(result.current.isExporting).toBe(null);
    });

    expect(mockScaledCanvas.getContext).toHaveBeenCalled();
    expect(mockScaledCanvas.remove).toHaveBeenCalled();
  });
});