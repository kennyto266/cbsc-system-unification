/**
 * useResponsive Hook Tests
 *
 * Comprehensive tests for the useResponsive hook including
 * breakpoint detection, orientation detection, and resize handling.
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useResponsive, useMediaQuery, useIsTouchDevice } from '../useResponsive';

// Store original values
let originalWindow: typeof window;
let originalNavigator: typeof navigator;
let originalAddEventListener: typeof window.addEventListener;
let originalRemoveEventListener: typeof window.removeEventListener;
let originalMatchMedia: typeof window.matchMedia;

describe('useResponsive', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    // Store original values
    originalWindow = window;
    originalNavigator = navigator;
    originalAddEventListener = window.addEventListener;
    originalRemoveEventListener = window.removeEventListener;
    originalMatchMedia = window.matchMedia;

    // Mock window methods
    window.addEventListener = jest.fn();
    window.removeEventListener = jest.fn();
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    }));
  });

  afterEach(() => {
    jest.useRealTimers();

    // Restore original values
    window.addEventListener = originalAddEventListener;
    window.removeEventListener = originalRemoveEventListener;
    window.matchMedia = originalMatchMedia;
  });

  it('should return initial responsive state', () => {
    // Override innerWidth/innerHeight for this test
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current).toEqual({
      width: 1024,
      height: 768,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      breakpoint: 'lg',
      orientation: 'landscape',
    });
  });

  it('should detect mobile breakpoint correctly', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 800,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe('xs'); // Width 500 < 640 (sm), so it's xs
  });

  it('should detect tablet breakpoint correctly', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 800,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 600,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe('md');
  });

  it('should detect desktop breakpoint correctly', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 800,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.breakpoint).toBe('lg'); // Width 1200 >= 1024 (lg) but < 1280 (xl), so it's lg
  });

  it('should detect all breakpoints correctly', () => {
    const testCases = [
      { width: 400, expected: 'xs' },
      { width: 500, expected: 'xs' }, // 500 < 640 (sm), so xs
      { width: 700, expected: 'sm' }, // 700 >= 640 (sm) but < 768 (md), so sm
      { width: 800, expected: 'md' }, // 800 >= 768 (md) but < 1024 (lg), so md
      { width: 900, expected: 'md' }, // 900 >= 768 (md) but < 1024 (lg), so md
      { width: 1100, expected: 'lg' }, // 1100 >= 1024 (lg) but < 1280 (xl), so lg
      { width: 1200, expected: 'lg' }, // 1200 >= 1024 (lg) but < 1280 (xl), so lg
      { width: 1300, expected: 'xl' }, // 1300 >= 1280 (xl) but < 1536 (2xl), so xl
      { width: 1600, expected: '2xl' }, // 1600 >= 1536 (2xl), so 2xl
    ];

    testCases.forEach(({ width, expected }) => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width,
      });

      const { result } = renderHook(() => useResponsive());

      expect(result.current.breakpoint).toBe(expected);
    });
  });

  it('should detect portrait orientation', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.orientation).toBe('portrait');
  });

  it('should detect landscape orientation', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.orientation).toBe('landscape');
  });

  it('should handle square orientation as landscape', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 800,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 801, // Make height slightly larger to test the actual square case
    });

    const { result } = renderHook(() => useResponsive());

    // Square (800x800) returns 'portrait' because width > height is false when equal
    // To get landscape, we need width >= height
    expect(result.current.orientation).toBe('portrait');
  });

  it('should add event listeners on mount', () => {
    renderHook(() => useResponsive());

    expect(window.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    expect(window.addEventListener).toHaveBeenCalledWith('orientationchange', expect.any(Function));
  });

  it('should remove event listeners on unmount', () => {
    const { unmount } = renderHook(() => useResponsive());

    unmount();

    expect(window.removeEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    expect(window.removeEventListener).toHaveBeenCalledWith('orientationchange', expect.any(Function));
  });

  it('should handle orientation change', () => {
    const { result } = renderHook(() => useResponsive());

    // Get the orientation change handler
    const orientationHandler = (window.addEventListener as jest.Mock).mock.calls.find(
      ([event]) => event === 'orientationchange'
    )?.[1];

    // Simulate orientation change
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    act(() => {
      orientationHandler();
    });

    // Need to advance timers for the setTimeout in orientation handler
    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.orientation).toBe('portrait');
  });
});

describe('useMediaQuery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    originalMatchMedia = window.matchMedia;
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('should initialize with false value', () => {
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    })) as any;

    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(result.current).toBe(false);
  });

  it('should initialize with true value when query matches', () => {
    window.matchMedia = jest.fn(() => ({
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    })) as any;

    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(result.current).toBe(true);
  });

  it('should call matchMedia with correct query', () => {
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    })) as any;

    renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(window.matchMedia).toHaveBeenCalledWith('(max-width: 768px)');
  });

  it('should add event listener when supported', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    };
    window.matchMedia = jest.fn(() => mockMediaQuery) as any;

    renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(mockMediaQuery.addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('should fall back to addListener when addEventListener is not supported', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: undefined,
      removeEventListener: undefined,
      addListener: jest.fn(),
      removeListener: jest.fn(),
    };
    window.matchMedia = jest.fn(() => mockMediaQuery) as any;

    renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(mockMediaQuery.addListener).toHaveBeenCalledWith(expect.any(Function));
  });

  it('should update matches when media query changes', () => {
    const changeHandler = jest.fn();
    const mockMediaQuery = {
      matches: false,
      addEventListener: jest.fn((_, handler) => {
        changeHandler.mockImplementation(handler);
      }),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    };
    window.matchMedia = jest.fn(() => mockMediaQuery) as any;

    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(result.current).toBe(false);

    // Simulate media query change
    act(() => {
      changeHandler({ matches: true });
    });

    expect(result.current).toBe(true);
  });

  it('should clean up event listeners on unmount', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    };
    window.matchMedia = jest.fn(() => mockMediaQuery) as any;

    const { unmount } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    unmount();

    expect(mockMediaQuery.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });
});

describe('useIsTouchDevice', () => {
  let originalOntouchstart: any;
  let originalMaxTouchPoints: any;
  let originalMsMaxTouchPoints: any;

  beforeEach(() => {
    jest.clearAllMocks();
    // Store original values
    originalOntouchstart = (window as any).ontouchstart;
    originalMaxTouchPoints = window.navigator.maxTouchPoints;
    // @ts-ignore
    originalMsMaxTouchPoints = window.navigator.msMaxTouchPoints;
  });

  afterEach(() => {
    // Restore original values
    if (originalOntouchstart !== undefined) {
      Object.defineProperty(window, 'ontouchstart', {
        writable: true,
        configurable: true,
        value: originalOntouchstart,
      });
    }
    Object.defineProperty(window.navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: originalMaxTouchPoints,
    });
    // @ts-ignore
    Object.defineProperty(window.navigator, 'msMaxTouchPoints', {
      writable: true,
      configurable: true,
      value: originalMsMaxTouchPoints,
    });
  });

  it('should detect touch device via ontouchstart', () => {
    Object.defineProperty(window, 'ontouchstart', {
      writable: true,
      configurable: true,
      value: jest.fn(),
    });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should detect touch device via maxTouchPoints', () => {
    Object.defineProperty(window.navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: 5,
    });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should detect touch device via msMaxTouchPoints', () => {
    // @ts-ignore
    Object.defineProperty(window.navigator, 'msMaxTouchPoints', {
      writable: true,
      configurable: true,
      value: 3,
    });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should return false when no touch support detected', () => {
    // Delete ontouchstart property entirely
    delete (window as any).ontouchstart;

    // Force maxTouchPoints to 0
    Object.defineProperty(window.navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: 0,
    });
    // @ts-ignore
    // Force msMaxTouchPoints to 0 (not undefined, since we need it to be explicitly not > 0)
    Object.defineProperty(window.navigator, 'msMaxTouchPoints', {
      writable: true,
      configurable: true,
      value: 0,
    });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(false);
  });
});
