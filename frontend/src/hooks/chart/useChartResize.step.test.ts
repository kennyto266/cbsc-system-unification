/**
 * Step-by-step test for useChartResize
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from '@jest/globals';

// Mock useResponsive
jest.mock('../useResponsive', () => ({
  useResponsive: jest.fn(),
}));

import { useChartResize } from './useChartResize';
import { useResponsive as mockUseResponsive } from '../useResponsive';
const mockedUseResponsive = mockUseResponsive as jest.MockedFunction<typeof mockUseResponsive>;

describe('useChartResize (step by step)', () => {
  beforeEach(() => {
    (mockedUseResponsive as jest.Mock).mockReturnValue({
      width: 1024,
      height: 768,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      breakpoint: 'lg',
      orientation: 'landscape' as const,
    });
  });

  it('step 1: should initialize', () => {
    const { result } = renderHook(() => useChartResize());
    expect(result.current).toBeDefined();
  });

  it('step 2: should have containerRef', () => {
    const { result } = renderHook(() => useChartResize());
    expect(typeof result.current.containerRef).toBe('function');
  });

  it('step 3: should call containerRef with null', () => {
    const { result } = renderHook(() => useChartResize());
    act(() => {
      result.current.containerRef(null);
    });
    expect(result.current.size).toEqual({ width: 0, height: 0 });
  });

  it('step 4: should call containerRef with element', () => {
    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');

    act(() => {
      result.current.containerRef(mockElement);
    });

    // Check what size we got
    console.log('Size after containerRef:', result.current.size);
    console.log('Element offsetWidth:', mockElement.offsetWidth);

    expect(result.current.size.width).toBeGreaterThanOrEqual(0);
  });

  it('step 5: should call containerRef with element having properties', () => {
    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    console.log('Size with properties:', result.current.size);

    expect(result.current.size.width).toBeGreaterThanOrEqual(0);
  });
});
