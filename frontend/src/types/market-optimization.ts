/**
 * Market-Wide Optimization Type Definitions
 */

// Strategy parameters
export interface StrategyParams {
  short_period: number;
  long_period: number;
}

// Single optimization result
export interface StrategyResult {
  symbol: string;
  params: StrategyParams;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  excess_return: number;
  information_ratio: number;
  equity_curve: number[];
  bnh_equity_curve: number[];
}

// Best overall strategy
export interface BestOverall {
  symbol: string;
  sharpe_ratio: number;
  params: StrategyParams;
}

// Summary statistics
export interface ResultSummary {
  total_backtests_run: number;
  qualification_rate: number;
  best_sharpe_ratio: number;
  best_symbol: string;
}

// Complete optimization results
export interface OptimizationResults {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  total_time_seconds: number;
  total_stocks: number;
  total_combinations: number;
  qualified_results_count: number;
  best_overall: BestOverall;
  top_10: StrategyResult[];
  summary: ResultSummary;
  error?: string;
}

// Progress update data
export interface ProgressData {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_stocks: number;
  waiting_stocks: number;
  processing_stocks: number;
  completed_stocks: number;
  current_stock_number: number;
  current_stock_symbol: string;
  best_sharpe_ratio: number;
  best_params: StrategyParams;
  best_symbol: string;
  elapsed_seconds: number;
  estimated_remaining_seconds: number;
  progress_percentage: number;
}

// API response for starting optimization
export interface StartOptimizationResponse {
  task_id: string;
  status: string;
  message: string;
  total_stocks: number;
  estimated_combinations: number;
}

// Configuration for starting optimization
export interface OptimizationConfig {
  symbols?: string[];
  stock_count?: number;
  start_date: string;
  end_date: string;
  strategy_type?: string;
  initial_cash?: number;
  commission?: number;
  min_sharpe_ratio?: number;
  max_workers?: number;
}

// Metric card data
export interface MetricData {
  label: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'flat';
  format?: 'percentage' | 'number' | 'currency';
}
