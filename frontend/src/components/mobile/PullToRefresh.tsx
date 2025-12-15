import React, { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';

interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void> | void;
  className?: string;
  disabled?: boolean;
  threshold?: number;
  resistance?: number;
  pullDownContent?: React.ReactNode;
  releaseContent?: React.ReactNode;
  refreshingContent?: React.ReactNode;
}

/**
 * PullToRefresh component for mobile下拉刷新
 */
const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  className,
  disabled = false,
  threshold = 60,
  resistance = 2.5,
  pullDownContent,
  releaseContent,
  refreshingContent,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPulling, setIsPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [canRelease, setCanRelease] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number>(0);
  const currentY = useRef<number>(0);
  const isDragging = useRef<boolean>(false);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (disabled || isRefreshing) return;

    const touch = e.touches[0];
    startY.current = touch.clientY;
    currentY.current = touch.clientY;
    isDragging.current = true;

    // Only allow pull to refresh when at the top
    if (containerRef.current) {
      const { scrollTop } = containerRef.current;
      if (scrollTop > 0) {
        isDragging.current = false;
      }
    }
  }, [disabled, isRefreshing]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isDragging.current || disabled || isRefreshing) return;

    const touch = e.touches[0];
    currentY.current = touch.clientY;
    const distance = (currentY.current - startY.current) / resistance;

    if (distance > 0) {
      e.preventDefault();
      setPullDistance(Math.min(distance, threshold * 1.5));
      setIsPulling(true);
      setCanRelease(distance >= threshold);
    }
  }, [disabled, isRefreshing, threshold, resistance]);

  const handleTouchEnd = useCallback(async () => {
    if (!isDragging.current || disabled) return;

    isDragging.current = false;

    if (pullDistance >= threshold && !isRefreshing) {
      // Trigger refresh
      setIsRefreshing(true);
      setCanRelease(false);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
        setIsPulling(false);
      }
    } else {
      // Reset
      setPullDistance(0);
      setIsPulling(false);
      setCanRelease(false);
    }
  }, [disabled, pullDistance, threshold, isRefreshing, onRefresh]);

  // Default content components
  const defaultPullDownContent = (
    <div className="flex items-center justify-center gap-2 text-gray-500">
      <RefreshCw className="w-5 h-5" />
      <span className="text-sm">下拉刷新</span>
    </div>
  );

  const defaultReleaseContent = (
    <div className="flex items-center justify-center gap-2 text-primary-600">
      <RefreshCw className="w-5 h-5 animate-bounce" />
      <span className="text-sm">釋放刷新</span>
    </div>
  );

  const defaultRefreshingContent = (
    <div className="flex items-center justify-center gap-2 text-primary-600">
      <RefreshCw className="w-5 h-5 animate-spin" />
      <span className="text-sm">刷新中...</span>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className={clsx(
        'relative h-full overflow-hidden',
        className
      )}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <motion.div
        className="absolute top-0 left-0 right-0 flex items-center justify-center pointer-events-none z-10"
        style={{
          height: threshold,
          transform: `translateY(${Math.max(0, pullDistance - threshold)}px)`,
          opacity: isPulling ? 1 : 0,
        }}
      >
        {isRefreshing ? (
          refreshingContent || defaultRefreshingContent
        ) : canRelease ? (
          releaseContent || defaultReleaseContent
        ) : (
          pullDownContent || defaultPullDownContent
        )}
      </motion.div>

      {/* Content container */}
      <motion.div
        className="h-full"
        style={{
          transform: isPulling ? `translateY(${pullDistance}px)` : 'translateY(0)',
          transition: isDragging.current ? 'none' : 'transform 0.3s ease-out',
        }}
      >
        {children}
      </motion.div>
    </div>
  );
};

export default PullToRefresh;