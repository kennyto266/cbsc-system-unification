# Chart.js 圖表組件文檔

## 概述

這個文件夾包含了基於 Chart.js 4.x 開發的策略管理圖表組件，為 CBSC 量化交易系統提供數據可視化功能。

## 組件列表

### 1. SharpeRatioChart

- **功能**: 顯示策略 Sharpe 比率排名的條形圖
- **用途**: 評估策略的風險調整後收益表現
- **特性**:
  - 按 Sharpe 比率降序排列
  - 顏色編碼表示績效等級
  - 支持點擊交互
  - 顯示 Top 10 策略

### 2. MaxDrawdownChart

- **功能**: 展示策略最大回撤趨勢的折線圖
- **用途**: 監控策略風險狀況
- **特性**:
  - 多策略對比顯示
  - 時間範圍選擇 (7天/30天/90天/180天)
  - 漸變填充效果
  - 實時數據更新

### 3. StrategyRadarChart

- **功能**: 多維度策略性能對比的雷達圖
- **用途**: 全面評估策略綜合表現
- **特性**:
  - 六個維度指標對比
  - 交互式策略選擇
  - 綜合評分排名
  - 自動數據歸一化

### 4. ChartsDashboard

- **功能**: 整合所有圖表的主儀表板組件
- **用途**: 提供完整的圖表展示和控制功能
- **特性**:
  - 網格/堆疊佈局切換
  - 實時更新控制
  - 圖表顯示/隱藏
  - 響應式設計

### 5. ChartManager

- **功能**: 圖表實例管理和生命週期控制
- **用途**: 統一管理所有圖表實例
- **特性**:
  - 實時數據更新
  - 性能監控
  - 自動銷毀清理
  - 響應式調整

## 使用方法

### 基本用法

```tsx
import React from 'react'
import { ChartsDashboard } from '../components/Charts'
import { Strategy } from '../types'

const MyComponent: React.FC<{ strategies: Strategy[] }> = ({ strategies }) => {
  return (
    <ChartsDashboard
      strategies={strategies}
      height={400}
      showControls={true}
      defaultLayout="grid"
    />
  )
}
```

### 單獨使用圖表

```tsx
import React from 'react'
import { SharpeRatioChart, MaxDrawdownChart, StrategyRadarChart } from '../components/Charts'

const MyCharts: React.FC<{ strategies: Strategy[] }> = ({ strategies }) => {
  return (
    <div>
      {/* Sharpe 比率圖 */}
      <SharpeRatioChart
        strategies={strategies}
        height={300}
        onBarClick={(strategy) => console.log('Selected:', strategy)}
      />

      {/* 最大回撤圖 */}
      <MaxDrawdownChart
        strategies={strategies}
        height={350}
        timeRange="30d"
        onStrategyClick={(strategy) => console.log('Selected:', strategy)}
      />

      {/* 雷達圖 */}
      <StrategyRadarChart
        strategies={strategies}
        height={400}
        maxStrategies={4}
        onStrategySelect={(strategy) => console.log('Selected:', strategy)}
      />
    </div>
  )
}
```

### 使用 Chart Manager

```tsx
import React from 'react'
import { ChartManagerProvider, useChartManager } from '../components/Charts'

const App: React.FC = () => {
  return (
    <ChartManagerProvider>
      <MyComponent />
    </ChartManagerProvider>
  )
}

const MyComponent: React.FC = () => {
  const { enableRealTimeUpdates, resizeCharts } = useChartManager()

  React.useEffect(() => {
    // 啟用實時更新
    enableRealTimeUpdates(true)

    // 監聽窗口大小變化
    window.addEventListener('resize', resizeCharts)
    return () => window.removeEventListener('resize', resizeCharts)
  }, [enableRealTimeUpdates, resizeCharts])

  // ... 其他代碼
}
```

## 數據格式

### Strategy 數據結構

```typescript
interface Strategy {
  id: string
  name: string
  type: string
  category: string
  status: 'active' | 'inactive'
  performance?: {
    totalReturn: number // 總回報率 (0.25 = 25%)
    sharpeRatio: number // Sharpe 比率
    maxDrawdown: number // 最大回撤 (0.083 = 8.3%)
    volatility: number // 波動率
    winRate: number // 勝率 (0.62 = 62%)
    profitFactor: number // 盈利因子
    calmarRatio: number // Calmar 比率
    var95: number // 95% VaR
    cvar95: number // 95% CVaR
    lastUpdated: Date // 最後更新時間
    dataQualityScore: number // 數據質量評分
  }
  parameters?: Record<string, any>
  latestSignal?: TradingSignal
  description: string
}
```

## 主題配置

### 顏色主題

```typescript
export const chartTheme = {
  primary: '#3498db', // 主藍色
  success: '#27ae60', // 成功綠色
  warning: '#f39c12', // 警告橙色
  danger: '#e74c3c', // 危險紅色
  info: '#9b59b6', // 信息紫色
  dark: '#34495e', // 深灰色
  light: '#ecf0f1', // 淺灰色
}
```

### 策略顏色映射

```typescript
const strategyColors = {
  direct_rsi: '#3498db',
  sentiment_momentum: '#27ae60',
  composite_index: '#f39c12',
  volatility_adjusted: '#e74c3c',
}
```

## 性能優化

### 1. 數據限制

- Sharpe 比率圖: 最多顯示 10 個策略
- 雷達圖: 最多顯示 4 個策略
- 历史數據: 根據時間範圍自動限制

### 2. 實時更新

- 默認更新間隔: 10 秒
- 可配置間隔: 5秒 - 1分鐘
- 頁面不可見時自動暫停

### 3. 內存管理

- 組件卸載時自動銷毀圖表實例
- 防止內存洩漏
- 智能垃圾回收

## 響應式設計

### 斷點設置

- `xs`: < 576px (手機)
- `sm`: ≥ 576px (平板)
- `md`: ≥ 768px (小型桌面)
- `lg`: ≥ 992px (桌面)
- `xl`: ≥ 1200px (大型桌面)

### 自適應策略

- 移動設備: 堆疊佈局
- 平板設備: 2列網格
- 桌面設備: 3-4列網格

## 無障礙支持

### 鍵盤導航

- Tab 鍵導航圖表元素
- Enter/Space 鍵激活交互
- Escape 鍵取消選擇

### 屏幕閱讀器

- ARIA 標籤支持
- 圖表數據表格備選
- 高對比度模式

## 測試

### 單元測試

```bash
# 運行圖表組件測試
npm test -- --testPathPattern=Charts

# 運行覆蓋率測試
npm test -- --coverage --testPathPattern=Charts
```

### 端到端測試

```bash
# 運行 E2E 測試
npm run test:e2e -- --spec="charts/**"
```

## 故障排除

### 常見問題

1. **圖表不顯示**
   - 檢查數據格式是否正確
   - 確認 Chart.js 已正確註冊
   - 驗證容器高度設置

2. **實時更新不工作**
   - 檢查 WebSocket 連接狀態
   - 確認組件是否在 ChartManagerProvider 內
   - 驗證更新間隔設置

3. **圖表渲染錯誤**
   - 檢查控制台錯誤信息
   - 確認數據值在有效範圍內
   - 驗證 Chart.js 版本兼容性

### 調試技巧

```tsx
// 開啟調試模式
const debugChart = () => {
  const chart = chartRef.current
  if (chart) {
    console.log('Chart instance:', chart)
    console.log('Chart data:', chart.data)
    console.log('Chart options:', chart.options)
  }
}

// 性能監控
const { performanceData } = useChartPerformance()
useEffect(() => {
  console.log('Chart performance:', performanceData)
}, [performanceData])
```

## 更新日誌

### v1.0.0 (2025-12-11)

- 初始版本發布
- 實現三個核心圖表組件
- 集成 Chart.js 4.x
- 添加實時更新功能
- 支持響應式設計

## 貢獻指南

1. Fork 項目倉庫
2. 創建功能分支
3. 提交代碼變更
4. 運行測試套件
5. 提交 Pull Request

## 許可證

本項目採用 MIT 許可證。詳見 [LICENSE](../../../LICENSE) 文件。
