import React, { useEffect, useRef, useMemo, useCallback, useState } from 'react'
import { Chart as ChartJS } from 'chart.js'
import { Chart } from '../base'
import ChartContainer from '../base/ChartContainer'
import { chartUtils } from '../../utils/charts'

// Register Chart.js components
Chart.register(...registerables)

export interface HeatmapDataPoint {
  x: number | string
  y: number | string
  value: number
  label?: string
  metadata?: Record<string, any>
}

export interface HeatmapDataset {
  data: HeatmapDataPoint[]
  colorScale?: {
    type?: 'sequential' | 'diverging' | 'categorical'
    colors?: string[]
    min?: string
    max?: string
    mid?: string // For diverging scales
    steps?: number
  }
  cellSize?: number
  gap?: number
  showLabels?: boolean
  labelFormat?: (value: number) => string
  borderRadius?: number
}

export interface HeatmapChartProps extends BaseChartProps {
  dataset: HeatmapDataset
  xAxis: {
    label: string
    categories: Array<string | number>
    angle?: number // Label rotation angle
  }
  yAxis: {
    label: string
    categories: Array<string | number>
    angle?: number
  }
  showColorScale?: boolean
  colorScalePosition?: 'left' | 'right' | 'top' | 'bottom'
  colorScaleLabel?: string
  interpolation?: 'nearest' | 'linear' | 'cubic'
  onCellClick?: (point: HeatmapDataPoint, event: MouseEvent) => void
  onCellHover?: (point: HeatmapDataPoint | null, event: MouseEvent) => void
  onBrush?: (range: { x: [number, number]; y: [number, number] }) => void
  brushEnabled?: boolean
}

// Color scale generators
const generateColorScale = (
  value: number,
  min: number,
  max: number,
  scale: HeatmapDataset['colorScale']
): string => {
  if (!scale) return '#3182ce'

  const normalizedValue = (value - min) / (max - min)
  const colors = scale.colors || ['#f7fafc', '#2d3748']

  switch (scale.type) {
    case 'diverging':
      const midPoint = scale.mid || '#cbd5e0'
      if (normalizedValue < 0.5) {
        return interpolateColor(colors[0] || '#ef4444', midPoint, normalizedValue * 2)
      } else {
        return interpolateColor(midPoint, colors[1] || '#22c55e', (normalizedValue - 0.5) * 2)
      }

    case 'categorical':
      const steps = scale.steps || 5
      const categoryIndex = Math.floor(normalizedValue * steps)
      return colors[categoryIndex % colors.length]

    default: // sequential
      return interpolateColor(colors[0], colors[colors.length - 1], normalizedValue)
  }
}

const interpolateColor = (color1: string, color2: string, factor: number): string => {
  const c1 = hexToRgb(color1)
  const c2 = hexToRgb(color2)

  if (!c1 || !c2) return color1

  const r = Math.round(c1.r + (c2.r - c1.r) * factor)
  const g = Math.round(c1.g + (c2.g - c1.g) * factor)
  const b = Math.round(c1.b + (c2.b - c1.b) * factor)

  return rgbToHex(r, g, b)
}

const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

const rgbToHex = (r: number, g: number, b: number): string => {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}

export const HeatmapChart: React.FC<HeatmapChartProps> = ({
  dataset,
  xAxis,
  yAxis,
  showColorScale = true,
  colorScalePosition = 'right',
  colorScaleLabel = 'Value',
  interpolation = 'nearest',
  brushEnabled = false,
  width = 800,
  height = 400,
  className = '',
  theme = 'light',
  responsive = true,
  animation = true,
  onCellClick,
  onCellHover,
  onBrush,
  dataTestId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart<'scatter'> | null>(null)
  const hoveredCellRef = useRef<HeatmapDataPoint | null>(null)

  // Process data for Chart.js bubble chart representation
  const { processedData, min, max, xMap, yMap } = useMemo(() => {
    const xCategories = xAxis.categories
    const yCategories = yAxis.categories
    const xMap = new Map(xCategories.map((cat, i) => [cat, i]))
    const yMap = new Map(yCategories.map((cat, i) => [cat, i]))

    let minValue = Infinity
    let maxValue = -Infinity

    const processed = dataset.data.map(point => {
      const x = typeof point.x === 'string' ? xMap.get(point.x) || 0 : point.x
      const y = typeof point.y === 'string' ? yMap.get(point.y) || 0 : point.y
      minValue = Math.min(minValue, point.value)
      maxValue = Math.max(maxValue, point.value)

      return {
        x,
        y,
        v: point.value,
        label: point.label,
        metadata: point.metadata
      }
    })

    return {
      processedData: processed,
      min: minValue,
      max: maxValue,
      xMap,
      yMap
    }
  }, [dataset.data, xAxis.categories, yAxis.categories])

  // Generate bubble chart data
  const bubbleData = useMemo(() => {
    const cellSize = dataset.cellSize || 40
    const gap = dataset.gap || 2
    const actualSize = cellSize - gap

    return processedData.map(point => ({
      x: point.x,
      y: point.y,
      r: actualSize / 2,
      backgroundColor: generateColorScale(point.v, min, max, dataset.colorScale),
      borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)',
      borderWidth: 1,
      originalValue: point.v,
      label: point.label,
      metadata: point.metadata
    }))
  }, [processedData, min, max, dataset.cellSize, dataset.gap, dataset.colorScale, theme])

  // Theme colors
  const themeColors = useMemo(() => {
    return theme === 'dark'
      ? {
          grid: 'rgba(255, 255, 255, 0.1)',
          text: 'rgba(255, 255, 255, 0.8)',
          background: '#1f1f1f'
        }
      : {
          grid: 'rgba(0, 0, 0, 0.1)',
          text: 'rgba(0, 0, 0, 0.8)',
          background: '#ffffff'
        }
  }, [theme])

  // Chart configuration
  const chartConfig = useMemo(() => {
    return {
      type: 'bubble' as const,
      data: {
        datasets: [{
          label: 'Heatmap',
          data: bubbleData,
          backgroundColor: bubbleData.map(d => d.backgroundColor),
          borderColor: bubbleData.map(d => d.borderColor),
          borderWidth: 1
        }]
      },
      options: {
        responsive,
        maintainAspectRatio: false,
        animation: animation ? {
          duration: 1000,
          easing: 'easeInOutQuart'
        } : false,
        scales: {
          x: {
            type: 'linear',
            min: -0.5,
            max: xAxis.categories.length - 0.5,
            grid: {
              display: false
            },
            ticks: {
              stepSize: 1,
              callback: (value: number) => {
                const category = xAxis.categories[value]
                return category !== undefined ? category : ''
              },
              font: {
                family: 'Inter, sans-serif',
                size: 11
              },
              color: themeColors.text,
              maxRotation: xAxis.angle || 0
            },
            title: {
              display: true,
              text: xAxis.label,
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 14,
                weight: '500'
              }
            }
          },
          y: {
            type: 'linear',
            min: -0.5,
            max: yAxis.categories.length - 0.5,
            grid: {
              display: false
            },
            ticks: {
              stepSize: 1,
              callback: (value: number) => {
                const category = yAxis.categories[value]
                return category !== undefined ? category : ''
              },
              font: {
                family: 'Inter, sans-serif',
                size: 11
              },
              color: themeColors.text,
              maxRotation: yAxis.angle || 0
            },
            title: {
              display: true,
              text: yAxis.label,
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 14,
                weight: '500'
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: true,
            backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
            titleColor: themeColors.text,
            bodyColor: themeColors.text,
            borderColor: themeColors.grid,
            borderWidth: 1,
            callbacks: {
              title: () => '',
              label: (context: any) => {
                const point = context.raw
                const xLabel = xAxis.categories[point.x] || point.x
                const yLabel = yAxis.categories[point.y] || point.y
                const formattedValue = dataset.labelFormat
                  ? dataset.labelFormat(point.originalValue)
                  : point.originalValue.toFixed(2)

                return [
                  `${xAxis.label}: ${xLabel}`,
                  `${yAxis.label}: ${yLabel}`,
                  `Value: ${formattedValue}`
                ]
              }
            }
          }
        },
        onClick: (event: any, elements: any[]) => {
          if (elements.length > 0 && onCellClick) {
            const element = elements[0]
            const datasetIndex = element.datasetIndex
            const index = element.index
            const point = processedData[index]
            onCellClick(point, event.native)
          }
        },
        onHover: (event: any, elements: any[]) => {
          if (elements.length > 0) {
            const element = elements[0]
            const index = element.index
            const point = processedData[index]

            if (hoveredCellRef.current !== point) {
              hoveredCellRef.current = point
              if (onCellHover) {
                onCellHover(point, event.native)
              }
            }
          } else {
            if (hoveredCellRef.current !== null) {
              hoveredCellRef.current = null
              if (onCellHover) {
                onCellHover(null, event.native)
              }
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'point'
        }
      }
    }
  }, [bubbleData, xAxis, yAxis, processedData, themeColors, responsive, animation, onCellClick, onCellHover, dataset])

  // Initialize chart
  useEffect(() => {
    if (!canvasRef.current) return

    const chart = new Chart(canvasRef.current, chartConfig)
    chartRef.current = chart

    return () => {
      chart.destroy()
    }
  }, [chartConfig])

  // Color scale component
  const ColorScale = () => {
    if (!showColorScale || !dataset.colorScale) return null

    const colors = dataset.colorScale.colors || ['#f7fafc', '#2d3748']
    const steps = dataset.colorScale.steps || 10

    return (
      <div className={`color-scale color-scale-${colorScalePosition}`} style={{
        position: 'absolute',
        ...(colorScalePosition === 'right' && { right: -60, top: 0, height: '100%' }),
        ...(colorScalePosition === 'left' && { left: -60, top: 0, height: '100%' }),
        ...(colorScalePosition === 'top' && { top: -40, left: 0, width: '100%' }),
        ...(colorScalePosition === 'bottom' && { bottom: -40, left: 0, width: '100%' })
      }}>
        <div className="color-scale-label" style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: '12px',
          color: themeColors.text,
          textAlign: 'center',
          marginBottom: '4px'
        }}>
          {colorScaleLabel}
        </div>
        <div className={`color-scale-gradient ${colorScalePosition === 'top' || colorScalePosition === 'bottom' ? 'horizontal' : 'vertical'}`} style={{
          width: colorScalePosition === 'top' || colorScalePosition === 'bottom' ? '200px' : '20px',
          height: colorScalePosition === 'top' || colorScalePosition === 'bottom' ? '20px' : '200px',
          background: `linear-gradient(to ${colorScalePosition === 'top' || colorScalePosition === 'bottom' ? 'right' : 'bottom'}, ${colors.join(', ')})`,
          border: `1px solid ${themeColors.grid}`,
          borderRadius: '4px'
        }} />
        <div className="color-scale-labels" style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '4px',
          fontFamily: 'Inter, sans-serif',
          fontSize: '10px',
          color: themeColors.text
        }}>
          <span>{dataset.labelFormat ? dataset.labelFormat(min) : min.toFixed(2)}</span>
          <span>{dataset.labelFormat ? dataset.labelFormat(max) : max.toFixed(2)}</span>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`heatmap-chart-container ${className}`}
      data-testid={dataTestId}
      style={{
        width,
        height,
        position: 'relative'
      }}
    >
      <canvas ref={canvasRef} />
      <ColorScale />
    </div>
  )
}

export default HeatmapChart