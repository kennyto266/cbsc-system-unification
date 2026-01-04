import React from 'react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import {
  Play,
  Pause,
  Square,
  Eye,
  Edit,
  Trash2,
  Copy,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'
import { format } from 'date-fns'

interface NonPriceStrategy {
  id: string
  name: string
  type: string
  status: 'active' | 'paused' | 'stopped' | 'error' | 'testing'
  description: string
  parameters: Record<string, any>
  indicators: string[]
  createdAt: string
  updatedAt: string
  lastRun?: string
  nextRun?: string
  performance?: {
    totalReturn: number
    winRate: number
    sharpeRatio: number
    maxDrawdown: number
    totalTrades: number
    profitableTrades: number
  }
  error?: string
  configuration?: {
    autoRestart: boolean
    riskLimits: {
      maxPositionSize: number
      maxDailyLoss: number
      maxDrawdown: number
    }
    executionSettings: {
      slippageTolerance: number
      executionDelay: number
      retryAttempts: number
    }
  }
}

interface NonPriceStrategyCardProps {
  strategy: NonPriceStrategy
  onStart: () => void
  onStop: () => void
  onPause: () => void
  onResume: () => void
  onEdit: () => void
  onDelete: () => void
  onDuplicate: () => void
  onViewHistory: () => void
  actionLoading: boolean
}

const STRATEGY_TYPE_CONFIG = {
  'interest_rate_arbitrage': {
    label: 'Interest Rate Arbitrage',
    icon: TrendingUp,
    color: 'blue'
  },
  'economic_data_correlation': {
    label: 'Economic Data Correlation',
    icon: Activity,
    color: 'green'
  },
  'multi_indicator_momentum': {
    label: 'Multi-Indicator Momentum',
    icon: Target,
    color: 'purple'
  },
  'volatility_based': {
    label: 'Volatility Based',
    icon: AlertCircle,
    color: 'orange'
  },
  'seasonal_patterns': {
    label: 'Seasonal Patterns',
    icon: Clock,
    color: 'pink'
  }
}

const STATUS_CONFIG = {
  active: {
    label: 'Active',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200',
    icon: Play
  },
  paused: {
    label: 'Paused',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200',
    icon: Pause
  },
  stopped: {
    label: 'Stopped',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200',
    icon: Square
  },
  error: {
    label: 'Error',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200',
    icon: XCircle
  },
  testing: {
    label: 'Testing',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200',
    icon: Clock
  }
}

export default function NonPriceStrategyCard({
  strategy,
  onStart,
  onStop,
  onPause,
  onResume,
  onEdit,
  onDelete,
  onDuplicate,
  onViewHistory,
  actionLoading
}: NonPriceStrategyCardProps) {
  const typeConfig = STRATEGY_TYPE_CONFIG[strategy.type as keyof typeof STRATEGY_TYPE_CONFIG] || STRATEGY_TYPE_CONFIG.interest_rate_arbitrage
  const statusConfig = STATUS_CONFIG[strategy.status]
  const TypeIcon = typeConfig.icon
  const StatusIcon = statusConfig.icon

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <div className={`p-2 ${typeConfig.color}-100 rounded-lg mr-3`}>
              <TypeIcon className={`h-5 w-5 text-${typeConfig.color}-600`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {strategy.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {typeConfig.label}
              </p>
            </div>
          </div>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color} ${statusConfig.borderColor}`}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusConfig.label}
          </span>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {strategy.description}
        </p>

        {/* Performance */}
        {strategy.performance && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Return</div>
              <div className={`text-sm font-semibold ${
                strategy.performance.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {strategy.performance.totalReturn >= 0 ? '+' : ''}{strategy.performance.totalReturn.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Win Rate</div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">
                {(strategy.performance.winRate * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Sharpe Ratio</div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">
                {strategy.performance.sharpeRatio.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Max Drawdown</div>
              <div className="text-sm font-semibold text-red-600">
                {strategy.performance.maxDrawdown.toFixed(2)}%
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {strategy.error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start">
              <XCircle className="h-4 w-4 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800 dark:text-red-200">{strategy.error}</p>
            </div>
          </div>
        )}

        {/* Indicators */}
        {strategy.indicators && strategy.indicators.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Indicators</div>
            <div className="flex flex-wrap gap-1">
              {strategy.indicators.slice(0, 3).map((indicator, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded"
                >
                  {indicator}
                </span>
              ))}
              {strategy.indicators.length > 3 && (
                <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded">
                  +{strategy.indicators.length - 3}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-4">
          <span>Updated: {format(new Date(strategy.updatedAt), 'yyyy-MM-dd HH:mm')}</span>
          {strategy.lastRun && (
            <span>Last run: {format(new Date(strategy.lastRun), 'yyyy-MM-dd HH:mm')}</span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            {strategy.status === 'active' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onPause}
                  disabled={actionLoading}
                  title="Pause"
                >
                  <Pause className="h-3 w-3" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onStop}
                  disabled={actionLoading}
                  title="Stop"
                >
                  <Square className="h-3 w-3" />
                </Button>
              </>
            )}
            {(strategy.status === 'paused' || strategy.status === 'stopped' || strategy.status === 'error') && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onStart}
                  disabled={actionLoading}
                  title="Start"
                >
                  <Play className="h-3 w-3" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onEdit}
                  disabled={actionLoading}
                  title="Edit"
                >
                  <Edit className="h-3 w-3" />
                </Button>
              </>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={onViewHistory}
              disabled={actionLoading}
              title="View History"
            >
              <Eye className="h-3 w-3" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onDuplicate}
              disabled={actionLoading}
              title="Duplicate"
            >
              <Copy className="h-3 w-3" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              disabled={actionLoading}
              title="Delete"
            >
              <Trash2 className="h-3 w-3 text-red-600" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
