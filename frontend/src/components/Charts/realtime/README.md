# 實時圖表組件 (Real-time Chart Components)

基於 Chart.js 4.4+ 和 react-chartjs-2 的高性能實時圖表組件庫，支持大量數據點的流暢渲染和WebSocket實時數據更新。

## 特性

- 🚀 **高性能渲染** - 支持1000+數據點流暢渲染
- 📡 **實時更新** - WebSocket數據連接，延遲 < 100ms
- 🎯 **數據優化** - LTTB抽樣算法，內存優化管理
- 🎨 **豐富類型** - 折線圖、柱狀圖、雷達圖、熱力圖
- 🔧 **高度可配置** - 支持主題、動畫、警報等自定義
- 📱 **響應式** - 自適應佈局，移動端支持

## 組件列表

### 1. RealTimeLineChart - 實時折線圖
用於顯示時間序列數據，如策略淨值曲線。

```tsx
<RealTimeLineChart
  websocketUrl="ws://localhost:3003"
  channel="strategy-netvalue"
  maxDataPoints={1000}
  showStats={true}
  showAlerts={true}
  alertThresholds={{
    upper: 1.5,
    lower: 0.5
  }}
  compareMode={true}
  enableCrosshair={true}
  enableZoom={true}
  onDataPointClick={(point) => console.log(point)}
/>
```

**主要配置：**
- `websocketUrl` - WebSocket服務器地址
- `channel` - 數據訂閱頻道
- `maxDataPoints` - 最大數據點數量
- `showStats` - 顯示統計信息
- `compareMode` - 啟用對比模式
- `enableZoom` - 啟用縮放功能

### 2. RealTimeBarChart - 實時柱狀圖
動態顯示分類數據，支持實時排序和動畫效果。

```tsx
<RealTimeBarChart
  websocketUrl="ws://localhost:3003"
  channel="strategy-returns"
  dynamicSorting={true}
  sortBy="value"
  sortOrder="desc"
  showChange={true}
  colorByValue={true}
  showTopN={10}
  onBarClick={(data, index) => console.log(data)}
/>
```

**主要配置：**
- `dynamicSorting` - 動態排序
- `sortBy` - 排序字段
- `colorByValue` - 根據值著色
- `showTopN` - 顯示前N項

### 3. RealTimeRadarChart - 實時雷達圖
多維度數據可視化，用於策略評分展示。

```tsx
<RealTimeRadarChart
  dimensions={[
    { key: 'sharpeRatio', label: '夏普比率', min: 0, max: 3 },
    { key: 'maxDrawdown', label: '最大回撤', min: 0, max: 50 },
    { key: 'winRate', label: '勝率', min: 0, max: 100 }
  ]}
  aggregationMethod="average"
  showAlerts={true}
  showPercentage={true}
  normalizeValues={true}
  onDimensionAlert={(dim, value) => console.log(dim, value)}
/>
```

**主要配置：**
- `dimensions` - 維度配置
- `aggregationMethod` - 數據聚合方法
- `normalizeValues` - 數值標準化
- `showPercentage` - 顯示百分比

### 4. RealTimeHeatmap - 實時熱力圖
相關性矩陣可視化，支持滾動更新。

```tsx
<RealTimeHeatmap
  xLabels={['策略A', '策略B', '策略C']}
  yLabels={['策略A', '策略B', '策略C']}
  colorScale={{
    min: '#3b82f6',
    mid: '#ffffff',
    max: '#ef4444'
  }}
  diverging={true}
  centerValue={0}
  showValues={true}
  onCellClick={(x, y, value) => console.log(x, y, value)}
/>
```

**主要配置：**
- `xLabels/yLabels` - 軸標籤
- `colorScale` - 顏色配置
- `diverging` - 發散顏色模式
- `showValues` - 顯示數值

### 5. RealTimeChartManager - 圖表管理器
統一管理多個實時圖表組件。

```tsx
<RealTimeChartManager
  charts={chartConfigs}
  layout="grid"
  theme="dark"
  onChartUpdate={(id, data) => console.log(id, data)}
/>
```

## 性能優化

### 1. 數據抽樣 (Decimation)
使用 LTTB (Largest Triangle Three Buckets) 算法減少渲染點數：
```tsx
enableDecimation={true}
decimationThreshold={500}
decimationAlgorithm="lttb"
```

### 2. 批量處理 (Batching)
批量處理數據更新以提高性能：
```tsx
enableDataBuffering={true}
bufferSize={100}
updateInterval={100}
```

### 3. 數據平滑 (Smoothing)
應用平滑算法減少噪點：
```tsx
smoothingEnabled={true}
smoothingWindow={5}
smoothingMethod="ema"
```

## 交互功能

### 1. 縮放和平移
```tsx
enableZoom={true}
enablePan={true}
zoomMode="x" // 'x', 'y', 'xy'
```

### 2. 數據點選擇
```tsx
onDataPointClick={(point, element) => {
  console.log('Clicked:', point)
}}
```

### 3. 警報系統
```tsx
showAlerts={true}
alertThresholds={{
  upper: 100,
  lower: 0
}}
onAlertTriggered={(type, value) => {
  alert(`${type} threshold: ${value}`)
}}
```

## 主題配置

### 1. 預定義主題
```tsx
theme="light" // 'light' | 'dark'
```

### 2. 自定義主題
```tsx
import { getTheme } from '../utils/chartThemes'

const customTheme = getTheme({
  backgroundColor: '#ffffff',
  textColor: '#333333',
  colors: ['#1e40af', '#dc2626', '#059669']
})
```

## 數據格式

### WebSocket數據格式
```typescript
interface RealTimeDataPoint {
  timestamp: number        // 時間戳
  value: number           // 主數值
  label?: string          // 標籤
  metadata?: {            // 元數據
    [key: string]: any
  }
}
```

### 雷達圖維度配置
```typescript
interface Dimension {
  key: string             // 數據鍵
  label: string           // 顯示標籤
  min?: number            // 最小值
  max?: number            // 最大值
  unit?: string           // 單位
}
```

## 最佳實踐

1. **數據量控制**
   - 使用 `maxDataPoints` 限制數據點數量
   - 啟用數據抽樣減少渲染壓力

2. **更新頻率**
   - 根據需求設置合適的 `updateInterval`
   - 使用批量處理減少更新次數

3. **內存管理**
   - 定期清理舊數據
   - 監控內存使用情況

4. **錯誤處理**
   - 監聽連接狀態
   - 提供重連機制
   - 顯示友好的錯誤信息

## 示例

查看完整示例：`/pages/demo/RealTimeChartsDemo.tsx`

## 依賴

```json
{
  "chart.js": "^4.5.1",
  "react-chartjs-2": "^5.3.1",
  "chartjs-plugin-zoom": "^2.2.0",
  "chartjs-plugin-annotation": "^3.1.0",
  "framer-motion": "^10.16.16",
  "lodash": "^4.17.21",
  "socket.io-client": "^4.7.4"
}
```

## 更新日誌

### v1.0.0 (2025-12-15)
- ✅ 實現四種實時圖表類型
- ✅ 支持WebSocket數據連接
- ✅ 性能優化和數據抽樣
- ✅ 警報系統和交互功能
- ✅ 響應式設計和主題支持