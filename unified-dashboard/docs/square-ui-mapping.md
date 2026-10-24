# Square-UI組件映射文檔

本文檔描述了Square-UI組件如何適配到CBSC量化交易系統中。

## 組件映射關係

### 1. Dashboard 模板組件

| Square-UI 組件 | CBSC 適配組件 | 用途描述 |
|---------------|---------------|----------|
| `DashboardHeader` | `src/components/layout/Header.tsx` | 頂部導航和用戶信息 |
| `SidebarNav` | `src/components/layout/Sidebar.tsx` | 側邊欄導航 |
| `MetricCard` | `src/components/square-ui/MetricCard.tsx` | 關鍵指標展示 |
| `StatGrid` | `src/components/dashboard/MetricCard.tsx` | 統計數據網格 |
| `ActivityFeed` | `src/components/dashboard/RecentSignals.tsx` | 活動流 |
| `QuickActions` | `src/components/dashboard/QuickActions.tsx` | 快速操作 |

### 2. CRM 模板組件

| Square-UI 組件 | CBSC 適配組件 | 用途描述 |
|---------------|---------------|----------|
| `DataTable` | `src/components/square-ui/Grid.tsx` | 數據表格展示 |
| `UserCard` | `src/components/WidgetTypes/StrategyOverview.tsx` | 用戶/策略卡片 |
| `ContactForm` | `src/components/forms/StrategyForm.tsx` | 表單組件 |
| `FilterBar` | `src/components/dashboard/FilterPanel.tsx` | 過濾器 |
| `SearchInput` | `src/components/common/SearchBar.tsx` | 搜索輸入 |

### 3. Tasks 模板組件

| Square-UI 組件 | CBSC 適配組件 | 用途描述 |
|---------------|---------------|----------|
| `TaskCard` | `src/components/WidgetTypes/BacktestResults.tsx` | 任務/回測卡片 |
| `StatusBadge` | `src/components/ui/Badge.tsx` | 狀態標籤 |
| `ProgressBar` | `src/components/ui/Progress.tsx` | 進度條 |
| `DropdownMenu` | `src/components/ui/Dropdown.tsx` | 下拉菜單 |
| `CalendarView` | `src/components/dashboard/Calendar.tsx` | 日曆視圖 |

## 適配策略

### 1. 數據適配

**交易特定數據類型:**
- 股票/期貨價格 → 使用 PriceDisplay 組件
- 收益率 → 使用 PercentageIndicator 組件
- 風險指標 → 使用 RiskMeter 組件
- 交易量 → 使用 VolumeBar 組件

### 2. 主題適配

**顏色映射:**
```typescript
const tradingColors = {
  profit: 'success.green',    // 盈利
  loss: 'danger.red',        // 虧損
  neutral: 'gray.500',       // 中性
  bullish: 'success.green',  // 看漲
  bearish: 'danger.red',     // 看跌
}
```

### 3. 圖表適配

**金融圖表類型:**
- 時間序列圖 → CandlestickChart, LineChart
- 分布圖 → Histogram, ScatterPlot
- 熱力圖 → Heatmap
- K線圖 → OHLCChart

## CBSC特定組件

### 1. TradingCard
```typescript
interface TradingCardProps {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap: number
}
```

### 2. StrategyCard
```typescript
interface StrategyCardProps {
  name: string
  type: string
  status: 'active' | 'paused' | 'stopped'
  performance: {
    totalReturn: number
    winRate: number
    maxDrawdown: number
    sharpeRatio: number
  }
  lastRun: Date
}
```

### 3. MetricCard
```typescript
interface MetricCardProps {
  title: string
  value: number | string
  change?: number
  changeType?: 'increase' | 'decrease' | 'neutral'
  icon?: React.ReactNode
  format?: 'currency' | 'percentage' | 'number'
}
```

## 組件使用示例

### Dashboard 頁面
```typescript
import { MetricCard, StrategyCard, TradingCard } from '@/components/square-ui'

const Dashboard = () => {
  return (
    <div className="grid grid-cols-12 gap-4">
      {/* 關鍵指標 */}
      <div className="col-span-3">
        <MetricCard
          title="總資產"
          value="1,234,567"
          change={2.34}
          format="currency"
        />
      </div>

      {/* 策略列表 */}
      <div className="col-span-9">
        <StrategyCard
          name="RSI均值回歸"
          status="active"
          performance={{
            totalReturn: 15.4,
            winRate: 68.2,
            maxDrawdown: -8.3,
            sharpeRatio: 1.24
          }}
        />
      </div>
    </div>
  )
}
```

### 策略管理頁面
```typescript
const StrategyManagement = () => {
  return (
    <div className="space-y-4">
      {/* 策略列表 */}
      <Grid>
        {strategies.map(strategy => (
          <StrategyCard key={strategy.id} {...strategy} />
        ))}
      </Grid>

      {/* 新增策略按鈕 */}
      <Button
        variant="primary"
        onClick={() => setShowCreateModal(true)}
      >
        新增策略
      </Button>
    </div>
  )
}
```

## 遷移指南

### 1. 現有組件遷移

**步驟:**
1. 識別需要遷移的組件
2. 創建對應的CBSC適配組件
3. 更新導入路徑
4. 測試組件功能
5. 更新文檔

### 2. 樣式遷移

**CSS類名映射:**
```css
/* Square-UI -> CBSC */
.square-btn -> .cbsc-btn
.square-card -> .cbsc-card
.square-table -> .cbsc-table
```

### 3. 數據格式適配

**金融數據格式:**
```typescript
// 價格格式化
const formatPrice = (price: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(price)
}

// 百分比格式化
const formatPercentage = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}
```

## 性能優化

### 1. 組件懶加載
```typescript
const HeavyChart = lazy(() => import('@/components/charts/HeavyChart'))

// 使用時
<Suspense fallback={<Loading />}>
  <HeavyChart data={chartData} />
</Suspense>
```

### 2. 虛擬化
```typescript
// 長列表使用虛擬滾動
import { FixedSizeList as List } from 'react-window'

const VirtualTable = ({ items }) => (
  <List
    height={400}
    itemCount={items.length}
    itemSize={50}
    itemData={items}
  >
    {({ index, style, data }) => (
      <div style={style}>
        <TableRow data={data[index]} />
      </div>
    )}
  </List>
)
```

## 測試策略

### 1. 單元測試
```typescript
import { render, screen } from '@testing-library/react'
import { MetricCard } from '@/components/square-ui/MetricCard'

test('MetricCard displays correct values', () => {
  render(<MetricCard title="Test" value={123} />)
  expect(screen.getByText('Test')).toBeInTheDocument()
  expect(screen.getByText('123')).toBeInTheDocument()
})
```

### 2. 集成測試
```typescript
test('Dashboard renders all components', async () => {
  const { findByText } = render(<Dashboard />)
  expect(await findByText('總資產')).toBeInTheDocument()
})
```

## 維護和更新

### 1. 版本控制
- 使用Git submodules管理Square-UI源碼
- 建立組件版本映射表
- 記錄自定義修改

### 2. 文檔維護
- 更新組件API文檔
- 維護遷移指南
- 更新最佳實踐

### 3. 測試維護
- 更新測試用例
- 執行回歸測試
- 監控組件性能

## 支持和幫助

如有問題，請參考：
1. [Square-UI文檔](https://square-ui.vercel.app)
2. [CB組件庫文檔](https://ui.shadcn.com)
3. [Tailwind CSS文檔](https://tailwindcss.com/docs)

---

最後更新: 2025-12-17