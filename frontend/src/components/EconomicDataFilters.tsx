/**
 * Economic Data Filters Component
 * 經濟數據過濾器組件
 */

import React, { useState } from 'react'
import { Calendar, ChevronDown, X, Filter } from 'lucide-react'
import { format } from 'date-fns'

interface TimeRangeOption {
  label: string
  value: { start: string; end: string }
  shortcut?: string
}

interface EconomicDataFiltersProps {
  timeRange: TimeRangeOption
  customDateRange: { start: string; end: string }
  selectedIndicators: string[]
  onTimeRangeChange: (timeRange: TimeRangeOption) => void
  onCustomDateRangeChange: (dateRange: { start: string; end: string }) => void
  onIndicatorChange: (indicators: string[]) => void
  onChartTypeChange: (chartType: string) => void
  timeRanges: TimeRangeOption[]
}

const INDICATOR_OPTIONS = [
  { value: 'hibor', label: 'HIBOR Rate', description: 'Hong Kong Interbank Offered Rate', color: 'blue' },
  { value: 'gdp', label: 'GDP Growth', description: 'Gross Domestic Product Growth Rate', color: 'green' },
  { value: 'pmi', label: 'PMI', description: 'Purchasing Managers Index', color: 'yellow' },
  { value: 'visitors', label: 'Visitor Arrivals', description: 'Tourist visitor statistics', color: 'purple' },
  { value: 'unemployment', label: 'Unemployment Rate', description: 'Labor market unemployment rate', color: 'red' }
]

const CHART_TYPE_OPTIONS = [
  { value: 'timeSeries', label: 'Time Series', icon: '📈' },
  { value: 'scatter', label: 'Scatter Plot', icon: '📊' },
  { value: 'heatmap', label: 'Heat Map', icon: '🔥' },
  { value: 'correlation', label: 'Correlation', icon: '🔗' },
  { value: 'comparison', label: 'Comparison', icon: '⚖️' }
]

export default function EconomicDataFilters({
  timeRange,
  customDateRange,
  selectedIndicators,
  onTimeRangeChange,
  onCustomDateRangeChange,
  onIndicatorChange,
  onChartTypeChange,
  timeRanges
}: EconomicDataFiltersProps) {
  const [showDatePicker, setShowDatePicker] = useState(false)
  const [tempStartDate, setTempStartDate] = useState(customDateRange.start)
  const [tempEndDate, setTempEndDate] = useState(customDateRange.end)

  const handleDateRangeApply = () => {
    if (tempStartDate && tempEndDate) {
      onCustomDateRangeChange({ start: tempStartDate, end: tempEndDate })
    }
    setShowDatePicker(false)
  }

  const handleDateRangeClear = () => {
    setTempStartDate('')
    setTempEndDate('')
    onCustomDateRangeChange({ start: '', end: '' })
    setShowDatePicker(false)
    // Reset to default 30 days
    onTimeRangeChange(timeRanges[1])
  }

  const handleIndicatorToggle = (indicator: string) => {
    const newIndicators = selectedIndicators.includes(indicator)
      ? selectedIndicators.filter(i => i !== indicator)
      : [...selectedIndicators, indicator]
    onIndicatorChange(newIndicators)
  }

  const getColorClass = (color: string) => {
    const colorMap = {
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      purple: 'bg-purple-500',
      red: 'bg-red-500'
    }
    return colorMap[color as keyof typeof colorMap] || 'bg-gray-500'
  }

  const getColorHoverClass = (color: string) => {
    const colorMap = {
      blue: 'hover:bg-blue-50',
      green: 'hover:bg-green-50',
      yellow: 'hover:bg-yellow-50',
      purple: 'hover:bg-purple-50',
      red: 'hover:bg-red-50'
    }
    return colorMap[color as keyof typeof colorMap] || 'hover:bg-gray-50'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Filter className="h-5 w-5 text-gray-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Dashboard Filters</h3>
        </div>
        <button
          onClick={() => {
            onIndicatorChange(['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'])
            onTimeRangeChange(timeRanges[1]) // Reset to 30 days
          }}
          className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
        >
          Reset All
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Time Range Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Time Range
          </label>
          <div className="space-y-2">
            {timeRanges.map((range) => (
              <button
                key={range.label}
                onClick={() => {
                  if (range.label !== 'Custom Range') {
                    onTimeRangeChange(range)
                    setShowDatePicker(false)
                  } else {
                    setShowDatePicker(true)
                  }
                }}
                className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                  timeRange.label === range.label
                    ? 'bg-blue-50 border-blue-200 text-blue-900'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{range.label}</span>
                  {range.shortcut && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {range.shortcut}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Custom Date Picker */}
          {showDatePicker && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={tempStartDate}
                    onChange={(e) => setTempStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={tempEndDate}
                    onChange={(e) => setTempEndDate(e.target.value)}
                    min={tempStartDate}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleDateRangeApply}
                    disabled={!tempStartDate || !tempEndDate}
                    className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Apply
                  </button>
                  <button
                    onClick={handleDateRangeClear}
                    className="flex-1 px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Indicator Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Economic Indicators
          </label>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {INDICATOR_OPTIONS.map((indicator) => (
              <div
                key={indicator.value}
                onClick={() => handleIndicatorToggle(indicator.value)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedIndicators.includes(indicator.value)
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                } ${getColorHoverClass(indicator.color)}`}
              >
                <div className="flex items-center">
                  <div
                    className={`w-3 h-3 rounded-full mr-3 ${getColorClass(indicator.color)}`}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{indicator.label}</div>
                    <div className="text-sm text-gray-500">{indicator.description}</div>
                  </div>
                  <div className="ml-3">
                    <div
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                        selectedIndicators.includes(indicator.value)
                          ? 'bg-blue-600 border-blue-600'
                          : 'bg-white border-gray-300'
                      }`}
                    >
                      {selectedIndicators.includes(indicator.value) && (
                        <div className="text-white text-xs">✓</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chart Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Visualization Type
          </label>
          <div className="space-y-2">
            {CHART_TYPE_OPTIONS.map((chartType) => (
              <button
                key={chartType.value}
                onClick={() => onChartTypeChange(chartType.value)}
                className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-xl mr-3">{chartType.icon}</span>
                  <span className="font-medium text-gray-900">{chartType.label}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Active Filters Summary */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {selectedIndicators.length} indicators selected • {timeRange.label}
          </div>
          {selectedIndicators.length === 0 && (
            <div className="text-sm text-red-600">
              Please select at least one indicator
            </div>
          )}
        </div>
      </div>
    </div>
  )
}