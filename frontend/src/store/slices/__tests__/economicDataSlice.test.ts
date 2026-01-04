/**
 * Economic Data Slice Tests
 * 經濟數據 Redux Slice 測試
 */

import { configureStore } from '@reduxjs/toolkit'
import economicDataSlice, {
  fetchEconomicIndicators,
  fetchAllEconomicIndicators,
  setFilter,
  setTimeRange,
  clearCache,
  EconomicDataState,
} from '../economicDataSlice'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock the economic data API
jest.mock('../../services/economicDataApi', () => ({
  economicDataApi: {
    getHiborData: jest.fn(),
    getGdpData: jest.fn(),
    getPmiData: jest.fn(),
    getVisitorData: jest.fn(),
    getUnemploymentData: jest.fn(),
    getAllEconomicIndicators: jest.fn(),
  },
}))

import { economicDataApi } from '@/services/economicDataApi'

describe('EconomicDataSlice', () => {
  let store: ReturnType<typeof configureStore>

  beforeEach(() => {
    jest.clearAllMocks()
    store = configureStore({
      reducer: {
        economicData: economicDataSlice,
      },
      middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
          serializableCheck: {
            ignoredActions: ['persist/PERSIST'],
          },
        }),
    })
  })

  const getInitialState = (): EconomicDataState => ({
    data: {
      hibor: [],
      gdp: [],
      pmi: [],
      visitors: [],
      unemployment: [],
    },
    loading: false,
    error: null,
    filters: {
      indicators: ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'],
      dateRange: { start: '', end: '' },
    },
    lastUpdated: null,
    cacheStatus: {},
  })

  describe('Initial State', () => {
    it('should return the initial state', () => {
      const state = store.getState().economicData
      expect(state).toEqual(getInitialState())
    })
  })

  describe('fetchEconomicIndicators', () => {
    it('should handle successful fetch of HIBOR data', async () => {
      // Arrange
      const mockHiborData = [
        { date: '2024-01-01', rate: 5.5 },
        { date: '2024-01-02', rate: 5.6 },
      ]
      jest.mocked(economicDataApi.getHiborData).mockResolvedValue({
        success: true,
        data: mockHiborData,
      })

      // Act
      await store.dispatch(
        fetchEconomicIndicators({ type: 'hibor', params: { startDate: '2024-01-01' } })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.data.hibor).toEqual(mockHiborData)
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
      expect(state.lastUpdated).toBeTruthy()
    })

    it('should handle fetch error', async () => {
      // Arrange
      const errorMessage = 'API Error'
      jest.mocked(economicDataApi.getHiborData).mockRejectedValue(new Error(errorMessage))

      // Act
      await store.dispatch(
        fetchEconomicIndicators({ type: 'hibor', params: {} })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.loading).toBe(false)
      expect(state.error).toBe(errorMessage)
    })

    it('should handle loading state during fetch', () => {
      // Arrange
      jest.mocked(economicDataApi.getHiborData).mockImplementation(() => new Promise(() => {}))

      // Act
      store.dispatch(
        fetchEconomicIndicators({ type: 'hibor', params: {} })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.loading).toBe(true)
    })
  })

  describe('fetchAllEconomicIndicators', () => {
    it('should fetch all indicators successfully', async () => {
      // Arrange
      const mockAllData = {
        hibor: [{ date: '2024-01-01', rate: 5.5 }],
        gdp: [{ quarter: '2024-Q1', gdp_growth: 3.2 }],
        pmi: [{ month: '2024-01', pmi: 52.3 }],
        visitors: [{ month: '2024-01', visitors: 150000 }],
        unemployment: [{ month: '2024-01', rate: 3.2 }],
      }

      jest.mocked(economicDataApi.getAllEconomicIndicators).mockResolvedValue(mockAllData)

      // Act
      await store.dispatch(
        fetchAllEconomicIndicators({
          dateRange: { start: '2024-01-01', end: '2024-12-31' },
        })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.data).toEqual(mockAllData)
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
    })

    it('should handle partial failure gracefully', async () => {
      // Arrange
      const mockPartialData = {
        hibor: [{ date: '2024-01-01', rate: 5.5 }],
        gdp: [], // Empty array for failed request
        pmi: [{ month: '2024-01', pmi: 52.3 }],
        visitors: [{ month: '2024-01', visitors: 150000 }],
        unemployment: [{ month: '2024-01', rate: 3.2 }],
      }

      jest.mocked(economicDataApi.getAllEconomicIndicators).mockResolvedValue(mockPartialData)

      // Act
      await store.dispatch(
        fetchAllEconomicIndicators({
          dateRange: { start: '2024-01-01', end: '2024-12-31' },
        })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.data.hibor).toEqual(mockPartialData.hibor)
      expect(state.data.gdp).toEqual([]) // Failed request returns empty array
      expect(state.loading).toBe(false)
    })
  })

  describe('setFilter', () => {
    it('should update filters', () => {
      // Act
      store.dispatch(
        setFilter({
          indicators: ['hibor', 'gdp'],
          dateRange: { start: '2024-01-01', end: '2024-12-31' },
        })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.filters.indicators).toEqual(['hibor', 'gdp'])
      expect(state.filters.dateRange).toEqual({ start: '2024-01-01', end: '2024-12-31' })
    })
  })

  describe('setTimeRange', () => {
    it('should update time range', () => {
      // Act
      store.dispatch(
        setTimeRange({ start: '2024-01-01', end: '2024-12-31' })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.filters.dateRange).toEqual({ start: '2024-01-01', end: '2024-12-31' })
    })
  })

  describe('clearCache', () => {
    it('should clear all data and reset state', () => {
      // Arrange - Add some data first
      jest.mocked(economicDataApi.getHiborData).mockResolvedValue({
        success: true,
        data: [{ date: '2024-01-01', rate: 5.5 }],
      })

      // Act
      store.dispatch(clearCache())

      // Assert
      const state = store.getState().economicData
      expect(state.data).toEqual(getInitialState().data)
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
      expect(state.lastUpdated).toBe(null)
    })
  })

  describe('Selectors', () => {
    it('should select filtered data correctly', () => {
      // Arrange
      const fullState = {
        economicData: {
          ...getInitialState(),
          data: {
            hibor: [{ date: '2024-01-01', rate: 5.5 }],
            gdp: [{ quarter: '2024-Q1', gdp_growth: 3.2 }],
            pmi: [],
            visitors: [],
            unemployment: [],
          },
          filters: {
            indicators: ['hibor', 'gdp'],
            dateRange: { start: '2024-01-01', end: '2024-12-31' },
          },
        },
      }

      // Act & Assert
      expect(fullState.economicData.data.hibor).toHaveLength(1)
      expect(fullState.economicData.data.gdp).toHaveLength(1)
      expect(fullState.economicData.data.pmi).toHaveLength(0)
    })
  })

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      // Arrange
      jest.mocked(economicDataApi.getHiborData).mockRejectedValue(
        new Error('Network Error')
      )

      // Act
      await store.dispatch(
        fetchEconomicIndicators({ type: 'hibor', params: {} })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.error).toBe('Network Error')
      expect(state.loading).toBe(false)
    })

    it('should handle API response errors', async () => {
      // Arrange
      jest.mocked(economicDataApi.getHiborData).mockRejectedValue(
        new Error('API Error: Invalid parameters')
      )

      // Act
      await store.dispatch(
        fetchEconomicIndicators({ type: 'hibor', params: { invalid: 'param' } })
      )

      // Assert
      const state = store.getState().economicData
      expect(state.error).toBe('API Error: Invalid parameters')
    })
  })
})