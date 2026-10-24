# CBSC Strategy Management API v2 Documentation

## 概述

CBSC 策略管理系統 API v2 是完全重構的版本，提供了更強大、更靈活、更高性能的策略管理功能。本文檔詳細介紹了 API v2 的所有端點、使用方法和最佳實踐。

## 主要改進

### 架構升級
- **統一架構**：所有功能通過一致的 RESTful API 暴露
- **異步處理**：全面利用 FastAPI 的異步特性
- **依賴注入**：實現了 IoC 容器，提高可測試性
- **模塊化設計**：清晰的模塊邊界，易於維護和擴展

### 性能提升
- **響應時間**：平均 120ms，P95 < 180ms
- **併發支持**：WebSocket 支持 1000+ 連接
- **緩存策略**：智能多級緩存
- **批處理**：高效的批量操作

### 功能增強
- **實時更新**：WebSocket v2 支持策略狀態、執行進度、性能指標實時推送
- **高級查詢**：支持複雜的過濾、排序、分頁
- **批量操作**：支持策略的批量創建、更新、刪除
- **性能分析**：內置策略性能分析和報告功能

## API 端點總覽

### 基礎信息
- **Base URL**: `https://api.cbsc.com/api/v2`
- **認證方式**: JWT Bearer Token
- **內容類型**: `application/json`
- **API 版本**: v2

### 策略管理端點

| 方法 | 端點 | 描述 | 認證 |
|------|------|------|------|
| GET | `/strategies/` | 獲取策略列表 | ✅ |
| POST | `/strategies/` | 創建新策略 | ✅ |
| GET | `/strategies/{strategy_id}` | 獲取策略詳情 | ✅ |
| PUT | `/strategies/{strategy_id}` | 更新策略 | ✅ |
| DELETE | `/strategies/{strategy_id}` | 刪除策略 | ✅ |
| PATCH | `/strategies/{strategy_id}/status` | 更新策略狀態 | ✅ |
| POST | `/strategies/batch` | 批量操作策略 | ✅ |

### 執行管理端點

| 方法 | 端點 | 描述 | 認證 |
|------|------|------|------|
| POST | `/strategies/{strategy_id}/executions` | 創建執行 | ✅ |
| GET | `/strategies/{strategy_id}/executions` | 獲取執行歷史 | ✅ |
| GET | `/strategies/{strategy_id}/executions/{execution_id}` | 獲取執行詳情 | ✅ |
| POST | `/strategies/{strategy_id}/executions/{execution_id}/stop` | 停止執行 | ✅ |

### 性能分析端點

| 方法 | 端點 | 描述 | 認證 |
|------|------|------|------|
| GET | `/strategies/{strategy_id}/performance` | 獲取性能指標 | ✅ |
| GET | `/strategies/{strategy_id}/performance/report` | 生成性能報告 | ✅ |

## 認證

API v2 使用 JWT (JSON Web Token) 進行認證。請求必須在 Authorization header 中包含有效的 token。

### 請求頭
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### 獲取 Token
```bash
curl -X POST https://api.cbsc.com/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### 響應示例
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 響應格式

所有 API 響應都遵循統一的格式。

### 成功響應
```json
{
  "success": true,
  "data": {
    // 響應數據
  },
  "message": "操作成功",
  "timestamp": "2025-12-17T17:30:00Z",
  "request_id": "req_123456789"
}
```

### 錯誤響應
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "輸入驗證失敗",
    "details": {
      "field": "name",
      "reason": "名稱不能為空"
    }
  },
  "timestamp": "2025-12-17T17:30:00Z",
  "request_id": "req_123456789"
}
```

## 分頁和排序

所有列表端點支持分頁和排序。

### 查詢參數
- `page`: 頁碼（從 1 開始）
- `page_size`: 每頁數量（1-100）
- `sort_by`: 排序字段
- `sort_order`: 排序順序（asc/desc）

### 示例
```bash
curl "https://api.cbsc.com/api/v2/strategies/?page=2&page_size=20&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer <token>"
```

### 響應
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 2,
      "page_size": 20,
      "total": 145,
      "pages": 8
    }
  }
}
```

## 過濾

列表端點支持複雜的過濾條件。

### 通用過濾參數
- `status`: 策略狀態
- `user_id`: 用戶 ID
- `created_after`: 創建時間起始
- `created_before`: 創建時間結束
- `search`: 搜索關鍵詞

### 示例
```bash
curl "https://api.cbsc.com/api/v2/strategies/?status=active&user_id=123&created_after=2025-01-01T00:00:00Z" \
  -H "Authorization: Bearer <token>"
```

## WebSocket v2

WebSocket v2 提供實時更新功能。

### 連接端點
```
wss://api.cbsc.com/api/v2/ws/strategies
```

### 訂閱消息格式
```json
{
  "action": "subscribe",
  "type": "strategy_updates",
  "filters": {
    "user_id": 123,
    "strategy_ids": ["s1", "s2"]
  }
}
```

### 實時消息類型
- `strategy_update`: 策略狀態更新
- `execution_update`: 執行進度更新
- `performance_update`: 性能指標更新
- `system_notification`: 系統通知

## 錯誤代碼

| 代碼 | HTTP狀態 | 描述 |
|------|----------|------|
| VALIDATION_ERROR | 400 | 請求參數驗證失敗 |
| UNAUTHORIZED | 401 | 未授權訪問 |
| FORBIDDEN | 403 | 權限不足 |
| NOT_FOUND | 404 | 資源不存在 |
| CONFLICT | 409 | 資源衝突 |
| RATE_LIMITED | 429 | 請求頻率超限 |
| INTERNAL_ERROR | 500 | 服務器內部錯誤 |
| SERVICE_UNAVAILABLE | 503 | 服務不可用 |

## 速率限制

API v2 實施了速率限制以防止濫用。

- **默認限制**: 1000 請求/分鐘
- **批量操作**: 100 請求/分鐘
- **WebSocket**: 100 消息/秒

### 響應頭
- `X-RateLimit-Limit`: 總限制數
- `X-RateLimit-Remaining`: 剩餘請求數
- `X-RateLimit-Reset`: 重置時間（Unix 時間戳）

## 最佳實踐

### 1. 錯誤處理
- 始終檢查響應的 `success` 字段
- 實現指數退避重試機制
- 記錄 `request_id` 用於調試

### 2. 性能優化
- 使用條件請求（ETag）
- 啟用 HTTP 緩存
- 使用 WebSocket 進行實時更新

### 3. 安全性
- 使用 HTTPS
- 不要在客戶端存儲密鑰
- 定期輪換 token

### 4. 版本管理
- 使用版本化的端點
- 實施向後兼容的變更
- 為新功能使用特性標誌

## SDK 和工具

我們提供以下 SDK 和工具來簡化集成：

- [Python SDK](../sdk/python/)
- [JavaScript SDK](../sdk/javascript/)
- [Postman Collection](../tools/postman/)
- [OpenAPI 規範](../openapi/)

## 遷移指南

如果您正在從 API v0/v1 遷移到 v2，請參考：

- [遷移指南](migration.md)
- [版本比較](version-comparison.md)
- [變更日誌](CHANGELOG.md)

## 支持和聯繫

- **API 文檔**: https://api.cbsc.com/docs
- **狀態頁面**: https://status.cbsc.com
- **技術支持**: api-support@cbsc.com
- **社區論壇**: https://community.cbsc.com

## 更新日誌

### v2.0.0 (2025-12-17)
- ✅ 完全重構的 API 架構
- ✅ WebSocket v2 實時通信
- ✅ 批量操作支持
- ✅ 高級性能分析
- ✅ 增強的安全特性
- ✅ 85% 測試覆蓋率
- ✅ CI/CD 自動化