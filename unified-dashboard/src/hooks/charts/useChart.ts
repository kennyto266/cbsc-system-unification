import { useRef, useState, useEffect, useCallback } from 'react'
import { Chart as ChartJS } from 'chart.js'

export interface UseChartOptions {
  responsive?: boolean
  maintainAspectRatio?: boolean
  animation?: boolean | any
  resizeDelay?: number
  onResize?: (chart: ChartJS, size: { width: number; height: number }) => void
  onDestroy?: () => void
}

export const useChart = (options: UseChartOptions = {}) => {
  const chartRef = useRef<ChartJS | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  // Resize observer for container
  const resizeObserver = useRef<ResizeObserver | null>(null)

  // Initialize chart
  const initChart = useCallback((chartInstance: ChartJS) => {
    chartRef.current = chartInstance
    setIsInitialized(true)

    // Set up resize observer if responsive
    if (options.resizeDelay && containerRef.current) {
      resizeObserver.current = new ResizeObserver(
        debounce((entries) => {
          const entry = entries[0]
          if (entry) {
            const { width, height } = entry.contentRect
            setDimensions({ width, height })

            if (chartRef.current && options.onResize) {
              options.onResize(chartRef.current, { width, height })
            }
          }
        }, options.resizeDelay)
      )

      resizeObserver.current.observe(containerRef.current)
    }
  }, [options])

  // Update chart
  const updateChart = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.update()
    }
  }, [])

  // Destroy chart
  const destroyChart = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.destroy()
      chartRef.current = null
      setIsInitialized(false)

      if (resizeObserver.current) {
        resizeObserver.current.disconnect()
        resizeObserver.current = null
      }

      options.onDestroy?.()
    }
  }, [options])

  // Get chart instance
  const getChart = useCallback(() => chartRef.current, [])

  // Export chart
  const exportChart = useCallback(async (format: 'png' | 'jpg' | 'svg' = 'png', quality = 1) => {
    if (!chartRef.current) return null

    const canvas = chartRef.current.canvas
    if (!canvas) return null

    switch (format) {
      case 'png':
        return canvas.toDataURL(`image/${format}`, quality)
      case 'jpg':
        return canvas.toDataURL('image/jpeg', quality)
      case 'svg':
        // For SVG export, you'd need additional library or custom implementation
        console.warn('SVG export requires additional implementation')
        return null
      default:
        return null
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      destroyChart()
    }
  }, [destroyChart])

  return {
    chartRef,
    containerRef,
    isInitialized,
    dimensions,
    initChart,
    updateChart,
    destroyChart,
    getChart,
    exportChart,
  }
}

// Utility debounce function
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}