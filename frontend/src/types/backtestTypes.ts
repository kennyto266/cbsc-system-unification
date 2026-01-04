/**
 * Backtest Types
 * 回測相關類型定義
 */

/**
 * Backtest Type Enum
 * 回測類型枚舉
 */
export enum BacktestType {
  SIMPLE = 'simple',
  VECTOR_BT = 'vector_bt',
  ENHANCED = 'enhanced',
  WALK_FORWARD = 'walk_forward',
  MONTE_CARLO = 'monte_carlo'
}

/**
 * Backtest Summary Response
 * 回測摘要響應
 */
export interface BacktestSummaryResponse {
  id: string;
  strategy_id: string;
  config_id: string;
  status: 'running' | 'completed' | 'failed';
  start_date: string;
  end_date: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  created_at: string;
}

/**
 * Backtest Config
 * 回測配置
 */
export interface BacktestConfig {
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission?: number;
  slippage?: number;
}
