---
name: task-006-api-integration-layer
title: 任務006：API集成層開發
status: completed
assignee: backend-frontend-developer
priority: P0
created: 2025-12-14T03:32:09Z
updated: 2025-12-17T14:02:48Z
estimated: 4 days
tags: [rtk-query, api-integration, fastapi, error-handling]
dependsOn: [task-005-state-management-architecture]
blocks: []
---

## 📋 任務描述

創建RTK Query API切片，實現與現有FastAPI後端的對接，建立錯誤處理和重試機制，為前端應用提供統一的API服務層。

## 🎯 具體要求

### 1. RTK Query API配置
- [ ] 創建基礎API切片配置
- [ ] 配置基礎URL和認證頭
- [ ] 實現自動Token注入
- [ ] 配置請求/響應攔截器

### 2. 認證API集成
- [ ] 實現登錄接口
- [ ] 實現Token刷新接口
- [ ] 實現註銷接口
- [ ] 實現用戶信息獲取接口
- [ ] 實現密碼修改接口

### 3. 策略管理API
- [ ] 策略列表查詢（支持分頁、過濾、排序）
- [ ] 策略詳情獲取
- [ ] 策略創建接口
- [ ] 策略更新接口
- [ ] 策略刪除接口
- [ ] 策略參數配置接口

### 4. 實時數據API
- [ ] WebSocket連接管理
- [ ] 策略執行狀態訂閱
- [ ] 實時行情數據訂閱
- [ ] 系統通知訂閱

### 5. 錯誤處理機制
- [ ] 統一錯誤格式化
- [ ] 自動重試配置
- [ ] 請求取消處理
- [ ] 網絡錯誤處理
- [ ] 業務錯誤碼映射

## 🔧 技術實施

### API切片結構
```typescript
// apiSlice.ts
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Strategy', 'Execution', 'Notification'],
  endpoints: (builder) => ({
    // 認證相關
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),

    // 策略相關
    getStrategies: builder.query<StrategiesResponse, StrategiesQuery>({
      query: (params) => ({
        url: '/strategies',
        params,
      }),
      providesTags: ['Strategy'],
    }),
  }),
});
```

### 基礎查詢配置
```typescript
// baseQuery.ts
const baseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003/api',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    headers.set('content-type', 'application/json');
    return headers;
  },
});

// 帶重新認證的查詢
const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result.error?.status === 401) {
    // 嘗試刷新token
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: {
          refreshToken: (api.getState() as RootState).auth.refreshToken,
        },
      },
      api,
      extraOptions
    );

    if (refreshResult.data) {
      // 重新設置token並重試原請求
      api.dispatch(setCredentials(refreshResult.data));
      result = await baseQuery(args, api, extraOptions);
    } else {
      // 刷新失敗，跳轉到登錄頁
      api.dispatch(logout());
    }
  }

  return result;
};
```

### 錯誤處理
```typescript
// errorTypes.ts
export interface ApiError {
  status: number;
  data: {
    code: string;
    message: string;
    details?: any;
  };
}

// 錯誤映射
export const errorMap: Record<string, string> = {
  'VALIDATION_ERROR': '輸入驗證失敗',
  'AUTHENTICATION_FAILED': '認證失敗',
  'PERMISSION_DENIED': '權限不足',
  'STRATEGY_NOT_FOUND': '策略不存在',
  'DUPLICATE_STRATEGY': '策略名稱已存在',
};
```

## 📁 文件結構

```
src/
├── api/
│   ├── index.ts                 # API匯出
│   ├── apiSlice.ts              # 基礎API切片
│   ├── baseQuery.ts             # 基礎查詢配置
│   ├── endpoints/
│   │   ├── authApi.ts           # 認證API
│   │   ├── strategyApi.ts       # 策略API
│   │   ├── userApi.ts           # 用戶API
│   │   └── realtimeApi.ts       # 實時數據API
│   ├── types/
│   │   ├── auth.ts              # 認證類型
│   │   ├── strategy.ts          # 策略類型
│   │   └── common.ts            # 通用類型
│   └── utils/
│       ├── errorHandlers.ts     # 錯誤處理
│       ├── retry.ts             # 重試邏輯
│       └── websocket.ts         # WebSocket管理
└── hooks/
    ├── useAuth.ts               # 認證相關hooks
    ├── useStrategy.ts           # 策略相關hooks
    └── useRealtime.ts           # 實時數據hooks
```

## 🔗 與現有系統集成

### FastAPI後端對接
- 使用現有API端點
- 遵循RESTful設計規範
- 處理FastAPI的驗證錯誤格式
- 支持FastAPI的分頁響應格式

### 現有認證系統
- 復用現有JWT機制
- 支持雙Token（access + refresh）
- 保持與現有權限系統兼容

## ✅ 驗收標準

1. **功能完整性**
   - 所有API端點正常工作
   - 自動Token刷新機制有效
   - WebSocket穩定連接

2. **性能指標**
   - API響應時間 < 500ms
   - 自動重試不影響用戶體驗
   - WebSocket消息延遲 < 100ms

3. **錯誤處理**
   - 網絡錯誤友好提示
   - 業務錯誤準確映射
   - 自動重試次數可配置

4. **開發體驗**
   - 完整的TypeScript類型支持
   - API文檔自動生成
   - 開發環境Mock數據支持

## 🧪 測試計劃

### 單元測試
- API端點測試
- 錯誤處理測試
- 重試機制測試
- WebSocket管理測試

### 集成測試
- 與FastAPI後端集成測試
- 認證流程端到端測試
- 並發請求處理測試
- 網絡異常恢復測試

### Mock服務
- MSW集成用於開發測試
- Mock數據生成
- API響應模擬

## 📝 注意事項

1. **性能優化**
   - 實現請求緩存機制
   - 避免重複請求
   - 實現樂觀更新

2. **安全考慮**
   - 敏感數據加密傳輸
   - 防止CSRF攻擊
   - 請求速率限制

3. **兼容性**
   - 支持IE11+（如需要）
   - 移動端適配
   - 離線處理機制

## 🚀 後續任務

完成後，支持：
- Task 007: 策略管理界面實現（提供數據支持）
- Task 008: 數據可視化組件開發（提供實時數據）

---

**創建人**: Claude Code Assistant
**最後更新**: 2025-12-14T03:32:09Z
---
## Completion
This task has been completed on 2025-12-17T14:02:48Z
