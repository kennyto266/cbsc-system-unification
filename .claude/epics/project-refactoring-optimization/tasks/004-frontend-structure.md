---
name: frontend-structure
title: 新前端項目結構設置與組件遷移
status: completed
phase: 2
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-24T23:59:00Z
estimated_hours: 64
actual_hours: 32
progress: 100%
assignee: TBD
dependencies: ["003-dev-environment"]
github:
  issue: 76
  url: https://github.com/kennyto266/cbsc-system-unification/issues/76
---

# Task 004: 新前端項目結構設置與組件遷移

## 概述

創建統一的 React 前端項目結構,將 frontend/、unified-dashboard/、strategy-dashboard/ 合併為單一應用,使用 Feature-Based 組織方式。

## 執行進度

### 階段 1: 項目結構設置 (已完成) ✅

- ✅ 創建 Feature-based 目錄結構
- ✅ 更新 Vite 配置 (vite.config.ts, vitest.config.ts)
- ✅ 更新 TypeScript 配置 (tsconfig.json, tsconfig.src.json, tsconfig.test.json)
- ✅ 創建路由配置 (router/index.tsx)
- ✅ 創建 Redux Store 配置 (store/index.ts)
- ✅ 創建 API 服務架構
- ✅ 創建共享 UI 組件 (ProtectedRoute, PageLoading, DashboardLayout)
- ✅ 創建 API 類型定義

### 階段 2: 組件遷移 (已完成) ✅

- ✅ 遷移 StrategyControl 組件
  - StrategyToggleEnhanced.tsx
  - BatchOperationsPanel.tsx
  - StrategyControlDashboard.tsx
- ✅ 遷移 Charts 組件到 shared/components/charts/
  - PerformanceChart.tsx
  - RealTimeChart.tsx
  - ChartsDashboard.tsx
- ✅ 遷移 Layout 組件到 shared/components/layout/
  - Header.tsx
  - Sidebar.tsx

### 階段 3: 頁面實現 (已完成) ✅

- ✅ 實現 StrategyList 頁面
- ✅ 實現 StrategyDetail 頁面
- ✅ 實現 StrategyCreate 頁面
- ✅ 實現 BacktestList 頁面
- ✅ 實現 BacktestCreate 頁面
- ✅ 實現 BacktestReport 頁面
- ✅ 實現 DashboardPage 頁面
- ✅ 實現 LoginPage 頁面
- ✅ 實現 RealtimeDashboard 頁面

### 階段 4: Redux Slices 實現 (已完成) ✅

- ✅ authSlice - 登入/登出/Token 管理/刷新機制
- ✅ strategiesSlice - CRUD 操作/篩選/選擇狀態
- ✅ store 配置更新 - 整合所有 slices 和 APIs

### 階段 5: RTK Query APIs 實現 (已完成) ✅

- ✅ authApi - 登入/註冊/Token 刷新/MFA/用戶資料
- ✅ strategiesApi - 策略 CRUD/批次操作/績效查詢
- ✅ backtestApi - 回測 CRUD/狀態查詢/交易記錄/導出
- ✅ realtimeApi - 實時行情/交易信號/警報/關注清單
- ✅ services/index.ts - 統一導出所有 API

### 階段 6: 路由和入口更新 (已完成) ✅

- ✅ router/index.ts 更新 - 使用新的 Feature-based 組件路徑
- ✅ App.tsx 更新 - 使用 RouterProvider 和 Redux Provider
- ✅ main.tsx 更新 - 簡化入口配置

### 已創建文件統計

| 類別 | 文件數 | 主要內容 |
|------|--------|----------|
| **目錄結構** | 48 | features/, shared/, store/, app/ |
| **路由配置** | 2 | router/index.tsx, main.tsx |
| **Store 配置** | 7 | index.ts, 2 slices, 4 APIs, services index |
| **共享組件** | 8 | ProtectedRoute, PageLoading, DashboardLayout, Header, Sidebar, Charts |
| **策略組件** | 5 | StrategyControl 組件和類型 |
| **圖表組件** | 4 | Performance, RealTime, ChartsDashboard, types |
| **Layout 組件** | 2 | Header, Sidebar |
| **策略頁面** | 3 | StrategyList, StrategyDetail, StrategyCreate |
| **回測頁面** | 3 | BacktestList, BacktestCreate, BacktestReport |
| **實時頁面** | 1 | RealtimeDashboard |
| **認證頁面** | 1 | LoginPage |
| **儀表板頁面** | 1 | DashboardPage |
| **API 服務** | 5 | authApi, strategiesApi, backtestApi, realtimeApi, index |
| **類型定義** | 5 | API 類型, 策略類型, 圖表類型 |
| **總計** | 95+ | |

### 待完成工作 (已完成) ✅

1. **連接前端到後端 API** (P0) ✅
   - ✅ 配置環境變量 (VITE_API_BASE_URL, VITE_WS_BASE_URL)
   - ✅ 創建 API 配置中心 (src/config/api.ts)
   - ✅ 實現請求/響應攔截器 (baseQueryWithReauth)
   - ✅ 錯誤處理和重試機制

2. **測試和優化** (P1) ✅
   - ✅ 構建測試通過
   - ✅ 修復所有導入錯誤
   - ✅ 代碼分割和懶加載配置
   - ⏳ 組件單元測試 (後續任務)
   - ⏳ E2E 測試 (後續任務)

3. **部署準備** (P2)
   - ⏳ 生產環境配置
   - ⏳ Docker 鏡像構建
   - ⏳ CI/CD 配置

## 詳細描述

### 新項目結構

```
frontend/
├── src/
│   ├── main.tsx                 # 應用啟動點
│   ├── App.tsx                  # Redux Provider + RouterProvider
│   ├── router/                  # 路由配置
│   │   └── index.tsx            # 使用 createBrowserRouter + 懶加載
│   ├── features/                # 功能模塊
│   │   ├── strategies/          # 策略管理
│   │   │   ├── components/      # StrategyControl 組件
│   │   │   ├── pages/           # StrategyList, Detail, Create
│   │   │   ├── hooks/           # 策略 hooks
│   │   │   └── types/           # 策略類型
│   │   ├── backtest/            # 回測系統
│   │   │   └── pages/           # BacktestList, Create, Report
│   │   ├── realtime/            # 實時數據
│   │   │   └── pages/           # RealtimeDashboard
│   │   ├── dashboard/           # 統一儀表板
│   │   │   └── pages/           # DashboardPage
│   │   └── auth/                # 認證模塊
│   │       └── pages/           # LoginPage
│   ├── shared/                  # 共享資源
│   │   ├── components/
│   │   │   ├── ui/              # 基礎 UI 組件
│   │   │   ├── layout/          # Header, Sidebar, DashboardLayout
│   │   │   └── charts/          # Performance, RealTime, ChartsDashboard
│   │   ├── hooks/               # 共享 hooks
│   │   └── types/               # 共享類型
│   └── store/                   # Redux Store
│       ├── slices/              # authSlice, strategiesSlice
│       ├── services/            # RTK Query APIs (auth, strategies, backtest, realtime)
│       └── index.ts             # Store 配置
```

## 下一步工作

1. 連接前端到後端 API (移除 mock 數據)
2. 實現 WebSocket 實時數據連接
3. 測試和優化
4. 部署配置

## 驗收標準

### 交付物

- [x] **新項目結構**
  - Feature-based 目錄結構
  - 統一的 Vite 配置
  - TypeScript 配置優化

- [x] **遷移的組件**
  - 策略管理組件 (StrategyControl)
  - 圖表組件 (Charts)
  - 佈局組件 (Layout)

- [x] **路由配置**
  - 統一的路由定義
  - 懶加載配置
  - 保護路由實現

- [x] **狀態管理**
  - 統一的 Redux Store
  - RTK Query API 配置
  - 類型安全的 hooks

- [x] **頁面實現**
  - 策略管理頁面 (列表/詳情/創建)
  - 回測頁面 (列表/創建/報告)
  - 實時數據頁面
  - 儀表板頁面
  - 登入頁面

- [x] **API 集成**
  - 後端 API 連接 ✅
  - 環境變量配置 ✅
  - 錯誤處理機制 ✅
  - Token 刷新機制 ✅

### 質量門檻

- 所有現有功能可訪問
- 無控制台錯誤
- TypeScript 編譯通過
- ESLint 檢查通過
- API 調用正常

## 技術實現

### 已實現的 Redux Slices

1. **authSlice** (`store/slices/authSlice.ts`)
   - login/createAsyncThunk - 用戶登入
   - logout/createAsyncThunk - 用戶登出
   - refreshToken/createAsyncThunk - Token 刷新
   - Token 持久化到 localStorage

2. **strategiesSlice** (`store/slices/strategiesSlice.ts`)
   - fetchStrategies/createAsyncThunk - 獲取策略列表
   - createStrategy/createAsyncThunk - 創建策略
   - updateStrategy/createAsyncThunk - 更新策略
   - deleteStrategy/createAsyncThunk - 刪除策略
   - 篩選和選擇狀態管理

### 已實現的 RTK Query APIs

1. **authApi** - 完整的認證 API
   - login, register, logout, refreshToken
   - getCurrentUser, updateProfile, changePassword
   - MFA: setupMfa, verifyMfa, disableMfa
   - 密碼重置: requestPasswordReset, confirmPasswordReset
   - 郵箱驗證: verifyEmail, resendVerificationEmail

2. **strategiesApi** - 策略管理 API
   - getStrategies, getStrategyById
   - createStrategy, updateStrategy, deleteStrategy
   - toggleStrategy - 開關策略
   - batchControlStrategies - 批量操作
   - getStrategyCategories, getStrategyPerformance

3. **backtestApi** - 回測管理 API
   - getBacktests, getBacktestById
   - createBacktest, startBacktest, stopBacktest
   - deleteBacktest
   - getBacktestStatus, getBacktestTrades, getBacktestEquityCurve
   - compareBacktests - 比較回測
   - getBacktestTemplates, createBacktestTemplate
   - exportBacktestReport - 導出報告

4. **realtimeApi** - 實時數據 API
   - getMarketData, getQuote, getOHLCV
   - getTradingSignals, executeSignal, cancelSignal
   - getWebSocketStatus, getSubscriptions
   - subscribeMarketData, subscribeSignals, unsubscribe
   - getAlerts, markAlertRead, createPriceAlert
   - getWatchlist, addToWatchlist, removeFromWatchlist

## 完成總結 (2025-12-24)

### API 集成完成
1. **環境配置**
   - 創建 `.env.development` 和 `.env.production`
   - 配置 API base URLs 和 feature flags

2. **API 配置中心**
   - 創建 `src/config/api.ts` 統一管理 API 配置
   - 實現 `getAuthToken`, `setAuthToken`, `getRefreshToken`, `setAuthTokens`, `removeAuthToken` 工具函數
   - 實現 `buildApiUrl`, `getDefaultHeaders` 等工具函數

3. **BaseQuery 配置**
   - 更新 `src/api/baseQuery.ts` 使用集中式配置
   - 實現 `baseQueryWithReauth` 支持自動 Token 刷新
   - 配置請求/響應攔截器

4. **構建修復**
   - 修復所有 Button 組件導入錯誤 (6 個文件)
   - 修復 NotFound 頁面缺失
   - 修復 LoginPage 路由導入
   - 構建成功 ✅

### 構建結果
```
✓ 5627 modules transformed.
✓ built in 13.21s

主要輸出:
- index.html: 1.05 kB
- CSS: 169.28 kB (gzip: 25.34 kB)
- JS: 1,456.51 kB (gzip: 427.08 kB)

代碼分割:
- react-vendor: 202.89 kB
- antd-vendor: 691.09 kB
- chart-vendor: 391.67 kB
- 頁面級別 chunk: StrategyList (51.61 kB) 等
```

### 待後續處理
- 組件單元測試
- E2E 測試
- 生產環境部署配置
