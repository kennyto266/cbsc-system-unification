/**
 * Economic Strategy API Service
 * 經濟策略 API 服務
 *
 * 提供經濟策略的 CRUD 操作和狀態管理功能
 */

import { api } from './api'

// TypeScript type definitions
export interface EconomicStrategy {
  id: string
  name: string
  type: 'hibor' | 'gdp' | 'pmi' | 'visitors' | 'unemployment' | 'composite'
  status: 'active' | 'inactive' | 'running' | 'stopped' | 'error'
  config: Record<string, any>
  created_at: string
  updated_at?: string
  description?: string
}

export interface CreateStrategyRequest {
  name: string
  type: EconomicStrategy['type']
  config: Record<string, any>
  description?: string
}

export interface UpdateStrategyRequest {
  name?: string
  config?: Record<string, any>
  description?: string
}

export interface StartStrategyParams {
  symbols: string[]
  initial_capital: number
  max_position_size?: number
  risk_limit?: number
}

export interface StrategyPerformance {
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  profit_factor?: number
  average_win?: number
  average_loss?: number
}

export interface StrategySignal {
  id: string
  strategy_id: string
  timestamp: string
  symbol: string
  signal_type: 'buy' | 'sell' | 'neutral'
  strength: number
  confidence: number
  price: number
  metadata: Record<string, any>
}

// Type alias for strategy position
export type StrategyPosition = {
  symbol: string
  quantity: number
  entry_price: number
  current_price: number
  pnl: number
}

/**
 * Economic Strategy API Service Class
 */
class EconomicStrategyApiService {
  /**
   * Get all economic strategies
   */
  async getEconomicStrategies(params: {
    type?: EconomicStrategy['type']
    status?: EconomicStrategy['status']
    page?: number
    limit?: number
  } = {}): Promise<{ success: boolean; data: EconomicStrategy[] }> {
    try {
      const response = await api.get('/strategies/economic', { params })
      return response
    } catch (error) {
      console.error('Error fetching economic strategies:', error)
      throw error
    }
  }

  /**
   * Get economic strategy by ID
   */
  async getEconomicStrategyById(id: string): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.get(`/strategies/economic/${id}`)
      return response
    } catch (error) {
      console.error(`Error fetching economic strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Create a new economic strategy
   */
  async createEconomicStrategy(
    data: CreateStrategyRequest
  ): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.post('/strategies/economic', data)
      return response
    } catch (error) {
      console.error('Error creating economic strategy:', error)
      throw error
    }
  }

  /**
   * Update an economic strategy
   */
  async updateEconomicStrategy(
    id: string,
    data: UpdateStrategyRequest
  ): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.put(`/strategies/economic/${id}`, data)
      return response
    } catch (error) {
      console.error(`Error updating economic strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Delete an economic strategy
   */
  async deleteEconomicStrategy(id: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.delete(`/strategies/economic/${id}`)
      return response
    } catch (error) {
      console.error(`Error deleting economic strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Start an economic strategy
   */
  async startEconomicStrategy(
    id: string,
    params: StartStrategyParams
  ): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.post(`/strategies/economic/${id}/start`, params)
      return response
    } catch (error) {
      console.error(`Error starting economic strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Stop an economic strategy
   */
  async stopEconomicStrategy(id: string): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.post(`/strategies/economic/${id}/stop`)
      return response
    } catch (error) {
      console.error(`Error stopping economic strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Get strategy performance data
   */
  async getStrategyPerformance(
    id: string,
    params: {
      start_date?: string
      end_date?: string
      benchmark?: string
    } = {}
  ): Promise<{ success: boolean; data: StrategyPerformance }> {
    try {
      const response = await api.get(`/strategies/economic/${id}/performance`, { params })
      return response
    } catch (error) {
      console.error(`Error fetching strategy performance ${id}:`, error)
      throw error
    }
  }

  /**
   * Get strategy signals
   */
  async getStrategySignals(
    id: string,
    params: {
      start_date?: string
      end_date?: string
      limit?: number
      offset?: number
    } = {}
  ): Promise<{ success: boolean; data: StrategySignal[] }> {
    try {
      const response = await api.get(`/strategies/economic/${id}/signals`, { params })
      return response
    } catch (error) {
      console.error(`Error fetching strategy signals ${id}:`, error)
      throw error
    }
  }

  /**
   * Get strategy positions
   */
  async getStrategyPositions(
    id: string
  ): Promise<{ success: boolean; data: StrategyPosition[] }> {
    try {
      const response = await api.get(`/strategies/economic/${id}/positions`)
      return response
    } catch (error) {
      console.error(`Error fetching strategy positions ${id}:`, error)
      throw error
    }
  }

  /**
   * Get strategy configuration templates
   */
  async getStrategyTemplates(): Promise<{
    success: boolean
    data: Array<{
      type: EconomicStrategy['type']
      name: string
      description: string
      default_config: Record<string, any>
    }>
  }> {
    try {
      const response = await api.get('/strategies/economic/templates')
      return response
    } catch (error) {
      console.error('Error fetching strategy templates:', error)
      throw error
    }
  }

  /**
   * Validate strategy configuration
   */
  async validateStrategyConfig(
    type: EconomicStrategy['type'],
    config: Record<string, any>
  ): Promise<{ success: boolean; valid: boolean; errors?: string[] }> {
    try {
      const response = await api.post('/strategies/economic/validate', { type, config })
      return response
    } catch (error) {
      console.error('Error validating strategy config:', error)
      throw error
    }
  }

  /**
   * Clone an existing strategy
   */
  async cloneStrategy(
    id: string,
    newName: string
  ): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.post(`/strategies/economic/${id}/clone`, { name: newName })
      return response
    } catch (error) {
      console.error(`Error cloning strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Export strategy configuration
   */
  async exportStrategy(id: string): Promise<{ success: boolean; data: string }> {
    try {
      const response = await api.get(`/strategies/economic/${id}/export`)
      return response
    } catch (error) {
      console.error(`Error exporting strategy ${id}:`, error)
      throw error
    }
  }

  /**
   * Import strategy configuration
   */
  async importStrategy(
    configData: string,
    name: string
  ): Promise<{ success: boolean; data: EconomicStrategy }> {
    try {
      const response = await api.post('/strategies/economic/import', { config: configData, name })
      return response
    } catch (error) {
      console.error('Error importing strategy:', error)
      throw error
    }
  }
}

// Export singleton instance
export const economicStrategyApi = new EconomicStrategyApiService()

// Export types
export type {
  EconomicStrategy,
  CreateStrategyRequest,
  UpdateStrategyRequest,
  StartStrategyParams,
  StrategyPerformance,
  StrategySignal,
}