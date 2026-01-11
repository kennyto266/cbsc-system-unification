# CBSC Dashboard Redux狀態管理架構

## 概述

本文檔描述了CBSC量化交易Dashboard的Redux狀態管理架構。該架構基於Redux Toolkit和RTK Query構建，提供了類型安全、高性能、可擴展的狀態管理解決方案。

## 架構特點

- **Redux Toolkit**: 使用現代化的Redux工具包，簡化Redux開發
- **TypeScript支持**: 完整的類型定義，提供類型安全的狀態管理
- **Redux Persist**: 自動狀態持久化，保持用戶會話
- **性能優化**: 使用Immer進行不可變更新，支持高效的重渲染
- **模塊化設計**: 清晰的文件結構和責任分離

## 文件結構

```
src/
├── store/
│   ├── index.ts              # Store配置和入口
│   ├── persistConfig.ts      # Redux持久化配置
│   ├── rootReducer.ts        # 根reducer（如果存在）
│   ├── middleware.ts         # 自定義中間件
│   ├── slices/               # Redux切片
│   │   ├── authSlice.ts      # 認證狀態
│   │   ├── strategiesSlice.ts # 策略狀態
│   │   ├── uiSlice.ts        # UI狀態
│   │   └── ...               # 其他切片
│   ├── api/                  # RTK Query API
│   └── store.test.ts         # 測試文件
├── providers/
│   └── ReduxProvider.tsx     # Redux提供者組件
├── hooks/
│   └── redux.ts              # Redux hooks
└── types/
    ├── auth.ts               # 認證類型
    ├── strategy.ts           # 策略類型
    ├── ui.ts                 # UI類型
    └── store.ts              # Store類型
```

## 核心切片

### 1. 認證切片 (authSlice)

管理用戶認證狀態，包括登錄、註冊、權限管理等。

**狀態結構:**
```typescript
interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  tokenExpiresAt: number | null
  permissions: Permission[]
  roles: Role[]
}
```

**主要操作:**
- `loginStart` / `loginSuccess` / `loginFailure` - 登錄流程
- `logout` - 登出
- `tokenRefreshed` - 刷新令牌
- `updateUser` - 更新用戶信息
- `updatePermissions` / `updateRoles` - 權限管理

### 2. 策略切片 (strategiesSlice)

管理交易策略的所有相關狀態，包括策略列表、執行狀態、回測結果等。

**狀態結構:**
```typescript
interface StrategiesState {
  items: Strategy[]
  selected: string | null
  editing: string | null
  loading: boolean
  error: string | null
  filters: StrategyFilters
  sorting: StrategySorting
  pagination: StrategyPagination
  execution: ExecutionState
  backtest: BacktestState
}
```

**主要操作:**
- `setStrategies` / `addStrategy` / `updateStrategy` / `deleteStrategy` - 策略CRUD
- `selectStrategy` / `startEditing` / `saveEditing` - 編輯狀態
- `setFilters` / `setSorting` / `setPagination` - 列表管理
- `setExecutionState` / `addExecutionLog` - 執行監控
- `startBacktest` / `completeBacktest` - 回測管理

### 3. UI切片 (uiSlice)

管理應用程序的UI狀態，包括主題、佈局、通知、模態框等。

**狀態結構:**
```typescript
interface UIState {
  theme: ThemeConfig
  layout: LayoutConfig
  screenSize: ScreenSize
  loading: LoadingState
  notifications: Notification[]
  navigation: NavigationState
  modals: ModalState
  preferences: UserPreferences
  systemStatus: SystemStatus
  // ... 其他UI相關狀態
}
```

**主要操作:**
- `setTheme` / `toggleTheme` - 主題管理
- `toggleSidebar` / `setScreenSize` - 佈局管理
- `addNotification` / `removeNotification` - 通知管理
- `openModal` / `closeModal` - 模態框管理
- `setLoading` / `setComponentLoading` - 加載狀態

## 使用指南

### 1. 在組件中使用

```tsx
import React from 'react'
import { useAppSelector, useAppDispatch } from '../hooks/redux'
import { selectUser, logout } from '../store/slices/authSlice'

const UserProfile = () => {
  const user = useAppSelector(selectUser)
  const dispatch = useAppDispatch()

  const handleLogout = () => {
    dispatch(logout())
  }

  return (
    <div>
      <h1>Welcome, {user?.username}</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  )
}
```

### 2. 使用ReduxProvider

```tsx
import React from 'react'
import { ReduxProvider } from '../providers/ReduxProvider'
import App from './App'

const Root = () => {
  return (
    <ReduxProvider>
      <App />
    </ReduxProvider>
  )
}
```

### 3. 使用RTK Query

```tsx
import { useGetStrategiesQuery, useCreateStrategyMutation } from '../store/api/strategiesApi'

const StrategyList = () => {
  const { data: strategies, isLoading, error } = useGetStrategiesQuery()
  const [createStrategy] = useCreateStrategyMutation()

  const handleCreate = async (strategy: Strategy) => {
    try {
      await createStrategy(strategy).unwrap()
    } catch (error) {
      console.error('Failed to create strategy:', error)
    }
  }

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading strategies</div>

  return (
    <div>
      {strategies?.map(strategy => (
        <div key={strategy.id}>{strategy.name}</div>
      ))}
    </div>
  )
}
```

## 最佳實踐

### 1. 狀態結構設計

- 保持狀態扁平化，避免深層嵌套
- 使用常規化數據結構管理集合
- 將相關狀態組織在同一個切片中

### 2. 動作設計

- 使用描述性的動作名稱
- 保持動作簡單且單一職責
- 使用類型安全的PayloadAction

### 3. 選擇器使用

- 使用選擇器從狀態中派生數據
- 創建可重用的選擇器
- 使用記憶化選擇器提高性能

```typescript
// 簡單選擇器
export const selectUser = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.user

// 記憶化選擇器
export const selectActiveStrategies = createSelector(
  [selectStrategies],
  (strategies) => strategies.filter(s => s.status === 'active')
)
```

### 4. 中間件使用

- 使用中間件處理橫切關注點
- 保持中間件簡單且專注
- 考慮中間件對性能的影響

### 5. 錯誤處理

- 在切片中集中處理錯誤
- 使用標準化的錯誤格式
- 提供用戶友好的錯誤消息

### 6. 性能優化

- 使用React.memo防止不必要的重渲染
- 使用useCallback和useMemo優化回調和計算
- 批處理相關的狀態更新

## 測試

### 1. 測試切片

```typescript
import authReducer, { loginSuccess, logout } from '../authSlice'
import { getMockAuthState } from '../store.test'

describe('Auth Slice', () => {
  it('should handle login success', () => {
    const mockUser = { id: '1', username: 'test', email: 'test@example.com' }
    const action = loginSuccess({ user: mockUser, token: 'test-token' })
    const state = authReducer(getMockAuthState(), action)

    expect(state.isAuthenticated).toBe(true)
    expect(state.user).toEqual(mockUser)
  })

  it('should handle logout', () => {
    const action = logout()
    const state = authReducer(getMockAuthState(), action)

    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBe(null)
  })
})
```

### 2. 測試組件

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { createTestStore } from '../store.test'
import { Provider } from 'react-redux'
import UserProfile from '../UserProfile'

test('should display user name and logout button', () => {
  const store = createTestStore({
    persisted: {
      auth: {
        user: { username: 'testuser' },
        isAuthenticated: true,
      },
    },
  })

  render(
    <Provider store={store}>
      <UserProfile />
    </Provider>
  )

  expect(screen.getByText('Welcome, testuser')).toBeInTheDocument()
  expect(screen.getByText('Logout')).toBeInTheDocument()
})
```

## 遷移指南

### 從舊版本遷移

1. **更新依賴項**:
   ```bash
   npm install @reduxjs/toolkit react-redux redux-persist
   ```

2. **重構Reducers**:
   - 將舊的reducer轉換為createSlice
   - 更新選擇器以使用新的狀態結構

3. **更新組件**:
   - 使用useAppSelector和useAppDispatch hooks
   - 更新狀態訪問模式

4. **添加持久化**:
   - 配置persistConfig
   - 更新store配置

## 故障排除

### 常見問題

1. **序列化檢查錯誤**:
   - 在configureStore中配置ignoredActions和ignoredPaths
   - 確保非序列化數據被正確忽略

2. **性能問題**:
   - 檢查是否有不必要的选择器重新計算
   - 使用React DevTools Profiler分析組件性能

3. **持久化問題**:
   - 檢查persistConfig的whitelist和blacklist
   - 確保狀態結構是可序列化的

### 調試工具

1. **Redux DevTools**:
   - 安裝瀏覽器擴展
   - 在configureStore中啟用devTools

2. **React Profiler**:
   - 使用React開發者工具分析性能
   - 識別不必要的重渲染

3. **日誌中間件**:
   - 在開發環境中啟用日誌
   - 監控狀態變化和動作

## 資源

- [Redux Toolkit文檔](https://redux-toolkit.js.org/)
- [React Redux文檔](https://react-redux.js.org/)
- [Redux Persist文檔](https://github.com/rt2zz/redux-persist)
- [RTK Query文檔](https://redux-toolkit.js.org/rtk-query/overview)