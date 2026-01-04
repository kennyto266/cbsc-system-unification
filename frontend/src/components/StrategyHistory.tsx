import React, { useState, useEffect } from 'react'
import { X, Calendar, Activity, TrendingUp, TrendingDown } from 'lucide-react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'

interface StrategyHistoryProps {
  strategy: any
  isOpen: boolean
  onClose: () => void
}

interface HistoryRecord {
  id: string
  timestamp: string
  action: string
  status: string
  details?: any
  performance?: {
    return: number
    trades: number
  }
}

export default function StrategyHistory({ strategy, isOpen, onClose }: StrategyHistoryProps) {
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadHistory()
    }
  }, [isOpen, strategy.id])

  const loadHistory = async () => {
    setLoading(true)
    try {
      // TODO: Implement actual API call
      // Mock data for now
      setHistory([
        {
          id: '1',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          action: 'Strategy Started',
          status: 'success',
          details: { reason: 'Manual start' }
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          action: 'Trade Executed',
          status: 'success',
          details: { symbol: 'AAPL', quantity: 100, price: 175.50 },
          performance: { return: 1.2, trades: 1 }
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 10800000).toISOString(),
          action: 'Strategy Paused',
          status: 'info',
          details: { reason: 'Manual pause' }
        }
      ])
    } catch (error) {
      console.error('Error loading history:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'warning': return 'text-yellow-600 bg-yellow-100'
      default: return 'text-blue-600 bg-blue-100'
    }
  }

  const getActionIcon = (action: string) => {
    if (action.includes('Start')) return Activity
    if (action.includes('Trade')) return TrendingUp
    if (action.includes('Stop') || action.includes('Pause')) return TrendingDown
    return Calendar
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl max-h-[80vh] overflow-hidden m-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Strategy History
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {strategy.name}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No history available</p>
            </div>
          ) : (
            <div className="overflow-y-auto max-h-[60vh]">
              <div className="space-y-3">
                {history.map((record) => {
                  const ActionIcon = getActionIcon(record.action)
                  return (
                    <div
                      key={record.id}
                      className="flex items-start p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="flex-shrink-0 mr-4">
                        <div className={`p-2 ${getStatusColor(record.status).split(' ')[1]} rounded-lg`}>
                          <ActionIcon className={`h-4 w-4 ${getStatusColor(record.status).split(' ')[0]}`} />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {record.action}
                          </h4>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(record.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {record.details && (
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            {Object.entries(record.details).map(([key, value]) => (
                              <span key={key} className="mr-3">
                                <strong>{key}:</strong> {String(value)}
                              </span>
                            ))}
                          </div>
                        )}
                        {record.performance && (
                          <div className="flex gap-4 mt-2">
                            <span className={`text-sm font-medium ${
                              record.performance.return >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {record.performance.return >= 0 ? '+' : ''}{record.performance.return}%
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              {record.performance.trades} trades
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={onClose}
            >
              Close
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
