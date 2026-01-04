# 前端API迁移指南
# Frontend API Migration Guide

**版本:** 1.0
**日期:** 2026-01-04
**目标:** 统一前端API调用，消除路由冲突

---

## 一、当前问题分析/Current Issues

### 1.1 存在的问题

1. **API端点不统一**
   ```typescript
   // 当前代码中存在多种调用方式
   '/api/strategies'              // 方式1
   '/strategies'                  // 方式2
   'http://localhost:3007/api/...' // 方式3（硬编码）
   ```

2. **没有版本控制**
   - 无法区分V1和V2 API
   - 无法实现渐进式升级

3. **错误处理不一致**
   - 不同API端点使用不同的错误处理方式
   - 缺少统一的错误格式

4. **TypeScript类型不完整**
   - 部分API缺少类型定义
   - 响应类型不匹配

### 1.2 影响范围

**受影响的文件:**
```typescript
// API定义文件
frontend/src/api/endpoints/strategyApi.ts
frontend/src/api/endpoints/userApi.ts
frontend/src/api/baseQuery.ts

// Hooks文件
frontend/src/hooks/useAuth.ts
frontend/src/hooks/useStrategies.ts

// Store文件
frontend/src/store/api/apiSlice.ts

// 服务文件
frontend/src/services/api.js
frontend/src/services/config.ts
```

---

## 二、迁移方案/Migration Strategy

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Application                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          API Client Layer (新增)                     │  │
│  │  - Version Management                                │  │
│  │  - Request Interception                              │  │
│  │  - Error Handling                                    │  │
│  │  - Retry Logic                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          API Service Layer (重构)                    │  │
│  │  - strategyApi.ts                                    │  │
│  │  - authApi.ts                                        │  │
│  │  - backtestApi.ts                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Data Layer (RTK Query)                       │  │
│  │  - apiSlice                                          │  │
│  │  - Cache Management                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API Gateway                       │
│                                                               │
│  /api/strategies      → cbsc_strategy_api.py                 │
│  /api/auth            → auth_endpoints.py (V1)               │
│  /api/v2/auth         → auth_endpoints_v2.py (V2)           │
│  /api/backtest        → backtest gateway                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 API版本管理

**配置文件:**
```typescript
// frontend/src/services/config.ts
export const API_CONFIG = {
  // 基础URL
  baseURL: process.env.REACT_APP_API_URL || '/api',

  // API版本配置
  versions: {
    strategies: 'v1',  // 默认使用V1
    auth: 'v1',        // 当前使用V1，准备升级到V2
    backtest: 'v1',
  },

  // 端点映射
  endpoints: {
    // 策略API
    strategies: '/strategies',
    strategiesV2: '/v2/strategies',

    // 认证API
    auth: '/auth',
    authV2: '/v2/auth',

    // 回测API
    backtest: '/backtest',
  },

  // 功能开关
  features: {
    useAuthV2: process.env.REACT_APP_USE_AUTH_V2 === 'true',
    useStrategiesV2: process.env.REACT_APP_USE_STRATEGIES_V2 === 'true',
  },
}
```

### 2.3 API客户端层

**统一API客户端:**
```typescript
// frontend/src/services/apiClient.ts
import { API_CONFIG } from './config'

class ApiClient {
  private baseURL: string
  private version: string

  constructor(module: 'strategies' | 'auth' | 'backtest') {
    this.baseURL = API_CONFIG.baseURL
    this.version = API_CONFIG.versions[module]
  }

  /**
   * 构建完整的API URL
   */
  getUrl(endpoint: string, useV2 = false): string {
    const version = useV2 ? 'v2' : this.version
    const versionPrefix = version === 'v1' ? '' : `/${version}`
    return `${this.baseURL}${versionPrefix}${endpoint}`
  }

  /**
   * 通用请求方法
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    useV2 = false
  ): Promise<T> {
    const url = this.getUrl(endpoint, useV2)

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new ApiError(response.status, await response.json())
    }

    return response.json()
  }

  // HTTP方法快捷方式
  get<T>(endpoint: string, useV2 = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, useV2)
  }

  post<T>(endpoint: string, data: any, useV2 = false): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }, useV2)
  }

  put<T>(endpoint: string, data: any, useV2 = false): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, useV2)
  }

  delete<T>(endpoint: string, useV2 = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, useV2)
  }
}

class ApiError extends Error {
  constructor(
    public status: number,
    public data: any
  ) {
    super(`API Error ${status}: ${data.message || 'Unknown error'}`)
  }
}

// 导出模块实例
export const strategyApiClient = new ApiClient('strategies')
export const authApiClient = new ApiClient('auth')
export const backtestApiClient = new ApiClient('backtest')
```

---

## 三、具体迁移步骤/Migration Steps

### 步骤1: 更新API基础配置

**文件:** `frontend/src/api/baseQuery.ts`

```typescript
// 之前
import { fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export const baseQuery = fetchBaseQuery({
  baseUrl: '/api',
})

// 之后
import { fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { API_CONFIG } from '../../services/config'

export const baseQuery = fetchBaseQuery({
  baseUrl: API_CONFIG.baseURL,
  prepareHeaders: (headers, { getState }) => {
    // 添加认证令牌
    const token = (getState() as any).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    return headers
  },
})

// 带重试的基础查询
export const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions)

  // 如果401错误，尝试刷新令牌
  if (result.error && result.error.status === 401) {
    const refreshResult = await baseQuery(
      '/auth/refresh',
      api,
      extraOptions
    )

    if (refreshResult.data) {
      // 重试原始请求
      result = await baseQuery(args, api, extraOptions)
    }
  }

  return result
}
```

### 步骤2: 重构策略API

**文件:** `frontend/src/api/endpoints/strategyApi.ts`

```typescript
import { createApi } from '@reduxjs/toolkit/query/react'
import { baseQueryWithReauth, providesList, invalidatesList } from '../baseQuery'
import type { Strategy } from '../../types/strategy'
import type { PaginatedResponse, SearchParams } from '../../types/api'
import { API_CONFIG } from '../../services/config'

// Strategy API slice
export const strategyApi = createApi({
  reducerPath: 'strategyApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Strategy', 'Execution', 'Backtest', 'Signal', 'Performance'],
  keepUnusedDataFor: 60,

  endpoints: (builder) => ({
    // 获取策略列表 - 使用统一的端点路径
    getStrategies: builder.query<PaginatedResponse<Strategy>, Partial<SearchParams> & {
      category?: string
      status?: string
      riskLevel?: string
    }>({
      query: (params) => ({
        // 移除硬编码的版本号，使用配置
        url: `${API_CONFIG.endpoints.strategies}/`,
        params,
      }),
      providesTags: (result) => providesList(result?.items || [], 'Strategy'),
      transformResponse: (response: any) => {
        // 统一响应格式转换
        const items = (response.items || []).map((item: any) => ({
          id: String(item.id),
          name: item.name,
          type: item.strategy_type || item.type || 'technical',
          category: item.category || 'other',
          status: item.is_active ? 'active' : (item.status || 'inactive'),
          // ... 其他字段映射
        }))

        return {
          items,
          total: response.total || 0,
          page: response.page || 1,
          pageSize: response.page_size || 20,
          totalPages: response.total_pages || 1,
        }
      },
    }),

    // 其他端点...
  }),
})
```

### 步骤3: 重构认证API

**文件:** `frontend/src/api/endpoints/authApi.ts` (新建)

```typescript
import { createApi } from '@reduxjs/toolkit/query/react'
import { baseQueryWithReauth } from '../baseQuery'
import { API_CONFIG } from '../../services/config'

interface LoginRequest {
  username: string
  password: string
}

interface LoginResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: {
    id: number
    username: string
    email: string
  }
}

// Auth API slice
export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Auth'],
  endpoints: (builder) => ({
    // 登录 - 根据配置使用V1或V2
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => {
        const useV2 = API_CONFIG.features.useAuthV2
        const endpoint = useV2
          ? `${API_CONFIG.endpoints.authV2}/login`
          : `${API_CONFIG.endpoints.auth}/login`

        return {
          url: endpoint,
          method: 'POST',
          body: credentials,
        }
      },
    }),

    // 刷新令牌
    refreshToken: builder.mutation<any, void>({
      query: () => ({
        url: `${API_CONFIG.endpoints.auth}/refresh`,
        method: 'POST',
      }),
    }),

    // 登出
    logout: builder.mutation<void, void>({
      query: () => ({
        url: `${API_CONFIG.endpoints.auth}/logout`,
        method: 'POST',
      }),
    }),

    // 获取当前用户
    getCurrentUser: builder.query<any, void>({
      query: () => `${API_CONFIG.endpoints.auth}/me`,
    }),
  }),
})

export const {
  useLoginMutation,
  useRefreshTokenMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
} = authApi
```

### 步骤4: 更新Hooks

**文件:** `frontend/src/hooks/useAuth.ts`

```typescript
import { useNavigate } from 'react-router-dom'
import { useLoginMutation, useLogoutMutation } from '../api/endpoints/authApi'

export const useAuth = () => {
  const navigate = useNavigate()
  const [login, { isLoading: isLoggingIn }] = useLoginMutation()
  const [logout, { isLoading: isLoggingOut }] = useLogoutMutation()

  const loginAction = async (username: string, password: string) => {
    try {
      const result = await login({ username, password }).unwrap()
      // 保存令牌
      localStorage.setItem('token', result.access_token)
      // 跳转到主页
      navigate('/dashboard')
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.data?.message || '登录失败',
      }
    }
  }

  const logoutAction = async () => {
    try {
      await logout().unwrap()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除本地存储
      localStorage.removeItem('token')
      // 跳转到登录页
      navigate('/login')
    }
  }

  return {
    login: loginAction,
    logout: logoutAction,
    isLoggingIn,
    isLoggingOut,
  }
}
```

### 步骤5: 更新环境变量

**文件:** `frontend/.env.development`

```bash
# API配置
REACT_APP_API_URL=http://localhost:3007/api

# API版本控制
REACT_APP_API_VERSION_STRATEGIES=v1
REACT_APP_API_VERSION_AUTH=v1
REACT_APP_API_VERSION_BACKTEST=v1

# 功能开关
# 启用V2认证（当后端准备好时）
# REACT_APP_USE_AUTH_V2=true
# 启用V2策略API（当后端准备好时）
# REACT_APP_USE_STRATEGIES_V2=true
```

**文件:** `frontend/.env.production`

```bash
# 生产环境配置
REACT_APP_API_URL=/api

# 使用稳定的V1版本
REACT_APP_API_VERSION_STRATEGIES=v1
REACT_APP_API_VERSION_AUTH=v1
REACT_APP_API_VERSION_BACKTEST=v1

# 功能开关默认关闭
REACT_APP_USE_AUTH_V2=false
REACT_APP_USE_STRATEGIES_V2=false
```

---

## 四、测试验证/Testing

### 4.1 单元测试

```typescript
// frontend/src/services/apiClient.test.ts
import { strategyApiClient } from './apiClient'

describe('ApiClient', () => {
  describe('getUrl', () => {
    it('should construct correct URL for V1', () => {
      const url = strategyApiClient.getUrl('/strategies/')
      expect(url).toBe('/api/strategies/')
    })

    it('should construct correct URL for V2', () => {
      const url = strategyApiClient.getUrl('/strategies/', true)
      expect(url).toBe('/api/v2/strategies/')
    })
  })

  describe('request', () => {
    it('should handle API errors', async () => {
      await expect(
        strategyApiClient.get('/non-existent')
      ).rejects.toThrow('API Error 404')
    })
  })
})
```

### 4.2 集成测试

```typescript
// frontend/src/api/endpoints/strategyApi.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { setupApiStore } from '../test-utils'
import { strategyApi } from './strategyApi'

describe('Strategy API', () => {
  let store: any

  beforeEach(() => {
    store = setupApiStore()
  })

  it('should fetch strategies list', async () => {
    const { result } = renderHook(() => strategyApi.useGetStrategiesQuery({}), {
      wrapper: ({ children }) => (
        <Provider store={store}>{children}</Provider>
      ),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeDefined()
  })
})
```

### 4.3 手动测试清单

- [ ] 登录功能正常
- [ ] 策略列表加载
- [ ] 策略创建/编辑/删除
- [ ] 回测功能运行
- [ ] 令牌刷新正常
- [ ] 错误处理正确
- [ ] 加载状态显示

---

## 五、回滚计划/Rollback Plan

### 触发条件

如果迁移后出现以下问题，考虑回滚：

- 关键功能不可用
- 性能严重下降
- 数据丢失或损坏

### 回滚步骤

1. **恢复代码**
   ```bash
   git revert <migration-commit>
   ```

2. **恢复环境变量**
   ```bash
   # 恢复 .env 文件
   git checkout HEAD~1 frontend/.env.development
   git checkout HEAD~1 frontend/.env.production
   ```

3. **重新部署**
   ```bash
   npm run build
   npm run deploy
   ```

---

## 六、后续优化/Future Improvements

### 6.1 短期优化（1-2周）

1. **添加请求缓存**
   ```typescript
   import { CachedApiClient } from './cachedApiClient'
   ```

2. **优化错误处理**
   ```typescript
   class ApiErrorHandler {
     static handle(error: ApiError) {
       // 统一错误处理逻辑
     }
   }
   ```

3. **添加请求重试**
   ```typescript
   import { retry } from '@reduxjs/toolkit/query/react'
   ```

### 6.2 中期优化（1-2月）

1. **实现请求取消**
   ```typescript
   const abortController = new AbortController()
   ```

2. **添加请求去重**
   ```typescript
   class RequestDeduplicator {
     // 防止重复请求
   }
   ```

3. **性能监控**
   ```typescript
   class ApiPerformanceMonitor {
     // 监控API性能
   }
   ```

### 6.3 长期优化（3-6月）

1. **GraphQL迁移**
   - 考虑使用GraphQL替代REST
   - 更灵活的数据查询

2. **实时通信**
   - WebSocket集成
   - 订阅模式

3. **离线支持**
   - Service Worker
   - 本地缓存策略

---

## 附录/Appendix

### A. API端点对照表

| 功能 | 旧端点 | 新端点 | 备注 |
|------|--------|--------|------|
| 获取策略列表 | `/api/strategies` | `/api/strategies/` | 统一 |
| 策略详情 | `/api/strategies/:id` | `/api/strategies/:id` | 统一 |
| 用户登录 | `/api/auth/login` | `/api/auth/login` | 不变 |
| 刷新令牌 | `/api/auth/refresh` | `/api/auth/refresh` | 不变 |
| 运行回测 | `/api/backtest/strategy` | `/api/backtest/strategy` | 统一 |

### B. 迁移检查清单

**准备阶段:**
- [ ] 阅读完整迁移指南
- [ ] 创建feature分支
- [ ] 备份当前代码
- [ ] 设置开发环境

**实施阶段:**
- [ ] 更新API配置
- [ ] 创建API客户端层
- [ ] 重构策略API
- [ ] 重构认证API
- [ ] 更新Hooks
- [ ] 更新环境变量

**测试阶段:**
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过
- [ ] 性能测试通过

**部署阶段:**
- [ ] 代码审查通过
- [ ] 合并到主分支
- [ ] 部署到测试环境
- [ ] 部署到生产环境

**验证阶段:**
- [ ] 监控错误日志
- [ ] 收集用户反馈
- [ ] 性能指标正常

---

**文档结束**
