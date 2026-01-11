/**
 * CorrelationHeatmap Component
 * Heatmap showing strategy correlation matrix
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const CorrelationHeatmap: React.FC = () => {
  const correlationData = useAppSelector((state) => state.performanceAnalytics.correlations);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!correlationData) return [];

    return [
      {
        type: 'heatmap',
        z: correlationData.matrix,
        x: correlationData.strategies,
        y: correlationData.strategies,
        colorscale: [
          [0, '#10b981'],    // Green - low correlation
          [0.5, '#f59e0b'],  // Yellow - medium
          [1, '#ef4444'],    // Red - high correlation
        ],
        colorbar: {
          title: '相關性',
          titleside: 'right',
        },
        hovertemplate: '%{x} vs %{y}<br>相關性: %{z:.2f}<extra></extra>',
      },
    ];
  }, [correlationData]);

  const layout = {
    title: {
      text: '策略相關性矩陣',
      font: { size: 16, color: '#111827' },
    },
    xaxis: {
      side: 'bottom',
    },
    yaxis: {
      automargin: true,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 100, r: 30, t: 50, b: 80 },
    height: 400,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!correlationData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="correlation-heatmap-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default CorrelationHeatmap;
