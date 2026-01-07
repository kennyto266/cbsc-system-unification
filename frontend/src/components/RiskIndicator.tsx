/**
 * Risk Indicator Component
 * 風險指標組件
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Gauge,
  Treemap
} from 'recharts'
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  Zap,
  Target,
  Eye,
  Bell,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Settings,
  Download,
  Info
} from 'lucide-react'

// Chart color categories
const CHART_CATEGORIES = {
  volatility: { color: '#8b5cf6' },
  drawdown: { color: '#ef4444' },
  var: { color: '#3b82f6' }
} as const

// Types
interface RiskMetric {
  timestamp: string
  value: number
  threshold?: number
  category: 'volatility' | 'drawdown' | 'correlation' | 'exposure' | 'var' | 'concentration'
}

interface RiskAlert {
  id: string
  level: 'low' | 'medium' | 'high' | 'critical'
  type: string
  message: string
  timestamp: string
  acknowledged: boolean
  action?: string
}

interface RiskLimits {
  maxDrawdown: number
  maxVaR: number
  maxPositionSize: number
  maxLeverage: number
  maxSectorExposure: number
  stopLossThreshold: number
}

interface RiskScore {
  overall: number
  volatility: number
  liquidity: number
  concentration: number
  market: number
  credit: number
  operational: number
}

interface PositionRisk {
  symbol: string
  position: number
  marketValue: number
  weight: number
  risk: number
  contribution: number
}

interface RiskIndicatorProps {
  strategyId?: string
  className?: string
  data?: {
    metrics: RiskMetric[]
    alerts: RiskAlert[]
    limits: RiskLimits
    riskScore: RiskScore
    positions: PositionRisk[]
    stressTest: {
      scenario: string
      impact: number
      probability: number
    }[]
  }
  refreshInterval?: number
  showAlerts?: boolean
  showStressTest?: boolean
  showPositions?: boolean
  autoRefresh?: boolean
  onAlertAcknowledge?: (alertId: string) => void
  onRiskLimitUpdate?: (limits: RiskLimits) => void
}

const RISK_LEVELS = {
  low: { color: '#10b981', label: '低風險', icon: Shield },
  medium: { color: '#f59e0b', label: '中風險', icon: AlertTriangle },
  high: { color: '#ef4444', label: '高風險', icon: TrendingUp },
  critical: { color: '#dc2626', label: '嚴重風險', icon: Zap }
}

const RISK_CATEGORIES = {
  volatility: { label: '波動率', color: '#3b82f6' },
  drawdown: { label: '回撤', color: '#ef4444' },
  correlation: { label: '相關性', color: '#8b5cf6' },
  exposure: { label: '曝險', color: '#f59e0b' },
  var: { label: 'VaR', color: '#ec4899' },
  concentration: { label: '集中度', color: '#10b981' }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value?.toFixed?.(2) ?? entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

const RiskGauge: React.FC<{
  value: number
  max: number
  thresholds: { warning: number; critical: number }
  label: string
  color?: string
}> = ({ value, max, thresholds, label, color = '#3b82f6' }) => {
  const percentage = (value / max) * 100
  const angle = (percentage * 180) / 100 - 90

  const getColor = () => {
    if (value >= thresholds.critical) return '#ef4444'
    if (value >= thresholds.warning) return '#f59e0b'
    return '#10b981'
  }

  return (
    <div className="text-center">
      <div className="relative w-32 h-16 mx-auto">
        <svg viewBox="0 0 120 60" className="w-full h-full">
          {/* Background arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 110 50"
            stroke="#e5e7eb"
            strokeWidth="8"
            fill="none"
          />
          {/* Colored arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 110 50"
            stroke={getColor()}
            strokeWidth="8"
            fill="none"
            strokeDasharray={`${(percentage / 100) * 125.66} 125.66`}
            className="transition-all duration-500"
          />
          {/* Pointer */}
          <line
            x1="60"
            y1="50"
            x2="60"
            y2="15"
            stroke="#374151"
            strokeWidth="2"
            transform={`rotate(${angle} 60 50)`}
            className="transition-transform duration-500"
          />
          {/* Center dot */}
          <circle cx="60" cy="50" r="3" fill="#374151" />
        </svg>
      </div>
      <p className="text-sm font-medium text-gray-600 mt-2">{label}</p>
      <p className="text-xl font-bold" style={{ color: getColor() }}>
        {value.toFixed(1)}
      </p>
    </div>
  )
}

const AlertCard: React.FC<{
  alert: RiskAlert
  onAcknowledge?: (id: string) => void
}> = ({ alert, onAcknowledge }) => {
  const levelConfig = RISK_LEVELS[alert.level]
  const Icon = levelConfig.icon

  return (
    <div className={`p-4 rounded-lg border-l-4 bg-${
      alert.level === 'critical' ? 'red' :
      alert.level === 'high' ? 'orange' :
      alert.level === 'medium' ? 'yellow' : 'green'
    }-50 border-${
      alert.level === 'critical' ? 'red' :
      alert.level === 'high' ? 'orange' :
      alert.level === 'medium' ? 'yellow' : 'green'
    }-400`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <Icon className={`w-5 h-5 mt-0.5 text-${levelConfig.color}-500`} />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-gray-900">{alert.type}</h4>
            <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
            {alert.action && (
              <p className="text-sm text-blue-600 mt-2">建議操作: {alert.action}</p>
            )}
            <p className="text-xs text-gray-500 mt-2">
              {new Date(alert.timestamp).toLocaleString('zh-CN')}
            </p>
          </div>
        </div>
        {!alert.acknowledged && onAcknowledge && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            確認
          </button>
        )}
      </div>
    </div>
  )
}

export default function RiskIndicator({
  strategyId,
  className = '',
  data,
  refreshInterval = 30000,
  showAlerts = true,
  showStressTest = true,
  showPositions = true,
  autoRefresh = false,
  onAlertAcknowledge,
  onRiskLimitUpdate
}: RiskIndicatorProps) {
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    alerts: true,
    limits: false,
    positions: false,
    stressTest: false
  })
  const [isLoading, setIsLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  // Mock data generation
  const mockData = useMemo(() => {
    // Check if data has actual content (is non-empty object)
    if (data && typeof data === 'object' && Object.keys(data).length > 0) {
      return data
    }

    // Generate mock risk metrics
    const metrics: RiskMetric[] = []
    const now = new Date()

    for (let i = 0; i < 30; i++) {
      const timestamp = new Date(now.getTime() - (29 - i) * 24 * 60 * 60 * 1000)

      metrics.push(
        {
          timestamp: timestamp.toISOString(),
          value: 10 + Math.random() * 15,
          category: 'volatility'
        },
        {
          timestamp: timestamp.toISOString(),
          value: Math.random() * 8,
          category: 'drawdown'
        },
        {
          timestamp: timestamp.toISOString(),
          value: 0.3 + Math.random() * 0.4,
          category: 'correlation'
        },
        {
          timestamp: timestamp.toISOString(),
          value: 50 + Math.random() * 50,
          category: 'exposure'
        },
        {
          timestamp: timestamp.toISOString(),
          value: 1 + Math.random() * 3,
          category: 'var'
        },
        {
          timestamp: timestamp.toISOString(),
          value: Math.random() * 30,
          category: 'concentration'
        }
      )
    }

    const alerts: RiskAlert[] = [
      {
        id: '1',
        level: 'high',
        type: '回撤警告',
        message: '當前回撤水平為 7.5%，接近風險閾值',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        acknowledged: false,
        action: '考慮減少倉位或調整策略參數'
      },
      {
        id: '2',
        level: 'medium',
        type: '波動率增加',
        message: '市場波動率顯著上升，建議密切監控',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        acknowledged: true
      },
      {
        id: '3',
        level: 'low',
        type: '集中度提醒',
        message: '單一持倉比例略高，可考慮分散投資',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        acknowledged: false
      }
    ]

    const limits: RiskLimits = {
      maxDrawdown: 15,
      maxVaR: 5,
      maxPositionSize: 20,
      maxLeverage: 2,
      maxSectorExposure: 30,
      stopLossThreshold: 10
    }

    const riskScore: RiskScore = {
      overall: 65,
      volatility: 70,
      liquidity: 85,
      concentration: 60,
      market: 55,
      credit: 90,
      operational: 95
    }

    const positions: PositionRisk[] = [
      { symbol: 'HKD/USD', position: 1000000, marketValue: 1000000, weight: 25, risk: 12.5, contribution: 15.2 },
      { symbol: 'HSI', position: 50, marketValue: 1500000, weight: 37.5, risk: 18.8, contribution: 28.5 },
      { symbol: 'RMB/USD', position: 800000, marketValue: 800000, weight: 20, risk: 8.2, contribution: 10.1 },
      { symbol: 'Bond ETF', position: 200000, marketValue: 700000, weight: 17.5, risk: 3.5, contribution: 6.2 }
    ]

    const stressTest = [
      { scenario: '2008金融危機', impact: -25, probability: 5 },
      { scenario: '2020疫情', impact: -15, probability: 10 },
      { scenario: '利率急升', impact: -12, probability: 15 },
      { scenario: '地產泡沫', impact: -20, probability: 8 },
      { scenario: '黑天鵝事件', impact: -35, probability: 2 }
    ]

    return {
      metrics,
      alerts,
      limits,
      riskScore,
      positions,
      stressTest
    }
  }, [data])

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

  const handleAlertAcknowledge = (alertId: string) => {
    if (onAlertAcknowledge) {
      onAlertAcknowledge(alertId)
    }
  }

  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(handleRefresh, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  const { metrics = [], alerts = [], limits = [], riskScore = { overall: 50 }, positions = [], stressTest = [] } = mockData

  // Calculate current risk values
  const latestMetrics = useMemo(() => {
    const latest: Record<string, number> = {}
    metrics.forEach(metric => {
      if (!latest[metric.category] || new Date(metric.timestamp) > new Date(latest[metric.category])) {
        latest[metric.category] = metric.value
      }
    })
    return latest
  }, [metrics])

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged)
  const riskLevel = riskScore?.overall >= 80 ? 'low' :
                   riskScore?.overall >= 60 ? 'medium' :
                   riskScore?.overall >= 40 ? 'high' : 'critical'

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">風險指標監控</h2>
            <p className="mt-1 text-sm text-gray-600">
              最後更新: {lastRefresh.toLocaleString('zh-CN')}
            </p>
          </div>
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center ${
              riskLevel === 'low' ? 'bg-green-100 text-green-800' :
              riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              riskLevel === 'high' ? 'bg-orange-100 text-orange-800' :
              'bg-red-100 text-red-800'
            }`}>
              {React.createElement(RISK_LEVELS[riskLevel].icon, { className: "w-4 h-4 mr-1" })}
              {RISK_LEVELS[riskLevel].label}
            </div>
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              aria-label="refresh"
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Risk Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overall Risk Score */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">整體風險評分</h3>
          <div className="text-center">
            <div className="relative inline-flex items-center justify-center">
              <div className="w-32 h-32 rounded-full border-8 border-gray-200"></div>
              <div
                className="absolute inset-0 w-32 h-32 rounded-full border-8 border-transparent border-t-blue-500 border-r-blue-500"
                style={{
                  transform: `rotate(${(riskScore.overall / 100) * 360 - 90}deg)`,
                  transition: 'transform 0.5s ease-in-out'
                }}
              ></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div>
                  <p className="text-3xl font-bold text-gray-900">{riskScore.overall}</p>
                  <p className="text-sm text-gray-600">分</p>
                </div>
              </div>
            </div>
            <p className="mt-4 text-sm text-gray-600">
              {riskScore.overall >= 80 ? '風險水平良好' :
               riskScore.overall >= 60 ? '風險水平中等' :
               riskScore.overall >= 40 ? '風險水平偏高' : '風險水平嚴重'}
            </p>
          </div>
        </div>

        {/* Risk Gauges */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">關鍵風險指標</h3>
          <div className="grid grid-cols-2 gap-4">
            <RiskGauge
              value={latestMetrics.drawdown || 0}
              max={limits.maxDrawdown}
              thresholds={{ warning: limits.maxDrawdown * 0.7, critical: limits.maxDrawdown * 0.9 }}
              label="回撤 (%)"
            />
            <RiskGauge
              value={latestMetrics.var || 0}
              max={limits.maxVaR}
              thresholds={{ warning: limits.maxVaR * 0.7, critical: limits.maxVaR * 0.9 }}
              label="VaR (%)"
            />
            <RiskGauge
              value={latestMetrics.volatility || 0}
              max={25}
              thresholds={{ warning: 15, critical: 20 }}
              label="波動率 (%)"
            />
            <RiskGauge
              value={latestMetrics.concentration || 0}
              max={40}
              thresholds={{ warning: 25, critical: 35 }}
              label="集中度 (%)"
            />
          </div>
        </div>

        {/* Risk Alerts Summary */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">風險預警</h3>
            <div className="relative">
              <Bell className="w-5 h-5 text-gray-600" />
              {unacknowledgedAlerts.length > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {unacknowledgedAlerts.slice(0, 3).map(alert => (
              <div key={alert.id} className="flex items-center space-x-2 text-sm">
                {React.createElement(RISK_LEVELS[alert.level].icon, {
                  className: `w-4 h-4 text-${RISK_LEVELS[alert.level].color}-500`
                })}
                <span className="text-gray-700 truncate">{alert.message}</span>
              </div>
            ))}
            {unacknowledgedAlerts.length === 0 && (
              <p className="text-sm text-gray-500">暫無未確認預警</p>
            )}
            {unacknowledgedAlerts.length > 3 && (
              <p className="text-sm text-blue-600">還有 {unacknowledgedAlerts.length - 3} 條預警...</p>
            )}
          </div>
        </div>
      </div>

      {/* Risk Metrics Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">風險指標趨勢</h3>
            <button
              onClick={() => toggleSection('overview')}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
            >
              {expandedSections.overview ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>
          </div>
        </div>

        {expandedSections.overview && (
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.filter(m => m.category === 'volatility').slice(0, 30)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                  }}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {Object.entries(RISK_CATEGORIES).map(([key, config]) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey="value"
                    name={config.label}
                    stroke={config.color}
                    strokeWidth={2}
                    dot={false}
                    data={metrics.filter(m => m.category === key).slice(0, 30)}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Risk Alerts */}
      {showAlerts && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">風險預警詳情</h3>
              <button
                onClick={() => toggleSection('alerts')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.alerts ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.alerts && (
            <div className="p-6 space-y-4">
              {alerts.map(alert => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onAcknowledge={handleAlertAcknowledge}
                />
              ))}
              {alerts.length === 0 && (
                <p className="text-center text-gray-500 py-8">暫無風險預警</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Position Risk */}
      {showPositions && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">持倉風險分析</h3>
              <button
                onClick={() => toggleSection('positions')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.positions ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.positions && (
            <div className="p-6">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        持倉
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        市值
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        權重
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        風險
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        貢獻度
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {positions.map((position, index) => (
                      <tr key={position.symbol}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {position.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ¥{position.marketValue.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {position.weight.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            position.risk > 15 ? 'bg-red-100 text-red-800' :
                            position.risk > 10 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {position.risk.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {position.contribution.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Position Risk Chart */}
              <div className="mt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={positions}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="symbol" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="weight" name="權重" fill={CHART_CATEGORIES.volatility.color} />
                    <Bar dataKey="risk" name="風險" fill={CHART_CATEGORIES.drawdown.color} />
                    <Bar dataKey="contribution" name="貢獻度" fill={CHART_CATEGORIES.var.color} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stress Test */}
      {showStressTest && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">壓力測試</h3>
              <button
                onClick={() => toggleSection('stressTest')}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {expandedSections.stressTest ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {expandedSections.stressTest && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stressTest.map((scenario, index) => (
                  <div key={scenario.scenario} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">{scenario.scenario}</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">預期影響:</span>
                        <span className={`text-sm font-medium ${
                          scenario.impact > -10 ? 'text-green-600' :
                          scenario.impact > -20 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {scenario.impact.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">發生概率:</span>
                        <span className="text-sm font-medium">{scenario.probability}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className={`h-2 rounded-full ${
                            scenario.probability > 15 ? 'bg-red-500' :
                            scenario.probability > 10 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${scenario.probability}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-blue-900">風險提示</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      壓力測試結果基於歷史數據模擬，實際市場表現可能有所不同。建議定期審查風險管理策略。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}