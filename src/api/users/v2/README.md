# User Management API v2

用戶管理 API v2 提供了完整的用戶管理功能，包括個人資料管理、密碼管理、多因子認證（MFA）、用戶偏好設置等。

## 功能特性

- ✅ 個人資料管理（CRUD）
- ✅ 密碼更改和重置
- ✅ MFA 支持（TOTP）
- ✅ 用戶偏好設置
- ✅ API 密鑰管理（待實現）
- ✅ 活動日誌記錄（待實現）
- ✅ 頭像上傳

## API 端點

### 基礎信息

- **基礎路徑**: `/api/v2/users`
- **認證方式**: Bearer Token (JWT)
- **內容類型**: `application/json`

### 端點列表

#### 1. 個人資料管理

##### 獲取用戶資料
```http
GET /api/v2/users/profile
Authorization: Bearer {token}
```

**響應示例**:
```json
{
  "success": true,
  "data": {
    "id": "user-id",
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "display_name": "Test User",
    "avatar_url": null,
    "phone": "+1234567890",
    "timezone": "UTC",
    "language": "en",
    "theme": "light",
    "is_active": true,
    "is_verified": true,
    "is_premium": false,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "last_login_at": null
  },
  "message": "成功獲取用戶資料",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

##### 更新用戶資料
```http
PUT /api/v2/users/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "Name",
  "phone": "+1234567890",
  "timezone": "Asia/Taipei",
  "language": "zh-TW",
  "theme": "dark"
}
```

##### 上傳頭像
```http
POST /api/v2/users/avatar
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [image file]
```

#### 2. 密碼管理

##### 更改密碼
```http
POST /api/v2/users/change-password
Authorization: Bearer {token}
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

##### 請求密碼重置
```http
POST /api/v2/users/request-password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

##### 確認密碼重置
```http
POST /api/v2/users/confirm-password-reset
Content-Type: application/json

{
  "token": "reset-token-here",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

#### 3. MFA 設置

##### 獲取 MFA 設置
```http
GET /api/v2/users/mfa-settings
Authorization: Bearer {token}
```

##### 設置 TOTP
```http
POST /api/v2/users/mfa/setup-totp
Authorization: Bearer {token}
Content-Type: application/json

{
  "password": "userpassword123"
}
```

**響應示例**:
```json
{
  "success": true,
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "backup_codes": ["code1", "code2", "..."]
  },
  "message": "TOTP 設置初始化成功"
}
```

##### 驗證並啟用 TOTP
```http
POST /api/v2/users/mfa/verify-totp
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "123456"
}
```

##### 禁用 TOTP
```http
POST /api/v2/users/mfa/disable-totp
Authorization: Bearer {token}
Content-Type: application/json

{
  "password": "userpassword123"
}
```

#### 4. 用戶偏好設置

##### 獲取偏好設置
```http
GET /api/v2/users/preferences
Authorization: Bearer {token}
```

##### 更新偏好設置
```http
PUT /api/v2/users/preferences
Authorization: Bearer {token}
Content-Type: application/json

{
  "notifications": {
    "email_enabled": true,
    "sms_enabled": false,
    "push_enabled": true,
    "browser_enabled": true,
    "strategy_alerts": true,
    "performance_reports": true,
    "system_updates": true,
    "security_alerts": true,
    "marketing_emails": false
  },
  "dashboard": {
    "default_layout": "grid",
    "show_welcome": true,
    "default_timeframe": "1D",
    "auto_refresh": true,
    "refresh_interval": 30
  },
  "api": {
    "api_key_enabled": false,
    "rate_limit_per_hour": 100
  }
}
```

#### 5. API 密鑰管理（待實現）

##### 創建 API 密鑰
```http
POST /api/v2/users/api-keys
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My API Key",
  "description": "API key for trading bot",
  "permissions": ["strategies:read", "strategies:write"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

##### 列出 API 密鑰
```http
GET /api/v2/users/api-keys
Authorization: Bearer {token}
```

##### 撤銷 API 密鑰
```http
DELETE /api/v2/users/api-keys/{key_id}
Authorization: Bearer {token}
```

#### 6. 活動日誌（待實現）

##### 獲取活動日誌
```http
GET /api/v2/users/activity-logs?page=1&page_size=20&action_filter=login
Authorization: Bearer {token}
```

## 錯誤響應格式

所有錯誤響應都遵循統一格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤描述",
    "details": {
      "field": "具體錯誤字段"
    }
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

常見錯誤代碼：
- `UNAUTHORIZED`: 未授權訪問
- `FORBIDDEN`: 權限不足
- `NOT_FOUND`: 資源不存在
- `VALIDATION_ERROR`: 請求參數驗證失敗
- `INTERNAL_ERROR`: 內部服務器錯誤

## 安全考慮

1. **認證**: 所有端點都需要有效的 JWT token
2. **授權**: 用戶只能訪問自己的資源
3. **密碼政策**: 密碼必須包含大小寫字母和數字，至少 8 個字符
4. **MFA**: 支援 TOTP 多因子認證
5. **速率限制**: 實施 API 請求速率限制
6. **輸入驗證**: 所有輸入都經過嚴格驗證

## 測試

運行測試：

```bash
# 安裝測試依賴
pip install pytest pytest-asyncio httpx

# 運行所有測試
pytest src/api/users/v2/tests/

# 運行特定測試
pytest src/api/users/v2/tests/test_user_endpoints.py
```

## 開發指南

### 添加新的端點

1. 在 `user_endpoints.py` 中添加新的路由函數
2. 在 `user_service_v2.py` 中實現對應的業務邏輯
3. 在 `user_schemas.py` 中定義請求/響應結構
4. 在 `tests/` 目錄中添加測試用例

### 依賴項

- FastAPI: Web 框架
- Pydantic: 數據驗證
- SQLAlchemy: ORM
- PyOTP: TOTP 支持
- QRCode: 二維碼生成

## 版本歷史

### v2.0.0 (2025-01-01)
- 初始版本
- 基礎用戶資料管理
- 密碼管理功能
- TOTP MFA 支持
- 用戶偏好設置

## 待辦事項

- [ ] 實現 API 密鑰管理
- [ ] 完善活動日誌功能
- [ ] 添加 SMS MFA 支持
- [ ] 實現用戶角色和權限管理
- [ ] 添加數據導出功能
- [ ] 實現 OAuth 社交登錄