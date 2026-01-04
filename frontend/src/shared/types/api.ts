// CBSC Trading System - API Type Definitions
// Centralized type definitions for API requests and responses

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  timestamp: string;
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Strategy types
 */
export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: 'momentum' | 'reversal' | 'breakout' | 'custom';
  status: 'active' | 'inactive' | 'testing';
  parameters: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  performance?: {
    totalReturn: number;
    winRate: number;
    maxDrawdown: number;
    sharpeRatio: number;
  };
}

export interface StrategyCreateInput {
  name: string;
  description: string;
  type: Strategy['type'];
  parameters: Record<string, unknown>;
}

export interface StrategyUpdateInput {
  id: string;
  name?: string;
  description?: string;
  status?: Strategy['status'];
  parameters?: Record<string, unknown>;
}

/**
 * Backtest types
 */
export interface Backtest {
  id: string;
  strategyId: string;
  strategyName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startDate: string;
  endDate: string;
  initialCapital: number;
  results?: {
    finalValue: number;
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number;
    totalTrades: number;
  };
  createdAt: string;
  completedAt?: string;
}

export interface BacktestCreateInput {
  strategyId: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  parameters?: Record<string, unknown>;
}

/**
 * Real-time data types
 */
export interface RealtimeQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: string;
}

export interface MarketData {
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
}

/**
 * Auth types
 */
export interface LoginInput {
  username: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
  };
}

/**
 * Dashboard types
 */
export interface DashboardStats {
  totalStrategies: number;
  activeStrategies: number;
  totalBacktests: number;
  runningBacktests: number;
  todayTrades: number;
  portfolioValue: number;
  dailyReturn: number;
}
