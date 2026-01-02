/**
 * PerformanceMetrics - Performance Metrics Display Component
 * Migrated from unified-dashboard analytics
 * Adapted to use frontend's existing components (Card, Grid, MetricCard, Progress)
 *
 * Features:
 * - Return metrics (total, annualized, max drawdown)
 * - Risk-adjusted ratios (Sharpe, Sortino, Calmar)
 * - Trading metrics (win rate, profit factor)
 * - Average win/loss analysis
 */

import React from 'react'
import { Card } from '../ui/Card'
import { Grid, GridItem } from '../ui-helpers/Grid'
import { MetricCard } from '../ui-helpers/MetricCard'
import { Progress } from '../ui/progress'
import {
  TrendingUp,
  Trophy,
  Percent,
  LineChart,
  Info,
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface PerformanceMetricsProps {
  metrics: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    sortinoRatio: number
    maxDrawdown: number
    calmarRatio: number
    winRate: number
    profitFactor: number
    avgWin: number
    avgLoss: number
  }
  className?: string
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  metrics,
  className
}) => {
  const getPerformanceColor = (value: number, type: string) => {
    if (type === 'drawdown') {
      return value > -10 ? 'text-green-600 dark:text-green-400' :
             value > -20 ? 'text-yellow-600 dark:text-yellow-400' :
             'text-red-600 dark:text-red-400'
    }
    if (type === 'ratio') {
      return value > 1.5 ? 'text-green-600 dark:text-green-400' :
             value > 1 ? 'text-yellow-600 dark:text-yellow-400' :
             'text-red-600 dark:text-red-400'
    }
    return value > 0 ? 'text-green-600 dark:text-green-400' :
           'text-red-600 dark:text-red-400'
  }

  const getProgressVariant = (value: number, type: string): 'success' | 'warning' | 'error' | 'default' => {
    if (type === 'drawdown') {
      return value > -10 ? 'success' : value > -20 ? 'warning' : 'error'
    }
    if (type === 'winrate') {
      return value > 60 ? 'success' : value > 40 ? 'warning' : 'error'
    }
    return 'default'
  }

  return (
    <Card className={cn('w-full', className)}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Performance Metrics
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            績效指標分析
          </p>
        </div>

        {/* Return Metrics */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Return Metrics / 收益指標
          </h4>
          <Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
            <MetricCard
              title="Total Return / 總收益率"
              value={metrics.totalReturn}
              format="percentage"
              precision={2}
              icon={<TrendingUp className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="Annualized Return / 年化收益率"
              value={metrics.annualizedReturn}
              format="percentage"
              precision={2}
              icon={<LineChart className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="Max Drawdown / 最大回撤"
              value={metrics.maxDrawdown}
              format="percentage"
              precision={2}
              icon={<TrendingUp className="w-5 h-5" />}
              variant="compact"
              trend={metrics.maxDrawdown}
            />
          </Grid>
        </div>

        {/* Risk-Adjusted Ratios */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Risk-Adjusted Ratios / 風險調整比率
          </h4>
          <Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
            <MetricCard
              title="Sharpe Ratio / 夏普比率"
              value={metrics.sharpeRatio}
              precision={2}
              icon={<Trophy className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="Sortino Ratio / 索提諾比率"
              value={metrics.sortinoRatio}
              precision={2}
              icon={<Trophy className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="Calmar Ratio / 卡瑪比率"
              value={metrics.calmarRatio}
              precision={2}
              icon={<Trophy className="w-5 h-5" />}
              variant="compact"
            />
          </Grid>
        </div>

        {/* Trading Metrics */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Trading Metrics / 交易指標
          </h4>
          <Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
            {/* Win Rate */}
            <Card className="p-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Percent className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Win Rate / 勝率
                  </span>
                </div>
                <Progress
                  value={metrics.winRate}
                  max={100}
                  showValue={false}
                  variant={getProgressVariant(metrics.winRate, 'winrate')}
                  size="lg"
                />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Profitable trades
                  </span>
                  <span className={cn(
                    'text-lg font-bold',
                    getPerformanceColor(metrics.winRate, 'winrate')
                  )}>
                    {metrics.winRate.toFixed(1)}%
                  </span>
                </div>
              </div>
            </Card>

            {/* Profit Factor */}
            <MetricCard
              title="Profit Factor / 盈利因子"
              value={metrics.profitFactor}
              precision={2}
              icon={<Percent className="w-5 h-5" />}
              variant="compact"
            />

            {/* Average Win/Loss */}
            <Card className="p-4">
              <div className="space-y-3">
                <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Avg Win/Loss / 平均盈虧
                </h5>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Avg Win / 平均盈利
                    </span>
                    <span className="text-sm font-bold text-green-600 dark:text-green-400">
                      +{metrics.avgWin.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Avg Loss / 平均虧損
                    </span>
                    <span className="text-sm font-bold text-red-600 dark:text-red-400">
                      {metrics.avgLoss.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Ratio / 盈虧比
                    </span>
                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                      {Math.abs(metrics.avgWin / metrics.avgLoss).toFixed(2)}:1
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </Grid>
        </div>
      </div>
    </Card>
  )
}

export default PerformanceMetrics
