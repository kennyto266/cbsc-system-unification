# Chart.js 圖表組件庫

## 概述

這是一個基於 Chart.js 4.x 和 React-Chartjs-2 構建的專業級金融圖表組件庫，專為 CBSC 量化交易策略管理系統設計。

## 特性

- 🎯 **多種圖表類型**: 線圖、柱狀圖、餅圖、散點圖、K線圖等
- 📊 **實時數據更新**: 支持 WebSocket 實時數據推送
- 🎨 **高度可定制**: 主題、顏色、動畫、交互效果
- 📱 **響應式設計**: 完美適配桌面、平板和手機端
- 💾 **導出功能**: 支持 PNG、JPG、SVG 等格式導出
- ⚡ **性能優化**: 大數據集渲染優化
- 🌐 **國際化支持**: 支持中文、英文等多語言
- ♿ **無障礙支持**: WCAG 2.1 AA 級別兼容

## 安裝依賴

```bash
npm install chart.js react-chartjs-2
```

## 組件列表

### 1. StrategyPerformanceChart
策略性能走勢圖 - 顯示多個策略的歷史表現對比

```tsx
import { StrategyPerformanceChart } from '@/components/Charts'

<StrategyPerformanceChart
  strategies={strategies}
  timeRange="1M"
  onTimeRangeChange={(range) => console.log(range)}
/>
```

**Props:**
- `strategies`: `Strategy[]` - 策略數據數組
- `timeRange`: `'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'` - 時間範圍
- `onTimeRangeChange`: `(range: string) => void` - 時間範圍變更回調

### 2. AssetAllocationChart
資產配置餅圖 - 顯示投資組合資產分配

```tsx
import { AssetAllocationChart } from '@/components/Charts'

<AssetAllocationChart
  strategies={strategies}
  totalValue={100000}
  showDetails={true}
/>
```

**Props:**
- `strategies`: `Strategy[]` - 策略數據數組
- `totalValue`: `number` - 投資組合總價值
- `showDetails`: `boolean` - 是否顯示詳情面板

### 3. StrategyComparisonChart
策略對比柱狀圖 - 多維度策略性能對比

```tsx
import { StrategyComparisonChart } from '@/components/Charts'

<StrategyComparisonChart
  strategies={strategies}
  metric="totalReturn"
  onMetricChange={(metric) => console.log(metric)}
  sortBy="value"
  showTopN={10}
/>
```

**Props:**
- `strategies`: `Strategy[]` - 策略數據數組
- `metric`: `'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'` - 對比指標
- `onMetricChange`: `(metric: string) => void` - 指標變更回調
- `sortBy`: `'name' | 'value'` - 排序方式
- `showTopN`: `number` - 顯示前N個策略

### 4. RiskReturnScatterChart
風險收益散點圖 - 風險 vs 收益可視化分析

```tsx
import { RiskReturnScatterChart } from '@/components/Charts'

<RiskReturnScatterChart
  strategies={strategies}
  showQuadrants={true}
  showEfficientFrontier={true}
  filterType="all"
  onFilterChange={(type) => console.log(type)}
/>
```

**Props:**
- `strategies`: `Strategy[]` - 策略數據數組
- `showQuadrants`: `boolean` - 是否顯示四象限
- `showEfficientFrontier`: `boolean` - 是否顯示有效前沿
- `filterType`: `StrategyType | 'all'` - 策略類型過濾
- `onFilterChange`: `(type: string) => void` - 過濾變更回調

### 5. RealTimePriceChart
實時價格K線圖 - 實時價格數據展示

```tsx
import { RealTimePriceChart } from '@/components/Charts'

<RealTimePriceChart
  strategy={strategy}
  symbol="BTC/USDT"
  timeFrame="1h"
  showVolume={true}
  showIndicators={true}
  autoUpdate={true}
/>
```

**Props:**
- `strategy`: `Strategy` - 策略對象
- `symbol`: `string` - 交易對符號
- `timeFrame`: `'1m' | '5m' | '15m' | '1h' | '4h' | '1d'` - 時間框架
- `showVolume`: `boolean` - 是否顯示成交量
- `showIndicators`: `boolean` - 是否顯示技術指標
- `autoUpdate`: `boolean` - 是否自動更新

## 工具函數

### ChartUtils

```tsx
import ChartUtils from '@/utils/chartUtils'

// 格式化數字
ChartUtils.formatNumber(1234.567) // "1,234.57"

// 格式化百分比
ChartUtils.formatPercentage(0.1234) // "12.34%"

// 格式化貨幣
ChartUtils.formatCurrency(1234.56) // "$1,234.56"

// 生成顏色數組
const colors = ChartUtils.generateColors(5) // ["#3B82F6", "#10B981", ...]

// 導出圖表
await ChartUtils.exportChart(canvas, 'my-chart', {
  format: 'png',
  quality: 0.9
})
```

## 主題配置

```tsx
import { defaultChartTheme, chartUtils } from '@/components/Charts'

// 自定義主題
const customTheme = chartUtils.applyTheme({
  primaryColor: '#FF6B6B',
  backgroundColor: '#F8F9FA',
  gridColor: 'rgba(0, 0, 0, 0.1)',
  textColor: '#495057'
})
```

## 響應式配置

```tsx
import { responsiveChartConfig } from '@/components/Charts'

// 創建響應式配置
const config = ChartUtils.createResponsiveConfig(
  baseConfig,
  'mobile' | 'tablet' | 'desktop'
)
```

## 技術指標

組件支持多種技術指標：

- **SMA (簡單移動平均線)**
- **EMA (指數移動平均線)**
- **RSI (相對強弱指標)**
- **MACD (移動平均收斂發散指標)**
- **布林帶 (Bollinger Bands)**

## 性能優化

### 大數據集處理

```tsx
// 使用數據採樣
const sampledData = data.filter((_, index) => index % sampleRate === 0)

// 啟用渲染優化
const options = {
  animation: false, // 禁用動畫
  elements: {
    point: {
      radius: 0 // 隱藏數據點
    }
  }
}
```

### 內存管理

```tsx
// 清理定時器
useEffect(() => {
  const interval = setInterval(updateData, 1000)
  return () => clearInterval(interval)
}, [])

// 使用 useMemo 優化計算
const chartData = useMemo(() => processChartData(rawData), [rawData])
```

## 類型定義

```tsx
interface Strategy {
  id: string
  name: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  description?: string
  parameters: Record<string, any>
  performance: {
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
  }
  createdAt: string
  updatedAt: string
}

enum StrategyType {
  SENTIMENT = 'sentiment',
  TECHNICAL = 'technical',
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  ARBITRAGE = 'arbitrage'
}

enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}
```

## 範例代碼

完整的使用範例請參考：

- `DashboardPage.tsx` - 主儀表板頁面
- `ChartsShowcasePage.tsx` - 圖表展示頁面
- `ChartTestComponent.tsx` - 測試組件

## 故障排除

### 常見問題

1. **圖表不顯示**
   - 檢查 Chart.js 是否正確註冊
   - 確認容器元素有固定高度
   - 驗證數據格式是否正確

2. **性能問題**
   - 減少數據點數量
   - 禁用不必要的動畫
   - 使用數據採樣

3. **響應式問題**
   - 確保容器元素有響應式樣式
   - 檢查 `maintainAspectRatio` 設置
   - 使用 `responsive: true`

### 調試技巧

```tsx
// 啟用 Chart.js 調試模式
Chart.defaults.debug = true

// 監聽圖表事件
const options = {
  onHover: (event, activeElements) => {
    console.log('Hover:', activeElements)
  },
  onClick: (event, activeElements) => {
    console.log('Click:', activeElements)
  }
}
```

## 更新日誌

### v1.0.0 (2024-12-10)
- ✅ 初始版本發布
- ✅ 5個核心圖表組件
- ✅ Chart.js 4.x 集成
- ✅ TypeScript 支持
- ✅ 響應式設計
- ✅ 導出功能
- ✅ 實時數據支持

## 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 創建 Pull Request

## 許可證

MIT License

## 聯繫方式

如有問題或建議，請聯繫開發團隊。