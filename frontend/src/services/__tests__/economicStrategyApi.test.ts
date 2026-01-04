/**
 * Economic Strategy API Service Tests
 * 經濟策略 API 服務測試
 */

import { economicStrategyApi } from '../economicStrategyApi'
import { api } from '../api'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// Mock the base API service
vi.mock('../api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// Mock console.error to avoid test output pollution
vi.spyOn(console, 'error').mockImplementation(() => {})

describe('EconomicStrategyApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getEconomicStrategies', () => {
    it('should fetch all economic strategies successfully', async () => {
      // Arrange
      const mockStrategies = {
        success: true,
        data: [
          {
            id: '1',
            name: 'HIBOR策略',
            type: 'hibor',
            status: 'active',
            config: { lookback_period: 30, threshold_high: 5.0 },
          },
          {
            id: '2',
            name: 'GDP策略',
            type: 'gdp',
            status: 'inactive',
            config: { growth_threshold: 3.0 },
          },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockStrategies)

      // Act
      const result = await economicStrategyApi.getEconomicStrategies()

      // Assert
      expect(api.get).toHaveBeenCalledWith('/strategies/economic')
      expect(result).toEqual(mockStrategies)
    })

    it('should handle API errors gracefully', async () => {
      // Arrange
      const error = new Error('Network Error')
      vi.mocked(api.get).mockRejectedValue(error)

      // Act & Assert
      await expect(economicStrategyApi.getEconomicStrategies()).rejects.toThrow('Network Error')
    })
  })

  describe('createEconomicStrategy', () => {
    it('should create a new economic strategy successfully', async () => {
      // Arrange
      const strategyData = {
        name: '新HIBOR策略',
        type: 'hibor',
        config: { lookback_period: 20, threshold_high: 4.5 },
      }
      const mockResponse = {
        success: true,
        data: { id: '3', ...strategyData, status: 'created' },
      }
      vi.mocked(api.post).mockResolvedValue(mockResponse)

      // Act
      const result = await economicStrategyApi.createEconomicStrategy(strategyData)

      // Assert
      expect(api.post).toHaveBeenCalledWith('/strategies/economic', strategyData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateEconomicStrategy', () => {
    it('should update an economic strategy successfully', async () => {
      // Arrange
      const strategyId = '1'
      const updateData = {
        name: '更新的HIBOR策略',
        config: { lookback_period: 25 },
      }
      const mockResponse = {
        success: true,
        data: { id: strategyId, ...updateData, updated_at: '2024-01-01' },
      }
      vi.mocked(api.put).mockResolvedValue(mockResponse)

      // Act
      const result = await economicStrategyApi.updateEconomicStrategy(strategyId, updateData)

      // Assert
      expect(api.put).toHaveBeenCalledWith(`/strategies/economic/${strategyId}`, updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteEconomicStrategy', () => {
    it('should delete an economic strategy successfully', async () => {
      // Arrange
      const strategyId = '1'
      const mockResponse = { success: true, message: 'Strategy deleted successfully' }
      vi.mocked(api.delete).mockResolvedValue(mockResponse)

      // Act
      const result = await economicStrategyApi.deleteEconomicStrategy(strategyId)

      // Assert
      expect(api.delete).toHaveBeenCalledWith(`/strategies/economic/${strategyId}`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('startEconomicStrategy', () => {
    it('should start an economic strategy successfully', async () => {
      // Arrange
      const strategyId = '1'
      const startParams = { symbols: ['HSI'], initial_capital: 1000000 }
      const mockResponse = {
        success: true,
        data: { id: strategyId, status: 'running', started_at: '2024-01-01T00:00:00Z' },
      }
      vi.mocked(api.post).mockResolvedValue(mockResponse)

      // Act
      const result = await economicStrategyApi.startEconomicStrategy(strategyId, startParams)

      // Assert
      expect(api.post).toHaveBeenCalledWith(`/strategies/economic/${strategyId}/start`, startParams)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('stopEconomicStrategy', () => {
    it('should stop an economic strategy successfully', async () => {
      // Arrange
      const strategyId = '1'
      const mockResponse = {
        success: true,
        data: { id: strategyId, status: 'stopped', stopped_at: '2024-01-01T00:00:00Z' },
      }
      vi.mocked(api.post).mockResolvedValue(mockResponse)

      // Act
      const result = await economicStrategyApi.stopEconomicStrategy(strategyId)

      // Assert
      expect(api.post).toHaveBeenCalledWith(`/strategies/economic/${strategyId}/stop`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStrategyPerformance', () => {
    it('should fetch strategy performance data successfully', async () => {
      // Arrange
      const strategyId = '1'
      const mockPerformance = {
        success: true,
        data: {
          total_return: 0.15,
          sharpe_ratio: 1.2,
          max_drawdown: -0.05,
          win_rate: 0.65,
          total_trades: 42,
        },
      }
      vi.mocked(api.get).mockResolvedValue(mockPerformance)

      // Act
      const result = await economicStrategyApi.getStrategyPerformance(strategyId)

      // Assert
      expect(api.get).toHaveBeenCalledWith(`/strategies/economic/${strategyId}/performance`)
      expect(result).toEqual(mockPerformance)
    })
  })
})