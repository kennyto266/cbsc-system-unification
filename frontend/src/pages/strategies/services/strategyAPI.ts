import { apiService } from '@/services/api'
import type {
  Strategy,
  StrategyFilter,
  StrategyListResponse,
  StrategyTemplate,
  StrategyFormData,
  StrategyValidationResult,
  StrategyRunRequest,
  StrategyRunResult,
  BatchOperation,
  BatchOperationResult,
} from '../types'

// Strategy API service - 策略API服务
export const strategyAPI = {
  // Get strategies with filters - 获取策略列表
  getStrategies: async (filter?: StrategyFilter): Promise<StrategyListResponse> => {
    const params = new URLSearchParams()

    if (filter?.search) params.append('search', filter.search)
    if (filter?.type) params.append('type', filter.type)
    if (filter?.status) params.append('status', filter.status)
    if (filter?.createdBy) params.append('createdBy', filter.createdBy)
    if (filter?.tags?.length) params.append('tags', filter.tags.join(','))

    if (filter?.dateRange) {
      params.append('startDate', filter.dateRange.start)
      params.append('endDate', filter.dateRange.end)
    }

    if (filter?.performanceRange) {
      if (filter.performanceRange.minReturn !== undefined) {
        params.append('minReturn', filter.performanceRange.minReturn.toString())
      }
      if (filter.performanceRange.maxReturn !== undefined) {
        params.append('maxReturn', filter.performanceRange.maxReturn.toString())
      }
      if (filter.performanceRange.minSharpe !== undefined) {
        params.append('minSharpe', filter.performanceRange.minSharpe.toString())
      }
      if (filter.performanceRange.maxDrawdown !== undefined) {
        params.append('maxDrawdown', filter.performanceRange.maxDrawdown.toString())
      }
    }

    return apiService.strategies.getAll(params.toString())
  },

  // Get strategy by ID - 根据ID获取策略
  getStrategy: async (id: string): Promise<Strategy> => {
    return apiService.strategies.getById(id)
  },

  // Create new strategy - 创建新策略
  createStrategy: async (data: StrategyFormData): Promise<Strategy> => {
    return apiService.strategies.create(data)
  },

  // Update strategy - 更新策略
  updateStrategy: async (id: string, data: Partial<StrategyFormData>): Promise<Strategy> => {
    return apiService.strategies.update(id, data)
  },

  // Delete strategy - 删除策略
  deleteStrategy: async (id: string): Promise<void> => {
    return apiService.strategies.delete(id)
  },

  // Duplicate strategy - 复制策略
  duplicateStrategy: async (id: string, name: string): Promise<Strategy> => {
    const original = await apiService.strategies.getById(id)
    return apiService.strategies.create({
      ...original,
      name,
      id: undefined,
    })
  },

  // Validate strategy - 验证策略
  validateStrategy: async (data: StrategyFormData): Promise<StrategyValidationResult> => {
    return apiService.strategies.post('/validate', data)
  },

  // Run strategy - 运行策略
  runStrategy: async (request: StrategyRunRequest): Promise<StrategyRunResult> => {
    return apiService.strategies.run(request.strategyId, request)
  },

  // Stop strategy - 停止策略
  stopStrategy: async (id: string): Promise<void> => {
    return apiService.strategies.stop(id)
  },

  // Get strategy performance - 获取策略性能
  getStrategyPerformance: async (id: string): Promise<any> => {
    return apiService.strategies.getPerformance(id)
  },

  // Get strategy templates - 获取策略模板
  getStrategyTemplates: async (type?: string): Promise<StrategyTemplate[]> => {
    const params = type ? { type } : {}
    return apiService.strategies.get('/templates', { params })
  },

  // Create strategy from template - 从模板创建策略
  createFromTemplate: async (
    templateId: string,
    data: { name: string; description?: string; parameters?: any }
  ): Promise<Strategy> => {
    return apiService.strategies.post(`/templates/${templateId}/create`, data)
  },

  // Batch operations - 批量操作
  batchOperation: async (operation: BatchOperation): Promise<BatchOperationResult> => {
    return apiService.strategies.post('/batch', operation)
  },

  // Export strategies - 导出策略
  exportStrategies: async (ids: string[]): Promise<Blob> => {
    const response = await apiService.strategies.post('/export', { ids }, {
      responseType: 'blob',
    })
    return response
  },

  // Import strategies - 导入策略
  importStrategies: async (file: File): Promise<{
    imported: Strategy[]
    errors: Array<{ row: number; error: string }>
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    return apiService.strategies.post('/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // Get strategy history - 获取策略历史
  getStrategyHistory: async (id: string): Promise<Array<{
    date: string;
    action: string;
    user: string;
    details?: any;
  }>> => {
    return apiService.strategies.get(`/${id}/history`)
  },

  // Get strategy logs - 获取策略日志
  getStrategyLogs: async (
    id: string,
    options?: {
      level?: 'info' | 'warning' | 'error'
      startDate?: string
      endDate?: string
      limit?: number
    }
  ): Promise<Array<{
    timestamp: string;
    level: string;
    message: string;
  }>> => {
    const params = new URLSearchParams()
    if (options?.level) params.append('level', options.level)
    if (options?.startDate) params.append('startDate', options.startDate)
    if (options?.endDate) params.append('endDate', options.endDate)
    if (options?.limit) params.append('limit', options.limit.toString())

    return apiService.strategies.get(`/${id}/logs?${params.toString()}`)
  },
}

export default strategyAPI