import { API_BASE_URL } from './config';

// API 响应类型定义
export interface StrategyControlRequest {
  action: 'enable' | 'disable' | 'start' | 'stop' | 'pause';
  reason?: string;
  confirm?: boolean;
}

export interface BatchStrategyControlRequest {
  strategy_ids: string[];
  action: 'enable' | 'disable' | 'start' | 'stop' | 'pause';
  reason?: string;
  confirm?: boolean;
}

export interface StrategyControlResult {
  strategy_id: string;
  success: boolean;
  action: string;
  previous_status: boolean;
  new_status: boolean;
  message: string;
  timestamp: string;
  requires_confirmation?: boolean;
}

export interface BatchStrategyControlResult {
  total_count: number;
  success_count: number;
  failure_count: number;
  results: StrategyControlResult[];
  batch_id: string;
  timestamp: string;
}

export interface OperationLog {
  log_id: string;
  user_id: number;
  strategy_id: string;
  action: string;
  previous_status?: boolean;
  new_status?: boolean;
  reason?: string;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  success: boolean;
  error_message?: string;
}

export interface OperationHistoryResponse {
  strategy_id: string;
  total_logs: number;
  logs: OperationLog[];
}

/**
 * 策略控制服务类
 * 提供策略启用/禁用、批量操作和操作历史查询功能
 */
class StrategyControlService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * 控制单个策略
   * @param strategyId 策略ID
   * @param request 控制请求
   * @returns 控制结果
   */
  async controlStrategy(strategyId: string, request: StrategyControlRequest): Promise<StrategyControlResult> {
    try {
      const response = await fetch(`${this.baseUrl}/personal-strategies/strategies/${strategyId}/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: '请求失败' }));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('控制策略失败:', error);
      throw error;
    }
  }

  /**
   * 批量控制策略
   * @param request 批量控制请求
   * @returns 批量控制结果
   */
  async batchControlStrategies(request: BatchStrategyControlRequest): Promise<BatchStrategyControlResult> {
    try {
      const response = await fetch(`${this.baseUrl}/personal-strategies/strategies/batch-control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: '请求失败' }));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('批量控制策略失败:', error);
      throw error;
    }
  }

  /**
   * 获取策略操作历史
   * @param strategyId 策略ID
   * @param limit 返回记录数限制
   * @returns 操作历史
   */
  async getOperationHistory(strategyId: string, limit: number = 50): Promise<OperationHistoryResponse> {
    try {
      const response = await fetch(
        `${this.baseUrl}/personal-strategies/strategies/${strategyId}/operation-history?limit=${limit}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getAuthToken()}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: '请求失败' }));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('获取操作历史失败:', error);
      throw error;
    }
  }

  /**
   * 启用策略
   * @param strategyId 策略ID
   * @param reason 操作原因
   * @returns 控制结果
   */
  async enableStrategy(strategyId: string, reason?: string): Promise<StrategyControlResult> {
    return this.controlStrategy(strategyId, {
      action: 'enable',
      reason,
    });
  }

  /**
   * 禁用策略
   * @param strategyId 策略ID
   * @param reason 操作原因
   * @param confirm 是否确认（危险操作需要）
   * @returns 控制结果
   */
  async disableStrategy(strategyId: string, reason?: string, confirm?: boolean): Promise<StrategyControlResult> {
    return this.controlStrategy(strategyId, {
      action: 'disable',
      reason,
      confirm,
    });
  }

  /**
   * 启动策略
   * @param strategyId 策略ID
   * @param reason 操作原因
   * @returns 控制结果
   */
  async startStrategy(strategyId: string, reason?: string): Promise<StrategyControlResult> {
    return this.controlStrategy(strategyId, {
      action: 'start',
      reason,
    });
  }

  /**
   * 停止策略
   * @param strategyId 策略ID
   * @param reason 操作原因
   * @param confirm 是否确认（危险操作需要）
   * @returns 控制结果
   */
  async stopStrategy(strategyId: string, reason?: string, confirm?: boolean): Promise<StrategyControlResult> {
    return this.controlStrategy(strategyId, {
      action: 'stop',
      reason,
      confirm,
    });
  }

  /**
   * 暂停策略
   * @param strategyId 策略ID
   * @param reason 操作原因
   * @returns 控制结果
   */
  async pauseStrategy(strategyId: string, reason?: string): Promise<StrategyControlResult> {
    return this.controlStrategy(strategyId, {
      action: 'pause',
      reason,
    });
  }

  /**
   * 批量启用策略
   * @param strategyIds 策略ID列表
   * @param reason 操作原因
   * @returns 批量控制结果
   */
  async batchEnableStrategies(strategyIds: string[], reason?: string): Promise<BatchStrategyControlResult> {
    return this.batchControlStrategies({
      strategy_ids: strategyIds,
      action: 'enable',
      reason,
    });
  }

  /**
   * 批量禁用策略
   * @param strategyIds 策略ID列表
   * @param reason 操作原因
   * @param confirm 是否确认（危险操作需要）
   * @returns 批量控制结果
   */
  async batchDisableStrategies(strategyIds: string[], reason?: string, confirm?: boolean): Promise<BatchStrategyControlResult> {
    return this.batchControlStrategies({
      strategy_ids: strategyIds,
      action: 'disable',
      reason,
      confirm,
    });
  }

  /**
   * 批量停止策略
   * @param strategyIds 策略ID列表
   * @param reason 操作原因
   * @param confirm 是否确认（危险操作需要）
   * @returns 批量控制结果
   */
  async batchStopStrategies(strategyIds: string[], reason?: string, confirm?: boolean): Promise<BatchStrategyControlResult> {
    return this.batchControlStrategies({
      strategy_ids: strategyIds,
      action: 'stop',
      reason,
      confirm,
    });
  }

  /**
   * 批量暂停策略
   * @param strategyIds 策略ID列表
   * @param reason 操作原因
   * @returns 批量控制结果
   */
  async batchPauseStrategies(strategyIds: string[], reason?: string): Promise<BatchStrategyControlResult> {
    return this.batchControlStrategies({
      strategy_ids: strategyIds,
      action: 'pause',
      reason,
    });
  }

  /**
   * 获取认证token
   * @returns JWT token
   */
  private getAuthToken(): string {
    // 从localStorage获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未找到认证token，请先登录');
    }
    return token;
  }

  /**
   * 验证策略操作权限
   * @param action 操作类型
   * @returns 是否有权限
   */
  hasPermission(action: string): boolean {
    // 这里可以根据用户的角色和权限系统进行验证
    // 暂时返回true，实际应用中应该从用户状态或权限服务获取
    const userRole = localStorage.getItem('user_role') || 'user';

    // 管理员可以执行所有操作
    if (userRole === 'admin') {
      return true;
    }

    // 普通用户不能执行危险操作
    const dangerousActions = ['stop', 'disable'];
    return !dangerousActions.includes(action);
  }

  /**
   * 格式化操作历史记录
   * @param logs 操作日志列表
   * @returns 格式化后的日志
   */
  formatOperationLogs(logs: OperationLog[]): Array<{
    id: string;
    action: string;
    description: string;
    timestamp: string;
    status: 'success' | 'failed';
  }> {
    return logs.map(log => ({
      id: log.log_id,
      action: log.action,
      description: this.formatActionDescription(log.action, log.previous_status, log.new_status),
      timestamp: new Date(log.timestamp).toLocaleString(),
      status: log.success ? 'success' : 'failed',
    }));
  }

  /**
   * 格式化操作描述
   * @param action 操作类型
   * @param previousStatus 之前状态
   * @param newStatus 新状态
   * @returns 操作描述
   */
  private formatActionDescription(action: string, previousStatus?: boolean, newStatus?: boolean): string {
    const actionTexts: Record<string, string> = {
      enable: '启用',
      disable: '禁用',
      start: '启动',
      stop: '停止',
      pause: '暂停',
      batch_enable: '批量启用',
      batch_disable: '批量禁用',
      batch_start: '批量启动',
      batch_stop: '批量停止',
      batch_pause: '批量暂停',
    };

    const actionText = actionTexts[action] || action;

    if (previousStatus !== undefined && newStatus !== undefined) {
      const statusText = (status: boolean) => status ? '运行中' : '已停止';
      return `${actionText}: ${statusText(previousStatus)} → ${statusText(newStatus)}`;
    }

    return actionText;
  }
}

// 创建并导出服务实例
export const strategyControlService = new StrategyControlService();
export default strategyControlService;