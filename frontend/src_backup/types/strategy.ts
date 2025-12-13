export interface Strategy {
  id: number;
  name: string;
  category: string;
  subcategory: string;
  annual_return: number;
  sharpe_ratio: number | null;
  max_drawdown: number;
  win_rate: number;
  volatility: number;
  trading_frequency: 'low' | 'medium' | 'high' | 'monthly' | 'daily' | 'weekly';
  risk_level: 'low' | 'medium' | 'high';
  grade: string;
  description: string;
}

// 向後兼容的策略接口
export interface LegacyStrategy {
  id: string;
  name: string;
  type: string;
  category: 'monthly' | 'multi_strategy' | 'multi_factor' | 'core_cbsc' | 'other';
  status: 'active' | 'inactive' | 'error' | 'processing';
  performance?: PerformanceMetrics;
  parameters: Record<string, any>;
  latestSignal?: TradingSignal;
  description: string;
}

export interface PerformanceMetrics {
  totalReturn: number;
  annualReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  winRate: number;
  profitFactor: number;
  calmarRatio: number;
  var95: number;
  cvar95: number;
  lastUpdated?: Date;
  dataQualityScore: number;
}

export interface TradingSignal {
  type: string;
  strength: number;
  confidence: number;
  timestamp?: Date;
}

export interface StrategyFilter {
  category: 'all' | 'monthly' | 'multi_strategy' | 'multi_factor' | 'core_cbsc' | 'other';
  status: 'all' | 'active' | 'inactive' | 'error' | 'processing';
  performance: 'all' | 'excellent' | 'good' | 'average' | 'poor';
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  strategy?: Strategy;
  performance?: PerformanceMetrics;
  signals?: Record<string, any>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface StrategyListResponse {
  strategies: Strategy[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PerformanceSummary {
  totalStrategies: number;
  activeStrategies: number;
  averageSharpeRatio: number;
  averageReturn: number;
  bestPerforming: {
    strategyId: string;
    strategyName: string;
    sharpeRatio: number;
  };
  worstPerforming: {
    strategyId: string;
    strategyName: string;
    sharpeRatio: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  apiResponseTime: number;
  websocketConnected: boolean;
  lastUpdate: Date;
  dataFreshness: 'fresh' | 'stale' | 'outdated';
}