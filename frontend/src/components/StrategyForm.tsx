import React, { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from './ui/Button'
import { Card } from './ui/Card'

interface StrategyFormProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (formData: any) => Promise<boolean>
  loading?: boolean
  initialData?: any
  isEdit?: boolean
}

const STRATEGY_TYPES = [
  { value: 'interest_rate_arbitrage', label: 'Interest Rate Arbitrage' },
  { value: 'economic_data_correlation', label: 'Economic Data Correlation' },
  { value: 'multi_indicator_momentum', label: 'Multi-Indicator Momentum' },
  { value: 'volatility_based', label: 'Volatility Based' },
  { value: 'seasonal_patterns', label: 'Seasonal Patterns' }
]

const AVAILABLE_INDICATORS = [
  'GDP Growth',
  'Inflation Rate',
  'Interest Rate',
  'Unemployment Rate',
  'PMI',
  'Retail Sales',
  'Consumer Confidence',
  'Industrial Production'
]

export default function StrategyForm({
  isOpen,
  onClose,
  onSubmit,
  loading = false,
  initialData,
  isEdit = false
}: StrategyFormProps) {
  const [formData, setFormData] = useState(
    initialData || {
      name: '',
      type: 'interest_rate_arbitrage',
      description: '',
      parameters: {},
      indicators: [],
      configuration: {
        autoRestart: false,
        riskLimits: {
          maxPositionSize: 100000,
          maxDailyLoss: 0.05,
          maxDrawdown: 0.15
        },
        executionSettings: {
          slippageTolerance: 0.001,
          executionDelay: 1000,
          retryAttempts: 3
        }
      }
    }
  )

  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(
    initialData?.indicators || []
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const success = await onSubmit({
      ...formData,
      indicators: selectedIndicators
    })
    if (success) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isEdit ? 'Edit Strategy' : 'Create New Strategy'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Strategy Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Strategy Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                placeholder="Enter strategy name"
              />
            </div>

            {/* Strategy Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Strategy Type *
              </label>
              <select
                required
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              >
                {STRATEGY_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description *
              </label>
              <textarea
                required
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                placeholder="Describe your strategy"
              />
            </div>

            {/* Indicators */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Economic Indicators *
              </label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_INDICATORS.map(indicator => (
                  <label key={indicator} className="flex items-center space-x-2 p-2 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                    <input
                      type="checkbox"
                      checked={selectedIndicators.includes(indicator)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedIndicators([...selectedIndicators, indicator])
                        } else {
                          setSelectedIndicators(selectedIndicators.filter(i => i !== indicator))
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{indicator}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Risk Limits */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Risk Limits</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max Position Size
                  </label>
                  <input
                    type="number"
                    value={formData.configuration.riskLimits.maxPositionSize}
                    onChange={(e) => setFormData({
                      ...formData,
                      configuration: {
                        ...formData.configuration,
                        riskLimits: {
                          ...formData.configuration.riskLimits,
                          maxPositionSize: Number(e.target.value)
                        }
                      }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max Daily Loss
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.configuration.riskLimits.maxDailyLoss}
                    onChange={(e) => setFormData({
                      ...formData,
                      configuration: {
                        ...formData.configuration,
                        riskLimits: {
                          ...formData.configuration.riskLimits,
                          maxDailyLoss: Number(e.target.value)
                        }
                      }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max Drawdown
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.configuration.riskLimits.maxDrawdown}
                    onChange={(e) => setFormData({
                      ...formData,
                      configuration: {
                        ...formData.configuration,
                        riskLimits: {
                          ...formData.configuration.riskLimits,
                          maxDrawdown: Number(e.target.value)
                        }
                      }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  />
                </div>
              </div>
            </div>

            {/* Auto Restart */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRestart"
                checked={formData.configuration.autoRestart}
                onChange={(e) => setFormData({
                  ...formData,
                  configuration: {
                    ...formData.configuration,
                    autoRestart: e.target.checked
                  }
                })}
                className="rounded"
              />
              <label htmlFor="autoRestart" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Auto-restart on error
              </label>
            </div>

            {/* Buttons */}
            <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={loading || selectedIndicators.length === 0}
              >
                {loading ? 'Saving...' : isEdit ? 'Update Strategy' : 'Create Strategy'}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  )
}
