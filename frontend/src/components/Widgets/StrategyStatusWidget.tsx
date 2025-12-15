/**
 * Strategy Status Widget
 * Displays real-time status of all trading strategies
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import {
  Play,
  Pause,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  MoreVertical
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { useStrategyUpdates } from '../../hooks/useStrategyUpdates';
import { cn } from '../lib/utils';

// Type definitions
export interface StrategyStatus {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'error' | 'paused';
  lastExecution: Date;
  nextExecution?: Date;
  dailyPnL: number;
  totalReturn: number;
  error?: string;
  symbol?: string;
  isRunning?: boolean;
}

interface StrategyStatusWidgetProps {
  className?: string;
  onToggleStrategy?: (strategyId: string, enabled: boolean) => void;
  onViewDetails?: (strategyId: string) => void;
}

// Mock data for development
const mockStrategies: StrategyStatus[] = [
  {
    id: '1',
    name: 'Momentum Trading Strategy',
    status: 'active',
    lastExecution: new Date(Date.now() - 60000),
    nextExecution: new Date(Date.now() + 300000),
    dailyPnL: 1250.50,
    totalReturn: 15.3,
    symbol: 'AAPL',
    isRunning: true
  },
  {
    id: '2',
    name: 'Mean Reversion Arbitrage',
    status: 'active',
    lastExecution: new Date(Date.now() - 120000),
    dailyPnL: 890.25,
    totalReturn: 8.7,
    symbol: 'MSFT',
    isRunning: true
  },
  {
    id: '3',
    name: 'Volatility Surface Trading',
    status: 'paused',
    lastExecution: new Date(Date.now() - 300000),
    dailyPnL: -150.75,
    totalReturn: -2.1,
    symbol: 'GOOGL',
    isRunning: false
  },
  {
    id: '4',
    name: 'Statistical Arbitrage',
    status: 'error',
    lastExecution: new Date(Date.now() - 600000),
    dailyPnL: 0,
    totalReturn: 5.2,
    error: 'Connection timeout',
    symbol: 'TSLA',
    isRunning: false
  }
];

// Mini sparkline chart component
const MiniSparkline: React.FC<{ data: number[]; positive: boolean }> = ({ data, positive }) => {
  const chartData = useMemo(() => {
    return data.map((value, index) => ({
      index,
      value
    }));
  }, [data]);

  return (
    <ResponsiveContainer width={60} height={30}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={positive ? '#10b981' : '#ef4444'}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export const StrategyStatusWidget: React.FC<StrategyStatusWidgetProps> = ({
  className,
  onToggleStrategy,
  onViewDetails
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Use the custom hook for strategy updates
  const {
    strategies,
    isConnected,
    connectionStatus,
    lastUpdate,
    error,
    toggleStrategy: handleToggleStrategy
  } = useStrategyUpdates();

  // Get status badge configuration
  const getStatusConfig = (status: StrategyStatus['status']) => {
    switch (status) {
      case 'active':
        return { color: 'bg-green-100 text-green-800', icon: Play, label: 'Active' };
      case 'paused':
        return { color: 'bg-yellow-100 text-yellow-800', icon: Pause, label: 'Paused' };
      case 'error':
        return { color: 'bg-red-100 text-red-800', icon: AlertTriangle, label: 'Error' };
      default:
        return { color: 'bg-gray-100 text-gray-800', icon: Pause, label: 'Inactive' };
    }
  };

  // Format time relative to now
  const formatRelativeTime = (date: Date) => {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Generate mock sparkline data
  const generateSparklineData = (baseValue: number, volatility: number = 0.02) => {
    const data = [baseValue];
    for (let i = 0; i < 10; i++) {
      const change = (Math.random() - 0.5) * volatility * baseValue;
      data.push(data[data.length - 1] + change);
    }
    return data;
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <span>Strategy Status</span>
          <Badge variant="outline" className="text-xs">
            {strategies.filter(s => s.status === 'active').length} / {strategies.length} Active
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {strategies.map((strategy) => {
          const statusConfig = getStatusConfig(strategy.status);
          const StatusIcon = statusConfig.icon;
          const isExpanded = expandedId === strategy.id;
          const sparklineData = generateSparklineData(strategy.totalReturn);

          return (
            <div
              key={strategy.id}
              className="border rounded-lg p-3 space-y-2 hover:bg-gray-50 transition-colors"
            >
              {/* Strategy Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <StatusIcon className="w-5 h-5 text-gray-500" />
                    {strategy.status === 'active' && (
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    )}
                  </div>

                  <div className="flex-1">
                    <h4 className="font-medium text-sm">{strategy.name}</h4>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>{strategy.symbol}</span>
                      <span>•</span>
                      <span>{formatRelativeTime(strategy.lastExecution)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {/* P&L Display */}
                  <div className="text-right">
                    <div className={cn(
                      'text-sm font-medium',
                      strategy.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      ${Math.abs(strategy.dailyPnL).toFixed(2)}
                    </div>
                    <div className={cn(
                      'text-xs',
                      strategy.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {strategy.totalReturn >= 0 ? '+' : ''}{strategy.totalReturn.toFixed(1)}%
                    </div>
                  </div>

                  {/* Mini Sparkline */}
                  <MiniSparkline
                    data={sparklineData}
                    positive={strategy.totalReturn >= 0}
                  />

                  {/* Status Badge */}
                  <Badge className={cn('text-xs', statusConfig.color)}>
                    {statusConfig.label}
                  </Badge>

                  {/* Toggle Switch */}
                  <Switch
                    checked={strategy.isRunning || strategy.status === 'active'}
                    onCheckedChange={(checked) => handleToggleStrategy(strategy.id, checked)}
                    disabled={strategy.status === 'error'}
                  />
                </div>
              </div>

              {/* Error Message */}
              {strategy.status === 'error' && strategy.error && (
                <div className="flex items-center space-x-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                  <AlertTriangle className="w-3 h-3" />
                  <span>{strategy.error}</span>
                </div>
              )}

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t pt-2 space-y-2">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-gray-500">Last Execution:</span>
                      <div>{strategy.lastExecution.toLocaleString()}</div>
                    </div>
                    {strategy.nextExecution && (
                      <div>
                        <span className="text-gray-500">Next Execution:</span>
                        <div>{strategy.nextExecution.toLocaleString()}</div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails?.(strategy.id)}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {/* Summary Stats */}
        <div className="border-t pt-3">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-gray-500">Daily P&L</div>
              <div className={cn(
                'text-sm font-semibold',
                strategies.reduce((sum, s) => sum + s.dailyPnL, 0) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              )}>
                ${strategies.reduce((sum, s) => sum + s.dailyPnL, 0).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Win Rate</div>
              <div className="text-sm font-semibold">
                {((strategies.filter(s => s.dailyPnL > 0).length / strategies.length) * 100).toFixed(0)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Active Now</div>
              <div className="text-sm font-semibold">
                {strategies.filter(s => s.status === 'active').length}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StrategyStatusWidget;