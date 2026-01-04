/**
 * Economic Data Dashboard Page
 * 經濟數據儀表板頁面
 */

import React, { useState, useEffect, useMemo } from 'react'
import { Calendar, Filter, RefreshCw, Download, Settings, TrendingUp, AlertCircle, Activity } from 'lucide-react'
import { format } from 'date-fns'
import EconomicDataCharts from '../components/EconomicDataCharts'
import EconomicDataFilters from '../components/EconomicDataFilters'
import EconomicDataTable from '../components/EconomicDataTable'
import { useEconomicData } from '../hooks/useEconomicData'
import { economicDataApi } from '../services/economicDataApi'

interface EconomicDataDashboardProps {
  className?: string
}

interface TimeRangeOption {
  label: string
  value: { start: string; end: string }
  shortcut?: string
}

interface QuickStats {
  totalIndicators: number
  lastUpdated: string | null
  dataPoints: number
  activeAlerts: number
}

const TIME_RANGES: TimeRangeOption[] = [
  {
    label: 'Last 7 Days',
    value: {
      start: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    shortcut: '7d'
  },
  {
    label: 'Last 30 Days',
    value: {
      start: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    shortcut: '30d'
  },
  {
    label: 'Last Quarter',
    value: {
      start: format(new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    shortcut: '90d'
  },
  {
    label: 'Year to Date',
    value: {
      start: format(new Date(new Date().getFullYear(), 0, 1), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    shortcut: 'ytd'
  },
  {
    label: 'Custom Range',
    value: { start: '', end: '' }
  }
]

export default function EconomicDataDashboard({ className = '' }: EconomicDataDashboardProps) {
  // State management
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRangeOption>(TIME_RANGES[1]) // Default to 30 days
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'])
  const [chartType, setChartType] = useState<'timeSeries' | 'scatter' | 'heatmap' | 'correlation' | 'comparison'>('timeSeries')
  const [showFilters, setShowFilters] = useState(false)
  const [showDataTable, setShowDataTable] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' })

  // Economic data hook
  const {
    data,
    filteredData,
    loading,
    error,
    lastUpdated,
    fetchAllIndicators,
    setFilter,
    refreshData,
    clearCache
  } = useEconomicData({
    autoFetch: true,
    cacheEnabled: true,
    refreshInterval: 300000 // 5 minutes
  })

  // Calculate quick statistics
  const quickStats: QuickStats = useMemo(() => {
    const totalIndicators = Object.keys(filteredData).length
    let dataPoints = 0
    let activeAlerts = 0

    Object.values(filteredData).forEach(indicatorData => {
      if (Array.isArray(indicatorData)) {
        dataPoints += indicatorData.length

        // Simulate alert detection (would be replaced with actual alert logic)
        indicatorData.forEach(point => {
          if (point.value && typeof point.value === 'number') {
            // Example alert conditions
            if (point.indicator === 'hibor' && point.value > 6) activeAlerts++
            if (point.indicator === 'unemployment' && point.value > 4) activeAlerts++
            if (point.indicator === 'pmi' && point.value < 50) activeAlerts++
          }
        })
      }
    })

    return {
      totalIndicators,
      lastUpdated,
      dataPoints,
      activeAlerts
    }
  }, [filteredData, lastUpdated])

  // Fetch data when time range changes
  useEffect(() => {
    if (selectedTimeRange.label === 'Custom Range' && customDateRange.start && customDateRange.end) {
      fetchAllIndicators(customDateRange)
    } else if (selectedTimeRange.value.start && selectedTimeRange.value.end) {
      fetchAllIndicators(selectedTimeRange.value)
    }
  }, [selectedTimeRange, customDateRange, fetchAllIndicators])

  // Handle manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      clearCache()
      await refreshData()
    } catch (error) {
      console.error('Error refreshing data:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  // Handle data export
  const handleExport = (format: 'csv' | 'json' | 'pdf') => {
    // Implementation would depend on the export library
    console.log(`Exporting data as ${format}`)
    // Example: exportEconomicData(filteredData, format)
  }

  // Handle time range change
  const handleTimeRangeChange = (timeRange: TimeRangeOption) => {
    setSelectedTimeRange(timeRange)
    if (timeRange.label !== 'Custom Range') {
      setCustomDateRange({ start: '', end: '' })
    }
  }

  // Handle indicator selection
  const handleIndicatorChange = (indicators: string[]) => {
    setSelectedIndicators(indicators)
    setFilter({ indicators })
  }

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Economic Data Dashboard</h1>
                <p className="text-sm text-gray-500">Real-time economic indicators and analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Toggle Filters"
              >
                <Filter className="h-5 w-5" />
              </button>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                title="Refresh Data"
              >
                <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <div className="relative group">
                <button
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Export Data"
                >
                  <Download className="h-5 w-5" />
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                  <button
                    onClick={() => handleExport('csv')}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as CSV
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as JSON
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as PDF
                  </button>
                </div>
              </div>
              <button
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Settings"
              >
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Activity className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Indicators</p>
                <p className="text-2xl font-semibold text-gray-900">{quickStats.totalIndicators}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <Calendar className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Data Points</p>
                <p className="text-2xl font-semibold text-gray-900">{quickStats.dataPoints.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <AlertCircle className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Alerts</p>
                <p className="text-2xl font-semibold text-gray-900">{quickStats.activeAlerts}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <RefreshCw className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Last Updated</p>
                <p className="text-sm font-semibold text-gray-900">
                  {quickStats.lastUpdated
                    ? format(new Date(quickStats.lastUpdated), 'MMM dd, HH:mm')
                    : 'Never'
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
          <EconomicDataFilters
            timeRange={selectedTimeRange}
            customDateRange={customDateRange}
            selectedIndicators={selectedIndicators}
            onTimeRangeChange={handleTimeRangeChange}
            onCustomDateRangeChange={setCustomDateRange}
            onIndicatorChange={handleIndicatorChange}
            onChartTypeChange={setChartType}
            timeRanges={TIME_RANGES}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Chart Area */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Economic Indicators Visualization</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {selectedTimeRange.label} • {selectedIndicators.length} indicators
                </p>
              </div>
              <div className="p-6">
                <EconomicDataCharts
                  timeRange={selectedTimeRange.value}
                  chartType={chartType}
                  indicators={selectedIndicators}
                />
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Chart Type Selector */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Chart Type</h3>
              <div className="space-y-2">
                {[
                  { type: 'timeSeries', label: 'Time Series', description: 'Historical trends' },
                  { type: 'scatter', label: 'Scatter Plot', description: 'Correlation analysis' },
                  { type: 'heatmap', label: 'Heat Map', description: 'Current values' },
                  { type: 'correlation', label: 'Correlation', description: 'Multi-factor analysis' },
                  { type: 'comparison', label: 'Comparison', description: 'Side-by-side view' }
                ].map(({ type, label, description }) => (
                  <button
                    key={type}
                    onClick={() => setChartType(type as any)}
                    className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                      chartType === type
                        ? 'bg-blue-50 border-blue-200 text-blue-900'
                        : 'bg-white border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="font-medium">{label}</div>
                    <div className="text-sm text-gray-500">{description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={() => setShowDataTable(!showDataTable)}
                  className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                >
                  {showDataTable ? 'Hide' : 'Show'} Data Table
                </button>
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isRefreshing ? 'Refreshing...' : 'Refresh All Data'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Data Table Section */}
        {showDataTable && (
          <div className="mt-6">
            <EconomicDataTable
              data={filteredData}
              indicators={selectedIndicators}
              loading={loading}
              error={error}
            />
          </div>
        )}
      </div>
    </div>
  )
}