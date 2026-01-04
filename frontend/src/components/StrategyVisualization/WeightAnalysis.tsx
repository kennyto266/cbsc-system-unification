import React, { useState, useMemo, useCallback } from 'react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export interface StrategyWeights {
  price: number
  economic: number
  volume: number
  technical: number
  [key: string]: number
}

export interface StrategyContribution {
  name: string
  weight: number
  contribution: number
  performance: number
  sharpe?: number
  maxDrawdown?: number
}

export interface CorrelationMatrix {
  [key: string]: { [key: string]: number }
}

export interface WeightAnalysisProps {
  weights: StrategyWeights
  contributions?: StrategyContribution[]
  correlations?: CorrelationMatrix
  onWeightChange?: (weights: StrategyWeights) => void
  onExport?: (weights: StrategyWeights) => void
  adjustable?: boolean
  showContributions?: boolean
  showRadar?: boolean
  showMetrics?: boolean
  showCorrelation?: boolean
  normalize?: boolean
  className?: string
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

const DEFAULT_WEIGHTS: StrategyWeights = {
  price: 0.25,
  economic: 0.25,
  volume: 0.25,
  technical: 0.25
}

export const WeightAnalysis: React.FC<WeightAnalysisProps> = ({
  weights,
  contributions = [],
  correlations,
  onWeightChange,
  onExport,
  adjustable = false,
  showContributions = true,
  showRadar = false,
  showMetrics = true,
  showCorrelation = false,
  normalize = true,
  className = ''
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const [validationError, setValidationError] = useState<string | null>(null)

  // Transform weights for pie chart
  const pieData = useMemo(() => {
    return Object.entries(weights)
      .filter(([_, value]) => value > 0)
      .map(([key, value]) => ({
        name: getStrategyName(key),
        value: value,
        percentage: (value * 100).toFixed(1)
      }))
  }, [weights])

  // Normalize weights if needed
  const normalizedWeights = useMemo(() => {
    if (!normalize) return weights

    const total = Object.values(weights).reduce((a, b) => a + b, 0)
    if (total === 0) return weights

    const normalized: StrategyWeights = {}
    for (const [key, value] of Object.entries(weights)) {
      normalized[key] = value / total
    }

    return normalized
  }, [weights, normalize])

  // Calculate performance metrics
  const metrics = useMemo(() => {
    if (!contributions.length) return null

    const totalReturn = contributions.reduce((sum, c) => sum + c.contribution * c.performance, 0)
    const weightedSharpe = contributions.reduce((sum, c) => sum + c.contribution * (c.sharpe || 0), 0)
    const maxDrawdown = Math.min(...contributions.map(c => c.maxDrawdown || 0))

    return {
      totalReturn,
      sharpeRatio: weightedSharpe,
      maxDrawdown,
      volatility: Math.sqrt(
        contributions.reduce((sum, c) => sum + Math.pow(c.contribution * (c.performance - totalReturn), 2), 0)
      )
    }
  }, [contributions])

  // Handle weight adjustment
  const handleWeightChange = useCallback((strategy: string, value: number) => {
    const newValue = parseFloat(value.toString())

    // Validation
    if (newValue < 0 || newValue > 1) {
      setValidationError('权重必须在 0 到 1 之间')
      return
    }

    setValidationError(null)

    const newWeights = { ...weights, [strategy]: newValue }

    // Normalize if enabled
    if (normalize && adjustable) {
      const total = Object.values(newWeights).reduce((a, b) => a + b, 0)
      if (total > 1) {
        // Normalize to keep sum = 1
        for (const key in newWeights) {
          newWeights[key] = newWeights[key] / total
        }
      }
    }

    onWeightChange?.(newWeights)
  }, [weights, onWeightChange, normalize, adjustable])

  // Reset to default weights
  const handleReset = useCallback(() => {
    onWeightChange?.(DEFAULT_WEIGHTS)
  }, [onWeightChange])

  // Get strategy display name
  function getStrategyName(key: string): string {
    const names: { [key: string]: string } = {
      price: '价格策略',
      economic: '经济指标',
      volume: '成交量',
      technical: '技术指标'
    }
    return names[key] || key
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null

    return (
      <div
        className={`p-3 rounded-lg shadow-lg border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}
      >
        <p className={`text-sm font-medium mb-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
          {label || payload[0].name}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(4) : entry.value}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          权重分析
        </h2>

        {adjustable && (
          <div className="flex space-x-2">
            <button
              onClick={handleReset}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              重置
            </button>

            {onExport && (
              <button
                onClick={() => onExport(weights)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isDark
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                导出配置
              </button>
            )}
          </div>
        )}
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className={`p-3 rounded-lg ${isDark ? 'bg-red-900' : 'bg-red-100'}`}>
          <p className={`text-sm ${isDark ? 'text-red-200' : 'text-red-700'}`}>
            {validationError}
          </p>
        </div>
      )}

      {/* Weight Normalization Notice */}
      {normalize && adjustable && (
        <div className={`p-3 rounded-lg ${isDark ? 'bg-blue-900' : 'bg-blue-100'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-200' : 'text-blue-700'}`}>
            权重已自动调整以确保总和为 1
          </p>
        </div>
      )}

      {/* Weight Distribution Pie Chart */}
      <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
        <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          权重分布
        </h3>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.percentage}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weight Adjustment Sliders */}
      {adjustable && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            权重调整
          </h3>

          <div className="space-y-4">
            {Object.entries(weights).map(([key, value]) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-2">
                  <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {getStrategyName(key)}权重
                  </label>
                  <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {(value * 100).toFixed(1)}%
                  </span>
                </div>

                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={value}
                  onChange={(e) => handleWeightChange(key, parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
              </div>
            ))}
          </div>

          <div className={`mt-4 pt-4 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                总计
              </span>
              <span className={`text-sm font-bold ${
                Math.abs(Object.values(weights).reduce((a, b) => a + b, 0) - 1) < 0.001
                  ? 'text-green-600'
                  : 'text-yellow-600'
              }`}>
                {(Object.values(weights).reduce((a, b) => a + b, 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Contribution Analysis */}
      {showContributions && contributions.length > 0 && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            贡献度分析
          </h3>

          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={contributions} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis
                  dataKey="name"
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                />
                <YAxis
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                  tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="contribution" fill={COLORS[0]} name="贡献度" />
                <Bar dataKey="performance" fill={COLORS[1]} name="收益率" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Radar Chart */}
      {showRadar && contributions.length > 0 && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            多维度分析
          </h3>

          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={contributions}>
                <PolarGrid stroke={isDark ? '#374151' : '#e5e7eb'} />
                <PolarAngleAxis
                  dataKey="name"
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 1]}
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  fontSize={12}
                />
                <Radar
                  name="权重"
                  dataKey="weight"
                  stroke={COLORS[0]}
                  fill={COLORS[0]}
                  fillOpacity={0.3}
                />
                <Radar
                  name="贡献度"
                  dataKey="contribution"
                  stroke={COLORS[1]}
                  fill={COLORS[1]}
                  fillOpacity={0.3}
                />
                <Legend />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {showMetrics && metrics && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            性能指标
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>总收益率</p>
              <p className={`text-lg font-semibold ${
                metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {(metrics.totalReturn * 100).toFixed(2)}%
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>夏普比率</p>
              <p className={`text-lg font-semibold ${
                metrics.sharpeRatio >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {metrics.sharpeRatio.toFixed(3)}
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>最大回撤</p>
              <p className={`text-lg font-semibold text-red-600`}>
                {(metrics.maxDrawdown * 100).toFixed(2)}%
              </p>
            </div>

            <div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>波动率</p>
              <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {(metrics.volatility * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Correlation Matrix */}
      {showCorrelation && correlations && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            相关性分析
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={`p-2 text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}></th>
                  {Object.keys(correlations).map(key => (
                    <th key={key} className={`p-2 text-center ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {getStrategyName(key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(correlations).map(([rowKey, row]) => (
                  <tr key={rowKey}>
                    <td className={`p-2 font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {getStrategyName(rowKey)}
                    </td>
                    {Object.entries(row).map(([colKey, value]) => (
                      <td
                        key={colKey}
                        className={`p-2 text-center ${
                          value > 0.7 ? 'text-green-600' :
                          value < -0.7 ? 'text-red-600' :
                          isDark ? 'text-gray-400' : 'text-gray-600'
                        }`}
                      >
                        {value.toFixed(3)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default WeightAnalysis