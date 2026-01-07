/**
 * Economic Data API Service Tests
 * 經濟數據 API 服務測試
 */

import { economicDataApi } from '../economicDataApi'
import { apiClient } from '../apiClient'
import axios from 'axios'

// Mock axios and apiClient
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}))

// Mock the apiClient module
jest.mock('../apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  get keys() { return [] },
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock console.error to avoid test output pollution
jest.spyOn(console, 'error').mockImplementation(() => {})

describe('EconomicDataApi', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset localStorage mock to return null by default
    localStorageMock.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('getEconomicIndicators', () => {
    it('should fetch HIBOR data successfully', async () => {
      // Arrange
      const mockHiborData = [
        { date: '2024-01-01', rate: 5.5 },
        { date: '2024-01-02', rate: 5.6 },
      ]
      // Mock localStorage.getItem to return null (no cache)
      localStorageMock.getItem.mockReturnValue(null)
      // Mock apiClient.get to return the data
      jest.mocked(apiClient.get).mockResolvedValue({ data: mockHiborData })

      // Act
      const result = await economicDataApi.getHiborData({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      })

      // Assert
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/economic/hibor', {
        params: { startDate: '2024-01-01', endDate: '2024-01-31' },
      })
      expect(result).toEqual({ success: true, data: mockHiborData })
    })

    it('should fetch GDP data successfully', async () => {
      // Arrange
      const mockGdpData = [
        { quarter: '2024-Q1', gdp_growth: 3.2 },
        { quarter: '2024-Q2', gdp_growth: 3.5 },
      ]
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get).mockResolvedValue({ data: mockGdpData })

      // Act
      const result = await economicDataApi.getGdpData({
        startQuarter: '2024-Q1',
        endQuarter: '2024-Q4',
      })

      // Assert
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/economic/gdp', {
        params: { startQuarter: '2024-Q1', endQuarter: '2024-Q4' },
      })
      expect(result).toEqual({ success: true, data: mockGdpData })
    })

    it('should fetch PMI data successfully', async () => {
      // Arrange
      const mockPmiData = [
        { month: '2024-01', pmi: 52.3 },
        { month: '2024-02', pmi: 51.8 },
      ]
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get).mockResolvedValue({ data: mockPmiData })

      // Act
      const result = await economicDataApi.getPmiData({
        startMonth: '2024-01',
        endMonth: '2024-06',
        type: 'manufacturing',
      })

      // Assert
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/economic/pmi', {
        params: { startMonth: '2024-01', endMonth: '2024-06', type: 'manufacturing' },
      })
      expect(result).toEqual({ success: true, data: mockPmiData })
    })

    it('should fetch visitor arrival data successfully', async () => {
      // Arrange
      const mockVisitorData = [
        { month: '2024-01', visitors: 150000 },
        { month: '2024-02', visitors: 160000 },
      ]
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get).mockResolvedValue({ data: mockVisitorData })

      // Act
      const result = await economicDataApi.getVisitorData({
        startMonth: '2024-01',
        endMonth: '2024-12',
      })

      // Assert
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/economic/visitors', {
        params: { startMonth: '2024-01', endMonth: '2024-12' },
      })
      expect(result).toEqual({ success: true, data: mockVisitorData })
    })

    it('should fetch unemployment data successfully', async () => {
      // Arrange
      const mockUnemploymentData = [
        { month: '2024-01', rate: 3.2 },
        { month: '2024-02', rate: 3.1 },
      ]
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get).mockResolvedValue({ data: mockUnemploymentData })

      // Act
      const result = await economicDataApi.getUnemploymentData({
        startMonth: '2024-01',
        endMonth: '2024-12',
      })

      // Assert
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/economic/unemployment', {
        params: { startMonth: '2024-01', endMonth: '2024-12' },
      })
      expect(result).toEqual({ success: true, data: mockUnemploymentData })
    })

    it('should handle API errors gracefully', async () => {
      // Arrange
      const error = new Error('Network Error')
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get).mockRejectedValue(error)

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

      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: mockData.hibor })
        .mockResolvedValueOnce({ data: mockData.gdp })
        .mockResolvedValueOnce({ data: mockData.pmi })
        .mockResolvedValueOnce({ data: mockData.visitors })
        .mockResolvedValueOnce({ data: mockData.unemployment })

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
      expect(apiClient.get).toHaveBeenCalledTimes(5)
    })

    it('should handle partial failures in parallel requests', async () => {
      // Arrange
      localStorageMock.getItem.mockReturnValue(null)
      jest.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: [{ date: '2024-01-01', rate: 5.5 }] })
        .mockRejectedValueOnce(new Error('GDP API Error'))
        .mockResolvedValueOnce({ data: [{ month: '2024-01', pmi: 52.3 }] })
        .mockResolvedValueOnce({ data: [{ month: '2024-01', visitors: 150000 }] })
        .mockResolvedValueOnce({ data: [{ month: '2024-01', rate: 3.2 }] })

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
      const cachedItem = JSON.stringify({
        data: cachedData,
        timestamp: Date.now(),
      })
      localStorageMock.getItem.mockReturnValue(cachedItem)

      // Act
      const result = await economicDataApi.getCachedData(cacheKey)

      // Assert
      expect(result).toEqual(cachedData)
      expect(localStorageMock.getItem).toHaveBeenCalledWith(`economic_cache_${cacheKey}`)
    })

    it('should return null when no cached data exists', async () => {
      // Arrange
      const cacheKey = 'non_existent_key'
      localStorageMock.getItem.mockReturnValue(null)

      // Act
      const result = await economicDataApi.getCachedData(cacheKey)

      // Assert
      expect(result).toBeNull()
    })
  })
})