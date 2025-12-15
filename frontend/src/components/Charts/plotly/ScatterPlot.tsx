import React, { useMemo, Suspense, lazy } from 'react';
import { ScatterPlotProps, BaseChartProps } from '../../../types/chart';
import { getPlotlyDefaults, getTheme } from '../utils/chartThemes';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

interface DataPoint {
  x: number;
  y: number;
  label?: string;
  size?: number;
  color?: string | number;
}

interface Dataset {
  name: string;
  data: DataPoint[];
  color?: string;
  size?: number;
  opacity?: number;
  symbol?: string;
  showTrendLine?: boolean;
}

interface ExtendedScatterPlotProps extends Omit<BaseChartProps, 'data'> {
  datasets: Dataset[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  showLegend?: boolean;
  title?: string;
  subtitle?: string;
  bubbleMode?: boolean;
  sizeRange?: [number, number];
  colorScale?: string[];
  regressionLine?: boolean;
  confidenceInterval?: number;
}

export const ScatterPlot: React.FC<ExtendedScatterPlotProps> = ({
  datasets,
  xAxisLabel = 'X Axis',
  yAxisLabel = 'Y Axis',
  showLegend = true,
  title,
  subtitle,
  height = 600,
  className = '',
  theme = 'light',
  onDataPointClick,
  bubbleMode = false,
  sizeRange = [5, 20],
  colorScale,
  regressionLine = false,
  confidenceInterval = 0.95
}) => {
  // Calculate trend line for a dataset
  const calculateTrendLine = (data: DataPoint[]) => {
    const n = data.length;
    if (n < 2) return null;

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    data.forEach(point => {
      sumX += point.x;
      sumY += point.y;
      sumXY += point.x * point.y;
      sumX2 += point.x * point.x;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const xMin = Math.min(...data.map(p => p.x));
    const xMax = Math.max(...data.map(p => p.x));

    return {
      x: [xMin, xMax],
      y: [xMin * slope + intercept, xMax * slope + intercept],
      equation: `y = ${slope.toFixed(2)}x + ${intercept.toFixed(2)}`,
      r2: calculateR2(data, slope, intercept)
    };
  };

  // Calculate R-squared for trend line
  const calculateR2 = (data: DataPoint[], slope: number, intercept: number) => {
    const yMean = data.reduce((sum, p) => sum + p.y, 0) / data.length;
    let ssTotal = 0, ssResidual = 0;

    data.forEach(point => {
      const yPredicted = slope * point.x + intercept;
      ssTotal += Math.pow(point.y - yMean, 2);
      ssResidual += Math.pow(point.y - yPredicted, 2);
    });

    return 1 - (ssResidual / ssTotal);
  };

  // Prepare chart data
  const plotlyData = useMemo(() => {
    const traces: any[] = [];
    const chartTheme = getTheme(theme);

    datasets.forEach((dataset, datasetIndex) => {
      // Main scatter plot
      const marker: any = {
        size: bubbleMode
          ? dataset.data.map(d => {
              if (d.size !== undefined) {
                const minSize = Math.min(...dataset.data.map(p => p.size || 1));
                const maxSize = Math.max(...dataset.data.map(p => d.size || 1));
                const normalized = (d.size - minSize) / (maxSize - minSize);
                return sizeRange[0] + normalized * (sizeRange[1] - sizeRange[0]);
              }
              return dataset.size || 8;
            })
          : dataset.size || 8,
        color: dataset.data.map(d => d.color !== undefined ? d.color : dataset.color || chartTheme.colors[datasetIndex % chartTheme.colors.length]),
        opacity: dataset.opacity || 0.8,
        symbol: dataset.symbol || 'circle',
        line: {
          color: chartTheme.borderColor,
          width: 0.5
        }
      };

      // Add color scale if values are numeric
      if (dataset.data.some(d => typeof d.color === 'number')) {
        marker.colorscale = colorScale || 'Viridis';
        marker.showscale = datasetIndex === 0;
        marker.colorbar = {
          title: 'Value',
          titleside: 'right'
        };
      }

      traces.push({
        x: dataset.data.map(d => d.x),
        y: dataset.data.map(d => d.y),
        text: dataset.data.map(d => d.label || `(${d.x}, ${d.y})`),
        type: 'scatter',
        mode: 'markers',
        name: dataset.name,
        marker: marker,
        hovertemplate: `<b>${dataset.name}</b><br>` +
                       'X: %{x}<br>' +
                       'Y: %{y}<br>' +
                       '%{text}<br>' +
                       '<extra></extra>',
        xaxis: 'x',
        yaxis: 'y'
      });

      // Add trend line if enabled
      if ((dataset.showTrendLine || regressionLine) && dataset.data.length >= 2) {
        const trendLine = calculateTrendLine(dataset.data);
        if (trendLine) {
          traces.push({
            x: trendLine.x,
            y: trendLine.y,
            type: 'scatter',
            mode: 'lines',
            name: `${dataset.name} Trend`,
            line: {
              color: dataset.color || chartTheme.colors[datasetIndex % chartTheme.colors.length],
              width: 2,
              dash: 'dash'
            },
            hovertemplate: `<b>Trend Line</b><br>` +
                           `Equation: ${trendLine.equation}<br>` +
                           `R²: ${trendLine.r2.toFixed(3)}<br>` +
                           '<extra></extra>',
            showlegend: false,
            xaxis: 'x',
            yaxis: 'y'
          });
        }
      }
    });

    return traces;
  }, [datasets, theme, bubbleMode, sizeRange, colorScale, regressionLine]);

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
        title: xAxisLabel,
        type: 'linear',
        zeroline: true,
        zerolinecolor: baseLayout.gridColor,
        zerolinewidth: 1
      },
      yaxis: {
        ...baseLayout.yaxis,
        title: yAxisLabel,
        type: 'linear',
        zeroline: true,
        zerolinecolor: baseLayout.gridColor,
        zerolinewidth: 1
      },
      margin: {
        l: 80,
        r: 30,
        t: title ? 50 : 20,
        b: 80
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
      hovermode: 'closest'
    };
  }, [theme, title, subtitle, height, showLegend, xAxisLabel, yAxisLabel]);

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
      filename: `scatter-plot-${Date.now()}`,
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
      const datasetIndex = point.curveNumber;
      const pointIndex = point.pointIndex;

      if (datasetIndex !== undefined && pointIndex !== undefined && datasets[datasetIndex]) {
        const dataPoint = datasets[datasetIndex].data[pointIndex];
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

export default ScatterPlot;