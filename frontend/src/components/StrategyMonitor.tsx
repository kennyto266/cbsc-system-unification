/**
 * Strategy Monitor Component
 * 策略實時監控組件
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  Target,
  BarChart3,
  Settings,
  Play,
  Pause,
  Square,
  RefreshCw,
  Bell,
  Eye,
  ChevronUp,
  ChevronDown,
  Info,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { format, formatDistanceToNow, subHours, subMinutes } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useEconomicData } from '../hooks/useEconomicData'

export interface StrategyMetrics {
  id: string
  name: string
  status: 'active' | 'paused' | 'stopped' | 'error'
  currentReturn: number
  dailyReturn: number
  totalTrades: number
  winRate: number
  sharpeRatio: number
  maxDrawdown: number
  exposure: number
  riskScore: number
  lastRun?: string
  lastSignal?: {
    type: 'buy' | 'sell' | 'neutral'
    strength: number
    timestamp: string
    description: string
  }
  alerts: StrategyAlert[]
  performance: Array<{
    timestamp: string
    return: number
    trades: number
    exposure: number
  }>
  indicators: Array<{
    name: string
    value: number
    change: number
    status: 'normal' | 'warning' | 'critical'
    threshold: number
  }>
}

export interface StrategyAlert {
  id: string
  strategyId: string
  type: 'warning' | 'error' | 'info' | 'success'
  message: string
  timestamp: string
  acknowledged: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface StrategyMonitorProps {
  strategies: StrategyMetrics[]
  selectedStrategies: string[]
  onStrategySelect?: (strategyIds: string[]) => void
  onAlertAcknowledge?: (alertId: string) => void
  className?: string
  autoRefresh?: boolean
  refreshInterval?: number
  showDetails?: boolean
  compact?: boolean
}

interface TimeRangeOption {
  label: string
  value: number // hours
  key: string
}

const TIME_RANGES: TimeRangeOption[] = [
  { label: '1 Hour', value: 1, key: '1h' },
  { label: '6 Hours', value: 6, key: '6h' },
  { label: '24 Hours', value: 24, key: '24h' },
  { label: '7 Days', value: 168, key: '7d' },
  { label: '30 Days', value: 720, key: '30d' }
]

const ALERT_TYPE_CONFIG = {
  warning: { color: 'text-yellow-600', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200', icon: AlertTriangle },
  error: { color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-200', icon: AlertCircle },
  info: { color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', icon: Info },
  success: { color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200', icon: CheckCircle }
}

const STATUS_CONFIG = {
  active: { color: 'text-green-600', bgColor: 'bg-green-100', icon: Play },
  paused: { color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: Pause },
  stopped: { color: 'text-red-600', bgColor: 'bg-red-100', icon: Square },
  error: { color: 'text-red-600', bgColor: 'bg-red-100', icon: AlertTriangle }
}

export default function StrategyMonitor({
  strategies,
  selectedStrategies,
  onStrategySelect,
  onAlertAcknowledge,
  className = '',
  autoRefresh = true,
  refreshInterval = 5000,
  showDetails = true,
  compact = false
}: StrategyMonitorProps) {
  const [expandedStrategies, setExpandedStrategies] = useState<Set<string>>(new Set())
  const [timeRange, setTimeRange] = useState<TimeRangeOption>(TIME_RANGES[2]) // 24 hours
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(new Date())
  const [showAlerts, setShowAlerts] = useState(true)

  const { economicData } = useEconomicData({
    autoFetch: autoRefresh,
    refreshInterval: autoRefresh ? refreshInterval : 0
  })

  // Filter selected strategies
  const monitoredStrategies = useMemo(() => {
    return strategies.filter(strategy => selectedStrategies.includes(strategy.id))
  }, [strategies, selectedStrategies])

  // Calculate overall metrics
  const overallMetrics = useMemo(() => {
    const activeStrategies = monitoredStrategies.filter(s => s.status === 'active')
    const totalReturn = activeStrategies.reduce((sum, s) => sum + s.currentReturn, 0)
    const totalExposure = activeStrategies.reduce((sum, s) => sum + s.exposure, 0)
    const totalTrades = activeStrategies.reduce((sum, s) => sum + s.totalTrades, 0)
    const avgWinRate = activeStrategies.length > 0
      ? activeStrategies.reduce((sum, s) => sum + s.winRate, 0) / activeStrategies.length
      : 0
    const avgSharpe = activeStrategies.length > 0
      ? activeStrategies.reduce((sum, s) => sum + s.sharpeRatio, 0) / activeStrategies.length
      : 0

    const totalAlerts = activeStrategies.reduce((sum, s) => sum + s.alerts.filter(a => !a.acknowledged).length, 0)
    const criticalAlerts = activeStrategies.reduce((sum, s) =>
      sum + s.alerts.filter(a => !a.acknowledged && a.severity === 'critical').length, 0
    , 0)

    return {
      activeCount: activeStrategies.length,
      totalReturn,
      totalExposure,
      totalTrades,
      avgWinRate,
      avgSharpe,
      totalAlerts,
      criticalAlerts,
      healthScore: calculateHealthScore(activeStrategies)
    }
  }, [monitoredStrategies])

  // Calculate health score
  function calculateHealthScore(strategies: StrategyMetrics[]): number {
    if (strategies.length === 0) return 100

    const scores = strategies.map(strategy => {
      let score = 100

      // Performance score
      if (strategy.currentReturn > 0) {
        score += Math.min(strategy.currentReturn * 10, 50) // Max 50 points
      } else {
        score -= Math.abs(strategy.currentReturn) * 5 // Max -50 points
      }

      // Risk score
      score -= Math.max(0, (strategy.riskScore - 50) * 2) // Reduce score for high risk

      // Alert score
      const criticalAlerts = strategy.alerts.filter(a => a.severity === 'critical').length
      score -= criticalAlerts * 10

      return Math.max(0, Math.min(100, score))
    })

    return scores.reduce((sum, score) => sum + score, 0) / scores.length
  }

  // Filter performance data based on time range
  const getFilteredPerformance = useCallback((strategy: StrategyMetrics) => {
    const cutoffTime = subHours(new Date(), timeRange.value)
    return strategy.performance.filter(p => new Date(p.timestamp) >= cutoffTime)
  }, [timeRange])

  // Format chart data for a strategy
  const getChartData = useCallback((strategy: StrategyMetrics) => {
    const performanceData = getFilteredPerformance(strategy)
    return performanceData.map(point => ({
      time: format(new Date(point.timestamp), 'HH:mm'),
      return: point.return * 100,
      trades: point.trades,
      exposure: point.exposure / 1000 // Convert to thousands
    }))
  }, [getFilteredPerformance])

  // Get status color
  const getStatusColor = (status: string) => {
    const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG]
    return config ? config.color : 'text-gray-600'
  }

  // Get alert type config
  const getAlertConfig = (type: string) => {
    return ALERT_TYPE_CONFIG[type as keyof typeof ALERT_TYPE_CONFIG] || ALERT_TYPE_CONFIG.info
  }

  // Handle manual refresh
  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      // Simulate refresh delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      setLastRefresh(new Date())
    } catch (error) {
      console.error('Error refreshing data:', error)
    } finally {
      setRefreshing(false)
    }
  }, [])

  // Toggle strategy expansion
  const toggleStrategyExpansion = useCallback((strategyId: string) => {
    setExpandedStrategies(prev => {
      const newSet = new Set(prev)
      if (newSet.has(strategyId)) {
        newSet.delete(strategyId)
      } else {
        newSet.add(strategyId)
      }
      return newSet
    })
  }, [])

  // Handle time range change
  const handleTimeRangeChange = useCallback((range: TimeRangeOption) => {
    setTimeRange(range)
  }, [])

  // Handle alert acknowledgment
  const handleAlertAcknowledge = useCallback((alertId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (onAlertAcknowledge) {
      onAlertAcknowledge(alertId)
    }
  }, [onAlertAcknowledge])

  // Calculate color based on value
  const getValueColor = (value: number, isPositiveGood = true) => {
    if (isPositiveGood) {
      return value >= 0 ? 'text-green-600' : 'text-red-600'
    } else {
      return value <= 0 ? 'text-green-600' : 'text-red-600'
    }
  }

  // Get change color
  const getChangeColor = (change: number) => {
    return change >= 0 ? 'text-green-600' : 'text-red-600'
  }

  if (monitoredStrategies.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 text-center ${className}`}>
        <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Strategies Being Monitored</h3>
        <p className="text-gray-500">
          Select strategies from the strategy management page to start monitoring.
        </p>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overall Metrics Summary */}
      {!compact && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Portfolio Overview</h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Clock className="h-4 w-4" />
                <span>Last updated: {formatDistanceToNow(lastRefresh, { addSuffix: true })}</span>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Time Range Selector */}
          <div className="flex items-center space-x-2 mb-6">
            <span className="text-sm text-gray-500">Time Range:</span>
            {TIME_RANGES.map((range) => (
              <button
                key={range.key}
                onClick={() => handleTimeRangeChange(range)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                  timeRange.key === range.key
                    ? 'bg-blue-100 text-blue-700 border-blue-200'
                    : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Active Strategies</span>
                <Play className="h-4 w-4 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{overallMetrics.activeCount}</div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Total Return</span>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </div>
              <div className={`text-2xl font-bold ${getValueColor(overallMetrics.totalReturn)}`}>
                {overallMetrics.totalReturn >= 0 ? '+' : ''}{overallMetrics.totalReturn.toFixed(2)}%
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Total Exposure</span>
                <BarChart3 className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                ${(overallMetrics.totalExposure / 1000000).toFixed(2)}M
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Win Rate</span>
                <Target className="h-4 w-4 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {(overallMetrics.avgWinRate * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Sharpe Ratio</span>
                <Zap className="h-4 w-4 text-orange-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {overallMetrics.avgSharpe.toFixed(2)}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Health Score</span>
                <Activity className="h-4 w-4 text-teal-600" />
              </div>
              <div className={`text-2xl font-bold ${
                overallMetrics.healthScore >= 80 ? 'text-green-600' :
                overallMetrics.healthScore >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {overallMetrics.healthScore.toFixed(0)}
              </div>
            </div>
          </div>

          {/* Alert Summary */}
          {overallMetrics.criticalAlerts > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-red-800">Critical Alerts</h4>
                  <p className="text-sm text-red-700">
                    {overallMetrics.criticalAlerts} critical alerts require immediate attention
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Strategy Monitoring Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {monitoredStrategies.map((strategy) => {
          const StatusIcon = STATUS_CONFIG[strategy.status].icon
          const statusConfig = STATUS_CONFIG[strategy.status]
          const isExpanded = expandedStrategies.has(strategy.id)
          const chartData = getChartData(strategy)

          return (
            <div key={strategy.id} className="bg-white rounded-lg shadow">
              {/* Strategy Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${statusConfig.bgColor}`}>
                      <StatusIcon className={`h-5 w-5 ${statusConfig.color}`} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{strategy.name}</h4>
                      <p className="text-sm text-gray-500">
                        {strategy.status.charAt(0).toUpperCase() + strategy.status.slice(1)} •
                        {formatDistanceToNow(new Date(strategy.lastRun || new Date()), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleStrategyExpansion(strategy.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick Metrics */}
              <div className="p-4 grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-sm text-gray-500">Return</div>
                  <div className={`font-semibold ${getValueColor(strategy.currentReturn)}`}>
                    {strategy.currentReturn >= 0 ? '+' : ''}{strategy.currentReturn.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Trades</div>
                  <div className="font-semibold text-gray-900">{strategy.totalTrades}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Win Rate</div>
                  <div className={`font-semibold ${strategy.winRate >= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                    {(strategy.winRate * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Risk Score</div>
                  <div className={`font-semibold ${
                    strategy.riskScore <= 30 ? 'text-green-600' :
                    strategy.riskScore <= 60 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {strategy.riskScore}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && showDetails && (
                <div className="border-t border-gray-200">
                  {/* Last Signal */}
                  {strategy.lastSignal && (
                    <div className="p-4 border-b border-gray-100">
                      <h5 className="text-sm font-semibold text-gray-900 mb-2">Last Signal</h5>
                      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-lg ${
                        strategy.lastSignal.type === 'buy' ? 'bg-green-50 text-green-700' :
                        strategy.lastSignal.type === 'sell' ? 'bg-red-50 text-red-700' :
                        'bg-gray-50 text-gray-700'
                      }`}>
                        {strategy.lastSignal.type.toUpperCase()} • {strategy.lastSignal.strength}% Strength
                      </div>
                      <p className="text-sm text-gray-600 mt-2">{strategy.lastSignal.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDistanceToNow(new Date(strategy.lastSignal.timestamp), { addSuffix: true })}
                      </p>
                    </div>
                  )}

                  {/* Performance Chart */}
                  <div className="p-4 border-b border-gray-100">
                    <h5 className="text-sm font-semibold text-gray-900 mb-4">Performance ({timeRange.label})</h5>
                    {chartData.length > 0 ? (
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="time" />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip />
                            <Area
                              yAxisId="left"
                              type="monotone"
                              dataKey="return"
                              stroke="#3b82f6"
                              fill="#3b82f6"
                              fillOpacity={0.2}
                            />
                            <Line
                              yAxisId="right"
                              type="monotone"
                              dataKey="trades"
                              stroke="#8b5cf6"
                              strokeWidth={2}
                              dot={false}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div className="h-64 flex items-center justify-center text-gray-500">
                        <p>No performance data available for selected time range</p>
                      </div>
                    )}
                  </div>

                  {/* Indicators Status */}
                  {strategy.indicators.length > 0 && (
                    <div className="p-4">
                      <h5 className="text-sm font-semibold text-gray-900 mb-4">Indicators Status</h5>
                      <div className="space-y-3">
                        {strategy.indicators.map((indicator, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${
                                indicator.status === 'normal' ? 'bg-green-500' :
                                indicator.status === 'warning' ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`} />
                              <span className="text-sm font-medium text-gray-700">{indicator.name}</span>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-900">{indicator.value.toFixed(2)}</div>
                              <div className={`text-xs ${getChangeColor(indicator.change)}`}>
                                {indicator.change >= 0 ? '+' : ''}{indicator.change.toFixed(2)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Alerts */}
                  {strategy.alerts.length > 0 && (
                    <div className="p-4">
                      <h5 className="text-sm font-semibold text-gray-900 mb-4">Recent Alerts</h5>
                      <div className="space-y-2">
                        {strategy.alerts.slice(0, 3).map((alert) => {
                          const alertConfig = getAlertConfig(alert.type)
                          const AlertIcon = alertConfig.icon
                          return (
                            <div
                              key={alert.id}
                              className={`flex items-start space-x-3 p-3 rounded-lg border ${alertConfig.borderColor} ${
                                alert.acknowledged ? 'opacity-50' : ''
                              }`}
                            >
                              <AlertIcon className={`h-5 w-5 mt-0.5 ${alertConfig.color} flex-shrink-0`} />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                                <div className="flex items-center justify-between mt-1">
                                  <span className="text-xs text-gray-500">
                                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                                  </span>
                                  {!alert.acknowledged && (
                                    <button
                                      onClick={(e) => handleAlertAcknowledge(alert.id, e)}
                                      className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                                    >
                                      Acknowledge
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Alerts Panel */}
      {showAlerts && overallMetrics.totalAlerts > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-yellow-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Recent Alerts ({overallMetrics.totalAlerts})
              </h3>
            </div>
            <button
              onClick={() => setShowAlerts(!showAlerts)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showAlerts ? 'Hide' : 'Show'}
            </button>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {monitoredStrategies
              .flatMap(strategy => strategy.alerts.filter(alert => !alert.acknowledged))
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
              .slice(0, 10)
              .map((alert) => {
                const alertConfig = getAlertConfig(alert.type)
                const AlertIcon = alertConfig.icon
                const strategy = strategies.find(s => s.id === alert.strategyId)

                return (
                  <div
                    key={alert.id}
                    className={`flex items-start space-x-3 p-4 rounded-lg border ${alertConfig.borderColor}`}
                  >
                    <AlertIcon className={`h-5 w-5 mt-0.5 ${alertConfig.color} flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-900">{strategy?.name}</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${alertConfig.bgColor} ${alertConfig.color}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{alert.message}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                        </span>
                        <button
                          onClick={(e) => handleAlertAcknowledge(alert.id, e)}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                        >
                          Acknowledge
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}