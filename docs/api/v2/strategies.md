# 策略管理 API v2

## 概述

策略管理模塊提供完整的交易策略生命週期管理功能，包括創建、編輯、版本控制、分類管理和執行監控。

### 端點列表

- [獲取策略列表](#獲取策略列表)
- [創建策略](#創建策略)
- [獲取策略詳情](#獲取策略詳情)
- [更新策略](#更新策略)
- [刪除策略](#刪除策略)
- [策略版本管理](#策略版本管理)
- [策略分類](#策略分類)
- [策略執行](#策略執行)

## 獲取策略列表

獲取用戶有權訪問的策略列表，支持分頁、排序和過濾。

```http
GET /api/v2/strategies
```

### 查詢參數

| 參數 | 類型 | 描述 | 默認值 |
|-----|------|------|--------|
| page | integer | 頁碼 | 1 |
| size | integer | 每頁大小 | 20 |
| sort | string | 排序字段 | created_at |
| order | string | 排序方向 | desc |
| status | string | 策略狀態 | - |
| category | string | 策略分類 | - |
| search | string | 搜索關鍵詞 | - |
| tags | string | 標籤過濾（逗號分隔） | - |
| created_after | string | 創建時間篩選（ISO 8601） | - |
| created_before | string | 創建時間篩選（ISO 8601） | - |

### 請求示例

```http
GET /api/v2/strategies?page=1&size=10&status=active&category=momentum
```

### 響應

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "str_123",
        "name": "雙均線交叉策略",
        "description": "基於短期和長期移動平均線交叉的信號策略",
        "version": "1.2.0",
        "status": "active",
        "category": {
          "id": "cat_001",
          "name": "技術指標策略",
          "slug": "technical"
        },
        "tags": ["均線", "趨勢", "量化"],
        "performance": {
          "total_return": 25.6,
          "sharpe_ratio": 1.85,
          "max_drawdown": -8.3,
          "win_rate": 0.62
        },
        "creator": {
          "id": 1,
          "username": "trader_001"
        },
        "created_at": "2025-12-01T10:00:00Z",
        "updated_at": "2025-12-15T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 45,
      "pages": 5
    }
  }
}
```

## 創建策略

創建新的交易策略。

```http
POST /api/v2/strategies
```

### 請求體

```json
{
  "name": "string",
  "description": "string",
  "category_id": "string",
  "tags": ["string"],
  "config": {
    "type": "momentum",
    "parameters": {
      "short_window": 5,
      "long_window": 20,
      "threshold": 0.02
    },
    "universe": {
      "symbols": ["AAPL", "MSFT", "GOOGL"],
      "exchange": "NASDAQ"
    },
    "risk_management": {
      "max_position_size": 0.1,
      "stop_loss": 0.05,
      "take_profit": 0.1
    }
  },
  "code": {
    "language": "python",
    "entry": "strategy.py",
    "files": {
      "strategy.py": "def initialize(context):\n    pass",
      "requirements.txt": "pandas==1.5.0\nnumpy==1.23.0"
    }
  }
}
```

### 響應

```json
{
  "success": true,
  "data": {
    "id": "str_456",
    "name": "RSI均值回歸策略",
    "version": "1.0.0",
    "status": "draft",
    "created_at": "2025-12-19T10:00:00Z"
  },
  "message": "策略創建成功"
}
```

### 驗證規則

- `name`: 必填，2-50個字符
- `category_id`: 必填，有效的分類ID
- `config.type`: 必填，支持的策略類型
- `config.parameters`: 必填，策略參數配置

## 獲取策略詳情

獲取指定策略的詳細信息。

```http
GET /api/v2/strategies/{strategy_id}
```

### 路徑參數

| 參數 | 類型 | 描述 |
|-----|------|------|
| strategy_id | string | 策略ID |

### 響應

```json
{
  "success": true,
  "data": {
    "id": "str_123",
    "name": "雙均線交叉策略",
    "description": "基於短期和長期移動平均線交叉的信號策略",
    "version": "1.2.0",
    "status": "active",
    "category": {
      "id": "cat_001",
      "name": "技術指標策略"
    },
    "tags": ["均線", "趨勢", "量化"],
    "config": {
      "type": "momentum",
      "parameters": {
        "short_window": 5,
        "long_window": 20,
        "threshold": 0.02
      }
    },
    "code": {
      "language": "python",
      "files": {
        "strategy.py": "def initialize(context):...",
        "requirements.txt": "pandas==1.5.0"
      }
    },
    "backtest_history": [
      {
        "id": "bt_789",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "performance": {
          "total_return": 25.6,
          "sharpe_ratio": 1.85,
          "max_drawdown": -8.3
        },
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "creator": {
      "id": 1,
      "username": "trader_001",
      "full_name": "張三"
    },
    "collaborators": [
      {
        "id": 2,
        "username": "analyst_001",
        "role": "editor"
      }
    ],
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-15T14:30:00Z"
  }
}
```

## 更新策略

更新現有策略的信息。

```http
PUT /api/v2/strategies/{strategy_id}
```

### 請求體

```json
{
  "name": "string",
  "description": "string",
  "tags": ["string"],
  "config": {
    "parameters": {
      "short_window": 10,
      "long_window": 30
    }
  },
  "code": {
    "files": {
      "strategy.py": "def initialize(context):\n    # Updated code"
    }
  }
}
```

### 響應

```json
{
  "success": true,
  "data": {
    "id": "str_123",
    "version": "1.3.0",
    "updated_at": "2025-12-19T11:00:00Z"
  },
  "message": "策略更新成功"
}
```

## 刪除策略

刪除指定的策略。

```http
DELETE /api/v2/strategies/{strategy_id}
```

### 路徑參數

| 參數 | 類型 | 描述 |
|-----|------|------|
| strategy_id | string | 策略ID |

### 請求體（可選）

```json
{
  "confirm": true,
  "reason": "策略不再需要"
}
```

### 響應

```json
{
  "success": true,
  "message": "策略刪除成功"
}
```

### 狀態碼

- `200`: 刪除成功
- `404`: 策略不存在
- `403`: 沒有權限刪除
- `409`: 策��正在運行中

## 策略版本管理

### 獲取版本列表

```http
GET /api/v2/strategies/{strategy_id}/versions
```

### 響應

```json
{
  "success": true,
  "data": {
    "versions": [
      {
        "version": "1.2.0",
        "status": "active",
        "created_at": "2025-12-15T14:30:00Z",
        "creator": "trader_001",
        "changes": "優化止盈策略"
      },
      {
        "version": "1.1.0",
        "status": "inactive",
        "created_at": "2025-12-10T09:15:00Z",
        "creator": "trader_001",
        "changes": "增加風險控制模塊"
      }
    ]
  }
}
```

### 回滾到指定版本

```http
POST /api/v2/strategies/{strategy_id}/versions/{version}/rollback
```

### 響應

```json
{
  "success": true,
  "message": "已回滾到版本 1.1.0"
}
```

## 策略分類

### 獲取分類列表

```http
GET /api/v2/strategies/categories
```

### 響應

```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "cat_001",
        "name": "技術指標策略",
        "slug": "technical",
        "description": "基於技術指標的交易策略",
        "strategy_count": 25,
        "subcategories": [
          {
            "id": "sub_001",
            "name": "均線策略",
            "strategy_count": 10
          }
        ]
      }
    ]
  }
}
```

### 創建分類

```http
POST /api/v2/strategies/categories
```

### 請求體

```json
{
  "name": "string",
  "slug": "string",
  "description": "string",
  "parent_id": "string"
}
```

## 策略執行

### 啟動策略

```http
POST /api/v2/strategies/{strategy_id}/start
```

### 請求體

```json
{
  "mode": "paper_trading",
  "initial_capital": 1000000,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

### 響應

```json
{
  "success": true,
  "data": {
    "execution_id": "exec_789",
    "status": "running",
    "started_at": "2025-12-19T11:00:00Z"
  }
}
```

### 停止策略

```http
POST /api/v2/strategies/{strategy_id}/stop
```

### 獲取執行狀態

```http
GET /api/v2/strategies/{strategy_id}/executions/{execution_id}
```

### 響應

```json
{
  "success": true,
  "data": {
    "id": "exec_789",
    "strategy_id": "str_123",
    "status": "running",
    "mode": "paper_trading",
    "progress": 0.65,
    "performance": {
      "current_return": 12.5,
      "daily_pnl": 2500,
      "positions_count": 5
    },
    "started_at": "2025-12-19T11:00:00Z",
    "updated_at": "2025-12-19T15:30:00Z"
  }
}
```

## 策略導入導出

### 導出策略

```http
GET /api/v2/strategies/{strategy_id}/export
```

### 查詢參數

| 參數 | 類型 | 描述 |
|-----|------|------|
| format | string | 導出格式 (json/yaml) |
| include_backtests | boolean | 是否包含回測數據 |

### 導入策略

```http
POST /api/v2/strategies/import
```

### 請求體 (multipart/form-data)

```
file: <策略文件>
name: <策略名稱>
category_id: <分類ID>
```

## 錯誤代碼

| 錯誤代碼 | 說明 |
|---------|------|
| `STRATEGY_NOT_FOUND` | 策略不存在 |
| `STRATEGY_NAME_EXISTS` | 策略名稱已存在 |
| `INVALID_STRATEGY_TYPE` | 無效的策略類型 |
| `STRATEGY_CODE_INVALID` | 策略代碼無效 |
| `STRATEGY_RUNNING` | 策略正在運行 |
| `INSUFFICIENT_PERMISSIONS` | 權限不足 |
| `QUOTA_EXCEEDED` | 策略數量超限 |

## 最佳實踐

1. **版本控制**: 每次重要修改都創建新版本
2. **文檔完善**: 編寫清晰的策略描述和參數說明
3. **測試驗證**: 生產部署前進行充分的回測
4. **監控警報**: 設置性能警報和風險提示
5. **定期審查**: 定期審查策略表現和有效性