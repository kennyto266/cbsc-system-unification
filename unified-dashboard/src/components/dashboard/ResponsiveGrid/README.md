# CBSC響應式網格系統

一個強大的響應式網格佈局系統，專為CBSC量化交易Dashboard設計，支持拖拽、調整大小、持久化等高級功能。

## 功能特性

### 🎯 核心功能
- **響應式佈局**: 自動適應不同屏幕尺寸（lg, md, sm, xs, xxs）
- **拖拽支持**: 組件可以自由拖拽移動位置
- **調整大小**: 支持拖拽調整組件大小
- **佈局持久化**: 自動保存和恢復用戶的佈局設置
- **實時預覽**: 拖拽時實時預覽效果
- **批量操作**: 支持多選和批量操作組件

### 🎨 組件系統
- **預製組件庫**: 包含常用的Dashboard組件
- **自定義組件**: 支持HTML、Markdown、iframe等自定義內容
- **技術指標集成**: 與477技術指標系統深度集成
- **配置面板**: 雙擊打開組件配置面板
- **組件分類**: chart、metric、table、control、custom五大類別

### 💾 數據管理
- **LocalStorage持久化**: 自動保存到本地存儲
- **佈局導入導出**: 支持JSON格式導入導出
- **預設佈局**: 提供多種預設佈局模板
- **狀態管理**: 基於React Context的狀態管理

## 快速開始

### 1. 基本使用

```tsx
import { ResponsiveGridProvider, ResponsiveGrid } from './ResponsiveGrid'

function App() {
  return (
    <ResponsiveGridProvider>
      <ResponsiveGrid
        editable={true}
        showToolbar={true}
        onLayoutChange={(layout) => console.log('Layout changed', layout)}
      />
    </ResponsiveGridProvider>
  )
}
```

### 2. 添加組件

```tsx
import { useResponsiveGrid } from './ResponsiveGrid'

function AddWidgetButton() {
  const { addWidget } = useResponsiveGrid()

  const handleAdd = () => {
    addWidget({
      id: 'widget-1',
      type: 'technical-indicator',
      name: 'RSI指標',
      category: 'chart',
      x: 0,
      y: 0,
      w: 4,
      h: 3,
      config: {
        indicator: 'RSI',
        symbol: 'BTC/USDT',
        timeFrame: '1h'
      }
    })
  }

  return <button onClick={handleAdd}>添加組件</button>
}
```

### 3. 使用預設佈局

```tsx
const PRESET_LAYOUT = {
  widgets: [
    {
      id: 'market-overview',
      type: 'market-overview',
      name: '市場概覽',
      x: 0,
      y: 0,
      w: 12,
      h: 2
    },
    {
      id: 'strategy-performance',
      type: 'strategy-performance',
      name: '策略表現',
      x: 0,
      y: 2,
      w: 8,
      h: 4
    }
  ]
}
```

## API文檔

### ResponsiveGridProvider

網格系統的Context Provider，必須包裹在應用的頂層。

```tsx
<ResponsiveGridProvider>
  <YourApp />
</ResponsiveGridProvider>
```

### useResponsiveGrid Hook

獲取網格系統的狀態和操作方法。

```tsx
const {
  // 狀態
  widgets,           // 所有組件列表
  layouts,          // 所有斷點的佈局
  currentBreakpoint,// 當前斷點
  gridConfig,       // 當前網格配置

  // 操作方法
  addWidget,        // 添加組件
  removeWidget,     // 刪除組件
  updateWidget,     // 更新組件
  moveWidget,       // 移動組件
  resizeWidget,     // 調整組件大小

  // 佈局操作
  saveLayout,       // 保存佈局
  loadLayout,       // 加載佈局
  exportLayout,     // 導出佈局
  importLayout,     // 導入佈局
  resetLayout       // 重置佈局
} = useResponsiveGrid()
```

### ResponsiveGrid Component

主要的網格組件。

```tsx
<ResponsiveGrid
  editable={true}              // 是否可編輯
  showToolbar={true}           // 是否顯示工具欄
  onLayoutChange={handleLayoutChange}
  onWidgetClick={handleWidgetClick}
  onWidgetDoubleClick={handleWidgetConfig}
/>
```

## 組件類型

### 內置組件類型

1. **market-overview** - 市場概覽
2. **technical-indicator** - 技術指標
3. **strategy-performance** - 策略表現
4. **asset-allocation** - 資產配置
5. **system-health** - 系統健康
6. **recent-signals** - 最近信號
7. **quick-actions** - 快速操作
8. **custom-widget** - 自定義組件

### 組件配置

每個組件都支持以下配置：

```tsx
interface GridWidget {
  id: string              // 唯一標識
  type: string            // 組件類型
  name: string            // 組件名稱
  category: string        // 組件分類

  // 位置和大小
  x: number               // X坐標
  y: number               // Y坐標
  w: number               // 寬度（格）
  h: number               // 高度（格）
  minW: number            // 最小寬度
  minH: number            // 最小高度
  maxW: number            // 最大寬度
  maxH: number            // 最大高度

  // 屬性
  isDraggable: boolean     // 是否可拖拽
  isResizable: boolean     // 是否可調整大小
  config?: object         // 自定義配置
  data?: any             // 組件數據
}
```

## 響應式斷點

```tsx
const BREAKPOINTS = {
  lg: 1200,    // 大屏幕 - 12列
  md: 992,     // 中等屏幕 - 10列
  sm: 768,     // 小屏幕 - 6列
  xs: 576,     // 超小屏幕 - 4列
  xxs: 0       // 極小屏幕 - 2列
}
```

## 佈局持久化

### 自動保存

佈局會自動保存到LocalStorage：

```tsx
// 保存當前佈局
saveLayout('my-layout')

// 加載保存的佈局
loadLayout('my-layout')
```

### 導入導出

```tsx
// 導出佈局為JSON
const layoutJson = exportLayout()

// 從JSON導入佈局
importLayout(layoutJson)
```

## 自定義組件

### 創建自定義組件

```tsx
import { WidgetRenderer } from './ResponsiveGrid'

const CustomWidget: React.FC<{ widget: GridWidget }> = ({ widget }) => {
  return (
    <div className="custom-widget">
      <h3>{widget.name}</h3>
      {/* 自定義內容 */}
    </div>
  )
}

// 註冊組件
const WIDGET_TYPES = {
  ...DEFAULT_WIDGET_TYPES,
  'my-custom': {
    id: 'my-custom',
    type: 'my-custom',
    name: '自定義組件',
    category: 'custom',
    // ...其他配置
  }
}
```

### 配置面板

```tsx
// 組件配置Modal
<WidgetConfigModal
  widget={selectedWidget}
  visible={configModalVisible}
  onClose={() => setConfigModalVisible(false)}
  onSave={(updatedWidget) => {
    updateWidget(updatedWidget.id, updatedWidget)
  }}
/>
```

## 最佳實踐

### 1. 組件設計
- 保持組件輕量級
- 使用React.memo優化性能
- 支持響應式設計

### 2. 佈局規劃
- 合理設置最小/最大尺寸
- 使用網格對齊
- 考慮不同斷點的適配

### 3. 性能優化
- 避免過多的組件
- 使用虛擬化處理大量數據
- 合理設置更新頻率

## 示例頁面

- `/responsive-dashboard` - 完整的響應式Dashboard
- `/dashboard-example` - 網格系統使用示例

## 依賴包

- `react-grid-layout` - 網格佈局核心
- `react-resizable` - 調整大小功能
- `react-hot-toast` - 消息提示

## 注意事項

1. 確保包裹在`ResponsiveGridProvider`中
2. 組件ID必須唯一
3. 避免頻繁的佈局更新
4. 合理使用localStorage空間