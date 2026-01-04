# CBSC 量化交易系統首頁優化設計

**日期**: 2025-12-28
**版本**: 1.0
**狀態**: 待實施

## 概述

本文檔描述了 CBSC 量化交易系統首頁（http://localhost:3000/）的優化設計方案，旨在創建一個「一目了然地掌握全局」的綜合儀表板，同時提供強大的回測和策略開發功能。

## 設計目標

1. **全局概覽** - 一眼看到所有關鍵指標和策略狀態
2. **快速操作** - 緊湊工具欄提供回測和策略開發的快速入口
3. **實時監控** - 分屏設計一屏掌控策略執行、市場數據和警報
4. **深度分析** - 詳細歸因分析揭示收益來源和風險驅動因素

## 整體架構

### Tab 結構

保持現有的 Tab 切換式結構，優化每個 tab 的內容：

1. **總覽** - 綜合儀表板，一目了然
2. **實時監控** - 分屏監控，一屏掌控
3. **性能分析** - 深度歸因，洞察根源
4. **設置** - 儀表板配置（保持現有）

### 頂部快捷工具欄

所有 tab 共享的緊湊工具欄：

```
[立即回測] [新建策略] [策略模板] [查看結果]
```

- 採用緊湊設計，按鈕帶圖標
- 固定在頁面頂部，方便隨時訪問
- 不佔用太多垂直空間

### 視覺風格

- **深色主題**: cyberpunk 金融美學
- **顏色編碼**: 綠色(好)、黃色(注意)、紅色(警報)
- **動畫**: 流暢的過渡動畫（Framer Motion）
- **響應式**: 支持桌面和平板

---

## 第一部分：「總覽」Tab

### 布局結構

```
┌─────────────────────────────────────────────────┐
│  關鍵指標卡片区（4列網格）                        │
│  [總收益率] [勝率] [最大回撤] [夏普比率]           │
│  [運行中策略] [今日盈虧] [風險等級] [系統健康度]  │
└─────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────────┐
│  策略狀態列表（左60%） │ 經濟數據監控（右40%）   │
│  ┌──────────────────┐ │ ┌────────────────────┐ │
│  │ 策略A 🟢 +2.3%    │ │ │ HIBOR: 5.23% 📈   │ │
│  │ 策略B 🟡 +0.8%    │ │ │ GDP: 3.20% 📊     │ │
│  │ 策略C 🔴 -1.2%    │ │ │ PMI: 50.10 📉     │ │
│  │ 策略D 🟢 +1.5%    │ │ │ Visitors: 3.5M    │ │
│  └──────────────────┘ │ │ Unemployment: 3.0%│ │
│  [查看全部策略]        │ └────────────────────┘ │
└──────────────────────┴──────────────────────────┘
```

### 關鍵指標卡片

- **大字號顯示數值**: 一眼可見
- **較昨日變化**: 小字號顯示 ↑↓
- **漸變背景**: 區分不同類別的指標
- **響應式**: 桌面4列，平板2列，手機1列

**指標列表**:
- 總收益率（Total Return）
- 勝率（Win Rate）
- 最大回撤（Max Drawdown）
- 夏普比率（Sharpe Ratio）
- 運行中策略數（Active Strategies）
- 今日盈虧（Today's P&L）
- 風險等級（Risk Level）
- 系統健康度（System Health）

### 策略狀態列表

每個策略一行，顯示：
- **名稱**: 策略名稱
- **狀態燈**: 🟢運行正常 🟡需要注意 🔴停止/異常
- **今日收益率**: 帶箭頭和顏色
- **懸停操作**: 啟動/停止/編輯

底部「查看全部策略」按鈕跳轉到策略管理頁面。

### 經濟數據監控

5個迷你卡片，縱向排列，每個包含：
- **指標名稱**: HIBOR、GDP、PMI、Visitors、Unemployment
- **當前值**: 大字號顯示
- **迷你走勢圖**: Sparkline 顯示最近7天/月變化
- **點擊交互**: 展開詳細數據或跳轉到策略生成器

**異常處理**:
- 數據異常時卡片邊框變黃/紅色
- 顯示「警告」或「警報」標籤

---

## 第二部分：「實時監控」Tab

### 分屏布局

```
┌──────────────────────────────────────────────────────────┐
│ 左側：策略執行狀態 (40%)      │   右側：市場數據 (60%)   │
│ ┌──────────────────────────┐ │ ┌──────────────────────┐ │
│ │ 運行中策略實時監控        │ │ │ 實時行情              │ │
│ │ ┌──────────────────────┐ │ │ │ ┌──────────────────┐ │ │
│ │ │ 策略A │ ↗ +0.12% │  │ │ │ │ │ 恆生指數 │ 17850 │ │ │
│ │ │ 策略B │ ↘ -0.05% │  │ │ │ │ │ HIBOR   │ 5.23% │ │ │
│ │ │ 策略C │ →  0.00% │  │ │ │ │ │ VIX     │ 18.5  │ │ │
│ │ └──────────────────────┘ │ │ │ └──────────────────┘ │ │
│ │                          │ │ │                       │ │
│ │ 訂單執行狀態              │ │ │ 經濟數據實時更新      │ │
│ │ ┌──────────────────────┐ │ │ │ ┌──────────────────┐ │ │
│ │ │ 待執行: 3 │ 成功: 125│ │ │ │ │ PMI剛更新! +0.5 │ │ │
│ │ │ 失敗: 0  │ 平均延遲  │ │ │ └──────────────────┘ │ │
│ │ └──────────────────────┘ │ │                       │ │
│ └──────────────────────────┘ │ └──────────────────────┘ │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 底部：警報滾動條（全寬，高度 60px，自動滾動）              │
│ ⚠️ 策略B觸發風險警報  │  📊 新經濟數據可用  │  🔧 系統檢查提醒 │
└──────────────────────────────────────────────────────────┘
```

### 左側 - 策略執行狀態

**實時盈虧監控**:
- 每秒更新數值（WebSocket推送）
- 箭頭表示趨勢（↗ ↘ →）
- 顏色編碼：綠色(盈利)、紅色(虧損)

**訂單執行統計**:
- 待執行數量
- 成功數量
- 失敗數量
- 平均執行延遲
- 成功率百分比

**系統資源監控**:
- CPU使用率
- 內存佔用
- WebSocket連接狀態（🟢正常 🟡重連中 🔴斷開）

### 右側 - 市場數據

**實時行情板**:
- 恆生指數
- VIX 波動率指數
- 關鍵匯率

**經濟數據即時通知**:
- 最新數據高亮動畫顯示
- 顯示「剛更新！變化量」
- 自動消失通知（5秒後淡出）

**迷你K線圖**:
- 點擊可展開詳細圖表
- 支持縮放和平移

### 底部 - 警報滾動條

全寬橫向滾動條，顯示：
- 最近24小時內的所有警報
- 顏色編碼：黃色=注意，紅色=緊急
- 點擊展開詳情或跳轉處理

---

## 第三部分：「性能分析」Tab

### 布局結構

```
┌──────────────────────────────────────────────────────────┐
│ 頂部：分析控制欄                                           │
│ 時間範圍: [1週 ▼]  策略選擇: [全選 ▼]  [對比模式] [導出報告] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 收益來源分解（堆疊條形圖或聖杯圖）                        │
│ 顯示各經濟指標對總收益的貢獻占比                           │
└──────────────────────────────────────────────────────────┘

┌─────────────────────────────┬───────────────────────────┐
│ 風險歸因分析（雷達圖）      │ 策略相關性矩陣（熱力圖）  │
│ 五維風險暴露評估           │ 策略間相關性分析          │
└─────────────────────────────┴───────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 壓力測試結果                                             │
│ 4種場景下的預期表現：基準、利率上升、經濟衰退、市場崩盤   │
└──────────────────────────────────────────────────────────┘
```

### 1. 收益來源分解

- **圖表類型**: 堆疊條形圖或 Sankey 圖
- **顯示內容**: 每個經濟指標對總收益的貢獻百分比
- **顏色編碼**: 正貢獻顯示綠色，負貢獻顯示紅色
- **交互功能**:
  - 懸停顯示具體數值和計算公式
  - 切換不同時間範圍查看變化
  - 點擊圖例顯示/隱藏特定指標

### 2. 風險歸因分析（雷達圖）

**5個維度**:
- 系統性風險
- 利率風險
- 流動性風險
- 經濟增長風險
- 匯率風險

**功能特性**:
- 顯示當前策略在各維度的風險暴露
- 對比多個策略的風險輪廓
- 紅色區域標示風險過高
- 可切換3D視覺效果

### 3. 策略相關性矩陣（熱力圖）

- **數據**: 策略間的相關性係數（-1到+1）
- **顏色編碼**:
  - 綠色 = 低相關（好，多樣化）
  - 紅色 = 高相關（風險集中）
- **對角線**: 自己與自己完全相關（=1）
- **用途**: 識別策略組合的多樣化程度

### 4. 壓力測試結果

**4種壓力場景**:
| 場景 | 描述 |
|------|------|
| 基準 | 正常市場條件 |
| 利率+200bp | 利率急劇上升 |
| 經濟衰退 | GDP負增長、失業率上升 |
| 市場崩盤 | 極端情況下的壓力測試 |

**顯示指標**:
- 預期收益
- 最大回撤
- 夏普比率

**功能特性**:
- 紅色高亮風險場景下的虧損
- 可自定義壓力測試參數
- 導出壓力測試報告

---

## 技術實現

### 組件層級結構

```
DashboardPage.tsx
├── DashboardHeader.tsx (快捷工具欄)
├── OverviewTab/
│   ├── MetricsCards.tsx (關鍵指標卡片 - 8個)
│   ├── StrategyList.tsx (策略狀態列表)
│   └── EconomicMiniCards.tsx (經濟數據迷你卡片 - 5個)
├── MonitoringTab/
│   ├── StrategyExecutionPanel.tsx (左側：策略執行)
│   ├── MarketDataPanel.tsx (右側：市場數據)
│   └── AlertTicker.tsx (底部：警報滾動條)
└── PerformanceTab/
    ├── ReturnAttribution.tsx (收益來源分解)
    ├── RiskRadarChart.tsx (風險雷達圖)
    ├── CorrelationHeatmap.tsx (相關性矩陣)
    └── StressTestTable.tsx (壓力測試表格)
```

### 數據流設計

#### 1. WebSocket 實時數據流

```typescript
class DashboardWebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  // 訂閱策略實時數據
  subscribeToStrategyUpdates(callback: (data: StrategyUpdate) => void) {
    // ...
  }

  // 訂閱市場數據
  subscribeToMarketData(callback: (data: MarketData) => void) {
    // ...
  }

  // 訂閱警報
  subscribeToAlerts(callback: (alert: Alert) => void) {
    // ...
  }

  // 心跳檢測
  heartbeat() {
    setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  // 自動重連（指數退避）
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect()
      }, 1000 * Math.pow(2, this.reconnectAttempts))
    }
  }
}
```

#### 2. Redux Store 結構

```typescript
// dashboardSlice.ts
interface DashboardState {
  metrics: {          // 關鍵指標
    totalReturn: number
    winRate: number
    maxDrawdown: number
    sharpeRatio: number
    activeStrategies: number
    todayPnL: number
    riskLevel: string
    systemHealth: string
  }
  strategies: {       // 策略狀態
    running: Strategy[]
    paused: Strategy[]
    stopped: Strategy[]
  }
  economicData: {     // 經濟數據
    hibor: EconomicDataPoint[]
    gdp: EconomicDataPoint[]
    pmi: EconomicDataPoint[]
    visitors: EconomicDataPoint[]
    unemployment: EconomicDataPoint[]
  }
  alerts: Alert[]      // 警報列表
  monitoring: {       // 實時監控數據
    executions: Execution[]
    orderStatus: OrderStatus
    resourceUsage: ResourceUsage
  }
  performance: {       // 性能分析數據
    returnAttribution: AttributionData
    riskExposure: RiskData
    correlations: CorrelationMatrix
    stressTest: StressTestResult[]
  }
}
```

#### 3. API 調用策略

```typescript
// 首次加載：並行獲取所有數據
useEffect(() => {
  const loadInitialData = async () => {
    const [
      metrics,
      strategies,
      economicData,
      alerts
    ] = await Promise.all([
      api.get('/api/dashboard/metrics'),
      api.get('/api/strategies'),
      api.get('/api/economic/all'),
      api.get('/api/alerts/recent')
    ])

    dispatch(setMetrics(metrics.data))
    dispatch(setStrategies(strategies.data))
    dispatch(setEconomicData(economicData.data))
    dispatch(setAlerts(alerts.data))
  }

  loadInitialData()
}, [])

// WebSocket更新實時數據
useWebSocket('ws://localhost:3001/dashboard', (data) => {
  switch (data.type) {
    case 'METRICS_UPDATE':
      dispatch(updateMetrics(data.payload))
      break
    case 'STRATEGY_UPDATE':
      dispatch(updateStrategies(data.payload))
      break
    case 'ALERT':
      dispatch(addAlert(data.payload))
      break
    case 'MARKET_DATA':
      dispatch(updateMarketData(data.payload))
      break
  }
})
```

### 性能優化

#### 1. 虛擬化長列表

```typescript
import { FixedSizeList } from 'react-window'

// 策略列表虛擬化
const StrategyList = ({ strategies }) => (
  <FixedSizeList
    height={400}
    itemCount={strategies.length}
    itemSize={60}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        <StrategyItem strategy={strategies[index]} />
      </div>
    )}
  </FixedSizeList>
)
```

#### 2. 防抖與節流

```typescript
import { throttle, debounce } from 'lodash'

// 圖表數據更新節流（500ms）
const throttledUpdate = throttle((data) => {
  updateCharts(data)
}, 500)

// 搜索框防抖（300ms）
const debouncedSearch = debounce((query) => {
  performSearch(query)
}, 300)
```

#### 3. 懶加載

```typescript
import { lazy, Suspense } from 'react'

// 圖表組件延遲加載
const ReturnAttribution = lazy(() =>
  import('./ReturnAttribution')
)
const CorrelationHeatmap = lazy(() =>
  import('./CorrelationHeatmap')
)

// 在 tab 切換時才加載
<TabPane key="performance">
  <Suspense fallback={<Loading />}>
    <ReturnAttribution />
    <CorrelationHeatmap />
  </Suspense>
</TabPane>
```

### 錯誤處理

#### 1. WebSocket 斷線處理

```typescript
ws.onclose = () => {
  console.log('WebSocket disconnected')

  // 指數退避重連
  if (reconnectAttempts < maxReconnectAttempts) {
    setTimeout(() => {
      reconnectAttempts++
      reconnect()
    }, 1000 * Math.pow(2, reconnectAttempts))
  } else {
    // 降級到輪詢模式
    startPolling()
    showErrorMessage('實時連接失敗，已切換到輪詢模式')
  }
}
```

#### 2. 數據加載失敗降級

```typescript
const fetchWithFallback = async (url, cacheKey) => {
  try {
    const response = await api.get(url)
    return response.data
  } catch (error) {
    // 嘗試從緩存讀取
    const cached = localStorage.getItem(cacheKey)
    if (cached) {
      const data = JSON.parse(cached)
      showWarningMessage('使用緩存數據，可能不是最新的')
      return { ...data, _stale: true }
    }
    throw error
  }
}
```

#### 3. 用戶友好的錯誤邊界

```typescript
class DashboardErrorBoundary extends React.Component {
  state = { hasError: false }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Dashboard error:', error, errorInfo)
    // 上報錯誤到監控服務
    reportError(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <DashboardError
          onReset={() => this.setState({ hasError: false })}
        />
      )
    }
    return this.props.children
  }
}
```

---

## 實施步驟

### Phase 1: 基礎結構（2-3天）
1. 創建組件目錄結構
2. 實現 DashboardHeader 工具欄
3. 更新 Redux store 結構
4. 建立數據獲取 API

### Phase 2: 總覽 Tab（3-4天）
1. 實現 MetricsCards 組件
2. 實現 StrategyList 組件
3. 實現 EconomicMiniCards 組件
4. 整合到 OverviewTab

### Phase 3: 實時監控 Tab（4-5天）
1. 建立 WebSocket 連接管理
2. 實現 StrategyExecutionPanel
3. 實現 MarketDataPanel
4. 實現 AlertTicker
5. 整合到 MonitoringTab

### Phase 4: 性能分析 Tab（5-6天）
1. 實現 ReturnAttribution 圖表
2. 實現 RiskRadarChart
3. 實現 CorrelationHeatmap
4. 實現 StressTestTable
5. 整合到 PerformanceTab

### Phase 5: 優化與測試（3-4天）
1. 性能優化（虛擬化、防抖節流、懶加載）
2. 錯誤處理完善
3. 響應式調整
4. 端到端測試

**總計估計時間**: 17-22 天

---

## 成功標準

- [ ] 首頁加載時間 < 2秒
- [ ] WebSocket 實時延遲 < 500ms
- [ ] 所有关鍵指標在一屏內可見
- [ ] 策略狀態實時更新準確率 > 99%
- [ ] 錯誤處理覆蓋所有邊界情況
- [ ] 移動端和平板端響應式正常
- [ ] 用戶可以快速找到常用功能（< 3次點擊）

---

## 相關文檔

- [策略生成器實現](/frontend/src/pages/strategies/components/StrategyGenerator.tsx)
- [API 文檔](/docs/api/)
- [經濟數據 API](/frontend/src/services/economicDataApi.ts)

---

*本文檔將在實施過程中持續更新*
