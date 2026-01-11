import { useState, useEffect, useMemo, useCallback, useRef } from 'react';

interface VirtualScrollOptions {
  itemHeight: number | ((index: number) => number);
  containerHeight: number;
  overscan?: number;
  scrollingDelay?: number;
}

interface VirtualScrollResult<T> {
  items: T[];
  containerProps: React.HTMLProps<HTMLDivElement>;
  innerStyle: React.CSSProperties;
  visibleItems: {
    item: T;
    index: number;
    style: React.CSSProperties;
  }[];
  totalHeight: number;
  scrollToIndex: (index: number, alignment?: 'auto' | 'smart' | 'center' | 'end' | 'start') => void;
  scrollTop: number;
  isScrolling: boolean;
}

export function useVirtualScroll<T>(
  items: T[],
  options: VirtualScrollOptions
): VirtualScrollResult<T> {
  const {
    itemHeight,
    containerHeight,
    overscan = 5,
    scrollingDelay = 150,
  } = options;

  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollingTimeoutRef = useRef<NodeJS.Timeout>();

  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate item positions and total height
  const { itemPositions, totalHeight } = useMemo(() => {
    const positions: number[] = [];
    let currentTop = 0;

    for (let i = 0; i < items.length; i++) {
      positions.push(currentTop);
      const height = typeof itemHeight === 'function' ? itemHeight(i) : itemHeight;
      currentTop += height;
    }

    return {
      itemPositions: positions,
      totalHeight: currentTop,
    };
  }, [items.length, itemHeight]);

  // Calculate visible range
  const visibleRange = useMemo(() => {
    let startIndex = 0;
    let endIndex = items.length - 1;

    // Binary search for start index
    let left = 0;
    let right = items.length - 1;
    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      if (itemPositions[mid] <= scrollTop) {
        startIndex = mid;
        left = mid + 1;
      } else {
        right = mid - 1;
      }
    }

    // Find end index
    const visibleBottom = scrollTop + containerHeight;
    for (let i = startIndex; i < items.length; i++) {
      const height = typeof itemHeight === 'function' ? itemHeight(i) : itemHeight;
      if (itemPositions[i] + height > visibleBottom) {
        endIndex = i;
        break;
      }
    }

    // Add overscan
    startIndex = Math.max(0, startIndex - overscan);
    endIndex = Math.min(items.length - 1, endIndex + overscan);

    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemPositions, items.length, overscan]);

  // Handle scroll events
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);

    setIsScrolling(true);
    if (scrollingTimeoutRef.current) {
      clearTimeout(scrollingTimeoutRef.current);
    }
    scrollingTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, scrollingDelay);
  }, [scrollingDelay]);

  // Scroll to specific index
  const scrollToIndex = useCallback((
    index: number,
    alignment: 'auto' | 'smart' | 'center' | 'end' | 'start' = 'auto'
  ) => {
    if (!containerRef.current) return;

    const itemTop = itemPositions[index];
    const itemBottom = itemTop + (typeof itemHeight === 'function' ? itemHeight(index) : itemHeight);

    let scrollTop: number;

    switch (alignment) {
      case 'start':
        scrollTop = itemTop;
        break;
      case 'center':
        scrollTop = itemTop - (containerHeight - (itemBottom - itemTop)) / 2;
        break;
      case 'end':
        scrollTop = itemBottom - containerHeight;
        break;
      case 'smart':
        if (itemTop < containerRef.current.scrollTop) {
          scrollTop = itemTop;
        } else if (itemBottom > containerRef.current.scrollTop + containerHeight) {
          scrollTop = itemBottom - containerHeight;
        } else {
          return; // Item is already visible
        }
        break;
      case 'auto':
      default:
        scrollTop = itemTop;
        break;
    }

    scrollTop = Math.max(0, Math.min(scrollTop, totalHeight - containerHeight));
    containerRef.current.scrollTop = scrollTop;
  }, [itemPositions, totalHeight, containerHeight, itemHeight]);

  // Generate visible items
  const visibleItems = useMemo(() => {
    const result = [];

    for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
      const height = typeof itemHeight === 'function' ? itemHeight(i) : itemHeight;
      result.push({
        item: items[i],
        index: i,
        style: {
          position: 'absolute' as const,
          top: itemPositions[i],
          left: 0,
          right: 0,
          height,
        },
      });
    }

    return result;
  }, [items, visibleRange, itemPositions, itemHeight]);

  // Container props
  const containerProps = useMemo(() => ({
    ref: containerRef,
    style: {
      height: containerHeight,
      overflow: 'auto' as const,
      WebkitOverflowScrolling: 'touch' as const,
    },
    onScroll: handleScroll,
  }), [containerHeight, handleScroll]);

  // Inner container style
  const innerStyle = useMemo(() => ({
    height: totalHeight,
    position: 'relative' as const,
  }), [totalHeight]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (scrollingTimeoutRef.current) {
        clearTimeout(scrollingTimeoutRef.current);
      }
    };
  }, []);

  return {
    items,
    containerProps,
    innerStyle,
    visibleItems,
    totalHeight,
    scrollToIndex,
    scrollTop,
    isScrolling,
  };
}

// Hook for dynamic item heights
export function useDynamicVirtualScroll<T>(
  items: T[],
  options: Omit<VirtualScrollOptions, 'itemHeight'> & {
    estimatedItemHeight: number;
    getItemHeight: (index: number, item: T) => number;
  }
): VirtualScrollResult<T> & { updateItemHeight: (index: number, height: number) => void } {
  const { estimatedItemHeight, getItemHeight, ...restOptions } = options;
  const [itemHeights, setItemHeights] = useState<Record<number, number>>({});

  const updateItemHeight = useCallback((index: number, height: number) => {
    setItemHeights(prev => ({
      ...prev,
      [index]: height,
    }));
  }, []);

  const itemHeight = useCallback((index: number) => {
    return itemHeights[index] || estimatedItemHeight;
  }, [itemHeights, estimatedItemHeight]);

  const virtualScrollResult = useVirtualScroll(items, {
    ...restOptions,
    itemHeight,
  });

  return {
    ...virtualScrollResult,
    updateItemHeight,
  };
}