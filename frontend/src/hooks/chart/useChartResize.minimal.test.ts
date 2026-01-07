/**
 * Minimal test for useChartResize
 */

import { renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach } from '@jest/globals';

// Mock useResponsive
jest.mock('../useResponsive', () => ({
  useResponsive: jest.fn(),
}));

import { useChartResize } from './useChartResize';
import { useResponsive as mockUseResponsive } from '../useResponsive';
const mockedUseResponsive = mockUseResponsive as jest.MockedFunction<typeof mockUseResponsive>;

describe('useChartResize (minimal)', () => {
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

  it('should have default size', () => {
    const { result } = renderHook(() => useChartResize());
    expect(result.current.size).toEqual({ width: 0, height: 0 });
  });
});
