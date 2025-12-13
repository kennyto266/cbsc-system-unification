// Core Strategy Types
export interface Strategy {
  id: string;
  name: string;
  type: string;
  category: 'core_cbsc' | 'multi_factor' | 'other';
  status: 'active' | 'inactive' | 'testing' | 'archived';
  performance?: PerformanceMetrics;
  parameters: Record<string, any>;
  latestSignal?: Signal;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  riskLevel: 'low' | 'medium' | 'high' | 'extreme';
  tags?: string[];
  assignedBy?: string;
  personalConfig?: PersonalStrategyConfig;
}

export interface PerformanceMetrics {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  winRate: number;
  profitFactor: number;
  calmarRatio: number;
  var95: number;
  cvar95: number;
  lastUpdated: Date;
  dataQualityScore: number;
}

export interface Signal {
  type: 'buy' | 'sell' | 'hold';
  strength: number;
  confidence: number;
  timestamp: Date;
  source: string;
  metadata?: Record<string, any>;
}

export interface StrategyFilter {
  category: string;
  status: string;
  performance: string;
  riskLevel: string;
  tag?: string;
  search?: string;
}

// Personal Strategy Management Types
export interface PersonalStrategyConfig {
  userId: string;
  customParameters: Record<string, any>;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  capitalAllocation: number;
  maxPositionSize: number;
  stopLoss: number;
  takeProfit: number;
  notifications: NotificationSettings;
  autoTrading: boolean;
  customName?: string;
  notes?: string;
}

export interface NotificationSettings {
  email: boolean;
  sms: boolean;
  push: boolean;
  signalAlert: boolean;
  riskAlert: boolean;
  performanceReport: boolean;
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly';
}

export interface UserPortfolio {
  id: string;
  userId: string;
  totalValue: number;
  availableCash: number;
  allocatedCapital: number;
  strategies: PortfolioStrategy[];
  performanceHistory: PortfolioSnapshot[];
  riskMetrics: PortfolioRiskMetrics;
  createdAt: Date;
  updatedAt: Date;
}

export interface PortfolioStrategy {
  strategyId: string;
  allocation: number;
  currentValue: number;
  costBasis: number;
  unrealizedPnL: number;
  realizedPnL: number;
  positions: Position[];
  lastRebalanced: Date;
}

export interface Position {
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  side: 'long' | 'short';
  openDate: Date;
}

export interface PortfolioSnapshot {
  date: Date;
  totalValue: number;
  cash: number;
  positionsValue: number;
  dailyReturn: number;
  cumulativeReturn: number;
}

export interface PortfolioRiskMetrics {
  var95: number;
  cvar95: number;
  beta: number;
  correlation: number;
  concentration: number;
  leverage: number;
}

// UI Component Types
export interface DashboardMetrics {
  totalValue: number;
  dailyChange: number;
  dailyChangePercent: number;
  totalReturn: number;
  sharpeRatio: number;
  activeStrategies: number;
  totalSignals: number;
  winRate: number;
  portfolioHealth: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface ChartDataPoint {
  timestamp: string | Date;
  value: number;
  benchmark?: number;
  volume?: number;
}

export interface MarketData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  lastUpdate: Date;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'strategy_update' | 'performance_update' | 'new_signals' | 'portfolio_update' | 'market_update';
  data: any;
  timestamp: string;
}

// Configuration Types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto';
  primaryColor: string;
  accentColor: string;
  customColors?: Record<string, string>;
}

export interface UserPreferences {
  theme: ThemeConfig;
  language: string;
  timezone: string;
  dateFormat: string;
  numberFormat: string;
  defaultTimeRange: '1d' | '1w' | '1m' | '3m' | '6m' | '1y';
  chartType: 'line' | 'area' | 'candlestick' | 'ohlc';
  refreshInterval: number;
}