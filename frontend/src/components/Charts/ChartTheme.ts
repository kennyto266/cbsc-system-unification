// Chart theme configuration for consistent styling
export const chartTheme = {
  // Primary colors
  primary: '#3498db',      // Main blue
  success: '#27ae60',      // Success green
  warning: '#f39c12',      // Warning orange
  danger: '#e74c3c',       // Danger red
  info: '#9b59b6',         // Info purple
  dark: '#34495e',         // Dark gray
  light: '#ecf0f1',        // Light gray

  // Strategy-specific colors
  strategyColors: {
    'direct_rsi': '#3498db',
    'sentiment_momentum': '#27ae60',
    'composite_index': '#f39c12',
    'volatility_adjusted': '#e74c3c'
  },

  // Default chart configuration
  defaultOptions: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
            size: 12
          },
          color: '#2c3e50',
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle' as const
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
          size: 14,
          weight: 'bold'
        },
        bodyFont: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
          size: 12
        },
        padding: 12,
        cornerRadius: 8,
        boxPadding: 4,
        borderColor: '#e0e0e0',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false
        },
        ticks: {
          font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
            size: 11
          },
          color: '#6c757d'
        }
      },
      y: {
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false
        },
        ticks: {
          font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
            size: 11
          },
          color: '#6c757d'
        }
      }
    },
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart' as const
    }
  }
};

// Helper function to get strategy color with fallback
export const getStrategyColor = (strategyName: string): string => {
  // Try exact match first
  if (chartTheme.strategyColors[strategyName as keyof typeof chartTheme.strategyColors]) {
    return chartTheme.strategyColors[strategyName as keyof typeof chartTheme.strategyColors];
  }

  // Try partial match
  for (const [key, color] of Object.entries(chartTheme.strategyColors)) {
    if (strategyName.toLowerCase().includes(key.toLowerCase())) {
      return color;
    }
  }

  // Default color rotation for unknown strategies
  const colors = Object.values(chartTheme.strategyColors);
  const index = strategyName.length % colors.length;
  return colors[index];
};

// Performance level colors for Sharpe ratio
export const getSharpeRatioColor = (sharpeRatio: number): string => {
  if (sharpeRatio >= 1.5) return chartTheme.success;
  if (sharpeRatio >= 1.0) return chartTheme.primary;
  if (sharpeRatio >= 0.5) return chartTheme.warning;
  return chartTheme.danger;
};

// Risk level colors for drawdown
export const getDrawdownColor = (drawdown: number): string => {
  if (drawdown <= 5) return chartTheme.success;
  if (drawdown <= 10) return chartTheme.warning;
  return chartTheme.danger;
};

// Export Chart.js font configuration
export const chartFont = {
  family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
  size: 12,
  weight: 'normal' as const
};