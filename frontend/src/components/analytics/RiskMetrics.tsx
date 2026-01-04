/**
 * RiskMetrics - Risk Metrics Display Component
 * Migrated from unified-dashboard analytics
 * Adapted to use frontend's existing components (Card, Grid, MetricCard, Progress)
 *
 * Features:
 * - Volatility analysis
 * - Market risk metrics (Beta, Alpha)
 * - Value at Risk (VaR, CVaR)
 * - Distribution characteristics (Skewness, Kurtosis)
 */

import React from 'react'
import { Card } from '../ui/Card'
import { Grid, GridItem } from '../ui-helpers/Grid'
import { MetricCard } from '../ui-helpers/MetricCard'
import { Progress } from '../ui/progress'
import {
  AlertTriangle,
  Shield,
  LineChart,
  BarChart3,
  Info,
  TrendingUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface RiskMetricsProps {
  metrics: {
    volatility: number
    beta: number
    alpha: number
    var95: number
    cvar95: number
    skewness: number
    kurtosis: number
    informationRatio: number
  }
  className?: string
}

const RiskMetrics: React.FC<RiskMetricsProps> = ({
  metrics,
  className
}) => {
  const getRiskColor = (value: number, type: string) => {
    switch (type) {
      case 'volatility':
        return value < 15 ? 'text-green-600 dark:text-green-400' :
               value < 25 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      case 'beta':
        return Math.abs(value - 1) < 0.2 ? 'text-green-600 dark:text-green-400' :
               Math.abs(value - 1) < 0.5 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      case 'alpha':
        return value > 5 ? 'text-green-600 dark:text-green-400' :
               value > 0 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      case 'var':
        return value > -2 ? 'text-green-600 dark:text-green-400' :
               value > -5 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      case 'skewness':
        return value > 0.5 ? 'text-green-600 dark:text-green-400' :
               value < -0.5 ? 'text-red-600 dark:text-red-400' :
               'text-yellow-600 dark:text-yellow-400'
      case 'kurtosis':
        return Math.abs(value - 3) < 1 ? 'text-green-600 dark:text-green-400' :
               Math.abs(value - 3) < 2 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      case 'infoRatio':
        return value > 0.5 ? 'text-green-600 dark:text-green-400' :
               value > 0 ? 'text-yellow-600 dark:text-yellow-400' :
               'text-red-600 dark:text-red-400'
      default:
        return 'text-blue-600 dark:text-blue-400'
    }
  }

  const getProgressVariant = (value: number, type: string): 'success' | 'warning' | 'error' | 'default' => {
    if (type === 'volatility') {
      return value < 15 ? 'success' : value < 25 ? 'warning' : 'error'
    }
    return 'default'
  }

  const getSkewnessLabel = (value: number) => {
    return value > 0.5 ? 'Right Skewed / 右偏' :
           value < -0.5 ? 'Left Skewed / 左偏' :
           'Symmetric / 對稱'
  }

  const getKurtosisLabel = (value: number) => {
    const deviation = Math.abs(value - 3)
    return deviation < 1 ? 'Normal / 正常' :
           deviation < 2 ? 'Slight Abnormal / 輕微異常' :
           'Significant Abnormal / 顯著異常'
  }

  return (
    <Card className={cn('w-full', className)}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Risk Metrics
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            風險指標分析
          </p>
        </div>

        {/* Volatility Risk */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Volatility Risk / 波動率風險
          </h4>
          <Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
            {/* Volatility */}
            <Card className="p-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <LineChart className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Volatility / 波動率
                  </span>
                </div>
                <Progress
                  value={metrics.volatility}
                  max={50}
                  showValue={false}
                  variant={getProgressVariant(metrics.volatility, 'volatility')}
                  size="lg"
                />
                <div className="flex justify-between items-center">
                  <span className={cn(
                    'text-xs px-2 py-1 rounded-full',
                    metrics.volatility < 15 ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' :
                    metrics.volatility < 25 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                  )}>
                    {metrics.volatility < 15 ? 'Low Volatility / 低波動' :
                     metrics.volatility < 25 ? 'Medium Volatility / 中等波動' :
                     'High Volatility / 高波動'}
                  </span>
                  <span className={cn(
                    'text-lg font-bold',
                    getRiskColor(metrics.volatility, 'volatility')
                  )}>
                    {metrics.volatility.toFixed(1)}%
                  </span>
                </div>
              </div>
            </Card>

            {/* Beta */}
            <MetricCard
              title="Beta Coefficient / Beta係數"
              value={metrics.beta}
              precision={2}
              icon={<BarChart3 className="w-5 h-5" />}
              variant="compact"
            />

            {/* Alpha */}
            <MetricCard
              title="Alpha Return / Alpha收益"
              value={metrics.alpha}
              format="percentage"
              precision={2}
              icon={<TrendingUp className="w-5 h-5" />}
              variant="compact"
            />
          </Grid>
        </div>

        {/* Value at Risk */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Value at Risk / 風險價值
          </h4>
          <Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
            <MetricCard
              title="VaR (95%) / 風險價值"
              value={metrics.var95}
              format="percentage"
              precision={2}
              icon={<AlertTriangle className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="CVaR (95%) / 條件風險價值"
              value={metrics.cvar95}
              format="percentage"
              precision={2}
              icon={<Shield className="w-5 h-5" />}
              variant="compact"
            />
            <MetricCard
              title="Information Ratio / 信息比率"
              value={metrics.informationRatio}
              precision={2}
              icon={<BarChart3 className="w-5 h-5" />}
              variant="compact"
            />
          </Grid>
        </div>

        {/* Distribution Characteristics */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Distribution Characteristics / 收益分佈特徵
          </h4>
          <Card className="p-4">
            <div className="space-y-4">
              {/* Skewness */}
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Skewness / 偏度
                  </span>
                  <Info className="w-4 h-4 text-gray-400" />
                </div>
                <div className="flex items-center gap-3">
                  <span className={cn(
                    'text-lg font-bold',
                    getRiskColor(metrics.skewness, 'skewness')
                  )}>
                    {metrics.skewness.toFixed(3)}
                  </span>
                  <span className={cn(
                    'text-xs px-2 py-1 rounded-full',
                    metrics.skewness > 0.5 ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' :
                    metrics.skewness < -0.5 ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400'
                  )}>
                    {getSkewnessLabel(metrics.skewness)}
                  </span>
                </div>
              </div>

              {/* Kurtosis */}
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Kurtosis / 峰度
                  </span>
                  <Info className="w-4 h-4 text-gray-400" />
                </div>
                <div className="flex items-center gap-3">
                  <span className={cn(
                    'text-lg font-bold',
                    getRiskColor(metrics.kurtosis, 'kurtosis')
                  )}>
                    {metrics.kurtosis.toFixed(3)}
                  </span>
                  <span className={cn(
                    'text-xs px-2 py-1 rounded-full',
                    Math.abs(metrics.kurtosis - 3) < 1 ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' :
                    Math.abs(metrics.kurtosis - 3) < 2 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                  )}>
                    {getKurtosisLabel(metrics.kurtosis)}
                  </span>
                </div>
              </div>

              {/* Explanation */}
              <div className="pt-3 mt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  <strong>Skewness:</strong> Measures asymmetry of return distribution. Positive = right-skewed, Negative = left-skewed.<br/>
                  <strong>Kurtosis:</strong> Measures tail thickness. Kurtosis of 3 indicates normal distribution. Higher values mean fatter tails.
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  偏度衡量收益分佈的不對稱性，正值為右偏，負值為左偏。峰度衡量尾部厚度，3表示正態分佈，大於3表示厚尾。
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Card>
  )
}

export default RiskMetrics
