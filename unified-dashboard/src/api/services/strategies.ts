/**
 * Strategy Management API Service
 * Handles all strategy-related API calls
 */

import { apiRequest } from '../client'
import { API_ENDPOINTS } from '../config'
import { ApiResponse, PaginatedResponse, BaseParams, ExportRequest } from '../types/common'
import {
  Strategy,
  CreateStrategyRequest,
  UpdateStrategyRequest,
  StrategyPerformance,
  StrategyBacktest,
  StrategyOptimization,
  StrategyExecution,
  StrategyParameters,
  StrategyHistory,
  StrategyTemplate,
  StrategyType,
  StrategyStatus,
  RiskLevel,
} from '../types/strategies'

export class StrategyService {
  /**
   * Get all strategies
   */
  async getStrategies(params?: BaseParams & {
    type?: StrategyType
    status?: StrategyStatus
    riskLevel?: RiskLevel
    search?: string
    sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'performance'
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<Strategy>> {
    return apiRequest.get<PaginatedResponse<Strategy>>(API_ENDPOINTS.STRATEGIES.LIST, { params })
  }

  /**
   * Get strategy by ID
   */
  async getStrategy(id: string): Promise<ApiResponse<Strategy>> {
    return apiRequest.get<ApiResponse<Strategy>>(API_ENDPOINTS.STRATEGIES.DETAIL(id))
  }

  /**
   * Create a new strategy
   */
  async createStrategy(data: CreateStrategyRequest): Promise<ApiResponse<Strategy>> {
    return apiRequest.post<ApiResponse<Strategy>>(API_ENDPOINTS.STRATEGIES.CREATE, data)
  }

  /**
   * Update strategy
   */
  async updateStrategy(id: string, data: UpdateStrategyRequest): Promise<ApiResponse<Strategy>> {
    return apiRequest.put<ApiResponse<Strategy>>(API_ENDPOINTS.STRATEGIES.UPDATE(id), data)
  }

  /**
   * Delete strategy
   */
  async deleteStrategy(id: string): Promise<void> {
    return apiRequest.delete<void>(API_ENDPOINTS.STRATEGIES.DELETE(id))
  }

  /**
   * Duplicate a strategy
   */
  async duplicateStrategy(id: string, name: string): Promise<ApiResponse<Strategy>> {
    return apiRequest.post<ApiResponse<Strategy>>(`${API_ENDPOINTS.STRATEGIES.DETAIL(id)}/duplicate`, { name })
  }

  /**
   * Execute strategy
   */
  async executeStrategy(id: string, data?: {
    symbols?: string[]
    initialCapital?: number
    parameters?: Record<string, any>
  }): Promise<ApiResponse<StrategyExecution>> {
    return apiRequest.post<ApiResponse<StrategyExecution>>(API_ENDPOINTS.STRATEGIES.EXECUTE(id), data)
  }

  /**
   * Stop strategy execution
   */
  async stopStrategy(id: string): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.STRATEGIES.STOP(id))
  }

  /**
   * Pause strategy execution
   */
  async pauseStrategy(id: string): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.STRATEGIES.PAUSE(id))
  }

  /**
   * Resume strategy execution
   */
  async resumeStrategy(id: string): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.STRATEGIES.RESUME(id))
  }

  /**
   * Get strategy performance
   */
  async getStrategyPerformance(
    id: string,
    params?: {
      timeRange?: '1d' | '1w' | '1m' | '3m' | '6m' | '1y'
      includeBenchmark?: boolean
    }
  ): Promise<ApiResponse<StrategyPerformance>> {
    return apiRequest.get<ApiResponse<StrategyPerformance>>(API_ENDPOINTS.STRATEGIES.PERFORMANCE(id), { params })
  }

  /**
   * Get strategy execution history
   */
  async getStrategyHistory(
    id: string,
    params?: BaseParams & {
      startDate?: string
      endDate?: string
      action?: string
    }
  ): Promise<PaginatedResponse<StrategyHistory>> {
    return apiRequest.get<PaginatedResponse<StrategyHistory>>(API_ENDPOINTS.STRATEGIES.HISTORY(id), { params })
  }

  /**
   * Get strategy parameters
   */
  async getStrategyParameters(id: string): Promise<ApiResponse<StrategyParameters>> {
    return apiRequest.get<ApiResponse<StrategyParameters>>(API_ENDPOINTS.STRATEGIES.PARAMETERS(id))
  }

  /**
   * Update strategy parameters
   */
  async updateStrategyParameters(id: string, parameters: Record<string, any>): Promise<ApiResponse<StrategyParameters>> {
    return apiRequest.put<ApiResponse<StrategyParameters>>(API_ENDPOINTS.STRATEGIES.PARAMETERS(id), { parameters })
  }

  /**
   * Run strategy backtest
   */
  async runBacktest(data: {
    strategyId: string
    symbols: string[]
    startDate: string
    endDate: string
    initialCapital: number
    parameters?: Record<string, any>
  }): Promise<ApiResponse<StrategyBacktest>> {
    return apiRequest.post<ApiResponse<StrategyBacktest>>(API_ENDPOINTS.STRATEGIES.BACKTEST, data)
  }

  /**
   * Get backtest results
   */
  async getBacktestResult(backtestId: string): Promise<ApiResponse<StrategyBacktest>> {
    return apiRequest.get<ApiResponse<StrategyBacktest>>(`/strategies/backtests/${backtestId}`)
  }

  /**
   * Run strategy optimization
   */
  async runOptimization(data: {
    strategyId: string
    symbols: string[]
    startDate: string
    endDate: string
    initialCapital: number
    parameters: {
      [key: string]: {
        min: number
        max: number
        step: number
      }
    }
    optimizationType: 'grid' | 'genetic' | 'bayesian'
    maxIterations?: number
  }): Promise<ApiResponse<StrategyOptimization>> {
    return apiRequest.post<ApiResponse<StrategyOptimization>>(API_ENDPOINTS.STRATEGIES.OPTIMIZE, data)
  }

  /**
   * Get optimization results
   */
  async getOptimizationResult(optimizationId: string): Promise<ApiResponse<StrategyOptimization>> {
    return apiRequest.get<ApiResponse<StrategyOptimization>>(`/strategies/optimizations/${optimizationId}`)
  }

  /**
   * Get strategy templates
   */
  async getStrategyTemplates(params?: BaseParams & {
    category?: string
    difficulty?: 'beginner' | 'intermediate' | 'advanced'
  }): Promise<PaginatedResponse<StrategyTemplate>> {
    return apiRequest.get<PaginatedResponse<StrategyTemplate>>('/strategies/templates', { params })
  }

  /**
   * Create strategy from template
   */
  async createFromTemplate(templateId: string, data: {
    name: string
    description?: string
    parameters?: Record<string, any>
  }): Promise<ApiResponse<Strategy>> {
    return apiRequest.post<ApiResponse<Strategy>>(`/strategies/templates/${templateId}/create`, data)
  }

  /**
   * Validate strategy code
   */
  async validateStrategyCode(code: string, language: 'python' | 'javascript'): Promise<ApiResponse<{
    valid: boolean
    errors?: string[]
    warnings?: string[]
  }>> {
    return apiRequest.post<ApiResponse<any>>('/strategies/validate', { code, language })
  }

  /**
   * Get strategy signals
   */
  async getStrategySignals(
    id: string,
    params?: BaseParams & {
      signalType?: 'buy' | 'sell' | 'hold'
      startDate?: string
      endDate?: string
    }
  ): Promise<PaginatedResponse<any>> {
    return apiRequest.get<PaginatedResponse<any>>(`/strategies/${id}/signals`, { params })
  }

  /**
   * Get strategy positions
   */
  async getStrategyPositions(
    id: string,
    params?: BaseParams
  ): Promise<PaginatedResponse<any>> {
    return apiRequest.get<PaginatedResponse<any>>(`/strategies/${id}/positions`, { params })
  }

  /**
   * Get strategy orders
   */
  async getStrategyOrders(
    id: string,
    params?: BaseParams & {
      status?: 'pending' | 'filled' | 'cancelled' | 'rejected'
      side?: 'buy' | 'sell'
    }
  ): Promise<PaginatedResponse<any>> {
    return apiRequest.get<PaginatedResponse<any>>(`/strategies/${id}/orders`, { params })
  }

  /**
   * Export strategy data
   */
  async exportStrategyData(id: string, request: ExportRequest): Promise<ApiResponse<{
    downloadUrl: string
    filename: string
  }>> {
    return apiRequest.post<ApiResponse<any>>(`/strategies/${id}/export`, request)
  }

  /**
   * Import strategy from file
   */
  async importStrategy(file: File): Promise<ApiResponse<Strategy>> {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest.post<ApiResponse<Strategy>>('/strategies/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  /**
   * Get strategy analytics
   */
  async getStrategyAnalytics(id: string): Promise<ApiResponse<{
    performance: any
    risk: any
    returns: any
    drawdowns: any
    trades: any
    monthlyReturns: any[]
  }>> {
    return apiRequest.get<ApiResponse<any>>(`/strategies/${id}/analytics`)
  }

  /**
   * Compare strategies
   */
  async compareStrategies(strategyIds: string[]): Promise<ApiResponse<{
    comparison: any[]
    metrics: Record<string, any>
    ranking: any[]
  }>> {
    return apiRequest.post<ApiResponse<any>>('/strategies/compare', { strategyIds })
  }
}

// Create singleton instance
export const strategyService = new StrategyService()