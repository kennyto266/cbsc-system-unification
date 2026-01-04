/**
 * Economic Data API Service
 * 經濟數據 API 服務
 *
 * 提供經濟數據的獲取、緩存和錯誤處理功能
 */

import { apiClient } from './apiClient'

// TypeScript type definitions
export interface HiborData {
  date: string
  rate: number
}

export interface GdpData {
  quarter: string
  gdp_growth: number
}

export interface PmiData {
  month: string
  pmi: number
}

export interface VisitorData {
  month: string
  visitors: number
}

export interface UnemploymentData {
  month: string
  rate: number
}

export interface EconomicDataParams {
  startDate?: string
  endDate?: string
  startQuarter?: string
  endQuarter?: string
  startMonth?: string
  endMonth?: string
  type?: string
}

export interface DateRange {
  start: string
  end: string
}

export interface GetAllIndicatorsParams {
  dateRange: DateRange
  indicators?: string[]
}

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const CACHE_PREFIX = 'economic_cache_'

/**
 * Economic Data API Service Class
 */
class EconomicDataApiService {
  /**
   * Generate cache key with parameters
   */
  private generateCacheKey(indicator: string, params: EconomicDataParams): string {
    const paramString = Object.entries(params)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}_${value}`)
      .join('_')
    return `${indicator}_${paramString}`
  }

  /**
   * Get cached data from localStorage
   */
  async getCachedData(cacheKey: string): Promise<any> {
    try {
      const cachedItem = localStorage.getItem(`${CACHE_PREFIX}${cacheKey}`)
      if (!cachedItem) return null

      const { data, timestamp } = JSON.parse(cachedItem)
      const isExpired = Date.now() - timestamp > CACHE_DURATION

      if (isExpired) {
        localStorage.removeItem(`${CACHE_PREFIX}${cacheKey}`)
        return null
      }

      return data
    } catch (error) {
      console.error('Error reading from cache:', error)
      return null
    }
  }

  /**
   * Set cached data in localStorage
   */
  private setCachedData(cacheKey: string, data: any): void {
    try {
      const cacheItem = {
        data,
        timestamp: Date.now(),
      }
      localStorage.setItem(`${CACHE_PREFIX}${cacheKey}`, JSON.stringify(cacheItem))
    } catch (error) {
      console.error('Error writing to cache:', error)
    }
  }

  /**
   * Fetch HIBOR data
   */
  async getHiborData(params: EconomicDataParams = {}): Promise<{ success: boolean; data: HiborData[] }> {
    const cacheKey = this.generateCacheKey('hibor', params)

    // Try cache first
    const cachedData = await this.getCachedData(cacheKey)
    if (cachedData) {
      return { success: true, data: cachedData }
    }

    try {
      const response = await apiClient.get('/api/v1/economic/hibor', { params })
      this.setCachedData(cacheKey, response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Error fetching HIBOR data:', error)
      throw error
    }
  }

  /**
   * Fetch GDP data
   */
  async getGdpData(params: EconomicDataParams = {}): Promise<{ success: boolean; data: GdpData[] }> {
    const cacheKey = this.generateCacheKey('gdp', params)

    // Try cache first
    const cachedData = await this.getCachedData(cacheKey)
    if (cachedData) {
      return { success: true, data: cachedData }
    }

    try {
      const response = await apiClient.get('/api/v1/economic/gdp', { params })
      this.setCachedData(cacheKey, response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Error fetching GDP data:', error)
      throw error
    }
  }

  /**
   * Fetch PMI data
   */
  async getPmiData(params: EconomicDataParams = {}): Promise<{ success: boolean; data: PmiData[] }> {
    const cacheKey = this.generateCacheKey('pmi', params)

    // Try cache first
    const cachedData = await this.getCachedData(cacheKey)
    if (cachedData) {
      return { success: true, data: cachedData }
    }

    try {
      const response = await apiClient.get('/api/v1/economic/pmi', { params })
      this.setCachedData(cacheKey, response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Error fetching PMI data:', error)
      throw error
    }
  }

  /**
   * Fetch visitor arrival data
   */
  async getVisitorData(params: EconomicDataParams = {}): Promise<{ success: boolean; data: VisitorData[] }> {
    const cacheKey = this.generateCacheKey('visitors', params)

    // Try cache first
    const cachedData = await this.getCachedData(cacheKey)
    if (cachedData) {
      return { success: true, data: cachedData }
    }

    try {
      const response = await apiClient.get('/api/v1/economic/visitors', { params })
      this.setCachedData(cacheKey, response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Error fetching visitor data:', error)
      throw error
    }
  }

  /**
   * Fetch unemployment data
   */
  async getUnemploymentData(params: EconomicDataParams = {}): Promise<{ success: boolean; data: UnemploymentData[] }> {
    const cacheKey = this.generateCacheKey('unemployment', params)

    // Try cache first
    const cachedData = await this.getCachedData(cacheKey)
    if (cachedData) {
      return { success: true, data: cachedData }
    }

    try {
      const response = await apiClient.get('/api/v1/economic/unemployment', { params })
      this.setCachedData(cacheKey, response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Error fetching unemployment data:', error)
      throw error
    }
  }

  /**
   * Fetch all economic indicators in parallel
   */
  async getAllEconomicIndicators(params: GetAllIndicatorsParams): Promise<{
    hibor: HiborData[]
    gdp: GdpData[]
    pmi: PmiData[]
    visitors: VisitorData[]
    unemployment: UnemploymentData[]
  }> {
    const { dateRange, indicators = ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'] } = params

    const requests: Promise<any>[] = []
    const indicatorMap = {
      hibor: () => this.getHiborData({ startDate: dateRange.start, endDate: dateRange.end }),
      gdp: () => this.getGdpData({ startQuarter: dateRange.start.replace(/-\d{2}$/, '-Q1'), endQuarter: dateRange.end.replace(/-\d{2}$/, '-Q4') }),
      pmi: () => this.getPmiData({ startMonth: dateRange.start, endMonth: dateRange.end, type: 'manufacturing' }),
      visitors: () => this.getVisitorData({ startMonth: dateRange.start, endMonth: dateRange.end }),
      unemployment: () => this.getUnemploymentData({ startMonth: dateRange.start, endMonth: dateRange.end }),
    }

    // Create requests for requested indicators
    indicators.forEach(indicator => {
      if (indicatorMap[indicator as keyof typeof indicatorMap]) {
        requests.push(indicatorMap[indicator as keyof typeof indicatorMap]())
      }
    })

    try {
      const results = await Promise.allSettled(requests)
      const data: any = {}

      results.forEach((result, index) => {
        const indicator = indicators[index]
        if (result.status === 'fulfilled') {
          data[indicator] = result.value.data
        } else {
          console.error(`Error fetching ${indicator} data:`, result.reason)
          data[indicator] = [] // Return empty array on error
        }
      })

      return data
    } catch (error) {
      console.error('Error fetching economic indicators:', error)
      throw error
    }
  }

  /**
   * Clear all economic data cache
   */
  clearCache(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Error clearing cache:', error)
    }
  }

  /**
   * Get cache status
   */
  getCacheStatus(): { [key: string]: { size: number; timestamp: number } } {
    const status: { [key: string]: { size: number; timestamp: number } } = {}

    try {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
          const cachedItem = localStorage.getItem(key)
          if (cachedItem) {
            const { data, timestamp } = JSON.parse(cachedItem)
            const cleanKey = key.replace(CACHE_PREFIX, '')
            status[cleanKey] = {
              size: JSON.stringify(data).length,
              timestamp,
            }
          }
        }
      })
    } catch (error) {
      console.error('Error getting cache status:', error)
    }

    return status
  }
}

// Export singleton instance
export const economicDataApi = new EconomicDataApiService()

// Export types
export type {
  HiborData,
  GdpData,
  PmiData,
  VisitorData,
  UnemploymentData,
  EconomicDataParams,
  GetAllIndicatorsParams,
  DateRange,
}