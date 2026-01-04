import React, { useMemo } from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Cell
} from 'recharts'
import { useTheme } from '../../contexts/ThemeContext'

// Types for mixed strategy data
export interface MixedStrategyData {
  date: string
  timestamp: number
  // Price data
  price?: number
  open?: number
  high?: number
  low?: number
  close?: number
  // Economic indicators
  gdp?: number
  inflation?: number
  unemployment?: number
  interest_rate?: number
  // Volume data
  volume?: number
  // Signal data (1: buy, -1: sell, 0: hold)
  signal?: number
  signal_strength?: number
  // Technical indicators
  ma_short?: number
  ma_long?: number
  rsi?: number
  macd?: number
  // Strategy weights
  price_weight?: number
  economic_weight?: number
}

export interface ChartThresholds {
  upper?: number
  lower?: number
  middle?: number
}

export interface ChartColors {
  price?: string
  volume?: string
  signal?: string
  economic?: string
  ma_short?: string
  ma_long?: string
  positive?: string
  negative?: string
}

export interface DualAxisChartProps {
  data: MixedStrategyData[]
  priceKey?: keyof MixedStrategyData
  volumeKey?: keyof MixedStrategyData
  signalKey?: keyof MixedStrategyData
  economicKeys?: (keyof MixedStrategyData)[]
  maKeys?: { short?: keyof MixedStrategyData; long?: keyof MixedStrategyData }
  height?: number
  title?: string
  showVolume?: boolean
  showSignals?: boolean
  showEconomic?: boolean
  showMA?: boolean
  showThresholds?: boolean
  showLegend?: boolean
  thresholds?: ChartThresholds
  colors?: ChartColors
  onPointClick?: (data: MixedStrategyData) => void
  animationDuration?: number
  syncId?: string // For chart synchronization
}

const defaultColors: ChartColors = {
  price: '#3b82f6',
  volume: '#10b981',
  signal: '#f59e0b',
  economic: '#8b5cf6',
  ma_short: '#ef4444',
  ma_long: '#22c55e',
  positive: '#10b981',
  negative: '#ef4444'
}

export const DualAxisChart: React.FC<DualAxisChartProps> = ({
  data,
  priceKey = 'price',
  volumeKey = 'volume',
  signalKey = 'signal',
  economicKeys = [],
  maKeys,
  height = 400,
  title,
  showVolume = true,
  showSignals = true,
  showEconomic = false,
  showMA = false,
  showThresholds = false,
  showLegend = true,
  thresholds,
  colors = defaultColors,
  onPointClick,
  animationDuration = 300,
  syncId
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  // Format data for chart
  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      // Format date for display
      displayDate: new Date(item.timestamp).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric'
      }),
      // Calculate signal position for visualization
      signalPosition: item[signalKey] ? item[priceKey || 'price']! * (1 + item[signalKey]! * 0.02) : null
    }))
  }, [data, priceKey, signalKey])

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null

    return (
      <div
        className={`p-3 rounded-lg shadow-lg border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}
      >
        <p className={`text-sm font-medium mb-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
          {label}
        </p>
        {payload.map((entry: any, index: number) => (
          <p
            key={index}
            className="text-sm"
            style={{ color: entry.color }}
          >
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
          </p>
        ))}
      </div>
    )
  }

  // Format for axis labels
  const formatPrice = (value: number) => {
    if (value >= 1000) {
      return `¥${(value / 1000).toFixed(1)}K`
    }
    return `¥${value.toFixed(0)}`
  }

  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    }
    return value.toString()
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className={`text-gray-500 ${isDark ? 'text-gray-400' : ''}`}>
          暂无数据
        </p>
      </div>
    )
  }

  return (
    <div className="w-full">
      {title && (
        <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          {title}
        </h3>
      )}

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            syncId={syncId}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={isDark ? '#374151' : '#e5e7eb'}
              vertical={false}
            />

            <XAxis
              dataKey="displayDate"
              stroke={isDark ? '#9ca3af' : '#6b7280'}
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />

            {/* Left Y-axis for price */}
            <YAxis
              yAxisId="price"
              stroke={isDark ? '#9ca3af' : '#6b7280'}
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatPrice}
              orientation="left"
            />

            {/* Right Y-axis for volume */}
            {showVolume && (
              <YAxis
                yAxisId="volume"
                stroke={isDark ? '#9ca3af' : '#6b7280'}
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={formatVolume}
                orientation="right"
              />
            )}

            <Tooltip content={<CustomTooltip />} />

            {showLegend && (
              <Legend
                wrapperStyle={{
                  paddingTop: '20px'
                }}
                iconType="line"
              />
            )}

            {/* Volume bars */}
            {showVolume && (
              <Bar
                yAxisId="volume"
                dataKey={volumeKey}
                fill={colors.volume}
                opacity={0.3}
                name="成交量"
              />
            )}

            {/* Price line */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey={priceKey}
              stroke={colors.price}
              strokeWidth={2}
              dot={false}
              name="价格"
              animationDuration={animationDuration}
            />

            {/* Moving averages */}
            {showMA && maKeys?.short && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey={maKeys.short}
                stroke={colors.ma_short}
                strokeWidth={1}
                dot={false}
                strokeDasharray="5 5"
                name="短期均线"
                animationDuration={animationDuration}
              />
            )}

            {showMA && maKeys?.long && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey={maKeys.long}
                stroke={colors.ma_long}
                strokeWidth={1}
                dot={false}
                strokeDasharray="5 5"
                name="长期均线"
                animationDuration={animationDuration}
              />
            )}

            {/* Economic indicators */}
            {showEconomic && economicKeys.map((key, index) => (
              <Line
                key={key as string}
                yAxisId="price"
                type="monotone"
                dataKey={key}
                stroke={colors.economic}
                strokeWidth={1}
                dot={false}
                opacity={0.7}
                name={key.toString()}
                animationDuration={animationDuration}
              />
            ))}

            {/* Signal markers */}
            {showSignals && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="signalPosition"
                stroke={colors.signal}
                strokeWidth={0}
                dot={(props: any) => {
                  const { cx, cy, payload } = props
                  if (!payload[signalKey]) return null

                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={6}
                      fill={payload[signalKey] === 1 ? colors.positive : colors.negative}
                      stroke={payload[signalKey] === 1 ? colors.positive : colors.negative}
                      strokeWidth={2}
                      style={{ cursor: onPointClick ? 'pointer' : 'default' }}
                      onClick={() => onPointClick?.(payload)}
                    />
                  )
                }}
                name="信号"
                animationDuration={animationDuration}
              />
            )}

            {/* Reference lines for thresholds */}
            {showThresholds && thresholds?.upper && (
              <ReferenceLine
                yAxisId="price"
                y={thresholds.upper}
                stroke={colors.negative}
                strokeDasharray="5 5"
                label="上限"
              />
            )}

            {showThresholds && thresholds?.lower && (
              <ReferenceLine
                yAxisId="price"
                y={thresholds.lower}
                stroke={colors.negative}
                strokeDasharray="5 5"
                label="下限"
              />
            )}

            {showThresholds && thresholds?.middle && (
              <ReferenceLine
                yAxisId="price"
                y={thresholds.middle}
                stroke={colors.price}
                strokeDasharray="3 3"
                opacity={0.5}
                label="中位"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default DualAxisChart