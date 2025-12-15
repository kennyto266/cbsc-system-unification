import React, { useMemo, Suspense, lazy } from 'react';
import { OHLCDataPoint, BaseChartProps } from '../../../types/chart';
import { getPlotlyDefaults, getTheme } from '../utils/chartThemes';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

interface OHLCChartProps extends Omit<BaseChartProps, 'data'> {
  data: OHLCDataPoint[];
  showVolume?: boolean;
  volumeOpacity?: number;
  showLegend?: boolean;
  title?: string;
  subtitle?: string;
  barWidth?: number;
  bullishColor?: string;
  bearishColor?: string;
  groupBars?: boolean;
}

export const OHLCChart: React.FC<OHLCChartProps> = ({
  data,
  showVolume = false,
  volumeOpacity = 0.5,
  showLegend = true,
  title,
  subtitle,
  height = 600,
  className = '',
  theme = 'light',
  onDataPointClick,
  barWidth = 0.8,
  bullishColor = '#10b981',
  bearishColor = '#ef4444',
  groupBars = true
}) => {
  // Prepare OHLC chart data
  const plotlyData = useMemo(() => {
    const traces: any[] = [];

    // Create OHLC traces using scatter plot with lines for each price level
    // Open price bars
    traces.push({
      x: data.map(d => d.timestamp),
      y: data.map(d => d.open),
      type: 'scatter',
      mode: 'markers',
      name: 'Open',
      marker: {
        symbol: 'line-ns-open',
        color: data.map((_, i) => i === 0 ? '#6b7280' : data[i].close >= data[i - 1].close ? bullishColor : bearishColor),
        size: 12,
        line: {
          width: 2
        }
      },
      hovertemplate: '<b>Open</b><br>' +
                     'Date: %{x}<br>' +
                     'Price: %{y}<br>' +
                     '<extra></extra>',
      xaxis: 'x',
      yaxis: 'y'
    });

    // High-Low lines
    const highLowLines = data.map(d => [d.low, d.high]).flat();
    const highLowX = data.flatMap(d => [d.timestamp, d.timestamp, null]);

    traces.push({
      x: highLowX,
      y: highLowLines,
      type: 'scatter',
      mode: 'lines',
      name: 'High-Low',
      line: {
        color: '#374151',
        width: 1
      },
      hoverinfo: 'skip',
      showlegend: false,
      xaxis: 'x',
      yaxis: 'y'
    });

    // Close price markers
    traces.push({
      x: data.map(d => d.timestamp),
      y: data.map(d => d.close),
      type: 'scatter',
      mode: 'markers',
      name: 'Close',
      marker: {
        symbol: 'line-ns',
        color: data.map((_, i) => i === 0 ? '#6b7280' : data[i].close >= data[i - 1].close ? bullishColor : bearishColor),
        size: 12,
        line: {
          width: 2
        }
      },
      hovertemplate: '<b>Close</b><br>' +
                     'Date: %{x}<br>' +
                     'Price: %{y}<br>' +
                     '<extra></extra>',
      xaxis: 'x',
      yaxis: 'y'
    });

    // Volume bars
    if (showVolume && data.every(d => d.volume !== undefined)) {
      const volumeColors = data.map((d, i) => {
        if (i === 0) return '#94a3b8';
        return d.close >= data[i - 1].close ? bullishColor : bearishColor;
      });

      traces.push({
        x: data.map(d => d.timestamp),
        y: data.map(d => d.volume || 0),
        type: 'bar',
        name: 'Volume',
        marker: {
          color: volumeColors,
          opacity: volumeOpacity,
          width: barWidth
        },
        hovertemplate: '<b>Volume</b><br>' +
                       'Date: %{x}<br>' +
                       'Volume: %{y:,.0f}<br>' +
                       '<extra></extra>',
        xaxis: 'x',
        yaxis: 'y2'
      });
    }

    return traces;
  }, [data, showVolume, bullishColor, bearishColor, volumeOpacity, barWidth]);

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
        title: 'Price',
        domain: showVolume ? [0.3, 1] : [0, 1],
        autorange: true
      },
      yaxis2: showVolume ? {
        ...baseLayout.yaxis,
        title: 'Volume',
        domain: [0, 0.2],
        anchor: 'free',
        overlaying: 'y',
        side: 'right',
        position: 0.98,
        showgrid: false
      } : undefined,
      margin: {
        l: 60,
        r: showVolume ? 80 : 30,
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
      hovermode: 'x unified'
    };
  }, [theme, title, subtitle, height, showLegend, showVolume]);

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
      filename: `ohlc-chart-${Date.now()}`,
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
      <Suspense fallback={<div className="flex items-center justify-center h-96">Loading chart...</div>}>
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

export default OHLCChart;