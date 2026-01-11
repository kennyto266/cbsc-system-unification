import React, { useMemo, Suspense, lazy } from 'react';
import { HeatmapProps, HeatmapData, BaseChartProps } from '../../../types/chart';
import { getPlotlyDefaults, getTheme } from '../utils/chartThemes';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

interface ExtendedHeatmapProps extends Omit<BaseChartProps, 'data'> {
  data: HeatmapData[];
  colorScale?: string[];
  height?: number;
  className?: string;
  showValues?: boolean;
  valueFormat?: string;
  title?: string;
  subtitle?: string;
  reverseColorScale?: boolean;
  centerColorScale?: boolean;
  showScaleBar?: boolean;
  scaleBarTitle?: string;
  cellAspectRatio?: number;
}

export const Heatmap: React.FC<ExtendedHeatmapProps> = ({
  data,
  colorScale = [
    '#313695', // Dark blue
    '#4575b4',
    '#74add1',
    '#abd9e9',
    '#e0f3f8',
    '#ffffcc',
    '#fee090',
    '#fdae61',
    '#f46d43',
    '#d73027',
    '#a50026'  // Dark red
  ],
  height = 600,
  className = '',
  showValues = true,
  valueFormat = '.2f',
  title,
  subtitle,
  theme = 'light',
  onDataPointClick,
  reverseColorScale = false,
  centerColorScale = false,
  showScaleBar = true,
  scaleBarTitle = 'Value',
  cellAspectRatio = 1
}) => {
  // Process data for heatmap
  const { z, x, y, annotations } = useMemo(() => {
    // Get unique x and y values
    const xValues = Array.from(new Set(data.map(d => d.x))).sort();
    const yValues = Array.from(new Set(data.map(d => d.y))).sort();

    // Create 2D matrix
    const zMatrix: number[][] = [];
    const annotations: any[] = [];

    yValues.forEach((yVal, yIndex) => {
      const row: number[] = [];
      xValues.forEach((xVal, xIndex) => {
        const dataPoint = data.find(d => d.x === xVal && d.y === yVal);
        const value = dataPoint ? dataPoint.value : 0;
        row.push(value);

        // Add annotation for value display
        if (showValues && dataPoint) {
          annotations.push({
            x: xIndex,
            y: yIndex,
            text: value.toFixed(2),
            font: {
              color: getTheme(theme).textColor,
              size: 10
            },
            showarrow: false
          });
        }
      });
      zMatrix.push(row);
    });

    return {
      z: zMatrix,
      x: xValues,
      y: yValues,
      annotations
    };
  }, [data, theme, showValues]);

  // Calculate center point for color scale if needed
  const colorscale = useMemo(() => {
    let scale = [...colorScale];

    if (centerColorScale) {
      const allValues = data.map(d => d.value);
      const minVal = Math.min(...allValues);
      const maxVal = Math.max(...allValues);
      const midVal = (minVal + maxVal) / 2;

      // Find the midpoint index
      const midIndex = scale.length / 2;
      scale[midIndex] = '#ffffff'; // White at center
    }

    return reverseColorScale ? scale.reverse() : scale;
  }, [colorScale, reverseColorScale, centerColorScale, data]);

  // Prepare chart data
  const plotlyData = useMemo(() => {
    const traces: any[] = [];

    // Main heatmap trace
    traces.push({
      z: z,
      x: x,
      y: y,
      type: 'heatmap',
      colorscale: colorscale,
      hovertemplate: '<b>%{y}</b> vs <b>%{x}</b><br>' +
                     'Value: %{z}<extra></extra>',
      xaxis: 'x',
      yaxis: 'y',
      showscale: showScaleBar,
      colorbar: showScaleBar ? {
        title: {
          text: scaleBarTitle,
          side: 'right'
        },
        titleside: 'right',
        tickformat: valueFormat
      } : undefined,
      reversescale: reverseColorScale,
      zsmooth: false,
      zauto: true
    });

    return traces;
  }, [z, x, y, colorscale, reverseColorScale, showScaleBar, scaleBarTitle, valueFormat]);

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
      showlegend: false,
      xaxis: {
        ...baseLayout.xaxis,
        type: 'category',
        tickangle: -45
      },
      yaxis: {
        ...baseLayout.yaxis,
        type: 'category',
        autorange: 'reversed' // Display y-axis from top to bottom
      },
      margin: {
        l: Math.max(100, y.length * 10), // Adjust left margin based on y-label length
        r: showScaleBar ? 80 : 30,
        t: title ? 50 : 20,
        b: Math.max(80, x.length * 10) // Adjust bottom margin based on x-label length
      },
      annotations: [
        ...(subtitle ? [
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
        ] : []),
        ...annotations
      ],
      hovermode: 'closest'
    };
  }, [theme, title, subtitle, height, x, y, showScaleBar, annotations]);

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
      filename: `heatmap-${Date.now()}`,
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
      const xIndex = point.x;
      const yIndex = point.y;

      if (xIndex !== undefined && yIndex !== undefined) {
        // Find the actual data point
        const xVal = x[xIndex];
        const yVal = y[yIndex];
        const dataPoint = data.find(d => d.x === xVal && d.y === yVal);

        if (dataPoint) {
          onDataPointClick(dataPoint, point);
        }
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

export default Heatmap;