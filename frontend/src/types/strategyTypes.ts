/**
 * Strategy Management Types
 * 策略管理相關類型定義
 */

import { BacktestType } from './backtestTypes';

/**
 * Strategy Types Enum
 * 策略類型枚舉
 */
export enum StrategyType {
  TECHNICAL_INDICATORS = 'technical_indicators',
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  VOLUME = 'volume',
  VOLATILITY = 'volatility',
  FUNDAMENTAL = 'fundamental',
  QUANTITATIVE = 'quantitative',
  PORTFOLIO = 'portfolio',
  ARBITRAGE = 'arbitrage',
  MACRO = 'macro'
}

/**
 * Risk Tolerance Enum
 * 風險承受度枚舉
 */
export enum RiskTolerance {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EXTREME = 'extreme'
}

/**
 * Strategy Status Enum
 * 策略狀態枚舉
 */
export enum StrategyStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  ARCHIVED = 'archived'
}

/**
 * Time Range Options
 * 時間範圍選項
 */
export type TimeRange = '1d' | '1w' | '1m' | '1y' | 'all';

/**
 * Base Strategy Interface
 * 基礎策略接口
 */
export interface BaseStrategy {
  id: string;
  name: string;
  description?: string;
  strategy_type: StrategyType;
  version: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Strategy Create Request
 * 策略創建請求
 */
export interface StrategyCreateRequest {
  name: string;
  description?: string;
  strategy_type: StrategyType;
  version?: string;
  parameters: Record<string, any>;
  metadata?: Record<string, any>;
}

/**
 * Strategy Update Request
 * 策略更新請求
 */
export interface StrategyUpdateRequest {
  name?: string;
  description?: string;
  version?: string;
  parameters?: Record<string, any>;
  metadata?: Record<string, any>;
  is_active?: boolean;
}

/**
 * Strategy Response
 * 策略響應
 */
export interface Strategy extends BaseStrategy {
  parameters: Record<string, any>;
  metadata: Record<string, any>;
  user_id: string;
  created_by?: string;
  updated_by?: string;
  last_backtest_at?: string;
  performance_summary?: PerformanceSummary;
}

/**
 * Strategy Configuration
 * 策略配置
 */
export interface StrategyConfig {
  id: string;
  strategy_id: string;
  name: string;
  description?: string;
  parameters: Record<string, any>;
  risk_tolerance: RiskTolerance;
  initial_capital: number;
  position_sizing: number;
  stop_loss?: number;
  take_profit?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_id: string;
  backtest_results?: BacktestResult[];
}

/**
 * Strategy Configuration Create Request
 * 策略配置創建請求
 */
export interface StrategyConfigCreateRequest {
  config_data: {
    name: string;
    description?: string;
    parameters: Record<string, any>;
    risk_tolerance: RiskTolerance;
    initial_capital: number;
    position_sizing: number;
    stop_loss?: number;
    take_profit?: number;
  };
}

/**
 * Strategy Configuration Update Request
 * 策略配置更新請求
 */
export interface StrategyConfigUpdateRequest {
  name?: string;
  description?: string;
  parameters?: Record<string, any>;
  risk_tolerance?: RiskTolerance;
  initial_capital?: number;
  position_sizing?: number;
  stop_loss?: number;
  take_profit?: number;
  is_active?: boolean;
}

/**
 * Strategy Execution Request
 * 策略執行請求
 */
export interface StrategyExecutionRequest {
  config_id?: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  data_source?: string;
  symbols?: string[];
  parameters?: Record<string, any>;
  backtest_type?: BacktestType;
}

/**
 * Strategy Execution
 * 策略執行
 */
export interface StrategyExecution {
  id: string;
  strategy_id: string;
  config_id?: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'stopped';
  progress?: number;
  start_time?: string;
  end_time?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  request: StrategyExecutionRequest;
  results?: ExecutionResult;
  error_message?: string;
}

/**
 * Execution Result
 * 執行結果
 */
export interface ExecutionResult {
  total_return?: number;
  annual_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_trades?: number;
  win_rate?: number;
  profit_factor?: number;
  trades?: Trade[];
  equity_curve?: EquityPoint[];
}

/**
 * Trade
 * 交易記錄
 */
export interface Trade {
  id: string;
  execution_id: string;
  timestamp: string;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission?: number;
  pnl?: number;
  balance?: number;
  metadata?: Record<string, any>;
}

/**
 * Equity Point
 * 權益曲線點
 */
export interface EquityPoint {
  timestamp: string;
  equity: number;
  returns?: number;
  drawdown?: number;
}

/**
 * Performance Summary
 * 性能摘要
 */
export interface PerformanceSummary {
  total_return: number;
  annual_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  last_updated: string;
}

/**
 * Performance Metrics Response
 * 性能指標響應
 */
export interface PerformanceMetricsResponse {
  period_start: string;
  period_end: string;
  total_return: number;
  annual_return: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  recovery_time?: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  largest_win: number;
  largest_loss: number;
  var_95?: number;
  var_99?: number;
  beta?: number;
  alpha?: number;
  information_ratio?: number;
}

/**
 * Backtest Result
 * 回測結果
 */
export interface BacktestResult {
  id: string;
  config_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annual_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  status: 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  completed_at?: string;
  trades?: Trade[];
  equity_curve?: EquityPoint[];
}

/**
 * Paginated Response
 * 分頁響應
 */
export interface PaginatedResponse {
  items: any[];
  page: number;
  pageSize: number;
  total: number;
  pages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

/**
 * Strategy Category
 * 策略分類
 */
export interface StrategyCategory {
  id: string;
  name: string;
  display_name: string;
  description: string;
  parent_id?: string;
  level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  children?: StrategyCategory[];
}

/**
 * Strategy Comparison
 * 策略對比
 */
export interface StrategyComparison {
  strategies: Array<{
    strategy_id: string;
    name: string;
    metrics: PerformanceMetricsResponse;
  }>;
  comparison_period: {
    start_date: string;
    end_date: string;
  };
  ranking: Array<{
    strategy_id: string;
    rank: number;
    score: number;
    criteria: string;
  }>;
}

/**
 * Performance Report
 * 性能報告
 */
export interface PerformanceReport {
  strategy_id: string;
  strategy_name: string;
  report_type: 'summary' | 'detailed' | 'monthly';
  period: {
    start_date: string;
    end_date: string;
  };
  generated_at: string;
  data: any;
}

/**
 * Strategy Filter
 * 策略過濾器
 */
export interface StrategyFilter {
  strategy_types?: StrategyType[];
  is_active?: boolean;
  risk_tolerances?: RiskTolerance[];
  date_range?: {
    start_date?: string;
    end_date?: string;
  };
  performance_range?: {
    min_return?: number;
    max_return?: number;
    min_sharpe?: number;
    max_drawdown?: number;
  };
  search_term?: string;
}

/**
 * Strategy Sort Option
 * 策略排序選項
 */
export interface StrategySortOption {
  field: string;
  order: 'asc' | 'desc';
}

/**
 * Strategy List Options
 * 策略列表選項
 */
export interface StrategyListOptions {
  page?: number;
  pageSize?: number;
  filter?: StrategyFilter;
  sort?: StrategySortOption;
  search?: string;
}

/**
 * Dashboard Widget
 * Dashboard 組件
 */
export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  config: Record<string, any>;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  data?: any;
}

/**
 * Strategy Dashboard Config
 * 策略 Dashboard 配置
 */
export interface StrategyDashboardConfig {
  id: string;
  user_id: string;
  name: string;
  layout: DashboardWidget[];
  filters: StrategyFilter;
  created_at: string;
  updated_at: string;
  is_default: boolean;
}