/**
 * RiskRadarChart Component
 * Radar chart showing 5-dimension risk exposure
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const RiskRadarChart: React.FC = () => {
  const riskData = useAppSelector((state) => state.performanceAnalytics.riskExposure);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!riskData) return [];

    const dimensions = [
      '系統性風險',
      '利率風險',
      '流動性風險',
      '經濟增長風險',
      '匯率風險',
    ];

    const values = [
      riskData.systematic,
      riskData.interestRate,
      riskData.liquidity,
      riskData.economicGrowth,
      riskData.fx,
    ];

    return [
      {
        type: 'scatterpolar',
        r: values,
        theta: dimensions,
        fill: 'toself',
        name: '風險暴露',
        marker: {
          color: 'rgb(59, 130, 246)',
        },
        line: {
          color: 'rgb(59, 130, 246)',
        },
      },
    ];
  }, [riskData]);

  const layout = {
    title: {
      text: '風險歸因分析',
      font: { size: 16, color: '#111827' },
    },
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 1],
        tickmode: 'linear',
        tick0: 0,
        dtick: 0.2,
      },
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 60, r: 60, t: 50, b: 60 },
    height: 400,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!riskData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="risk-radar-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default RiskRadarChart;
