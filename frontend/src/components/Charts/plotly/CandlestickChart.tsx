import React, { useMemo, Suspense, lazy } from 'react';
import { OHLCDataPoint, TechnicalIndicator, BaseChartProps } from '../../../types/chart';
import { getPlotlyDefaults, getTheme, colorSchemes } from '../utils/chartThemes';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

interface CandlestickChartProps extends Omit<BaseChartProps, 'data'> {
  data: OHLCDataPoint[];
  showVolume?: boolean;
  showMovingAverages?: number[];
  indicators?: TechnicalIndicator[];
  timeRange?: [Date, Date];
  onTimeRangeChange?: (range: [Date, Date]) => void;
  bullishColor?: string;
  bearishColor?: string;
  volumeOpacity?: number;
  showLegend?: boolean;
  title?: string;
  subtitle?: string;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  showVolume = false,
  showMovingAverages = [],
  indicators = [],
  timeRange,
  onTimeRangeChange,
  bullishColor = '#10b981',
  bearishColor = '#ef4444',
  volumeOpacity = 0.5,
  showLegend = true,
  title,
  subtitle,
  height = 600,
  className = '',
  theme = 'light',
  onDataPointClick
}) => {
  // Calculate moving averages
  const movingAverages = useMemo(() => {
    const maMap = new Map<number, number[]>();

    showMovingAverages.forEach(period => {
      const ma: number[] = [];
      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
          ma.push(null);
        } else {
          const sum = data.slice(i - period + 1, i + 1).reduce((acc, d) => acc + d.close, 0);
          ma.push(sum / period);
        }
      }
      maMap.set(period, ma);
    });

    return maMap;
  }, [data, showMovingAverages]);

  // Prepare chart data
  const plotlyData = useMemo(() => {
    const traces: any[] = [];
    const chartTheme = getTheme(theme);

    // Candlestick trace
    traces.push({
      type: 'candlestick',
      x: data.map(d => d.timestamp),
      open: data.map(d => d.open),
      high: data.map(d => d.high),
      low: data.map(d => d.low),
      close: data.map(d => d.close),
      name: 'Price',
      increasing: {
        line: { color: bullishColor },
        fillcolor: bullishColor
      },
      decreasing: {
        line: { color: bearishColor },
        fillcolor: bearishColor
      },
      xaxis: 'x',
      yaxis: 'y'
    });

    // Moving averages
    showMovingAverages.forEach((period, index) => {
      const maData = movingAverages.get(period);
      if (maData) {
        traces.push({
          x: data.map(d => d.timestamp),
          y: maData,
          type: 'scatter',
          mode: 'lines',
          name: `MA${period}`,
          line: {
            color: chartTheme.colors[index % chartTheme.colors.length],
            width: 1.5
          },
          xaxis: 'x',
          yaxis: 'y'
        });
      }
    });

    // Technical indicators
    indicators.forEach((indicator, index) => {
      if (indicator.type === 'overlay' && indicator.data.length === data.length) {
        traces.push({
          x: data.map(d => d.timestamp),
          y: indicator.data,
          type: 'scatter',
          mode: 'lines',
          name: indicator.name,
          line: {
            color: indicator.color || chartTheme.colors[(showMovingAverages.length + index) % chartTheme.colors.length],
            width: 1
          },
          xaxis: 'x',
          yaxis: 'y'
        });
      }
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
          opacity: volumeOpacity
        },
        xaxis: 'x',
        yaxis: 'y2'
      });
    }

    return traces;
  }, [data, showVolume, showMovingAverages, indicators, movingAverages, bullishColor, bearishColor, volumeOpacity, theme]);

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
        type: 'date',
        rangeslider: {
          visible: false
        },
        range: timeRange ? [timeRange[0].toISOString(), timeRange[1].toISOString()] : undefined
      },
      yaxis: {
        ...baseLayout.yaxis,
        title: 'Price',
        domain: showVolume ? [0.3, 1] : [0, 1]
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
      ] : undefined
    };
  }, [theme, title, subtitle, height, showLegend, showVolume, timeRange]);

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
      filename: `candlestick-chart-${Date.now()}`,
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

  // Handle range selection
  const handleRelayout = (event: any) => {
    if (onTimeRangeChange && event['xaxis.range']) {
      const [start, end] = event['xaxis.range'];
      onTimeRangeChange([new Date(start), new Date(end)]);
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
          onRelayout={handleRelayout}
          className="w-full"
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </Suspense>
    </div>
  );
};

export default CandlestickChart;