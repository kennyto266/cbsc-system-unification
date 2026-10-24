import React, { useState, useEffect, useMemo } from 'react'
import { Card, Select, Space, Spin, Alert, Button, Tooltip, Switch, InputNumber, Row, Col } from 'antd'
import { Line, Area, Bar } from '@ant-design/plots'
import {
  SettingOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
// import { useWebSocket } from '../../../hooks/useWebSocket'

const { Option } = Select

// Technical indicators configuration
const INDICATOR_CONFIGS = {
  RSI: {
    name: 'RSI相对强弱指标',
    description: '测量价格动量和变化速度',
    defaultParams: { period: 14, overbought: 70, oversold: 30 },
    range: [0, 100],
    lines: [
      { key: 'value', name: 'RSI', color: '#1890ff' },
      { key: 'overbought', name: '超买线', color: '#ff4d4f', dash: true },
      { key: 'oversold', name: '超卖线', color: '#52c41a', dash: true }
    ]
  },
  MACD: {
    name: 'MACD指标',
    description: '趋势和动量指标',
    defaultParams: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    lines: [
      { key: 'macd', name: 'MACD', color: '#1890ff' },
      { key: 'signal', name: 'Signal', color: '#ff7a45' },
      { key: 'histogram', name: 'Histogram', color: '#52c41a', type: 'bar' }
    ]
  },
  BOLL: {
    name: '布林带',
    description: '价格通道和波动率指标',
    defaultParams: { period: 20, stdDev: 2 },
    lines: [
      { key: 'upper', name: '上轨', color: '#ff4d4f' },
      { key: 'middle', name: '中轨', color: '#1890ff' },
      { key: 'lower', name: '下轨', color: '#52c41a' },
      { key: 'price', name: '价格', color: '#722ed1' }
    ]
  },
  KDJ: {
    name: 'KDJ随机指标',
    description: '超买超卖和动量指标',
    defaultParams: { kPeriod: 9, dPeriod: 3, jPeriod: 3 },
    range: [0, 100],
    lines: [
      { key: 'k', name: 'K', color: '#1890ff' },
      { key: 'd', name: 'D', color: '#ff7a45' },
      { key: 'j', name: 'J', color: '#52c41a' }
    ]
  },
  MA: {
    name: '移动平均线',
    description: '趋势跟踪指标',
    defaultParams: { periods: [5, 10, 20, 50, 200] },
    lines: [
      { key: 'ma5', name: 'MA5', color: '#ff4d4f' },
      { key: 'ma10', name: 'MA10', color: '#ff7a45' },
      { key: 'ma20', name: 'MA20', color: '#1890ff' },
      { key: 'ma50', name: 'MA50', color: '#52c41a' },
      { key: 'ma200', name: 'MA200', color: '#722ed1' }
    ]
  },
  VOLUME: {
    name: '成交量',
    description: '市场活跃度指标',
    defaultParams: {},
    type: 'bar',
    lines: [
      { key: 'volume', name: '成交量', color: '#1890ff' },
      { key: 'maVolume', name: '量均线', color: '#ff7a45', dash: true }
    ]
  }
}

// Time frame options
const TIME_FRAMES = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '30m', label: '30分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
  { value: '1w', label: '1周' }
]

// Common symbols
const COMMON_SYMBOLS = [
  'BTC/USDT',
  'ETH/USDT',
  'BNB/USDT',
  'ADA/USDT',
  'SOL/USDT',
  'XRP/USDT',
  'DOT/USDT',
  'DOGE/USDT',
  'AVAX/USDT',
  'MATIC/USDT'
]

interface TechnicalIndicatorWidgetProps {
  indicator?: string
  symbol?: string
  timeFrame?: string
  params?: Record<string, any>
  autoUpdate?: boolean
  showSettings?: boolean
  onConfigChange?: (config: any) => void
}

// Generate mock data for demonstration
const generateMockData = (indicator: string, params: any, count: number = 100) => {
  const data = []
  const now = Date.now()
  const config = INDICATOR_CONFIGS[indicator as keyof typeof INDICATOR_CONFIGS]

  for (let i = count; i >= 0; i--) {
    const timestamp = now - i * 60000 // 1 minute intervals
    const baseValue = 100 + Math.sin(i * 0.1) * 20
    const randomFactor = (Math.random() - 0.5) * 10

    const point: any = {
      timestamp,
      time: new Date(timestamp).toLocaleTimeString(),
      date: new Date(timestamp).toLocaleDateString()
    }

    switch (indicator) {
      case 'RSI':
        point.value = Math.max(0, Math.min(100, baseValue + randomFactor))
        point.overbought = config.defaultParams.overbought
        point.oversold = config.defaultParams.oversold
        break

      case 'MACD':
        point.macd = Math.sin(i * 0.05) * 2
        point.signal = Math.sin(i * 0.05 - 0.5) * 1.8
        point.histogram = point.macd - point.signal
        break

      case 'BOLL':
        const price = 100 + Math.sin(i * 0.1) * 10
        const stdDev = config.defaultParams.stdDev
        point.middle = price
        point.upper = price + stdDev * 5
        point.lower = price - stdDev * 5
        point.price = price + (Math.random() - 0.5) * 2
        break

      case 'KDJ':
        point.k = Math.max(0, Math.min(100, baseValue + randomFactor))
        point.d = Math.max(0, Math.min(100, baseValue + randomFactor * 0.8))
        point.j = Math.max(0, Math.min(100, baseValue + randomFactor * 1.2))
        break

      case 'MA':
        const maPrice = 100 + Math.sin(i * 0.1) * 10
        config.defaultParams.periods.forEach((period: number) => {
          point[`ma${period}`] = maPrice + (Math.random() - 0.5) * (period / 10)
        })
        break

      case 'VOLUME':
        point.volume = Math.max(0, 1000000 + randomFactor * 500000)
        point.maVolume = 1000000 + Math.sin(i * 0.1) * 200000
        break

      default:
        point.value = baseValue + randomFactor
    }

    data.push(point)
  }

  return data
}

const TechnicalIndicatorWidget: React.FC<TechnicalIndicatorWidgetProps> = ({
  indicator = 'RSI',
  symbol = 'BTC/USDT',
  timeFrame = '1h',
  params = {},
  autoUpdate = true,
  showSettings = true,
  onConfigChange
}) => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState({
    indicator,
    symbol,
    timeFrame,
    params: { ...INDICATOR_CONFIGS[indicator as keyof typeof INDICATOR_CONFIGS]?.defaultParams, ...params },
    autoUpdate
  })
  const [showConfigPanel, setShowConfigPanel] = useState(false)

  // const { isConnected } = useWebSocket()
  const isConnected = false // Mock WebSocket status

  // Fetch indicator data
  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // In real implementation, this would fetch from API
      // const response = await fetch(`/api/technical-indicators/${config.indicator}?symbol=${config.symbol}&timeframe=${config.timeFrame}&params=${JSON.stringify(config.params)}`)
      // const result = await response.json()

      // Mock data for demonstration
      await new Promise(resolve => setTimeout(resolve, 500))
      const mockData = generateMockData(config.indicator, config.params)
      setData(mockData)

    } catch (err) {
      setError('加载指标数据失败')
      console.error('Failed to fetch indicator data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchData()
  }, [config.indicator, config.symbol, config.timeFrame, JSON.stringify(config.params)])

  // Auto update with WebSocket
  useEffect(() => {
    if (!autoUpdate || !isConnected) return

    const interval = setInterval(fetchData, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [autoUpdate, isConnected, config])

  // Update config when props change
  useEffect(() => {
    const newConfig = {
      indicator,
      symbol,
      timeFrame,
      params: { ...INDICATOR_CONFIGS[indicator as keyof typeof INDICATOR_CONFIGS]?.defaultParams, ...params },
      autoUpdate
    }
    setConfig(newConfig)
  }, [indicator, symbol, timeFrame, params, autoUpdate])

  // Handle config change
  const handleConfigChange = (newConfig: any) => {
    setConfig(prev => ({ ...prev, ...newConfig }))
    if (onConfigChange) {
      onConfigChange({ ...config, ...newConfig })
    }
  }

  // Get current indicator configuration
  const currentIndicatorConfig = INDICATOR_CONFIGS[config.indicator as keyof typeof INDICATOR_CONFIGS]

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!currentIndicatorConfig) return []

    return data.map(point => {
      const chartPoint: any = {
        time: point.time,
        date: point.date
      }

      currentIndicatorConfig.lines.forEach((line: any) => {
        if (point[line.key] !== undefined) {
          chartPoint[line.name] = point[line.key]
        }
      })

      return chartPoint
    })
  }, [data, currentIndicatorConfig])

  // Chart configuration
  const chartConfig = useMemo(() => {
    if (!currentIndicatorConfig) return {}

    const baseConfig = {
      data: chartData,
      xField: 'time',
      smooth: true,
      animation: {
        appear: {
          animation: 'path-in',
          duration: 1000
        }
      },
      tooltip: {
        formatter: (datum: any) => {
          const values = currentIndicatorConfig.lines.map((line: any) =>
            `${line.name}: ${datum[line.name]?.toFixed(2)}`
          ).join('\n')
          return `时间: ${datum.time}\n${values}`
        }
      },
      legend: {
        position: 'top' as const
      }
    }

    // Configure based on indicator type
    if (currentIndicatorConfig.type === 'bar') {
      return {
        ...baseConfig,
        yField: currentIndicatorConfig.lines[0].name,
        seriesField: 'type',
        color: currentIndicatorConfig.lines.map((line: any) => line.color)
      }
    } else {
      return {
        ...baseConfig,
        yAxis: {
          min: currentIndicatorConfig.range?.[0],
          max: currentIndicatorConfig.range?.[1]
        }
      }
    }
  }, [chartData, currentIndicatorConfig])

  // Render chart based on indicator type
  const renderChart = () => {
    if (!currentIndicatorConfig) return null

    switch (currentIndicatorConfig.type) {
      case 'bar':
        return <Bar {...chartConfig} />
      case 'area':
        return <Area {...chartConfig} />
      default:
        return <Line {...chartConfig} />
    }
  }

  // Render parameter controls
  const renderParameterControls = () => {
    if (!currentIndicatorConfig || !showConfigPanel) return null

    const { defaultParams } = currentIndicatorConfig

    return (
      <div className="parameter-controls p-4 bg-gray-50 dark:bg-gray-800 space-y-3">
        <Row gutter={[16, 8]}>
          {Object.entries(defaultParams).map(([key, value]) => (
            <Col span={12} key={key}>
              <div className="flex items-center justify-between">
                <span className="text-sm">{key}:</span>
                <InputNumber
                  size="small"
                  value={config.params[key] || value}
                  onChange={(newVal) => handleConfigChange({
                    params: { ...config.params, [key]: newVal }
                  })}
                  min={key.includes('period') ? 1 : 0}
                  max={key.includes('period') ? 200 : 100}
                />
              </div>
            </Col>
          ))}
        </Row>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin size="large" tip="加载指标数据..." />
      </div>
    )
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" icon={<ReloadOutlined />} onClick={fetchData}>
            重试
          </Button>
        }
      />
    )
  }

  return (
    <div className="technical-indicator-widget h-full flex flex-col">
      {/* Header */}
      <div className="widget-header p-3 border-b dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h4 className="m-0 font-medium">{currentIndicatorConfig?.name}</h4>
            <Tooltip title={currentIndicatorConfig?.description}>
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          </div>

          <Space size="small">
            {/* Indicator selector */}
            {showSettings && (
              <Select
                value={config.indicator}
                onChange={(value) => handleConfigChange({ indicator: value })}
                size="small"
                style={{ width: 120 }}
              >
                {Object.entries(INDICATOR_CONFIGS).map(([key, cfg]) => (
                  <Option key={key} value={key}>{cfg.name}</Option>
                ))}
              </Select>
            )}

            {/* Symbol selector */}
            {showSettings && (
              <Select
                value={config.symbol}
                onChange={(value) => handleConfigChange({ symbol: value })}
                size="small"
                style={{ width: 120 }}
                showSearch
                filterOption={(input, option) =>
                  option?.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
              >
                {COMMON_SYMBOLS.map(symbol => (
                  <Option key={symbol} value={symbol}>{symbol}</Option>
                ))}
              </Select>
            )}

            {/* Time frame selector */}
            {showSettings && (
              <Select
                value={config.timeFrame}
                onChange={(value) => handleConfigChange({ timeFrame: value })}
                size="small"
                style={{ width: 80 }}
              >
                {TIME_FRAMES.map(tf => (
                  <Option key={tf.value} value={tf.value}>{tf.label}</Option>
                ))}
              </Select>
            )}

            {/* Auto update toggle */}
            <Tooltip title="自动更新">
              <Switch
                size="small"
                checked={config.autoUpdate}
                onChange={(checked) => handleConfigChange({ autoUpdate: checked })}
              />
            </Tooltip>

            {/* Settings toggle */}
            {showSettings && (
              <Tooltip title="参数设置">
                <Button
                  type="text"
                  size="small"
                  icon={<SettingOutlined />}
                  onClick={() => setShowConfigPanel(!showConfigPanel)}
                />
              </Tooltip>
            )}

            {/* Refresh */}
            <Tooltip title="刷新">
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined />}
                onClick={fetchData}
                loading={loading}
              />
            </Tooltip>

            {/* Fullscreen */}
            <Tooltip title="全屏">
              <Button
                type="text"
                size="small"
                icon={<FullscreenOutlined />}
              />
            </Tooltip>
          </Space>
        </div>
      </div>

      {/* Parameter controls */}
      {renderParameterControls()}

      {/* Chart */}
      <div className="chart-container flex-1 min-h-0">
        {renderChart()}
      </div>

      {/* Footer */}
      <div className="widget-footer p-2 border-t dark:border-gray-700 text-xs text-gray-500 flex items-center justify-between">
        <span>{config.symbol} - {config.timeFrame}</span>
        <Space size="small">
          <span>数据点: {data.length}</span>
          {isConnected && <span className="text-green-500">● 实时</span>}
        </Space>
      </div>
    </div>
  )
}

export default TechnicalIndicatorWidget