/**
 * Advanced Chart Types
 * Type definitions for advanced chart components
 */

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
  loading?: boolean
  error?: string | null
}

// Chart theme configuration
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

// Heatmap chart types
export interface HeatmapDataPoint {
  x: number | string
  y: number | string
  value: number
  label?: string
  metadata?: Record<string, any>
}

export interface ColorScaleConfig {
  min: string
  max: string
  steps?: Array<{ value: number; color: string }>
  type?: 'sequential' | 'diverging' | 'reverse'
}

export interface HeatmapDataset {
  data: HeatmapDataPoint[]
  colorScale?: ColorScaleConfig
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
  onCellClick?: (data: HeatmapDataPoint) => void
  onCellHover?: (data: HeatmapDataPoint) => void
  title?: string
  subtitle?: string
}

// 3D Chart types
export interface Point3D {
  x: number
  y: number
  z: number
  color?: string
  size?: number
  label?: string
  metadata?: Record<string, any>
}

export interface SurfaceData {
  x: number[]
  y: number[]
  z: number[][]
  type: 'surface' | 'heatmap'
  colorscale?: string
}

export type ChartType3D = 'scatter3d' | 'surface' | 'mesh3d' | 'heatmap3d'

export interface ThreeDChartProps extends BaseChartProps {
  data: Point3D[] | SurfaceData
  chartType?: ChartType3D
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  colors?: {
    background?: string
    grid?: string
    surface?: string
  }
  camera?: {
    eye: { x: number; y: number; z: number }
    center: { x: number; y: number; z: number }
    up?: { x: number; y: number; z: number }
  }
  axes?: {
    x?: { title?: string; range?: [number, number] }
    y?: { title?: string; range?: [number, number] }
    z?: { title?: string; range?: [number, number] }
  }
  onPointClick?: (point: Point3D) => void
  onSurfaceClick?: (x: number, y: number, z: number) => void
  animationEnabled?: boolean
  colorScale?: string[] | string
  markerSize?: number
  lineWidth?: number
  opacity?: number
}

export interface ThreeDChartRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<void>
  getCamera: () => any
  setCamera: (camera: any) => void
  resetCamera: () => void
  spin: (duration?: number) => void
}

// Performance chart types
export interface PerformanceDataPoint {
  date: Date | string | number
  value: number
  benchmark?: number
  metadata?: Record<string, any>
}

export interface DrawdownDataPoint {
  date: Date | string | number
  drawdown: number
  underwater?: boolean
  metadata?: Record<string, any>
}

export interface PerformanceChartProps extends BaseChartProps {
  data: PerformanceDataPoint[]
  showBenchmark?: boolean
  showArea?: boolean
  valueFormat?: (value: number) => string
}

export interface DrawdownChartProps extends BaseChartProps {
  data: DrawdownDataPoint[]
  showZone?: boolean
  valueFormat?: (value: number) => string
}

// Chart container ref
export interface ChartRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<void>
  getDataURL: () => string
  resetZoom: () => void
}
