# CBSC 前端項目結構文檔

## 概述

本文檔描述了 CBSC 量化交易系統的統一前端項目結構。該結構採用 **Feature-Based** 組織方式，將多個前端項目合併為單一應用。

## 項目結構

```
frontend/
├── src/
│   ├── app/                          # 應用入口
│   │   ├── main.tsx                  # 應用啟動點
│   │   └── router.tsx                # 路由配置 (懶加載)
│   ├── features/                     # 功能模塊 (Feature-based)
│   │   ├── strategies/               # 策略管理
│   │   │   ├── components/          # 策略相關組件
│   │   │   ├── pages/               # 策略頁面
│   │   │   ├── hooks/               # 策略 hooks
│   │   │   ├── services/            # 策略 API
│   │   │   └── types/               # 策略類型
│   │   ├── backtest/                 # 回測系統
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── realtime/                 # 實時數據
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── dashboard/                # 統一儀表板
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   └── widgets/             # 儀表板小部件
│   │   └── auth/                     # 認證模塊
│   │       ├── pages/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── services/
│   ├── shared/                       # 共享資源
│   │   ├── components/
│   │   │   ├── ui/                  # 基礎 UI 組件
│   │   │   │   ├── ProtectedRoute.tsx
│   │   │   │   └── PageLoading.tsx
│   │   │   ├── layout/              # 佈局組件
│   │   │   │   └── DashboardLayout.tsx
│   │   │   ├── charts/              # 圖表組件
│   │   │   └── forms/               # 表單組件
│   │   ├── hooks/                   # 共享 hooks
│   │   ├── services/                # API 服務
│   │   │   ├── api.ts               # 統一 API 配置
│   │   │   └── baseQuery.ts         # Base query with re-auth
│   │   ├── utils/                   # 工具函數
│   │   ├── types/                   # 共享類型
│   │   │   └── api.ts               # API 類型定義
│   │   └── config/                  # 配置
│   ├── store/                        # Redux Store
│   │   ├── slices/                  # Redux slices
│   │   ├── services/                # RTK Query APIs
│   │   ├── middleware/              # 自定義中間件
│   │   └── index.ts                 # Store 配置
│   └── styles/                      # 樣式文件
├── public/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## 路由配置

### 主路由 (`src/app/router.tsx`)

```
/                    → DashboardPage (儀表板)
/strategies         → StrategyList (策略列表)
/strategies/:id     → StrategyDetail (策略詳情)
/strategies/new     → StrategyCreate (創建策略)
/backtest           → BacktestList (回測列表)
/backtest/new       → BacktestCreate (創建回測)
/backtest/:id       → BacktestReport (回測報告)
/realtime           → RealtimeDashboard (實時數據)
/login              → LoginPage (登入頁面)
```

### 懶加載

所有頁面都使用 React.lazy() 進行代碼分割，實現按需加載。

## Redux Store 結構

### Slices

- `authSlice` - 認證狀態 (token, user)
- `strategiesSlice` - 策略列表和選中狀態
- `backtestSlice` - 回測狀態
- `realtimeSlice` - 實時數據緩存
- `dashboardSlice` - 儀表板統計數據

### RTK Query APIs

- `authApi` - 認證 API
- `strategiesApi` - 策略管理 API
- `backtestApi` - 回測 API
- `realtimeApi` - 實時數據 API
- `marketDataApi` - 市場數據 API

## API 服務架構

### Base Query (`src/shared/services/baseQuery.ts`)

- 自動添加 Authorization header
- 401 錯誤自動 token 刷新
- 刷新失敗自動跳轉登入

### 類型定義 (`src/shared/types/api.ts`)

- `ApiResponse<T>` - 通用 API 響應包裝
- `PaginatedResponse<T>` - 分頁響應
- `Strategy`, `Backtest`, `RealtimeQuote` - 領域實體類型

## 遷移狀態

### 已完成

| 模塊 | 狀態 | 說明 |
|------|------|------|
| 目錄結構 | ✅ | Feature-based 目錄已創建 |
| 路由配置 | ✅ | router.tsx 已實現 |
| Store 配置 | ✅ | store/index.ts 已創建 |
| 基礎組件 | ✅ | ProtectedRoute, PageLoading, DashboardLayout |
| API 服務 | ✅ | baseQuery, 類型定義 |
| 佔位文件 | ✅ | slices, APIs, pages |

### 待遷移

| 源項目 | 目標位置 | 狀態 |
|--------|----------|------|
| `frontend/src/components/StrategyControl/*` | `features/strategies/components/` | 待遷移 |
| `frontend/src/components/Charts/*` | `shared/components/charts/` | 待遷移 |
| `frontend/src/pages/*` | `features/*/pages/` | 待遷移 |
| `unified-dashboard/src/App-complex.tsx` | `features/dashboard/pages/` | 待遷移 |
| `strategy-dashboard/*` | `features/strategies/*` | 待遷移 |

## 下一步工作

1. **組件遷移** (優先級: P0)
   - 遷移策略管理組件
   - 遷移圖表組件
   - 遷移佈局組件

2. **頁面實現** (優先級: P0)
   - DashboardPage
   - StrategyList, StrategyDetail, StrategyCreate
   - BacktestList, BacktestCreate, BacktestReport
   - RealtimeDashboard
   - LoginPage

3. **Slice 實現** (優先級: P1)
   - authSlice with token management
   - strategiesSlice with CRUD operations
   - 其他 slices

4. **API 服務實現** (優先級: P1)
   - strategiesApi with RTK Query
   - backtestApi
   - realtimeApi with WebSocket

5. **測試** (優先級: P1)
   - 單元測試
   - 集成測試
   - E2E 測試

---

*創建時間: 2025-12-24*
*版本: 1.0*
