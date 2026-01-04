/**
 * Economic Data Hook
 * 經濟數據獲取和管理 Hook
 */

import { useEffect, useCallback, useMemo } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '../store'
import {
  fetchEconomicIndicators,
  fetchAllEconomicIndicators,
  setFilter,
  setTimeRange,
  selectEconomicData,
  selectEconomicDataLoading,
  selectEconomicDataError,
  selectEconomicDataFilters,
  selectFilteredEconomicData,
  selectLastUpdated,
  selectHiborData,
  selectGdpData,
  selectPmiData,
  selectVisitorData,
  selectUnemploymentData,
} from '../store/slices/economicDataSlice'
import { economicDataApi } from '../services/economicDataApi'

export interface UseEconomicDataOptions {
  autoFetch?: boolean
  cacheEnabled?: boolean
  refreshInterval?: number
}

export interface UseEconomicDataReturn {
  // Data
  data: ReturnType<typeof selectEconomicData>
  filteredData: ReturnType<typeof selectFilteredEconomicData>
  hiborData: ReturnType<typeof selectHiborData>
  gdpData: ReturnType<typeof selectGdpData>
  pmiData: ReturnType<typeof selectPmiData>
  visitorData: ReturnType<typeof selectVisitorData>
  unemploymentData: ReturnType<typeof selectUnemploymentData>

  // State
  loading: boolean
  error: string | null
  lastUpdated: string | null

  // Actions
  fetchIndicator: (type: string, params?: any) => Promise<void>
  fetchAllIndicators: (dateRange: { start: string; end: string }) => Promise<void>
  setFilter: (filters: { indicators?: string[]; dateRange?: { start: string; end: string } }) => void
  setTimeRange: (range: { start: string; end: string }) => void
  refreshData: () => Promise<void>
  clearCache: () => void
}

export const useEconomicData = (options: UseEconomicDataOptions = {}): UseEconomicDataReturn => {
  const { autoFetch = false, cacheEnabled = true, refreshInterval = 0 } = options

  const dispatch = useDispatch()

  // Selectors
  const data = useSelector(selectEconomicData)
  const filteredData = useSelector(selectFilteredEconomicData)
  const hiborData = useSelector(selectHiborData)
  const gdpData = useSelector(selectGdpData)
  const pmiData = useSelector(selectPmiData)
  const visitorData = useSelector(selectVisitorData)
  const unemploymentData = useSelector(selectUnemploymentData)
  const loading = useSelector(selectEconomicDataLoading)
  const error = useSelector(selectEconomicDataError)
  const lastUpdated = useSelector(selectLastUpdated)
  const filters = useSelector(selectEconomicDataFilters)

  // Actions
  const fetchIndicator = useCallback(async (type: string, params: any = {}) => {
    try {
      await dispatch(fetchEconomicIndicators({ type: type as any, params }))
    } catch (error) {
      console.error(`Error fetching ${type} data:`, error)
    }
  }, [dispatch])

  const fetchAllIndicators = useCallback(
    async (dateRange: { start: string; end: string }) => {
      try {
        await dispatch(fetchAllEconomicIndicators({ dateRange }))
      } catch (error) {
        console.error('Error fetching all indicators:', error)
      }
    },
    [dispatch]
  )

  const updateFilter = useCallback(
    (filterConfig: { indicators?: string[]; dateRange?: { start: string; end: string } }) => {
      dispatch(setFilter(filterConfig))
    },
    [dispatch]
  )

  const updateTimeRange = useCallback((range: { start: string; end: string }) => {
      dispatch(setTimeRange(range))
    }, [dispatch])

  const refreshData = useCallback(async () => {
    if (filters.dateRange.start && filters.dateRange.end) {
      await fetchAllIndicators(filters.dateRange)
    }
  }, [fetchAllIndicators, filters.dateRange])

  const clearCache = useCallback(() => {
    economicDataApi.clearCache()
  }, [])

  // Auto fetch effect
  useEffect(() => {
    if (autoFetch && filters.dateRange.start && filters.dateRange.end) {
      fetchAllIndicators(filters.dateRange)
    }
  }, [autoFetch, filters.dateRange, fetchAllIndicators])

  // Refresh interval effect
  useEffect(() => {
    if (refreshInterval > 0 && autoFetch) {
      const interval = setInterval(refreshData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [refreshInterval, autoFetch, refreshData])

  // Memoized return value
  return useMemo(
    () => ({
      // Data
      data,
      filteredData,
      hiborData,
      gdpData,
      pmiData,
      visitorData,
      unemploymentData,

      // State
      loading,
      error,
      lastUpdated,

      // Actions
      fetchIndicator,
      fetchAllIndicators,
      setFilter: updateFilter,
      setTimeRange: updateTimeRange,
      refreshData,
      clearCache,
    }),
    [
      data,
      filteredData,
      hiborData,
      gdpData,
      pmiData,
      visitorData,
      unemploymentData,
      loading,
      error,
      lastUpdated,
      fetchIndicator,
      fetchAllIndicators,
      updateFilter,
      updateTimeRange,
      refreshData,
      clearCache,
    ]
  )
}