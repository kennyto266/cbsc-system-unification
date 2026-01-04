/**
 * PerformanceChart - Strategy Performance Chart Component
 * Migrated from square-ui with enhanced features
 */

import React, { useMemo } from 'react'
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card } from '../../ui/Card'
import type { PerformanceChartProps, PerformanceDataPoint } from './types'

const CHART_COLORS = {
  primary: '#3B82F6',
  neutral: '#9CA3AF',
  success: '#10B981',
  danger: '#EF4444',
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  title = '策略表現',
  subtitle,
  showBenchmark = true,
  showArea = true,
  valueFormat = (v) => `${v.toFixed(2)}%`,
  className = '',
  height = 400,
  loading = false,
  error,
  theme = 'light'
}) => {
  // Format data for chart
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      date: new Date(point.date).toLocaleDateString('zh-TW', {
        month: 'short',
        day: 'numeric',
      }),
    }))
  }, [data])

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null

    return (
      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {payload[0].payload.date}
        </p>
        {payload.map((entry: any, index: number) => (
          <p
            key={index}
            className="text-sm"
            style={{ color: entry.color }}
          >
            {entry.name}: {valueFormat(entry.value)}
          </p>
        ))}
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6" style={{ height }}>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        </div>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <div className="p-6" style={{ height }}>
          <div className="flex items-center justify-center h-full">
            <p className="text-red-500">{error}</p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <div className="p-6">
        {(title || subtitle) && (
          <div className="mb-4">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
        )}

        <ResponsiveContainer width="100%" height={height}>
          {showArea ? (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient
                  id="colorValue"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="5%"
                    stopColor={CHART_COLORS.primary}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={CHART_COLORS.primary}
                    stopOpacity={0}
                  />
                </linearGradient>
                {showBenchmark && (
                  <linearGradient
                    id="colorBenchmark"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor={CHART_COLORS.neutral}
                      stopOpacity={0.2}
                    />
                    <stop
                      offset="95%"
                      stopColor={CHART_COLORS.neutral}
                      stopOpacity={0}
                    />
                  </linearGradient>
                )}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e5e7eb"
                strokeOpacity={0.5}
              />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                name="策略收益率"
                stroke={CHART_COLORS.primary}
                strokeWidth={2}
                fill="url(#colorValue)"
              />
              {showBenchmark && (
                <Area
                  type="monotone"
                  dataKey="benchmark"
                  name="基準指數"
                  stroke={CHART_COLORS.neutral}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  fill="url(#colorBenchmark)"
                />
              )}
            </AreaChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e5e7eb"
                strokeOpacity={0.5}
              />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                name="策略收益率"
                stroke={CHART_COLORS.primary}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS.primary, r: 4 }}
                activeDot={{ r: 6 }}
              />
              {showBenchmark && (
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  name="基準指數"
                  stroke={CHART_COLORS.neutral}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
              )}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export default PerformanceChart
