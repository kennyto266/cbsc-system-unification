import React from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Target,
  AlertCircle,
  BarChart3,
  PieChart
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Progress } from '../ui/progress'
import { cn } from '../../lib/utils'

// 模拟性能数据
const performanceData = {
  totalReturn: 24.5,
  monthlyReturn: 2.3,
  sharpeRatio: 1.85,
  maxDrawdown: -8.2,
  winRate: 72.5,
  profitFactor: 1.65,
  avgReturn: 0.8,
  volatility: 15.3
}

const MetricCard: React.FC<{
  title: string
  value: string | number
  change?: number
  icon: React.ElementType
  format?: 'percentage' | 'currency' | 'number'
  trend?: 'up' | 'down' | 'neutral'
}> = ({ title, value, change, icon: Icon, format = 'number', trend }) => {
  const formatValue = (val: string | number) => {
    const num = typeof val === 'string' ? parseFloat(val) : val
    if (format === 'percentage') return `${num.toFixed(1)}%`
    if (format === 'currency') return `$${num.toLocaleString()}`
    return num.toFixed(2)
  }

  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : null

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground">{title}</span>
        </div>
        {change !== undefined && TrendIcon && (
          <div className={cn("flex items-center space-x-1", trendColor)}>
            <TrendIcon className="h-3 w-3" />
            <span className="text-xs">{Math.abs(change).toFixed(1)}%</span>
          </div>
        )}
      </div>
      <div className="text-lg font-bold">{formatValue(value)}</div>
    </div>
  )
}

export const PerformanceMetrics: React.FC = () => {
  const metrics = [
    {
      title: '总收益率',
      value: performanceData.totalReturn,
      change: 2.1,
      icon: TrendingUp,
      format: 'percentage' as const,
      trend: 'up' as const
    },
    {
      title: '月收益率',
      value: performanceData.monthlyReturn,
      change: 0.5,
      icon: Activity,
      format: 'percentage' as const,
      trend: 'up' as const
    },
    {
      title: '夏普比率',
      value: performanceData.sharpeRatio,
      icon: BarChart3,
      format: 'number' as const
    },
    {
      title: '最大回撤',
      value: Math.abs(performanceData.maxDrawdown),
      icon: AlertCircle,
      format: 'percentage' as const,
      trend: 'down' as const
    },
    {
      title: '胜率',
      value: performanceData.winRate,
      icon: Target,
      format: 'percentage' as const
    },
    {
      title: '盈利因子',
      value: performanceData.profitFactor,
      icon: PieChart,
      format: 'number' as const
    }
  ]

  // 风险评级
  const getRiskLevel = () => {
    if (performanceData.maxDrawdown < -5) return { level: '低', color: 'bg-green-100 text-green-800', value: 85 }
    if (performanceData.maxDrawdown < -10) return { level: '中', color: 'bg-yellow-100 text-yellow-800', value: 65 }
    return { level: '高', color: 'bg-red-100 text-red-800', value: 45 }
  }

  const riskLevel = getRiskLevel()

  return (
    <div className="space-y-4 h-full">
      {/* 风险评级 */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold">风险评级</span>
          <span className={cn("px-2 py-1 rounded-full text-xs font-medium", riskLevel.color)}>
            {riskLevel.level}风险
          </span>
        </div>
        <Progress value={riskLevel.value} className="h-2" />
        <p className="text-xs text-muted-foreground mt-2">
          基于最大回撤和波动率计算
        </p>
      </div>

      {/* 性能指标网格 */}
      <div className="grid grid-cols-2 gap-3">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* 月度表现 */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h4 className="text-sm font-semibold mb-3">月度表现</h4>
        <div className="space-y-2">
          {[
            { month: '2024-01', return: 3.2 },
            { month: '2023-12', return: -1.1 },
            { month: '2023-11', return: 2.8 },
            { month: '2023-10', return: 1.5 },
            { month: '2023-09', return: 4.2 }
          ].map((data, index) => (
            <div key={index} className="flex items-center justify-between text-xs">
              <span>{data.month}</span>
              <span className={cn(
                "font-medium",
                data.return >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {data.return >= 0 ? '+' : ''}{data.return}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 详细信息 */}
      <div className="pt-2 border-t border-border">
        <button className="text-xs text-blue-600 hover:underline">
          查看详细报告
        </button>
      </div>
    </div>
  )
}

export default PerformanceMetrics