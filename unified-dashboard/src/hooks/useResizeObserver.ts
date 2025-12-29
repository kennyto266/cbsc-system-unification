import { useState, useCallback, useRef, useEffect } from 'react'

interface UseResizeObserverOptions {
  debounceMs?: number
}

interface UseResizeObserverReturn {
  width: number | undefined
  height: number | undefined
}

export const useResizeObserver = (
  target: React.RefObject<Element>,
  options: UseResizeObserverOptions = {}
): UseResizeObserverReturn => {
  const { debounceMs = 100 } = options
  const [dimensions, setDimensions] = useState<{ width?: number; height?: number }>({
    width: undefined,
    height: undefined
  })

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()
  const observerRef = useRef<ResizeObserver>()

  const updateDimensions = useCallback((entries: ResizeObserverEntry[]) => {
    const entry = entries[0]

    // 清除之前的防抖
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // 防抖处理
    debounceTimeoutRef.current = setTimeout(() => {
      const { width, height } = entry.contentRect
      setDimensions({ width, height })
    }, debounceMs)
  }, [debounceMs])

  useEffect(() => {
    const targetElement = target.current

    if (!targetElement) {
      return
    }

    // 创建 ResizeObserver
    observerRef.current = new ResizeObserver(updateDimensions)
    observerRef.current.observe(targetElement)

    return () => {
      // 清理
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = undefined
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [target, updateDimensions])

  return dimensions
}