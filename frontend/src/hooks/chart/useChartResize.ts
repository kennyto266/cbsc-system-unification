/**
 * useChartResize Hook
 *
 * A comprehensive hook for managing chart responsive behavior using ResizeObserver.
 * Provides debounced resize handling, container size tracking, and breakpoint support.
 *
 * @example
 * ```tsx
 * const MyChart = () => {
 *   const chartRef = useRef<HTMLDivElement>(null);
 *   const { width, height, containerRef, isMobile } = useChartResize({
 *     ref: chartRef,
 *     debounceMs: 150,
 *     breakpoints: {
 *       mobile: 768,
 *       tablet: 1024,
 *       desktop: 1440
 *     }
 *   });
 *
 *   return (
 *     <div ref={containerRef} style={{ width: '100%', height: '400px' }}>
 *       <Line data={data} options={{ responsive: false, width, height }} />
 *     </div>
 *   );
 * };
 * ```

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useResponsive } from '../useResponsive';

// Types for the hook
export interface ChartSize {
  width: number;
  height: number;
}

export interface ChartBreakpoints {
  /** Mobile breakpoint width in pixels */
  mobile?: number;
  /** Tablet breakpoint width in pixels */
  tablet?: number;
  /** Desktop breakpoint width in pixels */
  desktop?: number;
}

export interface ChartResizeConfig {
  /** Reference to the chart container element */
  ref?: React.RefObject<HTMLElement>;
  /** Debounce delay for resize events in milliseconds */
  debounceMs?: number;
  /** Custom breakpoints for responsive behavior */
  breakpoints?: ChartBreakpoints;
  /** Enable height auto-calculation based on aspect ratio */
  enableAspectRatio?: boolean;
  /** Aspect ratio (width / height) if enableAspectRatio is true */
  aspectRatio?: number;
  /** Minimum width in pixels */
  minWidth?: number;
  /** Minimum height in pixels */
  minHeight?: number;
  /** Maximum width in pixels */
  maxWidth?: number;
  /** Maximum height in pixels */
  maxHeight?: number;
  /** Padding to subtract from dimensions */
  padding?: {
    top?: number;
    right?: number;
    bottom?: number;
    left?: number;
  };
  /** Callback when resize occurs */
  onResize?: (size: ChartSize, previousSize: ChartSize) => void;
  /** Enable debug logging */
  enableDebug?: boolean;
}

export interface ChartResizeState {
  /** Current container dimensions */
  size: ChartSize;
  /** Previous container dimensions */
  previousSize: ChartSize;
  /** Whether container is currently resizing */
  isResizing: boolean;
  /** Resize direction */
  resizeDirection: 'horizontal' | 'vertical' | 'both' | null;
  /** Current breakpoint */
  breakpoint: 'mobile' | 'tablet' | 'desktop' | null;
  /** Whether device is mobile */
  isMobile: boolean;
  /** Whether device is tablet */
  isTablet: boolean;
  /** Whether device is desktop */
  isDesktop: boolean;
}

export interface ChartResizeActions {
  /** Manually trigger resize */
  triggerResize: () => void;
  /** Get container element */
  getContainer: () => HTMLElement | null;
  /** Check if container is visible */
  isVisible: () => boolean;
  /** Force update dimensions */
  updateDimensions: () => void;
}

export interface UseChartResizeReturn extends ChartResizeState, ChartResizeActions {
  /** Combined ref to pass to container element */
  containerRef: (node: HTMLElement | null) => void;
}

// Default configuration
const DEFAULT_CONFIG: Partial<ChartResizeConfig> = {
  debounceMs: 150,
  enableAspectRatio: false,
  aspectRatio: 16 / 9,
  minWidth: 100,
  minHeight: 100,
  padding: {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
  },
  breakpoints: {
    mobile: 768,
    tablet: 1024,
    desktop: 1440,
  },
  enableDebug: false,
};

// Utility functions
const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

const getElementSize = (element: HTMLElement): ChartSize => {
  const rect = element.getBoundingClientRect();
  return {
    width: rect.width,
    height: rect.height,
  };
};

const applyConstraints = (
  size: ChartSize,
  config: ChartResizeConfig
): ChartSize => {
  let { width, height } = size;

  // Apply min/max constraints
  if (config.minWidth && width < config.minWidth) {
    width = config.minWidth;
  }
  if (config.minHeight && height < config.minHeight) {
    height = config.minHeight;
  }
  if (config.maxWidth && width > config.maxWidth) {
    width = config.maxWidth;
  }
  if (config.maxHeight && height > config.maxHeight) {
    height = config.maxHeight;
  }

  // Apply aspect ratio if enabled
  if (config.enableAspectRatio && config.aspectRatio) {
    height = width / config.aspectRatio;
  }

  return { width, height };
};

const applyPadding = (size: ChartSize, padding: ChartResizeConfig['padding']): ChartSize => {
  if (!padding) return size;

  return {
    width: size.width - (padding.left || 0) - (padding.right || 0),
    height: size.height - (padding.top || 0) - (padding.bottom || 0),
  };
};

const getResizeDirection = (
  currentSize: ChartSize,
  previousSize: ChartSize
): 'horizontal' | 'vertical' | 'both' | null => {
  const widthChanged = currentSize.width !== previousSize.width;
  const heightChanged = currentSize.height !== previousSize.height;

  if (widthChanged && heightChanged) return 'both';
  if (widthChanged) return 'horizontal';
  if (heightChanged) return 'vertical';
  return null;
};

const getCurrentBreakpoint = (
  width: number,
  breakpoints: ChartBreakpoints
): 'mobile' | 'tablet' | 'desktop' | null => {
  if (width < (breakpoints.mobile || 768)) return 'mobile';
  if (width < (breakpoints.tablet || 1024)) return 'tablet';
  if (width < (breakpoints.desktop || 1440)) return 'desktop';
  return null;
};

/**
 * useChartResize Hook
 *
 * @param config - Configuration object for chart resize management
 * @returns Hook state, actions, and container ref
 */
export const useChartResize = (config: ChartResizeConfig = {}): UseChartResizeReturn => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  // State management
  const [size, setSize] = useState<ChartSize>({ width: 0, height: 0 });
  const [previousSize, setPreviousSize] = useState<ChartSize>({ width: 0, height: 0 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeDirection, setResizeDirection] = useState<'horizontal' | 'vertical' | 'both' | null>(null);

  // Refs for DOM and ResizeObserver
  const containerRefElement = useRef<HTMLElement | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout>();

  // Use responsive hook for device detection
  const { isMobile: deviceIsMobile, isTablet: deviceIsTablet } = useResponsive();

  // Get current breakpoint
  const breakpoint = useMemo(() => {
    return getCurrentBreakpoint(size.width, finalConfig.breakpoints || {});
  }, [size.width, finalConfig.breakpoints]);

  // Debounced resize handler
  const handleResize = useCallback(
    debounce((entries: ResizeObserverEntry[]) => {
      if (!containerRefElement.current) return;

      const entry = entries[0];
      if (!entry) return;

      const rawSize = getElementSize(entry.target as HTMLElement);
      const constrainedSize = applyConstraints(rawSize, finalConfig);
      const finalSize = applyPadding(constrainedSize, finalConfig.padding);

      setSize(prevSize => {
        // Only update if size actually changed
        if (prevSize.width === finalSize.width && prevSize.height === finalSize.height) {
          return prevSize;
        }

        finalConfig.enableDebug &&
          console.log('[useChartResize] Size changed:', prevSize, '->', finalSize);

        // Update previous size
        setPreviousSize(prevSize);

        // Calculate resize direction
        const direction = getResizeDirection(finalSize, prevSize);
        setResizeDirection(direction);

        // Call onResize callback
        finalConfig.onResize?.(finalSize, prevSize);

        return finalSize;
      });

      // Clear resize timeout
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }

      // Set resizing state to false after debounce period
      resizeTimeoutRef.current = setTimeout(() => {
        setIsResizing(false);
        setResizeDirection(null);
      }, finalConfig.debounceMs);

    }, finalConfig.debounceMs || 150),
    [finalConfig]
  );

  // Set up ResizeObserver
  useEffect(() => {
    if (!containerRefElement.current) return;

    // Create ResizeObserver
    resizeObserverRef.current = new ResizeObserver(handleResize);

    // Start observing
    resizeObserverRef.current.observe(containerRefElement.current, {
      box: 'border-box',
    });

    // Initial size measurement
    const initialSize = getElementSize(containerRefElement.current);
    const constrainedSize = applyConstraints(initialSize, finalConfig);
    const finalSize = applyPadding(constrainedSize, finalConfig.padding);

    setSize(finalSize);
    setPreviousSize(finalSize);

    finalConfig.enableDebug &&
      console.log('[useChartResize] Initial size:', finalSize);

    // Cleanup
    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, [handleResize, finalConfig]);

  // Combined ref function
  const containerRef = useCallback((node: HTMLElement | null) => {
    // Update ref
    containerRefElement.current = node;

    // If an external ref is provided, update it as well
    if (finalConfig.ref) {
      (finalConfig.ref as React.MutableRefObject<HTMLElement | null>).current = node;
    }
  }, [finalConfig.ref]);

  // Manual actions
  const triggerResize = useCallback(() => {
    if (!containerRefElement.current) return;

    setIsResizing(true);
    const rawSize = getElementSize(containerRefElement.current);
    const constrainedSize = applyConstraints(rawSize, finalConfig);
    const finalSize = applyPadding(constrainedSize, finalConfig.padding);

    setSize(finalSize);
    setPreviousSize(size);

    const direction = getResizeDirection(finalSize, size);
    setResizeDirection(direction);

    finalConfig.onResize?.(finalSize, size);

    // Reset resizing state after a short delay
    setTimeout(() => {
      setIsResizing(false);
      setResizeDirection(null);
    }, finalConfig.debounceMs);
  }, [size, finalConfig]);

  const getContainer = useCallback(() => {
    return containerRefElement.current;
  }, []);

  const isVisible = useCallback(() => {
    if (!containerRefElement.current) return false;
    return containerRefElement.current.offsetParent !== null;
  }, []);

  const updateDimensions = useCallback(() => {
    triggerResize();
  }, [triggerResize]);

  // Memoized return value
  const returnValue = useMemo<UseChartResizeReturn>(() => ({
    // State
    size,
    previousSize,
    isResizing,
    resizeDirection,
    breakpoint,
    isMobile: deviceIsMobile || breakpoint === 'mobile',
    isTablet: deviceIsTablet || breakpoint === 'tablet',
    isDesktop: !deviceIsMobile && !deviceIsTablet && breakpoint === 'desktop',

    // Actions
    triggerResize,
    getContainer,
    isVisible,
    updateDimensions,

    // Ref
    containerRef,
  }), [
    size,
    previousSize,
    isResizing,
    resizeDirection,
    breakpoint,
    deviceIsMobile,
    deviceIsTablet,
    triggerResize,
    getContainer,
    isVisible,
    updateDimensions,
    containerRef,
  ]);

  return returnValue;
};

// Export types for external use
export type {
  ChartSize,
  ChartBreakpoints,
  ChartResizeConfig,
  ChartResizeState,
  ChartResizeActions,
  UseChartResizeReturn
};