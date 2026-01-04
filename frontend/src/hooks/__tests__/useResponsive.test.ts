/**
 * useResponsive Hook Tests
 *
 * Comprehensive tests for the useResponsive hook including
 * breakpoint detection, orientation detection, and resize handling.
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useResponsive, useMediaQuery, useIsTouchDevice } from '../useResponsive';

// Mock window object and its properties
const mockWindow = {
  innerWidth: 1024,
  innerHeight: 768,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  matchMedia: jest.fn(),
  orientation: 0,
};

// Mock navigator
const mockNavigator = {
  maxTouchPoints: 0,
  msMaxTouchPoints: 0,
};

// Store original values
let originalWindow: typeof window;
let originalNavigator: typeof navigator;

describe('useResponsive', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Store original values
    originalWindow = window;
    originalNavigator = navigator;

    // Mock window
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

    window.addEventListener = jest.fn();
    window.removeEventListener = jest.fn();
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    }));

    // Mock navigator
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: mockNavigator,
    });
  });

  afterEach(() => {
    // Restore original values
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalWindow.innerWidth,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: originalWindow.innerHeight,
    });
    window.addEventListener = originalWindow.addEventListener;
    window.removeEventListener = originalWindow.removeEventListener;
    window.matchMedia = originalWindow.matchMedia;
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: originalNavigator,
    });
  });

  it('should return initial responsive state', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1024 });
    Object.defineProperty(window, 'innerHeight', { value: 768 });

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
    Object.defineProperty(window, 'innerWidth', { value: 500 });
    Object.defineProperty(window, 'innerHeight', { value: 800 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe('sm');
  });

  it('should detect tablet breakpoint correctly', () => {
    Object.defineProperty(window, 'innerWidth', { value: 800 });
    Object.defineProperty(window, 'innerHeight', { value: 600 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe('md');
  });

  it('should detect desktop breakpoint correctly', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1200 });
    Object.defineProperty(window, 'innerHeight', { value: 800 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.breakpoint).toBe('xl');
  });

  it('should detect all breakpoints correctly', () => {
    const testCases = [
      { width: 400, expected: 'xs' },
      { width: 500, expected: 'sm' },
      { width: 700, expected: 'sm' },
      { width: 800, expected: 'md' },
      { width: 900, expected: 'md' },
      { width: 1100, expected: 'lg' },
      { width: 1200, expected: 'xl' },
      { width: 1300, expected: 'xl' },
      { width: 1600, expected: '2xl' },
    ];

    testCases.forEach(({ width, expected }) => {
      Object.defineProperty(window, 'innerWidth', { value: width });

      const { result } = renderHook(() => useResponsive());

      expect(result.current.breakpoint).toBe(expected);
    });
  });

  it('should detect portrait orientation', () => {
    Object.defineProperty(window, 'innerWidth', { value: 768 });
    Object.defineProperty(window, 'innerHeight', { value: 1024 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.orientation).toBe('portrait');
  });

  it('should detect landscape orientation', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1024 });
    Object.defineProperty(window, 'innerHeight', { value: 768 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.orientation).toBe('landscape');
  });

  it('should handle square orientation as landscape', () => {
    Object.defineProperty(window, 'innerWidth', { value: 800 });
    Object.defineProperty(window, 'innerHeight', { value: 800 });

    const { result } = renderHook(() => useResponsive());

    expect(result.current.orientation).toBe('landscape');
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

  it('should update state on window resize', () => {
    const { result } = renderHook(() => useResponsive());

    // Get the resize handler
    const resizeHandler = (window.addEventListener as any).mock.calls.find(
      ([event]) => event === 'resize'
    )[1];

    // Simulate window resize
    Object.defineProperty(window, 'innerWidth', { value: 500 });
    Object.defineProperty(window, 'innerHeight', { value: 900 });

    act(() => {
      resizeHandler();
    });

    expect(result.current.width).toBe(500);
    expect(result.current.height).toBe(900);
    expect(result.current.isMobile).toBe(true);
    expect(result.current.breakpoint).toBe('sm');
    expect(result.current.orientation).toBe('portrait');
  });

  it('should handle orientation change', () => {
    const { result } = renderHook(() => useResponsive());

    // Get the orientation change handler
    const orientationHandler = (window.addEventListener as any).mock.calls.find(
      ([event]) => event === 'orientationchange'
    )[1];

    // Simulate orientation change
    Object.defineProperty(window, 'innerWidth', { value: 768 });
    Object.defineProperty(window, 'innerHeight', { value: 1024 });

    act(() => {
      orientationHandler();
    });

    // Need to advance timers for the setTimeout in orientation handler
    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.orientation).toBe('portrait');
  });

  it('should return default values on server-side render', () => {
    // Mock window as undefined (SSR scenario)
    const originalWindow = global.window;
    delete (global as any).window;

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

    // Restore window
    global.window = originalWindow;
  });
});

describe('useMediaQuery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with false value', () => {
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
    }));

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
    }));

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
    }));

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
    window.matchMedia = jest.fn(() => mockMediaQuery);

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
    window.matchMedia = jest.fn(() => mockMediaQuery);

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
    window.matchMedia = jest.fn(() => mockMediaQuery);

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
    window.matchMedia = jest.fn(() => mockMediaQuery);

    const { unmount } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    unmount();

    expect(mockMediaQuery.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('should return false on server-side render', () => {
    const originalWindow = global.window;
    delete (global as any).window;

    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));

    expect(result.current).toBe(false);

    global.window = originalWindow;
  });
});

describe('useIsTouchDevice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(window, 'ontouchstart', {
      writable: true,
      configurable: true,
      value: undefined,
    });
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: {
        maxTouchPoints: 0,
        msMaxTouchPoints: 0,
      },
    });
  });

  it('should detect touch device via ontouchstart', () => {
    Object.defineProperty(window, 'ontouchstart', { value: jest.fn() });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should detect touch device via maxTouchPoints', () => {
    Object.defineProperty(window.navigator, 'maxTouchPoints', { value: 5 });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should detect touch device via msMaxTouchPoints', () => {
    // @ts-ignore
    Object.defineProperty(window.navigator, 'msMaxTouchPoints', { value: 3 });

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(true);
  });

  it('should return false when no touch support detected', () => {
    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(false);
  });

  it('should return false on server-side render', () => {
    const originalWindow = global.window;
    delete (global as any).window;

    const { result } = renderHook(() => useIsTouchDevice());

    expect(result.current).toBe(false);

    global.window = originalWindow;
  });
});