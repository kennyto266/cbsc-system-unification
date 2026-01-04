/**
 * Economic Signal Markers Component
 * 經濟信號標記組件
 */

import React, { useState, useMemo, useCallback } from 'react'
import { AlertTriangle, TrendingUp, TrendingDown, Minus, Info, X, Clock, Target, Activity } from 'lucide-react'
import { format } from 'date-fns'

export interface EconomicSignal {
  id: string
  date: string
  indicator: string
  type: 'buy' | 'sell' | 'neutral' | 'warning' | 'opportunity'
  strength: number // 0-1
  confidence: number // 0-1
  value: number
  previousValue?: number
  threshold?: number
  description: string
  category: 'interest_rate' | 'economic_growth' | 'employment' | 'tourism' | 'inflation'
  metadata?: Record<string, any>
  createdAt: string
}

interface EconomicSignalMarkersProps {
  signals: EconomicSignal[]
  onSignalClick?: (signal: EconomicSignal) => void
  onSignalDismiss?: (signalId: string) => void
  showFilters?: boolean
  className?: string
  maxVisible?: number
  autoRefresh?: boolean
  refreshInterval?: number
}

interface SignalCategory {
  key: string
  label: string
  icon: React.ComponentType<any>
  color: string
  bgColor: string
}

interface SignalType {
  key: string
  label: string
  icon: React.ComponentType<any>
  color: string
  bgColor: string
  borderColor: string
}

const SIGNAL_CATEGORIES: SignalCategory[] = [
  {
    key: 'interest_rate',
    label: 'Interest Rate',
    icon: Activity,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100'
  },
  {
    key: 'economic_growth',
    label: 'Economic Growth',
    icon: TrendingUp,
    color: 'text-green-600',
    bgColor: 'bg-green-100'
  },
  {
    key: 'employment',
    label: 'Employment',
    icon: Target,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100'
  },
  {
    key: 'tourism',
    label: 'Tourism',
    icon: Info,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100'
  },
  {
    key: 'inflation',
    label: 'Inflation',
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-100'
  }
]

const SIGNAL_TYPES: SignalType[] = [
  {
    key: 'buy',
    label: 'Buy Signal',
    icon: TrendingUp,
    color: 'text-green-700',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  {
    key: 'sell',
    label: 'Sell Signal',
    icon: TrendingDown,
    color: 'text-red-700',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200'
  },
  {
    key: 'neutral',
    label: 'Neutral',
    icon: Minus,
    color: 'text-gray-700',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200'
  },
  {
    key: 'warning',
    label: 'Warning',
    icon: AlertTriangle,
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200'
  },
  {
    key: 'opportunity',
    label: 'Opportunity',
    icon: TrendingUp,
    color: 'text-blue-700',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  }
]

export default function EconomicSignalMarkers({
  signals,
  onSignalClick,
  onSignalDismiss,
  showFilters = true,
  className = '',
  maxVisible = 10,
  autoRefresh = false,
  refreshInterval = 30000
}: EconomicSignalMarkersProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [timeFilter, setTimeFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('date')
  const [showDetails, setShowDetails] = useState<string | null>(null)

  // Filter signals based on selected criteria
  const filteredSignals = useMemo(() => {
    let filtered = [...signals]

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(signal => signal.category === selectedCategory)
    }

    // Type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter(signal => signal.type === selectedType)
    }

    // Time filter
    const now = new Date()
    switch (timeFilter) {
      case 'last_hour':
        filtered = filtered.filter(signal => {
          const signalDate = new Date(signal.date)
          return (now.getTime() - signalDate.getTime()) < 60 * 60 * 1000
        })
        break
      case 'last_day':
        filtered = filtered.filter(signal => {
          const signalDate = new Date(signal.date)
          return (now.getTime() - signalDate.getTime()) < 24 * 60 * 60 * 1000
        })
        break
      case 'last_week':
        filtered = filtered.filter(signal => {
          const signalDate = new Date(signal.date)
          return (now.getTime() - signalDate.getTime()) < 7 * 24 * 60 * 60 * 1000
        })
        break
    }

    // Sort signals
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.date).getTime() - new Date(a.date).getTime()
        case 'strength':
          return b.strength - a.strength
        case 'confidence':
          return b.confidence - a.confidence
        case 'value':
          return b.value - a.value
        default:
          return 0
      }
    })

    return filtered.slice(0, maxVisible)
  }, [signals, selectedCategory, selectedType, timeFilter, sortBy, maxVisible])

  // Get signal statistics
  const signalStats = useMemo(() => {
    const stats = {
      total: signals.length,
      byType: {} as Record<string, number>,
      byCategory: {} as Record<string, number>,
      recent: signals.filter(s => {
        const signalDate = new Date(s.date)
        const now = new Date()
        return (now.getTime() - signalDate.getTime()) < 24 * 60 * 60 * 1000
      }).length,
      highConfidence: signals.filter(s => s.confidence > 0.8).length
    }

    signals.forEach(signal => {
      stats.byType[signal.type] = (stats.byType[signal.type] || 0) + 1
      stats.byCategory[signal.category] = (stats.byCategory[signal.category] || 0) + 1
    })

    return stats
  }, [signals])

  const getSignalTypeConfig = (type: string) => {
    return SIGNAL_TYPES.find(t => t.key === type) || SIGNAL_TYPES[2] // Default to neutral
  }

  const getCategoryConfig = (category: string) => {
    return SIGNAL_CATEGORIES.find(c => c.key === category) || SIGNAL_CATEGORIES[0]
  }

  const getStrengthColor = (strength: number) => {
    if (strength >= 0.8) return 'bg-green-500'
    if (strength >= 0.6) return 'bg-yellow-500'
    if (strength >= 0.4) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600'
    if (confidence >= 0.7) return 'text-yellow-600'
    if (confidence >= 0.5) return 'text-orange-600'
    return 'text-red-600'
  }

  const handleSignalClick = useCallback((signal: EconomicSignal) => {
    if (onSignalClick) {
      onSignalClick(signal)
    } else {
      setShowDetails(showDetails === signal.id ? null : signal.id)
    }
  }, [onSignalClick, showDetails])

  const handleDismiss = useCallback((signalId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (onSignalDismiss) {
      onSignalDismiss(signalId)
    }
  }, [onSignalDismiss])

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AlertTriangle className="h-6 w-6 text-yellow-600 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Economic Signal Markers</h3>
              <p className="text-sm text-gray-500">
                {signalStats.total} signals detected • {signalStats.recent} in last 24 hours
              </p>
            </div>
          </div>
          {onSignalDismiss && (
            <button
              onClick={() => {
                // Dismiss all signals
                signals.forEach(signal => onSignalDismiss(signal.id))
              }}
              className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
            >
              Dismiss All
            </button>
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{signalStats.total}</div>
            <div className="text-xs text-gray-500">Total Signals</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{signalStats.highConfidence}</div>
            <div className="text-xs text-gray-500">High Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{signalStats.recent}</div>
            <div className="text-xs text-gray-500">Last 24h</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {Object.keys(signalStats.byCategory).length}
            </div>
            <div className="text-xs text-gray-500">Categories</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Categories</option>
                {SIGNAL_CATEGORIES.map(category => (
                  <option key={category.key} value={category.key}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Signal Type</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Types</option>
                {SIGNAL_TYPES.map(type => (
                  <option key={type.key} value={type.key}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Time Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Time Range</label>
              <select
                value={timeFilter}
                onChange={(e) => setTimeFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Time</option>
                <option value="last_hour">Last Hour</option>
                <option value="last_day">Last 24 Hours</option>
                <option value="last_week">Last Week</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="date">Date (Newest)</option>
                <option value="strength">Signal Strength</option>
                <option value="confidence">Confidence</option>
                <option value="value">Value</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Signals List */}
      <div className="divide-y divide-gray-200">
        {filteredSignals.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <AlertTriangle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p>No signals found for the selected criteria.</p>
          </div>
        ) : (
          filteredSignals.map(signal => {
            const typeConfig = getSignalTypeConfig(signal.type)
            const categoryConfig = getCategoryConfig(signal.category)
            const TypeIcon = typeConfig.icon

            return (
              <div
                key={signal.id}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  typeConfig.borderColor
                }`}
                onClick={() => handleSignalClick(signal)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {/* Signal Icon */}
                    <div className={`p-2 rounded-lg ${typeConfig.bgColor}`}>
                      <TypeIcon className={`h-5 w-5 ${typeConfig.color}`} />
                    </div>

                    {/* Signal Content */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`text-sm font-medium ${typeConfig.color}`}>
                          {typeConfig.label}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${categoryConfig.bgColor} ${categoryConfig.color}`}>
                          {categoryConfig.label}
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(signal.date), 'MMM dd, HH:mm')}
                        </span>
                      </div>

                      <p className="text-sm text-gray-900 mb-2">{signal.description}</p>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>
                          Value: <span className="font-medium">{signal.value.toFixed(2)}</span>
                          {signal.previousValue && (
                            <span className="ml-1">
                              ({signal.value > signal.previousValue ? '+' : ''}{(signal.value - signal.previousValue).toFixed(2)})
                            </span>
                          )}
                        </span>
                        <span>
                          Strength: <span className={`font-medium ${getStrengthColor(signal.strength).replace('bg-', 'text-')}`}>
                            {(signal.strength * 100).toFixed(0)}%
                          </span>
                        </span>
                        <span>
                          Confidence: <span className={`font-medium ${getConfidenceColor(signal.confidence)}`}>
                            {(signal.confidence * 100).toFixed(0)}%
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    {onSignalDismiss && (
                      <button
                        onClick={(e) => handleDismiss(signal.id, e)}
                        className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        title="Dismiss signal"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    <Clock className="h-4 w-4 text-gray-400" />
                  </div>
                </div>

                {/* Signal Details (expandable) */}
                {showDetails === signal.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Signal Details</h4>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Indicator:</span>
                            <span className="font-medium">{signal.indicator.toUpperCase()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Threshold:</span>
                            <span className="font-medium">
                              {signal.threshold ? signal.threshold.toFixed(2) : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Previous Value:</span>
                            <span className="font-medium">
                              {signal.previousValue ? signal.previousValue.toFixed(2) : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Created:</span>
                            <span className="font-medium">
                              {format(new Date(signal.createdAt), 'MMM dd, yyyy HH:mm:ss')}
                            </span>
                          </div>
                        </div>
                      </div>

                      {signal.metadata && Object.keys(signal.metadata).length > 0 && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Additional Information</h4>
                          <div className="space-y-1">
                            {Object.entries(signal.metadata).map(([key, value]) => (
                              <div key={key} className="flex justify-between">
                                <span className="text-gray-500 capitalize">
                                  {key.replace(/_/g, ' ')}:
                                </span>
                                <span className="font-medium">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="mt-4 flex justify-end">
                      <button
                        onClick={() => setShowDetails(null)}
                        className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        Close Details
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer */}
      {filteredSignals.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Showing {filteredSignals.length} of {signalStats.total} signals</span>
            {autoRefresh && (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Auto-refresh every {refreshInterval / 1000}s</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}