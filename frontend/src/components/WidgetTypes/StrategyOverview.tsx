import React from 'react'
import { BarChart3, TrendingUp, Activity, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { cn } from '@/lib/utils'

// 模拟数据
const mockStrategies = [
  { name: 'RSI均值回归', status: 'running', profit: 5.2, trades: 156, winRate: 68 },
  { name: 'MACD趋势跟踪', status: 'stopped', profit: -1.3, trades: 89, winRate: 52 },
  { name: '布林带突破', status: 'running', profit: 8.7, trades: 234, winRate: 72 },
  { name: '多因子组合', status: 'running', profit: 12.4, trades: 445, winRate: 75 },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'running':
      return <Badge variant="default" className="bg-green-100 text-green-800">运行中</Badge>
    case 'stopped':
      return <Badge variant="secondary">已停止</Badge>
    case 'paused':
      return <Badge variant="outline">已暂停</Badge>
    default:
      return <Badge variant="outline">未知</Badge>
  }
}

const getProfitColor = (profit: number) => {
  if (profit > 0) return 'text-green-600'
  if (profit < 0) return 'text-red-600'
  return 'text-gray-600'
}

export const StrategyOverview: React.FC = () => {
  const totalStrategies = mockStrategies.length
  const runningStrategies = mockStrategies.filter(s => s.status === 'running').length
  const totalProfit = mockStrategies.reduce((sum, s) => sum + s.profit, 0)
  const avgWinRate = mockStrategies.reduce((sum, s) => sum + s.winRate, 0) / mockStrategies.length

  return (
    <div className="space-y-4 h-full">
      {/* 总览卡片 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <span className="text-2xl font-bold text-blue-600">{totalStrategies}</span>
          </div>
          <p className="text-xs text-blue-600 mt-1">总策略数</p>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <Activity className="h-5 w-5 text-green-600" />
            <span className="text-2xl font-bold text-green-600">{runningStrategies}</span>
          </div>
          <p className="text-xs text-green-600 mt-1">运行中</p>
        </div>
      </div>

      {/* 性能指标 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-muted-foreground">总收益率</p>
            <p className={cn("text-lg font-semibold", getProfitColor(totalProfit))}>
              {totalProfit > 0 ? '+' : ''}{totalProfit.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">平均胜率</p>
            <p className="text-lg font-semibold">{avgWinRate.toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">总交易数</p>
            <p className="text-lg font-semibold">
              {mockStrategies.reduce((sum, s) => sum + s.trades, 0)}
            </p>
          </div>
        </div>
      </div>

      {/* 策略列表 */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-muted-foreground">策略列表</h4>
        {mockStrategies.map((strategy, index) => (
          <div
            key={index}
            className={cn(
              "bg-background border border-border rounded-lg p-3 hover:bg-accent/50 transition-colors",
              "cursor-pointer"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">{strategy.name}</span>
              {getStatusBadge(strategy.status)}
            </div>

            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>收益: <span className={getProfitColor(strategy.profit)}>
                {strategy.profit > 0 ? '+' : ''}{strategy.profit}%
              </span></span>
              <span>交易: {strategy.trades}</span>
              <span>胜率: {strategy.winRate}%</span>
            </div>

            <div className="mt-2">
              <Progress
                value={strategy.winRate}
                className="h-1"
                indicatorColor={
                  strategy.winRate >= 70
                    ? 'bg-green-500'
                    : strategy.winRate >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }
              />
            </div>
          </div>
        ))}
      </div>

      {/* 快捷操作 */}
      <div className="pt-2 border-t border-border">
        <div className="flex justify-between text-xs">
          <button className="text-blue-600 hover:underline">
            查看所有策略
          </button>
          <button className="text-blue-600 hover:underline">
            创建新策略
          </button>
        </div>
      </div>
    </div>
  )
}

export default StrategyOverview