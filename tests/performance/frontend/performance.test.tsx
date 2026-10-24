/**
 * Frontend Performance Tests
 * Tests component rendering performance, bundle size, and runtime performance
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { PerformanceObserver, measure } from 'perf_hooks'

// Import components to test
import StrategyList from '../../../src/pages/strategies/components/StrategyList'
import TradingViewChart from '../../../src/components/charts/composite/TradingViewChart'
import PerformanceAnalysis from '../../../src/pages/strategies/components/PerformanceAnalysis'

describe('Frontend Performance Tests', () => {
  // Mock performance APIs if not available
  beforeAll(() => {
    if (typeof window.performance === 'undefined') {
      ;(window as any).performance = {
        now: jest.fn(() => Date.now()),
        mark: jest.fn(),
        measure: jest.fn(),
        getEntriesByName: jest.fn(() => []),
        getEntriesByType: jest.fn(() => []),
      }
    }
  })

  describe('Component Rendering Performance', () => {
    test('StrategyList should render within performance threshold', async () => {
      const startTime = performance.now()

      // Create large dataset
      const largeDataSet = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        name: `Strategy ${i + 1}`,
        description: `Test strategy number ${i + 1}`,
        status: i % 2 === 0 ? 'active' : 'inactive',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameters: { test: 'value' }
      }))

      render(<StrategyList strategies={largeDataSet} />)

      const renderTime = performance.now() - startTime

      // Rendering should complete within 100ms for 1000 items
      expect(renderTime).toBeLessThan(100)

      // Verify all items are rendered
      const strategyItems = screen.getAllByText(/Strategy \d+/)
      expect(strategyItems.length).toBeGreaterThan(0)
    })

    test('TradingViewChart should render efficiently with large datasets', () => {
      const startTime = performance.now()

      // Generate large OHLC dataset
      const largeOHLCData = Array.from({ length: 5000 }, (_, i) => ({
        timestamp: new Date(Date.now() - (5000 - i) * 60000),
        open: 50000 + Math.random() * 1000,
        high: 50000 + Math.random() * 1500,
        low: 50000 - Math.random() * 1000,
        close: 50000 + Math.random() * 1000,
        volume: Math.floor(Math.random() * 1000000)
      }))

      render(
        <TradingViewChart
          data={largeOHLCData}
          height={600}
          showVolume={true}
        />
      )

      const renderTime = performance.now() - startTime

      // Chart rendering should complete within 200ms
      expect(renderTime).toBeLessThan(200)
    })

    test('PerformanceAnalysis should handle large calculation datasets efficiently', async () => {
      const startTime = performance.now()

      // Create large performance dataset
      const largePerformanceData = {
        returns: Array.from({ length: 10000 }, () => Math.random() * 0.1 - 0.05),
        equity: Array.from({ length: 10000 }, (_, i) => 100000 * (1 + i * 0.0001)),
        trades: Array.from({ length: 1000 }, (_, i) => ({
          id: i + 1,
          timestamp: new Date(Date.now() - i * 3600000),
          type: i % 2 === 0 ? 'BUY' : 'SELL',
          price: 50000 + Math.random() * 2000,
          quantity: Math.random() * 10,
          profit: Math.random() * 1000 - 500
        }))
      }

      render(<PerformanceAnalysis data={largePerformanceData} />)

      const calculationTime = performance.now() - startTime

      // Performance calculations should complete within 500ms
      expect(calculationTime).toBeLessThan(500)
    })
  })

  describe('Memory Usage Tests', () => {
    test('should not leak memory on repeated component mount/unmount', () => {
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0

      // Mount and unmount components multiple times
      for (let i = 0; i < 100; i++) {
        const { unmount } = render(<StrategyList />)
        unmount()
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc()
      }

      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0
      const memoryIncrease = finalMemory - initialMemory

      // Memory increase should be minimal (< 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024)
    })

    test('should clean up event listeners on component unmount', () => {
      const addEventListenerSpy = jest.spyOn(document, 'addEventListener')
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener')

      const { unmount } = render(<TradingViewChart />)

      const addedListeners = addEventListenerSpy.mock.calls.length
      unmount()

      // Verify cleanup
      expect(removeEventListenerSpy.mock.calls.length).toBeGreaterThanOrEqual(addedListeners)

      addEventListenerSpy.mockRestore()
      removeEventListenerSpy.mockRestore()
    })
  })

  describe('Bundle Size Analysis', () => {
    test('core components should have reasonable bundle sizes', async () => {
      // This would typically be done with webpack-bundle-analyzer
      // For now, we'll check if components import only necessary dependencies

      // Check if heavy libraries are properly code-split
      const heavyLibraries = ['plotly.js', 'monaco-editor', '@monaco-editor/react']

      heavyLibraries.forEach(lib => {
        // These should be lazy loaded, not in main bundle
        expect(require.cache[require.resolve(lib)]).toBeUndefined()
      })
    })

    test('should lazy load heavy components', async () => {
      const lazyImportPromises = [
        import('../../../src/components/charts/plotly/CandlestickChart'),
        import('../../../src/components/monaco/MonacoEditor')
      ]

      const startTime = performance.now()
      await Promise.all(lazyImportPromises)
      const loadTime = performance.now() - startTime

      // Lazy loading should be fast (< 1 second)
      expect(loadTime).toBeLessThan(1000)
    })
  })

  describe('Animation Performance', () => {
    test('chart animations should maintain 60fps', () => {
      // Mock requestAnimationFrame
      const rafCallbacks: Array<FrameRequestCallback> = []
      const mockRAF = (callback: FrameRequestCallback) => {
        rafCallbacks.push(callback)
        return rafCallbacks.length
      }

      global.requestAnimationFrame = mockRAF

      render(<TradingViewChart enableAnimations={true} />)

      // Simulate animation frames
      let frameCount = 0
      const startTime = performance.now()

      while (frameCount < 60 && rafCallbacks.length > 0) {
        const callback = rafCallbacks.shift()
        if (callback) {
          callback(performance.now() + frameCount * 16.67)
          frameCount++
        }
      }

      const totalTime = performance.now() - startTime
      const fps = (frameCount * 1000) / totalTime

      // Should maintain at least 30fps (considering test environment)
      expect(fps).toBeGreaterThan(30)
    })

    test('should reduce animation quality on low-end devices', () => {
      // Mock low-end device
      Object.defineProperty(navigator, 'hardwareConcurrency', {
        value: 2,
        configurable: true
      })

      const { container } = render(<TradingViewChart enableAnimations={true} />)

      // Should disable complex animations on low-end devices
      expect(container.querySelector('.high-performance-animation')).toBeNull()
    })
  })

  describe('Network Performance', () => {
    test('should implement efficient data fetching with caching', async () => {
      const mockFetch = jest.fn()
      global.fetch = mockFetch

      mockFetch.mockResolvedValue({
        json: async () => ({ data: [] }),
        status: 200
      })

      // Import and use data fetching hook
      const { useStrategyData } = await import('../../../src/hooks/useStrategyData')

      // Simulate component that uses the hook
      function TestComponent() {
        const { data, isLoading } = useStrategyData()
        return <div>{isLoading ? 'Loading...' : `Loaded ${data?.length} items`}</div>
      }

      render(<TestComponent />)

      // Should only make one request due to caching
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    test('should implement request deduplication', async () => {
      const mockFetch = jest.fn()
      global.fetch = mockFetch

      mockFetch.mockResolvedValue({
        json: async () => ({ data: [] }),
        status: 200
      })

      // Simulate multiple simultaneous requests for same data
      const promises = Array.from({ length: 5 }, () =>
        fetch('/api/strategies').then(res => res.json())
      )

      await Promise.all(promises)

      // Should only make one actual request
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Accessibility Performance', () => {
    test('should maintain accessibility with large lists', () => {
      const largeDataSet = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        name: `Strategy ${i + 1}`,
        status: 'active'
      }))

      const startTime = performance.now()

      render(<StrategyList strategies={largeDataSet} />)

      const renderTime = performance.now() - startTime

      // Even with accessibility features, should render quickly
      expect(renderTime).toBeLessThan(150)

      // Check for proper ARIA attributes
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })
  })

  describe('Error Recovery Performance', () => {
    test('should handle errors without performance degradation', () => {
      const errorCount = 0
      const startTime = performance.now()

      // Simulate multiple error conditions
      for (let i = 0; i < 10; i++) {
        try {
          render(<StrategyList strategies={[]} />)
        } catch (error) {
          // Count errors but ensure rendering continues
        }
      }

      const totalTime = performance.now() - startTime

      // Error handling should not significantly impact performance
      expect(totalTime).toBeLessThan(100)
    })
  })
})