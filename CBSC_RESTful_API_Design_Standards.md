# CBSC系統 RESTful API設計規範 v2.0

## 📋 概述

本文檔定義了CBSC量化交易系統的RESTful API設計標準和規範，確保API的一致性、可維護性和易用性。

## 🎯 設計原則

### 1. 資源導向 (Resource-Oriented)
- URI應該代表資源，不是動作
- 使用名詞而非動詞
- 資源名稱使用複數形式

### 2. HTTP語義化 (Semantic HTTP)
- 正確使用HTTP方法 (GET, POST, PUT, DELETE, PATCH)
- 合理使用HTTP狀態碼
- 利用HTTP頭部傳遞元數據

### 3. 統一響應格式 (Consistent Response)
- 標準化的成功/錯誤響應
- 統一的數據結構
- 一致的錯誤處理

### 4. 版本控制 (Versioning)
- API版本通過URL路徑管理
- 向後兼容性保證
- 明確的版本生命週期

## 🏗️ API架構設計

### URL結構規範

```yaml
# 基礎URL格式
https://api.cbsc.com/{version}/{service}/{resource}/{id}/{sub-resource}

# 示例
https://api.cbsc.com/v1/users/123/strategies
https://api.cbsc.com/v1/strategies/456/backtests
https://api.cbsc.com/v1/market-data/hk/stocks
```

### 版本控制策略

```yaml
# URL版本控制 (推薦)
/api/v1/users
/api/v2/users

# 向後兼容規則
- 新增字段: 不影響現有客戶端
- 刪除字段: 需要版本升級
- 修改字段類型: 需要版本升級
- 新增端點: 不影響現有客戶端
- 修改端點: 需要版本升級
```

## 📡 HTTP方法使用規範

### 標準CRUD操作

| 操作 | HTTP方法 | URL路徑 | 描述 |
|------|----------|---------|------|
| 創建 | POST | `/api/v1/{resource}` | 創建新資源 |
| 讀取 | GET | `/api/v1/{resource}` | 獲取資源列表 |
| 讀取 | GET | `/api/v1/{resource}/{id}` | 獲取特定資源 |
| 更新 | PUT | `/api/v1/{resource}/{id}` | 完整更新資源 |
| 部分更新 | PATCH | `/api/v1/{resource}/{id}` | 部分更新資源 |
| 刪除 | DELETE | `/api/v1/{resource}/{id}` | 刪除資源 |

### CBSC業務特定操作

```yaml
# 策略管理
POST   /api/v1/strategies/{id}/backtest     # 執行回測
POST   /api/v1/strategies/{id}/optimize     # 參數優化
POST   /api/v1/strategies/{id}/activate     # 激活策略
POST   /api/v1/strategies/{id}/deactivate   # 停用策略

# 市場數據
GET    /api/v1/market-data/hk/stocks        # 香港股票數據
GET    /api/v1/market-data/cbsc/bull-bear  # CBSC牛熊證數據
POST   /api/v1/market-data/refresh          # 刷新市場數據

# 分析服務
POST   /api/v1/analysis/technical          # 技術分析
POST   /api/v1/analysis/sentiment          # 情緒分析
POST   /api/v1/analysis/risk               # 風險評估
```

## 📊 請求和響應格式

### 請求格式規範

#### Content-Type
```yaml
# JSON格式 (默認)
Content-Type: application/json

# 文件上傳
Content-Type: multipart/form-data

# 表單提交
Content-Type: application/x-www-form-urlencoded
```

#### 請求頭部
```yaml
# 認證
Authorization: Bearer <access_token>

# 內容類型
Content-Type: application/json

# 接受格式
Accept: application/json

# 客戶端信息
User-Agent: CBSC-Client/1.0
X-Client-Version: 1.0.0
X-Request-ID: <unique_request_id>
```

#### 請求體示例
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "roles": ["user"],
  "profile": {
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### 響應格式規範

#### 成功響應格式
```json
{
  "success": true,
  "data": {
    // 具體數據內容
  },
  "message": "操作成功",
  "timestamp": "2025-12-10T10:00:00Z",
  "request_id": "req_123456789",
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### 錯誤響應格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "輸入驗證失敗",
    "details": {
      "field": "email",
      "reason": "郵箱格式不正確"
    },
    "timestamp": "2025-12-10T10:00:00Z",
    "request_id": "req_123456789"
  }
}
```

#### 分頁響應格式
```json
{
  "success": true,
  "data": [
    // 資源列表
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🔢 HTTP狀態碼規範

### 成功狀態碼
| 狀態碼 | 含義 | 使用場景 |
|--------|------|----------|
| 200 | OK | 請求成功，返回數據 |
| 201 | Created | 資源創建成功 |
| 202 | Accepted | 請求已接受，異步處理中 |
| 204 | No Content | 請求成功，無返回內容 |

### 客戶端錯誤狀態碼
| 狀態碼 | 含義 | 使用場景 |
|--------|------|----------|
| 400 | Bad Request | 請求參數錯誤 |
| 401 | Unauthorized | 未認證或認證失敗 |
| 403 | Forbidden | 無權限訪問 |
| 404 | Not Found | 資源不存在 |
| 409 | Conflict | 資源衝突 |
| 422 | Unprocessable Entity | 請求格式正確但語義錯誤 |
| 429 | Too Many Requests | 請求過於頻繁 |

### 服務器錯誤狀態碼
| 狀態碼 | 含義 | 使用場景 |
|--------|------|----------|
| 500 | Internal Server Error | 服務器內部錯誤 |
| 502 | Bad Gateway | 網關錯誤 |
| 503 | Service Unavailable | 服務暫時不可用 |
| 504 | Gateway Timeout | 網關超時 |

## 🏷️ 命名規範

### URL命名規範
```yaml
# 使用小寫字母和連字符
/api/v1/user-profiles
/api/v1/strategy-management

# 避免下劃線
# ❌ 錯誤: /api/v1/user_profiles
# ✅ 正確: /api/v1/user-profiles

# 資源名稱使用複數
# ❌ 錯誤: /api/v1/user
# ✅ 正確: /api/v1/users
```

### 字段命名規範
```json
{
  // 使用snake_case
  "user_id": 123,
  "created_at": "2025-12-10T10:00:00Z",
  "strategy_name": "RSI_Strategy",

  // 布爾值使用is_前綴
  "is_active": true,
  "is_deleted": false,

  // 時間字段包含時區信息
  "last_updated_at": "2025-12-10T10:00:00Z"
}
```

### 錯誤代碼命名規範
```yaml
# 格式: {DOMAIN}_{ERROR_TYPE}
VALIDATION_ERROR
AUTHENTICATION_FAILED
PERMISSION_DENIED
RESOURCE_NOT_FOUND
STRATEGY_NOT_ACTIVE
MARKET_DATA_UNAVAILABLE
```

## 🔍 查詢參數規範

### 分頁參數
```yaml
page: 1              # 頁碼，從1開始
per_page: 20         # 每頁數量，默認20，最大100
sort: created_at     # 排序字段
order: desc          # 排序方向: asc | desc
```

### 過濾參數
```yaml
# 字段過濾
status: active
type: cbsc_strategy

# 日期範圍過濾
created_from: 2025-12-01
created_to: 2025-12-31

# 搜索參數
search: keyword
fields: name,description  # 搜索字段
```

### 字段選擇
```yaml
# 只返回指定字段
fields: id,name,status,created_at

# 排除指定字段
exclude: password_hash,salt
```

## 🔒 安全規範

### 認證機制
```yaml
# JWT Bearer Token
Authorization: Bearer <jwt_token>

# API Key (機器對機器通信)
X-API-Key: <api_key>
```

### 權限控制
```yaml
# 基於角色的訪問控制 (RBAC)
roles: [admin, user, viewer]
permissions: [read, write, delete]

# 資源級權限
can_read: true
can_write: false
can_delete: false
```

### 數據驗證
```yaml
# 輸入驗證
- 必填字段驗證
- 數據類型驗證
- 格式驗證 (email, date等)
- 業務規則驗證

# 輸出過濾
- 敏感數據過濾
- 權限字段過濾
- 脫敏處理
```

## 📈 性能規範

### 響應時間要求
```yaml
# 簡單查詢: < 100ms
# 複雜查詢: < 500ms
# 批量操作: < 2000ms
# 文件上傳: < 5000ms
```

### 緩存策略
```yaml
# HTTP緩存頭
Cache-Control: public, max-age=3600
ETag: "abc123"
Last-Modified: "Wed, 10 Dec 2025 10:00:00 GMT"

# 業務緩存
- 用戶信息: 5分鐘
- 市場數據: 1分鐘
- 配置信息: 30分鐘
```

### 限流規範
```yaml
# 全局限流
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000

# 用戶級限流
- 普通用戶: 100 requests/minute
- 高級用戶: 500 requests/minute
- 管理員: 1000 requests/minute
```

## 📝 API文檔規範

### OpenAPI 3.0規範
```yaml
# 基本信息
info:
  title: CBSC System API
  version: 2.0.0
  description: CBSC量化交易系統API
  contact:
    name: API Support
    email: api-support@cbsc.com

# 路徑定義
paths:
  /api/v1/users:
    get:
      summary: 獲取用戶列表
      description: 返回用戶列表，支持分頁和過濾
      tags:
        - Users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: 成功返回用戶列表
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
```

### 文檔生成
- 自動生成OpenAPI文檔
- 提供交互式API測試界面
- 包含完整的示例代碼
- 多語言客戶端SDK生成

## 🧪 測試規範

### API測試類型
```yaml
# 單元測試
- 端點功能測試
- 參數驗證測試
- 錯誤處理測試

# 集成測試
- 服務間通信測試
- 數據庫集成測試
- 認證授權測試

# 端到端測試
- 完整業務流程測試
- 性能測試
- 安全測試
```

### 測試數據管理
```yaml
# 測試環境隔離
- 獨立的測試數據庫
- 測試數據自動生成
- 測試後數據清理

# 測試用例管理
- 測試用例版本控制
- 自動化測試執行
- 測試覆蓋率報告
```

## 🚀 實施指南

### 開發流程
1. **API設計**: 使用OpenAPI規範設計API
2. **代碼實現**: 按照規範實現API端點
3. **單元測試**: 編寫完整的單元測試
4. **集成測試**: 進行服務集成測試
5. **文檔生成**: 自動生成API文檔
6. **代碼審查**: 團隊代碼審查
7. **部署上線**: CI/CD自動部署

### 質量保證
```yaml
# 代碼質量
- ESLint/Python flake8檢查
- 代碼格式化
- 類型檢查

# API質量
- 響應時間監控
- 錯誤率監控
- 可用性監控

# 文檔質量
- 文檔完整性檢查
- 示例代碼驗證
- 用戶反饋收集
```

---

**文檔版本**: v2.0
**最後更新**: 2025-12-10
**審核狀態**: 已審核
**適用範圍**: CBSC系統所有API服務