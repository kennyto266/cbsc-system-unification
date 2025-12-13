# API端點文檔

## 概述

本文檔描述了CBSC個人策略管理系統的前端API集成端點，用於與後端FastAPI服務通信。

## 基礎配置

- **基礎URL**: `http://localhost:3004` (可通過 `REACT_APP_API_URL` 環境變量配置)
- **認證方式**: Bearer Token (JWT)
- **數據格式**: JSON
- **字符編碼**: UTF-8

## 認證

所有需要認證的請求都必須在請求頭中包含：

```
Authorization: Bearer <your-jwt-token>
```

Token存儲在 `localStorage` 的 `auth_token` 鍵中。

## 策略管理端點

### 1. 獲取策略列表

**端點**: `GET /api/strategies/list`

**描述**: 獲取所有可用策略的列表

**查詢參數**:

- `page` (可選): 頁碼，默認為 1
- `page_size` (可選): 每頁大小，默認為 50

**響應示例**:

```json
{
  "strategies": [
    {
      "name": "DirectRSIStrategy",
      "enabled": true,
      "description": "基於牛熊比例的RSI策略",
      "parameters": {
        "rsi_period": 14,
        "overbought": 70,
        "oversold": 30
      },
      "strategy_type": "RSI",
      "risk_level": "medium",
      "created_at": "2025-12-10T08:00:00Z",
      "updated_at": "2025-12-10T08:00:00Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 50,
  "has_more": false
}
```

### 2. 獲取策略性能數據

**端點**: `GET /api/strategies/performance`

**描述**: 獲取所有策略的性能指標

**查詢參數**:

- `strategy_name` (可選): 特定策略名稱，不提供則返回所有策略

**響應示例**:

```json
[
  {
    "name": "DirectRSIStrategy",
    "sharpe_ratio": 1.23,
    "max_drawdown": -0.15,
    "total_return": 0.25,
    "win_rate": 0.65,
    "status": "enabled",
    "daily_pnl": 1500.0,
    "volatility": 0.12,
    "calmar_ratio": 1.67,
    "profit_factor": 1.8,
    "last_updated": "2025-12-10T08:30:00Z"
  }
]
```

### 3. 獲取策略詳細信息

**端點**: `GET /api/strategies/{strategy_name}/details`

**描述**: 獲取特定策略的完整詳細信息

**路徑參數**:

- `strategy_name`: 策略名稱

**響應示例**:

```json
{
  "name": "DirectRSIStrategy",
  "enabled": true,
  "description": "基於牛熊比例的RSI策略",
  "parameters": {
    "rsi_period": 14,
    "overbought": 70,
    "oversold": 30
  },
  "strategy_type": "RSI",
  "risk_level": "medium",
  "created_at": "2025-12-10T08:00:00Z",
  "updated_at": "2025-12-10T08:00:00Z"
}
```

### 4. 獲取策略性能詳情

**端點**: `GET /api/strategies/{strategy_name}/performance`

**描述**: 獲取特定策略的性能數據

**路徑參數**:

- `strategy_name`: 策略名稱

**響應示例**:

```json
{
  "name": "DirectRSIStrategy",
  "sharpe_ratio": 1.23,
  "max_drawdown": -0.15,
  "total_return": 0.25,
  "win_rate": 0.65,
  "status": "enabled",
  "daily_pnl": 1500.0,
  "volatility": 0.12,
  "calmar_ratio": 1.67,
  "profit_factor": 1.8,
  "last_updated": "2025-12-10T08:30:00Z"
}
```

### 5. 獲取最後信號

**端點**: `GET /api/strategies/{strategy_name}/last-signal`

**描述**: 獲取策略的最後交易信號

**路徑參數**:

- `strategy_name`: 策略名稱

**響應示例**:

```json
{
  "type": "buy",
  "strength": 75,
  "timestamp": "2025-12-10T08:30:00Z",
  "price": 45000.0,
  "reason": "RSI超賣區反彈"
}
```

### 6. 切換策略狀態

**端點**: `POST /api/strategies/{strategy_name}/toggle`

**描述**: 啟用或禁用策略

**路徑參數**:

- `strategy_name`: 策略名稱

**請求體**:

```json
{
  "enabled": true
}
```

**響應示例**:

```json
{
  "success": true,
  "message": "策略狀態已更新",
  "previous_status": false,
  "new_status": true,
  "timestamp": "2025-12-10T08:30:00Z"
}
```

### 7. 獲取性能摘要

**端點**: `GET /api/strategies/performance-summary`

**描述**: 獲取所有策略的性能摘要統計

**響應示例**:

```json
{
  "total_strategies": 5,
  "active_strategies": 3,
  "total_return": 0.45,
  "daily_pnl": 5000.0,
  "sharpe_ratio": 1.35,
  "max_drawdown": -0.12,
  "win_rate": 0.62,
  "best_strategy": {
    "name": "DirectRSIStrategy",
    "sharpe_ratio": 1.23,
    "max_drawdown": -0.15,
    "total_return": 0.25,
    "win_rate": 0.65,
    "status": "enabled",
    "last_updated": "2025-12-10T08:30:00Z"
  },
  "worst_strategy": {
    "name": "MAMACrossStrategy",
    "sharpe_ratio": 0.85,
    "max_drawdown": -0.25,
    "total_return": 0.08,
    "win_rate": 0.52,
    "status": "enabled",
    "last_updated": "2025-12-10T08:30:00Z"
  }
}
```

## 實時數據端點

### WebSocket連接

**端點**: `ws://localhost:3004/ws`

**描述**: 建立WebSocket連接以接收實時數據更新

**訂閱消息格式**:

```json
{
  "type": "subscribe",
  "data": {
    "channel": "performance_updates" | "strategy_updates" | "signals_updates"
  }
}
```

**實時更新消息格式**:

```json
{
  "type": "performance_update",
  "strategy_name": "DirectRSIStrategy",
  "performance": {
    "sharpe_ratio": 1.24,
    "daily_pnl": 1550.0,
    "timestamp": "2025-12-10T08:31:00Z"
  }
}
```

## 系統端點

### 1. 健康檢查

**端點**: `GET /health`

**描述**: 檢查API服務健康狀態

**響應示例**:

```json
{
  "status": "healthy",
  "timestamp": "2025-12-10T08:30:00Z",
  "version": "1.0.0"
}
```

### 2. 系統信息

**端點**: `GET /api/system/info`

**描述**: 獲取系統信息

**響應示例**:

```json
{
  "version": "1.0.0",
  "environment": "development",
  "supported_features": ["real_time_updates", "strategy_management", "performance_analysis"]
}
```

## 錯誤處理

所有API錯誤都遵循統一的響應格式：

```json
{
  "success": false,
  "error": "錯誤描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-12-10T08:30:00Z",
  "details": {
    "field": "具體錯誤字段",
    "reason": "錯誤原因"
  }
}
```

### 常見錯誤碼

| 狀態碼 | 錯誤碼               | 描述                 |
| ------ | -------------------- | -------------------- |
| 400    | VALIDATION_ERROR     | 請求參數驗證失敗     |
| 401    | AUTHENTICATION_ERROR | 未提供有效的認證令牌 |
| 403    | AUTHORIZATION_ERROR  | 沒有權限執行此操作   |
| 404    | NOT_FOUND            | 請求的資源不存在     |
| 429    | RATE_LIMIT_ERROR     | 請求頻率過高         |
| 500    | INTERNAL_ERROR       | 服務器內部錯誤       |
| 503    | SERVICE_UNAVAILABLE  | 服務暫時不可用       |

## 數據驗證

前端會對所有API響應進行數據驗證，確保數據完整性和類型正確性。驗證規則包括：

### 策略性能數據

- `sharpe_ratio`: -10 到 10 之間的數字
- `max_drawdown`: -1 到 0 之間的數字
- `total_return`: -10 到 10 之間的數字
- `win_rate`: 0 到 1 之間的數字
- `status`: 必須是 "enabled" 或 "disabled"

### 策略配置數據

- `name`: 非空字符串
- `enabled`: 布爾值
- `description`: 字符串，至少10個字符
- `strategy_type`: 字符串
- `risk_level`: 字符串

## 緩存策略

為了提高性能和減少API調用，前端實施了以下緩存策略：

- **策略列表**: 5分鐘緩存
- **性能數據**: 1分鐘緩存
- **性能摘要**: 30秒緩存
- **策略詳細信息**: 2分鐘緩存

緩存會在以下情況下自動清除：

1. 接收到WebSocket實時更新
2. 執行策略操作（如啟用/禁用）
3. 緩存過期
4. 手動清除

## 自動刷新

- **默認間隔**: 10秒
- **可配置**: 通過Hook的 `refreshInterval` 參數
- **可禁用**: 設置 `autoRefresh: false`

## 使用示例

### React Hook 使用示例

```typescript
import useStrategyDataEnhanced from '../hooks/useStrategyDataEnhanced';

function MyComponent() {
  const {
    strategies,
    performances,
    performanceSummary,
    loading,
    error,
    fetchStrategies,
    toggleStrategy
  } = useStrategyDataEnhanced({
    autoRefresh: true,
    refreshInterval: 15000
  });

  const handleToggleStrategy = async (strategyName: string) => {
    await toggleStrategy(strategyName, true);
  };

  if (loading) return <div>加載中...</div>;
  if (error) return <div>錯誤: {error}</div>;

  return (
    <div>
      {/* 渲染策略數據 */}
    </div>
  );
}
```

### 直接API調用示例

```typescript
import strategyDataService from '../services/strategyDataService'

// 獲取策略列表
const strategies = await strategyDataService.getStrategyList()

// 獲取性能數據
const performances = await strategyDataService.getStrategyPerformance()

// 切換策略
await strategyDataService.toggleStrategy('MyStrategy', true)
```

## 注意事項

1. **CORS配置**: 確保後端正確配置了CORS以允許前端域名訪問
2. **認證令牌**: 定期檢查並刷新過期的JWT令牌
3. **錯誤處理**: 始終檢查API響應的 `success` 字段
4. **數據驗證**: 依賴前端驗證，但也要處理意外的數據格式
5. **性能優化**: 合理使用緩存和自動刷新，避免過度頻繁的API調用
6. **網絡錯誤**: 實施適當的重試機制和用戶友好的錯誤提示
