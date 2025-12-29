/**
 * Technical Indicators API Service
 * Handles all technical indicator related API calls
 */

import { apiRequest } from '../client'
import { API_ENDPOINTS } from '../config'
import { ApiResponse, PaginatedResponse, BaseParams } from '../types/common'
import {
  Indicator,
  IndicatorCategory,
  IndicatorPreset,
  IndicatorCalculation,
  IndicatorFormula,
  IndicatorSearchResult,
} from '../types/indicators'

export class IndicatorService {
  /**
   * Get all available indicators
   */
  async getIndicators(params?: BaseParams & {
    category?: string
    type?: string
    search?: string
  }): Promise<PaginatedResponse<Indicator>> {
    return apiRequest.get<PaginatedResponse<Indicator>>(API_ENDPOINTS.INDICATORS.LIST, { params })
  }

  /**
   * Get indicator by ID
   */
  async getIndicator(id: string): Promise<ApiResponse<Indicator>> {
    return apiRequest.get<ApiResponse<Indicator>>(API_ENDPOINTS.INDICATORS.DETAIL(id))
  }

  /**
   * Search indicators
   */
  async searchIndicators(query: string, params?: {
    limit?: number
    category?: string
  }): Promise<ApiResponse<IndicatorSearchResult[]>> {
    return apiRequest.get<ApiResponse<IndicatorSearchResult[]>>(API_ENDPOINTS.INDICATORS.SEARCH, {
      params: { q: query, ...params },
    })
  }

  /**
   * Calculate single indicator
   */
  async calculateIndicator(data: IndicatorCalculation): Promise<ApiResponse<any[]>> {
    return apiRequest.post<ApiResponse<any[]>>(API_ENDPOINTS.INDICATORS.CALCULATE, data)
  }

  /**
   * Calculate multiple indicators (batch)
   */
  async calculateBatchIndicators(data: {
    symbol: string
    interval: string
    indicators: {
      name: string
      parameters: Record<string, any>
    }[]
    startDate?: string
    endDate?: string
    limit?: number
  }): Promise<ApiResponse<Record<string, any[]>>> {
    return apiRequest.post<ApiResponse<Record<string, any[]>>>(
      API_ENDPOINTS.INDICATORS.BATCH_CALCULATE,
      data
    )
  }

  /**
   * Get indicator presets
   */
  async getIndicatorPresets(params?: BaseParams & {
    category?: string
    strategy?: string
  }): Promise<PaginatedResponse<IndicatorPreset>> {
    return apiRequest.get<PaginatedResponse<IndicatorPreset>>(API_ENDPOINTS.INDICATORS.PRESETS, { params })
  }

  /**
   * Get indicator categories
   */
  async getIndicatorCategories(): Promise<ApiResponse<IndicatorCategory[]>> {
    return apiRequest.get<ApiResponse<IndicatorCategory[]>>(API_ENDPOINTS.INDICATORS.CATEGORIES)
  }

  /**
   * Get indicator formulas
   */
  async getIndicatorFormulas(params?: {
    indicator?: string
    category?: string
  }): Promise<ApiResponse<IndicatorFormula[]>> {
    return apiRequest.get<ApiResponse<IndicatorFormula[]>>(API_ENDPOINTS.INDICATORS.FORMULAS, { params })
  }

  /**
   * Get indicator by name
   */
  async getIndicatorByName(name: string): Promise<ApiResponse<Indicator>> {
    return apiRequest.get<ApiResponse<Indicator>>(`/indicators/by-name/${name}`)
  }

  /**
   * Get popular indicators
   */
  async getPopularIndicators(limit?: number): Promise<ApiResponse<Indicator[]>> {
    return apiRequest.get<ApiResponse<Indicator[]>>('/indicators/popular', {
      params: { limit },
    })
  }

  /**
   * Get related indicators
   */
  async getRelatedIndicators(indicatorId: string, limit?: number): Promise<ApiResponse<Indicator[]>> {
    return apiRequest.get<ApiResponse<Indicator[]>>(`/indicators/${indicatorId}/related`, {
      params: { limit },
    })
  }

  /**
   * Validate indicator parameters
   */
  async validateIndicatorParams(
    indicatorName: string,
    parameters: Record<string, any>
  ): Promise<ApiResponse<{
    valid: boolean
    errors?: string[]
    warnings?: string[]
  }>> {
    return apiRequest.post<ApiResponse<any>>(`/indicators/${indicatorName}/validate`, { parameters })
  }

  /**
   * Get indicator usage statistics
   */
  async getIndicatorStats(): Promise<ApiResponse<{
    totalIndicators: number
    categoryCounts: Record<string, number>
    mostUsed: Array<{
      indicator: string
      count: number
    }>
    recentlyAdded: Indicator[]
  }>> {
    return apiRequest.get<ApiResponse<any>>('/indicators/stats')
  }

  // CBSC Specific Indicator Methods

  /**
   * Calculate CBSC warrant indicators
   */
  async calculateCBSCWarrantIndicators(data: {
    warrantCode: string
    indicators: string[]
    parameters?: Record<string, any>
  }): Promise<ApiResponse<Record<string, any>>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/cbsc/warrant', data)
  }

  /**
   * Calculate CBSC bull/bear indicators
   */
  async calculateCBSCBullBearIndicators(data: {
    code: string
    type: 'bull' | 'bear'
    indicators: string[]
    parameters?: Record<string, any>
  }): Promise<ApiResponse<Record<string, any>>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/cbsc/bullbear', data)
  }

  /**
   * Get CBSC specific indicators
   */
  async getCBSCIndicators(): Promise<ApiResponse<Indicator[]>> {
    return apiRequest.get<ApiResponse<Indicator[]>>('/indicators/cbsc')
  }

  /**
   * Calculate implied volatility for CBSC products
   */
  async calculateImpliedVolatility(data: {
    code: string
    price: number
    underlyingPrice: number
    strike: number
    timeToExpiry: number
    riskFreeRate?: number
  }): Promise<ApiResponse<{
    impliedVolatility: number
    delta: number
    gamma: number
    theta: number
    vega: number
  }>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/cbsc/implied-volatility', data)
  }

  /**
   * Calculate greeks for CBSC products
   */
  async calculateGreeks(data: {
    code: string
    price: number
    underlyingPrice: number
    strike: number
    timeToExpiry: number
    volatility?: number
    riskFreeRate?: number
    dividendYield?: number
  }): Promise<ApiResponse<{
    delta: number
    gamma: number
    theta: number
    vega: number
    rho: number
  }>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/cbsc/greeks', data)
  }

  /**
   * Get CBSC market sentiment indicators
   */
  async getCBSCSentimentIndicators(code: string): Promise<ApiResponse<{
    sentiment: 'bullish' | 'bearish' | 'neutral'
    score: number
    factors: {
      putCallRatio: number
      impliedVolatility: number
      volume: number
      openInterest: number
    }
  }>> {
    return apiRequest.get<ApiResponse<any>>(`/indicators/cbsc/sentiment/${code}`)
  }

  // Utility Methods

  /**
   * Convert indicator values to signals
   */
  async convertToSignals(data: {
    symbol: string
    indicators: Record<string, any[]>
    rules: Array<{
      indicator: string
      condition: string
      threshold?: number
    }>
  }): Promise<ApiResponse<Array<{
    timestamp: string
    signal: 'buy' | 'sell' | 'hold'
    strength: number
    reason: string
  }>>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/convert-signals', data)
  }

  /**
   * Backtest indicator combination
   */
  async backtestIndicators(data: {
    symbol: string
    interval: string
    startDate: string
    endDate: string
    indicators: Array<{
      name: string
      parameters: Record<string, any>
    }>
    rules: Array<{
      name: string
      conditions: Array<{
        indicator: string
        operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
        value: number
      }>
      action: 'buy' | 'sell'
    }>
    initialCapital: number
  }): Promise<ApiResponse<{
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    trades: Array<{
      entryDate: string
      exitDate: string
      entryPrice: number
      exitPrice: number
      profit: number
      signal: string
    }>
  }>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/backtest', data)
  }

  /**
   * Optimize indicator parameters
   */
  async optimizeIndicatorParameters(data: {
    symbol: string
    interval: string
    indicator: string
    parameterRanges: Record<string, {
      min: number
      max: number
      step: number
    }>
    objective: 'sharpe' | 'return' | 'winrate'
    startDate: string
    endDate: string
  }): Promise<ApiResponse<{
    bestParameters: Record<string, number>
    performance: {
      totalReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
    }
    optimizationResults: Array<{
      parameters: Record<string, number>
      performance: any
    }>
  }>> {
    return apiRequest.post<ApiResponse<any>>('/indicators/optimize', data)
  }
}

// Create singleton instance
export const indicatorService = new IndicatorService()