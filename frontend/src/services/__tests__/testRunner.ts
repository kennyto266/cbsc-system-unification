/**
 * Simple Test Runner for Economic API Services
 * 經濟 API 服務的簡單測試運行器
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Import services to test
import { economicDataApi } from '../economicDataApi'
import { economicStrategyApi } from '../economicStrategyApi'
import { economicWebSocket } from '../economicWebSocket'

// Mock API for testing
const mockApi = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  onopen: any = null
  onclose: any = null
  onmessage: any = null
  onerror: any = null

  constructor(url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) this.onopen({ type: 'open' })
    }, 100)
  }

  send() {}
  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) this.onclose({ type: 'close' })
  }
}

// Setup mocks
vi.mock('../api', () => ({ api: mockApi }))
vi.stubGlobal('WebSocket', MockWebSocket)

describe('Economic API Services Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    economicWebSocket.disconnect()
  })

  it('should create economic data API instance', () => {
    expect(economicDataApi).toBeDefined()
    expect(typeof economicDataApi.getHiborData).toBe('function')
    expect(typeof economicDataApi.getAllEconomicIndicators).toBe('function')
    expect(typeof economicDataApi.getCachedData).toBe('function')
  })

  it('should create economic strategy API instance', () => {
    expect(economicStrategyApi).toBeDefined()
    expect(typeof economicStrategyApi.getEconomicStrategies).toBe('function')
    expect(typeof economicStrategyApi.createEconomicStrategy).toBe('function')
    expect(typeof economicStrategyApi.startEconomicStrategy).toBe('function')
  })

  it('should create economic WebSocket instance', () => {
    expect(economicWebSocket).toBeDefined()
    expect(typeof economicWebSocket.connect).toBe('function')
    expect(typeof economicWebSocket.subscribe).toBe('function')
    expect(typeof economicWebSocket.getConnectionStatus).toBe('function')
  })

  it('should handle WebSocket connection', async () => {
    const status = economicWebSocket.getConnectionStatus()
    expect(status).toBe('disconnected')

    await economicWebSocket.connect()
    expect(economicWebSocket.getConnectionStatus()).toBe('connecting')
  })

  it('should handle API method calls', () => {
    // Mock successful API response
    mockApi.get.mockResolvedValue({
      success: true,
      data: [{ date: '2024-01-01', rate: 5.5 }]
    })

    expect(economicDataApi.getHiborData()).resolves.toEqual({
      success: true,
      data: [{ date: '2024-01-01', rate: 5.5 }]
    })

    expect(mockApi.get).toHaveBeenCalledWith('/economic/hibor', { params: {} })
  })

  it('should handle strategy API calls', () => {
    const mockStrategy = {
      id: '1',
      name: 'Test Strategy',
      type: 'hibor',
      status: 'active'
    }

    mockApi.get.mockResolvedValue({
      success: true,
      data: [mockStrategy]
    })

    expect(economicStrategyApi.getEconomicStrategies()).resolves.toEqual({
      success: true,
      data: [mockStrategy]
    })

    expect(mockApi.get).toHaveBeenCalledWith('/strategies/economic', {})
  })
})

console.log('✅ Economic API Services Test Runner loaded successfully!')