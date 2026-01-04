import React, { useRef, useCallback, useState, useEffect } from 'react';
import { clsx } from 'clsx';

export interface Point {
  x: number;
  y: number;
  timestamp: number;
}

export interface GestureState {
  isActive: boolean;
  startPoint: Point | null;
  currentPoint: Point | null;
  velocity: { x: number; y: number };
  distance: { x: number; y: number };
  duration: number;
  direction: 'left' | 'right' | 'up' | 'down' | null;
}

export interface GestureConfig {
  // Swipe configuration
  swipeThreshold: number; // Minimum distance for swipe
  swipeVelocityThreshold: number; // Minimum velocity for swipe
  swipeTimeout: number; // Maximum time for swipe gesture

  // Tap configuration
  tapTimeout: number; // Maximum time for tap
  tapThreshold: number; // Maximum movement for tap
  doubleTapTimeout: number; // Time between taps for double tap
  doubleTapThreshold: number; // Maximum movement between taps

  // Long press configuration
  longPressTimeout: number; // Minimum time for long press
  longPressThreshold: number; // Maximum movement for long press

  // Pinch configuration
  pinchThreshold: number; // Minimum distance change for pinch

  // Rotation configuration
  rotationThreshold: number; // Minimum angle change for rotation
}

export interface GestureCallbacks {
  // Single finger gestures
  onTap?: (point: Point) => void;
  onDoubleTap?: (point: Point) => void;
  onLongPress?: (point: Point) => void;
  onSwipe?: (direction: 'left' | 'right' | 'up' | 'down', velocity: { x: number; y: number }) => void;
  onPan?: (delta: { x: number; y: number }, state: GestureState) => void;
  onPanStart?: (point: Point) => void;
  onPanEnd?: (velocity: { x: number; y: number }) => void;

  // Multi-finger gestures
  onPinch?: (scale: number, center: Point) => void;
  onPinchStart?: (center: Point) => void;
  onPinchEnd?: () => void;
  onRotate?: (angle: number, center: Point) => void;
  onRotateStart?: (center: Point) => void;
  onRotateEnd?: () => void;

  // General events
  onTouchStart?: (touches: TouchList) => void;
  onTouchMove?: (touches: TouchList) => void;
  onTouchEnd?: (touches: TouchList) => void;
}

interface GestureRecognizerProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  config?: Partial<GestureConfig>;
  callbacks?: GestureCallbacks;
  preventDefault?: boolean;
  stopPropagation?: boolean;
}

/**
 * GestureRecognizer - Advanced touch gesture recognition for mobile
 */
const GestureRecognizer: React.FC<GestureRecognizerProps> = ({
  children,
  className,
  disabled = false,
  config = {},
  callbacks = {},
  preventDefault = true,
  stopPropagation = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const gestureStateRef = useRef<GestureState>({
    isActive: false,
    startPoint: null,
    currentPoint: null,
    velocity: { x: 0, y: 0 },
    distance: { x: 0, y: 0 },
    duration: 0,
    direction: null,
  });

  // Multi-touch state
  const touchesRef = useRef<Touch[]>([]);
  const initialDistanceRef = useRef<number>(0);
  const initialAngleRef = useRef<number>(0);

  // Timers
  const tapTimerRef = useRef<NodeJS.Timeout | null>(null);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const doubleTapTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastTapTimeRef = useRef<number>(0);
  const lastTapPointRef = useRef<Point | null>(null);

  // State for visual feedback
  const [isGesturing, setIsGesturing] = useState(false);

  // Default configuration
  const defaultConfig: GestureConfig = {
    swipeThreshold: 50,
    swipeVelocityThreshold: 500,
    swipeTimeout: 500,
    tapTimeout: 300,
    tapThreshold: 10,
    doubleTapTimeout: 300,
    doubleTapThreshold: 20,
    longPressTimeout: 500,
    longPressThreshold: 10,
    pinchThreshold: 20,
    rotationThreshold: 15,
  };

  const gestureConfig = { ...defaultConfig, ...config };

  // Calculate distance between two points
  const getDistance = (p1: Point | Touch, p2: Point | Touch): number => {
    const dx = p1.x - p2.x;
    const dy = p1.y - p2.y;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Calculate angle between two points
  const getAngle = (p1: Point | Touch, p2: Point | Touch): number => {
    return Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI;
  };

  // Calculate velocity
  const calculateVelocity = (p1: Point, p2: Point, deltaTime: number): { x: number; y: number } => {
    if (deltaTime === 0) return { x: 0, y: 0 };
    return {
      x: (p2.x - p1.x) / deltaTime * 1000,
      y: (p2.y - p1.y) / deltaTime * 1000,
    };
  };

  // Determine swipe direction
  const getSwipeDirection = (dx: number, dy: number): 'left' | 'right' | 'up' | 'down' => {
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    if (absDx > absDy) {
      return dx > 0 ? 'right' : 'left';
    } else {
      return dy > 0 ? 'down' : 'up';
    }
  };

  // Handle touch start
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (disabled) return;

    const touches = e.touches;
    touchesRef.current = Array.from(touches);

    if (preventDefault) e.preventDefault();
    if (stopPropagation) e.stopPropagation();

    const touch = touches[0];
    const now = Date.now();
    const point: Point = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: now,
    };

    // Update gesture state
    gestureStateRef.current = {
      isActive: true,
      startPoint: point,
      currentPoint: point,
      velocity: { x: 0, y: 0 },
      distance: { x: 0, y: 0 },
      duration: 0,
      direction: null,
    };

    setIsGesturing(true);

    // Clear existing timers
    if (tapTimerRef.current) clearTimeout(tapTimerRef.current);
    if (longPressTimerRef.current) clearTimeout(longPressTimerRef.current);

    // Handle multi-touch gestures
    if (touches.length === 2) {
      const distance = getDistance(touches[0], touches[1]);
      const angle = getAngle(touches[0], touches[1]);
      initialDistanceRef.current = distance;
      initialAngleRef.current = angle;

      const center: Point = {
        x: (touches[0].clientX + touches[1].clientX) / 2,
        y: (touches[0].clientY + touches[1].clientY) / 2,
        timestamp: now,
      };

      callbacks.onPinchStart?.(center);
      callbacks.onRotateStart?.(center);
    } else if (touches.length === 1) {
      // Single finger gestures

      // Set up long press timer
      longPressTimerRef.current = setTimeout(() => {
        const state = gestureStateRef.current;
        if (state.isActive && state.startPoint) {
          const distance = getDistance(state.startPoint, state.currentPoint!);
          if (distance <= gestureConfig.longPressThreshold) {
            callbacks.onLongPress?.(state.startPoint);
          }
        }
      }, gestureConfig.longPressTimeout);

      callbacks.onPanStart?.(point);
    }

    callbacks.onTouchStart?.(touches);
  }, [disabled, preventDefault, stopPropagation, callbacks, gestureConfig]);

  // Handle touch move
  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (disabled) return;

    const touches = e.touches;
    touchesRef.current = Array.from(touches);

    if (preventDefault) e.preventDefault();
    if (stopPropagation) e.stopPropagation();

    const now = Date.now();
    const state = gestureStateRef.current;

    if (!state.isActive || !state.startPoint) return;

    // Handle multi-touch gestures
    if (touches.length === 2) {
      const distance = getDistance(touches[0], touches[1]);
      const angle = getAngle(touches[0], touches[1]);
      const scale = distance / initialDistanceRef.current;
      const rotation = angle - initialAngleRef.current;

      const center: Point = {
        x: (touches[0].clientX + touches[1].clientX) / 2,
        y: (touches[0].clientY + touches[1].clientY) / 2,
        timestamp: now,
      };

      if (Math.abs(scale - 1) * 100 > gestureConfig.pinchThreshold) {
        callbacks.onPinch?.(scale, center);
      }

      if (Math.abs(rotation) > gestureConfig.rotationThreshold) {
        callbacks.onRotate?.(rotation, center);
      }
    } else if (touches.length === 1) {
      // Single finger gestures
      const touch = touches[0];
      const point: Point = {
        x: touch.clientX,
        y: touch.clientY,
        timestamp: now,
      };

      const dx = point.x - state.startPoint.x;
      const dy = point.y - state.startPoint.y;
      const deltaTime = now - state.startPoint.timestamp;

      // Check if we've exceeded tap threshold (cancel long press)
      const distance = getDistance(state.startPoint, point);
      if (distance > gestureConfig.longPressThreshold && longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = null;
      }

      // Update gesture state
      gestureStateRef.current = {
        ...state,
        currentPoint: point,
        velocity: calculateVelocity(state.startPoint, point, deltaTime),
        distance: { x: dx, y: dy },
        duration: deltaTime,
        direction: getSwipeDirection(dx, dy),
      };

      callbacks.onPan?.({ x: dx, y: dy }, gestureStateRef.current);
    }

    callbacks.onTouchMove?.(touches);
  }, [disabled, preventDefault, stopPropagation, callbacks, gestureConfig]);

  // Handle touch end
  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (disabled) return;

    const touches = e.changedTouches;
    const now = Date.now();
    const state = gestureStateRef.current;

    if (preventDefault) e.preventDefault();
    if (stopPropagation) e.stopPropagation();

    // Clear timers
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    if (!state.isActive || !state.startPoint || !state.currentPoint) {
      setIsGesturing(false);
      callbacks.onTouchEnd?.(touches);
      return;
    }

    const deltaTime = now - state.startPoint.timestamp;
    const distance = getDistance(state.startPoint, state.currentPoint);

    // Handle single finger gestures
    if (e.touches.length === 0) {
      // Check for tap
      if (distance <= gestureConfig.tapThreshold && deltaTime <= gestureConfig.tapTimeout) {
        // Check for double tap
        if (now - lastTapTimeRef.current <= gestureConfig.doubleTapTimeout) {
          if (lastTapPointRef.current) {
            const doubleTapDistance = getDistance(lastTapPointRef.current, state.startPoint);
            if (doubleTapDistance <= gestureConfig.doubleTapThreshold) {
              callbacks.onDoubleTap?.(state.startPoint);
              if (doubleTapTimerRef.current) {
                clearTimeout(doubleTapTimerRef.current);
                doubleTapTimerRef.current = null;
              }
              lastTapTimeRef.current = 0;
              lastTapPointRef.current = null;
            }
          }
        } else {
          // Single tap - delay to check for potential double tap
          lastTapTimeRef.current = now;
          lastTapPointRef.current = state.startPoint;

          tapTimerRef.current = setTimeout(() => {
            callbacks.onTap?.(state.startPoint!);
            lastTapTimeRef.current = 0;
            lastTapPointRef.current = null;
          }, gestureConfig.doubleTapTimeout);

          doubleTapTimerRef.current = setTimeout(() => {
            lastTapTimeRef.current = 0;
            lastTapPointRef.current = null;
          }, gestureConfig.doubleTapTimeout);
        }
      }

      // Check for swipe
      if (distance >= gestureConfig.swipeThreshold && deltaTime <= gestureConfig.swipeTimeout) {
        const velocity = Math.sqrt(
          state.velocity.x * state.velocity.x + state.velocity.y * state.velocity.y
        );

        if (velocity >= gestureConfig.swipeVelocityThreshold && state.direction) {
          callbacks.onSwipe?.(state.direction, state.velocity);
        }
      }

      callbacks.onPanEnd?.(state.velocity);
    }

    // Reset gesture state
    gestureStateRef.current = {
      isActive: false,
      startPoint: null,
      currentPoint: null,
      velocity: { x: 0, y: 0 },
      distance: { x: 0, y: 0 },
      duration: 0,
      direction: null,
    };

    setIsGesturing(false);
    callbacks.onTouchEnd?.(touches);
  }, [disabled, preventDefault, stopPropagation, callbacks, gestureConfig]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (tapTimerRef.current) clearTimeout(tapTimerRef.current);
      if (longPressTimerRef.current) clearTimeout(longPressTimerRef.current);
      if (doubleTapTimerRef.current) clearTimeout(doubleTapTimerRef.current);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={clsx(
        'touch-none',
        isGesturing && 'select-none',
        className
      )}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchEnd}
      style={{
        WebkitTapHighlightColor: 'transparent',
        WebkitTouchCallout: 'none',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      }}
    >
      {children}
    </div>
  );
};

export default GestureRecognizer;

// Export hook for easier usage
export const useGesture = () => {
  const recognize = (
    element: HTMLElement,
    config: Partial<GestureConfig>,
    callbacks: GestureCallbacks
  ) => {
    // Implementation for hook-based gesture recognition
    console.log('Setting up gesture recognition for element:', element);
  };

  return {
    recognize,
  };
};