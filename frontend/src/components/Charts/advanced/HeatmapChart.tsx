/**
 * HeatmapChart - Advanced Heatmap Chart Component
 * Migrated from unified-dashboard with enhanced features
 */

import React, { useRef, useMemo, useCallback, useState, forwardRef, useImperativeHandle } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  Legend
} from 'recharts'
import { Card } from '../../ui/Card'
import type {
  HeatmapChartProps,
  HeatmapDataPoint,
  ColorScaleConfig,
  ChartRef
} from './types'

const defaultColorScale: ColorScaleConfig = {
  min: '#10B981',
  max: '#EF4444',
  type: 'sequential'
}

// Color scale interpolation
function interpolateColor(value: number, min: number, max: number, colorScale: ColorScaleConfig): string {
  const ratio = Math.max(0, Math.min(1, (value - min) / (max - min)))

  if (colorScale.type === 'diverging') {
    // Diverging color scale (blue -> white -> red)
    if (ratio < 0.5) {
      return interpolateColor(value, min, (min + max) / 2, { ...colorScale, min: '#3B82F6', max: '#ffffff', type: 'sequential' })
    } else {
      return interpolateColor(value, (min + max) / 2, max, { ...colorScale, min: '#ffffff', max: '#EF4444', type: 'sequential' })
    }
  }

  // Sequential color scale
  const [r1, g1, b1] = hexToRgb(colorScale.min)
  const [r2, g2, b2] = hexToRgb(colorScale.max)

  const r = Math.round(r1 + (r2 - r1) * ratio)
  const g = Math.round(g1 + (g2 - g1) * ratio)
  const b = Math.round(b1 + (b2 - b1) * ratio)

  return `rgb(${r}, ${g}, ${b})`
}

function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
      ]
    : [0, 0, 0]
}

// Custom Tooltip Component
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null

  const data = payload[0].payload as HeatmapDataPoint

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {data.label && (
        <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
          {data.label}
        </p>
      )}
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
        X: {data.x}
      </p>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
        Y: {data.y}
      </p>
      <p
        className="text-sm font-semibold"
        style={{
          color: interpolateColor(
            data.value,
            payload[0].payload.minValue,
            payload[0].payload.maxValue,
            payload[0].payload.colorScale || defaultColorScale
          )
        }}
      >
        值: {data.value.toFixed(2)}
      </p>
    </div>
  )
}

const HeatmapChart = forwardRef<ChartRef, HeatmapChartProps>(({
  dataset,
  xAxis,
  yAxis,
  showColorScale = true,
  onCellClick,
  onCellHover,
  title,
  subtitle,
  className = '',
  height = 400,
  width = '100%',
  theme = 'light',
  animation = true,
  loading = false,
  error = null
}, ref) => {
  const [hoveredCell, setHoveredCell] = useState<HeatmapDataPoint | null>(null)
  const chartRef = useRef<any>(null)

  // Expose chart methods via ref
  useImperativeHandle(ref, () => ({
    exportChart: async (format: 'png' | 'svg' | 'pdf' = 'png') => {
      // Implement export functionality
      const chartElement = chartRef.current
      if (chartElement) {
        const svgElement = chartElement.querySelector('svg')
        if (svgElement) {
          const svgData = new XMLSerializer().serializeToString(svgElement)
          const canvas = document.createElement('canvas')
          const ctx = canvas.getContext('2d')
          const img = new Image()

          return new Promise((resolve) => {
            img.onload = () => {
              canvas.width = img.width * 2
              canvas.height = img.height * 2
              ctx?.scale(2, 2)
              ctx?.drawImage(img, 0, 0)

              if (format === 'png') {
                const pngUrl = canvas.toDataURL('image/png')
                const link = document.createElement('a')
                link.download = `heatmap-${Date.now()}.png`
                link.href = pngUrl
                link.click()
                resolve()
              }
            }
            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
          })
        }
      }
    },
    getDataURL: () => {
      const chartElement = chartRef.current
      if (chartElement) {
        const svgElement = chartElement.querySelector('svg')
        if (svgElement) {
          const svgData = new XMLSerializer().serializeToString(svgElement)
          return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
        }
      }
      return ''
    },
    resetZoom: () => {
      // Reset zoom (placeholder)
    }
  }))

  // Process data for chart
  const chartData = useMemo(() => {
    const values = dataset.data.map(d => d.value)
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const colorScale = dataset.colorScale || defaultColorScale

    return dataset.data.map(point => ({
      ...point,
      xLabel: xAxis.categories.indexOf(point.x as string | number),
      yLabel: yAxis.categories.indexOf(point.y as string | number),
      color: interpolateColor(point.value, minValue, maxValue, colorScale),
      minValue,
      maxValue,
      colorScale
    }))
  }, [dataset, xAxis.categories, yAxis.categories])

  // Handle cell click
  const handleCellClick = useCallback((data: HeatmapDataPoint) => {
    if (onCellClick) {
      onCellClick(data)
    }
  }, [onCellClick])

  // Handle cell hover
  const handleCellHover = useCallback((data: HeatmapDataPoint | null) => {
    setHoveredCell(data)
    if (onCellHover && data) {
      onCellHover(data)
    }
  }, [onCellHover])

  // Custom cell shape
  const CustomCell = (props: any) => {
    const { cx, cy, payload } = props

    return (
      <g>
        <rect
          x={cx - 15}
          y={cy - 15}
          width={30}
          height={30}
          fill={payload.color}
          stroke={hoveredCell?.x === payload.x && hoveredCell?.y === payload.y ? '#000' : 'transparent'}
          strokeWidth={2}
          style={{ cursor: 'pointer', transition: animation ? 'all 0.2s' : 'none' }}
          onClick={() => handleCellClick(payload)}
          onMouseEnter={() => handleCellHover(payload)}
          onMouseLeave={() => handleCellHover(null)}
          opacity={hoveredCell && (hoveredCell.x !== payload.x || hoveredCell.y !== payload.y) ? 0.3 : 1}
        />
        {showColorScale && (
          <text
            x={cx}
            y={cy}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={10}
            fill="#ffffff"
            style={{ pointerEvents: 'none' }}
          >
            {payload.value.toFixed(1)}
          </text>
        )}
      </g>
    )
  }

  // Color scale legend
  const ColorScaleLegend = () => {
    const values = dataset.data.map(d => d.value)
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const colorScale = dataset.colorScale || defaultColorScale

    const steps = 10
    const legendSteps = Array.from({ length: steps }, (_, i) => {
      const value = minValue + (maxValue - minValue) * (i / (steps - 1))
      const color = interpolateColor(value, minValue, maxValue, colorScale)
      return { value, color }
    })

    return (
      <div className="flex items-center gap-2 mt-4">
        <span className="text-xs text-gray-600 dark:text-gray-400">
          {minValue.toFixed(2)}
        </span>
        <div className="flex-1 h-3 rounded" style={{
          background: `linear-gradient(to right, ${legendSteps.map(s => s.color).join(', ')})`
        }} />
        <span className="text-xs text-gray-600 dark:text-gray-400">
          {maxValue.toFixed(2)}
        </span>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <Card className={className}>
        <div className="p-6" style={{ height: typeof height === 'number' ? `${height}px` : height }}>
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
        <div className="p-6" style={{ height: typeof height === 'number' ? `${height}px` : height }}>
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

        <ResponsiveContainer width={width} height={height}>
          <ScatterChart
            ref={chartRef}
            margin={{ top: 20, right: 20, bottom: 20, left: 60 }}
            data={chartData}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
            <XAxis
              type="number"
              dataKey="xLabel"
              name={xAxis.label}
              tickFormatter={(value) => xAxis.categories[value] || ''}
              stroke="#6b7280"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              type="number"
              dataKey="yLabel"
              name={yAxis.label}
              tickFormatter={(value) => yAxis.categories[value] || ''}
              stroke="#6b7280"
              fontSize={12}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Scatter dataKey="y" shape={<CustomCell />} />
          </ScatterChart>
        </ResponsiveContainer>

        {showColorScale && <ColorScaleLegend />}
      </div>
    </Card>
  )
})

HeatmapChart.displayName = 'HeatmapChart'

export default HeatmapChart
