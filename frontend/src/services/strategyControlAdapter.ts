import { strategyControlService } from './strategyControlService';
import {
  StrategyControlRequest,
  BatchStrategyControlRequest,
  StrategyControlResult,
  BatchStrategyControlResult
} from './strategyControlService';

// Strategy status types (matching component expectations)
export type StrategyStatus = 'active' | 'inactive' | 'paused' | 'stopped' | 'error';

// Strategy data interface (matching component expectations)
export interface StrategyData {
  id: string;
  name: string;
  isActive: boolean;
  status: StrategyStatus;
  lastUpdated?: string;
  performance?: {
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturn: number;
    winRate: number;
  };
}

// Batch operation types (matching component expectations)
export type BatchOperation = 'enable' | 'disable' | 'pause' | 'stop';

// API response types (matching component expectations)
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// WebSocket message types
interface StrategyUpdateMessage {
  type: 'strategy_update';
  strategyId: string;
  status: StrategyStatus;
  isActive: boolean;
  timestamp: string;
}

/**
 * Strategy Control Adapter - Bridges existing service with component expectations
 */
class StrategyControlAdapter {
  private ws: WebSocket | null = null;
  private wsUrl: string = process.env.REACT_APP_WS_URL || 'ws://localhost:3004/ws';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private subscribers: Array<(message: StrategyUpdateMessage) => void> = [];

  /**
   * Get all strategies (mock implementation - should be enhanced with real API)
   */
  async getAllStrategies(): Promise<ApiResponse<StrategyData[]>> {
    try {
      // Mock data - replace with actual API call
      const mockStrategies: StrategyData[] = [
        {
          id: 'direct_rsi',
          name: '直接RSI情绪策略',
          isActive: false,
          status: 'inactive',
          performance: {
            sharpeRatio: 1.85,
            maxDrawdown: 0.12,
            totalReturn: 0.35,
            winRate: 0.65,
          },
        },
        {
          id: 'sentiment_momentum',
          name: '情绪动量策略',
          isActive: true,
          status: 'active',
          performance: {
            sharpeRatio: 2.12,
            maxDrawdown: 0.08,
            totalReturn: 0.42,
            winRate: 0.71,
          },
        },
        {
          id: 'composite_index',
          name: '综合指数策略',
          isActive: false,
          status: 'inactive',
          performance: {
            sharpeRatio: 1.65,
            maxDrawdown: 0.15,
            totalReturn: 0.28,
            winRate: 0.58,
          },
        },
        {
          id: 'volatility_adjusted',
          name: '波动率调整策略',
          isActive: false,
          status: 'inactive',
          performance: {
            sharpeRatio: 1.93,
            maxDrawdown: 0.10,
            totalReturn: 0.38,
            winRate: 0.67,
          },
        },
      ];

      return {
        success: true,
        data: mockStrategies,
      };
    } catch (error: any) {
      console.error('Get all strategies error:', error);
      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * Get single strategy by ID
   */
  async getStrategy(strategyId: string): Promise<ApiResponse<StrategyData>> {
    const allResult = await this.getAllStrategies();
    if (!allResult.success || !allResult.data) {
      return allResult as ApiResponse<any>;
    }

    const strategy = allResult.data.find(s => s.id === strategyId);
    if (!strategy) {
      return {
        success: false,
        error: 'Strategy not found',
      };
    }

    return {
      success: true,
      data: strategy,
    };
  }

  /**
   * Toggle strategy (enable/disable) using existing service
   */
  async toggleStrategy(
    strategyId: string,
    enabled: boolean
  ): Promise<ApiResponse<any>> {
    try {
      let result: StrategyControlResult;

      if (enabled) {
        result = await strategyControlService.enableStrategy(strategyId, '用户操作启用');
      } else {
        result = await strategyControlService.disableStrategy(strategyId, '用户操作禁用');
      }

      return {
        success: result.success,
        data: result,
      };
    } catch (error: any) {
      console.error('Toggle strategy error:', error);
      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * Control strategy (start, stop, pause, resume) using existing service
   */
  async controlStrategy(
    strategyId: string,
    action: 'start' | 'stop' | 'pause' | 'resume'
  ): Promise<ApiResponse<any>> {
    try {
      let result: StrategyControlResult;

      switch (action) {
        case 'start':
          result = await strategyControlService.startStrategy(strategyId, '用户操作启动');
          break;
        case 'stop':
          result = await strategyControlService.stopStrategy(strategyId, '用户操作停止', true);
          break;
        case 'pause':
          result = await strategyControlService.pauseStrategy(strategyId, '用户操作暂停');
          break;
        case 'resume':
          result = await strategyControlService.startStrategy(strategyId, '用户操作恢复');
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      return {
        success: result.success,
        data: result,
      };
    } catch (error: any) {
      console.error('Control strategy error:', error);
      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * Batch control multiple strategies using existing service
   */
  async batchControlStrategies(
    strategyIds: string[],
    operation: BatchOperation
  ): Promise<ApiResponse<any>> {
    try {
      let result: BatchStrategyControlResult;

      switch (operation) {
        case 'enable':
          result = await strategyControlService.batchEnableStrategies(strategyIds, '批量操作启用');
          break;
        case 'disable':
          result = await strategyControlService.batchDisableStrategies(strategyIds, '批量操作禁用', true);
          break;
        case 'pause':
          result = await strategyControlService.batchPauseStrategies(strategyIds, '批量操作暂停');
          break;
        case 'stop':
          result = await strategyControlService.batchStopStrategies(strategyIds, '批量操作停止', true);
          break;
        default:
          throw new Error(`Unknown operation: ${operation}`);
      }

      return {
        success: true,
        data: {
          results: result.results.map(r => ({
            strategyId: r.strategy_id,
            success: r.success,
            error: r.success ? undefined : r.message,
          })),
        },
      };
    } catch (error: any) {
      console.error('Batch control strategies error:', error);
      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * Get operation history using existing service
   */
  async getOperationHistory(
    strategyId?: string,
    limit: number = 50
  ): Promise<ApiResponse<any[]>> {
    try {
      if (!strategyId) {
        // Return empty array for now - could implement batch history fetching
        return {
          success: true,
          data: [],
        };
      }

      const history = await strategyControlService.getOperationHistory(strategyId, limit);
      const formattedLogs = strategyControlService.formatOperationLogs(history.logs);

      return {
        success: true,
        data: formattedLogs,
      };
    } catch (error: any) {
      console.error('Get operation history error:', error);
      return {
        success: false,
        error: error.message || 'Network error',
      };
    }
  }

  /**
   * Initialize WebSocket connection for real-time updates
   */
  initializeWebSocket(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('Strategy Control WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: StrategyUpdateMessage = JSON.parse(event.data);
          this.notifySubscribers(message);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('Strategy Control WebSocket disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('Strategy Control WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  }

  /**
   * Close WebSocket connection
   */
  closeWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to WebSocket updates
   */
  subscribe(callback: (message: StrategyUpdateMessage) => void): () => void {
    this.subscribers.push(callback);

    // Initialize WebSocket if not already connected
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.initializeWebSocket();
    }

    // Return unsubscribe function
    return () => {
      const index = this.subscribers.indexOf(callback);
      if (index > -1) {
        this.subscribers.splice(index, 1);
      }
    };
  }

  /**
   * Notify all subscribers of WebSocket message
   */
  private notifySubscribers(message: StrategyUpdateMessage): void {
    this.subscribers.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('Subscriber callback error:', error);
      }
    });
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max WebSocket reconnection attempts reached');
      return;
    }

    setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`WebSocket reconnection attempt ${this.reconnectAttempts}`);
      this.initializeWebSocket();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  /**
   * Get strategy performance metrics (mock implementation)
   */
  async getStrategyPerformance(strategyId: string): Promise<ApiResponse<any>> {
    // This would be implemented with actual performance API
    return {
      success: true,
      data: {
        sharpeRatio: 1.85,
        maxDrawdown: 0.12,
        totalReturn: 0.35,
        winRate: 0.65,
      },
    };
  }

  /**
   * Get real-time strategy status (mock implementation)
   */
  async getRealtimeStatus(strategyIds: string[]): Promise<ApiResponse<any>> {
    // This would be implemented with actual real-time status API
    const statusMap: Record<string, StrategyStatus> = {
      'direct_rsi': 'inactive',
      'sentiment_momentum': 'active',
      'composite_index': 'inactive',
      'volatility_adjusted': 'inactive',
    };

    const data = strategyIds.map(id => ({
      id,
      status: statusMap[id] || 'inactive',
      isActive: statusMap[id] === 'active',
    }));

    return {
      success: true,
      data,
    };
  }
}

// Create singleton instance
export const strategyControlAdapter = new StrategyControlAdapter();

export default strategyControlAdapter;