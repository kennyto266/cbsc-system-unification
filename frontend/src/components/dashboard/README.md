# Unified Dashboard 組件文檔

## 概述

Unified Dashboard 是 CBSC 量化交易系統的主要儀表板組件，提供統一的界面來監控策略、查看性能指標和管理交易活動。

## 組件結構

```
frontend/src/components/Dashboard/
├── UnifiedDashboard.tsx        # 主儀表板組件
├── UnifiedDashboard.css        # 樣式文件
├── index.ts                    # 導出文件
└── __tests__/                  # 測試文件
    └── UnifiedDashboard.test.tsx

frontend/src/components/Monitoring/
├── RealTimeMonitor.tsx         # 實時監控組件
├── RealTimeMonitor.css         # 樣式文件
└── index.ts                    # 導出文件

frontend/src/pages/UnifiedDashboard/
├── UnifiedDashboardPage.tsx    # 頁面組件
├── UnifiedDashboardPage.css    # 樣式文件
└── index.ts                    # 導出文件
```

## 主要功能

### 1. UnifiedDashboard 組件

**功能：**
- 顯示關鍵統計數據（總策略數、收益率、勝率、最大回撤）
- 性能走勢圖表
- 策略分佈餅圖
- 頂級策略列表
- 最近通知
- 系統健康狀態

**使用示例：**
```tsx
import { UnifiedDashboard } from '@/components/Dashboard/UnifiedDashboard';

function MyPage() {
  const handleStrategyClick = (strategyId: string) => {
    console.log('Selected strategy:', strategyId);
  };

  return (
    <UnifiedDashboard
      onStrategyClick={handleStrategyClick}
      className="custom-dashboard"
    />
  );
}
```

**Props：**
```typescript
interface UnifiedDashboardProps {
  className?: string;              // 自定義樣式類名
  onStrategyClick?: (strategyId: string) => void;  // 策略點擊回調
  onFullscreen?: () => void;       // 全屏回調
}
```

### 2. RealTimeMonitor 組件

**功能：**
- 實時價格更新
- 交易活動監控
- WebSocket 連接狀態
- 價格走勢圖表
- 活動篩選

**使用示例：**
```tsx
import { RealTimeMonitor } from '@/components/Monitoring/RealTimeMonitor';

function MonitorPage() {
  return (
    <RealTimeMonitor
      symbols={['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']}
      maxDataPoints={100}
      className="custom-monitor"
    />
  );
}
```

**Props：**
```typescript
interface RealTimeMonitorProps {
  className?: string;              // 自定義樣式類名
  symbols?: string[];              // 監控的股票代碼
  maxDataPoints?: number;          // 最大數據點數
}
```

### 3. UnifiedDashboardPage 組件

**功能：**
- 集成所有 Dashboard 組件
- 選項卡導航（總覽、實時監控、性能分析、設置）
- 全屏模式支持

**使用示例：**
```tsx
import { UnifiedDashboardPage } from '@/pages/UnifiedDashboard';

function App() {
  return (
    <Router>
      <Route path="/dashboard" element={<UnifiedDashboardPage />} />
    </Router>
  );
}
```

## Redux 狀態管理

### Dashboard Slice

**狀態結構：**
```typescript
interface DashboardState {
  stats: DashboardStats | null;        // 統計數據
  health: SystemHealth | null;         // 系統健康
  performanceData: PerformanceData | null;  // 性能數據
  alerts: Alert[];                     // 通知列表
  isLoading: boolean;                  // 加載狀態
  isRefreshing: boolean;               // 刷新狀態
  error: string | null;                // 錯誤信息
  preferences: DashboardPreferences;   // 用戶偏好
}
```

**Actions：**
```typescript
import {
  fetchDashboardStats,
  fetchSystemHealth,
  fetchPerformanceData,
  fetchRecentAlerts,
  refreshDashboard,
  setTimeRange,
  toggleAutoRefresh,
  setRefreshInterval,
} from '@/store/slices/dashboardSlice';

// 使用示例
dispatch(fetchDashboardStats());
dispatch(setTimeRange('1M'));
dispatch(toggleAutoRefresh());
```

**Selectors：**
```typescript
import {
  selectDashboardStats,
  selectSystemHealth,
  selectAlerts,
  selectDashboardLoading,
  selectDashboardPreferences,
} from '@/store/slices/dashboardSlice';

// 使用示例
const stats = useAppSelector(selectDashboardStats);
const isLoading = useAppSelector(selectDashboardLoading);
```

## 自定義 Hooks

### useDashboardData

管理 Dashboard 數據的獲取和更新。

```typescript
import { useDashboardData } from '@/hooks/useDashboardData';

function MyComponent() {
  const {
    stats,
    health,
    performanceData,
    alerts,
    isLoading,
    error,
    preferences,
    setTimeRange,
    toggleAutoRefresh,
    refresh,
  } = useDashboardData('1M');

  return (
    <div>
      {/* 使用數據渲染 UI */}
    </div>
  );
}
```

### useRealTimeData

管理實時數據訂閱。

```typescript
import { useRealTimeData } from '@/hooks/useRealTimeData';

function MyComponent() {
  const {
    realTimePrices,
    notifications,
    subscribeToPrices,
    subscribeToNotifications,
    isConnected,
  } = useRealTimeData();

  useEffect(() => {
    const unsubscribe = subscribeToPrices((data) => {
      console.log('Price update:', data);
    });

    return () => unsubscribe();
  }, [subscribeToPrices]);

  return (
    <div>
      {/* 使用實時數據 */}
    </div>
  );
}
```

## WebSocket 集成

Dashboard 組件使用 `wsManager` 進行實時數據更新：

```typescript
import { wsManager } from '@/services/websocketManager';

// 訂閱價格更新
const unsubscribePrices = wsManager.subscribe('price_update', (data) => {
  console.log('Price update:', data);
});

// 訂閱交易信號
const unsubscribeSignals = wsManager.subscribe('trading_signal', (data) => {
  console.log('New signal:', data);
});

// 清理
unsubscribePrices();
unsubscribeSignals();
```

## API 集成

Dashboard 使用以下 API 端點：

```
GET  /api/dashboard/stats          # 獲取統計數據
GET  /api/dashboard/performance    # 獲取性能數據
GET  /api/health                   # 獲取系統健康
GET  /api/alerts/recent            # 獲取最近通知
GET  /api/strategies               # 獲取策略列表
GET  /api/market/prices            # 獲取市場價格
GET  /api/dashboard/export         # 導出儀表板數據
GET  /api/monitoring/export        # 導出監控數據
```

## 樣式自定義

### CSS 變量

```css
:root {
  --dashboard-bg: #f8fafc;
  --stat-card-bg: #ffffff;
  --chart-card-bg: #ffffff;
  --primary-color: #3b82f6;
  --success-color: #22c55e;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
}
```

### 暗色模式

```css
.dark {
  --dashboard-bg: #0f172a;
  --stat-card-bg: rgba(30, 41, 59, 0.8);
  --chart-card-bg: rgba(30, 41, 59, 0.8);
}
```

## 響應式設計

Dashboard 支持以下斷點：

```css
/* 手機 */
@media (max-width: 640px) { }

/* 平板 */
@media (min-width: 641px) and (max-width: 1024px) { }

/* 桌面 */
@media (min-width: 1025px) { }
```

## 性能優化

1. **數據緩存**：使用 Redux 進行數據緩存
2. **懶加載**：使用 React.lazy 進行組件懶加載
3. **虛擬化**：大型列表使用虛擬化
4. **防抖**：搜索和篩選使用防抖
5. **Throttle**：滾動事件使用 Throttle

## 測試

運行測試：

```bash
npm run test
```

運行特定測試：

```bash
npm run test -- UnifiedDashboard
```

## 故障排除

### Dashboard 不顯示數據

1. 檢查 API 連接
2. 檢查 Redux 狀態
3. 檢查 WebSocket 連接
4. 查看瀏覽器控制台錯誤

### 圖表不渲染

1. 檢查 Chart.js 是否正確註冊
2. 檢查數據格式
3. 檢查容器高度

### WebSocket 連接失敗

1. 檢查 WebSocket 服務器是否運行
2. 檢查防火牆設置
3. 檢查代理配置

## 未來改進

- [ ] 添加更多圖表類型
- [ ] 支持自定義布局
- [ ] 添加拖拽功能
- [ ] 支持多語言
- [ ] 添加離線模式
- [ ] 優化性能

## 貢獻指南

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 推送到分支
5. 創建 Pull Request

## 許可證

MIT License
