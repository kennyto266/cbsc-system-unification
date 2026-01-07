import React, { useState, useMemo, useCallback } from 'react'
import DualAxisChart, { MixedStrategyData, ChartThresholds } from './DualAxisChart'
import TimeframeSelector from './TimeframeSelector'
import { useTheme } from '../../contexts/ThemeContext'

export interface MixedStrategyViewerProps {
  data: MixedStrategyData[]
  title?: string
  loading?: boolean
  error?: string
  defaultTimeframe?: string
  onTimeframeChange?: (timeframe: string) => void
  onExport?: (filteredData: MixedStrategyData[]) => void
  className?: string
}

type Timeframe = '1d' | '1w' | '1m' | '1y' | 'all'

interface ViewerStats {
  avgPrice: number
  maxPrice: number
  minPrice: number
  totalVolume: number
  signalCount: {
    buy: number
    sell: number
    hold: number
  }
  priceChange: number
  priceChangePercent: number
}

const MixedStrategyViewer: React.FC<MixedStrategyViewerProps> = ({
  data,
  title = '混合策略视图',
  loading,
  error,
  defaultTimeframe = '1m',
  onTimeframeChange,
  onExport,
  className = ''
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  // State management
  const [timeframe, setTimeframe] = useState<Timeframe>(defaultTimeframe as Timeframe)
  const [showVolume, setShowVolume] = useState(true)
  const [showSignals, setShowSignals] = useState(true)
  const [showEconomic, setShowEconomic] = useState(false)
  const [showMA, setShowMA] = useState(false)
  const [showThresholds, setShowThresholds] = useState(false)
  const [selectedPoint, setSelectedPoint] = useState<MixedStrategyData | null>(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Filter data based on timeframe
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return []

    let filtered = [...data]

    // Apply date range filter if set
    if (startDate || endDate) {
      const startTime = startDate ? new Date(startDate).getTime() : 0
      const endTime = endDate ? new Date(endDate).getTime() : Infinity
      filtered = filtered.filter(d => d.timestamp >= startTime && d.timestamp <= endTime)
    } else {
      // Apply timeframe filter
      const now = Date.now()
      const cutoffs: Record<Timeframe, number> = {
        '1d': 24 * 60 * 60 * 1000,
        '1w': 7 * 24 * 60 * 60 * 1000,
        '1m': 30 * 24 * 60 * 60 * 1000,
        '1y': 365 * 24 * 60 * 60 * 1000,
        'all': 0
      }

      const cutoff = cutoffs[timeframe]
      if (cutoff > 0) {
        filtered = filtered.filter(d => d.timestamp >= now - cutoff)
      }
    }

    return filtered.sort((a, b) => a.timestamp - b.timestamp)
  }, [data, timeframe, startDate, endDate])

  // Calculate statistics
  const stats = useMemo((): ViewerStats | null => {
    if (!filteredData || filteredData.length === 0) return null

    const prices = filteredData.map(d => d.price || 0).filter(p => p > 0)
    const volumes = filteredData.map(d => d.volume || 0).filter(v => v > 0)
    const signals = filteredData.map(d => d.signal || 0)

    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length || 0
    const maxPrice = Math.max(...prices, 0)
    const minPrice = Math.min(...prices, Infinity)
    const totalVolume = volumes.reduce((a, b) => a + b, 0)

    const signalCount = {
      buy: signals.filter(s => s > 0).length,
      sell: signals.filter(s => s < 0).length,
      hold: signals.filter(s => s === 0).length
    }

    const firstPrice = prices[0] || 0
    const lastPrice = prices[prices.length - 1] || 0
    const priceChange = lastPrice - firstPrice
    const priceChangePercent = firstPrice > 0 ? (priceChange / firstPrice) * 100 : 0

    return {
      avgPrice,
      maxPrice,
      minPrice,
      totalVolume,
      signalCount,
      priceChange,
      priceChangePercent
    }
  }, [filteredData])

  // Calculate thresholds
  const thresholds: ChartThresholds | undefined = useMemo(() => {
    if (!stats) return undefined

    const { maxPrice, minPrice, avgPrice } = stats
    const range = maxPrice - minPrice

    return {
      upper: avgPrice + range * 0.1,
      lower: avgPrice - range * 0.1,
      middle: avgPrice
    }
  }, [stats])

  // Handle timeframe change
  const handleTimeframeChange = useCallback((newTimeframe: string) => {
    setTimeframe(newTimeframe as Timeframe)
    onTimeframeChange?.(newTimeframe)
  }, [onTimeframeChange])

  // Handle chart point click
  const handlePointClick = useCallback((point: MixedStrategyData) => {
    setSelectedPoint(point)
  }, [])

  // Handle export
  const handleExport = useCallback(() => {
    onExport?.(filteredData)
  }, [onExport, filteredData])

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `¥${(value / 1000).toFixed(1)}K`
    }
    return `¥${value.toFixed(2)}`
  }

  // Format large numbers
  const formatNumber = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    }
    return value.toString()
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  return (
    <div className={`w-full space-y-4 ${className}`}>
      {/* Header with title and controls */}
      <div className="flex items-center justify-between">
        <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          {title}
        </h2>

        <div className="flex items-center space-x-4">
          {/* Timeframe selector */}
          <TimeframeSelector
            value={timeframe}
            onChange={handleTimeframeChange}
          />

          {/* Export button */}
          {onExport && (
            <button
              onClick={handleExport}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              导出数据
            </button>
          )}
        </div>
      </div>

      {/* Date range filter */}
      <div className="flex items-center space-x-4">
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            开始日期
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className={`px-3 py-2 rounded-lg border ${
              isDark
                ? 'bg-gray-700 border-gray-600 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          />
        </div>

        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            结束日期
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className={`px-3 py-2 rounded-lg border ${
              isDark
                ? 'bg-gray-700 border-gray-600 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          />
        </div>
      </div>

      {/* Control Panel */}
      <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showVolume}
              onChange={(e) => setShowVolume(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              显示成交量
            </span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showSignals}
              onChange={(e) => setShowSignals(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              显示信号
            </span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showEconomic}
              onChange={(e) => setShowEconomic(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              显示经济指标
            </span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showMA}
              onChange={(e) => setShowMA(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              显示均线
            </span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showThresholds}
              onChange={(e) => setShowThresholds(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              显示阈值线
            </span>
          </label>
        </div>
      </div>

      {/* Main Chart */}
      <DualAxisChart
        data={filteredData}
        priceKey="price"
        volumeKey="volume"
        signalKey="signal"
        economicKeys={showEconomic ? ['gdp', 'inflation', 'unemployment'] : []}
        maKeys={showMA ? { short: 'ma_short', long: 'ma_long' } : undefined}
        height={400}
        showVolume={showVolume}
        showSignals={showSignals}
        showEconomic={showEconomic}
        showMA={showMA}
        showThresholds={showThresholds}
        thresholds={thresholds}
        onPointClick={handlePointClick}
      />

      {/* Statistics Panel */}
      {stats && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            统计信息
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>平均价格</p>
              <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {formatCurrency(stats.avgPrice)}
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>价格变化</p>
              <p className={`text-lg font-semibold ${
                stats.priceChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {stats.priceChange >= 0 ? '+' : ''}{formatCurrency(stats.priceChange)}
                <span className={`text-sm ml-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  ({stats.priceChangePercent.toFixed(2)}%)
                </span>
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>总成交量</p>
              <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {formatNumber(stats.totalVolume)}
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>信号分布</p>
              <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                买入: {stats.signalCount.buy} | 卖出: {stats.signalCount.sell} | 持有: {stats.signalCount.hold}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Point Detail Modal */}
      {selectedPoint && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedPoint(null)}
        >
          <div
            className={`p-6 rounded-lg max-w-md w-full mx-4 ${
              isDark ? 'bg-gray-800' : 'bg-white'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              详细信息
            </h3>

            <div className="space-y-2">
              <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                日期: {selectedPoint.date}
              </p>
              <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                价格: {formatCurrency(selectedPoint.price || 0)}
              </p>
              {selectedPoint.volume && (
                <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                  成交量: {formatNumber(selectedPoint.volume)}
                </p>
              )}
              {selectedPoint.signal && (
                <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                  信号: {selectedPoint.signal > 0 ? '买入' : selectedPoint.signal < 0 ? '卖出' : '持有'}
                </p>
              )}
              {selectedPoint.gdp && (
                <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                  GDP: {selectedPoint.gdp}%
                </p>
              )}
            </div>

            <button
              onClick={() => setSelectedPoint(null)}
              className={`mt-4 px-4 py-2 rounded-lg w-full ${
                isDark
                  ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default MixedStrategyViewer
export { MixedStrategyViewer }