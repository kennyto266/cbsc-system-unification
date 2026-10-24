// Chart type definitions for real-time chart components

import { ReactNode } from 'react'

// Base chart configuration
export interface BaseChartProps {
  width?: number | string
  height?: number | string
  className?: string
  theme?: 'light' | 'dark'
  responsive?: boolean
  animation?: boolean
  dataTestId?: string
}

// Time series chart specific types
export interface TimeSeriesDataPoint {
  timestamp: Date | number | string
  value: number
  volume?: number
  metadata?: Record<string, any>
}

export interface TimeSeriesDataset {
  id: string
  label: string
  data: TimeSeriesDataPoint[]
  color?: string
  strokeWidth?: number
  fill?: boolean
  fillOpacity?: number
  strokeDasharray?: string
  symbol?: 'circle' | 'square' | 'triangle'
  yAxisId?: string
}

export interface TimeSeriesChartProps extends BaseChartProps {
  datasets: TimeSeriesDataset[]
  timeRange?: {
    start: Date | number | string
    end: Date | number | string
  }
  showGrid?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  showCrosshair?: boolean
  allowZoom?: boolean
  allowPan?: boolean
  timeFormat?: string
  valueFormat?: (value: number) => string
  onTimeRangeChange?: (range: { start: Date; end: Date }) => void
  onDataPointClick?: (point: TimeSeriesDataPoint, dataset: TimeSeriesDataset) => void
  yAxis?: {
    left?: YAxisConfig
    right?: YAxisConfig
  }
}

// Y-axis configuration
export interface YAxisConfig {
  id: string
  label?: string
  orientation: 'left' | 'right'
  domain?: ['auto' | number, 'auto' | number]
  format?: (value: number) => string
  showGrid?: boolean
}

// Heatmap chart types
export interface HeatmapDataPoint {
  x: number | string
  y: number | string
  value: number
  label?: string
}

export interface HeatmapDataset {
  data: HeatmapDataPoint[]
  colorScale?: {
    min: string
    max: string
    steps?: Array<{ value: number; color: string }>
  }
  cellSize?: number
  gap?: number
  showLabels?: boolean
  labelFormat?: (value: number) => string
}

export interface HeatmapChartProps extends BaseChartProps {
  dataset: HeatmapDataset
  xAxis: {
    label: string
    categories: Array<string | number>
  }
  yAxis: {
    label: string
    categories: Array<string | number>
  }
  showColorScale?: boolean
  colorScalePosition?: 'left' | 'right' | 'top' | 'bottom'
  onCellClick?: (point: HeatmapDataPoint) => void
  onCellHover?: (point: HeatmapDataPoint) => void
}

// Distribution chart types
export interface DistributionDataPoint {
  label: string
  value: number
  percentage?: number
  color?: string
}

export interface DistributionDataset {
  data: DistributionDataPoint[]
  type: 'bar' | 'pie' | 'donut' | 'horizontal-bar'
  showLabels?: boolean
  showValues?: boolean
  showPercentages?: boolean
  innerRadius?: number // for donut chart
  outerRadius?: number
  padAngle?: number // for pie/donut
}

export interface DistributionChartProps extends BaseChartProps {
  dataset: DistributionDataset
  sortOrder?: 'asc' | 'desc' | 'none'
  maxItems?: number
  onSliceClick?: (point: DistributionDataPoint) => void
  onBarClick?: (point: DistributionDataPoint) => void
  animationDuration?: number
}

// Chart interaction types
export interface ChartInteractionState {
  isHovering: boolean
  hoveredPoint?: any
  selectedPoints?: any[]
  zoomLevel?: number
  panOffset?: { x: number; y: number }
  crosshairPosition?: { x: number; y: number }
}

export interface ChartEventHandlers {
  onMouseMove?: (event: MouseEvent, chartState: ChartInteractionState) => void
  onMouseClick?: (event: MouseEvent, chartState: ChartInteractionState) => void
  onZoom?: (zoomLevel: number) => void
  onPan?: (panOffset: { x: number; y: number }) => void
  onBrush?: (range: { start: Date; end: Date }) => void
}

// Chart theme types
export interface ChartTheme {
  name: string
  colors: {
    primary: string[]
    secondary: string[]
    background: string
    foreground: string
    grid: string
    tooltip: {
      background: string
      foreground: string
      border: string
    }
  }
  typography: {
    fontFamily: string
    fontSize: {
      small: number
      medium: number
      large: number
    }
  }
  spacing: {
    xs: number
    sm: number
    md: number
    lg: number
    xl: number
  }
}

// Chart animation types
export interface ChartAnimationConfig {
  duration: number
  easing: string
  delay?: number
  stagger?: number
}

// Chart performance monitoring
export interface ChartPerformanceMetrics {
  renderTime: number
  updateCount: number
  lastUpdate: Date
  fps?: number
  memoryUsage?: number
  dataPointsCount: number
}

// Chart error types
export interface ChartError {
  code: string
  message: string
  details?: any
  timestamp: Date
}

// Chart reference types for imperative API
export interface ChartRef {
  updateData: (data: any) => void
  zoomTo: (range: { start: Date; end: Date }) => void
  resetZoom: () => void
  exportImage: (format: 'png' | 'svg' | 'pdf') => Promise<Blob>
  getPerformanceMetrics: () => ChartPerformanceMetrics
  destroy: () => void
}

// Legend configuration
export interface LegendConfig {
  show: boolean
  position: 'top' | 'bottom' | 'left' | 'right'
  orientation?: 'horizontal' | 'vertical'
  itemClick?: (datasetId: string) => void
  formatter?: (label: string, color: string) => ReactNode
}

// Tooltip configuration
export interface TooltipConfig {
  show: boolean
  followCursor?: boolean
  format?: {
    title: (value: any) => string
    value: (value: any) => string
  }
  customContent?: (props: any) => ReactNode
}

// Grid configuration
export interface GridConfig {
  show: boolean
  strokeDasharray?: string
  strokeOpacity?: number
  horizontal?: boolean
  vertical?: boolean
}