// Chart type definitions
export interface ChartDataPoint {
  x: number | string
  y: number
  label?: string
  color?: string
}

export interface TimeSeriesData {
  timestamp: string
  value: number
  volume?: number
  high?: number
  low?: number
  open?: number
  close?: number
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'candlestick' | 'pie' | 'area' | 'scatter'
  title: string
  data: ChartDataPoint[] | TimeSeriesData[]
  height?: number
  width?: number
  responsive?: boolean
  realTime?: boolean
  updateInterval?: number
  colors?: string[]
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  animationDuration?: number
}

export interface ChartTheme {
  backgroundColor: string
  gridColor: string
  textColor: string
  colors: string[]
}

export const defaultChartTheme: ChartTheme = {
  backgroundColor: 'transparent',
  gridColor: 'hsl(var(--border))',
  textColor: 'hsl(var(--foreground))',
  colors: [
    'hsl(var(--primary))',
    'hsl(var(--secondary))',
    'hsl(142, 76%, 36%)',
    'hsl(25, 95%, 53%)',
    'hsl(339, 86%, 58%)',
    'hsl(262, 83%, 58%)',
  ]
}

export const chartBreakpoints = {
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1400,
}