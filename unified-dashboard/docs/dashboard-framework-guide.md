# CBSC Dashboard Framework 使用指南

## 概述

本文檔介紹了為CBSC量化交易系統開發的現代化Dashboard框架。該框架提供了響應式設計、主題系統、實時數據連接等功能，無縫集成現有的CBSC後端服務。

## 核心特性

### 1. 響應式設計
- 移動端優先的設計理念
- 自適應佈局，支持手機、平板和桌面設備
- 可摺疊的側邊欄導航
- 靈活的網格系統

### 2. 主題系統
- 支持明亮和暗黑主題
- 自動檢測系統主題偏好
- 自定義顏色配置
- CSS變量驅動的設計令牌

### 3. 實時數據
- WebSocket自動重連機制
- 實時市場數據更新
- 策略執行狀態監控
- 系統警報通知

### 4. 組件化架構
- 可復用的UI組件
- 模塊化的頁面設計
- TypeScript類型安全
- 組件文檔和Storybook支持

## 快速開始

### 1. 安裝依賴

```bash
cd unified-dashboard
npm install
```

### 2. 啟動開發服務器

```bash
# 啟動前端開發服務器 (端口 3000)
npm run dev

# 啟動後端API服務器 (端口 3004)
cd ../src/api
python -m uvicorn main:app --reload --port 3004
```

### 3. 訪問Dashboard

打開瀏覽器訪問 `http://localhost:3000`

## 項目結構

```
unified-dashboard/
├── src/
│   ├── adapters/           # 系統適配器
│   │   └── CBSCAdapter.tsx # CBSC系統集成層
│   ├── components/         # UI組件
│   │   └── layout/        # 佈局組件
│   │       ├── DashboardLayout.tsx
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   ├── contexts/          # React Context
│   │   └── ThemeContext.tsx # 主題管理
│   ├── hooks/             # 自定義Hooks
│   │   ├── useWebSocket.ts
│   │   └── useWindowSize.ts
│   ├── pages/             # 頁面組件
│   │   └── dashboard/
│   │       ├── DashboardPage.tsx
│   │       └── NewDashboardPage.tsx
│   ├── router/            # 路由配置
│   │   └── index.tsx
│   ├── services/          # API服務
│   ├── store/             # 狀態管理
│   ├── types/             # TypeScript類型
│   ├── utils/             # 工具函數
│   ├── App.tsx            # 主應用組件
│   ├── App_new.tsx        # 新框架應用組件
│   └── main.tsx           # 應用入口
├── docs/                  # 文檔
└── package.json
```

## 核心組件使用

### 1. DashboardLayout

響應式佈局容器，提供側邊欄和頂部導航：

```tsx
import DashboardLayout from './components/layout/DashboardLayout'

function App() {
  return (
    <DashboardLayout>
      <div>
        {/* 頁面內容 */}
      </div>
    </DashboardLayout>
  )
}
```

### 2. 主題系統

使用ThemeContext管理主題：

```tsx
import { ThemeProvider, useTheme } from './contexts/ThemeContext'

function App() {
  return (
    <ThemeProvider defaultTheme="light">
      {/* 應用內容 */}
    </ThemeProvider>
  )
}

function Component() {
  const { theme, themeConfig, toggleTheme } = useTheme()

  return (
    <div style={{ background: themeConfig.colors.background }}>
      <button onClick={toggleTheme}>
        切換主題
      </button>
    </div>
  )
}
```

### 3. WebSocket集成

實時數據連接：

```tsx
import { useWebSocket } from './hooks/useWebSocket'

function Component() {
  const { isConnected, sendMessage, subscribe } = useWebSocket()

  useEffect(() => {
    if (isConnected) {
      subscribe('market_data', (data) => {
        console.log('市場數據更新:', data)
      })
    }
  }, [isConnected, subscribe])

  return (
    <div>
      連接狀態: {isConnected ? '已連接' : '未連接'}
    </div>
  )
}
```

### 4. CBSC系統適配器

與現有後端API集成：

```tsx
import cbscAdapter from './adapters/CBSCAdapter'

async function loadData() {
  try {
    // 獲取策略列表
    const strategies = await cbscAdapter.getStrategies()

    // 獲取投資組合數據
    const portfolio = await cbscAdapter.getPortfolio()

    // 獲取市場數據
    const marketData = await cbscAdapter.getMarketData(['BTC', 'ETH'])

    console.log('數據加載成功')
  } catch (error) {
    console.error('加載失敗:', error)
  }
}
```

## 自定義主題

通過修改 `ThemeContext.tsx` 中的主題配置：

```typescript
const customTheme: ThemeConfig = {
  colors: {
    primary: '#your-brand-color',
    secondary: '#your-secondary-color',
    // ... 其他顏色配置
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    // ... 其他間距配置
  },
  // ... 其他配置
}
```

## 添加新頁面

1. 在 `src/pages/` 下創建頁面組件
2. 在 `src/router/index.tsx` 中添加路由配置

```tsx
// 1. 創建頁面組件
const NewPage = lazy(() => import('../pages/NewPage'))

// 2. 添加路由
{
  path: 'new-page',
  element: (
    <Suspense fallback={<PageLoading />}>
      <NewPage />
    </Suspense>
  ),
},
```

## 性能優化建議

1. **代碼分割** - 使用 `React.lazy` 進行路由級別的代碼分割
2. **組件緩存** - 使用 `React.memo` 緩存純組件
3. **數據緩存** - 使用 React Query 的緩存機制
4. **圖片優化** - 使用合適的圖片格式和尺寸

## 故障排除

### WebSocket連接失敗
- 檢查後端服務是否運行在正確端口
- 確認防火牆設置
- 查看瀏覽器控制台的錯誤信息

### API請求失敗
- 檢查 `REACT_APP_API_URL` 環境變量配置
- 確認後端服務狀態
- 檢查網絡連接和CORS設置

### 主題切換不生效
- 確保組件在 `ThemeProvider` 內部
- 檢查CSS變量是否正確應用

## 後續開發計劃

1. **數據可視化** - 集成Chart.js和Plotly.js
2. **國際化** - 多語言支持
3. **離線功能** - PWA支持
4. **單元測試** - Jest和React Testing Library
5. **E2E測試** - Cypress支持

## 聯繫和支持

如有問題或建議，請通過以下方式聯繫：
- 提交GitHub Issue
- 發送郵件至開發團隊
- 查看項目Wiki了解更多信息