// =============================================================================
// 核心类型定义 (Core Type Definitions)
// =============================================================================

export interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  role: UserRole;
  isActive: boolean;
  emailVerified: boolean;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserRole {
  id: string;
  name: string;
  permissions: string[];
  isSystemRole: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// =============================================================================
// 策略管理类型 (Strategy Management Types)
// =============================================================================

export enum StrategyType {
  CBSCTECHNICAL = 'cbsc_technical',
  CBSCSENTIMENT = 'cbsc_sentiment',
  CBSCTECHNICALADVANCED = 'cbsc_technical_advanced',
  MONTHLYLOWFREQUENCY = 'monthly_low_frequency',
  MULTISTRATEGYVALIDATION = 'multi_strategy_validation',
  MULTIFACTORMODEL = 'multi_factor_model',
  CORECBSCTECHNICAL = 'core_cbsc_technical',
  CORECBSCTECHNICALADVANCED = 'core_cbsc_technical_advanced',
  CORECBSCSENTIMENT = 'core_cbsc_sentiment',
  CORECBSCAGGRESSIVE = 'core_cbsc_aggressive'
}

export enum StrategyStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  ERROR = 'error'
}

export enum SignalType {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold',
  STRONGBUY = 'strong_buy',
  STRONGSELL = 'strong_sell'
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  strategyType: StrategyType;
  parameters: Record<string, any>;
  status: StrategyStatus;
  isActive: boolean;
  riskLevel: RiskLevel;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  lastRunAt?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface StrategySignal {
  signalId: string;
  strategyType: StrategyType;
  signalType: SignalType;
  strength: number;
  confidence: number;
  timestamp: string;
  marketData: Record<string, any>;
  parameters: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface StrategyPerformance {
  strategyType: StrategyType;
  totalReturn: number;
  annualReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  calmarRatio: number;
  totalTrades: number;
  profitTrades: number;
  avgProfit: number;
  avgLoss: number;
  lastUpdated: string;
}

export interface StrategyExecutionRequest {
  strategyId: string;
  executionMode: 'backtest' | 'real_time';
  startTime?: string;
  endTime?: string;
  dataSource?: string;
  parametersOverride?: Record<string, any>;
}

export interface StrategyExecutionResult {
  executionId: string;
  strategyId: string;
  status: 'running' | 'completed' | 'error' | 'stopped';
  startTime: string;
  endTime?: string;
  signals?: StrategySignal[];
  performance?: StrategyPerformance;
  error?: string;
  logs?: string[];
}

export interface CreateStrategyRequest {
  name: string;
  description: string;
  strategyType: StrategyType;
  parameters: Record<string, any>;
  templateId?: string;
}

export interface UpdateStrategyRequest {
  name?: string;
  description?: string;
  parameters?: Record<string, any>;
  status?: StrategyStatus;
  isActive?: boolean;
}

export interface StrategyListResponse {
  strategies: Strategy[];
  totalCount: number;
  page: number;
  pageSize: number;
}

export interface StrategyDetailResponse {
  strategy: Strategy;
  recentSignals: StrategySignal[];
  performance?: StrategyPerformance;
  executionHistory: StrategyExecutionResult[];
}

export interface BatchStrategyOperation {
  strategyIds: string[];
  operation: 'activate' | 'deactivate' | 'delete';
  parameters?: Record<string, any>;
}

export interface StrategyOptimizationRequest {
  optimizationMethod: 'grid' | 'random' | 'bayes' | 'genetic' | 'particle_swarm';
  parameterRanges: Record<string, [number, number]>;
  objectiveMetric: 'sharpe_ratio' | 'total_return' | 'calmar_ratio' | 'win_rate';
  maxIterations: number;
  timeRange?: {
    startTime: string;
    endTime: string;
  };
}

export interface StrategyOptimizationResult {
  optimizationId: string;
  strategyId: string;
  bestParameters: Record<string, any>;
  bestPerformance: StrategyPerformance;
  optimizationHistory: Array<{
    iteration: number;
    parameters: Record<string, any>;
    performance: Record<string, number>;
  }>;
  convergenceInfo: Record<string, any>;
}

export interface CBSCStrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  strategyType: StrategyType;
  defaultParameters: Record<string, any>;
  parameterDescriptions: Record<string, string>;
  riskLevel: RiskLevel;
  expectedReturn: number;
  tags: string[];
}

// =============================================================================
// 监控和实时数据类型 (Monitoring and Real-time Data Types)
// =============================================================================

export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  timestamp: string;
  services: Record<string, {
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    lastCheck: string;
    error?: string;
  }>;
  resources: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  };
}

export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  timestamp: string;
  bid?: number;
  ask?: number;
  high?: number;
  low?: number;
}

export interface WebSocketMessage {
  type: 'performance_update' | 'signals_update' | 'market_data' | 'system_status' | 'strategy_execution';
  timestamp: string;
  data: any;
}

export interface MonitoringState {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  systemStatus: SystemStatus | null;
  marketData: Record<string, MarketData>;
  activeStrategies: Strategy[];
}

// =============================================================================
// 分析和报告类型 (Analytics and Reporting Types)
// =============================================================================

export interface AnalyticsData {
  portfolio: {
    totalValue: number;
    totalReturn: number;
    dailyReturn: number;
    winRate: number;
    sharpeRatio: number;
    maxDrawdown: number;
  };
  strategies: Array<{
    id: string;
    name: string;
    performance: StrategyPerformance;
    recentSignals: StrategySignal[];
  }>;
  market: {
    trend: 'bullish' | 'bearish' | 'neutral';
    volatility: 'low' | 'medium' | 'high';
    sentiment: 'positive' | 'negative' | 'neutral';
  };
}

export interface ReportConfig {
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  startDate: string;
  endDate: string;
  strategies: string[];
  includeMetrics: string[];
  format: 'pdf' | 'excel' | 'json';
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
    tension?: number;
  }>;
}

// =============================================================================
// UI 和应用状态类型 (UI and Application State Types)
// =============================================================================

export interface UIState {
  theme: 'light' | 'dark' | 'auto';
  sidebarCollapsed: boolean;
  currentPath: string;
  loading: {
    global: boolean;
    strategies: boolean;
    analytics: boolean;
    monitoring: boolean;
  };
  notifications: Notification[];
  modals: {
    strategyDetail: boolean;
    createStrategy: boolean;
    settings: boolean;
  };
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

export interface AppState {
  auth: AuthState;
  strategies: StrategyState;
  monitoring: MonitoringState;
  analytics: AnalyticsData | null;
  ui: UIState;
}

export interface StrategyState {
  list: Strategy[];
  templates: CBSCStrategyTemplate[];
  selectedStrategy: Strategy | null;
  signals: StrategySignal[];
  executions: Record<string, StrategyExecutionResult>;
  loading: boolean;
  error: string | null;
}

// =============================================================================
// API 响应类型 (API Response Types)
// =============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// =============================================================================
// 配置类型 (Configuration Types)
// =============================================================================

export interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retries: number;
  };
  websocket: {
    url: string;
    reconnectInterval: number;
    maxReconnectAttempts: number;
  };
  features: {
    enableRealTimeData: boolean;
    enableNotifications: boolean;
    enableAnalytics: boolean;
    enableAdvancedCharts: boolean;
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    language: 'zh-CN' | 'en-US';
    timezone: string;
  };
}

// =============================================================================
// 导出所有类型 (Export All Types)
// =============================================================================

export type {
  // User & Auth
  User,
  UserRole,
  AuthState,

  // Strategy Management
  Strategy,
  StrategySignal,
  StrategyPerformance,
  StrategyExecutionRequest,
  StrategyExecutionResult,
  CreateStrategyRequest,
  UpdateStrategyRequest,
  StrategyListResponse,
  StrategyDetailResponse,
  BatchStrategyOperation,
  StrategyOptimizationRequest,
  StrategyOptimizationResult,
  CBSCStrategyTemplate,

  // Monitoring & Real-time
  SystemStatus,
  MarketData,
  WebSocketMessage,
  MonitoringState,

  // Analytics & Reports
  AnalyticsData,
  ReportConfig,
  ChartData,

  // UI & App State
  UIState,
  Notification,
  AppState,
  StrategyState,

  // API & Configuration
  ApiResponse,
  PaginatedResponse,
  AppConfig
};