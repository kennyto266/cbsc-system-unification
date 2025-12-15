import { useState, useEffect, useRef, RefObject } from 'react';

interface IntersectionOptions extends IntersectionObserverInit {
  freezeOnceVisible?: boolean;
}

interface UseIntersectionObserverResult {
  ref: RefObject<Element>;
  isIntersecting: boolean;
  entry: IntersectionObserverEntry | null;
}

export const useIntersectionObserver = (
  options: IntersectionOptions = {}
): UseIntersectionObserverResult => {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0%',
    freezeOnceVisible = false,
  } = options;

  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const ref = useRef<Element>(null);
  const frozen = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setEntry(entry);

        if (freezeOnceVisible && entry.isIntersecting) {
          frozen.current = true;
          setIsIntersecting(true);
        } else {
          setIsIntersecting(entry.isIntersecting);
        }
      },
      {
        threshold,
        root,
        rootMargin,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [threshold, root, rootMargin, freezeOnceVisible]);

  return { ref, isIntersecting, entry };
};

interface LazyLoadOptions extends IntersectionOptions {
  onLoad?: () => void;
  onError?: () => void;
}

export const useLazyLoad = (
  options: LazyLoadOptions = {}
): UseIntersectionObserverResult & { hasLoaded: boolean; hasError: boolean } => {
  const [hasLoaded, setHasLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const { onLoad, onError, ...observerOptions } = options;

  const result = useIntersectionObserver({
    ...observerOptions,
    freezeOnceVisible: true,
  });

  useEffect(() => {
    if (result.isIntersecting && !hasLoaded && !hasError) {
      try {
        onLoad?.();
        setHasLoaded(true);
      } catch (error) {
        console.error('Error loading lazy content:', error);
        onError?.();
        setHasError(true);
      }
    }
  }, [result.isIntersecting, hasLoaded, hasError, onLoad, onError]);

  return {
    ...result,
    hasLoaded,
    hasError,
  };
};

interface UseInViewOptions extends IntersectionOptions {
  onChange?: (inView: boolean, entry: IntersectionObserverEntry) => void;
  triggerOnce?: boolean;
  skip?: boolean;
}

export const useInView = (
  options: UseInViewOptions = {}
): { ref: RefObject<Element>; inView: boolean; entry: IntersectionObserverEntry | null } => {
  const { onChange, triggerOnce = false, skip = false, ...observerOptions } = options;
  const [inView, setInView] = useState(false);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const ref = useRef<Element>(null);
  const triggered = useRef(false);

  useEffect(() => {
    if (skip) return;

    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setEntry(entry);
        const isInView = entry.isIntersecting;

        if (triggerOnce && isInView) {
          triggered.current = true;
        }

        setInView(isInView);
        onChange?.(isInView, entry);

        if (triggered.current) {
          observer.disconnect();
        }
      },
      observerOptions
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [skip, triggerOnce, onChange, observerOptions]);

  return { ref, inView, entry };
};

interface InfiniteScrollOptions {
  hasNextPage: boolean;
  fetchNextPage: () => Promise<any> | void;
  loading?: boolean;
  threshold?: number;
  rootMargin?: string;
  disabled?: boolean;
}

export const useInfiniteScroll = (options: InfiniteScrollOptions): {
  ref: RefObject<HTMLDivElement>;
  isIntersecting: boolean;
} => {
  const {
    hasNextPage,
    fetchNextPage,
    loading = false,
    threshold = 0,
    rootMargin = '200px',
    disabled = false,
  } = options;

  const { ref, isIntersecting } = useIntersectionObserver({
    threshold,
    rootMargin,
  });

  useEffect(() => {
    if (isIntersecting && hasNextPage && !loading && !disabled) {
      fetchNextPage();
    }
  }, [isIntersecting, hasNextPage, loading, disabled, fetchNextPage]);

  return { ref, isIntersecting };
};