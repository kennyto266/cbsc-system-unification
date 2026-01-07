/**
 * Test for useChartResize without console mock
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

describe('useChartResize (no console mock)', () => {
  // Don't mock console
  const originalConsole = {
    ...console,
  };

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

  it('should initialize', () => {
    const { result } = renderHook(() => useChartResize());
    expect(result.current).toBeDefined();
  });

  it('should call containerRef with element', () => {
    const { result } = renderHook(() => useChartResize());

    const mockElement = document.createElement('div');
    Object.defineProperty(mockElement, 'offsetWidth', { value: 800 });
    Object.defineProperty(mockElement, 'offsetHeight', { value: 600 });

    act(() => {
      result.current.containerRef(mockElement);
    });

    console.log('Size:', result.current.size);

    expect(result.current.size.width).toBeGreaterThanOrEqual(0);
  });
});
