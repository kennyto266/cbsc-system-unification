/**
 * Test Setup Configuration
 * 測試設置配置
 */

import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock matchMedia with full event listener support
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => {
    const listeners: Array<(event: MediaQueryListEvent) => void> = []

    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn((event: string, listener: any) => {
        if (event === 'change') {
          listeners.push(listener)
        }
      }),
      removeEventListener: jest.fn((event: string, listener: any) => {
        const index = listeners.indexOf(listener)
        if (index > -1) {
          listeners.splice(index, 1)
        }
      }),
      dispatchEvent: jest.fn(),
      // Helper method for testing
      _simulateChange: (matches: boolean) => {
        listeners.forEach(listener => {
          listener({ matches } as MediaQueryListEvent)
        })
      },
    }
  }),
})

// Mock scrollTo
window.scrollTo = jest.fn()

// Mock crypto.getRandomValues
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: jest.fn(() => Array.from({length: 16}, () => Math.floor(Math.random() * 256)))
  }
})

// Suppress console warnings during tests
const originalWarn = console.warn
beforeAll(() => {
  console.warn = jest.fn()
})

afterAll(() => {
  console.warn = originalWarn
})

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks()
})