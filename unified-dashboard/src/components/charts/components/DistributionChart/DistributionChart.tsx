import React, { useRef, useMemo, useCallback, useState } from 'react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { motion } from 'framer-motion'
import BaseChartContainer, { ChartRef } from '../shared/ChartContainer'
import { useChartTooltip } from '../shared/ChartTooltip'
import ChartControls from '../shared/ChartControls'
import {
  DistributionChartProps,
  DistributionDataPoint,
  DistributionDataset,
  ChartTheme
} from '../../types/chart.types'
import { useChartPerformance } from '../../hooks/useChartPerformance'

const defaultTheme: ChartTheme = {
  name: 'default',
  colors: {
    primary: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'],
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

const DistributionChart = React.forwardRef<ChartRef, DistributionChartProps>(({
  dataset,
  width,
  height = 400,
  showTooltip = true,
  showLegend = true,
  sortOrder = 'none',
  maxItems,
  animationDuration = 1000,
  onSliceClick,
  onBarClick,
  className = '',
  theme = defaultTheme,
  responsive = true,
  animation = true
}, ref) => {
  const chartRef = useRef<ChartRef>(null)
  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined)
  const { show: showTooltipContent, hide: hideTooltip, Tooltip } = useChartTooltip({
    followCursor: true
  })

  const { metrics, startRenderTracking, endRenderTracking } = useChartPerformance()

  // Process and sort data
  const processedData = useMemo(() => {
    startRenderTracking()
    let data = [...dataset.data]

    // Apply sorting
    if (sortOrder === 'asc') {
      data.sort((a, b) => a.value - b.value)
    } else if (sortOrder === 'desc') {
      data.sort((a, b) => b.value - a.value)
    }

    // Apply max items limit
    if (maxItems && maxItems > 0 && data.length > maxItems) {
      data = data.slice(0, maxItems)
    }

    // Calculate percentages if not provided
    const total = data.reduce((sum, item) => sum + item.value, 0)
    data = data.map(item => ({
      ...item,
      percentage: item.percentage ?? (item.value / total) * 100
    }))

    // Assign colors if not provided
    data = data.map((item, index) => ({
      ...item,
      color: item.color || theme.colors.primary[index % theme.colors.primary.length]
    }))

    endRenderTracking()
    return data
  }, [dataset.data, sortOrder, maxItems, theme.colors.primary, startRenderTracking, endRenderTracking])

  // Custom tooltip content
  const CustomTooltip = useCallback(({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0].payload as DistributionDataPoint

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
          {data.label}
        </div>
        <div style={{ marginBottom: '4px' }}>
          值: {data.value.toLocaleString()}
        </div>
        <div style={{ marginBottom: '4px' }}>
          占比: {(data.percentage || 0).toFixed(1)}%
        </div>
      </div>
    )
  }, [theme])

  // Custom label for pie chart
  const renderCustomizedLabel = useCallback((props: any) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if ((percent || 0) < 0.05) return null // Don't show label for slices < 5%

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        fontSize={12}
        fontWeight={600}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }, [])

  // Handle slice/click interactions
  const handleSliceClick = useCallback((data: any, index: number) => {
    setActiveIndex(activeIndex === index ? undefined : index)
    if (onSliceClick && data) {
      onSliceClick(data)
    }
  }, [activeIndex, onSliceClick])

  const handleBarClick = useCallback((data: any) => {
    if (onBarClick && data) {
      onBarClick(data)
    }
  }, [onBarClick])

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
          ['Label', 'Value', 'Percentage', 'Color'].join(','),
          ...processedData.map(row => [
            row.label,
            row.value,
            (row.percentage || 0).toFixed(2),
            row.color
          ].join(','))
        ].join('\n')

        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `distribution-data-${Date.now()}.csv`
        a.click()
        URL.revokeObjectURL(url)
        break
    }
  }, [chartRef, processedData])

  // Render chart based on type
  const renderChart = () => {
    const { type } = dataset

    switch (type) {
      case 'bar':
        return (
          <BarChart
            data={processedData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.grid} />
            <XAxis
              dataKey="label"
              angle={-45}
              textAnchor="end"
              height={100}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            <YAxis
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            <Bar
              dataKey="value"
              onClick={handleBarClick}
              animationDuration={animation ? animationDuration : 0}
            >
              {processedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={activeIndex === index ? theme.colors.foreground : 'none'}
                  strokeWidth={activeIndex === index ? 2 : 0}
                  style={{
                    cursor: 'pointer'
                  }}
                />
              ))}
            </Bar>
          </BarChart>
        )

      case 'horizontal-bar':
        return (
          <BarChart
            data={processedData}
            layout="horizontal"
            margin={{
              top: 20,
              right: 30,
              left: 100,
              bottom: 20
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.grid} />
            <XAxis
              type="number"
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={80}
              stroke={theme.colors.foreground}
              fontSize={theme.typography.fontSize.small}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            <Bar
              dataKey="value"
              onClick={handleBarClick}
              animationDuration={animation ? animationDuration : 0}
            >
              {processedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={activeIndex === index ? theme.colors.foreground : 'none'}
                  strokeWidth={activeIndex === index ? 2 : 0}
                  style={{
                    cursor: 'pointer'
                  }}
                />
              ))}
            </Bar>
          </BarChart>
        )

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={processedData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={dataset.showLabels ? renderCustomizedLabel : false}
              outerRadius={dataset.outerRadius || 120}
              fill={theme.colors.primary[0]}
              dataKey="value"
              onClick={(data, index) => handleSliceClick(data, index)}
              animationDuration={animation ? animationDuration : 0}
            >
              {processedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={activeIndex === index ? theme.colors.foreground : 'none'}
                  strokeWidth={activeIndex === index ? 2 : 0}
                  style={{
                    cursor: 'pointer',
                    filter: activeIndex === index ? 'brightness(1.1)' : 'brightness(1)'
                  }}
                />
              ))}
            </Pie>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
          </PieChart>
        )

      case 'donut':
        return (
          <PieChart>
            <Pie
              data={processedData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={dataset.showLabels ? renderCustomizedLabel : false}
              innerRadius={dataset.innerRadius || 60}
              outerRadius={dataset.outerRadius || 120}
              fill={theme.colors.primary[0]}
              dataKey="value"
              onClick={(data, index) => handleSliceClick(data, index)}
              animationDuration={animation ? animationDuration : 0}
              paddingAngle={dataset.padAngle || 0}
            >
              {processedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={activeIndex === index ? theme.colors.foreground : 'none'}
                  strokeWidth={activeIndex === index ? 2 : 0}
                  style={{
                    cursor: 'pointer',
                    filter: activeIndex === index ? 'brightness(1.1)' : 'brightness(1)'
                  }}
                />
              ))}
            </Pie>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
          </PieChart>
        )

      default:
        return null
    }
  }

  const toolbar = (
    <ChartControls
      onReset={() => setActiveIndex(undefined)}
      onExport={handleExport}
      showGrid={false}
      showGridToggle={false}
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
    >
      <ResponsiveContainer width="100%" height="100%">
        {renderChart()}
      </ResponsiveContainer>
      <Tooltip />
    </BaseChartContainer>
  )
})

DistributionChart.displayName = 'DistributionChart'

export default DistributionChart