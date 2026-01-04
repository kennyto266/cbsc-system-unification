import React, { useRef, useMemo, useCallback, useState } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts'
import { motion } from 'framer-motion'
import BaseChartContainer, { ChartRef } from '../shared/ChartContainer'
import { useChartTooltip } from '../shared/ChartTooltip'
import ChartControls from '../shared/ChartControls'
import {
  HeatmapChartProps,
  HeatmapDataPoint,
  ChartTheme
} from '../../types/chart.types'
import { useChartPerformance } from '../../hooks/useChartPerformance'

const defaultTheme: ChartTheme = {
  name: 'default',
  colors: {
    primary: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
    secondary: ['#6B7280', '#9CA3AF', '#D1D5DB'],
    background: '#ffffff',
    foreground: '#1F2937',
    grid: 'rgba(0, 0, 0, 0.05)',
    tooltip: {
      background: 'rgba(0, 0, 0, 0.8)',
      foreground: '#ffffff',
      border: 'rgba(0, 0, 0, 0.8)'
    }
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: {
      small: 12,
      medium: 14,
      large: 16
    }
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  }
}

const HeatmapChart = React.forwardRef<ChartRef, HeatmapChartProps>(({
  dataset,
  xAxis,
  yAxis,
  width,
  height = 400,
  showColorScale = true,
  colorScalePosition = 'right',
  showGrid = true,
  showTooltip = true,
  onCellClick,
  onCellHover,
  className = '',
  theme = defaultTheme,
  responsive = true,
  animation = true
}, ref) => {
  const chartRef = useRef<ChartRef>(null)
  const [hoveredCell, setHoveredCell] = useState<HeatmapDataPoint | null>(null)
  const [showGridLines, setShowGridLines] = useState(showGrid)
  const { show: showTooltipContent, hide: hideTooltip, Tooltip } = useChartTooltip({
    followCursor: true
  })

  const { metrics, startRenderTracking, endRenderTracking } = useChartPerformance()

  // Generate color scale
  const colorScale = useMemo(() => {
    const { data, colorScale: config } = dataset

    if (!data || data.length === 0) return []

    const values = data.map(d => d.value)
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)

    if (config?.steps) {
      // Use custom color steps
      return config.steps.map(step => ({
        value: step.value,
        color: step.color
      }))
    }

    // Generate default gradient between min and max colors
    const defaultSteps = 10
    const steps = []
    for (let i = 0; i <= defaultSteps; i++) {
      const ratio = i / defaultSteps
      const value = minValue + (maxValue - minValue) * ratio

      // Interpolate between colors
      const minColor = config?.min || '#3B82F6'
      const maxColor = config?.max || '#EF4444'
      const color = interpolateColor(minColor, maxColor, ratio)

      steps.push({ value, color })
    }

    return steps
  }, [dataset])

  // Process data for heatmap visualization
  const processedData = useMemo(() => {
    startRenderTracking()
    const { data, cellSize = 10, gap = 1 } = dataset

    if (!data || data.length === 0) {
      endRenderTracking()
      return []
    }

    const processed = data.map(point => {
      const xIndex = xAxis.categories.indexOf(point.x)
      const yIndex = yAxis.categories.indexOf(point.y)

      if (xIndex === -1 || yIndex === -1) return null

      const x = xIndex * (cellSize + gap) + cellSize / 2
      const y = yIndex * (cellSize + gap) + cellSize / 2
      const size = cellSize

      // Find color for this value
      const colorStep = colorScale
        .sort((a, b) => b.value - a.value)
        .find(step => point.value >= step.value)

      const color = colorStep?.color || colorScale[0]?.color || '#3B82F6'

      return {
        x,
        y,
        size,
        fill: color,
        originalData: point
      }
    }).filter(Boolean)

    endRenderTracking()
    return processed
  }, [dataset, xAxis.categories, yAxis.categories, colorScale])

  // Color interpolation helper
  function interpolateColor(color1: string, color2: string, ratio: number): string {
    const hex2rgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : { r: 0, g: 0, b: 0 }
    }

    const c1 = hex2rgb(color1)
    const c2 = hex2rgb(color2)

    const r = Math.round(c1.r + (c2.r - c1.r) * ratio)
    const g = Math.round(c1.g + (c2.g - c1.g) * ratio)
    const b = Math.round(c1.b + (c2.b - c1.b) * ratio)

    return `rgb(${r}, ${g}, ${b})`
  }

  // Custom tooltip content
  const CustomTooltip = useCallback(({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0].payload.originalData as HeatmapDataPoint

    return (
      <div style={{
        backgroundColor: theme.colors.tooltip.background,
        color: theme.colors.tooltip.foreground,
        padding: '8px 12px',
        borderRadius: '6px',
        fontSize: '12px',
        border: `1px solid ${theme.colors.tooltip.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <div style={{ marginBottom: '4px', fontWeight: 600 }}>
          {yAxis.label}: {data.y}
        </div>
        <div style={{ marginBottom: '4px' }}>
          {xAxis.label}: {data.x}
        </div>
        <div style={{ fontWeight: 600 }}>
          值: {dataset.labelFormat ? dataset.labelFormat(data.value) : data.value.toFixed(2)}
        </div>
        {data.label && (
          <div style={{ fontSize: '10px', opacity: 0.8 }}>
            {data.label}
          </div>
        )}
      </div>
    )
  }, [dataset.labelFormat, theme, xAxis.label, yAxis.label])

  // Handle cell interaction
  const handleCellClick = useCallback((data: any) => {
    if (data?.originalData && onCellClick) {
      onCellClick(data.originalData)
    }
  }, [onCellClick])

  const handleCellMouseEnter = useCallback((data: any) => {
    if (data?.originalData) {
      setHoveredCell(data.originalData)
      onCellHover?.(data.originalData)
    }
  }, [onCellHover])

  const handleCellMouseLeave = useCallback(() => {
    setHoveredCell(null)
  }, [])

  // Handle export
  const handleExport = useCallback((format: 'png' | 'svg' | 'csv') => {
    switch (format) {
      case 'png':
        chartRef.current?.exportImage('png')
        break
      case 'svg':
        chartRef.current?.exportImage('svg')
        break
      case 'csv':
        // Convert data to CSV and download
        const csv = [
          [yAxis.label, xAxis.label, 'Value', 'Label'].join(','),
          ...dataset.data.map(row => [
            row.y,
            row.x,
            row.value,
            row.label || ''
          ].join(','))
        ].join('\n')

        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `heatmap-data-${Date.now()}.csv`
        a.click()
        URL.revokeObjectURL(url)
        break
    }
  }, [chartRef, dataset, xAxis.label, yAxis.label])

  // Render color scale legend
  const renderColorScale = () => {
    if (!showColorScale || colorScale.length === 0) return null

    const scaleHeight = 200
    const scaleWidth = 20

    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '4px'
        }}
      >
        <div
          style={{
            height: scaleHeight,
            width: scaleWidth,
            background: `linear-gradient(to top, ${colorScale.map(s => s.color).join(', ')})`,
            border: '1px solid rgba(0,0,0,0.1)',
            borderRadius: '2px'
          }}
        />
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            height: scaleHeight,
            fontSize: '10px',
            color: theme.colors.foreground
          }}
        >
          {colorScale.map((step, index) => (
            <div key={index} style={{ textAlign: 'center' }}>
              {dataset.labelFormat ? dataset.labelFormat(step.value) : step.value.toFixed(1)}
            </div>
          ))}
        </div>
      </div>
    )
  }

  const toolbar = (
    <ChartControls
      onReset={() => setHoveredCell(null)}
      onExport={handleExport}
      onToggleGrid={() => setShowGridLines(!showGridLines)}
      showGridToggle={showGrid}
      showGrid={showGridLines}
    />
  )

  const chartContent = (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* Main heatmap */}
      <div style={{ flex: 1 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart
            margin={{
              top: 20,
              right: colorScalePosition === 'right' ? 20 : 40,
              bottom: 60,
              left: 80
            }}
          >
            {showGridLines && <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.grid} />}
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, 'dataMax']}
              ticks={xAxis.categories.map((_, i) => i * (dataset.cellSize || 10 + 1))}
              tickFormatter={(value) => xAxis.categories[Math.floor(value / (dataset.cellSize || 10 + 1))] || ''}
              label={{ value: xAxis.label, position: 'insideBottom', offset: -10 }}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            <YAxis
              type="number"
              dataKey="y"
              domain={[0, 'dataMax']}
              ticks={yAxis.categories.map((_, i) => i * (dataset.cellSize || 10 + 1))}
              tickFormatter={(value) => yAxis.categories[Math.floor(value / (dataset.cellSize || 10 + 1))] || ''}
              label={{ value: yAxis.label, angle: -90, position: 'insideLeft' }}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} cursor={false} />}

            <Scatter
              data={processedData}
              fill={theme.colors.primary[0]}
              onClick={handleCellClick}
              onMouseEnter={handleCellMouseEnter}
              onMouseLeave={handleCellMouseLeave}
              animationDuration={animation ? 1000 : 0}
            >
              {processedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.fill}
                  stroke={hoveredCell === entry.originalData ? theme.colors.foreground : 'none'}
                  strokeWidth={hoveredCell === entry.originalData ? 2 : 0}
                  style={{
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Color scale legend */}
      {showColorScale && colorScalePosition === 'right' && (
        <div style={{
          marginLeft: theme.spacing.md,
          display: 'flex',
          alignItems: 'center'
        }}>
          {renderColorScale()}
        </div>
      )}
    </div>
  )

  return (
    <BaseChartContainer
      ref={chartRef}
      width={width}
      height={height}
      className={className}
      theme={theme}
      toolbar={toolbar}
    >
      {chartContent}
      <Tooltip />
    </BaseChartContainer>
  )
})

HeatmapChart.displayName = 'HeatmapChart'

export default HeatmapChart