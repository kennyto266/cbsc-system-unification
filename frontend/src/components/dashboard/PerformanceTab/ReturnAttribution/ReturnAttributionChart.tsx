/**
 * ReturnAttributionChart Component
 * Stacked bar chart showing economic indicator contributions to total return
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const ReturnAttributionChart: React.FC = () => {
  const attributionData = useAppSelector((state) => state.performanceAnalytics.returnAttribution);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!attributionData) return [];

    const indicators = attributionData.breakdown.map((d) => d.indicator);
    const contributions = attributionData.breakdown.map((d) => d.contribution);
    const colors = contributions.map((c) => (c >= 0 ? '#10b981' : '#ef4444'));

    return [
      {
        type: 'bar',
        x: indicators,
        y: contributions,
        marker: {
          color: colors,
        },
        text: contributions.map(
          (c) => `${c >= 0 ? '+' : ''}${c.toFixed(2)}%`
        ),
        textposition: 'outside',
        hoverinfo: 'x+y+text',
      },
    ];
  }, [attributionData]);

  const layout = {
    title: {
      text: '收益來源分解',
      font: { size: 16, color: '#111827' },
    },
    xaxis: {
      title: '經濟指標',
    },
    yaxis: {
      title: '貢獻 (%)',
      zeroline: true,
      gridcolor: '#e5e7eb',
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 60, r: 30, t: 50, b: 60 },
    height: 350,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!attributionData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="return-attribution-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default ReturnAttributionChart;
