// Import Chart.js configuration first
import './ChartConfig';

// Export all chart components
export { default as SharpeRatioChart } from './SharpeRatioChart';
export { default as MaxDrawdownChart } from './MaxDrawdownChart';
export { default as StrategyRadarChart } from './StrategyRadarChart';
export { default as ChartsDashboard } from './ChartsDashboard';
export { default as ChartsDemo } from './ChartsDemo';

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