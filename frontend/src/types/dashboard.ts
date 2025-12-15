// Dashboard types definition

export interface DashboardStats {
  totalStrategies: number;
  activeStrategies: number;
  totalReturn: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  todayProfit: number;
  totalAssets: number;
}

export interface Strategy {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'paused' | 'error';
  return: number;
  dailyReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  tradesCount: number;
  lastActive: string;
  instruments: string[];
}

export interface Trade {
  id: string;
  strategyId: string;
  strategyName: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  amount: number;
  profit: number;
  timestamp: string;
  status: 'filled' | 'pending' | 'cancelled';
}

export interface PerformanceData {
  date: string;
  value: number;
  benchmark?: number;
  drawdown?: number;
}

export interface RealTimePrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: string;
}

export interface DashboardLayout {
  id: string;
  name: string;
  widgets: WidgetConfig[];
}

export interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  size: {
    w: number;
    h: number;
  };
  position: {
    x: number;
    y: number;
  };
  config?: Record<string, any>;
}