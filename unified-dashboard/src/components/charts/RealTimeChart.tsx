import React, { useEffect, useRef, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  ResponsiveContainer,
  ReferenceLine,
  Brush,
  Legend,
  ComposedChart
} from 'recharts'
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  Zap,
  BarChart3,
  LineChart as LineChartIcon
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Switch } from '../ui/switch'
import { cn } from '../../lib/utils'
import { useWebSocket } from '../../hooks/useWebSocket'

interface DataPoint {
  timestamp: number
  value: number
  volume?: number
  high?: number
  low?: number
  open?: number
  close?: number
  [key: string]: any
}

interface RealTimeChartProps {
  symbol: string
  timeframe: string
  type: 'line' | 'area' | 'bar' | 'candlestick' | 'composed'
  indicators?: string[]
  showVolume?: boolean
  showGrid?: boolean
  height?: number
  className?: string
}

const chartColors = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  grid: '#e5e7eb',
  text: '#6b7280'
}

const timeFrames = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
  { value: '1w', label: '1周' }
]

const indicatorsList = [
  { value: 'sma', label: 'SMA', color: chartColors.secondary },
  { value: 'ema', label: 'EMA', color: chartColors.warning },
  { value: 'rsi', label: 'RSI', color: chartColors.success },
  { value: 'macd', label: 'MACD', color: chartColors.info },
  { value: 'bb', label: 'Bollinger Bands', color: chartColors.danger }
]

const RealTimeChart: React.FC<RealTimeChartProps> = ({
  symbol,
  timeframe,
  type = 'line',
  indicators = [],
  showVolume = true,
  showGrid = true,
  height = 400,
  className
}) => {
  const [data, setData] = useState<DataPoint[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isRealTime, setIsRealTime] = useState(true)
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe)
  const [selectedIndicators, setSelectedIndicators] = useState(indicators)
  const [isLoading, setIsLoading] = useState(false)

  // WebSocket connection for real-time data
  const { lastMessage, connectionStatus } = useWebSocket(
    `ws://localhost:3004/ws/chart/${symbol}?timeframe=${selectedTimeframe}`
  )

  // Generate initial historical data
  useEffect(() => {
    const generateHistoricalData = () => {
      const points: DataPoint[] = []
      const now = Date.now()
      let basePrice = 43000

      for (let i = 500; i >= 0; i--) {
        const timestamp = now - i * 60000 // 1 minute intervals
        const randomChange = (Math.random() - 0.5) * 100
        basePrice += randomChange

        const point: DataPoint = {
          timestamp,
          value: basePrice,
          high: basePrice + Math.random() * 50,
          low: basePrice - Math.random() * 50,
          open: basePrice + (Math.random() - 0.5) * 20,
          close: basePrice,
          volume: Math.random() * 1000000
        }

        // Add indicators
        selectedIndicators.forEach(indicator => {
          if (indicator === 'sma') {
            point.sma = basePrice + (Math.random() - 0.5) * 30
          } else if (indicator === 'ema') {
            point.ema = basePrice + (Math.random() - 0.5) * 25
          } else if (indicator === 'rsi') {
            point.rsi = 30 + Math.random() * 40
          }
        })

        points.push(point)
      }

      return points
    }

    setIsLoading(true)
    const historicalData = generateHistoricalData()
    setData(historicalData)
    setIsLoading(false)
  }, [symbol, selectedTimeframe, selectedIndicators])

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage && isRealTime) {
      try {
        const newData = JSON.parse(lastMessage.data)
        setData(prevData => {
          const updatedData = [...prevData, newData]
          // Keep only last 500 points
          if (updatedData.length > 500) {
            return updatedData.slice(-500)
          }
          return updatedData
        })
      } catch (error) {
        console.error('Error parsing WebSocket data:', error)
      }
    }
  }, [lastMessage, isRealTime])

  // Connection status
  useEffect(() => {
    setIsConnected(connectionStatus === 'open')
  }, [connectionStatus])

  // Format data for display
  const formattedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      time: new Date(point.timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }))
  }, [data])

  // Calculate price change
  const priceChange = useMemo(() => {
    if (data.length < 2) return { value: 0, percentage: 0, direction: 'neutral' as const }
    const current = data[data.length - 1].value
    const previous = data[data.length - 2].value
    const value = current - previous
    const percentage = (value / previous) * 100
    const direction = value > 0 ? 'up' : value < 0 ? 'down' : 'neutral'
    return { value, percentage, direction }
  }, [data])

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Card className="shadow-lg border-0 bg-background/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-xs text-muted-foreground mb-2">
              {payload[0].payload.time}
            </div>
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex items-center justify-between space-x-4">
                <div className="flex items-center space-x-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm font-medium">{entry.name}</span>
                </div>
                <span className="text-sm font-mono">
                  {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
                </span>
              </div>
            ))}
            {payload[0].payload.volume && (
              <div className="mt-2 pt-2 border-t">
                <div className="flex items-center justify-between space-x-4">
                  <span className="text-xs text-muted-foreground">成交量</span>
                  <span className="text-xs font-mono">
                    {(payload[0].payload.volume / 1000000).toFixed(2)}M
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )
    }
    return null
  }

  const renderChart = () => {
    const commonProps = {
      data: formattedData,
      margin: { top: 5, right: 5, left: 5, bottom: 5 }
    }

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />}
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
              domain={['dataMin - 100', 'dataMax + 100']}
            />
            <Tooltip content={<CustomTooltip />} />
            {selectedIndicators.includes('bb') && (
              <>
                <ReferenceLine y={data[data.length - 1]?.sma + 50} stroke={chartColors.danger} strokeDasharray="3 3" />
                <ReferenceLine y={data[data.length - 1]?.sma - 50} stroke={chartColors.danger} strokeDasharray="3 3" />
              </>
            )}
            {selectedIndicators.includes('sma') && (
              <Line
                type="monotone"
                dataKey="sma"
                stroke={chartColors.secondary}
                strokeWidth={2}
                dot={false}
              />
            )}
            {selectedIndicators.includes('ema') && (
              <Line
                type="monotone"
                dataKey="ema"
                stroke={chartColors.warning}
                strokeWidth={2}
                dot={false}
              />
            )}
            <Area
              type="monotone"
              dataKey="value"
              stroke={chartColors.primary}
              fill={chartColors.primary}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </AreaChart>
        )

      case 'bar':
        return (
          <ComposedChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />}
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <YAxis
              yAxisId="price"
              orientation="right"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <YAxis
              yAxisId="volume"
              orientation="left"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
              hide={!showVolume}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              yAxisId="price"
              dataKey="value"
              fill={chartColors.primary}
              opacity={0.8}
            />
            {selectedIndicators.includes('sma') && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="sma"
                stroke={chartColors.secondary}
                strokeWidth={2}
                dot={false}
              />
            )}
            {showVolume && (
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill={chartColors.text}
                opacity={0.3}
              />
            )}
          </ComposedChart>
        )

      case 'candlestick':
        return (
          <ComposedChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />}
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="high"
              fill={chartColors.success}
              opacity={0.8}
            />
            <Bar
              dataKey="low"
              fill={chartColors.danger}
              opacity={0.8}
            />
            <Line
              type="monotone"
              dataKey="sma"
              stroke={chartColors.secondary}
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        )

      default: // line
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />}
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: chartColors.text }}
              domain={['dataMin - 100', 'dataMax + 100']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Brush
              dataKey="time"
              height={30}
              stroke={chartColors.primary}
              fill={chartColors.primary}
              fillOpacity={0.1}
            />
            {selectedIndicators.map(indicator => (
              <Line
                key={indicator}
                type="monotone"
                dataKey={indicator}
                stroke={indicatorsList.find(i => i.value === indicator)?.color || chartColors.secondary}
                strokeWidth={2}
                dot={false}
                opacity={0.8}
              />
            ))}
            <Line
              type="monotone"
              dataKey="value"
              stroke={chartColors.primary}
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        )
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('space-y-4', className)}
    >
      {/* Chart Header */}
      <Card className="shadow-lg">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <span>{symbol}</span>
                <Badge
                  variant={priceChange.direction === 'up' ? 'default' :
                           priceChange.direction === 'down' ? 'destructive' : 'secondary'}
                  className="flex items-center space-x-1"
                >
                  {priceChange.direction === 'up' && <TrendingUp className="h-3 w-3" />}
                  {priceChange.direction === 'down' && <TrendingDown className="h-3 w-3" />}
                  {priceChange.direction === 'neutral' && <Minus className="h-3 w-3" />}
                  <span>{priceChange.percentage.toFixed(2)}%</span>
                </Badge>
                <Badge variant="outline" className="flex items-center space-x-1">
                  {isConnected ? (
                    <>
                      <Activity className="h-3 w-3 text-green-500" />
                      <span>实时</span>
                    </>
                  ) : (
                    <>
                      <Clock className="h-3 w-3 text-gray-500" />
                      <span>离线</span>
                    </>
                  )}
                </Badge>
              </CardTitle>
              <CardDescription>
                当前价格: ${data[data.length - 1]?.value?.toFixed(2) || '--'}
              </CardDescription>
            </div>

            <div className="flex items-center space-x-2">
              {/* Chart Type Selector */}
              <Select value={type} onValueChange={(value: any) => {}}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="line">
                    <div className="flex items-center space-x-2">
                      <LineChartIcon className="h-4 w-4" />
                      <span>线形图</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="area">
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="h-4 w-4" />
                      <span>面积图</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="bar">
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="h-4 w-4" />
                      <span>柱状图</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="candlestick">
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="h-4 w-4" />
                      <span>K线图</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>

              {/* Timeframe Selector */}
              <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timeFrames.map(tf => (
                    <SelectItem key={tf.value} value={tf.value}>
                      {tf.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Real-time Toggle */}
              <div className="flex items-center space-x-2">
                <Switch
                  checked={isRealTime}
                  onCheckedChange={setIsRealTime}
                />
                <span className="text-sm">实时</span>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Indicator Selection */}
          <div className="mb-4 flex flex-wrap gap-2">
            {indicatorsList.map(indicator => (
              <Button
                key={indicator.value}
                variant={selectedIndicators.includes(indicator.value) ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  if (selectedIndicators.includes(indicator.value)) {
                    setSelectedIndicators(prev => prev.filter(i => i !== indicator.value))
                  } else {
                    setSelectedIndicators(prev => [...prev, indicator.value])
                  }
                }}
                className="text-xs"
                style={
                  selectedIndicators.includes(indicator.value)
                    ? { backgroundColor: indicator.color, borderColor: indicator.color }
                    : undefined
                }
              >
                {indicator.label}
              </Button>
            ))}
          </div>

          {/* Chart */}
          <div className="relative" style={{ height }}>
            {isLoading ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Activity className="h-8 w-8 text-primary" />
                </motion.div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                {renderChart()}
              </ResponsiveContainer>
            )}
          </div>

          {/* Volume Chart */}
          {showVolume && (type === 'line' || type === 'area') && (
            <div className="mt-2" style={{ height: 80 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formattedData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <XAxis dataKey="time" hide />
                  <YAxis hide />
                  <Bar
                    dataKey="volume"
                    fill={chartColors.text}
                    opacity={0.2}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default RealTimeChart