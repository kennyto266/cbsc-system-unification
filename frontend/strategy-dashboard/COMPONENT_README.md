# CBSC Dashboard UI 組件文檔

## 概述

本文檔介紹了為 CBSC 策略管理 Dashboard 開發的四個核心 UI 組件，它們提供了豐富的交互功能和視覺效果，支持響應式設計和無障礙訪問。

## 組件列表

### 1. StrategyList (策略列表組件)

**功能描述：**
- 以表格和卡片兩種視圖展示策略列表
- 支持按多個欄位排序（夏普比率、最大回撤、勝率等）
- 內置搜索和分類篩選功能
- 響應式設計，適配各種屏幕尺寸

**主要方法：**
```javascript
// 創建策略列表
const strategyList = new StrategyList(containerElement);

// 設置策略數據
strategyList.setStrategies(strategies);

// 篩選策略
strategyList.filterByCategory('monthly_low_frequency');

// 排序策略
strategyList.sortStrategies('sharpeRatio');

// 更新策略狀態
strategyList.updateStrategyStatus(strategyId, enabled);
```

**事件監聽：**
```javascript
containerElement.addEventListener('strategy-list:toggle', (e) => {
  console.log('策略切換:', e.detail);
});

containerElement.addEventListener('strategy-list:show-details', (e) => {
  console.log('查看詳情:', e.detail);
});
```

### 2. PerformanceCards (性能數值卡片組件)

**功能描述：**
- 展示策略綜合評分、夏普比率、最大回撤、勝率等關鍵指標
- 支持動畫數值變化效果
- 包含趨勢指示器和風險等級評估
- 實時數據更新視覺化

**主要方法：**
```javascript
// 創建性能卡片
const performanceCards = new PerformanceCards(containerElement);

// 更新指標數據
performanceCards.updateMetrics(strategies);

// 刷新動畫效果
performanceCards.refreshAnimations();
```

**支持的指標：**
- 綜合評分（0-100分）
- 平均夏普比率
- 最大回撤與風險等級
- 平均勝率與進度條
- 策略狀態統計
- 近期表現趨勢圖

### 3. StatusIndicator (狀態指示器組件)

**功能描述：**
- 提供多種狀態視覺指示（運行中、載入中、錯誤、警告等）
- 支持工具提示顯示詳細信息
- 響應式尺寸調整
- 無障礙訪問支持

**使用示例：**
```javascript
// 創建狀態指示器
const indicator = new StatusIndicator(containerElement, {
  size: 'medium',        // small, medium, large
  showText: true,
  showIcon: true,
  animated: true
});

// 設置狀態
indicator.setActive('策略運行中', {
  lastUpdate: new Date().toISOString(),
  strategyId: 123,
  performance: '+15.6%'
});

// 設置載入狀態
indicator.setLoading('正在處理請求...');

// 設置錯誤狀態
indicator.setError('連接失敗', {
  errorCode: 'NETWORK_ERROR',
  retryCount: 3
});
```

**支持的狀態類型：**
- `loading` - 載入中
- `active`/`running` - 運行中
- `success`/`completed` - 成功/完成
- `inactive`/`stopped`/`disabled` - 非活躍/已停止/已禁用
- `error`/`failed` - 錯誤/失敗
- `warning`/`caution` - 警告/注意
- `info` - 信息
- `neutral`/`unknown` - 中性/未知

### 4. StrategyToggle (策略切換開關組件)

**功能描述：**
- 提供 iOS 風格的切換開關界面
- 支持停用確認對話框
- 觸摸友好的交互設計
- 狀態變化動畫效果

**使用示例：**
```javascript
// 創建切換開關
const toggle = new StrategyToggle(containerElement, '策略名稱', {
  size: 'medium',           // small, medium, large
  showLabel: true,
  showIcon: true,
  animated: true,
  confirmDisable: true,     // 停用時顯示確認對話框
  confirmMessage: '確定要停用此策略嗎？',
  onToggle: async (enabled) => {
    // 處理切換邏輯
    console.log('切換到狀態:', enabled);
    return true; // 返回 false 可以取消切換
  }
});

// 設置初始狀態
toggle.setState(true, false); // enabled, animate

// 程序化切換
await toggle.toggle();

// 監聽切換事件
toggle.onToggle((strategyName, newState) => {
  console.log(`${strategyName} 切換到 ${newState ? '啟用' : '禁用'}`);
});
```

**批量創建切換開關：**
```javascript
const toggles = StrategyToggle.createToggles(container, strategies, {
  size: 'small',
  onToggle: async (strategyName, enabled) => {
    // 批量處理邏輯
    return true;
  }
});
```

## 集成指南

### 基本集成步驟

1. **引入CSS樣式：**
```html
<link rel="stylesheet" href="css/dashboard.css">
<link rel="stylesheet" href="css/components.css">
```

2. **加載JavaScript組件：**
```html
<script src="js/components/StrategyList.js"></script>
<script src="js/components/PerformanceCards.js"></script>
<script src="js/components/StatusIndicator.js"></script>
<script src="js/components/StrategyToggle.js"></script>
```

3. **創建HTML容器：**
```html
<!-- 策略列表 -->
<div id="strategy-list"></div>

<!-- 性能卡片 -->
<div id="performance-cards"></div>

<!-- 狀態指示器 -->
<div id="status-indicators"></div>

<!-- 策略切換 -->
<div id="strategy-toggles"></div>
```

4. **初始化組件：**
```javascript
// 初始化策略列表
const strategyList = new StrategyList(document.getElementById('strategy-list'));
strategyList.setStrategies(strategiesData);

// 初始化性能卡片
const performanceCards = new PerformanceCards(document.getElementById('performance-cards'));
performanceCards.updateMetrics(strategiesData);

// 初始化狀態指示器
strategiesData.forEach(strategy => {
  const container = document.createElement('div');
  document.getElementById('status-indicators').appendChild(container);

  const indicator = new StatusIndicator(container);
  if (strategy.isActive) {
    indicator.setActive('運行中');
  } else {
    indicator.setInactive('已停止');
  }
});

// 初始化策略切換
const toggles = StrategyToggle.createToggles(
  document.getElementById('strategy-toggles'),
  strategiesData
);
```

### 使用增強版Dashboard

```html
<!-- 使用預配置的增強版Dashboard -->
<script src="js/dashboard-enhanced.js"></script>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const dashboard = new EnhancedDashboard();
  dashboard.init();
});
</script>
```

## 樣式自定義

### CSS變量

組件使用CSS變量實現主題化設計，可以通過修改根級變量來自定義外觀：

```css
:root {
  /* 顏色主題 */
  --primary-color: #2c3e50;
  --success-color: #27ae60;
  --warning-color: #f39c12;
  --danger-color: #e74c3c;
  --info-color: #3498db;

  /* 間距系統 */
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-3: 0.75rem;
  --spacing-4: 1rem;

  /* 字體大小 */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
}
```

### 組件特定樣式

每個組件都有專門的CSS類可以進行自定義：

```css
/* 自定義策略列表樣式 */
.strategy-table .strategy-row:hover {
  background: #f0f8ff;
}

/* 自定義性能卡片樣式 */
.performance-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 自定義狀態指示器動畫 */
.status-indicator[data-status="active"] .status-pulse {
  animation-duration: 1s;
}
```

## 響應式設計

所有組件都支持響應式設計：

- **桌面 (>1200px)**: 完整功能展示
- **平板 (768-1200px)**: 適配的佈局調整
- **手機 (<768px)**: 優化的移動體驗

## 無障礙訪問

組件支持無障礙訪問：

- 鍵盤導航支持
- ARIA標籤和角色
- 高對比度模式支持
- 屏幕閱讀器兼容

## 性能優化

### 建議的最佳實踐

1. **延遲加載**: 對於大量數據，使用分頁或虛擬滾動
2. **防抖處理**: 搜索和排序操作使用防抖功能
3. **事件委託**: 使用事件委託減少事件監聽器數量
4. **動畫優化**: 使用CSS transform和opacity屬性

### 內置性能特性

- 組件支持增量更新，只更新變化的部分
- 自動清理事件監聽器
- 防抖的搜索功能
- 動畫使用GPU加速

## 測試頁面

提供完整的組件測試頁面：

- `component-test.html` - 獨立的組件測試
- `index-enhanced.html` - 集成展示頁面

## 瀏覽器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 故障排除

### 常見問題

1. **組件未正確顯示**
   - 檢查CSS文件是否正確引入
   - 確認容器元素是否存在

2. **事件監聽器不工作**
   - 檢查組件是否已正確初始化
   - 確認事件名稱是否正確

3. **動畫效果卡頓**
   - 檢查是否在大量數據時使用動畫
   - 考慮使用CSS will-change屬性

4. **響應式佈局問題**
   - 檢查meta viewport標籤
   - 確認CSS媒體查詢是否正確

## 更新日誌

### v1.0.0 (2025-12-11)
- 初始版本發布
- 四個核心組件完成開發
- 完整的文檔和測試頁面

## 貢獻指南

歡迎提交問題報告和功能請求。在提交代碼前，請確保：

1. 所有測試通過
2. 代碼符合項目風格規範
3. 包含適當的文檔更新
4. 確保無障礙訪問兼容性

## 聯繫方式

如有問題或建議，請聯繫開發團隊或通過項目倉庫提交Issue。