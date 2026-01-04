/**
 * Strategy Performance Component
 * 策略績效分析組件
 */

import React, { useState, useEffect, useMemo } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Activity,
  Award,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Download,
  RefreshCw,
  Calendar,
  BarChart3,
  PieChart as PieChartIcon,
  Crosshair
} from 'lucide-react'

// Types
interface PerformanceMetric {
  date: string
  value: number
  benchmark?: number
  category?: string
}

interface PerformanceStats {
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  totalTrades: number
  averageWin: number
  averageLoss: number
  largestWin: number
  largestLoss: number
  volatility: number
  var: number  // Value at Risk
  beta: number
  alpha: number
}

interface ComparisonData {
  strategy: number
  benchmark: number
  category: string
}

interface AttributionData {
  category: string
  contribution: number
  percentage: number
}

interface StrategyPerformanceProps {
  strategyId?: string
  className?: string
  data?: {
    performance: PerformanceMetric[]
    stats: PerformanceStats
    comparison: ComparisonData[]
    attribution: AttributionData[]
    riskMetrics: {
      volatility: number[]
      correlation: number
      var: number[]
    }
  }
  timeRange?: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'
  benchmark?: string
  showComparison?: boolean
  showAttribution?: boolean
  showRiskMetrics?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  onExport?: (format: 'csv' | 'json' | 'pdf') => void
}

const CHART_COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  tertiary: '#f59e0b',
  quaternary: '#ef4444',
  quinary: '#8b5cf6',
  senary: '#ec4899',
  benchmark: '#6b7280',
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#6b7280'
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value?.toLocaleString?.() ?? entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

const PerformanceCard: React.FC<{
  title: string
  value: number | string
  change?: number
  icon?: React.ReactNode
  color?: string
  format?: 'number' | 'percentage' | 'currency'
}> = ({ title, value, change, icon, color = CHART_COLORS.primary, format = 'number' }) => {
  const formatValue = (val: number | string) => {
    if (typeof val === 'string') return val

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('zh-CN', {
          style: 'currency',
          currency: 'CNY'
        }).format(val)
      case 'percentage':
        return `${val.toFixed(2)}%`
      default:
        return val.toLocaleString('zh-CN')
    }
  }

  const isPositive = change && change > 0
  const isNegative = change && change < 0

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold" style={{ color }}>
            {formatValue(value)}
          </p>
          {change !== undefined && (
            <div className="flex items-center mt-2">
              {isPositive && <TrendingUp className="w-4 h-4 text-green-500 mr-1" />}
              {isNegative && <TrendingDown className="w-4 h-4 text-red-500 mr-1" />}
              <span className={`text-sm font-medium ${
                isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
              }`}>
                {isPositive && '+'}{change.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
        {icon && (
          <div className="text-gray-400">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}

export default function StrategyPerformance({
  strategyId,
  className = '',
  data,
  timeRange = '1M',
  benchmark = 'HSI',
  showComparison = true,
  showAttribution = true,
  showRiskMetrics = true,
  autoRefresh = false,
  refreshInterval = 60000,
  onExport
}: StrategyPerformanceProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange)
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    returns: true,
    risk: false,
    attribution: false,
    comparison: false
  })
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('area')
  const [isLoading, setIsLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  // Mock data generation (replace with real API calls)
  const mockData = useMemo(() => {
    if (data) return data

    // Generate mock performance data
    const days = selectedTimeRange === '1D' ? 1 :
                 selectedTimeRange === '1W' ? 7 :
                 selectedTimeRange === '1M' ? 30 :
                 selectedTimeRange === '3M' ? 90 :
                 selectedTimeRange === '6M' ? 180 :
                 selectedTimeRange === '1Y' ? 365 : 730

    const performance: PerformanceMetric[] = []
    const baseValue = 100000
    let currentValue = baseValue

    for (let i = 0; i < days; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (days - i))

      const dailyReturn = (Math.random() - 0.48) * 0.03 // Slight positive bias
      currentValue *= (1 + dailyReturn)

      performance.push({
        date: date.toISOString().split('T')[0],
        value: currentValue,
        benchmark: baseValue * (1 + (Math.random() - 0.5) * 0.02 * (i / days))
      })
    }

    const stats: PerformanceStats = {
      totalReturn: ((currentValue - baseValue) / baseValue) * 100,
      annualizedReturn: Math.pow(currentValue / baseValue, 365 / days) * 100 - 100,
      sharpeRatio: 1.2 + Math.random() * 0.8,
      maxDrawdown: 5 + Math.random() * 10,
      winRate: 0.5 + Math.random() * 0.3,
      profitFactor: 1.1 + Math.random() * 0.5,
      totalTrades: Math.floor(50 + Math.random() * 200),
      averageWin: 0.5 + Math.random() * 1.5,
      averageLoss: 0.3 + Math.random() * 1.0,
      largestWin: 2 + Math.random() * 3,
      largestLoss: 1 + Math.random() * 2,
      volatility: 8 + Math.random() * 7,
      var: 1.5 + Math.random() * 2,
      beta: 0.8 + Math.random() * 0.4,
      alpha: 2 + Math.random() * 4
    }

    const comparison: ComparisonData[] = [
      { strategy: stats.annualizedReturn, benchmark: 8.5, category: '年化回報' },
      { strategy: stats.sharpeRatio, benchmark: 0.8, category: '夏普比率' },
      { strategy: stats.maxDrawdown, benchmark: 12, category: '最大回撤' },
      { strategy: stats.winRate * 100, benchmark: 52, category: '勝率' }
    ]

    const attribution: AttributionData[] = [
      { category: 'HIBOR套利', contribution: 4.5, percentage: 35 },
      { category: 'GDP相關', contribution: 3.2, percentage: 25 },
      { category: 'PMI指標', contribution: 2.8, percentage: 22 },
      { category: '訪客數據', contribution: 1.5, percentage: 12 },
      { category: '失業率', contribution: 0.8, percentage: 6 }
    ]

    return {
      performance,
      stats,
      comparison,
      attribution,
      riskMetrics: {
        volatility: Array.from({ length: 12 }, () => 5 + Math.random() * 10),
        correlation: 0.3 + Math.random() * 0.4,
        var: Array.from({ length: 30 }, () => 1 + Math.random() * 3)
      }
    }
  }, [selectedTimeRange, data])

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const handleRefresh = async () => {
    setIsLoading(true)
    // Simulate data refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    setLastRefresh(new Date())
    setIsLoading(false)
  }

  const handleExport = (format: 'csv' | 'json' | 'pdf') => {
    if (onExport) {
      onExport(format)
    }
  }

  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(handleRefresh, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  const { performance, stats, comparison, attribution } = mockData

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">策略績效分析</h2>
            <p className="mt-1 text-sm text-gray-600">
              最後更新: {lastRefresh.toLocaleString('zh-CN')}
            </p>
          </div>
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            {/* Time Range Selector */}
            <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
              {['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'].map((range) => (
                <button
                  key={range}
                  onClick={() => setSelectedTimeRange(range as any)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    selectedTimeRange === range
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            {/* Chart Type Selector */}
            <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setChartType('line')}
                className={`p-1 rounded transition-colors ${
                  chartType === 'line' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="折線圖"
              >
                <Activity className="w-4 h-4" />
              </button>
              <button
                onClick={() => setChartType('area')}
                className={`p-1 rounded transition-colors ${
                  chartType === 'area' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="面積圖"
              >
                <BarChart3 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setChartType('bar')}
                className={`p-1 rounded transition-colors ${
                  chartType === 'bar' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="柱狀圖"
              >
                <BarChart3 className="w-4 h-4" />
              </button>
            </div>

            {/* Export Menu */}
            <div className="relative group">
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                <Download className="w-4 h-4" />
              </button>
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                <div className="p-2">
                  <button
                    onClick={() => handleExport('csv')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    導出 CSV
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    導出 JSON
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    導出 PDF
                  </button>
                </div>
              </div>
            </div>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <PerformanceCard
          title="總回報率"
          value={stats.totalReturn}
          icon={<DollarSign className="w-6 h-6" />}
          color={stats.totalReturn >= 0 ? CHART_COLORS.positive : CHART_COLORS.negative}
          format="percentage"
        />
        <PerformanceCard
          title="年化回報率"
          value={stats.annualizedReturn}
          icon={<TrendingUp className="w-6 h-6" />}
          color={stats.annualizedReturn >= 0 ? CHART_COLORS.positive : CHART_COLORS.negative}
          format="percentage"
        />
        <PerformanceCard
          title="夏普比率"
          value={stats.sharpeRatio}
          icon={<Target className="w-6 h-6" />}
          color={CHART_COLORS.primary}
        />
        <PerformanceCard
          title="最大回撤"
          value={stats.maxDrawdown}
          icon={<AlertCircle className="w-6 h-6" />}
          color={CHART_COLORS.negative}
          format="percentage"
        />
      </div>

      {/* Performance Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">績效走勢圖</h3>
            <button
              onClick={() => toggleSection('returns')}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
            >
              {expandedSections.returns ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>
          </div>
        </div>

        {expandedSections.returns && (
          <div className="p-6">
            <ResponsiveContainer width="100%" height={400}>
              {chartType === 'line' ? (
                <LineChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                    }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="策略淨值"
                    stroke={CHART_COLORS.primary}
                    strokeWidth={2}
                    dot={false}
                  />
                  {showComparison && (
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      name={benchmark}
                      stroke={CHART_COLORS.benchmark}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  )}
                </LineChart>
              ) : chartType === 'area' ? (
                <AreaChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                    }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="value"
                    name="策略淨值"
                    stroke={CHART_COLORS.primary}
                    fill={CHART_COLORS.primary}
                    fillOpacity={0.3}
                  />
                  {showComparison && (
                    <Area
                      type="monotone"
                      dataKey="benchmark"
                      name={benchmark}
                      stroke={CHART_COLORS.benchmark}
                      fill={CHART_COLORS.benchmark}
                      fillOpacity={0.1}
                    />
                  )}
                </AreaChart>
              ) : (
                <BarChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                    }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}K`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="value" name="策略淨值" fill={CHART_COLORS.primary} />
                  {showComparison && (
                    <Bar dataKey="benchmark" name={benchmark} fill={CHART_COLORS.benchmark} />
                  )}
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Detailed Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Stats */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">詳細統計</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">總交易次數</p>
                <p className="text-lg font-semibold">{stats.totalTrades}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">勝率</p>
                <p className="text-lg font-semibold">{(stats.winRate * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">平均盈利</p>
                <p className="text-lg font-semibold text-green-600">+{stats.averageWin.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">平均虧損</p>
                <p className="text-lg font-semibold text-red-600">-{stats.averageLoss.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">最大盈利</p>
                <p className="text-lg font-semibold text-green-600">+{stats.largestWin.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">最大虧損</p>
                <p className="text-lg font-semibold text-red-600">-{stats.largestLoss.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">盈利因子</p>
                <p className="text-lg font-semibold">{stats.profitFactor.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">波動率</p>
                <p className="text-lg font-semibold">{stats.volatility.toFixed(2)}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">風險指標</h3>
              <button
                onClick={() => toggleSection('risk')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.risk ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.risk && (
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">VaR (95%)</p>
                  <p className="text-lg font-semibold text-red-600">-{stats.var.toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Beta</p>
                  <p className="text-lg font-semibold">{stats.beta.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Alpha</p>
                  <p className="text-lg font-semibold">{stats.alpha.toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">夏普比率</p>
                  <p className="text-lg font-semibold">{stats.sharpeRatio.toFixed(2)}</p>
                </div>
              </div>

              {/* Risk Radar Chart */}
              <div className="mt-6">
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={[
                    { subject: '回報率', value: (stats.annualizedReturn / 20) * 100, fullMark: 100 },
                    { subject: '夏普比率', value: (stats.sharpeRatio / 3) * 100, fullMark: 100 },
                    { subject: '風險控制', value: 100 - (stats.maxDrawdown / 20) * 100, fullMark: 100 },
                    { subject: '穩定性', value: 100 - (stats.volatility / 20) * 100, fullMark: 100 },
                    { subject: '勝率', value: stats.winRate * 100, fullMark: 100 }
                  ]}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <Radar
                      name="風險指標"
                      dataKey="value"
                      stroke={CHART_COLORS.primary}
                      fill={CHART_COLORS.primary}
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Performance Attribution */}
      {showAttribution && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">績效歸因分析</h3>
              <button
                onClick={() => toggleSection('attribution')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.attribution ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.attribution && (
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Attribution Pie Chart */}
                <div>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={attribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ category, percentage }) => `${category} ${percentage}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="contribution"
                      >
                        {attribution.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={[
                              CHART_COLORS.primary,
                              CHART_COLORS.secondary,
                              CHART_COLORS.tertiary,
                              CHART_COLORS.quaternary,
                              CHART_COLORS.quinary
                            ][index] || CHART_COLORS.senary}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Attribution Details */}
                <div className="space-y-3">
                  {attribution.map((item, index) => (
                    <div key={item.category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div
                          className="w-3 h-3 rounded-full mr-3"
                          style={{
                            backgroundColor: [
                              CHART_COLORS.primary,
                              CHART_COLORS.secondary,
                              CHART_COLORS.tertiary,
                              CHART_COLORS.quaternary,
                              CHART_COLORS.quinary
                            ][index] || CHART_COLORS.senary
                          }}
                        />
                        <span className="font-medium text-gray-900">{item.category}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold" style={{
                          color: item.contribution > 0 ? CHART_COLORS.positive : CHART_COLORS.negative
                        }}>
                          {item.contribution > 0 ? '+' : ''}{item.contribution.toFixed(2)}%
                        </p>
                        <p className="text-sm text-gray-600">{item.percentage}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Benchmark Comparison */}
      {showComparison && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">基準比較</h3>
              <button
                onClick={() => toggleSection('comparison')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.comparison ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.comparison && (
            <div className="p-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparison} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis dataKey="category" type="category" tick={{ fontSize: 12 }} width={80} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="strategy" name="策略" fill={CHART_COLORS.primary} />
                  <Bar dataKey="benchmark" name={benchmark} fill={CHART_COLORS.benchmark} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  )
}