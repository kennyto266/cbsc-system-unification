# Real-time Chart Components

這個目錄包含了用於實時金融圖表的組件和工具，專為CBSC量化交易系統設計。

## 組件列表

### 核心組件

1. **RealTimeChart.tsx** - 實時圖表基礎組件
   - 支持線形圖、柱狀圖、面積圖
   - 實時數據更新和動畫
   - 自動縮放和性能優化

2. **RealTimeCandlestick.tsx** - 實時K線圖組件
   - 使用 lightweight-charts 庫
   - 支持成交量顯示
   - 多時間週期切換

3. **RealTimeVolumeChart.tsx** - 實時成交量圖
   - 買賣量分離顯示
   - 累計成交量曲線
   - 平均成交量線

4. **RealTimeLineChart.tsx** - 實時線形圖
   - 多系列數據支持
   - 漸變填充效果
   - 平滑曲線選項

5. **StreamingDataProvider.tsx** - 流式數據提供者
   - 數據緩衝管理
   - 去重和壓縮
   - 訂閱管理

6. **ChartAnnotation.tsx** - 圖表標註組件
   - 緫條、矩形、橢圓標註
   - 文字和箭頭工具
   - 斐波那契回撤

7. **CrosshairTracker.tsx** - 十字線跟蹤
   - 數據提示框
   - X/Y軸標籤
   - 數據點吸附

### 數據提供者

1. **RealTimeChartProvider.tsx** - 實時圖表數據提供者
   - WebSocket數據管理
   - 圖表數據緩存
   - 訂閱/取消訂閱

2. **RealTimeDataProvider.tsx** - 實時數據提供者
   - 市場數據管理
   - 技術指標數據
   - 訂單簿和成交數據

3. **WebSocketProvider.tsx** - WebSocket連接提供者
   - 自動重連機制
   - 心跳檢測
   - 認證管理

## Hooks

### 實時圖表Hooks

1. **useRealTimeChart.ts** - 實時圖表Hook
   ```typescript
   const { data, subscribe, unsubscribe, getLatestPoint } = useRealTimeChart({
     symbol: 'HK.00700',
     timeframe: '1m',
     maxDataPoints: 1000
   })
   ```

2. **useWebSocketData.ts** - WebSocket數據Hook
   ```typescript
   const { subscribe, getLatestData, getConnectionStats } = useWebSocketData({
     channels: ['market.data', 'indicator.data']
   })
   ```

3. **useTechnicalIndicators.ts** - 技術指標Hook
   ```typescript
   const { indicators, calculateIndicator, getLatestValue } = useTechnicalIndicators({
     symbol: 'HK.00700',
     timeframe: '1m',
     indicators: ['RSI', 'MACD', 'BB']
   })
   ```

4. **useChartStreaming.ts** - 圖表流式更新Hook
   ```typescript
   const { start, stop, addData, getStats } = useChartStreaming({
     chart,
     updateInterval: 1000,
     enableAnimation: false
   })
   ```

## 工具類

### 實時圖表工具

1. **chartStreaming.ts** - 圖表流式管理
   - 數據緩衝和更新
   - 性能監控
   - 批處理優化

2. **dataBuffer.ts** - 數據緩衝區
   - 循環緩衝區實現
   - 數據壓縮
   - 持久化支持

3. **indicatorCalculator.ts** - 技術指標計算
   - 477個技術指標
   - 實時計算支持
   - 批量計算功能

4. **performanceOptimizer.ts** - 性能優化器
   - 幀率監控
   - 數據節流
   - 內存管理

## 使用示例

### 基本實時圖表

```typescript
import { RealTimeChart, RealTimeChartProvider } from './RealTime'

function App() {
  return (
    <RealTimeChartProvider>
      <RealTimeChart
        symbol="HK.00700"
        timeframe="1m"
        chartType="line"
        height={400}
        onDataUpdate={(data) => console.log('New data:', data)}
      />
    </RealTimeChartProvider>
  )
}
```

### K線圖與成交量

```typescript
import { RealTimeCandlestick, RealTimeVolumeChart } from './RealTime'

function ChartContainer() {
  return (
    <div>
      <RealTimeCandlestick
        symbol="HK.00700"
        timeframe="5m"
        height={300}
        showVolume={false}
      />
      <RealTimeVolumeChart
        symbol="HK.00700"
        timeframe="5m"
        height={100}
        showBuySell={true}
      />
    </div>
  )
}
```

### 技術指標圖表

```typescript
import { RealTimeLineChart, useTechnicalIndicators } from './RealTime'

function IndicatorChart() {
  const { indicators } = useTechnicalIndicators({
    symbol: 'HK.00700',
    timeframe: '1m',
    indicators: ['RSI', 'MACD']
  })

  return (
    <RealTimeLineChart
      symbol="HK.00700"
      timeframe="1m"
      series={[
        { key: 'close', label: 'Price' },
        { key: 'RSI', label: 'RSI', yAxisID: 'y1' }
      ]}
    />
  )
}
```

## 性能優化

### 數據點限制
- 最大顯示1000個數據點
- 自動清理舊數據
- 數據採樣和壓縮

### 更新頻率
- 默認16ms更新週期（60fps）
- 可配置的節流間隔
- 批量數據更新

### 內存管理
- 循環緩衝區
- 對象池復用
- 自動垃圾回收

## 配置選項

### 圖表配置

```typescript
interface ChartConfig {
  // 數據
  maxDataPoints: 1000
  updateInterval: 1000
  bufferSize: 1000

  // 渲染
  enableAnimation: false
  enableThrottling: true
  enableCompression: true

  // 交互
  showCrosshair: true
  showGrid: true
  showTooltip: true

  // 主題
  theme: 'light' | 'dark'
  colors: {
    primary: string
    secondary: string
    background: string
  }
}
```

### WebSocket配置

```typescript
interface WebSocketConfig {
  url: string
  autoConnect: true
  reconnectInterval: 3000
  maxReconnectAttempts: 5
  heartbeatInterval: 30000
  authenticationToken?: string
}
```

## 故障排除

### 常見問題

1. **圖表不更新**
   - 檢查WebSocket連接
   - 確認訂閱的頻道正確
   - 查看控制台錯誤信息

2. **性能問題**
   - 減少數據點數量
   - 禁用動畫效果
   - 使用數據壓縮

3. **內存泄漏**
   - 組件卸載時清理訂閱
   - 限制緩衝區大小
   - 使用自動清理功能

### 調試工具

開啟調試模式查看詳細信息：

```javascript
localStorage.setItem('debug', 'realtime-chart')
```

## 貢獻指南

1. 遵循現有的代碼風格
2. 添加必要的類型定義
3. 編寫單元測試
4. 更新文檔

## 許可證

MIT License