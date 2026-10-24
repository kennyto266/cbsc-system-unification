import { useState, useCallback, useRef, useEffect } from 'react'

interface UseIntersectionObserverOptions {
  threshold?: number | number[]
  root?: Element | null
  rootMargin?: string
  triggerOnce?: boolean
}

interface UseIntersectionObserverReturn {
  isIntersecting: boolean
  entry?: IntersectionObserverEntry
  observer?: IntersectionObserver
}

export const useIntersectionObserver = (
  target: React.RefObject<Element>,
  options: UseIntersectionObserverOptions = {}
): UseIntersectionObserverReturn => {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0px',
    triggerOnce = false
  } = options

  const [isIntersecting, setIsIntersecting] = useState(false)
  const [entry, setEntry] = useState<IntersectionObserverEntry>()
  const observerRef = useRef<IntersectionObserver>()

  const updateEntry = useCallback(([entry]: IntersectionObserverEntry[]) => {
    setEntry(entry)
    setIsIntersecting(entry.isIntersecting)

    // 如果只触发一次且已进入视口，停止观察
    if (triggerOnce && entry.isIntersecting) {
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = undefined
      }
    }
  }, [triggerOnce])

  useEffect(() => {
    const targetElement = target.current

    if (!targetElement || !('IntersectionObserver' in window)) {
      return
    }

    // 创建 IntersectionObserver
    observerRef.current = new IntersectionObserver(updateEntry, {
      threshold,
      root,
      rootMargin
    })

    observerRef.current.observe(targetElement)

    return () => {
      // 清理
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = undefined
      }
    }
  }, [target, threshold, root, rootMargin, updateEntry])

  return {
    isIntersecting,
    entry,
    observer: observerRef.current
  }
}