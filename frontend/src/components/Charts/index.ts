// Import Chart.js configuration first
import '../Charts/ChartConfig';

// Re-export all types from chart.ts
export * from '../../types/chart';

// ============================================================================
// Base Components
// ============================================================================
export { ChartContainer } from '../Charts/base/ChartContainer';
export { default as BaseChart } from '../Charts/common/BaseChart';
export { ChartToolbar } from '../Charts/common/ChartToolbar';

// ============================================================================
// Chart.js Components
// ============================================================================
export { LineChart } from '../Charts/chartjs/LineChart';
export { BarChart } from '../Charts/chartjs/BarChart';
export { PieChart } from '../Charts/chartjs/PieChart';
export { AreaChart } from '../Charts/chartjs/AreaChart';
export { RadarChart } from '../Charts/chartjs/RadarChart';

// ============================================================================
// Plotly.js Components
// ============================================================================
export { CandlestickChart } from '../Charts/plotly/CandlestickChart';
export { OHLCChart } from '../Charts/plotly/OHLCChart';
export { VolumeChart } from '../Charts/plotly/VolumeChart';
export { ScatterPlot } from '../Charts/plotly/ScatterPlot';
export { Heatmap } from '../Charts/plotly/Heatmap';
export { RealTimeChart } from '../Charts/plotly/RealTimeChart';
export { ThreeDChart } from '../Charts/plotly/ThreeDChart';

// ============================================================================
// Composite Components
// ============================================================================
export { TradingViewChart } from '../Charts/composite/TradingViewChart';

// ============================================================================
// Legacy Chart Components
// ============================================================================
export { default as SharpeRatioChart } from '../Charts/SharpeRatioChart';
export { default as MaxDrawdownChart } from '../Charts/MaxDrawdownChart';
export { default as StrategyRadarChart } from '../Charts/StrategyRadarChart';
export { default as StrategyPerformanceChart } from '../Charts/StrategyPerformanceChart';
export { default as PerformanceChart } from '../Charts/PerformanceChart';

// ============================================================================
// Dashboard Components
// ============================================================================
export { default as ChartsDashboard } from '../Charts/ChartsDashboard';
export { default as ChartsDemo } from '../Charts/ChartsDemo';
export { RealTimeDashboard } from '../Charts/RealTimeDashboard';

// ============================================================================
// Chart Manager and State Management
// ============================================================================
export {
  ChartManagerProvider,
  useChartManager,
  useChartRegistration,
  useRealTimeChartUpdate,
  useChartPerformance
} from '../Charts/ChartManager';

// ============================================================================
// Hooks
// ============================================================================
export { useRealTimeChart } from '../Charts/hooks/useRealTimeChart';
export { useChartExport } from '../Charts/hooks/useChartExport';

// ============================================================================
// Chart Themes and Utilities
// ============================================================================
export {
  getChartJsDefaults,
  getPlotlyDefaults,
  themes,
  colorSchemes,
  squareLightTheme,
  darkTheme,
  cbscTheme,
  defaultChartConfig,
  getTheme
} from '../Charts/utils/chartThemes';

// Export theme utilities from legacy ChartTheme
export {
  chartTheme,
  getStrategyColor,
  getSharpeRatioColor,
  getDrawdownColor,
  chartFont
} from '../Charts/ChartTheme';

// ============================================================================
// Re-export Chart.js for convenience
// ============================================================================
export {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// ============================================================================
// Re-export Plotly.js for convenience
// ============================================================================
export {
  Plotly
} from 'plotly.js-dist-min';
