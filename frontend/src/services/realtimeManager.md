# 實時數據更新管理器 (Realtime Data Manager)

## 概述

實時數據更新管理器提供了一個統一的解決方案，用於在 CBSC 策略管理 Dashboard 中實現實時數據更新。它整合了 WebSocket 連接、定時器管理、網路狀態監控和錯誤處理等功能。

## 主要功能

### 1. 自動數據刷新
- **預設間隔**: 10秒
- **可配置**: 支援自訂更新間隔（5秒 - 5分鐘）
- **智能檢測**: 只有在數據變更時才更新 UI

### 2. WebSocket 實時推送
- **策略更新**: 即時接收策略狀態變更
- **性能指標**: 實時更新 Sharpe 比率、回撤等指標
- **交易信號**: 即時推送新的交易信號
- **自動重連**: 網路中斷時自動嘗試重新連接

### 3. 網路狀態監控
- **離線檢測**: 自動檢測網路連線狀態
- **暫停機制**: 離線時自動暫停更新
- **恢復同步**: 重新上線時立即同步數據

### 4. 加載狀態管理
- **細粒度控制**: 支援全域、圖表、策略等不同層級的加載狀態
- **骨架屏**: 提供優雅的加載動畫
- **用戶反饋**: 清晰的加載進度指示

### 5. 錯誤處理機制
- **重試策略**: 智能指數退避重試
- **錯誤分類**: 區分網路錯誤、API 錯誤、WebSocket 錯誤
- **用戶提示**: 友好的錯誤訊息和恢復建議

## 使用方法

### 基本使用

```typescript
import { getRealtimeManager } from '../services/realtimeManager';
import { StrategyDashboardWithRealtime } from '../components/StrategyDashboard/StrategyDashboardWithRealtime';

// 使用預設配置的 Dashboard
function App() {
  return (
    <StrategyDashboardWithRealtime
      apiUrl="/api"
      wsUrl="ws://localhost:3003/ws"
      refreshInterval={10000} // 10秒
      enableRealtime={true}
    />
  );
}
```

### 高級配置

```typescript
import { getRealtimeManager } from '../services/realtimeManager';

const realtimeManager = getRealtimeManager({
  updateInterval: 5000,        // 5秒更新間隔
  maxRetries: 5,              // 最大重試次數
  retryDelay: 2000,           // 重試延遲
  enableWebSocket: true,       // 啟用 WebSocket
  enablePeriodicRefresh: true  // 啟用定時刷新
});

// 初始化並設置回調
await realtimeManager.initialize({
  onStrategyUpdate: (strategies) => {
    console.log('策略更新:', strategies);
    // 更新策略列表
  },
  onPerformanceUpdate: (performance) => {
    console.log('性能更新:', performance);
    // 更新性能圖表
  },
  onError: (error, context) => {
    console.error(`錯誤 (${context}):`, error);
    // 錯誤處理
  },
  onNetworkChange: (status) => {
    console.log('網路狀態變更:', status);
    // 更新網路狀態 UI
  }
});

// 啟動實時更新
realtimeManager.start();
```

### 自訂回調

```typescript
realtimeManager.initialize({
  onSyncStart: () => {
    console.log('數據同步開始');
    showLoadingIndicator();
  },

  onSyncComplete: (duration) => {
    console.log(`數據同步完成，耗時 ${duration}ms`);
    hideLoadingIndicator();

    // 性能警告
    if (duration > 500) {
      console.warn('數據同步較慢，請檢查網路或服務器性能');
    }
  },

  onStrategyUpdate: (strategies) => {
    // 只更新有變更的策略
    strategies.forEach(strategy => {
      updateStrategyCard(strategy.id, strategy);
    });

    // 觸發動畫
    animateUpdatedCards();
  },

  onPerformanceUpdate: (performance) => {
    // 更新性能圖表
    performanceCharts.forEach(chart => {
      const data = performance.find(p => p.strategyId === chart.strategyId);
      if (data) {
        chart.updateData(data);
      }
    });
  }
});
```

## API 參考

### RealtimeManager 類

#### 配置選項

```typescript
interface RealtimeConfig {
  updateInterval: number;      // 更新間隔（毫秒）
  maxRetries: number;         // 最大重試次數
  retryDelay: number;         // 重試延遲（毫秒）
  enableWebSocket: boolean;    // 是否啟用 WebSocket
  enablePeriodicRefresh: boolean; // 是否啟用定時刷新
}
```

#### 回調函數

```typescript
interface RealtimeCallbacks {
  onStrategyUpdate?: (strategies: Strategy[]) => void;
  onPerformanceUpdate?: (performance: PerformanceMetrics[]) => void;
  onError?: (error: Error, context: string) => void;
  onNetworkChange?: (status: NetworkStatus) => void;
  onSyncStart?: () => void;
  onSyncComplete?: (duration: number) => void;
}
```

#### 主要方法

- `initialize(callbacks)`: 初始化管理器並設置回調
- `start()`: 啟動實時更新
- `stop()`: 停止所有更新
- `pause()`: 暫停更新（保留連接）
- `resume()`: 恢復更新
- `triggerManualRefresh()`: 手動觸發數據刷新
- `getStats()`: 獲取統計信息
- `getCachedData()`: 獲取緩存的數據
- `destroy()`: 銷毀管理器並清理資源

### 組件

#### RealTimeMonitor

實時監控組件，顯示連接狀態和最後更新時間。

```typescript
<RealTimeMonitor
  showDetails={false}      // 是否顯示詳細信息
  compact={false}         // 緊湊模式
  className="custom-class"
/>
```

#### RefreshControl

手動刷新控制組件。

```typescript
<RefreshControl
  size="md"               // sm | md | lg
  variant="button"        // button | icon
  showText={true}         // 是否顯示文字
  onRefresh={handleRefresh}
/>
```

#### AutoRefreshToggle

自動刷新開關組件。

```typescript
<AutoRefreshToggle
  interval={10}           // 預設間隔（秒）
  onIntervalChange={setInterval}
/>
```

## 性能優化

### 1. 數據變更檢測

使用雜湊值檢測數據是否真的發生變更，避免不必要的 DOM 更新：

```typescript
// 自動計算數據雜湊值
const newDataHash = realtimeManager.calculateDataHash(strategies, performance);

// 只有在數據變更時才更新 UI
if (hasDataChanged(newDataHash)) {
  updateUI(strategies, performance);
}
```

### 2. 批量更新

將多個數據更新批量處理，減少重複渲染：

```typescript
// 實時管理器會自動批量處理 WebSocket 消息
// 避免每個策略更新都觸發一次 UI 更新
```

### 3. 緩存機制

```typescript
// 獲取緩存的數據，避免重複請求
const cachedData = realtimeManager.getCachedData();
const { strategies, performance } = cachedData;
```

## 錯誤處理

### 網路錯誤

```typescript
realtimeManager.initialize({
  onError: (error, context) => {
    switch (context) {
      case 'websocket':
        showNotification('WebSocket 連接失敗，嘗試重新連接...', 'warning');
        break;
      case 'data_sync':
        showNotification('數據同步失敗，將在稍後重試', 'error');
        break;
      case 'network':
        showNotification('網路連線中斷，請檢查您的網路', 'error');
        break;
    }
  }
});
```

### 重試策略

實時管理器使用指數退避算法進行重試：

- 第1次重試: 2秒後
- 第2次重試: 4秒後
- 第3次重試: 8秒後
- 依此類推，最大重試次數可配置

## 測試

運行測試以確保功能正常：

```bash
# 運行實時管理器測試
npm test -- realtimeManager.test.ts

# 運行所有相關測試
npm test -- --testPathPattern=realtime
```

## 故障排除

### 常見問題

1. **WebSocket 連接失敗**
   - 檢查 WebSocket 服務器是否運行
   - 確認 URL 格式正確（ws:// 或 wss://）
   - 檢查防火牆設置

2. **數據更新延遲**
   - 檢查網路連接品質
   - 調整更新間隔配置
   - 監控服務器響應時間

3. **頻繁斷線重連**
   - 檢查網路穩定性
   - 調整重試參數
   - 考慮增加心跳間隔

### 調試工具

```typescript
// 獲取詳細統計信息
const stats = realtimeManager.getStats();
console.log('統計信息:', stats);

// 監控網路狀態
console.log('網路狀態:', stats.networkStatus);

// 檢查緩存數據
const cachedData = realtimeManager.getCachedData();
console.log('緩存策略:', cachedData.strategies.length);
console.log('緩存性能:', cachedData.performance.length);
```

## 最佳實踐

1. **合理設置更新間隔**
   - 避免過於頻繁的更新（少於5秒）
   - 根據數據重要性調整頻率
   - 考慮用戶設備性能

2. **優雅的錯誤處理**
   - 提供明確的錯誤訊息
   - 實現自動恢復機制
   - 保留離線時的基本功能

3. **用戶體驗優化**
   - 使用骨架屏代替空白載入
   - 提供明確的狀態指示
   - 支援手動控制自動更新

4. **性能監控**
   - 監控同步延遲
   - 追蹤錯誤率
   - 優化重渲染頻率