import { api } from './api'

// 个人策略管理相关的数据类型
export interface PersonalStrategySummary {
  strategy_id: string
  name: string
  strategy_type: string
  status: string
  is_active: boolean
  current_return: number
  daily_pnl: number
  risk_level: string
  last_updated: string
  created_at: string
}

export interface PersonalDashboardData {
  total_strategies: number
  active_strategies: number
  total_return: number
  daily_pnl: number
  best_performing: PersonalStrategySummary | null
  worst_performing: PersonalStrategySummary | null
  recent_signals: any[]
  market_overview: {
    market_status: string
    index_change: number
    volatility_index: number
    sector_performance: Record<string, number>
  }
}

export interface Strategy {
  id: string
  name: string
  description: string
  strategy_type: string
  status: string
  is_active: boolean
  parameters: Record<string, any>
  created_at: string
  updated_at: string
  risk_level?: string
  max_position_size?: number
}

export interface StrategyPerformance {
  strategy_type: string
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  calmar_ratio: number
  total_trades: number
  profit_trades: number
  avg_profit: number
  avg_loss: number
  last_updated: string
  daily_pnl?: number
}

export interface StrategyDetail {
  strategy: Strategy
  recent_signals: any[]
  performance: StrategyPerformance | null
  execution_history: any[]
}

export interface CreateStrategyRequest {
  name: string
  description: string
  strategy_type: string
  parameters: Record<string, any>
  template_id?: string
}

export interface UpdateStrategyRequest {
  name?: string
  description?: string
  parameters?: Record<string, any>
  status?: string
  is_active?: boolean
}

export interface StrategyListResponse {
  strategies: Strategy[]
  total_count: number
  page: number
  page_size: number
}

export interface UserPreferences {
  default_strategy_type?: string
  risk_tolerance: string
  notification_settings: Record<string, boolean>
  dashboard_layout: Record<string, any>
  auto_refresh_interval: number
}

// 个人策略管理API服务
export class PersonalStrategyService {
  // 获取个人仪表板数据
  async getDashboardData(): Promise<PersonalDashboardData> {
    try {
      const response = await api.get('/personal-strategies/dashboard')
      return response.data
    } catch (error) {
      console.error('获取仪表板数据失败:', error)
      throw error
    }
  }

  // 获取个人策略列表
  async getStrategies(params?: {
    page?: number
    page_size?: number
    strategy_type?: string
    status?: string
    is_active?: boolean
  }): Promise<StrategyListResponse> {
    try {
      const response = await api.get('/personal-strategies/strategies', { params })
      return response.data
    } catch (error) {
      console.error('获取策略列表失败:', error)
      throw error
    }
  }

  // 创建新的个人策略
  async createStrategy(request: CreateStrategyRequest): Promise<Strategy> {
    try {
      const response = await api.post('/personal-strategies/strategies', request)
      return response.data
    } catch (error) {
      console.error('创建策略失败:', error)
      throw error
    }
  }

  // 获取策略详情
  async getStrategyDetail(strategyId: string): Promise<StrategyDetail> {
    try {
      const response = await api.get(`/personal-strategies/strategies/${strategyId}`)
      return response.data
    } catch (error) {
      console.error('获取策略详情失败:', error)
      throw error
    }
  }

  // 更新策略
  async updateStrategy(strategyId: string, request: UpdateStrategyRequest): Promise<Strategy> {
    try {
      const response = await api.put(`/personal-strategies/strategies/${strategyId}`, request)
      return response.data
    } catch (error) {
      console.error('更新策略失败:', error)
      throw error
    }
  }

  // 删除策略
  async deleteStrategy(strategyId: string): Promise<void> {
    try {
      await api.delete(`/personal-strategies/strategies/${strategyId}`)
    } catch (error) {
      console.error('删除策略失败:', error)
      throw error
    }
  }

  // 获取策略性能指标
  async getStrategyMetrics(strategyId: string, timeRange?: number): Promise<any> {
    try {
      const params = timeRange ? { time_range: timeRange } : {}
      const response = await api.get(`/personal-strategies/strategies/${strategyId}/metrics`, { params })
      return response.data
    } catch (error) {
      console.error('获取策略性能指标失败:', error)
      throw error
    }
  }

  // 获取用户偏好设置
  async getUserPreferences(): Promise<UserPreferences> {
    try {
      const response = await api.get('/personal-strategies/preferences')
      return response.data
    } catch (error) {
      console.error('获取用户偏好设置失败:', error)
      throw error
    }
  }

  // 更新用户偏好设置
  async updateUserPreferences(preferences: UserPreferences): Promise<void> {
    try {
      await api.put('/personal-strategies/preferences', preferences)
    } catch (error) {
      console.error('更新用户偏好设置失败:', error)
      throw error
    }
  }

  // 批量操作策略
  async batchOperation(strategyIds: string[], operation: 'activate' | 'deactivate' | 'delete'): Promise<any> {
    try {
      const response = await api.post('/api/strategies/batch', {
        strategy_ids: strategyIds,
        operation
      })
      return response.data
    } catch (error) {
      console.error('批量操作策略失败:', error)
      throw error
    }
  }

  // 获取策略模板
  async getStrategyTemplates(category?: string): Promise<any[]> {
    try {
      const params = category ? { category } : {}
      const response = await api.get('/api/strategies/templates', { params })
      return response.data
    } catch (error) {
      console.error('获取策略模板失败:', error)
      throw error
    }
  }

  // 优化策略参数
  async optimizeStrategyParameters(strategyId: string, request: any): Promise<any> {
    try {
      const response = await api.post(`/api/strategies/${strategyId}/optimize`, request)
      return response.data
    } catch (error) {
      console.error('优化策略参数失败:', error)
      throw error
    }
  }

  // 执行策略
  async executeStrategy(strategyId: string, request?: any): Promise<any> {
    try {
      const response = await api.post(`/api/strategies/${strategyId}/execute`, request)
      return response.data
    } catch (error) {
      console.error('执行策略失败:', error)
      throw error
    }
  }

  // 停止策略执行
  async stopStrategyExecution(strategyId: string, executionId?: string): Promise<any> {
    try {
      const params = executionId ? { execution_id: executionId } : {}
      const response = await api.post(`/api/strategies/${strategyId}/stop`, null, { params })
      return response.data
    } catch (error) {
      console.error('停止策略执行失败:', error)
      throw error
    }
  }

  // 获取策略信号
  async getStrategySignals(
    strategyId: string,
    params?: {
      limit?: number
      start_time?: string
      end_time?: string
      signal_type?: string
    }
  ): Promise<any> {
    try {
      const response = await api.get(`/api/strategies/${strategyId}/signals`, { params })
      return response.data
    } catch (error) {
      console.error('获取策略信号失败:', error)
      throw error
    }
  }
}

// 创建服务实例
export const personalStrategyService = new PersonalStrategyService()

// 导出默认服务
export default personalStrategyService