# CBSC API Integration層文檔

## 概述

本文檔描述了CBSC量化交易系統的API集成層實現，基於RTK Query和Redux Toolkit構建，提供統一的API調用、狀態管理和WebSocket實時通信。

## 架構

### 核心組件

1. **API Services** (`src/store/services/`)
   - `authApi.ts` - 認證相關API
   - `strategyApi.ts` - 策略管理API
   - `userApi.ts` - 用戶管理API
   - `dashboardApi.ts` - 儀表板API
   - `marketDataApi.ts` - 市場數據API
   - `index.ts` - 統一導出

2. **Base Query** (`src/api/baseQuery.ts`)
   - 統一的請求配置
   - 認證頭部注入
   - 錯誤處理和重試機制
   - 響應轉換

3. **WebSocket集成** (`src/api/endpoints/realtimeApi.ts`)
   - WebSocket連接管理
   - 實時數據推送
   - 自動重連機制
   - 心跳保活

4. **工具函數** (`src/utils/`)
   - `apiHelpers.ts` - API輔助函數
   - `errorHandling.ts` - 錯誤處理工具

5. **自定義Hooks** (`src/hooks/`)
   - `useWebSocketIntegration.ts` - WebSocket集成Hook
   - 各種特定功能的Hook

## 快速開始

### 1. 安裝依賴

```bash
npm install @reduxjs/toolkit react-redux
```

### 2. 配置Store

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import {
  authApi,
  strategyApi,
  userApi,
  dashboardApi,
  marketDataApi,
  realtimeApi
} from './services';

export const store = configureStore({
  reducer: {
    // 你的 reducers
    [authApi.reducerPath]: authApi.reducer,
    [strategyApi.reducerPath]: strategyApi.reducer,
    [userApi.reducerPath]: userApi.reducer,
    [dashboardApi.reducerPath]: dashboardApi.reducer,
    [marketDataApi.reducerPath]: marketDataApi.reducer,
    [realtimeApi.reducerPath]: realtimeApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      authApi.middleware,
      strategyApi.middleware,
      userApi.middleware,
      dashboardApi.middleware,
      marketDataApi.middleware,
      realtimeApi.middleware
    ),
});
```

### 3. 在組件中使用

```typescript
import React from 'react';
import {
  useLoginMutation,
  useGetStrategiesQuery,
  useStrategyWebSocketIntegration,
} from '../store';

const MyComponent = () => {
  // 登錄
  const [login] = useLoginMutation();

  // 獲取策略列表
  const { data: strategies, isLoading } = useGetStrategiesQuery({
    status: 'active',
    page: 1,
  });

  // 實時策略更新
  const { executionUpdates, isConnected } = useStrategyWebSocketIntegration('strategy-id');

  const handleLogin = async () => {
    await login({
      email: 'user@example.com',
      password: 'password',
    }).unwrap();
  };

  return (
    <div>
      <button onClick={handleLogin}>Login</button>
      {isLoading ? <p>Loading...</p> : (
        <ul>
          {strategies?.map(strategy => (
            <li key={strategy.id}>{strategy.name}</li>
          ))}
        </ul>
      )}
      <p>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</p>
    </div>
  );
};
```

## API服務詳解

### 認證API (authApi)

```typescript
import { useLoginMutation, useAuthState } from '../store';

const LoginComponent = () => {
  const [login] = useLoginMutation();
  const { isAuthenticated, user } = useAuthState();

  const handleLogin = async (credentials) => {
    try {
      await login(credentials).unwrap();
      // 登錄成功
    } catch (error) {
      // 處理錯誤
    }
  };

  return (
    // JSX
  );
};
```

### 策略API (strategyApi)

```typescript
import {
  useGetStrategiesQuery,
  useCreateStrategyMutation,
  useStrategiesWithFilters
} from '../store';

const StrategyComponent = () => {
  // 基礎查詢
  const { data, isLoading } = useGetStrategiesQuery({
    page: 1,
    pageSize: 20,
  });

  // 使用過濾器
  const { strategies, total } = useStrategiesWithFilters({
    category: 'trend_following',
    riskLevel: 'medium',
  });

  // 創建策略
  const [createStrategy] = useCreateStrategyMutation();

  return (
    // JSX
  );
};
```

### 市場數據API (marketDataApi)

```typescript
import {
  useMarketData,
  useGetMarketOverviewQuery,
  useGetOHLCQuery
} from '../store';

const MarketComponent = () => {
  // 獲取市場概覽
  const { data: overview } = useGetMarketOverviewQuery();

  // 獲取特定股票數據
  const { instrument, ticker, technical } = useMarketData('AAPL');

  // 獲取K線數據
  const { data: ohlc } = useGetOHLCQuery({
    symbol: 'AAPL',
    interval: '1d',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
  });

  return (
    // JSX
  );
};
```

### 儀表板API (dashboardApi)

```typescript
import {
  useDashboardManagement,
  useCBSCDashboard
} from '../store';

const DashboardComponent = () => {
  // 儀表板管理
  const { config, widgets, layout } = useDashboardManagement();

  // CBSC特定功能
  const {
    tokenStatus,
    systemStatus,
    strategies,
    alerts
  } = useCBSCDashboard();

  return (
    // JSX
  );
};
```

## WebSocket集成

### 基礎WebSocket使用

```typescript
import { useWebSocketIntegration } from '../hooks/useWebSocketIntegration';

const WebSocketComponent = () => {
  const ws = useWebSocketIntegration({
    autoConnect: true,
    subscriptions: {
      notifications: true,
    },
  });

  useEffect(() => {
    // 訂閱特定消息
    const unsubscribe = ws.subscribe('notification', (data) => {
      console.log('收到通知:', data);
    });

    return unsubscribe;
  }, [ws.subscribe]);

  const sendMessage = () => {
    ws.send({
      type: 'custom_message',
      data: { hello: 'world' },
    });
  };

  return (
    <div>
      <p>狀態: {ws.isConnected ? '已連接' : '未連接'}</p>
      <button onClick={sendMessage}>發送消息</button>
    </div>
  );
};
```

### 策略實時更新

```typescript
import { useStrategyWebSocketIntegration } from '../hooks/useWebSocketIntegration';

const StrategyRealtimeComponent = ({ strategyId }) => {
  const {
    executionUpdates,
    signals,
    performance,
    isConnected
  } = useStrategyWebSocketIntegration(strategyId);

  return (
    <div>
      <h3>執行更新</h3>
      <ul>
        {executionUpdates.map(update => (
          <li key={update.id}>{update.message}</li>
        ))}
      </ul>

      <h3>信號</h3>
      <ul>
        {signals.map(signal => (
          <li key={signal.id}>
            {signal.type}: {signal.symbol} @ {signal.price}
          </li>
        ))}
      </ul>

      <h3>性能指標</h3>
      {performance && (
        <div>
          <p>總回報: {performance.totalReturn}%</p>
          <p>夏普比率: {performance.sharpeRatio}</p>
        </div>
      )}
    </div>
  );
};
```

## 錯誤處理

### 使用全局錯誤處理

```typescript
import { globalErrorHandler, ErrorSeverity } from '../utils/errorHandling';

// 添加自定義錯誤處理器
globalErrorHandler.addHandler((error) => {
  if (error.severity === ErrorSeverity.CRITICAL) {
    // 處理嚴重錯誤
    alert('發生嚴重錯誤，請刷新頁面');
  }
});

// 在組件中處理錯誤
const MyComponent = () => {
  const [mutation] = useSomeMutation();

  const handleSubmit = async () => {
    try {
      await mutation().unwrap();
    } catch (error) {
      // 錯誤會自動被全局處理器捕獲
      console.error('操作失敗:', error);
    }
  };
};
```

### API錯誤分類

```typescript
import {
  isNetworkError,
  isAuthError,
  isValidationError,
  getErrorMessage
} from '../utils/apiHelpers';

const ErrorComponent = ({ error }) => {
  let errorMessage = getErrorMessage(error);

  if (isNetworkError(error)) {
    errorMessage = '網絡連接錯誤，請檢查網絡設置';
  } else if (isAuthError(error)) {
    errorMessage = '請重新登錄';
  } else if (isValidationError(error)) {
    errorMessage = '輸入數據有誤，請檢查後重試';
  }

  return <div className="error">{errorMessage}</div>;
};
```

## 最佳實踐

### 1. 緩存策略

```typescript
// 使用標籤緩存失效
export const strategyApi = createApi({
  // ...
  tagTypes: ['Strategy', 'Execution'],
  endpoints: (builder) => ({
    getStrategies: builder.query({
      query: (params) => ({ url: '/strategies', params }),
      providesTags: ['Strategy'], // 緩存標籤
    }),
    createStrategy: builder.mutation({
      query: (strategy) => ({
        url: '/strategies',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: ['Strategy'], // 失效緩存
    }),
  }),
});
```

### 2. 條件查詢

```typescript
// 僅在認證後查詢
const { data } = useGetCurrentUserQuery(undefined, {
  skip: !isAuthenticated,
});

// 基於其他查詢結果的條件查詢
const { data: strategy } = useGetStrategyQuery(strategyId, {
  skip: !strategyId,
});
```

### 3. 樂觀更新

```typescript
const [updateStrategy] = useUpdateStrategyMutation({
  onQueryStarted: async ({ id, data }, { dispatch, queryFulfilled }) => {
    // 樂觀更新
    const patchResult = dispatch(
      strategyApi.util.updateQueryData('getStrategy', id, (draft) => {
        Object.assign(draft, data);
      })
    );

    try {
      await queryFulfilled;
    } catch {
      // 回滾樂觀更新
      patchResult.undo();
    }
  },
});
```

### 4. 預加載數據

```typescript
// 在用戶交互前預加載
const preloadStrategy = (strategyId: string) => {
  store.dispatch(
    strategyApi.util.prefetch('getStrategy', strategyId, { force: true })
  );
};

// 在hover時預加載
<button
  onMouseEnter={() => preloadStrategy(strategy.id)}
  onClick={() => setSelectedStrategy(strategy.id)}
>
  {strategy.name}
</button>
```

### 5. WebSocket重連策略

```typescript
const ws = useWebSocketIntegration({
  autoConnect: true,
  subscriptions: {
    strategies: activeStrategyIds,
  },
  onMessage: (message) => {
    // 處理消息
    handleWebSocketMessage(message);
  },
});

// 在網絡恢復時重新連接
useEffect(() => {
  const handleOnline = () => {
    if (!ws.isConnected) {
      ws.connect();
    }
  };

  window.addEventListener('online', handleOnline);
  return () => window.removeEventListener('online', handleOnline);
}, [ws]);
```

## 性能優化

### 1. 選擇性訂閱

```typescript
// 只訂閱需要的數據
const { data: user } = useGetCurrentUserQuery(undefined, {
  selectFromResult: ({ data, isLoading }) => ({
    name: data?.name,
    email: data?.email,
    isLoading,
  }),
});
```

### 2. 分頁和無限滾動

```typescript
const {
  data,
  isLoading,
  isFetching,
  hasNextPage,
} = useGetStrategiesQuery({
  page: currentPage,
  pageSize: 20,
});

const loadMore = () => {
  if (hasNextPage && !isFetching) {
    setCurrentPage(prev => prev + 1);
  }
};
```

### 3. 防抖搜索

```typescript
const debouncedSearch = useMemo(
  () => debounce((searchTerm: string) => {
    setFilters({ ...filters, search: searchTerm });
  }, 300),
  [filters]
);
```

## 測試

### 測試API組件

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../store';
import { useGetStrategiesQuery } from '../store/services/strategyApi';

const wrapper = ({ children }) => (
  <Provider store={store}>{children}</Provider>
);

test('should fetch strategies', async () => {
  const { result } = renderHook(() => useGetStrategiesQuery(), {
    wrapper,
  });

  expect(result.current.isLoading).toBe(true);

  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeDefined();
  });
});
```

### Mock API

```typescript
// 測試設置
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  rest.get('/api/strategies', (req, res, ctx) => {
    return res(
      ctx.json({
        strategies: [{ id: '1', name: 'Test Strategy' }],
        total: 1,
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## 故障排除

### 常見問題

1. **WebSocket連接失敗**
   - 檢查後端WebSocket服務是否運行
   - 確認token是否有效
   - 檢查網絡連接

2. **API請求401錯誤**
   - Token可能已過期，嘗試刷新
   - 檢查token是否正確存儲

3. **緩存問題**
   - 使用`dispatch(api.util.resetApiState())`重置
   - 檢查標籤配置是否正確

4. **性能問題**
   - 檢查是否過度獲取數據
   - 使用`selectFromResult`優化
   - 考慮使用`keepUnusedDataFor`調整

### 調試技巧

```typescript
// 開啟Redux DevTools
const store = configureStore({
  // ...
  devTools: process.env.NODE_ENV !== 'production',
});

// 添加中間件日誌
import { logger } from 'redux-logger';

// 在開發環境使用
if (process.env.NODE_ENV === 'development') {
  store.addEnhancer(logger);
}

// RTK Query調試
import { focus, prepareHeaders } from '@reduxjs/toolkit/query/react';

// 在baseQuery中添加日誌
export const baseQueryWithLogger = async (args, api, extraOptions) => {
  console.log('API Request:', args);
  const result = await baseQuery(args, api, extraOptions);
  console.log('API Response:', result);
  return result;
};
```

## 更新日誌

### v1.0.0 (2024-12-17)
- 初始版本發布
- 實現所有核心API服務
- WebSocket集成
- 錯誤處理機制
- 工具函數和Hooks

### 計劃功能
- [ ] 離線支持
- [ ] 請求去重
- [ ] 更智能的緩存策略
- [ ] GraphQL支持