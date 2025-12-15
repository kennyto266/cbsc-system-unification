# 实时数据可视化系统

## 概述

本系统为 CBSC 量化交易平台提供了完整的实时数据可视化解决方案，包括 Chart.js 和 Plotly.js 的高级图表组件，支持实时数据更新和丰富的交互功能。

## 功能特性

### 1. Chart.js 图表组件
- **LineChart**: 时间序列折线图，支持多数据集、双Y轴、时间轴
- **BarChart**: 柱状图，支持水平/垂直、堆叠、分组显示
- **PieChart**: 饼图，支持中心文本、百分比显示、自定义配色

### 2. Plotly.js 高级图表
- **CandlestickChart**: 专业K线图，支持成交量、移动平均线、技术指标
- **RealTimeChart**: 实时流图，支持多数据流、多Y轴、暂停/恢复
- **ThreeDChart**: 3D可视化，支持散点图、曲面图、网格图

### 3. 核心功能
- **WebSocket 实时连接**: 自动重连、心跳检测、错误处理
- **数据缓冲管理**: 滑动窗口、数据降采样、性能优化
- **图表交互**: 缩放、平移、数据点点击、十字准线
- **导出功能**: PNG、SVG、CSV、JSON 格式导出
- **主题支持**: 亮色/暗色主题自动切换
- **响应式设计**: 自适应不同屏幕尺寸

## 组件结构

```
frontend/src/components/charts/
├── common/                    # 通用组件
│   ├── BaseChart.tsx         # 基础图表组件
│   ├── ChartContainer.tsx    # 图表容器
│   └── ChartToolbar.tsx      # 图表工具栏
├── chartjs/                   # Chart.js 组件
│   ├── LineChart.tsx         # 折线图
│   ├── BarChart.tsx          # 柱状图
│   └── PieChart.tsx          # 饼图
├── plotly/                    # Plotly.js 组件
│   ├── CandlestickChart.tsx  # K线图
│   ├── RealTimeChart.tsx     # 实时流图
│   └── ThreeDChart.tsx       # 3D图表
├── hooks/                     # 自定义 Hooks
│   ├── useRealTimeChart.ts   # 实时图表Hook
│   └── useChartExport.ts     # 图表导出Hook
└── RealTimeDashboard.tsx     # 完整仪表板示例
```

## 使用示例

### 基础折线图
```tsx
import { LineChart } from '../components/charts';

const data = [{
  label: '策略收益',
  data: [
    { x: new Date(), y: 100 },
    { x: new Date(Date.now() + 3600000), y: 105 }
  ],
  borderColor: '#3b82f6',
  fill: true
}];

<LineChart
  title="策略收益曲线"
  data={data}
  height={400}
  timeAxis={true}
  onDataPointClick={(index, point) => console.log(point)}
/>
```

### K线图
```tsx
import { CandlestickChart } from '../components/charts';

const candleData = {
  x: ['2025-01-01', '2025-01-02'],
  open: [100, 102],
  high: [105, 108],
  low: [98, 100],
  close: [102, 105],
  volume: [1000000, 1200000]
};

<CandlestickChart
  title="价格走势"
  data={candleData}
  showVolume={true}
  showMA={true}
  onCandleClick={(date, ohlc) => console.log(date, ohlc)}
/>
```

### 实时图表
```tsx
import { RealTimeChart } from '../components/charts';

const streams = [
  { id: 'strategy1', name: '策略1', color: '#3b82f6' },
  { id: 'strategy2', name: '策略2', color: '#10b981' }
];

<RealTimeChart
  title="实时监控"
  streams={streams}
  wsUrl="ws://localhost:3003"
  maxDataPoints={100}
/>
```

## 配置选项

### WebSocket 配置
```typescript
{
  url: 'ws://localhost:3003',        // WebSocket地址
  channel: 'chart-data',            // 订阅频道
  maxDataPoints: 100,              // 最大数据点数
  updateInterval: 1000,            // 更新间隔(ms)
  autoReconnect: true,             // 自动重连
  reconnectDelay: 3000             // 重连延迟(ms)
}
```

### 主题配置
系统自动检测并应用系统主题：
- `light`: 亮色主题，白色背景
- `dark`: 暗色主题，深色背景

## 性能优化

1. **懒加载**: Plotly组件使用React.lazy动态加载
2. **数据缓冲**: 限制最大数据点数量，避免内存泄漏
3. **批量更新**: 批量处理数据更新，减少重渲染
4. **虚拟化**: 大数据集时自动启用数据降采样

## 依赖项

```json
{
  "chart.js": "^4.4.0",
  "react-chartjs-2": "^5.2.0",
  "plotly.js": "^2.26.0",
  "react-plotly.js": "^2.6.0",
  "socket.io-client": "^4.7.4",
  "html2canvas": "^1.4.1",
  "date-fns": "^3.0.6"
}
```

## 注意事项

1. **SSR支持**: Plotly组件使用动态导入避免SSR问题
2. **浏览器兼容**: 需要现代浏览器支持ES6+
3. **WebSocket**: 确保服务器支持WebSocket连接
4. **性能建议**: 大量数据时建议使用数据降采样

## 开发指南

1. 添加新图表类型时，继承BaseChart或ChartContainer
2. 实现实时更新时使用useRealTimeChart Hook
3. 需要导出功能时使用useChartExport Hook
4. 保持组件API一致性，便于维护和使用