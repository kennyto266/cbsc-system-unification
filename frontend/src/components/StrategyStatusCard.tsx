import React from 'react'
import { Card } from './ui/Card'
import { Activity, TrendingUp, Target, AlertTriangle } from 'lucide-react'

interface Strategy {
  id: string
  name: string
  status: string
  performance?: {
    totalReturn: number
    winRate: number
    sharpeRatio: number
    maxDrawdown: number
    totalTrades: number
    profitableTrades: number
  }
  lastRun?: string
  nextRun?: string
}

interface StrategyStatusCardProps {
  strategy: Strategy
}

export default function StrategyStatusCard({ strategy }: StrategyStatusCardProps) {
  const statusColor = {
    active: 'text-green-600',
    paused: 'text-yellow-600',
    stopped: 'text-red-600',
    error: 'text-red-600',
    testing: 'text-blue-600'
  }[strategy.status] || 'text-gray-600'

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Strategy Status
      </h3>

      <div className="space-y-4">
        {/* Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">Status</span>
          <span className={`text-sm font-medium ${statusColor}`}>
            {strategy.status.charAt(0).toUpperCase() + strategy.status.slice(1)}
          </span>
        </div>

        {/* Performance Metrics */}
        {strategy.performance && (
          <>
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Performance
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center">
                  <Activity className="h-4 w-4 text-blue-500 mr-2" />
                  <div>
                    <div className="text-xs text-gray-500">Total Return</div>
                    <div className={`text-sm font-semibold ${
                      strategy.performance.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {strategy.performance.totalReturn >= 0 ? '+' : ''}{strategy.performance.totalReturn.toFixed(2)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center">
                  <Target className="h-4 w-4 text-purple-500 mr-2" />
                  <div>
                    <div className="text-xs text-gray-500">Win Rate</div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">
                      {(strategy.performance.winRate * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center">
                  <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                  <div>
                    <div className="text-xs text-gray-500">Sharpe Ratio</div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">
                      {strategy.performance.sharpeRatio.toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center">
                  <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
                  <div>
                    <div className="text-xs text-gray-500">Max Drawdown</div>
                    <div className="text-sm font-semibold text-red-600">
                      {strategy.performance.maxDrawdown.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Total Trades</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {strategy.performance.totalTrades}
                </span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-600 dark:text-gray-400">Profitable</span>
                <span className="font-medium text-green-600">
                  {strategy.performance.profitableTrades}
                </span>
              </div>
            </div>
          </>
        )}

        {/* Timestamps */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
          {strategy.lastRun && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Last Run</span>
              <span className="text-gray-900 dark:text-white">
                {new Date(strategy.lastRun).toLocaleString()}
              </span>
            </div>
          )}
          {strategy.nextRun && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Next Run</span>
              <span className="text-gray-900 dark:text-white">
                {new Date(strategy.nextRun).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
