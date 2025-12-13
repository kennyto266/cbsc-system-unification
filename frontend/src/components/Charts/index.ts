// Import Chart.js configuration first
import './ChartConfig';

// Export legacy chart components
export { default as SharpeRatioChart } from './SharpeRatioChart';
export { default as MaxDrawdownChart } from './MaxDrawdownChart';
export { default as StrategyRadarChart } from './StrategyRadarChart';
export { default as ChartsDashboard } from './ChartsDashboard';
export { default as ChartsDemo } from './ChartsDemo';

// Export new chart components
// Common components
export { default as BaseChart } from './common/BaseChart';
export { ChartContainer } from './common/ChartContainer';
export { ChartToolbar } from './common/ChartToolbar';

// Chart.js components
export { LineChart } from './chartjs/LineChart';
export { BarChart } from './chartjs/BarChart';
export { PieChart } from './chartjs/PieChart';

// Plotly components
export { CandlestickChart } from './plotly/CandlestickChart';
export { RealTimeChart } from './plotly/RealTimeChart';
export { ThreeDChart } from './plotly/ThreeDChart';

// Hooks
export { useRealTimeChart } from './hooks/useRealTimeChart';
export { useChartExport } from './hooks/useChartExport';

// Dashboard
export { RealTimeDashboard } from './RealTimeDashboard';

// Export chart manager and utilities
export {
  ChartManagerProvider,
  useChartManager,
  useChartRegistration,
  useRealTimeChartUpdate,
  useChartPerformance
} from './ChartManager';

// Export theme utilities
export {
  chartTheme,
  getStrategyColor,
  getSharpeRatioColor,
  getDrawdownColor,
  chartFont
} from './ChartTheme';

// Re-export Chart.js components for convenience
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
