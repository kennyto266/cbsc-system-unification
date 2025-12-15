// Real-time Chart Components
export { default as RealTimeLineChart } from './RealTimeLineChart'
export { default as RealTimeBarChart } from './RealTimeBarChart'
export { default as RealTimeRadarChart } from './RealTimeRadarChart'
export { default as RealTimeHeatmap } from './RealTimeHeatmap'

// Re-export types
export type {
  RealTimeLineChartProps,
  RealTimeBarChartProps,
  RealTimeRadarChartProps,
  RealTimeHeatmapProps
} from './RealTimeLineChart'
export type {
  RealTimeBarChartProps as RealTimeBarChartPropsType
} from './RealTimeBarChart'
export type {
  RealTimeRadarChartProps as RealTimeRadarChartPropsType
} from './RealTimeRadarChart'
export type {
  RealTimeHeatmapProps as RealTimeHeatmapPropsType
} from './RealTimeHeatmap'

// Matrix data point type for heatmap
export interface MatrixDataPoint {
  x: string
  y: string
  v: number
  metadata?: Record<string, any>
}