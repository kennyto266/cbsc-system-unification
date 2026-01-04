/**
 * DrawdownChart - Drawdown Analysis Chart Component
 * Migrated from square-ui with enhanced features
 */

import React, { useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Card } from '../../ui/Card'
import type { DrawdownChartProps, DrawdownDataPoint } from './types'

const CHART_COLORS = {
  danger: '#EF4444',
  success: '#10B981',
  warning: '#F59E0B',
  primary: '#3B82F6',
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({
  data,
  title = '回撤分析',
  subtitle,
  showZone = true,
  valueFormat = (v) => `-${Math.abs(v).toFixed(2)}%`,
  className = '',
  height = 400,
  loading = false,
  error,
  theme = 'light'
}) => {
  // Process data
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      date: new Date(point.date).toLocaleDateString('zh-TW', {
        month: 'short',
        day: 'numeric',
      }),
      isUnderwater: point.underwater ?? point.drawdown < 0,
    }))
  }, [data])

  // Calculate stats
  const stats = useMemo(() => {
    const maxDrawdown = Math.min(...data.map((d) => d.drawdown))
    const avgDrawdown =
      data.filter((d) => d.drawdown < 0).reduce((sum, d) => sum + d.drawdown, 0) /
      data.filter((d) => d.drawdown < 0).length || 0
    const underwaterDays = data.filter((d) => d.underwater).length
    const maxUnderwaterStreak = calculateMaxStreak(data)

    return {
      maxDrawdown,
      avgDrawdown,
      underwaterDays,
      maxUnderwaterStreak,
    }
  }, [data])

  // Calculate max underwater streak
  function calculateMaxStreak(data: DrawdownDataPoint[]): number {
    let maxStreak = 0
    let currentStreak = 0

    for (const point of data) {
      if (point.underwater) {
        currentStreak++
        maxStreak = Math.max(maxStreak, currentStreak)
      } else {
        currentStreak = 0
      }
    }

    return maxStreak
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null

    const dataPoint = payload[0].payload

    return (
      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {dataPoint.date}
        </p>
        <p
          className="text-sm font-semibold"
          style={{
            color: dataPoint.drawdown < 0 ? CHART_COLORS.danger : CHART_COLORS.success,
          }}
        >
          回撤: {valueFormat(dataPoint.drawdown)}
        </p>
        {dataPoint.isUnderwater && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            水面下
          </p>
        )}
      </div>
    )
  }

  // Define gradient for underwater areas
  const underwaterGradient = (
    <defs>
      <linearGradient id="underwaterGradient" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={CHART_COLORS.danger} stopOpacity={0.3} />
        <stop offset="100%" stopColor={CHART_COLORS.danger} stopOpacity={0.05} />
      </linearGradient>
    </defs>
  )

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

        {/* Stats summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-xs text-gray-600 dark:text-gray-400">最大回撤</p>
            <p className="text-lg font-semibold text-red-600 dark:text-red-400">
              {valueFormat(stats.maxDrawdown)}
            </p>
          </div>
          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <p className="text-xs text-gray-600 dark:text-gray-400">平均回撤</p>
            <p className="text-lg font-semibold text-orange-600 dark:text-orange-400">
              {valueFormat(stats.avgDrawdown)}
            </p>
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-xs text-gray-600 dark:text-gray-400">水面下天數</p>
            <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
              {stats.underwaterDays} 天
            </p>
          </div>
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <p className="text-xs text-gray-600 dark:text-gray-400">最長回撤期</p>
            <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">
              {stats.maxUnderwaterStreak} 天
            </p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            {underwaterGradient}
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
            <ReferenceLine y={0} stroke="#6b7280" strokeWidth={1} />
            {showZone && (
              <Area
                type="monotone"
                dataKey="drawdown"
                name="回撤"
                stroke={CHART_COLORS.danger}
                strokeWidth={2}
                fill="url(#underwaterGradient)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export default DrawdownChart
