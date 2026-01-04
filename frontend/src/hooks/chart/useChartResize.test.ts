/**
 * useChartResize Hook Tests
 *
 * Comprehensive tests for the useChartResize hook
 * including ResizeObserver integration, responsive behavior, and edge cases.
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useChartResize } from './useChartResize';
import { createMockRef, createMockElement } from '../__tests__/setup';

// Mock useResponsive hook with complete return value
jest.mock('../useResponsive', () => ({
  useResponsive: jest.fn().mockImplementation(() => ({
    width: 1024,
    height: 768,
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    breakpoint: 'lg',
    orientation: 'landscape' as const,
  })),
  __esModule: true,
}));

// Import the mocked module to access it in tests
const mockUseResponsive = jest.requireMock('../useResponsive').useResponsive as jest.Mock;

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

describe('useChartResize', () => {
  const mockRef = createMockRef();

  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.log = jest.fn();

    // Reset mock ref
    mockRef.current = null;
  });

  afterEach(() => {
    console.error = originalConsoleError;
    console.log = originalConsoleLog;
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useChartResize({ ref: mockRef }));

    expect(result.current.size.width).toBe(0);
    expect(result.current.size.height).toBe(0);
    expect(result.current.isResizing).toBe(false);
    expect(result.current.resizeDirection).toBe(null);
    expect(result.current.breakpoint).toBe(null);
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
  });

  it('should create container ref function', () => {
    const { result } = renderHook(() => useChartResize());

    expect(typeof result.current.containerRef).toBe('function');
  });

  it('should set initial size from element', () => {
    const { result } = renderHook(() => useChartResize());

    // Simulate element being attached
    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    // Wait for initial resize observation
    jest.advanceTimersByTime(0);

    expect(result.current.size.width).toBe(800);
    expect(result.current.size.height).toBe(600);
  });

  it('should apply minimum constraints', () => {
    const config = {
      minWidth: 400,
      minHeight: 300,
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 200 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 150 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(result.current.size.width).toBe(400);
    expect(result.current.size.height).toBe(300);
  });

  it('should apply maximum constraints', () => {
    const config = {
      maxWidth: 1000,
      maxHeight: 750,
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1200 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 900 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(result.current.size.width).toBe(1000);
    expect(result.current.size.height).toBe(750);
  });

  it('should apply aspect ratio when enabled', () => {
    const config = {
      enableAspectRatio: true,
      aspectRatio: 16 / 9,
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(result.current.size.width).toBe(800);
    expect(result.current.size.height).toBe(450); // 800 / (16/9) = 450
  });

  it('should apply padding', () => {
    const config = {
      padding: {
        top: 10,
        right: 20,
        bottom: 30,
        left: 40,
      },
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(result.current.size.width).toBe(800 - 20 - 40); // 740
    expect(result.current.size.height).toBe(600 - 10 - 30); // 560
  });

  it('should detect breakpoints correctly', () => {
    const config = {
      breakpoints: {
        mobile: 768,
        tablet: 1024,
        desktop: 1440,
      },
    };

    const { result, rerender } = renderHook(() => useChartResize(config));

    // Test mobile breakpoint
    let mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);
    expect(result.current.breakpoint).toBe('mobile');
    expect(result.current.isMobile).toBe(true);

    // Test tablet breakpoint
    mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);
    expect(result.current.breakpoint).toBe('tablet');
    expect(result.current.isTablet).toBe(true);

    // Test desktop breakpoint
    mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1200 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);
    expect(result.current.breakpoint).toBe('desktop');
    expect(result.current.isDesktop).toBe(true);
  });

  it('should trigger manual resize', () => {
    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    const initialSize = { ...result.current.size };

    // Simulate size change
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1000 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 750 });

    act(() => {
      result.current.triggerResize();
    });

    expect(result.current.size.width).toBe(1000);
    expect(result.current.size.height).toBe(750);
    expect(result.current.previousSize).toEqual(initialSize);
  });

  it('should detect resize direction', () => {
    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    // Change only width
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1000 });

    act(() => {
      result.current.triggerResize();
    });

    expect(result.current.resizeDirection).toBe('horizontal');

    // Change only height
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1000 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 800 });

    act(() => {
      result.current.triggerResize();
    });

    expect(result.current.resizeDirection).toBe('vertical');

    // Change both
    Object.defineProperty(mockElement, 'offsetWidth', { value: 1200 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 900 });

    act(() => {
      result.current.triggerResize();
    });

    expect(result.current.resizeDirection).toBe('both');
  });

  it('should check if container is visible', () => {
    const { result } = renderHook(() => useChartResize());

    // Initially no container
    expect(result.current.isVisible()).toBe(false);

    const mockElement = document.createElement('div');
    mockElement.style.display = 'block';

    act(() => {
      result.current.containerRef(mockElement);
    });

    // Visible element
    expect(result.current.isVisible()).toBe(true);

    mockElement.style.display = 'none';
    expect(result.current.isVisible()).toBe(false);
  });

  it('should call onResize callback', () => {
    const onResizeMock = jest.fn();
    const config = {
      onResize: onResizeMock,
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(onResizeMock).toHaveBeenCalled();
    expect(onResizeMock).toHaveBeenCalledWith(
      { width: 800, height: 600 },
      { width: 0, height: 0 }
    );
  });

  it('should debounce resize events', () => {
    jest.useFakeTimers();

    const config = {
      debounceMs: 100,
    };

    const { result } = renderHook(() => useChartResize(config));

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    // Trigger multiple rapid resizes
    act(() => {
      result.current.triggerResize();
      result.current.triggerResize();
      result.current.triggerResize();
    });

    // Should not update yet due to debounce
    expect(result.current.isResizing).toBe(true);

    // Wait for debounce
    jest.advanceTimersByTime(100);

    // Should have updated now
    expect(result.current.isResizing).toBe(false);
    expect(result.current.resizeDirection).toBe(null);

    jest.useRealTimers();
  });

  it('should handle device responsiveness from useResponsive', () => {
    // Override the mock to return mobile
    mockUseResponsive.mockReturnValue({
      width: 600,
      height: 800,
      isMobile: true,
      isTablet: false,
      isDesktop: false,
      breakpoint: 'sm',
      orientation: 'portrait' as const,
    });

    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    jest.advanceTimersByTime(0);

    expect(result.current.isMobile).toBe(true);
  });

  it('should clean up on unmount', () => {
    const { result, unmount } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    // Get the ResizeObserver instance
    const resizeObserverInstance = global.ResizeObserver.mock.results[0].value;

    unmount();

    // Should have disconnected
    expect(resizeObserverInstance.disconnect).toHaveBeenCalled();
  });
});

// Helper function for act is no longer needed with @testing-library/react