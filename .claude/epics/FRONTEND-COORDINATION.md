# 前端結構協調文檔

**創建時間**: 2025-12-25T02:30:00Z
**協調範圍**: system-unification #004 + project-refactoring-optimization #004

---

## 📊 當前狀態分析

### system-unification #004: UI Library (已完成 ✅)

**結構**: `frontend/src/components/`

```
frontend/src/components/
├── ui/                      # 60+ 基礎UI組件
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   ├── Modal.tsx
│   └── ...
├── Charts/                  # 20+ 圖表組件
│   ├── chartjs/            # Chart.js 組件
│   ├── plotly/             # Plotly.js 組件
│   └── ChartManager.tsx
├── StrategyDashboard/       # 策略儀表板組件
├── PersonalStrategy/        # 個人策略組件
├── StrategyClassification/  # 策略分類組件
└── RealTime/               # 實時監控組件
```

**特點**:
- ✅ 組件類型組織 (Component-based)
- ✅ 完整的 shadcn/ui 集成
- ✅ 豐富的圖表組件
- ✅ 業務組件模塊化

---

### project-refactoring-optimization #004: Frontend Structure (已完成 ✅)

**結構**: `frontend/src/features/`

```
frontend/src/
├── features/               # 功能模塊
│   ├── auth/              # 認證功能
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types.ts
│   ├── strategies/        # 策略管理
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── backtest/          # 回測功能
│   ├── realtime/          # 實時數據
│   ├── dashboard/         # 統一儀表板
│   └── settings/          # 設置
├── store/                 # Redux Store
│   ├── index.ts
│   ├── middleware.ts
│   └── slices/
├── services/api/          # RTK Query APIs
│   ├── baseApi.ts
│   ├── authApi.ts
│   └── strategiesApi.ts
└── components/ui/         # 可復用UI組件
```

**特點**:
- ✅ Feature-based 組織
- ✅ Redux Toolkit + RTK Query
- ✅ 完整的狀態管理
- ✅ 模塊化服務層

---

## 🎯 協調策略

### 統一架構 (混合模式)

```
frontend/src/
├── features/              # 保留 (Feature-based)
│   ├── auth/              # 新增
│   ├── strategies/        # 整合現有組件
│   ├── backtest/          # 新增
│   ├── realtime/          # 整合現有組件
│   ├── dashboard/         # 整合現有組件
│   └── settings/          # 新增
│
├── components/            # 保留 (可復用組件)
│   ├── ui/                # system-unification 的組件
│   ├── layouts/           # 佈局組件
│   └── shared/            # 共享組件
│
├── store/                 # 保留 (Redux Store)
│   ├── index.ts
│   ├── middleware.ts
│   └── slices/
│       ├── authSlice.ts
│       ├── strategiesSlice.ts
│       └── dashboardSlice.ts
│
├── services/              # 保留 (API服務)
│   ├── api/
│   │   ├── baseApi.ts
│   │   ├── authApi.ts
│   │   └── strategiesApi.ts
│   └── websocket/
│
├── hooks/                 # 保留 (自定義Hooks)
│   ├── useAuth.ts
│   ├── useStrategies.ts
│   └── useRealTimeData.ts
│
├── pages/                 # 新增 (頁面組件)
│   ├── Dashboard.tsx
│   ├── Strategies.tsx
│   └── Backtest.tsx
│
└── router/                # 新增 (路由配置)
    └── index.tsx
```

---

## 📋 整合步驟

### Phase 1: 組織現有組件 (1天)

#### 1.1 移動組件到 features/

```bash
# 策略儀表板組件
mv frontend/src/components/StrategyDashboard \
   frontend/src/features/strategies/components/Dashboard

# 個人策略組件
mv frontend/src/components/PersonalStrategy \
   frontend/src/features/strategies/components/Personal

# 實時監控組件
mv frontend/src/components/RealTime \
   frontend/src/features/realtime/components/

# 圖表演示
mv frontend/src/components/Charts/ChartsDemo.tsx \
   frontend/src/features/dashboard/components/
```

#### 1.2 更新導入路徑

```typescript
// Before
import { StrategyCard } from '../../components/StrategyDashboard';

// After
import { StrategyCard } from '@/features/strategies/components/Dashboard';
```

### Phase 2: 創建頁面層 (1天)

#### 2.1 創建頁面組件

```typescript
// frontend/src/pages/Dashboard.tsx
import { RealTimeDashboard } from '@/features/realtime';
import { StrategySummary } from '@/features/strategies';

export function DashboardPage() {
  return (
    <div className="dashboard-container">
      <StrategySummary />
      <RealTimeDashboard />
    </div>
  );
}
```

#### 2.2 配置路由

```typescript
// frontend/src/router/index.tsx
import { createBrowserRouter } from 'react-router-dom';
import { DashboardPage } from '@/pages/Dashboard';
import { StrategiesPage } from '@/pages/Strategies';
import { BacktestPage } from '@/pages/Backtest';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardPage />
  },
  {
    path: '/strategies',
    element: <StrategiesPage />
  },
  {
    path: '/backtest',
    element: <BacktestPage />
  }
]);
```

### Phase 3: 統一狀態管理 (1天)

#### 3.1 整合 Redux Slices

```typescript
// frontend/src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import strategiesReducer from './slices/strategiesSlice';
import dashboardReducer from './slices/dashboardSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    strategies: strategiesReducer,
    dashboard: dashboardReducer
  }
});
```

#### 3.2 整合 RTK Query APIs

```typescript
// frontend/src/services/api/baseApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:3004'
  }),
  tagTypes: ['Strategy', 'Backtest', 'User', 'Auth'],
  endpoints: () => ({})
});
```

---

## ✅ 驗收標準

### 完成標誌

- [ ] 組件正確組織到 features/
- [ ] 頁面組件創建完成
- [ ] 路由配置正確
- [ ] 所有導入路徑更新
- [ ] Redux Store 正常工作
- [ ] 應用可以正常啟動
- [ ] 所有組件測試通過

### 質量標準

- [ ] TypeScript 無錯誤
- [ ] ESLint 無警告
- [ ] 所有路由可訪問
- [ ] 組件可復用性良好
- [ ] 代碼結構清晰

---

## 📝 後續行動

### 立即執行

1. **創建 features 目錄結構**
2. **移動現有組件到對應 features**
3. **創建頁面組件**
4. **配置路由**
5. **更新所有導入路徑**

### 驗證步驟

1. `npm run type-check` - 檢查類型錯誤
2. `npm run lint` - 檢查代碼質量
3. `npm run build` - 檢查構建
4. `npm run dev` - 啟動開發服務器
5. 手動測試所有頁面

---

*協調文檔創建於 2025-12-25T02:30:00Z*
