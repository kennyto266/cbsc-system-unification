import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components globally
export const registerChartJS = () => {
  // Only register if not already registered
  if (ChartJS.register) {
    ChartJS.register(
      CategoryScale,
      LinearScale,
      PointElement,
      LineElement,
      BarElement,
      RadialLinearScale,
      Title,
      Tooltip,
      Legend,
      Filler
    );
  }
};

// Configure Chart.js defaults
export const configureChartDefaults = () => {
  if (ChartJS.defaults) {
    // Set default font family
    ChartJS.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif';
    ChartJS.defaults.color = '#2c3e50';

    // Set default responsive options
    ChartJS.defaults.responsive = true;
    ChartJS.defaults.maintainAspectRatio = false;

    // Set default animation options
    ChartJS.defaults.animation.duration = 1000;
    ChartJS.defaults.animation.easing = 'easeInOutQuart';

    // Set default legend options
    ChartJS.defaults.plugins.legend.position = 'top';
    ChartJS.defaults.plugins.legend.labels.usePointStyle = true;
    ChartJS.defaults.plugins.legend.labels.pointStyle = 'circle';

    // Set default tooltip options
    ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    ChartJS.defaults.plugins.tooltip.titleFont.size = 14;
    ChartJS.defaults.plugins.tooltip.bodyFont.size = 12;
    ChartJS.defaults.plugins.tooltip.padding = 12;
    ChartJS.defaults.plugins.tooltip.cornerRadius = 8;
  }
};

// Auto-register and configure when this module is imported
registerChartJS();
configureChartDefaults();

export default ChartJS;