import { useState, useRef, useCallback, useEffect } from 'react';
import { useGesture } from '@use-gesture/react';

interface SwipeGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  onTap?: () => void;
  onDoubleTap?: () => void;
  onLongPress?: () => void;
  threshold?: number;
  longPressDelay?: number;
  preventDefault?: boolean;
}

interface SwipeGestureState {
  isSwiping: boolean;
  isPressing: boolean;
  direction: 'left' | 'right' | 'up' | 'down' | null;
  velocity: number;
}

export const useSwipeGesture = (
  options: SwipeGestureOptions = {}
): [React.RefObject<HTMLElement>, SwipeGestureState] => {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onTap,
    onDoubleTap,
    onLongPress,
    threshold = 50,
    longPressDelay = 500,
    preventDefault = true,
  } = options;

  const [state, setState] = useState<SwipeGestureState>({
    isSwiping: false,
    isPressing: false,
    direction: null,
    velocity: 0,
  });

  const elementRef = useRef<HTMLElement>(null);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastTapRef = useRef<number>(0);

  const handleLongPress = useCallback(() => {
    setState(prev => ({ ...prev, isPressing: true }));
    onLongPress?.();
  }, [onLongPress]);

  const clearLongPressTimer = useCallback(() => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, []);

  const bind = useGesture(
    {
      onDrag: ({ movement: [mx, my], direction: [xDir, yDir], velocity: [vx, vy], event, cancel }) => {
        if (preventDefault && event.cancelable) {
          event.preventDefault();
        }

        setState(prev => ({
          ...prev,
          isSwiping: true,
          velocity: Math.sqrt(vx * vx + vy * vy),
        }));

        const absX = Math.abs(mx);
        const absY = Math.abs(my);

        if (absX > threshold || absY > threshold) {
          clearLongPressTimer();

          if (absX > absY) {
            // Horizontal swipe
            if (xDir > 0) {
              setState(prev => ({ ...prev, direction: 'right' }));
              onSwipeRight?.();
            } else {
              setState(prev => ({ ...prev, direction: 'left' }));
              onSwipeLeft?.();
            }
          } else {
            // Vertical swipe
            if (yDir > 0) {
              setState(prev => ({ ...prev, direction: 'down' }));
              onSwipeDown?.();
            } else {
              setState(prev => ({ ...prev, direction: 'up' }));
              onSwipeUp?.();
            }
          }

          cancel();
        }
      },
      onDragEnd: () => {
        setState(prev => ({
          ...prev,
          isSwiping: false,
          direction: null,
          velocity: 0,
        }));
        clearLongPressTimer();
      },
      onTap: ({ event }) => {
        if (preventDefault && event.cancelable) {
          event.preventDefault();
        }

        const now = Date.now();
        const timeSinceLastTap = now - lastTapRef.current;

        if (timeSinceLastTap < 300) {
          // Double tap
          onDoubleTap?.();
        } else {
          // Single tap
          onTap?.();
        }

        lastTapRef.current = now;
      },
      onPointerDown: () => {
        longPressTimerRef.current = setTimeout(handleLongPress, longPressDelay);
      },
      onPointerUp: () => {
        setState(prev => ({ ...prev, isPressing: false }));
        clearLongPressTimer();
      },
    },
    {
      target: elementRef,
      eventOptions: { passive: !preventDefault },
    }
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearLongPressTimer();
    };
  }, [clearLongPressTimer]);

  return [elementRef, state];
};

export const usePullToRefresh = (
  onRefresh: () => Promise<void> | void,
  options: {
    threshold?: number;
    disabled?: boolean;
  } = {}
): [React.RefObject<HTMLElement>, boolean, (refresh: () => Promise<void> | void) => void] => {
  const { threshold = 80, disabled = false } = options;
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPulling, setIsPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const elementRef = useRef<HTMLElement>(null);

  const triggerRefresh = useCallback(async (refreshFn?: () => Promise<void> | void) => {
    if (isRefreshing || disabled) return;

    setIsRefreshing(true);
    try {
      await (refreshFn || onRefresh)();
    } finally {
      setIsRefreshing(false);
      setPullDistance(0);
    }
  }, [isRefreshing, disabled, onRefresh]);

  const bind = useGesture(
    {
      onDrag: ({ movement: [, my], direction: [_, yDir], event, cancel }) => {
        if (disabled || !event.cancelable) return;

        const scrollTop = elementRef.current?.scrollTop || 0;
        if (scrollTop > 0) return;

        if (yDir > 0 && my > 0) {
          event.preventDefault();
          setPullDistance(Math.min(my * 0.5, threshold * 2)); // Damping effect
          setIsPulling(true);

          if (my >= threshold) {
            cancel();
            triggerRefresh();
          }
        }
      },
      onDragEnd: () => {
        if (pullDistance < threshold) {
          setPullDistance(0);
        }
        setIsPulling(false);
      },
    },
    {
      target: elementRef,
      eventOptions: { passive: false },
    }
  );

  return [
    elementRef,
    isRefreshing || (isPulling && pullDistance >= threshold),
    triggerRefresh,
  ];
};

export const usePinchToZoom = (
  options: {
    minScale?: number;
    maxScale?: number;
    onZoomChange?: (scale: number) => void;
  } = {}
): [React.RefObject<HTMLElement>, number, (scale: number) => void] => {
  const { minScale = 0.5, maxScale = 3, onZoomChange } = options;
  const [scale, setScale] = useState(1);
  const elementRef = useRef<HTMLElement>(null);

  const updateScale = useCallback((newScale: number) => {
    const clampedScale = Math.max(minScale, Math.min(maxScale, newScale));
    setScale(clampedScale);
    onZoomChange?.(clampedScale);
  }, [minScale, maxScale, onZoomChange]);

  const bind = useGesture(
    {
      onPinch: ({ da: [d], event }) => {
        if (event.cancelable) {
          event.preventDefault();
        }
        updateScale(scale * (1 + d * 0.01));
      },
    },
    {
      target: elementRef,
      eventOptions: { passive: false },
    }
  );

  return [elementRef, scale, updateScale];
};