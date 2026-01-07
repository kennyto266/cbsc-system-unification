/**
 * Performance Metrics Widget
 * Displays comprehensive performance indicators for trading strategies
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import {
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Clock,
  DollarSign,
  Info,
  Settings
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { useWebSocket } from '@hooks/useWebSocket';
import { cn } from '@/lib/utils';

// Type definitions
export interface PerformanceMetrics {
  period: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  avgTradeDuration: number;
  volatility: number;
  beta: number;
  alpha: number;
  calmarRatio: number;
  sortinoRatio: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
}

interface MetricData {
  date: string;
  value: number;
  benchmark?: number;
}

interface PerformanceMetricsWidgetProps {
  className?: string;
  metrics?: PerformanceMetrics;
  historicalData?: MetricData[];
  benchmark?: string;
  onPeriodChange?: (period: string) => void;
  onBenchmarkChange?: (benchmark: string) => void;
}

// Mock data for development
const mockMetrics: PerformanceMetrics = {
  period: '1M',
  totalReturn: 12.5,
  sharpeRatio: 1.85,
  maxDrawdown: -8.3,
  winRate: 65.4,
  profitFactor: 1.95,
  avgTradeDuration: 2.4, // days
  volatility: 15.2,
  beta: 0.85,
  alpha: 3.2,
  calmarRatio: 1.51,
  sortinoRatio: 2.1,
  totalTrades: 124,
  winningTrades: 81,
  losingTrades: 43
};

const generateHistoricalData = (): MetricData[] => {
  const data: MetricData[] = [];
  const startDate = new Date();
  startDate.setMonth(startDate.getMonth() - 1);

  let value = 100;
  let benchmark = 100;

  for (let i = 0; i < 30; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    value += (Math.random() - 0.45) * 2;
    benchmark += (Math.random() - 0.5) * 1.5;

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value,
      benchmark
    });
  }

  return data;
};

// Custom tooltip component
const CustomTooltip: React.FC<{ active?: any; payload?: any[]; label?: string }> = ({
  active,
  payload,
  label
}) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white p-3 border rounded-lg shadow-lg">
      <p className="text-sm font-medium">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center space-x-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span>{entry.name}: {entry.value.toFixed(2)}%</span>
        </div>
      ))}
    </div>
  );
};

// Metric card component
const MetricCard: React.FC<{
  title: string;
  value: number | string;
  unit?: string;
  trend?: number;
  good?: boolean;
  info?: string;
}> = ({ title, value, unit = '%', trend, good = true, info }) => {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="relative p-3 border rounded-lg hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">{title}</span>
        {info && (
          <div className="relative">
            <Info
              className="w-3 h-3 text-gray-400 cursor-help"
              onMouseEnter={() => setShowInfo(true)}
              onMouseLeave={() => setShowInfo(false)}
            />
            {showInfo && (
              <div className="absolute z-10 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg top-full right-0 mt-1">
                {info}
              </div>
            )}
          </div>
        )}
      </div>
      <div className="flex items-end justify-between">
        <div className="flex items-baseline">
          <span className={cn(
            'text-lg font-semibold',
            good ? 'text-green-600' : 'text-red-600'
          )}>
            {typeof value === 'number' ? value.toFixed(2) : value}
          </span>
          <span className="text-xs text-gray-500 ml-1">{unit}</span>
        </div>
        {trend !== undefined && (
          <div className={cn(
            'flex items-center text-xs',
            trend >= 0 ? 'text-green-600' : 'text-red-600'
          )}>
            {trend >= 0 ? (
              <TrendingUp className="w-3 h-3 mr-1" />
            ) : (
              <TrendingDown className="w-3 h-3 mr-1" />
            )}
            {Math.abs(trend).toFixed(1)}
          </div>
        )}
      </div>
    </div>
  );
};

export const PerformanceMetricsWidget: React.FC<PerformanceMetricsWidgetProps> = ({
  className,
  metrics = mockMetrics,
  historicalData = generateHistoricalData(),
  benchmark = 'S&P 500',
  onPeriodChange,
  onBenchmarkChange
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  const [selectedView, setSelectedView] = useState<'returns' | 'risk' | 'efficiency'>('returns');

  // Subscribe to performance updates via WebSocket
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('performance', (data) => {
      if (data.type === 'metrics_update') {
        // Handle real-time metrics updates
        console.log('Performance metrics updated:', data);
      }
    });

    return unsubscribe;
  }, [subscribe]);

  // Radar chart data for efficiency metrics
  const radarData = useMemo(() => [
    { metric: 'Sharpe', value: metrics.sharpeRatio * 20, fullMark: 50 },
    { metric: 'Win Rate', value: metrics.winRate, fullMark: 100 },
    { metric: 'Profit Factor', value: metrics.profitFactor * 20, fullMark: 100 },
    { metric: 'Calmar', value: metrics.calmarRatio * 20, fullMark: 50 },
    { metric: 'Sortino', value: metrics.sortinoRatio * 20, fullMark: 60 }
  ].map(item => ({
    ...item,
    value: Math.min(item.value, item.fullMark)
  })), [metrics]);

  // Risk metrics for bar chart
  const riskMetrics = useMemo(() => [
    { name: 'Volatility', value: metrics.volatility, color: '#3b82f6' },
    { name: 'Max Drawdown', value: Math.abs(metrics.maxDrawdown), color: '#ef4444' },
    { name: 'Beta', value: metrics.beta * 20, color: '#f59e0b' }
  ], [metrics]);

  // Period options
  const periods = ['1D', '1W', '1M', '3M', '6M', '1Y', 'All'];

  // Benchmark options
  const benchmarks = ['S&P 500', 'NASDAQ', 'Russell 2000', 'Custom'];

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Performance Metrics</CardTitle>
          <div className="flex items-center space-x-2">
            {/* Period Selector */}
            <Select value={selectedPeriod} onValueChange={(value) => {
              setSelectedPeriod(value);
              onPeriodChange?.(value);
            }}>
              <SelectTrigger className="w-20 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {periods.map(period => (
                  <SelectItem key={period} value={period}>{period}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* View Selector */}
            <Select value={selectedView} onValueChange={(value: any) => setSelectedView(value)}>
              <SelectTrigger className="w-24 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="returns">Returns</SelectItem>
                <SelectItem value="risk">Risk</SelectItem>
                <SelectItem value="efficiency">Efficiency</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Metrics Row */}
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            title="Total Return"
            value={metrics.totalReturn}
            good={metrics.totalReturn > 0}
            trend={metrics.totalReturn > 0 ? metrics.totalReturn : 0}
            info="Total portfolio return including all trades"
          />
          <MetricCard
            title="Sharpe Ratio"
            value={metrics.sharpeRatio}
            good={metrics.sharpeRatio > 1}
            info="Risk-adjusted return measure (higher is better)"
          />
          <MetricCard
            title="Max Drawdown"
            value={Math.abs(metrics.maxDrawdown)}
            good={metrics.maxDrawdown > -10}
            trend={metrics.maxDrawdown}
            info="Maximum peak-to-trough decline"
          />
          <MetricCard
            title="Win Rate"
            value={metrics.winRate}
            good={metrics.winRate > 50}
            info="Percentage of profitable trades"
          />
        </div>

        {/* Performance Chart */}
        {selectedView === 'returns' && (
          <div className="h-64">
            <h4 className="text-sm font-medium mb-2">Return vs Benchmark</h4>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Portfolio"
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#9ca3af"
                  strokeWidth={1}
                  name={benchmark}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Risk Metrics */}
        {selectedView === 'risk' && (
          <div className="space-y-4">
            <div className="h-48">
              <h4 className="text-sm font-medium mb-2">Risk Analysis</h4>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6">
                    {riskMetrics.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Efficiency Radar */}
        {selectedView === 'efficiency' && (
          <div className="h-64">
            <h4 className="text-sm font-medium mb-2">Efficiency Metrics</h4>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8 }} />
                <Radar
                  name="Strategy"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Additional Metrics */}
        <div className="grid grid-cols-3 gap-3">
          <MetricCard
            title="Profit Factor"
            value={metrics.profitFactor}
            good={metrics.profitFactor > 1.5}
            info="Ratio of gross profits to gross losses"
          />
          <MetricCard
            title="Avg Duration"
            value={metrics.avgTradeDuration}
            unit="days"
            good={metrics.avgTradeDuration < 5}
            info="Average holding period per trade"
          />
          <MetricCard
            title="Total Trades"
            value={metrics.totalTrades}
            unit=""
            info="Total number of executed trades"
          />
        </div>

        {/* Footer with benchmark selector */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <span>Benchmark:</span>
            <Select value={benchmark} onValueChange={onBenchmarkChange}>
              <SelectTrigger className="w-24 h-6 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {benchmarks.map(b => (
                  <SelectItem key={b} value={b}>{b}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center space-x-4">
            <span>Volatility: {metrics.volatility.toFixed(1)}%</span>
            <span>Beta: {metrics.beta.toFixed(2)}</span>
            <span>Alpha: {metrics.alpha.toFixed(2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PerformanceMetricsWidget;