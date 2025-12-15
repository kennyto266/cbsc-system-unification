import { ChartTheme, ChartConfig } from '../../../types/chart'

// Square-UI Light Theme
export const squareLightTheme: ChartTheme = {
  backgroundColor: 'transparent',
  borderColor: '#e8e8e8',
  gridColor: '#f0f0f0',
  textColor: '#262626',
  colors: [
    '#1890ff', // Blue
    '#52c41a', // Green
    '#faad14', // Gold
    '#f5222d', // Red
    '#722ed1', // Purple
    '#13c2c2', // Cyan
    '#eb2f96', // Magenta
    '#fa8c16', // Orange
    '#a0d911', // Lime
    '#fadb14', // Yellow
  ],
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontSize: 12
}

// Dark Theme
export const darkTheme: ChartTheme = {
  backgroundColor: '#141414',
  borderColor: '#434343',
  gridColor: '#303030',
  textColor: '#ffffff',
  colors: [
    '#177ddc', // Blue
    '#49aa19', // Green
    '#d89614', // Gold
    '#dc4446', // Red
    '#642ab5', // Purple
    '#39a9c9', // Cyan
    '#d32029', // Magenta
    '#cf1322', // Orange
    '#95de64', // Lime
    '#ffd666', // Yellow
  ],
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontSize: 12
}

// CBSC Brand Theme
export const cbscTheme: ChartTheme = {
  backgroundColor: 'transparent',
  borderColor: '#d9d9d9',
  gridColor: '#f5f5f5',
  textColor: '#333333',
  colors: [
    '#2f54eb', // Primary Blue
    '#52c41a', // Success Green
    '#fa8c16', // Warning Orange
    '#ff4d4f', // Error Red
    '#722ed1', // Purple
    '#13c2c2', // Cyan
    '#eb2f96', // Magenta
    '#faad14', // Gold
    '#1890ff', // Secondary Blue
    '#36cfc9', // Teal
  ],
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontSize: 12
}

// Default Chart Configurations
export const defaultChartConfig: ChartConfig = {
  theme: squareLightTheme,
  animation: {
    duration: 300,
    easing: 'easeInOutQuad'
  },
  zoom: {
    enable: false,
    mode: 'x'
  },
  tooltip: {
    enabled: true,
    mode: 'index',
    intersect: false,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    titleColor: '#ffffff',
    bodyColor: '#ffffff',
    borderColor: '#333333',
    borderWidth: 1,
    cornerRadius: 4,
    displayColors: true
  },
  legend: {
    display: true,
    position: 'top',
    align: 'center',
    labels: {
      boxWidth: 12,
      boxHeight: 12,
      padding: 20,
      font: {
        size: 12,
        family: squareLightTheme.fontFamily,
        weight: 'normal'
      }
    }
  },
  responsive: true,
  maintainAspectRatio: false,
  devicePixelRatio: window.devicePixelRatio || 1
}

// Chart.js Default Options
export const getChartJsDefaults = (theme: ChartTheme = squareLightTheme): any => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 300,
    easing: 'easeInOutQuad'
  },
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      align: 'center',
      labels: {
        boxWidth: 12,
        boxHeight: 12,
        padding: 20,
        font: {
          size: theme.fontSize,
          family: theme.fontFamily
        },
        color: theme.textColor
      }
    },
    tooltip: {
      enabled: true,
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333333',
      borderWidth: 1,
      cornerRadius: 4,
      displayColors: true,
      titleFont: {
        size: theme.fontSize,
        weight: 'bold',
        family: theme.fontFamily
      },
      bodyFont: {
        size: theme.fontSize,
        family: theme.fontFamily
      },
      padding: 10,
      displayColors: true,
      boxPadding: 4
    }
  },
  scales: {
    x: {
      grid: {
        color: theme.gridColor,
        borderDash: [2, 2]
      },
      ticks: {
        color: theme.textColor,
        font: {
          size: theme.fontSize,
          family: theme.fontFamily
        }
      },
      border: {
        color: theme.borderColor
      }
    },
    y: {
      grid: {
        color: theme.gridColor,
        borderDash: [2, 2]
      },
      ticks: {
        color: theme.textColor,
        font: {
          size: theme.fontSize,
          family: theme.fontFamily
        }
      },
      border: {
        color: theme.borderColor
      }
    }
  }
})

// Plotly.js Default Layout
export const getPlotlyDefaults = (theme: ChartTheme = squareLightTheme): any => ({
  paper_bgcolor: theme.backgroundColor,
  plot_bgcolor: theme.backgroundColor,
  font: {
    family: theme.fontFamily,
    size: theme.fontSize,
    color: theme.textColor
  },
  margin: {
    l: 50,
    r: 30,
    t: 30,
    b: 50
  },
  showlegend: true,
  legend: {
    orientation: 'h',
    yanchor: 'bottom',
    y: 1.02,
    xanchor: 'right',
    x: 1,
    bgcolor: theme.backgroundColor,
    bordercolor: theme.borderColor,
    borderwidth: 1,
    font: {
      size: theme.fontSize,
      color: theme.textColor
    }
  },
  xaxis: {
    gridcolor: theme.gridColor,
    gridwidth: 1,
    zerolinecolor: theme.borderColor,
    zerolinewidth: 1,
    showgrid: true,
    tickfont: {
      size: theme.fontSize,
      color: theme.textColor
    }
  },
  yaxis: {
    gridcolor: theme.gridColor,
    gridwidth: 1,
    zerolinecolor: theme.borderColor,
    zerolinewidth: 1,
    showgrid: true,
    tickfont: {
      size: theme.fontSize,
      color: theme.textColor
    }
  },
  hovermode: 'x unified',
  hoverlabel: {
    bgcolor: 'rgba(0, 0, 0, 0.8)',
    bordercolor: '#333333',
    font: {
      size: theme.fontSize,
      color: '#ffffff'
    }
  }
})

// Color Schemes
export const colorSchemes = {
  default: squareLightTheme.colors,
  monochrome: ['#f0f0f0', '#d9d9d9', '#bfbfbf', '#8c8c8c', '#595959', '#262626'],
  warm: ['#ff4d4f', '#ff7a45', '#ffa940', '#ffd666', '#fff1b8'],
  cool: ['#1890ff', '#40a9ff', '#69c0ff', '#91d5ff', '#bae7ff'],
  nature: ['#52c41a', '#73d13d', '#95de64', '#b7eb8f', '#d9f7be'],
  financial: [
    '#2f54eb', // Bullish
    '#f5222d', // Bearish
    '#52c41a', // Profit
    '#fa8c16', // Loss
    '#722ed1', // Neutral
  ]
}

// Export all themes
export const themes = {
  light: squareLightTheme,
  dark: darkTheme,
  cbsc: cbscTheme
}

// Theme resolver
export const getTheme = (themeName: 'light' | 'dark' | 'cbsc' = 'light'): ChartTheme => {
  return themes[themeName] || squareLightTheme
}