/**
 * Equity Curve Chart Component
 * Displays strategy vs Buy&Hold performance comparison
 */

import React, { useMemo, lazy, Suspense } from 'react';
import { Card, Spin, Alert } from 'antd';
import type { StrategyResult } from '../../types/market-optimization';
import './EquityCurveChart.css';

// Lazy load Plotly to avoid SSR issues
const Plot = lazy(() => import('react-plotly.js'), { ssr: false });

interface EquityCurveChartProps {
  strategy: StrategyResult | null;
}

const EquityCurveChart: React.FC<EquityCurveChartProps> = ({ strategy }) => {
  if (!strategy) {
    return (
      <Card className="equity-curve-chart" bordered={false}>
        <div className="equity-curve-empty">
          請選擇一個策略查看 Equity Curve
        </div>
      </Card>
    );
  }

  const { symbol, params, equity_curve, bnh_equity_curve } = strategy;

  // Validate data
  if (!equity_curve || equity_curve.length === 0) {
    return (
      <Card className="equity-curve-chart" bordered={false}>
        <Alert
          message="該策略沒有 Equity Curve 數據"
          type="warning"
          showIcon
        />
      </Card>
    );
  }

  // Generate date labels (approximate trading days)
  const dates = useMemo(() => {
    const startDate = new Date(2020, 0, 1); // 2020-01-01
    const dateList: string[] = [];
    const totalDays = equity_curve.length;

    for (let i = 0; i < totalDays; i++) {
      // Approximate: 252 trading days per year
      const tradingDaysPerYear = 252;
      const daysToAdd = Math.floor((i / totalDays) * 5 * 365);
      const date = new Date(startDate);
      date.setDate(date.getDate() + daysToAdd);
      dateList.push(date.toISOString().split('T')[0]);
    }

    return dateList;
  }, [equity_curve.length]);

  // Chart data
  const chartData = [
    {
      x: dates,
      y: equity_curve,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: '策略',
      line: { color: '#1890ff', width: 2 }
    },
    {
      x: dates,
      y: bnh_equity_curve || equity_curve,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: 'Buy & Hold',
      line: { color: '#8c8c8c', width: 2, dash: 'dash' }
    }
  ];

  // Chart layout
  const layout = {
    title: `${symbol} - MA(${params.short_period}/${params.long_period})`,
    xaxis: {
      title: '日期',
      autorange: true as const
    },
    yaxis: {
      title: '投資價值 ($)',
      autorange: true as const
    },
    hovermode: 'x unified' as const,
    legend: {
      x: 0,
      y: 1.1,
      orientation: 'h' as const,
      xanchor: 'left' as const
    },
    autosize: true as const,
    margin: { l: 60, r: 30, t: 60, b: 60 }
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  return (
    <Card className="equity-curve-chart" bordered={false}>
      <Suspense fallback={<Spin size="large" />}>
        <Plot
          data={chartData}
          layout={layout}
          config={config}
          className="equity-curve-plot"
          useResizeHandler={true}
        />
      </Suspense>
    </Card>
  );
};

export default EquityCurveChart;
