import React, { useMemo, Suspense, lazy } from 'react';
import { VolumeChartProps, BaseChartProps } from '../../../types/chart';
import { getPlotlyDefaults, getTheme, colorSchemes } from '../utils/chartThemes';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

interface ExtendedVolumeChartProps extends Omit<BaseChartProps, 'data'> {
  data: { timestamp: string | Date; volume: number }[];
  color?: string;
  height?: number;
  className?: string;
  showLegend?: boolean;
  title?: string;
  subtitle?: string;
  barWidth?: number;
  opacity?: number;
  showMovingAverage?: boolean;
  movingAveragePeriod?: number;
  autoScale?: boolean;
  logScale?: boolean;
}

export const VolumeChart: React.FC<ExtendedVolumeChartProps> = ({
  data,
  color = '#3b82f6',
  height = 400,
  className = '',
  showLegend = false,
  title,
  subtitle,
  theme = 'light',
  onDataPointClick,
  barWidth = 0.8,
  opacity = 0.7,
  showMovingAverage = false,
  movingAveragePeriod = 10,
  autoScale = true,
  logScale = false
}) => {
  // Calculate moving average for volume
  const movingAverage = useMemo(() => {
    if (!showMovingAverage) return [];

    const ma: number[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < movingAveragePeriod - 1) {
        ma.push(null);
      } else {
        const sum = data.slice(i - movingAveragePeriod + 1, i + 1)
          .reduce((acc, d) => acc + d.volume, 0);
        ma.push(sum / movingAveragePeriod);
      }
    }
    return ma;
  }, [data, showMovingAverage, movingAveragePeriod]);

  // Prepare chart data
  const plotlyData = useMemo(() => {
    const traces: any[] = [];
    const chartTheme = getTheme(theme);

    // Volume bars with gradient color based on value
    const maxVolume = Math.max(...data.map(d => d.volume));
    const minVolume = Math.min(...data.map(d => d.volume));
    const volumeRange = maxVolume - minVolume || 1;

    const volumeColors = data.map(d => {
      // Create gradient effect based on volume intensity
      const intensity = (d.volume - minVolume) / volumeRange;
      if (typeof color === 'string' && color.startsWith('#')) {
        // Convert hex to RGB and apply intensity
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity * (0.5 + intensity * 0.5)})`;
      }
      return color;
    });

    traces.push({
      x: data.map(d => d.timestamp),
      y: data.map(d => d.volume),
      type: 'bar',
      name: 'Volume',
      marker: {
        color: volumeColors,
        line: {
          color: chartTheme.borderColor,
          width: 0
        },
        width: barWidth
      },
      hovertemplate: '<b>Volume</b><br>' +
                     'Date: %{x}<br>' +
                     'Volume: %{y:,.0f}<br>' +
                     'Relative: %{marker.color}<extra></extra>',
      xaxis: 'x',
      yaxis: 'y'
    });

    // Moving average line
    if (showMovingAverage && movingAverage.length > 0) {
      traces.push({
        x: data.map(d => d.timestamp),
        y: movingAverage,
        type: 'scatter',
        mode: 'lines',
        name: `MA${movingAveragePeriod}`,
        line: {
          color: chartTheme.colors[1],
          width: 2
        },
        hovertemplate: '<b>Volume MA</b><br>' +
                       'Date: %{x}<br>' +
                       'Avg Volume: %{y:,.0f}<extra></extra>',
        xaxis: 'x',
        yaxis: 'y'
      });
    }

    return traces;
  }, [data, color, opacity, barWidth, showMovingAverage, movingAverage, movingAveragePeriod, theme]);

  // Chart layout
  const layout = useMemo(() => {
    const baseLayout = getPlotlyDefaults(getTheme(theme));

    return {
      ...baseLayout,
      title: title ? {
        text: title,
        font: {
          size: 18,
          ...baseLayout.font
        }
      } : undefined,
      height,
      showlegend: showLegend,
      xaxis: {
        ...baseLayout.xaxis,
        type: 'date'
      },
      yaxis: {
        ...baseLayout.yaxis,
        title: 'Volume',
        type: logScale ? 'log' : 'linear',
        autorange: autoScale,
        tickformat: ',.0f'
      },
      margin: {
        l: 80,
        r: 30,
        t: title ? 50 : 20,
        b: 50
      },
      annotations: subtitle ? [
        {
          xref: 'paper',
          yref: 'paper',
          x: 0,
          y: 1.1,
          xanchor: 'left',
          yanchor: 'bottom',
          text: subtitle,
          showarrow: false,
          font: {
            size: 12,
            color: baseLayout.font.color
          }
        }
      ] : undefined,
      hovermode: 'x unified',
      bargap: 0.1,
      bargroupgap: 0.1
    };
  }, [theme, title, subtitle, height, showLegend, autoScale, logScale]);

  // Chart config
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'pan2d',
      'select2d',
      'lasso2d',
      'toggleSpikelines'
    ],
    toImageButtonOptions: {
      format: 'png',
      filename: `volume-chart-${Date.now()}`,
      height: height,
      width: 1200,
      scale: 2
    },
    responsive: true
  }), [height]);

  // Handle click events
  const handlePlotClick = (event: any) => {
    if (onDataPointClick && event.points && event.points.length > 0) {
      const point = event.points[0];
      const index = point.pointIndex;
      if (index !== undefined && data[index]) {
        onDataPointClick(data[index], point);
      }
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <Suspense fallback={<div className="flex items-center justify-center h-64">Loading chart...</div>}>
        <Plot
          data={plotlyData}
          layout={layout}
          config={config}
          onClick={handlePlotClick}
          className="w-full"
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </Suspense>
    </div>
  );
};

export default VolumeChart;