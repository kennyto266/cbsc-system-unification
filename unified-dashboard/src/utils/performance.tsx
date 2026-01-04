// Performance optimization utilities
import React from 'react'

// Debounce function
export function debounce<TFunc extends (...args: any[]) => any>(
  func: TFunc,
  wait: number,
  immediate?: boolean
): (...args: any[]) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: any[]): void {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }

    const callNow = immediate && !timeout

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)

    if (callNow) func(...args)
  }
}

// Throttle function
export function throttle<TFunc extends (...args: any[]) => any>(
  func: TFunc,
  limit: number
): (...args: any[]) => void {
  let inThrottle: boolean

  return function executedFunction(...args: any[]): void {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// Memoize function
export function memoize<TFunc extends (...args: any[]) => any>(func: TFunc): TFunc {
  const cache = new Map()

  const executedFunction = function (...args: any[]): any {
    const key = JSON.stringify(args)

    if (cache.has(key)) {
      return cache.get(key)
    }

    const result = func(...args)
    cache.set(key, result)
    return result
  }

  return executedFunction as TFunc
}

// Lazy load component
export function lazyLoad<TComponent extends React.ComponentType<any>>(
  importFunc: () => Promise<{ default: TComponent }>,
  fallback?: React.ComponentType
) {
  const LazyComponent = React.lazy(importFunc)

  return function LazyWrapper(props: React.ComponentProps<TComponent>) {
    return (
      <React.Suspense fallback={fallback ? React.createElement(fallback) : <div>Loading...</div>}>
        <LazyComponent {...props} />
      </React.Suspense>
    )
  }
}

// Intersection Observer for lazy loading
export function useIntersectionObserver(
  elementRef: React.RefObject<Element>,
  options?: IntersectionObserverInit
) {
  const [isIntersecting, setIsIntersecting] = React.useState(false)

  React.useEffect(() => {
    const element = elementRef.current
    if (!element) return

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting)
    }, options)

    observer.observe(element)

    return () => {
      observer.unobserve(element)
    }
  }, [elementRef, options])

  return isIntersecting
}

// Virtual scroll utilities
export function calculateVisibleItems<T>(
  items: T[],
  containerHeight: number,
  itemHeight: number,
  scrollTop: number,
  overscan: number = 5
): { visibleItems: T[][]; startIndex: number; endIndex: number } {
  const itemCount = items.length
  const viewportItems = Math.ceil(containerHeight / itemHeight)

  let startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  let endIndex = Math.min(
    itemCount - 1,
    startIndex + viewportItems + overscan * 2
  )

  startIndex = Math.max(0, startIndex - overscan)

  const visibleItems = items.slice(startIndex, endIndex + 1)

  return { visibleItems: [visibleItems], startIndex, endIndex }
}

// Performance monitoring
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics: Map<string, number[]> = new Map()

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  startTimer(name: string): () => void {
    const startTime = performance.now()

    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime

      if (!this.metrics.has(name)) {
        this.metrics.set(name, [])
      }

      this.metrics.get(name)!.push(duration)

      // Keep only last 100 measurements
      const measurements = this.metrics.get(name)!
      if (measurements.length > 100) {
        measurements.shift()
      }
    }
  }

  getAverageTime(name: string): number {
    const measurements = this.metrics.get(name) || []
    if (measurements.length === 0) return 0

    const sum = measurements.reduce((a, b) => a + b, 0)
    return sum / measurements.length
  }

  getMetrics(): Record<string, { avg: number; min: number; max: number; count: number }> {
    const result: Record<string, { avg: number; min: number; max: number; count: number }> = {}

    for (const [name, measurements] of this.metrics) {
      if (measurements.length === 0) continue

      const avg = measurements.reduce((a, b) => a + b, 0) / measurements.length
      const min = Math.min(...measurements)
      const max = Math.max(...measurements)

      result[name] = { avg, min, max, count: measurements.length }
    }

    return result
  }
}

// Bundle size optimization
export function preloadComponent(importFunc: () => Promise<any>) {
  // Preload component when user is idle
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      importFunc()
    })
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      importFunc()
    }, 1000)
  }
}

// Image optimization utilities
export function getOptimizedImageUrl(
  url: string,
  width?: number,
  height?: number,
  quality: number = 80
): string {
  if (!url) return url

  // If it's already a data URL or external, return as is
  if (url.startsWith('data:') || url.startsWith('http')) {
    return url
  }

  // Add optimization parameters for local images
  const params = new URLSearchParams()
  if (width) params.set('w', width.toString())
  if (height) params.set('h', height.toString())
  params.set('q', quality.toString())

  return `${url}?${params.toString()}`
}

// Animation performance utilities
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function createOptimizedAnimation(
  element: Element,
  keyframes: Keyframe[],
  options?: KeyframeAnimationOptions
): Animation {
  const defaultOptions: KeyframeAnimationOptions = {
    duration: 300,
    easing: 'ease-out',
    fill: 'forwards'
  }

  // Reduce animations if user prefers reduced motion
  if (prefersReducedMotion()) {
    return element.animate(keyframes, { ...defaultOptions, duration: 0 })
  }

  return element.animate(keyframes, { ...defaultOptions, ...options })
}

// Memory optimization
export function cleanupObject<TObj extends Record<string, any>>(obj: TObj): Partial<TObj> {
  const cleaned: Partial<TObj> = {}

  for (const key in obj) {
    const value = obj[key]

    // Skip null, undefined, and empty values
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        // Clean arrays recursively
        const cleanedArray = value
          .map(item => typeof item === 'object' ? cleanupObject(item) : item)
          .filter(item => item !== null && item !== undefined && item !== '')

        if (cleanedArray.length > 0) {
          cleaned[key] = cleanedArray as any
        }
      } else if (typeof value === 'object' && !(value instanceof Date)) {
        // Clean objects recursively
        const cleanedObj = cleanupObject(value)
        if (Object.keys(cleanedObj).length > 0) {
          cleaned[key] = cleanedObj
        }
      } else {
        cleaned[key] = value
      }
    }
  }

  return cleaned
}

// Resource monitoring
export function getResourceUsage(): {
  memory: MemoryInfo | undefined
  connection: NetworkInformation | undefined
  cores: number
} {
  return {
    memory: (performance as any).memory,
    connection: (navigator as any).connection,
    cores: navigator.hardwareConcurrency || 4
  }
}

// FPS monitoring
export function createFPSMonitor(callback: (fps: number) => void) {
  let lastTime = performance.now()
  let frames = 0

  function checkFPS() {
    frames++
    const currentTime = performance.now()

    if (currentTime >= lastTime + 1000) {
      const fps = Math.round((frames * 1000) / (currentTime - lastTime))
      callback(fps)
      frames = 0
      lastTime = currentTime
    }

    requestAnimationFrame(checkFPS)
  }

  return {
    start: () => requestAnimationFrame(checkFPS),
    stop: () => {
      // Implementation would need to store the request ID to cancel
    }
  }
}
