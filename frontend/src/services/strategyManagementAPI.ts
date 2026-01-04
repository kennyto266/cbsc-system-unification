/**
 * Strategy Management API Service
 * 策略管理 API 服務
 */

import { apiClient } from './apiClient';
import {
  Strategy,
  StrategyConfig,
  StrategyType,
  RiskTolerance,
  BacktestType,
  StrategyCreateRequest,
  StrategyUpdateRequest,
  StrategyConfigCreateRequest,
  StrategyConfigUpdateRequest,
  PaginatedResponse,
  BacktestSummaryResponse,
  PerformanceMetricsResponse
} from '../types/strategyTypes';

export interface StrategyListParams {
  page?: number;
  pageSize?: number;
  strategyType?: StrategyType;
  is_active?: boolean;
  search?: string;
}

export interface StrategyConfigListParams {
  strategy_id: string;
  page?: number;
  pageSize?: number;
  is_active?: boolean;
  risk_tolerance?: RiskTolerance;
}

export interface StrategyPerformanceParams {
  strategy_id: string;
  time_range?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * Strategy Management API Class
 * 策略管理 API 類
 */
export class StrategyManagementAPI {
  private static readonly BASE_PATH = '/strategies';

  /**
   * Get strategies list with pagination and filtering
   * 獲取策略列表（支持分頁和過濾）
   */
  static async getStrategies(params?: StrategyListParams): Promise<PaginatedResponse> {
    const response = await apiClient.get(this.BASE_PATH, { params });
    return response.data;
  }

  /**
   * Get strategy by ID
   * 根據ID獲取策略詳情
   */
  static async getStrategy(strategyId: string): Promise<Strategy> {
    const response = await apiClient.get(`${this.BASE_PATH}/${strategyId}`);
    return response.data;
  }

  /**
   * Create new strategy
   * 創建新策略
   */
  static async createStrategy(strategyData: StrategyCreateRequest): Promise<Strategy> {
    const response = await apiClient.post(this.BASE_PATH, strategyData);
    return response.data;
  }

  /**
   * Update existing strategy
   * 更新策略
   */
  static async updateStrategy(
    strategyId: string,
    updateData: StrategyUpdateRequest
  ): Promise<Strategy> {
    const response = await apiClient.put(`${this.BASE_PATH}/${strategyId}`, updateData);
    return response.data;
  }

  /**
   * Delete strategy (soft delete)
   * 刪除策略（軟刪除）
   */
  static async deleteStrategy(strategyId: string): Promise<void> {
    await apiClient.delete(`${this.BASE_PATH}/${strategyId}`);
  }

  /**
   * Get strategy configurations
   * 獲取策略配置列表
   */
  static async getStrategyConfigs(params: StrategyConfigListParams): Promise<PaginatedResponse> {
    const response = await apiClient.get(
      `${this.BASE_PATH}/${params.strategy_id}/configs`,
      { params: { ...params, strategy_id: undefined } }
    );
    return response.data;
  }

  /**
   * Get strategy configuration by ID
   * 獲取策略配置詳情
   */
  static async getStrategyConfig(
    strategyId: string,
    configId: string
  ): Promise<StrategyConfig> {
    const response = await apiClient.get(
      `${this.BASE_PATH}/${strategyId}/configs/${configId}`
    );
    return response.data;
  }

  /**
   * Create strategy configuration
   * 創建策略配置
   */
  static async createStrategyConfig(
    strategyId: string,
    configData: StrategyConfigCreateRequest
  ): Promise<StrategyConfig> {
    const response = await apiClient.post(
      `${this.BASE_PATH}/${strategyId}/configs`,
      configData
    );
    return response.data;
  }

  /**
   * Update strategy configuration
   * 更新策略配置
   */
  static async updateStrategyConfig(
    strategyId: string,
    configId: string,
    updateData: StrategyConfigUpdateRequest
  ): Promise<StrategyConfig> {
    const response = await apiClient.put(
      `${this.BASE_PATH}/${strategyId}/configs/${configId}`,
      updateData
    );
    return response.data;
  }

  /**
   * Delete strategy configuration
   * 刪除策略配置
   */
  static async deleteStrategyConfig(
    strategyId: string,
    configId: string
  ): Promise<void> {
    await apiClient.delete(`${this.BASE_PATH}/${strategyId}/configs/${configId}`);
  }

  /**
   * Get strategy summary with latest performance
   * 獲取策略摘要和最新表現
   */
  static async getStrategySummary(strategyId: string): Promise<any> {
    const response = await apiClient.get(`${this.BASE_PATH}/${strategyId}/summary`);
    return response.data;
  }

  /**
   * Get strategy performance metrics
   * 獲取策略性能指標
   */
  static async getStrategyPerformance(
    strategyId: string,
    params?: StrategyPerformanceParams
  ): Promise<PerformanceMetricsResponse> {
    const response = await apiClient.get(
      `${this.BASE_PATH}/${strategyId}/performance`,
      { params }
    );
    return response.data;
  }

  /**
   * Compare strategies performance
   * 策略性能對比
   */
  static async compareStrategies(
    strategyId: string,
    compareWith: string[],
    timeRange?: string
  ): Promise<any> {
    const params = { compare_with: compareWith };
    if (timeRange) {
      Object.assign(params, { time_range: timeRange });
    }

    const response = await apiClient.get(
      `${this.BASE_PATH}/${strategyId}/performance/comparison`,
      { params }
    );
    return response.data;
  }

  /**
   * Generate performance report
   * 生成性能報告
   */
  static async generatePerformanceReport(
    strategyId: string,
    reportType: 'summary' | 'detailed' | 'monthly' = 'summary',
    timeRange?: string
  ): Promise<any> {
    const params = { report_type: reportType };
    if (timeRange) {
      Object.assign(params, { time_range: timeRange });
    }

    const response = await apiClient.get(
      `${this.BASE_PATH}/${strategyId}/performance/report`,
      { params }
    );
    return response.data;
  }

  /**
   * Get strategy categories
   * 獲取策略分類
   */
  static async getStrategyCategories(): Promise<any[]> {
    const response = await apiClient.get(`${this.BASE_PATH}/categories`);
    return response.data;
  }

  /**
   * Get available strategy types
   * 獲取可用策略類型
   */
  static async getStrategyTypes(): Promise<any[]> {
    const response = await apiClient.get(`${this.BASE_PATH}/types`);
    return response.data;
  }

  /**
   * Get available risk tolerance levels
   * 獲取可用風險承受水平
   */
  static async getRiskTolerances(): Promise<any[]> {
    const response = await apiClient.get(`${this.BASE_PATH}/risk-tolerances`);
    return response.data;
  }

  /**
   * Execute strategy
   * 執行策略
   */
  static async executeStrategy(
    strategyId: string,
    executionRequest: any
  ): Promise<any> {
    const response = await apiClient.post(
      `${this.BASE_PATH}/${strategyId}/executions`,
      executionRequest
    );
    return response.data;
  }

  /**
   * Get execution status
   * 獲取執行狀態
   */
  static async getExecutionStatus(
    strategyId: string,
    executionId: string
  ): Promise<any> {
    const response = await apiClient.get(
      `${this.BASE_PATH}/${strategyId}/executions/${executionId}`
    );
    return response.data;
  }

  /**
   * Stop strategy execution
   * 停止策略執行
   */
  static async stopExecution(
    strategyId: string,
    executionId: string
  ): Promise<any> {
    const response = await apiClient.post(
      `${this.BASE_PATH}/${strategyId}/executions/${executionId}/stop`
    );
    return response.data;
  }

  /**
   * Batch operations on strategies
   * 批量操作策略
   */
  static async batchOperation(
    operation: 'delete' | 'activate' | 'deactivate',
    strategyIds: string[]
  ): Promise<any> {
    const response = await apiClient.post(
      `${this.BASE_PATH}/batch`,
      { strategy_ids: strategyIds },
      { params: { operation } }
    );
    return response.data;
  }
}

// Export convenience methods
export const strategyAPI = {
  // Basic CRUD
  getStrategies: StrategyManagementAPI.getStrategies,
  getStrategy: StrategyManagementAPI.getStrategy,
  createStrategy: StrategyManagementAPI.createStrategy,
  updateStrategy: StrategyManagementAPI.updateStrategy,
  deleteStrategy: StrategyManagementAPI.deleteStrategy,

  // Configuration management
  getStrategyConfigs: StrategyManagementAPI.getStrategyConfigs,
  getStrategyConfig: StrategyManagementAPI.getStrategyConfig,
  createStrategyConfig: StrategyManagementAPI.createStrategyConfig,
  updateStrategyConfig: StrategyManagementAPI.updateStrategyConfig,
  deleteStrategyConfig: StrategyManagementAPI.deleteStrategyConfig,

  // Analytics and performance
  getStrategySummary: StrategyManagementAPI.getStrategySummary,
  getStrategyPerformance: StrategyManagementAPI.getStrategyPerformance,
  compareStrategies: StrategyManagementAPI.compareStrategies,
  generatePerformanceReport: StrategyManagementAPI.generatePerformanceReport,

  // Execution
  executeStrategy: StrategyManagementAPI.executeStrategy,
  getExecutionStatus: StrategyManagementAPI.getExecutionStatus,
  stopExecution: StrategyManagementAPI.stopExecution,

  // Utilities
  getStrategyCategories: StrategyManagementAPI.getStrategyCategories,
  getStrategyTypes: StrategyManagementAPI.getStrategyTypes,
  getRiskTolerances: StrategyManagementAPI.getRiskTolerances,
  batchOperation: StrategyManagementAPI.batchOperation,
};

export default StrategyManagementAPI;