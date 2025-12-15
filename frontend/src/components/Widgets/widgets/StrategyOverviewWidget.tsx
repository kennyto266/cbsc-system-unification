import React, { useEffect, useState } from 'react';
import { Widget } from '../../../types/widget';
import { Badge } from '../../ui/badge';
import { Progress } from '../../ui/progress';
import { Card, CardContent } from '../../ui/card';

interface StrategyOverviewWidgetProps {
  widget: Widget;
}

export function StrategyOverviewWidget({ widget }: StrategyOverviewWidgetProps) {
  const [strategies, setStrategies] = useState([
    {
      id: '1',
      name: 'CBSC多因子策略',
      status: 'active',
      performance: 12.5,
      risk: 'medium',
      trades: 156,
      winRate: 68.5,
    },
    {
      id: '2',
      name: '動量突破策略',
      status: 'active',
      performance: 8.3,
      risk: 'high',
      trades: 89,
      winRate: 72.1,
    },
    {
      id: '3',
      name: '均值回歸策略',
      status: 'paused',
      performance: -2.1,
      risk: 'low',
      trades: 234,
      winRate: 61.2,
    },
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStrategies(prev =>
        prev.map(s => ({
          ...s,
          performance: s.performance + (Math.random() - 0.5) * 0.1,
        }))
      );
    }, (widget.config?.refreshInterval || 5) * 1000);

    return () => clearInterval(interval);
  }, [widget.config?.refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'paused':
        return 'bg-yellow-500';
      case 'stopped':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-3">
      {strategies.map(strategy => (
        <Card key={strategy.id} className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-sm">{strategy.name}</h4>
            <Badge
              variant="secondary"
              className={`${getStatusColor(strategy.status)} text-white text-xs`}
            >
              {strategy.status === 'active' ? '運行中' : '已暫停'}
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">總收益率：</span>
              <span className={`font-semibold ${
                strategy.performance > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {strategy.performance.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">交易次數：</span>
              <span className="font-medium">{strategy.trades}</span>
            </div>
            <div>
              <span className="text-muted-foreground">勝率：</span>
              <span className="font-medium">{strategy.winRate}%</span>
            </div>
            <div>
              <span className="text-muted-foreground">風險等級：</span>
              <span className={`font-medium ${getRiskColor(strategy.risk)}`}>
                {strategy.risk === 'low' ? '低' : strategy.risk === 'medium' ? '中' : '高'}
              </span>
            </div>
          </div>

          <div className="mt-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>日內表現</span>
              <span>+{(Math.random() * 2).toFixed(2)}%</span>
            </div>
            <Progress
              value={Math.random() * 100}
              className="h-1"
            />
          </div>
        </Card>
      ))}
    </div>
  );
}