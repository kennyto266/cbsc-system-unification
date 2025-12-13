import React, { useMemo, Suspense, lazy } from 'react';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'));

// K线数据接口
interface CandlestickData {
  x: string[]; // 日期时间
  open: number[];
  high: number[];
  low: number[];
  close: number[];
  volume?: number[];
}

// 技术指标接口
interface TechnicalIndicator {
  name: string;
  data: number[];
  color?: string;
  type?: 'scatter' | 'line';
}

// Props接口
interface CandlestickChartProps {
  title?: string;
  subtitle?: string;
  data: CandlestickData;
  height?: number;
  className?: string;
  showVolume?: boolean;
  showMA?: boolean;
  technicalIndicators?: TechnicalIndicator[];
  theme?: 'light' | 'dark';
  onCandleClick?: (date: string, ohlc: { open: number; high: number; low: number; close: number }) => void;
  yAxisConfig?: {
    title?: string;
    range?: [number, number];
  };
  annotations?: Array<{
    x: string;
    y: number;
    text: string;
    arrowhead?: number;
  }>;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  title,
  subtitle,
  data,
  height = 600,
  className = '',
  showVolume = true,
  showMA = false,
  technicalIndicators = [],
  theme = 'light',
  onCandleClick,
  yAxisConfig,
  annotations = []
}) => {
  // 计算移动平均线
  const ma5 = useMemo(() => {
    const ma: number[] = [];
    for (let i = 0; i < data.close.length; i++) {
      if (i < 4) {
        ma.push(null);
      } else {
        const sum = data.close.slice(i - 4, i + 1).reduce((a, b) => a + b, 0);
        ma.push(sum / 5);
      }
    }
    return ma;
  }, [data.close]);

  const ma10 = useMemo(() => {
    const ma: number[] = [];
    for (let i = 0; i < data.close.length; i++) {
      if (i < 9) {
        ma.push(null);
      } else {
        const sum = data.close.slice(i - 9, i + 1).reduce((a, b) => a + b, 0);
        ma.push(sum / 10);
      }
    }
    return ma;
  }, [data.close]);

  // 构建图表数据
  const plotlyData = useMemo(() => {
    const traces: any[] = [];

    // K线图
    traces.push({
      type: 'candlestick',
      x: data.x,
      open: data.open,
      high: data.high,
      low: data.low,
      close: data.close,
      name: 'K线',
      increasing: {
        line: { color: '#10b981' },
        fillcolor: '#10b981'
      },
      decreasing: {
        line: { color: '#ef4444' },
        fillcolor: '#ef4444'
      },
      xaxis: 'x',
      yaxis: 'y'
    });

    // 移动平均线
    if (showMA) {
      traces.push({
        x: data.x,
        y: ma5,
        type: 'scatter',
        mode: 'lines',
        name: 'MA5',
        line: {
          color: '#f59e0b',
          width: 1
        },
        xaxis: 'x',
        yaxis: 'y'
      });

      traces.push({
        x: data.x,
        y: ma10,
        type: 'scatter',
        mode: 'lines',
        name: 'MA10',
        line: {
          color: '#8b5cf6',
          width: 1
        },
        xaxis: 'x',
        yaxis: 'y'
      });
    }

    // 技术指标
    technicalIndicators.forEach(indicator => {
      traces.push({
        x: data.x,
        y: indicator.data,
        type: indicator.type || 'scatter',
        mode: 'lines',
        name: indicator.name,
        line: {
          color: indicator.color || '#3b82f6',
          width: 1
        },
        xaxis: 'x',
        yaxis: 'y'
      });
    });

    // 成交量
    if (showVolume && data.volume) {
      const colors = data.close.map((close, i) => {
        if (i === 0) return '#94a3b8';
        return close >= data.close[i - 1] ? '#10b981' : '#ef4444';
      });

      traces.push({
        x: data.x,
        y: data.volume,
        type: 'bar',
        name: '成交量',
        marker: {
          color: colors,
          opacity: 0.5
        },
        xaxis: 'x',
        yaxis: 'y2'
      });
    }

    return traces;
  }, [data, showMA, showVolume, ma5, ma10, technicalIndicators]);

  // 图表布局配置
  const layout = useMemo(() => {
    const isDark = theme === 'dark';
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#f3f4f6';
    const bgColor = isDark ? '#1f2937' : '#ffffff';

    return {
      title: title ? {
        text: title,
        font: {
          color: textColor,
          size: 18
        }
      } : undefined,
      height,
      plot_bgcolor: bgColor,
      paper_bgcolor: bgColor,
      font: {
        color: textColor
      },
      showlegend: true,
      legend: {
        x: 0,
        y: 1,
        bgcolor: 'rgba(255,255,255,0)',
        bordercolor: 'rgba(255,255,255,0)',
        orientation: 'h'
      },
      xaxis: {
        type: 'category',
        rangeslider: {
          visible: false
        },
        gridcolor: gridColor,
        showgrid: false
      },
      yaxis: {
        title: yAxisConfig?.title || '价格',
        gridcolor: gridColor,
        showgrid: true,
        autorange: !yAxisConfig?.range,
        range: yAxisConfig?.range,
        domain: showVolume ? [0.3, 1] : [0, 1]
      },
      yaxis2: {
        title: '成交量',
        gridcolor: gridColor,
        showgrid: false,
        anchor: 'x',
        overlaying: 'y',
        side: 'right',
        domain: showVolume ? [0, 0.2] : [0, 0],
        visible: showVolume
      },
      annotations: annotations.map(ann => ({
        x: ann.x,
        y: ann.y,
        text: ann.text,
        showarrow: true,
        arrowhead: ann.arrowhead || 2,
        ax: 0,
        ay: -40
      })),
      margin: {
        l: 60,
        r: 60,
        t: 40,
        b: 40
      }
    };
  }, [theme, title, height, yAxisConfig, annotations, showVolume]);

  // 图表配置选项
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'pan2d',
      'select2d',
      'lasso2d',
      'autoScale2d',
      'toggleSpikelines',
      'hoverClosestCartesian',
      'hoverCompareCartesian'
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

  // 处理K线点击事件
  const handlePlotClick = (event: any) => {
    if (onCandleClick && event.points && event.points.length > 0) {
      const point = event.points[0];
      const index = point.pointIndex;
      if (index !== undefined) {
        const date = data.x[index];
        const ohlc = {
          open: data.open[index],
          high: data.high[index],
          low: data.low[index],
          close: data.close[index]
        };
        onCandleClick(date, ohlc);
      }
    }
  };

  return (
    <Suspense fallback={<div className="flex items-center justify-center h-96">加载图表中...</div>}>
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {subtitle}
          </p>
        )}
        <Plot
          data={plotlyData}
          layout={layout}
          config={config}
          onClick={handlePlotClick}
          className="w-full"
        />
      </div>
    </Suspense>
  );
};