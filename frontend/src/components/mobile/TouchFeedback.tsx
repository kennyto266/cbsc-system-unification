import React, { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface TouchFeedbackProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  scale?: number;
  opacity?: number;
  ripple?: boolean;
  rippleColor?: string;
  onPress?: () => void;
  onRelease?: () => void;
  onTap?: () => void;
  onLongPress?: () => void;
  longPressDelay?: number;
}

/**
 * TouchFeedback component provides visual feedback for touch interactions
 */
const TouchFeedback: React.FC<TouchFeedbackProps> = ({
  children,
  className,
  disabled = false,
  scale = 0.95,
  opacity = 0.7,
  ripple = true,
  rippleColor = 'rgba(255, 255, 255, 0.5)',
  onPress,
  onRelease,
  onTap,
  onLongPress,
  longPressDelay = 500,
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number; size: number }>>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const rippleIdRef = useRef(0);

  const handlePressStart = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (disabled) return;

    setIsPressed(true);
    onPress?.();

    // Create ripple effect
    if (ripple && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      let x: number;
      let y: number;

      if ('touches' in e) {
        x = e.touches[0].clientX - rect.left;
        y = e.touches[0].clientY - rect.top;
      } else {
        x = e.clientX - rect.left;
        y = e.clientY - rect.top;
      }

      const size = Math.max(rect.width, rect.height);
      const newRipple = {
        id: rippleIdRef.current++,
        x,
        y,
        size,
      };

      setRipples(prev => [...prev, newRipple]);

      // Remove ripple after animation
      setTimeout(() => {
        setRipples(prev => prev.filter(r => r.id !== newRipple.id));
      }, 600);
    }

    // Handle long press
    if (onLongPress) {
      longPressTimerRef.current = setTimeout(() => {
        onLongPress();
      }, longPressDelay);
    }
  }, [disabled, ripple, onPress, onLongPress, longPressDelay]);

  const handlePressEnd = useCallback(() => {
    if (disabled) return;

    setIsPressed(false);
    onRelease?.();
    onTap?.();

    // Clear long press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, [disabled, onRelease, onTap]);

  // Cleanup long press timer on unmount
  React.useEffect(() => {
    return () => {
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, []);

  return (
    <motion.div
      ref={containerRef}
      className={clsx(
        'touch-feedback',
        'relative overflow-hidden cursor-pointer select-none',
        disabled && 'cursor-default opacity-50',
        className
      )}
      whileTap={disabled ? {} : { scale }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onMouseDown={handlePressStart}
      onMouseUp={handlePressEnd}
      onMouseLeave={handlePressEnd}
      onTouchStart={handlePressStart}
      onTouchEnd={handlePressEnd}
      onTouchCancel={handlePressEnd}
      style={{
        WebkitTapHighlightColor: 'transparent',
        WebkitTouchCallout: 'none',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      }}
    >
      {/* Overlay for opacity effect */}
      {isPressed && !disabled && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.1 }}
          style={{
            backgroundColor: rippleColor,
          }}
        />
      )}

      {/* Ripple effects */}
      {ripples.map(ripple => (
        <motion.div
          key={ripple.id}
          className="absolute rounded-full pointer-events-none"
          initial={{
            width: 0,
            height: 0,
            x: ripple.x,
            y: ripple.y,
          }}
          animate={{
            width: ripple.size * 2,
            height: ripple.size * 2,
            x: ripple.x - ripple.size,
            y: ripple.y - ripple.size,
            opacity: [0.5, 0],
          }}
          transition={{
            duration: 0.6,
            ease: 'easeOut',
          }}
          style={{
            backgroundColor: rippleColor,
          }}
        />
      ))}

      {/* Children */}
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

export default TouchFeedback;

/**
 * Simple touchable component for buttons
 */
interface TouchableProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  onPress?: () => void;
  onLongPress?: () => void;
}

export const Touchable: React.FC<TouchableProps> = ({
  children,
  className,
  disabled = false,
  onPress,
  onLongPress,
}) => {
  return (
    <TouchFeedback
      className={className}
      disabled={disabled}
      onPress={onPress}
      onLongPress={onLongPress}
      onTap={onPress}
      scale={0.98}
      opacity={0.8}
    >
      {children}
    </TouchFeedback>
  );
};