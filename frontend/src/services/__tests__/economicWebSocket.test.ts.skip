/**
 * Economic WebSocket Service Tests
 * 經濟數據 WebSocket 服務測試
 */

import { economicWebSocket } from '../economicWebSocket'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState: number = MockWebSocket.CONNECTING
  onopen: ((event: any) => void) | null = null
  onclose: ((event: any) => void) | null = null
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null

  constructor(url: string) {
    this.url = url

    // Simulate connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen({ type: 'open' })
      }
    }, 100)
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose({ type: 'close' })
    }
  }

  addEventListener(type: string, listener: (event: any) => void) {
    switch (type) {
      case 'open':
        this.onopen = listener
        break
      case 'close':
        this.onclose = listener
        break
      case 'message':
        this.onmessage = listener
        break
      case 'error':
        this.onerror = listener
        break
    }
  }

  removeEventListener(type: string, listener: (event: any) => void) {
    switch (type) {
      case 'open':
        this.onopen = null
        break
      case 'close':
        this.onclose = null
        break
      case 'message':
        this.onmessage = null
        break
      case 'error':
        this.onerror = null
        break
    }
  }
}

// Mock global WebSocket
jest.stubGlobal('WebSocket', MockWebSocket)

describe('EconomicWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    economicWebSocket.disconnect()
  })

  afterEach(() => {
    jest.restoreAllMocks()
    economicWebSocket.disconnect()
  })

  describe('connect', () => {
    it('should establish WebSocket connection', async () => {
      // Act
      const connectionPromise = economicWebSocket.connect()

      // Assert
      expect(connectionPromise).toBeInstanceOf(Promise)

      const connection = await connectionPromise
      expect(connection).toBeDefined()
    })

    it('should not reconnect if already connected', async () => {
      // Arrange
      await economicWebSocket.connect()
      const connectSpy = jest.spyOn(economicWebSocket as any, 'createConnection')

      // Act
      await economicWebSocket.connect()

      // Assert
      expect(connectSpy).not.toHaveBeenCalled()
    })

    it('should handle connection errors', async () => {
      // Arrange
      const originalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          setTimeout(() => {
            this.readyState = MockWebSocket.CLOSED
            if (this.onerror) {
              this.onerror({ type: 'error', message: 'Connection failed' })
            }
          }, 100)
        }
      } as any

      // Act & Assert
      await expect(economicWebSocket.connect()).rejects.toThrow()

      // Restore
      global.WebSocket = originalWebSocket
    })
  })

  describe('subscribe', () => {
    it('should subscribe to economic data updates', async () => {
      // Arrange
      await economicWebSocket.connect()
      const callback = jest.fn()

      // Act
      economicWebSocket.subscribe('hibor', callback)

      // Simulate incoming message
      const mockData = {
        type: 'hibor_update',
        data: { date: '2024-01-01', rate: 5.5 },
      }

      if (economicWebSocket['ws']?.onmessage) {
        economicWebSocket['ws'].onmessage({
          type: 'message',
          data: JSON.stringify(mockData),
        })
      }

      // Assert
      expect(callback).toHaveBeenCalledWith(mockData.data)
    })

    it('should subscribe to multiple indicators', async () => {
      // Arrange
      await economicWebSocket.connect()
      const hiborCallback = jest.fn()
      const gdpCallback = jest.fn()

      // Act
      economicWebSocket.subscribe('hibor', hiborCallback)
      economicWebSocket.subscribe('gdp', gdpCallback)

      // Simulate HIBOR update
      const hiborData = {
        type: 'hibor_update',
        data: { date: '2024-01-01', rate: 5.5 },
      }

      if (economicWebSocket['ws']?.onmessage) {
        economicWebSocket['ws'].onmessage({
          type: 'message',
          data: JSON.stringify(hiborData),
        })
      }

      // Assert
      expect(hiborCallback).toHaveBeenCalledWith(hiborData.data)
      expect(gdpCallback).not.toHaveBeenCalled()
    })

    it('should handle subscription errors gracefully', () => {
      // Arrange
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      // Act
      economicWebSocket.subscribe('invalid_indicator', jest.fn())

      // Assert
      expect(consoleSpy).toHaveBeenCalledWith(
        'Invalid subscription type: invalid_indicator'
      )

      consoleSpy.mockRestore()
    })
  })

  describe('unsubscribe', () => {
    it('should unsubscribe from economic data updates', async () => {
      // Arrange
      await economicWebSocket.connect()
      const callback = jest.fn()
      economicWebSocket.subscribe('hibor', callback)

      // Act
      economicWebSocket.unsubscribe('hibor', callback)

      // Simulate incoming message
      const mockData = {
        type: 'hibor_update',
        data: { date: '2024-01-01', rate: 5.5 },
      }

      if (economicWebSocket['ws']?.onmessage) {
        economicWebSocket['ws'].onmessage({
          type: 'message',
          data: JSON.stringify(mockData),
        })
      }

      // Assert
      expect(callback).not.toHaveBeenCalled()
    })

    it('should remove specific callback but keep others', async () => {
      // Arrange
      await economicWebSocket.connect()
      const callback1 = jest.fn()
      const callback2 = jest.fn()
      economicWebSocket.subscribe('hibor', callback1)
      economicWebSocket.subscribe('hibor', callback2)

      // Act
      economicWebSocket.unsubscribe('hibor', callback1)

      // Simulate incoming message
      const mockData = {
        type: 'hibor_update',
        data: { date: '2024-01-01', rate: 5.5 },
      }

      if (economicWebSocket['ws']?.onmessage) {
        economicWebSocket['ws'].onmessage({
          type: 'message',
          data: JSON.stringify(mockData),
        })
      }

      // Assert
      expect(callback1).not.toHaveBeenCalled()
      expect(callback2).toHaveBeenCalledWith(mockData.data)
    })
  })

  describe('getConnectionStatus', () => {
    it('should return correct connection status', () => {
      // Initially disconnected
      expect(economicWebSocket.getConnectionStatus()).toBe('disconnected')

      // After connecting (simulated)
      economicWebSocket.connect()
      expect(economicWebSocket.getConnectionStatus()).toBe('connecting')
    })
  })

  describe('disconnect', () => {
    it('should close WebSocket connection', async () => {
      // Arrange
      await economicWebSocket.connect()
      const ws = economicWebSocket['ws']
      const closeSpy = jest.spyOn(ws!, 'close')

      // Act
      economicWebSocket.disconnect()

      // Assert
      expect(closeSpy).toHaveBeenCalled()
      expect(economicWebSocket.getConnectionStatus()).toBe('disconnected')
    })

    it('should handle disconnect when not connected', () => {
      // Act & Assert - should not throw
      expect(() => economicWebSocket.disconnect()).not.toThrow()
    })
  })

  describe('reconnect', () => {
    it('should attempt to reconnect with backoff', async () => {
      // Arrange
      const setTimeoutSpy = jest.spyOn(global, 'setTimeout')
      await economicWebSocket.connect()
      economicWebSocket.disconnect()

      // Act
      economicWebSocket.reconnect()

      // Assert
      expect(setTimeoutSpy).toHaveBeenCalledWith(
        expect.any(Function),
        expect.any(Number) // Backoff delay
      )

      setTimeoutSpy.mockRestore()
    })
  })
})