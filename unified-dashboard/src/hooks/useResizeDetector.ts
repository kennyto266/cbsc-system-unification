import { useState, useEffect, useCallback } from 'react'
import { useRef } from 'react'

// Simple resize detector hook (lightweight alternative to react-resize-detector)
export const useResizeDetector = (options: {
  handleHeight?: boolean
  refreshMode?: 'throttle' | 'debounce'
  refreshRate?: number
}) => {
  const { handleHeight = true, refreshMode = 'throttle', refreshRate = 100 } = options
  const [size, setSize] = useState({ width: 0, height: 0 })
  const elementRef = useRef<HTMLElement | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const observe = useCallback((element: HTMLElement | null) => {
    // Clean up previous observer
    if (elementRef.current && elementRef.current !== element) {
      // No need for cleanup in this simple implementation
    }

    elementRef.current = element

    if (!element) return

    // Initial size
    const rect = element.getBoundingClientRect()
    setSize({
      width: rect.width,
      height: rect.height
    })

    // Create a resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect

        if (refreshMode === 'debounce') {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = setTimeout(() => {
            setSize({ width, height: handleHeight ? height : size.height })
          }, refreshRate)
        } else {
          // Throttle
          if (!timeoutRef.current) {
            timeoutRef.current = setTimeout(() => {
              setSize({ width, height: handleHeight ? height : size.height })
              timeoutRef.current = undefined
            }, refreshRate)
          }
        }
      }
    })

    resizeObserver.observe(element)

    return () => {
      resizeObserver.disconnect()
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [handleHeight, refreshMode, refreshRate, size.height])

  const ref = useCallback((node: HTMLElement | null) => {
    const cleanup = observe(node)
    return cleanup
  }, [observe])

  return {
    width: size.width,
    height: size.height,
    ref
  }
}