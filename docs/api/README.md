# CBS-C 策略管理系統 API 文檔

## 概述

CBS-C策略管理系統提供了一套完整的RESTful API，支持策略管理、回測分析、實時交易等功能。

### API版本

- **v1**: 傳統API，保持向後兼容
- **v2**: 新版API，提供增強功能和更好的性能

### 基礎URL

```
開發環境: http://localhost:3004
測試環境: https://api-test.cbsc.example.com
生產環境: https://api.cbsc.example.com
```

### 認證方式

系統使用JWT Bearer Token進行認證：

```http
Authorization: Bearer <your-jwt-token>
```

獲取Token：
```http
POST /api/v2/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

### 響應格式

所有API響應都遵循統一格式：

**成功響應 (2xx)**
```json
{
  "success": true,
  "data": {
    // 響應數據
  },
  "message": "操作成功",
  "timestamp": "2025-12-19T10:00:00Z"
}
```

**錯誤響應 (4xx, 5xx)**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤描述",
    "details": {
      // 詳細錯誤信息
    }
  },
  "timestamp": "2025-12-19T10:00:00Z"
}
```

### 狀態碼說明

| 狀態碼 | 說明 |
|--------|------|
| 200 | 請求成功 |
| 201 | 創建成功 |
| 400 | 請求參數錯誤 |
| 401 | 未授權 |
| 403 | 禁止訪問 |
| 404 | 資源不存在 |
| 409 | 資源衝突 |
| 422 | 數據驗證失敗 |
| 429 | 請求頻率限制 |
| 500 | 服務器內部錯誤 |

### 分頁參數

列表接口支持分頁：

```
?page=1&size=20&sort=created_at&order=desc
```

參數說明：
- `page`: 頁碼（從1開始）
- `size`: 每頁大小（默認20，最大100）
- `sort`: 排序字段
- `order`: 排序方向（asc/desc）

### 過濾參數

多數列表接口支持過濾：

```
?status=active&category=momentum&created_after=2025-01-01
```

## API 文檔結構

### 核心模塊

1. **認證授權** (`/api/v2/auth/`)
   - 用戶登錄/登出
   - Token刷新
   - 多因子認證

2. **策略管理** (`/api/v2/strategies/`)
   - 策略CRUD操作
   - 策略分類管理
   - 策略版本控制

3. **回測分析** (`/api/v2/backtest/`)
   - 回測任務管理
   - 回測報告生成
   - 性能指標分析

4. **實時交易** (`/api/v2/trading/`)
   - 訂單管理
   - 持倉查詢
   - 風險控制

5. **數據服務** (`/api/v2/data/`)
   - 市場數據獲取
   - 歷史數據查詢
   - 數據導出

6. **用戶管理** (`/api/v2/users/`)
   - 用戶信息管理
   - 權限配置
   - 活動記錄

7. **系統監控** (`/api/v2/system/`)
   - 健康檢查
   - 性能指標
   - 日誌查詢

### 工具與SDK

- **OpenAPI規範**: [openapi.yaml](./v2/openapi.yaml)
- **Postman集合**: [cbsc-api.postman_collection.json](./tools/)
- **Python SDK**: [cbsc-python-sdk](../sdk/python/)
- **JavaScript SDK**: [cbsc-js-sdk](../sdk/javascript/)

### 快速開始

1. 獲取訪問令牌
2. 使用令牌訪問API
3. 參考各模塊文檔了解詳情

### 支持與反饋

- 技術支持: api-support@cbsc.example.com
- 問題追蹤: [GitHub Issues](https://github.com/your-org/cbsc-system/issues)
- API狀態: [status.cbsc.example.com](https://status.cbsc.example.com)

---

*最後更新: 2025-12-19*
*版本: v2.0.0*