import React, { useRef, useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { clsx } from 'clsx';

interface SwipeContainerProps {
  children: React.ReactNode[];
  className?: string;
  itemClassName?: string;
  index?: number;
  onChange?: (index: number) => void;
  enableSwipe?: boolean;
  threshold?: number;
  resistance?: number;
  loop?: boolean;
  autoplay?: boolean;
  autoplayDelay?: number;
  pauseOnHover?: boolean;
  showDots?: boolean;
  showArrows?: boolean;
  vertical?: boolean;
}

/**
 * SwipeContainer - Touch-friendly carousel/swipe container for mobile
 */
const SwipeContainer: React.FC<SwipeContainerProps> = ({
  children,
  className,
  itemClassName,
  index: controlledIndex,
  onChange,
  enableSwipe = true,
  threshold = 50,
  resistance = 0.5,
  loop = false,
  autoplay = false,
  autoplayDelay = 3000,
  pauseOnHover = true,
  showDots = true,
  showArrows = false,
  vertical = false,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const autoplayRef = useRef<NodeJS.Timeout | null>(null);

  // Use controlled index if provided
  const activeIndex = controlledIndex !== undefined ? controlledIndex : currentIndex;
  const isControlled = controlledIndex !== undefined;

  const handlePageChange = useCallback((newIndex: number) => {
    if (isControlled) {
      onChange?.(newIndex);
    } else {
      setCurrentIndex(newIndex);
      onChange?.(newIndex);
    }
  }, [isControlled, onChange]);

  // Navigation functions
  const goToPrevious = useCallback(() => {
    if (loop) {
      handlePageChange(activeIndex === 0 ? children.length - 1 : activeIndex - 1);
    } else {
      handlePageChange(Math.max(0, activeIndex - 1));
    }
  }, [activeIndex, children.length, loop, handlePageChange]);

  const goToNext = useCallback(() => {
    if (loop) {
      handlePageChange(activeIndex === children.length - 1 ? 0 : activeIndex + 1);
    } else {
      handlePageChange(Math.min(children.length - 1, activeIndex + 1));
    }
  }, [activeIndex, children.length, loop, handlePageChange]);

  const goToIndex = useCallback((index: number) => {
    if (index >= 0 && index < children.length) {
      handlePageChange(index);
    }
  }, [children.length, handlePageChange]);

  // Autoplay
  useEffect(() => {
    if (autoplay && !isPaused && children.length > 1) {
      autoplayRef.current = setTimeout(goToNext, autoplayDelay);
    }

    return () => {
      if (autoplayRef.current) {
        clearTimeout(autoplayRef.current);
      }
    };
  }, [autoplay, isPaused, children.length, goToNext, autoplayDelay, activeIndex]);

  // Drag handlers
  const handleDragStart = () => {
    if (!enableSwipe) return;
    setIsDragging(true);
    if (pauseOnHover) {
      setIsPaused(true);
    }
  };

  const handleDragEnd = (event: any, info: PanInfo) => {
    if (!enableSwipe) return;

    setIsDragging(false);
    if (pauseOnHover) {
      setIsPaused(false);
    }

    const { offset, velocity } = info;
    const direction = vertical ? offset.y : offset.x;
    const vel = vertical ? velocity.y : velocity.x;

    // Check if swipe meets threshold or has sufficient velocity
    if (Math.abs(direction) > threshold || Math.abs(vel) > 500) {
      if (direction > 0) {
        goToPrevious();
      } else {
        goToNext();
      }
    }
  };

  // Touch/Crossfade animation variants
  const variants = {
    enter: {
      x: vertical ? '100%' : '100%',
      opacity: 0,
    },
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1,
    },
    exit: {
      zIndex: 0,
      x: vertical ? '-100%' : '-100%',
      opacity: 0,
    },
  };

  const swipeConfidenceThreshold = 10000;
  const swipePower = (offset: number, velocity: number) => {
    return Math.abs(offset) * velocity;
  };

  const paginate = (direction: number) => {
    if (direction > 0) {
      goToNext();
    } else if (direction < 0) {
      goToPrevious();
    }
  };

  return (
    <div className={clsx('relative overflow-hidden', className)}>
      {/* Main container */}
      <div
        ref={containerRef}
        className="relative touch-pan-y"
        onMouseEnter={() => pauseOnHover && setIsPaused(true)}
        onMouseLeave={() => pauseOnHover && setIsPaused(false)}
      >
        <AnimatePresence initial={false} custom={vertical}>
          <motion.div
            key={activeIndex}
            custom={vertical}
            className={clsx('w-full', itemClassName)}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: 'spring', stiffness: 300, damping: 30 },
              opacity: { duration: 0.2 },
            }}
            drag={enableSwipe ? (vertical ? 'y' : 'x') : false}
            dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
            dragElastic={resistance}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDrag={(event, info) => {
              const swipe = swipePower(
                vertical ? info.offset.y : info.offset.x,
                vertical ? info.velocity.y : info.velocity.x
              );
              if (swipe < -swipeConfidenceThreshold) {
                paginate(1);
              } else if (swipe > swipeConfidenceThreshold) {
                paginate(-1);
              }
            }}
          >
            {children[activeIndex]}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation arrows */}
      {showArrows && children.length > 1 && (
        <>
          <button
            onClick={goToPrevious}
            disabled={!loop && activeIndex === 0}
            className={clsx(
              'absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 shadow-lg flex items-center justify-center transition-all',
              'hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed z-10'
            )}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={goToNext}
            disabled={!loop && activeIndex === children.length - 1}
            className={clsx(
              'absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 shadow-lg flex items-center justify-center transition-all',
              'hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed z-10'
            )}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </>
      )}

      {/* Dots indicator */}
      {showDots && children.length > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 z-10">
          {children.map((_, index) => (
            <button
              key={index}
              onClick={() => goToIndex(index)}
              className={clsx(
                'transition-all duration-200',
                index === activeIndex
                  ? 'w-8 h-2 bg-primary-600 rounded-full'
                  : 'w-2 h-2 bg-gray-400 rounded-full hover:bg-gray-600'
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default SwipeContainer;