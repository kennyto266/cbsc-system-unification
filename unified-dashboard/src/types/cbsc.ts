/**
 * CBSC (牛熊证) 相关类型定义
 * CBSC (Callable Bull/Bear Contract) Type Definitions
 */

// CBSC 合约信息
export interface CBSCContract {
  rank: number;
  code: string;
  name: string;
  price: number;
  strike: number;
  expiry: string;
  leverage: number;
  volume: number;
  change: number;
}

// 牛熊证前十名数据
export interface CBSCTopContracts {
  bull_contracts: CBSCContract[];
  bear_contracts: CBSCContract[];
}

// 市场情绪指标
export interface MarketSentiment {
  fear_greed_index: number;
  bull_bear_ratio: number;
  realized_volatility: number;
  rsi_signal: number;
  sentiment_score: number;
  sentiment_label: string;
  update_time: string;
}

// 历史数据点
export interface HistoricalDataPoint {
  date: string;
  hsif_close: number;
  hsif_return: number;
  fear_greed_index?: number;
  bull_bear_ratio?: number;
  realized_volatility?: number;
  volume?: number;
}

// 统计信息
export interface CBSCStatistics {
  hsif_current: number;
  hsif_change: number;
  hsif_change_percent: number;
  total_volume: number;
  active_contracts: number;
  market_capitalization: number;
  last_update: string;
}

// Dashboard 综合数据
export interface CBSCDashboardData {
  market_sentiment: MarketSentiment;
  top_contracts: CBSCTopContracts;
  statistics: CBSCStatistics;
}

// API 响应格式
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

// 历史数据 API 响应
export interface HistoricalDataResponse {
  historical_data: HistoricalDataPoint[];
  metric: string;
  period_days: number;
  start_date: string;
  end_date: string;
}

// 图表数据类型
export interface ChartDataPoint {
  x: string; // 日期
  y: number; // 值
}

// 图表配置
export interface ChartConfig {
  title: string;
  xAxis: string;
  yAxis: string;
  color: string;
  type: 'line' | 'bar' | 'area';
}