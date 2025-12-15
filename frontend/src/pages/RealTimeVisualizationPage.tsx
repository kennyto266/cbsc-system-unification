import React from 'react';
import { RealTimeDashboard } from '../components/charts';

/**
 * 实时数据可视化页面
 *
 * 此页面展示了完整的实时数据可视化功能，包括：
 * - Chart.js 图表组件（折线图、柱状图、饼图）
 * - Plotly.js 高级图表（K线图、3D图表、实时流图）
 * - WebSocket 实时数据更新
 * - 图表交互功能（缩放、平移、导出）
 */
const RealTimeVisualizationPage: React.FC = () => {
  return (
    <div className="min-h-screen">
      <RealTimeDashboard />
    </div>
  );
};

export default RealTimeVisualizationPage;