export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  role?: string
  createdAt?: string
  updatedAt?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp: string
}

// Strategy related types
export enum StrategyType {
  SENTIMENT = 'sentiment',
  TECHNICAL = 'technical',
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  ARBITRAGE = 'arbitrage'
}

export enum StrategyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  ARCHIVED = 'archived'
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export interface Strategy {
  id: string
  name: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  description?: string
  parameters: Record<string, any>
  performance: {
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
  }
  createdAt: string
  updatedAt: string
  lastActive?: string
}

// WebSocket擴展類型
export interface WebSocketStatus {
  connected: boolean
  reconnecting: boolean
  lastError?: string
  reconnectAttempts: number
}

export interface StrategyUpdate {
  id: string
  name: string
  category: string
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  volatility: number
  risk_level: string
  last_updated: string
}

export interface TradingSignal {
  id: string
  category: string
  signal: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  strength: number
  timestamp: Date
}

export interface SystemHealth {
  active_connections: number
  total_strategies: number
  server_uptime?: string
  memory_usage: string
  cpu_usage: string
  last_update: string
}
