// Auth types
export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  role: UserRole;
  isActive: boolean;
  emailVerified: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
}

export interface UserRole {
  id: string;
  name: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
}

export interface Session {
  user: User;
  expires: string;
  accessToken?: string;
}

// Strategy types
export interface Strategy {
  id: string;
  name: string;
  description?: string;
  type: StrategyType;
  parameters: StrategyParameters;
  isActive: boolean;
  isPublic: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  tags?: string[];
  performance?: StrategyPerformance;
}

export type StrategyType =
  | 'trend_following'
  | 'mean_reversion'
  | 'momentum'
  | 'arbitrage'
  | 'market_making'
  | 'statistical_arbitrage'
  | 'custom';

export interface StrategyParameters {
  [key: string]: number | string | boolean;
  // Common parameters
  timeframe?: string;
  riskLevel?: 'low' | 'medium' | 'high';
  maxPositionSize?: number;
  stopLoss?: number;
  takeProfit?: number;
  // Strategy-specific parameters
  [key: string]: any;
}

export interface StrategyPerformance {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  averageTrade: number;
  volatility: number;
  beta?: number;
  alpha?: number;
  calmarRatio?: number;
}

// Backtest types
export interface Backtest {
  id: string;
  strategyId: string;
  name: string;
  description?: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  parameters: StrategyParameters;
  results?: BacktestResults;
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface BacktestResults {
  finalCapital: number;
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  averageTrade: number;
  volatility: number;
  equity: EquityPoint[];
  trades: Trade[];
  metrics: BacktestMetrics;
}

export interface EquityPoint {
  date: string;
  equity: number;
  drawdown: number;
}

export interface Trade {
  id: string;
  symbol: string;
  type: 'long' | 'short';
  entryDate: string;
  exitDate?: string;
  entryPrice: number;
  exitPrice?: number;
  quantity: number;
  profit?: number;
  profitPercentage?: number;
  exitReason?: string;
}

export interface BacktestMetrics {
  // Risk metrics
  var95?: number;
  var99?: number;
  cvar95?: number;
  skewness?: number;
  kurtosis?: number;

  // Performance metrics
  sortinoRatio?: number;
  informationRatio?: number;
  beta?: number;
  alpha?: number;
  calmarRatio?: number;

  // Trade statistics
  averageWinningTrade?: number;
  averageLosingTrade?: number;
  largestWinningTrade?: number;
  largestLosingTrade?: number;
  averageTradeDuration?: number;
  averageWinningTradeDuration?: number;
  averageLosingTradeDuration?: number;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
  field?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// UI Component types
export interface TableColumn {
  key: string;
  title: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string | number;
  render?: (value: any, record: any) => React.ReactNode;
}

export interface TableAction {
  key: string;
  label: string;
  icon?: React.ReactNode;
  onClick: (record: any) => void;
  disabled?: (record: any) => boolean;
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string;
  borderWidth?: number;
  fill?: boolean;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: string;
  read: boolean;
}

// Dashboard types
export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  size: WidgetSize;
  position: WidgetPosition;
  config: WidgetConfig;
  data?: any;
}

export type WidgetType =
  | 'performance_summary'
  | 'equity_curve'
  | 'drawdown_chart'
  | 'trade_distribution'
  | 'strategy_list'
  | 'recent_activity'
  | 'market_overview'
  | 'risk_metrics'
  | 'custom';

export interface WidgetSize {
  width: number;
  height: number;
}

export interface WidgetPosition {
  x: number;
  y: number;
}

export interface WidgetConfig {
  [key: string]: any;
  refreshInterval?: number;
  autoRefresh?: boolean;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface RealtimeUpdate {
  type: 'strategy' | 'backtest' | 'market' | 'system';
  id: string;
  data: any;
  timestamp: string;
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'radio' | 'date' | 'file';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ label: string; value: any }>;
  validation?: ValidationRule[];
  defaultValue?: any;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

// Search and filter types
export interface SearchFilter {
  field?: string;
  operator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'nin';
  value?: any;
}

export interface SearchParams {
  query?: string;
  filters?: SearchFilter[];
  sort?: {
    field: string;
    order: 'asc' | 'desc';
  };
  page?: number;
  limit?: number;
}