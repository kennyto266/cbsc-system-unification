// Strategy types - 策略类型定义

export interface Strategy {
  id: string;
  name: string;
  description?: string;
  type: StrategyType;
  status: StrategyStatus;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  lastRunAt?: string;
  parameters: StrategyParameters;
  performance?: StrategyPerformance;
  tags?: string[];
  isTemplate?: boolean;
  templateId?: string;
}

export enum StrategyType {
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  ARBITRAGE = 'arbitrage',
  TREND_FOLLOWING = 'trend_following',
  CUSTOM = 'custom',
}

export enum StrategyStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  ARCHIVED = 'archived',
  ERROR = 'error',
}

export interface StrategyParameters {
  [key: string]: any;
  // Common parameters
  symbols?: string[];
  timeframe?: string;
  initialCapital?: number;
  maxPositionSize?: number;
  stopLoss?: number;
  takeProfit?: number;
  // Strategy-specific parameters
  [strategySpecific: string]: any;
}

export interface StrategyPerformance {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgTradeReturn: number;
  volatility: number;
  calmarRatio: number;
  sortinoRatio: number;
  beta?: number;
  alpha?: number;
  // Performance data points for charts
  equityCurve?: Array<{
    date: string;
    value: number;
  }>;
  drawdownCurve?: Array<{
    date: string;
    value: number;
  }>;
  monthlyReturns?: Array<{
    month: string;
    return: number;
  }>;
}

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  type: StrategyType;
  category: string;
  parameters: StrategyParameters;
  defaultCode?: string;
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  createdBy: string;
  createdAt: string;
  usageCount: number;
  rating: number;
}

export interface StrategyFilter {
  search?: string;
  type?: StrategyType;
  status?: StrategyStatus;
  createdBy?: string;
  tags?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  performanceRange?: {
    minReturn?: number;
    maxReturn?: number;
    minSharpe?: number;
    maxDrawdown?: number;
  };
}

export interface StrategyListResponse {
  strategies: Strategy[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface BatchOperation {
  action: 'start' | 'stop' | 'pause' | 'archive' | 'delete' | 'update';
  strategyIds: string[];
  parameters?: StrategyParameters;
}

export interface BatchOperationResult {
  success: boolean;
  results: Array<{
    strategyId: string;
    success: boolean;
    error?: string;
  }>;
}

export interface StrategyFormData {
  name: string;
  description?: string;
  type: StrategyType;
  parameters: StrategyParameters;
  code?: string;
  tags: string[];
  isTemplate?: boolean;
}

export interface StrategyValidationResult {
  isValid: boolean;
  errors: Array<{
    field: string;
    message: string;
  }>;
  warnings: Array<{
    field: string;
    message: string;
  }>;
}

export interface StrategyRunRequest {
  strategyId: string;
  parameters?: StrategyParameters;
  backtestMode?: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface StrategyRunResult {
  runId: string;
  status: 'running' | 'completed' | 'failed';
  startTime: string;
  endTime?: string;
  performance?: StrategyPerformance;
  logs?: Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
  }>;
}