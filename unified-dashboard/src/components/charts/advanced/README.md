# 高級數據可視化組件

## 組件概述

本模塊包含專為量化交易Dashboard設計的高級數據可視化組件，提供專業級的圖表展示能力。

## 核心組件

### 1. 高級圖表組件
- **ScatterPlot** - 多維度散點圖，支持數據點聚类和回歸線
- **RadarChart** - 雷達圖，用於多指標對比分析
- **HeatmapChart** - 熱力圖，支持時間序列和矩陣數據
- **SankeyChart** - 桑基圖，展示數據流和關係
- **NetworkGraph** - 網絡關係圖，可視化複雜網絡結構
- **TreeMap** - 樹狀圖，層次化數據展示

### 2. 金融圖表組件
- **CandlestickChart** - K線圖，支持OHLC數據
- **VolumeChart** - 成交量圖，支持條形圖和山形圖
- **OrderBookChart** - 訂單簿圖，實時盤口數據
- **MarketDepthChart** - 市場深度圖，買賣盤可視化

### 3. 儀表板組件
- **PerformanceGauge** - 性能儀表盤，動態指標展示
- **TrendChart** - 趨勢圖，支持多時間週期
- **MetricCard** - 指標卡片，關鍵數據展示
- **StatusIndicator** - 狀態指示器，實時狀態監控

### 4. 共享組件
- **ChartContainer** - 統一的圖表容器
- **ChartLegend** - 可定制圖例組件
- **ChartTooltip** - 智能提示框
- **ChartControls** - 圖表控制面板

## 特性

### 🎯 核心特性
- 支持實時數據更新（WebSocket）
- 高性能渲染（1000+數據點）
- 響應式設計，自適應不同屏幕
- 深色/淺色主題支持
- 多語言支持

### ⚡ 性能優化
- 虛擬化渲染大數據集
- 數據採樣和聚合
- Canvas加速渲染
- 組件級緩存

### 🎨 交互功能
- 縮放和平移
- 十字線追蹤
- 數據點標注
- 圖表導出（PNG/SVG/PDF）
- 全屏模式

## 使用示例

```typescript
import { ScatterPlot, CandlestickChart, PerformanceGauge } from '@/components/charts'

// 散點圖
<ScatterPlot
  data={scatterData}
  config={{
    width: 800,
    height: 400,
    theme: 'dark',
    showRegression: true
  }}
  onPointClick={(point) => console.log(point)}
/>

// K線圖
<CandlestickChart
  data={ohlcData}
  volumeData={volumeData}
  technicalIndicators={['MA', 'MACD', 'RSI']}
  timeRange={{ start: '2024-01-01', end: '2024-12-31' }}
/>

// 性能儀表
<PerformanceGauge
  value={75.5}
  max={100}
  thresholds={[{ value: 50, color: '#ff4d4f' }]}
  label="策略收益率"
  unit="%"
/>
```

## 技術棧

- **React 18** - 組件框架
- **TypeScript** - 類型安全
- **Chart.js** - 基礎圖表庫
- **Plotly.js** - 高級可視化
- **Recharts** - React圖表庫
- **D3.js** - 數據驅動可視化
- **Canvas API** - 高性能渲染

## 數據格式

### 時間序列數據
```typescript
interface TimeSeriesData {
  timestamp: Date | number
  value: number
  volume?: number
  metadata?: Record<string, any>
}
```

### OHLC數據
```typescript
interface OHLCData {
  timestamp: Date | number
  open: number
  high: number
  low: number
  close: number
  volume: number
}
```

## 自定義主題

```typescript
const customTheme = {
  colors: {
    primary: ['#1890ff', '#2fc25b', '#facc14'],
    background: '#141414',
    grid: 'rgba(255,255,255,0.1)'
  },
  typography: {
    fontFamily: 'Inter, sans-serif'
  }
}
```

## 開發指南

1. 組件應保持純函數特性
2. 使用TypeScript定義清晰類型
3. 實現shouldComponentUpdate優化
4. 添加單元測試覆蓋
5. 遵循可訪問性標準

## 測試

```bash
# 運行測試
npm run test:charts

# 生成覆蓋率報告
npm run test:charts:coverage
```

## 文檔

- [組件API文檔](./api)
- [示例集合](./examples)
- [最佳實踐](./best-practices)
- [性能指南](./performance)