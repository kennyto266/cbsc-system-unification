/**
 * Economic Data API Service Tests
 * 經濟數據 API 服務測試
 */

import { economicDataApi } from '../economicDataApi'
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

describe('EconomicDataApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getEconomicIndicators', () => {
    it('should fetch HIBOR data successfully', async () => {
      // Arrange
      const mockHiborData = {
        success: true,
        data: [
          { date: '2024-01-01', rate: 5.5 },
          { date: '2024-01-02', rate: 5.6 },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockHiborData)

      // Act
      const result = await economicDataApi.getHiborData({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      })

      // Assert
      expect(api.get).toHaveBeenCalledWith('/economic/hibor', {
        params: { startDate: '2024-01-01', endDate: '2024-01-31' },
      })
      expect(result).toEqual(mockHiborData)
    })

    it('should fetch GDP data successfully', async () => {
      // Arrange
      const mockGdpData = {
        success: true,
        data: [
          { quarter: '2024-Q1', gdp_growth: 3.2 },
          { quarter: '2024-Q2', gdp_growth: 3.5 },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockGdpData)

      // Act
      const result = await economicDataApi.getGdpData({
        startQuarter: '2024-Q1',
        endQuarter: '2024-Q4',
      })

      // Assert
      expect(api.get).toHaveBeenCalledWith('/economic/gdp', {
        params: { startQuarter: '2024-Q1', endQuarter: '2024-Q4' },
      })
      expect(result).toEqual(mockGdpData)
    })

    it('should fetch PMI data successfully', async () => {
      // Arrange
      const mockPmiData = {
        success: true,
        data: [
          { month: '2024-01', pmi: 52.3 },
          { month: '2024-02', pmi: 51.8 },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockPmiData)

      // Act
      const result = await economicDataApi.getPmiData({
        startMonth: '2024-01',
        endMonth: '2024-06',
        type: 'manufacturing',
      })

      // Assert
      expect(api.get).toHaveBeenCalledWith('/economic/pmi', {
        params: { startMonth: '2024-01', endMonth: '2024-06', type: 'manufacturing' },
      })
      expect(result).toEqual(mockPmiData)
    })

    it('should fetch visitor arrival data successfully', async () => {
      // Arrange
      const mockVisitorData = {
        success: true,
        data: [
          { month: '2024-01', visitors: 150000 },
          { month: '2024-02', visitors: 160000 },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockVisitorData)

      // Act
      const result = await economicDataApi.getVisitorData({
        startMonth: '2024-01',
        endMonth: '2024-12',
      })

      // Assert
      expect(api.get).toHaveBeenCalledWith('/economic/visitors', {
        params: { startMonth: '2024-01', endMonth: '2024-12' },
      })
      expect(result).toEqual(mockVisitorData)
    })

    it('should fetch unemployment data successfully', async () => {
      // Arrange
      const mockUnemploymentData = {
        success: true,
        data: [
          { month: '2024-01', rate: 3.2 },
          { month: '2024-02', rate: 3.1 },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockUnemploymentData)

      // Act
      const result = await economicDataApi.getUnemploymentData({
        startMonth: '2024-01',
        endMonth: '2024-12',
      })

      // Assert
      expect(api.get).toHaveBeenCalledWith('/economic/unemployment', {
        params: { startMonth: '2024-01', endMonth: '2024-12' },
      })
      expect(result).toEqual(mockUnemploymentData)
    })

    it('should handle API errors gracefully', async () => {
      // Arrange
      const error = new Error('Network Error')
      vi.mocked(api.get).mockRejectedValue(error)

      // Act & Assert
      await expect(
        economicDataApi.getHiborData({
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        })
      ).rejects.toThrow('Network Error')
    })
  })

  describe('getAllEconomicIndicators', () => {
    it('should fetch all economic indicators in parallel', async () => {
      // Arrange
      const mockData = {
        hibor: [{ date: '2024-01-01', rate: 5.5 }],
        gdp: [{ quarter: '2024-Q1', gdp_growth: 3.2 }],
        pmi: [{ month: '2024-01', pmi: 52.3 }],
        visitors: [{ month: '2024-01', visitors: 150000 }],
        unemployment: [{ month: '2024-01', rate: 3.2 }],
      }

      vi.mocked(api.get)
        .mockResolvedValueOnce({ success: true, data: mockData.hibor })
        .mockResolvedValueOnce({ success: true, data: mockData.gdp })
        .mockResolvedValueOnce({ success: true, data: mockData.pmi })
        .mockResolvedValueOnce({ success: true, data: mockData.visitors })
        .mockResolvedValueOnce({ success: true, data: mockData.unemployment })

      // Act
      const result = await economicDataApi.getAllEconomicIndicators({
        dateRange: { start: '2024-01-01', end: '2024-12-31' },
      })

      // Assert
      expect(result).toEqual({
        hibor: mockData.hibor,
        gdp: mockData.gdp,
        pmi: mockData.pmi,
        visitors: mockData.visitors,
        unemployment: mockData.unemployment,
      })
      expect(api.get).toHaveBeenCalledTimes(5)
    })

    it('should handle partial failures in parallel requests', async () => {
      // Arrange
      vi.mocked(api.get)
        .mockResolvedValueOnce({ success: true, data: [{ date: '2024-01-01', rate: 5.5 }] })
        .mockRejectedValueOnce(new Error('GDP API Error'))
        .mockResolvedValueOnce({ success: true, data: [{ month: '2024-01', pmi: 52.3 }] })
        .mockResolvedValueOnce({ success: true, data: [{ month: '2024-01', visitors: 150000 }] })
        .mockResolvedValueOnce({ success: true, data: [{ month: '2024-01', rate: 3.2 }] })

      // Act
      const result = await economicDataApi.getAllEconomicIndicators({
        dateRange: { start: '2024-01-01', end: '2024-12-31' },
      })

      // Assert
      expect(result.hibor).toEqual([{ date: '2024-01-01', rate: 5.5 }])
      expect(result.gdp).toEqual([])
      expect(result.pmi).toEqual([{ month: '2024-01', pmi: 52.3 }])
      expect(result.visitors).toEqual([{ month: '2024-01', visitors: 150000 }])
      expect(result.unemployment).toEqual([{ month: '2024-01', rate: 3.2 }])
    })
  })

  describe('getCachedData', () => {
    it('should return cached data when available', async () => {
      // Arrange
      const cacheKey = 'hibor_2024-01-01_2024-01-31'
      const cachedData = [{ date: '2024-01-01', rate: 5.5 }]

      // Mock localStorage
      const localStorageGet = vi.spyOn(Storage.prototype, 'getItem')
      localStorageGet.mockReturnValue(JSON.stringify(cachedData))

      // Act
      const result = await economicDataApi.getCachedData(cacheKey)

      // Assert
      expect(result).toEqual(cachedData)
      expect(localStorageGet).toHaveBeenCalledWith(`economic_cache_${cacheKey}`)
    })

    it('should return null when no cached data exists', async () => {
      // Arrange
      const cacheKey = 'non_existent_key'
      const localStorageGet = vi.spyOn(Storage.prototype, 'getItem')
      localStorageGet.mockReturnValue(null)

      // Act
      const result = await economicDataApi.getCachedData(cacheKey)

      // Assert
      expect(result).toBeNull()
    })
  })
})