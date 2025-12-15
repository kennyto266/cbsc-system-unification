'use client';

import React, { Suspense, lazy } from 'react';
import { Loader2 } from 'lucide-react';

interface LazyLoadProps {
  loader: () => Promise<{ default: React.ComponentType<any> }>;
  fallback?: React.ReactNode;
  error?: React.ComponentType<{ error: Error; retry: () => void }>;
  retry?: () => Promise<any>;
  delay?: number;
  children?: React.ReactNode;
}

// Default fallback component
const DefaultFallback = () => (
  <div className="flex items-center justify-center p-8">
    <div className="text-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
      <p className="text-sm text-gray-600 dark:text-gray-400">Loading...</p>
    </div>
  </div>
);

// Default error component
const DefaultError: React.FC<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <div className="flex items-center justify-center p-8">
    <div className="text-center max-w-md">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
        Failed to load component
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {error.message || 'An unexpected error occurred'}
      </p>
      <button
        onClick={retry}
        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
      >
        Try Again
      </button>
    </div>
  </div>
);

// Lazy load wrapper component
export function LazyLoad({
  loader,
  fallback = <DefaultFallback />,
  error: ErrorComponent = DefaultError,
  retry,
  delay = 200,
}: LazyLoadProps) {
  const [Component, setComponent] = React.useState<React.ComponentType<any> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const loadComponent = async () => {
      try {
        // Add delay to prevent flashing for fast loads
        if (delay > 0) {
          await new Promise(resolve => {
            timeoutId = setTimeout(resolve, delay);
          });
        }

        const module = await loader();
        setComponent(() => module.default);
        setLoading(false);
      } catch (err) {
        setLoadError(err as Error);
        setLoading(false);
      }
    };

    loadComponent();

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [loader, delay]);

  const handleRetry = async () => {
    setLoading(true);
    setLoadError(null);

    try {
      if (retry) {
        await retry();
      }
      const module = await loader();
      setComponent(() => module.default);
      setLoading(false);
    } catch (err) {
      setLoadError(err as Error);
      setLoading(false);
    }
  };

  if (loading) {
    return <>{fallback}</>;
  }

  if (loadError) {
    return <ErrorComponent error={loadError} retry={handleRetry} />;
  }

  if (!Component) {
    return null;
  }

  return (
    <Suspense fallback={fallback}>
      <Component />
    </Suspense>
  );
}

// Higher-order component for lazy loading
export function withLazyLoad<P extends object>(
  importFunc: () => Promise<{ default: React.ComponentType<P> }>,
  options: Omit<LazyLoadProps, 'loader'> & { displayName?: string } = {}
) {
  const LazyComponent = React.lazy(importFunc);
  const {
    fallback = <DefaultFallback />,
    error: ErrorComponent = DefaultError,
  } = options;

  const WrappedComponent = (props: P) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );

  WrappedComponent.displayName = options.displayName || 'WithLazyLoad';

  return WrappedComponent;
}

// Intersection Observer lazy load for images and components
interface IntersectionLazyLoadProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  rootMargin?: string;
  threshold?: number;
  className?: string;
}

export function IntersectionLazyLoad({
  children,
  fallback = <DefaultFallback />,
  rootMargin = '50px',
  threshold = 0.1,
  className = '',
}: IntersectionLazyLoadProps) {
  const [isVisible, setIsVisible] = React.useState(false);
  const elementRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      {
        rootMargin,
        threshold,
      }
    );

    const element = elementRef.current;
    if (element) {
      observer.observe(element);
    }

    return () => {
      if (element) {
        observer.unobserve(element);
      }
      observer.disconnect();
    };
  }, [rootMargin, threshold]);

  return (
    <div ref={elementRef} className={className}>
      {isVisible ? children : fallback}
    </div>
  );
}

// Virtual list for large datasets
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
}

export function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className = '',
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleScroll = React.useCallback(() => {
    if (containerRef.current) {
      setScrollTop(containerRef.current.scrollTop);
    }
  }, []);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: items.length * itemHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div
              key={startIndex + index}
              style={{ height: itemHeight }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Preload utilities
export const preloadComponent = (importFunc: () => Promise<any>) => {
  return importFunc();
};

// Preload multiple components
export const preloadComponents = (importFuncs: Array<() => Promise<any>>) => {
  return Promise.all(importFuncs.map(func => func()));
};

// Dynamic import with prefetch
export const dynamicImport = (importFunc: () => Promise<any>) => {
  // Prefetch the component
  importFunc();

  // Return lazy component
  return React.lazy(importFunc);
};