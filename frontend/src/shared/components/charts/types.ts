// Chart component types

export interface PerformanceData {
  date: string;
  value: number;
  benchmark?: number;
}

export interface DataPoint {
  time: string;
  value: number;
}

export interface ChartStats {
  avg: number;
  min: number;
  max: number;
  trend: 'up' | 'down' | 'stable';
}

export interface PerformanceChartProps {
  data?: PerformanceData[];
  height?: number;
  showBenchmark?: boolean;
  title?: string;
}

export interface RealTimeChartProps {
  title?: string;
  dataSource?: () => Promise<number>;
  updateInterval?: number;
  maxDataPoints?: number;
  height?: number;
  className?: string;
}

export interface StrategyChartData {
  name: string;
  sharpeRatio: number;
  maxDrawdown: number;
  totalReturn: number;
  winRate: number;
}
