# Mobile Components Library

移動優化組件庫，提供適應移動設備的高性能組件。

## 核心組件

### TouchFeedback
觸摸反饋組件，為移動設備提供視覺和觸覺反饋。

```tsx
import { TouchFeedback, Touchable } from '@/components/Mobile';

// 基本使用
<TouchFeedback onPress={() => console.log('pressed')}>
  <button>點擊我</button>
</TouchFeedback>

// 使用簡化的 Touchable 組件
<Touchable onPress={() => console.log('pressed')}>
  <div>可觸摸的內容</div>
</Touchable>

// 帶長按功能
<TouchFeedback
  onPress={() => console.log('tap')}
  onLongPress={() => console.log('long press')}
  longPressDelay={500}
>
  <div>支持長按</div>
</TouchFeedback>
```

**Props:**
- `onPress`: 點擊回調
- `onLongPress`: 長按回調
- `scale`: 縮放比例 (默認 0.95)
- `ripple`: 是否顯示漣漪效果 (默認 true)
- `disabled`: 是否禁用

### GestureRecognizer
高級手勢識別組件，支持多點觸控。

```tsx
import { GestureRecognizer } from '@/components/Mobile';

<GestureRecognizer
  callbacks={{
    onTap: (point) => console.log('tap at', point),
    onDoubleTap: (point) => console.log('double tap'),
    onSwipe: (direction) => console.log('swipe', direction),
    onPinch: (scale) => console.log('pinch', scale),
    onRotate: (angle) => console.log('rotate', angle),
  }}
  config={{
    swipeThreshold: 50,
    pinchThreshold: 20,
  }}
>
  <div>支持手勢的內容</div>
</GestureRecognizer>
```

**支持的單指手勢:**
- `onTap`: 輕觸
- `onDoubleTap`: 雙擊
- `onLongPress`: 長按
- `onSwipe`: 滑動
- `onPan`: 拖動

**支持的多指手勢:**
- `onPinch`: 捏合縮放
- `onRotate`: 旋轉

### OfflineMode
離線模式組件，提供緩存管理和離線狀態指示。

```tsx
import { OfflineMode, useOfflineMode } from '@/components/Mobile';

// 使用組件
<OfflineMode
  maxCacheSize={50} // MB
  retentionPeriod={24 * 7} // 小時
  onCacheUpdate={(stats) => console.log('cache stats', stats)}
>
  <App />
</OfflineMode>

// 使用 Hook
const { cacheData, getCachedData, clearCache } = useOfflineMode();

// 緩存數據
cacheData('strategy', '我的策略', strategyData, 24); // 24小時過期

// 獲取緩存
const cached = getCachedData('strategy');
```

### MobileOptimizedChart
移動優化的圖表組件，支持手勢交互和簡化模式。

```tsx
import { MobileOptimizedChart } from '@/components/Mobile';

const data = [
  { name: '1月', value: 100 },
  { name: '2月', value: 200 },
];

<MobileOptimizedChart
  data={data}
  type="line"
  title="策略表現"
  height={300}
  enableGestures={true}
  enableFullscreen={true}
  enableZoom={true}
  showTrendIndicator={true}
  simplified={isMobile}
  onDataPointClick={(point, index) => {
    console.log('Clicked:', point);
  }}
/>
```

**特性:**
- 手勢支持（滑動、捏合縮放、雙擊全屏）
- 自動簡化模式（小屏幕）
- 趨勢指示器
- 離線緩存支持
- 平滑動畫

### MobileOptimizedForm
移動優化的表單組件，支持大觸摸區域和自動進位。

```tsx
import { MobileOptimizedForm } from '@/components/Mobile';

const fields = [
  {
    name: 'name',
    label: '策略名稱',
    type: 'text',
    required: true,
    validation: {
      minLength: 2,
      maxLength: 50,
    },
  },
  {
    name: 'type',
    label: '策略類型',
    type: 'select',
    options: [
      { label: '高頻交易', value: 'high-frequency' },
      { label: '趨勢跟蹤', value: 'trend-following' },
    ],
  },
];

<MobileOptimizedForm
  fields={fields}
  onSubmit={handleSubmit}
  submitButtonText="創建策略"
  largeTouchTargets={true}
  stickySubmit={true}
  autoAdvance={true}
  validateOnChange={true}
/>
```

**特性:**
- 大觸摸區域
- 粘性提交按鈕
- 自動進位到下一欄位
- 實時驗證
- 手勢導航（左右滑動）

### MobileOptimizedList
移動優化的列表組件，支持滑動操作和虛擬滾動。

```tsx
import { MobileOptimizedList } from '@/components/Mobile';

const items = [
  {
    id: 1,
    title: '策略 Alpha',
    subtitle: '高頻交易',
    badge: '熱門',
    tags: ['高頻', '短期'],
  },
];

<MobileOptimizedList
  items={items}
  searchable={true}
  filterable={true}
  pullToRefresh={true}
  onRefresh={handleRefresh}
  onItemClick={handleItemClick}
  enableSwipeActions={true}
  swipeActions={{
    left: [
      { icon: <ArchiveIcon />, label: '存檔', color: 'bg-gray-500', onPress: handleArchive },
    ],
    right: [
      { icon: <TrashIcon />, label: '刪除', color: 'bg-red-500', onPress: handleDelete },
    ],
  }}
/>
```

**特性:**
- 搜索和過濾
- 拉取刷新
- 滑動操作
- 無限滾動
- 選擇模式
- 骨架屏加載

## Hooks

### useMobileOptimization
綜合移動優化 Hook。

```tsx
import { useMobileOptimization } from '@/hooks/useMobileOptimization';

const {
  screenInfo,  // 屏幕信息
  orientation, // 屏幕方向
  networkInfo, // 網絡狀態
  visibility,  // 頁面可見性
  safeArea,    // 安全區域
} = useMobileOptimization();
```

### useResponsive
響應式斷點 Hook。

```tsx
import { useResponsive } from '@/hooks/useMobileOptimization';

const {
  isMobile,    // 是否移動設備
  isTablet,    // 是否平板
  isDesktop,   // 是否桌面
  breakpoint,  // 當前斷點
  up,          // up('md') => width >= 768
  down,        // down('md') => width < 768
  between,     // between('sm', 'lg') => 480 <= width < 992
} = useResponsive();
```

## 最佳實踐

### 1. 觸摸目標大小
- 按鈕最小 44x44px
- 列表項目高度至少 48px
- 表單控件最小 48px 高度

### 2. 手勢使用
- 使用一致的滑動方向
- 提供視覺提示
- 支持撤销操作

### 3. 性能優化
- 使用虛擬滾動處理長列表
- 實現圖片懶加載
- 優化動畫性能

### 4. 離線支持
- 緩存關鍵數據
- 提供離線指示器
- 實現數據同步

### 5. 可訪問性
- 保持足夠的對比度
- 支持鍵盤導航
- 提供屏幕閱讀器支持

## 瀏覽器兼容性

- iOS Safari 12+
- Chrome Mobile 70+
- Firefox Mobile 68+
- Samsung Internet 10+

## 注意事項

1. **安全區域**: 使用 `SafeArea` 組件處理劉海屏
2. **橫屏模式**: 考慮橫屏時的佈局變化
3. **網絡狀態**: 適配不同網絡速度
4. **電量優化**: 減少不必要的動畫和輪詢