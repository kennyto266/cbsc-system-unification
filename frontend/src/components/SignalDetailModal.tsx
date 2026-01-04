/**
 * Signal Detail Modal Component
 * 信號詳細信息彈窗組件
 */

import React, { useState, useEffect } from 'react'
import {
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  Calendar,
  Target,
  Activity,
  Share2,
  Bookmark,
  Download,
  ExternalLink
} from 'lucide-react'
import { format } from 'date-fns'
import { EconomicSignal } from './EconomicSignalMarkers'

interface SignalDetailModalProps {
  signal: EconomicSignal | null
  isOpen: boolean
  onClose: () => void
  onAction?: (action: string, signal: EconomicSignal) => void
  className?: string
}

interface RelatedSignal {
  id: string
  date: string
  indicator: string
  type: 'buy' | 'sell' | 'neutral' | 'warning' | 'opportunity'
  description: string
  correlation: number
}

export default function SignalDetailModal({
  signal,
  isOpen,
  onClose,
  onAction,
  className = ''
}: SignalDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'history' | 'correlation'>('details')
  const [isBookmarked, setIsBookmarked] = useState(false)

  // Mock related signals based on the current signal
  const relatedSignals: RelatedSignal[] = [
    {
      id: 'rel-1',
      date: '2024-01-14T10:30:00Z',
      indicator: 'PMI',
      type: 'buy',
      description: 'PMI increased above 50, indicating expansion',
      correlation: 0.85
    },
    {
      id: 'rel-2',
      date: '2024-01-14T09:15:00Z',
      indicator: 'GDP',
      type: 'warning',
      description: 'GDP growth rate approaching threshold',
      correlation: -0.42
    },
    {
      id: 'rel-3',
      date: '2024-01-14T08:45:00Z',
      indicator: 'HIBOR',
      type: 'sell',
      description: 'HIBOR spike detected, potential market pressure',
      correlation: 0.67
    }
  ]

  useEffect(() => {
    // Reset to details tab when modal opens with new signal
    if (isOpen && signal) {
      setActiveTab('details')
      setIsBookmarked(false)
    }
  }, [isOpen, signal])

  if (!signal || !isOpen) {
    return null
  }

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'buy':
      case 'opportunity':
        return TrendingUp
      case 'sell':
        return TrendingDown
      case 'warning':
        return AlertTriangle
      default:
        return Info
    }
  }

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'buy':
      case 'opportunity':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'sell':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
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

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'interest_rate':
        return Activity
      case 'economic_growth':
        return TrendingUp
      case 'employment':
        return Target
      case 'tourism':
        return Info
      case 'inflation':
        return AlertTriangle
      default:
        return Info
    }
  }

  const handleAction = (action: string) => {
    if (onAction) {
      onAction(action, signal)
    }
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Economic Signal Alert',
          text: `${signal.type.toUpperCase()} signal for ${signal.indicator}: ${signal.description}`,
          url: window.location.href
        })
      } catch (error) {
        console.log('Error sharing:', error)
      }
    } else {
      // Fallback for browsers that don't support Web Share API
      navigator.clipboard.writeText(
        `${signal.type.toUpperCase()} signal for ${signal.indicator}: ${signal.description} - ${window.location.href}`
      )
      alert('Signal details copied to clipboard')
    }
  }

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked)
    handleAction('bookmark')
  }

  const handleExport = () => {
    const exportData = {
      signal: {
        id: signal.id,
        type: signal.type,
        indicator: signal.indicator,
        value: signal.value,
        strength: signal.strength,
        confidence: signal.confidence,
        description: signal.description,
        date: signal.date,
        category: signal.category
      },
      exportedAt: new Date().toISOString(),
      exportedBy: 'Economic Dashboard'
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `economic-signal-${signal.id}-${format(new Date(), 'yyyy-MM-dd')}.json`
    a.click()
    URL.revokeObjectURL(url)

    handleAction('export')
  }

  const SignalIcon = getSignalIcon(signal.type)
  const CategoryIcon = getCategoryIcon(signal.category)

  return (
    <div className={`fixed inset-0 z-50 overflow-y-auto ${className}`}>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className={`px-6 py-4 border-b ${getSignalColor(signal.type)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-3 rounded-lg ${getSignalColor(signal.type).split(' ')[1]} ${getSignalColor(signal.type).split(' ')[2]}`}>
                  <SignalIcon className={`h-6 w-6 ${getSignalColor(signal.type).split(' ')[0]}`} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {signal.type.toUpperCase()} Signal
                  </h3>
                  <p className="text-sm text-gray-600">
                    {signal.indicator.toUpperCase()} • {format(new Date(signal.date), 'MMM dd, yyyy HH:mm')}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {/* Action Buttons */}
                <button
                  onClick={handleBookmark}
                  className={`p-2 rounded-lg hover:bg-gray-100 transition-colors ${
                    isBookmarked ? 'text-yellow-600' : 'text-gray-400'
                  }`}
                  title={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
                >
                  <Bookmark className={`h-5 w-5 ${isBookmarked ? 'fill-current' : ''}`} />
                </button>

                <button
                  onClick={handleShare}
                  className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Share signal"
                >
                  <Share2 className="h-5 w-5" />
                </button>

                <button
                  onClick={handleExport}
                  className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Export signal data"
                >
                  <Download className="h-5 w-5" />
                </button>

                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { key: 'details', label: 'Signal Details', icon: Info },
                { key: 'history', label: 'Historical Context', icon: Calendar },
                { key: 'correlation', label: 'Related Signals', icon: Target }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4" />
                    <span>{label}</span>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
            {/* Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                {/* Main Description */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Signal Description</h4>
                  <p className="text-gray-700">{signal.description}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Current Value</div>
                    <div className="text-xl font-bold text-gray-900">
                      {signal.value.toFixed(2)}
                    </div>
                    {signal.previousValue && (
                      <div className="text-xs text-gray-500 mt-1">
                        Previous: {signal.previousValue.toFixed(2)}
                      </div>
                    )}
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Signal Strength</div>
                    <div className="flex items-center space-x-2">
                      <div className="text-xl font-bold text-gray-900">
                        {(signal.strength * 100).toFixed(0)}%
                      </div>
                      <div className={`w-3 h-3 rounded-full ${getStrengthColor(signal.strength)}`} />
                    </div>
                    <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getStrengthColor(signal.strength)} transition-all duration-300`}
                        style={{ width: `${signal.strength * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Confidence</div>
                    <div className="flex items-center space-x-2">
                      <div className={`text-xl font-bold ${getConfidenceColor(signal.confidence)}`}>
                        {(signal.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {signal.confidence >= 0.9 ? 'Very High' :
                       signal.confidence >= 0.7 ? 'High' :
                       signal.confidence >= 0.5 ? 'Medium' : 'Low'}
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Category</div>
                    <div className="flex items-center space-x-2">
                      <CategoryIcon className="h-5 w-5 text-blue-600" />
                      <span className="text-xl font-bold text-gray-900 capitalize">
                        {signal.category.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Additional Information */}
                {signal.threshold && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Threshold Information</h4>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        <span className="font-medium text-yellow-800">
                          Threshold Value: {signal.threshold.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-sm text-yellow-700 mt-2">
                        Signal triggered when value crossed this threshold
                      </p>
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {signal.metadata && Object.keys(signal.metadata).length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Additional Information</h4>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(signal.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-sm font-medium text-gray-700 capitalize">
                              {key.replace(/_/g, ' ')}:
                            </span>
                            <span className="text-sm text-gray-900 font-medium">
                              {String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">Signal Timestamps</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Signal Date:</span>
                        <span className="text-sm font-medium">
                          {format(new Date(signal.date), 'MMM dd, yyyy HH:mm:ss')}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Created:</span>
                        <span className="text-sm font-medium">
                          {format(new Date(signal.createdAt), 'MMM dd, yyyy HH:mm:ss')}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Historical Context Tab */}
            {activeTab === 'history' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Historical Performance</h4>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <div className="text-center">
                      <TrendingUp className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                      <h5 className="text-lg font-semibold text-blue-900 mb-2">Historical Analysis</h5>
                      <p className="text-blue-700 mb-4">
                        This signal type has historically shown a {signal.type === 'buy' ? '75%' : signal.type === 'sell' ? '68%' : '50%'}
                        accuracy rate for {signal.indicator} indicators.
                      </p>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-900">42</div>
                          <div className="text-sm text-blue-700">Similar Signals</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-green-600">85%</div>
                          <div className="text-sm text-blue-700">Success Rate</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-blue-900">3.2%</div>
                          <div className="text-sm text-blue-700">Avg. Impact</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Recent Similar Signals</h4>
                  <div className="space-y-3">
                    {[
                      {
                        date: '2024-01-10T14:30:00Z',
                        indicator: 'HIBOR',
                        type: 'buy',
                        strength: 0.85,
                        outcome: 'Successful',
                        impact: '+2.3%'
                      },
                      {
                        date: '2024-01-05T09:15:00Z',
                        indicator: 'PMI',
                        type: 'buy',
                        strength: 0.72,
                        outcome: 'Successful',
                        impact: '+1.8%'
                      },
                      {
                        date: '2023-12-28T11:45:00Z',
                        indicator: 'GDP',
                        type: 'warning',
                        strength: 0.68,
                        outcome: 'Neutral',
                        impact: '0.0%'
                      }
                    ].map((item, index) => {
                      const Icon = getSignalIcon(item.type)
                      return (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <Icon className={`h-5 w-5 ${getSignalColor(item.type).split(' ')[0]}`} />
                              <div>
                                <div className="font-medium text-gray-900">
                                  {item.indicator} - {item.type.toUpperCase()}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {format(new Date(item.date), 'MMM dd, yyyy HH:mm')}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-sm font-medium ${
                                item.outcome === 'Successful' ? 'text-green-600' :
                                item.outcome === 'Failed' ? 'text-red-600' : 'text-gray-600'
                              }`}>
                                {item.outcome}
                              </div>
                              <div className="text-xs text-gray-500">
                                Impact: {item.impact}
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Related Signals Tab */}
            {activeTab === 'correlation' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Related Economic Signals</h4>
                  <p className="text-sm text-gray-600 mb-6">
                    Signals that occurred around the same time and may be related to the current signal.
                  </p>

                  <div className="space-y-4">
                    {relatedSignals.map(relatedSignal => {
                      const Icon = getSignalIcon(relatedSignal.type)
                      const correlationColor = relatedSignal.correlation > 0.7 ? 'text-green-600' :
                                               relatedSignal.correlation > 0.3 ? 'text-yellow-600' :
                                               relatedSignal.correlation > -0.3 ? 'text-gray-600' : 'text-red-600'

                      return (
                        <div key={relatedSignal.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <Icon className={`h-5 w-5 ${getSignalColor(relatedSignal.type).split(' ')[0]}`} />
                              <div>
                                <div className="font-medium text-gray-900">
                                  {relatedSignal.indicator} - {relatedSignal.type.toUpperCase()}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {format(new Date(relatedSignal.date), 'MMM dd, HH:mm')}
                                </div>
                                <div className="text-sm text-gray-600 mt-1">
                                  {relatedSignal.description}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-lg font-bold ${correlationColor}`}>
                                {(relatedSignal.correlation * 100).toFixed(0)}%
                              </div>
                              <div className="text-xs text-gray-500">Correlation</div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Correlation Analysis</h4>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Target className="h-5 w-5 text-purple-600" />
                          <span className="font-medium text-purple-900">Strong Positive Correlation</span>
                        </div>
                        <p className="text-sm text-purple-700">
                          2 signals show strong positive correlation (70%+), suggesting they may be influenced by similar economic factors.
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <AlertTriangle className="h-5 w-5 text-purple-600" />
                          <span className="font-medium text-purple-900">Diverging Signals</span>
                        </div>
                        <p className="text-sm text-purple-700">
                          1 signal shows negative correlation, indicating potential market volatility or conflicting economic indicators.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Signal ID: {signal.id}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => window.open(`/dashboard/signals/${signal.id}`, '_blank')}
                  className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 transition-colors flex items-center space-x-1"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>View in Dashboard</span>
                </button>
                <button
                  onClick={() => handleAction('investigate')}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Investigate Further
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}