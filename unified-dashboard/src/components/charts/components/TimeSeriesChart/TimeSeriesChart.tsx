import React, { useRef, useMemo, useCallback, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ComposedChart,
  Bar,
  ReferenceLine,
  Brush
} from 'recharts'
import { motion } from 'framer-motion'
import BaseChartContainer, { ChartRef } from '../shared/ChartContainer'
import { useChartTooltip } from '../shared/ChartTooltip'
import ChartControls from '../shared/ChartControls'
import {
  TimeSeriesChartProps,
  TimeSeriesDataPoint,
  TimeSeriesDataset,
  ChartTheme
} from '../../types/chart.types'
import { useChartInteraction } from '../../hooks/useChartInteraction'
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

const TimeSeriesChart = React.forwardRef<ChartRef, TimeSeriesChartProps>(({
  datasets,
  timeRange,
  width,
  height = 400,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  showCrosshair = true,
  allowZoom = true,
  allowPan = true,
  timeFormat = 'HH:mm:ss',
  valueFormat = (value) => value.toFixed(2),
  onTimeRangeChange,
  onDataPointClick,
  yAxis,
  className = '',
  theme = defaultTheme,
  responsive = true,
  animation = true
}, ref) => {
  const chartRef = useRef<ChartRef>(null)
  const [showBrush, setShowBrush] = useState(false)
  const [showGridLines, setShowGridLines] = useState(showGrid)
  const { show: showTooltipContent, hide: hideTooltip, Tooltip } = useChartTooltip({
    followCursor: true
  })

  const {
    state: interactionState,
    handlers: interactionHandlers,
    containerRef: interactionContainerRef,
    reset: resetInteraction
  } = useChartInteraction({
    enableZoom: allowZoom,
    enablePan: allowPan,
    enableCrosshair: showCrosshair
  })

  const { metrics, startRenderTracking, endRenderTracking } = useChartPerformance()

  // Process and transform data for Recharts
  const processedData = useMemo(() => {
    startRenderTracking()
    const allTimestamps = new Set<number>()
    const dataMap = new Map<number, any>()

    // Collect all unique timestamps
    datasets.forEach(dataset => {
      dataset.data.forEach(point => {
        const timestamp = new Date(point.timestamp).getTime()
        allTimestamps.add(timestamp)
      })
    })

    // Create data points for each timestamp
    Array.from(allTimestamps)
      .sort((a, b) => a - b)
      .forEach(timestamp => {
        const dataPoint: any = {
          timestamp,
          displayTime: new Date(timestamp).toLocaleTimeString()
        }

        // Add values for each dataset
        datasets.forEach(dataset => {
          const point = dataset.data.find(p =>
            new Date(p.timestamp).getTime() === timestamp
          )
          if (point) {
            dataPoint[dataset.id] = point.value
            dataPoint[`${dataset.id}_volume`] = point.volume
          }
        })

        dataMap.set(timestamp, dataPoint)
      })

    const processed = Array.from(dataMap.values())
    endRenderTracking()
    return processed
  }, [datasets, startRenderTracking, endRenderTracking])

  // Apply time range filter
  const filteredData = useMemo(() => {
    if (!timeRange) return processedData

    const startTime = new Date(timeRange.start).getTime()
    const endTime = new Date(timeRange.end).getTime()

    return processedData.filter(point =>
      point.timestamp >= startTime && point.timestamp <= endTime
    )
  }, [processedData, timeRange])

  // Custom tooltip content
  const CustomTooltip = useCallback(({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null

    const timestamp = new Date(label)

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
          {timestamp.toLocaleString()}
        </div>
        {payload.map((entry: any, index: number) => {
          const dataset = datasets.find(d => d.id === entry.dataKey)
          return (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: entry.color,
                  borderRadius: '50%'
                }}
              />
              <span>{dataset?.label || entry.dataKey}: </span>
              <span style={{ fontWeight: 600 }}>
                {valueFormat(entry.value)}
              </span>
            </div>
          )
        })}
      </div>
    )
  }, [datasets, theme, valueFormat])

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
          ['Timestamp', ...datasets.map(d => d.label)].join(','),
          ...filteredData.map(row => [
            new Date(row.timestamp).toISOString(),
            ...datasets.map(d => row[d.id] || '')
          ].join(','))
        ].join('\n')

        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `chart-data-${Date.now()}.csv`
        a.click()
        URL.revokeObjectURL(url)
        break
    }
  }, [chartRef, datasets, filteredData])

  // Custom tick formatter for X-axis
  const formatXAxisTick = useCallback((tickItem: number) => {
    const date = new Date(tickItem)
    switch (timeFormat) {
      case 'HH:mm:ss':
        return date.toLocaleTimeString()
      case 'MM/dd':
        return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' })
      case 'MM/dd HH:mm':
        return date.toLocaleString('en-US', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        })
      default:
        return date.toLocaleString()
    }
  }, [timeFormat])

  // Render chart lines based on dataset type
  const renderChartContent = () => {
    const commonProps = {
      data: filteredData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    }

    // Determine chart type based on datasets
    const hasAreaDataset = datasets.some(d => d.fill)
    const hasBarDataset = datasets.some(d => d.strokeDasharray)

    if (hasAreaDataset || hasBarDataset) {
      // Use ComposedChart for mixed types
      return (
        <ComposedChart {...commonProps}>
          {showGridLines && <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.grid} />}
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatXAxisTick}
            stroke={theme.colors.foreground}
            fontSize={theme.typography.fontSize.small}
          />
          {yAxis?.left && (
            <YAxis
              yAxisId="left"
              orientation="left"
              tickFormatter={valueFormat}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
              label={yAxis.left.label ? {
                value: yAxis.left.label,
                angle: -90,
                position: 'insideLeft'
              } : undefined}
            />
          )}
          {yAxis?.right && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tickFormatter={valueFormat}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
              label={yAxis.right.label ? {
                value: yAxis.right.label,
                angle: 90,
                position: 'insideRight'
              } : undefined}
            />
          )}
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && <Legend />}

          {datasets.map((dataset, index) => {
            const color = dataset.color || theme.colors.primary[index % theme.colors.primary.length]

            if (dataset.fill) {
              return (
                <Area
                  key={dataset.id}
                  type="monotone"
                  dataKey={dataset.id}
                  stroke={color}
                  strokeWidth={dataset.strokeWidth || 2}
                  fill={color}
                  fillOpacity={dataset.fillOpacity || 0.1}
                  yAxisId={dataset.yAxisId || 'left'}
                  animationDuration={animation ? 1000 : 0}
                  name={dataset.label}
                />
              )
            }

            return (
              <Line
                key={dataset.id}
                type="monotone"
                dataKey={dataset.id}
                stroke={color}
                strokeWidth={dataset.strokeWidth || 2}
                strokeDasharray={dataset.strokeDasharray}
                dot={false}
                yAxisId={dataset.yAxisId || 'left'}
                animationDuration={animation ? 1000 : 0}
                name={dataset.label}
              />
            )
          })}

          {showBrush && <Brush dataKey="timestamp" height={30} stroke={theme.colors.primary[0]} />}
        </ComposedChart>
      )
    }

    // Simple line chart
    return (
      <LineChart {...commonProps}>
        {showGridLines && <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.grid} />}
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatXAxisTick}
          stroke={theme.colors.foreground}
          fontSize={theme.typography.fontSize.small}
        />
        {yAxis?.left && (
          <YAxis
            yAxisId="left"
            orientation="left"
            tickFormatter={valueFormat}
            stroke={theme.colors.foreground}
            fontSize={theme.typography.fontSize.small}
            label={yAxis.left.label ? {
              value: yAxis.left.label,
              angle: -90,
              position: 'insideLeft'
            } : undefined}
          />
        )}
        {yAxis?.right && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={valueFormat}
            stroke={theme.colors.foreground}
            fontSize={theme.typography.fontSize.small}
            label={yAxis.right.label ? {
              value: yAxis.right.label,
              angle: 90,
              position: 'insideRight'
            } : undefined}
          />
        )}
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}

        {datasets.map((dataset, index) => {
          const color = dataset.color || theme.colors.primary[index % theme.colors.primary.length]
          return (
            <Line
              key={dataset.id}
              type="monotone"
              dataKey={dataset.id}
              stroke={color}
              strokeWidth={dataset.strokeWidth || 2}
              strokeDasharray={dataset.strokeDasharray}
              dot={{
                r: dataset.symbol ? 4 : 0,
                fill: color
              }}
              yAxisId={dataset.yAxisId || 'left'}
              animationDuration={animation ? 1000 : 0}
              name={dataset.label}
            />
          )
        })}

        {showBrush && <Brush dataKey="timestamp" height={30} stroke={theme.colors.primary[0]} />}
      </LineChart>
    )
  }

  const toolbar = (
    <ChartControls
      onReset={() => {
        resetInteraction()
        setShowBrush(false)
      }}
      onExport={handleExport}
      onToggleGrid={() => setShowGridLines(!showGridLines)}
      onToggleBrush={() => setShowBrush(!showBrush)}
      showGridToggle={showGrid}
      showExport={true}
      showGrid={showGridLines}
      showBrush={showBrush}
    />
  )

  return (
    <BaseChartContainer
      ref={chartRef}
      width={width}
      height={height}
      className={className}
      theme={theme}
      toolbar={toolbar}
      containerRef={interactionContainerRef}
    >
      <ResponsiveContainer width="100%" height="100%">
        {renderChartContent()}
      </ResponsiveContainer>
      <Tooltip />
    </BaseChartContainer>
  )
})

TimeSeriesChart.displayName = 'TimeSeriesChart'

export default TimeSeriesChart