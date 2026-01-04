import React, { useState, useMemo, useCallback } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ScatterChart,
  Scatter,
  Cell
} from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

export interface SensitivityPoint {
  value: number
  return: number
  sharpe: number
  drawdown: number
  volatility?: number
  winRate?: number
  profitFactor?: number
}

export interface SensitivityData {
  [parameter: string]: SensitivityPoint[]
}

export interface HeatmapPoint {
  x: number
  y: number
  z: number
}

export interface HeatmapConfig {
  xParam: string
  yParam: string
  metric: keyof SensitivityPoint
}

export interface OptimalParameters {
  [parameter: string]: number
}

export interface ParameterRecommendation {
  parameter: string
  reason: string
  suggestion: string
  impact: 'low' | 'medium' | 'high'
  expectedImprovement?: number
}

export interface SensitivityAnalysisProps {
  parameters: { [key: string]: any }
  sensitivityData: SensitivityData
  optimalParameters?: OptimalParameters
  heatmapData?: HeatmapPoint[]
  heatmapConfig?: HeatmapConfig
  recommendations?: ParameterRecommendation[]
  onParameterChange?: (parameter: string, config: any) => void
  onOptimize?: (parameters: string[]) => void
  onExport?: (data: SensitivityData) => void
  loading?: boolean
  showHeatmap?: boolean
  showRecommendations?: boolean
  className?: string
}

type MetricType = 'return' | 'sharpe' | 'drawdown' | 'volatility' | 'winRate' | 'profitFactor'

const METRICS: { value: MetricType; label: string; color: string; formatter: (v: number) => string }[] = [
  {
    value: 'return',
    label: '收益率',
    color: '#3b82f6',
    formatter: (v: number) => `${(v * 100).toFixed(2)}%`
  },
  {
    value: 'sharpe',
    label: '夏普比率',
    color: '#10b981',
    formatter: (v: number) => v.toFixed(3)
  },
  {
    value: 'drawdown',
    label: '最大回撤',
    color: '#ef4444',
    formatter: (v: number) => `${(v * 100).toFixed(2)}%`
  },
  {
    value: 'volatility',
    label: '波动率',
    color: '#f59e0b',
    formatter: (v: number) => `${(v * 100).toFixed(2)}%`
  },
  {
    value: 'winRate',
    label: '胜率',
    color: '#8b5cf6',
    formatter: (v: number) => `${(v * 100).toFixed(2)}%`
  },
  {
    value: 'profitFactor',
    label: '盈亏比',
    color: '#ec4899',
    formatter: (v: number) => v.toFixed(2)
  }
]

export const SensitivityAnalysis: React.FC<SensitivityAnalysisProps> = ({
  parameters,
  sensitivityData,
  optimalParameters,
  heatmapData,
  heatmapConfig,
  recommendations,
  onParameterChange,
  onOptimize,
  onExport,
  loading = false,
  showHeatmap = false,
  showRecommendations = true,
  className = ''
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  // State for UI controls
  const [selectedParameter, setSelectedParameter] = useState<string>(
    Object.keys(sensitivityData)[0] || ''
  )
  const [selectedMetrics, setSelectedMetrics] = useState<MetricType[]>(['return', 'sharpe', 'drawdown'])
  const [parameterRange, setParameterRange] = useState<{ min: number; max: number }>({
    min: 0,
    max: 100
  })

  // Get current parameter data
  const currentData = useMemo(() => {
    return sensitivityData[selectedParameter] || []
  }, [sensitivityData, selectedParameter])

  // Calculate optimal point for current parameter
  const optimalPoint = useMemo(() => {
    if (!currentData.length) return null

    // Find point with highest Sharpe ratio
    return currentData.reduce((best, point) =>
      point.sharpe > best.sharpe ? point : best
    )
  }, [currentData])

  // Update parameter range when data changes
  useEffect(() => {
    if (currentData.length > 0) {
      const values = currentData.map(d => d.value)
      setParameterRange({
        min: Math.min(...values),
        max: Math.max(...values)
      })
    }
  }, [currentData])

  // Handle parameter selection
  const handleParameterSelect = useCallback((parameter: string) => {
    setSelectedParameter(parameter)
  }, [])

  // Handle metric toggle
  const handleMetricToggle = useCallback((metric: MetricType) => {
    setSelectedMetrics(prev =>
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    )
  }, [])

  // Handle range change
  const handleRangeChange = useCallback((type: 'min' | 'max', value: number) => {
    const newRange = { ...parameterRange, [type]: value }
    setParameterRange(newRange)

    onParameterChange?.(selectedParameter, {
      range: newRange
    })
  }, [parameterRange, selectedParameter, onParameterChange])

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null

    return (
      <div
        className={`p-3 rounded-lg shadow-lg border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}
      >
        <p className={`text-sm font-medium mb-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
          参数值: {label}
        </p>
        {payload.map((entry: any, index: number) => {
          const metric = METRICS.find(m => m.value === entry.dataKey)
          return (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {metric?.label || entry.dataKey}: {metric?.formatter(entry.value) || entry.value}
            </p>
          )
        })}
      </div>
    )
  }

  // Heatmap color scale
  const getHeatmapColor = (value: number, min: number, max: number) => {
    const ratio = (value - min) / (max - min)
    if (ratio < 0.25) return '#22c55e'
    if (ratio < 0.5) return '#84cc16'
    if (ratio < 0.75) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          参数敏感性分析
        </h2>

        <div className="flex space-x-2">
          {onOptimize && (
            <button
              onClick={() => onOptimize([selectedParameter])}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              优化参数
            </button>
          )}

          {onExport && (
            <button
              onClick={() => onExport(sensitivityData)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              导出结果
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className={`ml-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            分析中...
          </span>
        </div>
      )}

      {!loading && !Object.keys(sensitivityData).length && (
        <div className="flex items-center justify-center h-64">
          <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
            暂无敏感性数据
          </p>
        </div>
      )}

      {!loading && Object.keys(sensitivityData).length > 0 && (
        <>
          {/* Parameter Selection */}
          <div className="flex items-center space-x-4">
            <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              选择参数:
            </label>
            <select
              data-testid="parameter-selector"
              value={selectedParameter}
              onChange={(e) => handleParameterSelect(e.target.value)}
              className={`px-3 py-2 rounded-lg border ${
                isDark
                  ? 'bg-gray-700 border-gray-600 text-white'
                  : 'bg-white border-gray-300 text-gray-900'
              } focus:outline-none focus:ring-2 focus:ring-blue-500`}
            >
              {Object.entries(sensitivityData).map(([key, _]) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>

            {/* Metric Selection */}
            <div className="flex items-center space-x-2">
              <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                显示指标:
              </label>
              {METRICS.map(metric => (
                <label key={metric.value} className="flex items-center space-x-1">
                  <input
                    type="checkbox"
                    checked={selectedMetrics.includes(metric.value)}
                    onChange={() => handleMetricToggle(metric.value)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {metric.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Parameter Range Controls */}
          {currentData.length > 0 && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className={`text-sm font-medium mb-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                参数范围调整
              </h3>

              <div className="flex items-center space-x-4">
                <div>
                  <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    范围起始
                  </label>
                  <input
                    type="number"
                    value={parameterRange.min}
                    onChange={(e) => handleRangeChange('min', parseFloat(e.target.value))}
                    className={`w-24 px-2 py-1 rounded border ${
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}
                  />
                </div>

                <div>
                  <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    范围结束
                  </label>
                  <input
                    type="number"
                    value={parameterRange.max}
                    onChange={(e) => handleRangeChange('max', parseFloat(e.target.value))}
                    className={`w-24 px-2 py-1 rounded border ${
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}
                  />
                </div>

                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  当前值: {parameters[selectedParameter]}
                </div>
              </div>
            </div>
          )}

          {/* Sensitivity Chart */}
          {currentData.length > 0 && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                敏感性曲线
              </h3>

              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={currentData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={isDark ? '#374151' : '#e5e7eb'}
                    />
                    <XAxis
                      dataKey="value"
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                      label={{ value: '参数值', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                      tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    {/* Current parameter value line */}
                    <Line
                      type="monotone"
                      dataKey={() => parameters[selectedParameter]}
                      stroke="#ef4444"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      name="当前值"
                    />

                    {/* Optimal point marker */}
                    {optimalPoint && (
                      <Line
                        type="monotone"
                        dataKey={() => optimalPoint.value}
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={{ fill: '#10b981', r: 6 }}
                        name="最优点"
                      />
                    )}

                    {/* Metric lines */}
                    {selectedMetrics.map(metric => {
                      const metricConfig = METRICS.find(m => m.value === metric)
                      return (
                        <Line
                          key={metric}
                          type="monotone"
                          dataKey={metric}
                          stroke={metricConfig?.color}
                          strokeWidth={2}
                          dot={false}
                          name={metricConfig?.label}
                        />
                      )
                    })}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Optimal Point Info */}
              {optimalPoint && (
                <div className={`mt-4 p-3 rounded-lg ${
                  isDark ? 'bg-gray-700' : 'bg-gray-100'
                }`}>
                  <h4 className={`text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    最优参数值: {optimalPoint.value}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>收益率:</span>
                      <span className={`ml-2 ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                        {(optimalPoint.return * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div>
                      <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>夏普比率:</span>
                      <span className={`ml-2 ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                        {optimalPoint.sharpe.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>最大回撤:</span>
                      <span className={`ml-2 ${isDark ? 'text-red-400' : 'text-red-600'}`}>
                        {(optimalPoint.drawdown * 100).toFixed(2)}%
                      </span>
                    </div>
                    {optimalPoint.winRate && (
                      <div>
                        <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>胜率:</span>
                        <span className={`ml-2 ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                          {(optimalPoint.winRate * 100).toFixed(2)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Heatmap for Two-Parameter Analysis */}
          {showHeatmap && heatmapData && heatmapConfig && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                双参数热力图
              </h3>

              <div className="mb-4">
                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  X轴: {heatmapConfig.xParam} | Y轴: {heatmapConfig.yParam} | 指标: {
                    METRICS.find(m => m.value === heatmapConfig.metric)?.label
                  }
                </span>
              </div>

              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <XAxis
                      type="number"
                      dataKey="x"
                      name={heatmapConfig.xParam}
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name={heatmapConfig.yParam}
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                    />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter
                      name="参数组合"
                      data={heatmapData}
                      fill="#8884d8"
                    >
                      {heatmapData.map((entry, index) => {
                        const metric = heatmapConfig.metric
                        const values = heatmapData.map(d => d.z)
                        const min = Math.min(...values)
                        const max = Math.max(...values)
                        return (
                          <Cell
                            key={`cell-${index}`}
                            fill={getHeatmapColor(entry.z, min, max)}
                          />
                        )
                      })}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {showRecommendations && recommendations && recommendations.length > 0 && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                参数建议
              </h3>

              <div className="space-y-3">
                {recommendations.map((rec, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`font-medium ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                        {rec.parameter}: {rec.suggestion}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        rec.impact === 'high'
                          ? 'bg-red-100 text-red-700'
                          : rec.impact === 'medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                      }`}>
                        {rec.impact === 'high' ? '高' :
                         rec.impact === 'medium' ? '中' : '低'}影响
                      </span>
                    </div>
                    <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      {rec.reason}
                      {rec.expectedImprovement && (
                        <span className="ml-2 font-medium text-green-600">
                          (预期改善: {(rec.expectedImprovement * 100).toFixed(2)}%)
                        </span>
                      )}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default SensitivityAnalysis