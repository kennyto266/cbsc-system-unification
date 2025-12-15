import React, { useMemo } from 'react';
import lazy, { Suspense } from 'react';

// Dynamically import Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'), { ssr: false });

// 3D数据点接口
interface DataPoint3D {
  x: number;
  y: number;
  z: number;
  value?: number;
  label?: string;
  color?: string;
}

// 数据系列接口
interface DataSeries3D {
  name: string;
  data: DataPoint3D[];
  type?: 'scatter3d' | 'surface' | 'mesh3d' | 'heatmap3d';
  colorscale?: string;
  showscale?: boolean;
  opacity?: number;
}

// Props接口
interface ThreeDChartProps {
  title?: string;
  subtitle?: string;
  series: DataSeries3D[];
  height?: number;
  className?: string;
  theme?: 'light' | 'dark';
  showColorbar?: boolean;
  camera?: {
    eye: { x: number; y: number; z: number };
    center: { x: number; y: number; z: number };
  };
  axisLabels?: {
    x: string;
    y: string;
    z: string;
  };
  onPointClick?: (seriesIndex: number, pointIndex: number, point: DataPoint3D) => void;
}

export const ThreeDChart: React.FC<ThreeDChartProps> = ({
  title,
  subtitle,
  series,
  height = 600,
  className = '',
  theme = 'light',
  showColorbar = true,
  camera = {
    eye: { x: 1.5, y: 1.5, z: 1.5 },
    center: { x: 0, y: 0, z: 0 }
  },
  axisLabels = {
    x: 'X轴',
    y: 'Y轴',
    z: 'Z轴'
  },
  onPointClick
}) => {
  // 构建Plotly数据
  const plotlyData = useMemo(() => {
    const traces: any[] = [];

    series.forEach((s, seriesIndex) => {
      const { name, data, type = 'scatter3d', colorscale, showscale = true, opacity = 0.8 } = s;

      if (type === 'scatter3d') {
        // 3D散点图
        traces.push({
          type: 'scatter3d',
          mode: 'markers',
          name: name,
          x: data.map(d => d.x),
          y: data.map(d => d.y),
          z: data.map(d => d.z),
          text: data.map(d => d.label || `(${d.x}, ${d.y}, ${d.z})`),
          marker: {
            size: data.map(d => d.value || 8),
            color: data.map(d => d.color || d.value || d.z),
            colorscale: colorscale || 'Viridis',
            showscale: showscale && seriesIndex === 0,
            colorbar: showColorbar && seriesIndex === 0 ? {
              title: '值',
              titleside: 'right',
              tickmode: 'linear',
              tick0: 0,
              dtick: 0.2
            } : undefined,
            opacity,
            line: {
              color: 'rgba(255, 255, 255, 0.14)',
              width: 0.5
            }
          },
          hovertemplate: '<b>%{text}</b><br>' +
                        'X: %{x}<br>' +
                        'Y: %{y}<br>' +
                        'Z: %{z}<br>' +
                        (data[0]?.value !== undefined ? '值: %{marker.color}<extra></extra>' : '<extra></extra>')
        });
      } else if (type === 'surface') {
        // 3D曲面图
        // 需要将数据转换为网格格式
        const uniqueX = Array.from(new Set(data.map(d => d.x))).sort((a, b) => a - b);
        const uniqueY = Array.from(new Set(data.map(d => d.y))).sort((a, b) => a - b);

        const zGrid: number[][] = [];
        for (let i = 0; i < uniqueY.length; i++) {
          zGrid[i] = [];
          for (let j = 0; j < uniqueX.length; j++) {
            const point = data.find(d => d.x === uniqueX[j] && d.y === uniqueY[i]);
            zGrid[i][j] = point ? point.z : 0;
          }
        }

        traces.push({
          type: 'surface',
          name: name,
          x: uniqueX,
          y: uniqueY,
          z: zGrid,
          colorscale: colorscale || 'Viridis',
          showscale: showscale && seriesIndex === 0,
          colorbar: showColorbar && seriesIndex === 0 ? {
            title: 'Z值',
            titleside: 'right'
          } : undefined,
          opacity,
          hovertemplate: '<b>曲面</b><br>' +
                        'X: %{x}<br>' +
                        'Y: %{y}<br>' +
                        'Z: %{z}<extra></extra>'
        });
      } else if (type === 'mesh3d') {
        // 3D网格图
        traces.push({
          type: 'mesh3d',
          name: name,
          x: data.map(d => d.x),
          y: data.map(d => d.y),
          z: data.map(d => d.z),
          color: data.map(d => d.color || d.value || d.z),
          colorscale: colorscale || 'Viridis',
          showscale: showscale && seriesIndex === 0,
          colorbar: showColorbar && seriesIndex === 0 ? {
            title: '值',
            titleside: 'right'
          } : undefined,
          opacity,
          hovertemplate: '<b>网格</b><br>' +
                        'X: %{x}<br>' +
                        'Y: %{y}<br>' +
                        'Z: %{z}<br>' +
                        '值: %{color}<extra></extra>'
        });
      } else if (type === 'heatmap3d') {
        // 3D热力图
        const uniqueX = Array.from(new Set(data.map(d => d.x))).sort((a, b) => a - b);
        const uniqueY = Array.from(new Set(data.map(d => d.y))).sort((a, b) => a - b);

        const zGrid: number[][] = [];
        for (let i = 0; i < uniqueY.length; i++) {
          zGrid[i] = [];
          for (let j = 0; j < uniqueX.length; j++) {
            const point = data.find(d => d.x === uniqueX[j] && d.y === uniqueY[i]);
            zGrid[i][j] = point ? point.value || point.z : 0;
          }
        }

        traces.push({
          type: 'surface',
          name: name,
          x: uniqueX,
          y: uniqueY,
          z: zGrid,
          colorscale: colorscale || 'Jet',
          showscale: showscale && seriesIndex === 0,
          colorbar: showColorbar && seriesIndex === 0 ? {
            title: '强度',
            titleside: 'right'
          } : undefined,
          opacity: 0.9,
          hovertemplate: '<b>热力图</b><br>' +
                        'X: %{x}<br>' +
                        'Y: %{y}<br>' +
                        '强度: %{z}<extra></extra>'
        });
      }
    });

    return traces;
  }, [series, showColorbar]);

  // 图表布局
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
      scene: {
        xaxis: {
          title: axisLabels.x,
          gridcolor: gridColor,
          showbackground: true,
          backgroundcolor: isDark ? '#111827' : '#f9fafb',
          color: textColor,
          zerolinecolor: gridColor
        },
        yaxis: {
          title: axisLabels.y,
          gridcolor: gridColor,
          showbackground: true,
          backgroundcolor: isDark ? '#111827' : '#f9fafb',
          color: textColor,
          zerolinecolor: gridColor
        },
        zaxis: {
          title: axisLabels.z,
          gridcolor: gridColor,
          showbackground: true,
          backgroundcolor: isDark ? '#111827' : '#f9fafb',
          color: textColor,
          zerolinecolor: gridColor
        },
        camera: camera,
        aspectmode: 'cube'
      },
      margin: {
        l: 0,
        r: 0,
        t: 40,
        b: 40
      }
    };
  }, [theme, title, height, axisLabels, camera]);

  // 配置选项
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'select2d',
      'lasso2d',
      'resetScale2d',
      'toggleSpikelines',
      'hoverClosestCartesian',
      'hoverCompareCartesian'
    ],
    toImageButtonOptions: {
      format: 'png',
      filename: `3d-chart-${Date.now()}`,
      height: height,
      width: 1200,
      scale: 2
    },
    responsive: true
  }), [height]);

  // 处理点击事件
  const handlePlotClick = (event: any) => {
    if (onPointClick && event.points && event.points.length > 0) {
      const point = event.points[0];
      const seriesIndex = point.curveNumber;
      const pointIndex = point.pointIndex;

      if (seriesIndex !== undefined && pointIndex !== undefined) {
        const dataPoint = series[seriesIndex].data[pointIndex];
        onPointClick(seriesIndex, pointIndex, dataPoint);
      }
    }
  };

  return (
    <Suspense fallback={<div>Loading...</div>}>
  return (
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
  );
    </Suspense>
  );
};