// Main visualization components
export { default as DualAxisChart } from './DualAxisChart'
export { default as MixedStrategyViewer } from './MixedStrategyViewer'
export { default as TimeframeSelector } from './TimeframeSelector'
export { default as WeightAnalysis } from './WeightAnalysis'
export { default as ParameterPreview } from './ParameterPreview'
export { default as SensitivityAnalysis } from './SensitivityAnalysis'

// Export types
export type {
  MixedStrategyData,
  ChartThresholds,
  ChartColors
} from './DualAxisChart'

export type {
  Timeframe
} from './TimeframeSelector'

export type {
  StrategyWeights,
  StrategyContribution,
  CorrelationMatrix
} from './WeightAnalysis'

export type {
  ParameterType,
  ParameterConfig,
  StrategyParameters,
  PreviewResults,
  ParameterImpact
} from './ParameterPreview'

export type {
  SensitivityPoint,
  SensitivityData,
  HeatmapPoint,
  HeatmapConfig,
  OptimalParameters,
  ParameterRecommendation
} from './SensitivityAnalysis'