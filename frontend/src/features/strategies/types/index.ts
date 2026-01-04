// Strategy management types

export type StrategyStatus = 'active' | 'inactive' | 'paused' | 'stopped' | 'error';

export interface StrategyPerformance {
  sharpeRatio: number;
  maxDrawdown: number;
  totalReturn: number;
  winRate: number;
}

export interface StrategyData {
  id: string;
  name: string;
  isActive: boolean;
  status: StrategyStatus;
  lastUpdated?: string;
  performance?: StrategyPerformance;
}

export type BatchOperation = 'enable' | 'disable' | 'pause' | 'stop';

export interface StrategyControlResponse {
  success: boolean;
  data?: StrategyData[];
  error?: string;
  results?: Array<{
    strategyId: string;
    success: boolean;
    error?: string;
  }>;
}
