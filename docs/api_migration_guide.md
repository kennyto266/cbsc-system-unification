# API Module Refactoring Migration Guide
# API模块重构迁移指南

## 概述

本文档描述了CBSC策略管理系统的API模块重构，从旧的架构迁移到新的模块化架构的指南。

## 新架构特性

### 1. 模块化设计
- **服务层分离**: 业务逻辑与数据访问完全分离
- **仓库模式**: 统一的数据访问接口
- **依赖注入**: 松耦合的组件依赖管理

### 2. 增强功能
- **批量操作**: 高性能的批量策略处理
- **实时更新**: WebSocket和Server-Sent Events支持
- **高级搜索**: 灵活的策略搜索和过滤
- **乐观锁**: 防止并发更新冲突

### 3. 改进的错误处理
- **统一错误格式**: 标准化的错误响应
- **详细错误信息**: 包含错误码、详情和时间戳
- **自定义异常类型**: 业务异常的分类处理

### 4. 增强的验证
- **参数验证**: 全面的请求参数验证
- **业务规则验证**: 策略特定的业务规则检查
- **批量验证**: 批量操作的统一验证

## API端点对比

### 策略CRUD操作

| 旧端点 | 新端点 | 说明 |
|--------|--------|------|
| `/api/personal-strategies` | `/api/v1/strategies` | 统一的策略管理端点 |
| - | `/api/v1/strategies/search` | 新增：高级搜索功能 |
| - | `/api/v1/strategies/batch` | 新增：批量操作端点 |
| - | `/api/v1/strategies/{id}/analytics` | 新增：策略分析数据 |

### 实时更新

| 功能 | 旧实现 | 新实现 |
|------|--------|--------|
| 实时数据 | 轮询 | WebSocket (`/api/v1/strategies/ws`) |
| 更新推送 | 无 | Server-Sent Events (`/api/v1/strategies/realtime`) |

## 迁移步骤

### 1. 更新API基础URL

```javascript
// 旧代码
const BASE_URL = 'http://localhost:3004/api/personal-strategies';

// 新代码
const BASE_URL = 'http://localhost:3004/api/v1/strategies';
```

### 2. 更新请求格式

新的API使用统一的响应格式：

```javascript
// 旧响应格式
{
  "data": [...],
  "total": 100
}

// 新响应格式
{
  "success": true,
  "code": "success",
  "message": "操作成功",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "timestamp": "2025-12-14T10:00:00Z"
}
```

### 3. 错误处理更新

```javascript
// 旧错误处理
if (response.status === 400) {
  console.error('Bad Request:', response.data);
}

// 新错误处理
if (!response.data.success) {
  const error = response.data.error;
  console.error(`${error.code}: ${error.message}`);
  if (error.details) {
    error.details.forEach(detail => {
      console.error(`${detail.field}: ${detail.message}`);
    });
  }
}
```

### 4. 批量操作集成

```javascript
// 批量激活策略
const batchRequest = {
  strategy_ids: ['strategy_1', 'strategy_2', 'strategy_3'],
  operation: 'activate',
  batch_size: 50,
  continue_on_error: true
};

const response = await fetch('/api/v1/strategies/batch', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(batchRequest)
});

const result = await response.json();
console.log(`成功: ${result.data.successful}, 失败: ${result.data.failed}`);
```

### 5. 实时更新集成

#### WebSocket连接

```javascript
// 创建WebSocket连接
const ws = new WebSocket('ws://localhost:3004/api/v1/strategies/ws?user_id=123');

ws.onopen = () => {
  // 订阅特定策略的更新
  ws.send(JSON.stringify({
    type: 'subscribe',
    filters: {
      strategy_ids: ['strategy_1', 'strategy_2']
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'strategy_update') {
    updateStrategyInUI(data.strategy);
  }
};
```

#### Server-Sent Events

```javascript
// 创建EventSource连接
const eventSource = new EventSource(
  '/api/v1/strategies/realtime?user_id=123&strategy_ids=strategy_1,strategy_2'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleRealTimeUpdate(data);
};
```

## 前端代码更新指南

### 1. API服务层更新

```typescript
// 旧的API服务
class StrategyService {
  async getStrategies(params: any) {
    const response = await axios.get('/api/personal-strategies', { params });
    return response.data;
  }
}

// 新的API服务
class EnhancedStrategyService {
  async getStrategies(params: {
    page?: number;
    page_size?: number;
    filters?: Record<string, any>;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }) {
    const response = await axios.get('/api/v1/strategies', { params });

    if (!response.data.success) {
      throw new Error(response.data.error.message);
    }

    return response.data.data;
  }

  async searchStrategies(params: {
    query: string;
    filters?: Record<string, any>;
    page?: number;
    page_size?: number;
  }) {
    const response = await axios.get('/api/v1/strategies/search', { params });
    return response.data.data;
  }

  async batchOperation(params: {
    strategy_ids: string[];
    operation: 'activate' | 'deactivate' | 'delete';
    batch_size?: number;
    continue_on_error?: boolean;
  }) {
    const response = await axios.post('/api/v1/strategies/batch', null, { params });
    return response.data.data;
  }
}
```

### 2. Redux/状态管理更新

```typescript
// 更新Redux actions和reducers
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// 异步thunk for fetching strategies
export const fetchStrategies = createAsyncThunk(
  'strategies/fetch',
  async (params: any, { rejectWithValue }) => {
    try {
      const service = new EnhancedStrategyService();
      const result = await service.getStrategies(params);
      return result;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// 异步thunk for batch operations
export const batchActivateStrategies = createAsyncThunk(
  'strategies/batchActivate',
  async (strategyIds: string[], { rejectWithValue }) => {
    try {
      const service = new EnhancedStrategyService();
      const result = await service.batchOperation({
        strategy_ids: strategyIds,
        operation: 'activate'
      });
      return result;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Slice定义
const strategiesSlice = createSlice({
  name: 'strategies',
  initialState: {
    items: [],
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
      totalPages: 0
    },
    loading: false,
    error: null,
    batchOperation: {
      loading: false,
      result: null
    }
  },
  reducers: {
    // 处理实时更新
    strategyUpdated: (state, action) => {
      const index = state.items.findIndex(s => s.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStrategies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.pagination = {
          page: action.payload.page,
          pageSize: action.payload.page_size,
          total: action.payload.total,
          totalPages: action.payload.total_pages
        };
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});
```

### 3. 实时更新集成

```typescript
// WebSocket Hook
import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { strategyUpdated } from '../store/strategiesSlice';

export const useStrategyWebSocket = (userId: number, strategyIds?: string[]) => {
  const dispatch = useDispatch();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 建立WebSocket连接
    const wsUrl = `ws://localhost:3004/api/v1/strategies/ws?user_id=${userId}`;
    if (strategyIds) {
      wsUrl += `&strategy_ids=${strategyIds.join(',')}`;
    }

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'strategy_update') {
        dispatch(strategyUpdated(data.strategy));
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      // 实现重连逻辑
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          useStrategyWebSocket(userId, strategyIds);
        }
      }, 5000);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId, strategyIds]);
};
```

## 性能优化建议

### 1. 批量操作
- 使用批量操作API处理多个策略
- 合理设置批次大小（建议50-100）
- 使用continue_on_error避免单个失败影响整体

### 2. 缓存策略
- 利用浏览器缓存存储策略列表
- 使用Redux缓存分页数据
- 实现本地状态同步

### 3. 实时更新
- 使用WebSocket而非轮询
- 合理订阅策略更新，避免不必要的数据传输
- 实现连接断开重连机制

## 兼容性说明

### 向后兼容
- 旧的API端点仍然可用（标记为v0）
- 新功能逐步迁移到新API
- 支持渐进式升级

### 版本支持
- v0.x: 旧版API（逐步废弃）
- v1.0: 新版增强API
- v2.0: 未来版本规划

## 故障排除

### 常见问题

1. **连接超时**
   - 检查WebSocket连接状态
   - 实现重连机制
   - 验证网络连接

2. **验证错误**
   - 检查请求参数格式
   - 查看错误详情
   - 确认业务规则

3. **批量操作失败**
   - 检查批次大小
   - 查看失败详情
   - 考虑使用continue_on_error

### 调试工具

1. **API文档**: 访问 `/api/v1/docs` 查看完整API文档
2. **健康检查**: 访问 `/api/v1/health` 检查服务状态
3. **日志监控**: 查看服务器日志获取详细错误信息

## 支持和反馈

如有迁移问题或建议，请：
1. 查看API文档
2. 检查测试用例
3. 提交Issue或联系技术支持

---

**更新日期**: 2025-12-14
**版本**: 1.0.0
**维护者**: CBSC开发团队