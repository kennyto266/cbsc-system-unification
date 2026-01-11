import { ChartData, ChartOptions, ChartType } from 'chart.js'

// Base Chart Data Types
export interface BaseChartDataPoint {
  x: string | number | Date
  y: number
  label?: string
}

export interface TimeSeriesDataPoint extends BaseChartDataPoint {
  timestamp: string | Date
  volume?: number
  high?: number
  low?: number
  open?: number
  close?: number
}

// Chart Data Interfaces
export interface LineChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
    tension?: number
    fill?: boolean
    [key: string]: any
  }[]
}

export interface BarChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string
    borderWidth?: number
    [key: string]: any
  }[]
}

export interface PieChartData {
  labels: string[]
  datasets: {
    data: number[]
    backgroundColor?: string[]
    borderColor?: string[]
    borderWidth?: number
    [key: string]: any
  }[]
}

export interface RadarChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
    pointBackgroundColor?: string
    pointBorderColor?: string
    [key: string]: any
  }[]
}

// OHLC/Candlestick Data for Plotly
export interface OHLCDataPoint {
  timestamp: string | Date
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

// Technical Indicators
export interface TechnicalIndicator {
  name: string
  data: number[]
  type: 'overlay' | 'oscillator'
  color: string
  parameters?: Record<string, any>
}

// Chart Theme Configuration
export interface ChartTheme {
  backgroundColor: string
  borderColor: string
  gridColor: string
  textColor: string
  colors: string[]
  fontFamily?: string
  fontSize?: number
}

// Chart Component Props
export interface BaseChartProps<T = any> {
  data: ChartData<T>
  options?: ChartOptions<T>
  type?: ChartType
  width?: number
  height?: number
  className?: string
  theme?: 'light' | 'dark'
  onDataPointClick?: (point: any, element: any) => void
  onLegendClick?: (item: any, legend: any) => void
}

export interface TrendChartProps {
  data: TimeSeriesDataPoint[]
  timeRange?: [Date, Date]
  showVolume?: boolean
  showMovingAverages?: number[]
  indicators?: TechnicalIndicator[]
  height?: number
  onDataPointClick?: (point: TimeSeriesDataPoint) => void
}

export interface CandlestickChartProps {
  data: OHLCDataPoint[]
  volume?: number[]
  indicators?: TechnicalIndicator[]
  timeRange?: [Date, Date]
  onTimeRangeChange?: (range: [Date, Date]) => void
  height?: number
}

export interface VolumeChartProps {
  data: { timestamp: string | Date; volume: number }[]
  color?: string
  height?: number
}

export interface ScatterPlotProps {
  data: { x: number; y: number; label?: string }[]
  xAxisLabel?: string
  yAxisLabel?: string
  showTrendLine?: boolean
  height?: number
}

export interface HeatmapData {
  x: string
  y: string
  value: number
}

export interface HeatmapProps {
  data: HeatmapData[]
  colorScale?: string[]
  height?: number
}

// Chart Export Options
export interface ChartExportOptions {
  format: 'png' | 'jpg' | 'svg' | 'pdf'
  width?: number
  height?: number
  quality?: number
  backgroundColor?: string
}

// Real-time Chart Configuration
export interface RealtimeChartConfig {
  symbol: string
  interval: number // milliseconds
  maxDataPoints: number
  enableAnimation: boolean
  buffer_size?: number
}

// Chart Animation Options
export interface ChartAnimationOptions {
  duration: number
  easing: 'linear' | 'easeInQuad' | 'easeOutQuad' | 'easeInOutQuad'
  delay?: number
}

// Chart Zoom and Pan Options
export interface ChartZoomOptions {
  enable: boolean
  mode: 'x' | 'y' | 'xy'
  wheelEnabled?: boolean
  pinchEnabled?: boolean
  dragEnabled?: boolean
}

// Chart Tooltip Options
export interface ChartTooltipOptions {
  enabled: boolean
  mode: 'index' | 'dataset' | 'point' | 'nearest'
  intersect?: boolean
  backgroundColor?: string
  titleColor?: string
  bodyColor?: string
  borderColor?: string
  borderWidth?: number
  cornerRadius?: number
  displayColors?: boolean
  callbacks?: {
    title?: (items: any[]) => string
    label?: (context: any) => string
    afterLabel?: (context: any) => string
  }
}

// Chart Legend Options
export interface ChartLegendOptions {
  display: boolean
  position: 'top' | 'bottom' | 'left' | 'right'
  align?: 'start' | 'center' | 'end'
  labels?: {
    boxWidth?: number
    boxHeight?: number
    padding?: number
    font?: {
      size?: number
      family?: string
      weight?: string
    }
    generateLabels?: (chart: any) => any[]
  }
}

// Complete Chart Configuration
export interface ChartConfig {
  theme: ChartTheme
  animation: ChartAnimationOptions
  zoom: ChartZoomOptions
  tooltip: ChartTooltipOptions
  legend: ChartLegendOptions
  responsive: boolean
  maintainAspectRatio: boolean
  devicePixelRatio?: number
}

// Market Data Types for Charts
export interface MarketData {
  symbol: string
  timestamp: Date
  price: number
  change: number
  changePercent: number
  volume: number
  high: number
  low: number
  open: number
  close: number
  bid?: number
  ask?: number
}

// Portfolio Performance Data
export interface PortfolioPerformance {
  date: string
  value: number
  return: number
  benchmark?: number
}

// Strategy Performance Metrics
export interface StrategyMetrics {
  date: string
  equity: number
  drawdown: number
  sharpe: number
  winRate: number
  profitFactor: number
}

// Correlation Matrix Data
export interface CorrelationData {
  assets: string[]
  matrix: number[][]
}