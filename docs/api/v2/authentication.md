# 認證授權 API v2

## 概述

認證模塊提供用戶身份驗證、授權管理和會話控制功能。

### 端點列表

- [用戶登錄](#用戶登錄)
- [用戶登出](#用戶登出)
- [刷新令牌](#刷新令牌)
- [獲取當前用戶](#獲取當前用戶)
- [修改密碼](#修改密碼)
- [啟用MFA](#啟用mfa)
- [驗證MFA](#驗證mfa)

## 用戶登錄

用戶使用用戶名和密碼進行身份驗證。

```http
POST /api/v2/auth/login
```

### 請求體

```json
{
  "username": "string",
  "password": "string",
  "mfa_code": "string",  // 可選，如果啟用了MFA
  "remember_me": false   // 可選，是否記住登錄狀態
}
```

### 響應

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "roles": ["trader"],
      "permissions": ["strategy:read", "strategy:write"]
    }
  },
  "message": "登錄成功"
}
```

### 錯誤響應

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用戶名或密碼錯誤"
  }
}
```

### 狀態碼

- `200`: 登錄成功
- `401`: 認證失敗
- `403`: 帳戶被禁用
- `422`: 請求參數錯誤

## 用戶登出

使當前訪問令牌失效。

```http
POST /api/v2/auth/logout
```

### 請求頭

```http
Authorization: Bearer <access_token>
```

### 響應

```json
{
  "success": true,
  "message": "登出成功"
}
```

### 狀態碼

- `200`: 登出成功
- `401`: 未授權

## 刷新令牌

使用刷新令牌獲取新的訪問令牌。

```http
POST /api/v2/auth/refresh
```

### 請求體

```json
{
  "refresh_token": "string"
}
```

### 響應

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600
  }
}
```

### 狀態碼

- `200`: 刷新成功
- `401`: 刷新令牌無效或已過期

## 獲取當前用戶

獲取當前認證用戶的詳細信息。

```http
GET /api/v2/auth/me
```

### 請求頭

```http
Authorization: Bearer <access_token>
```

### 響應

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "avatar_url": "https://example.com/avatars/john.jpg",
    "roles": ["trader"],
    "permissions": [
      "strategy:read",
      "strategy:write",
      "backtest:execute"
    ],
    "preferences": {
      "language": "zh-CN",
      "timezone": "Asia/Shanghai",
      "theme": "dark"
    },
    "last_login": "2025-12-19T09:30:00Z",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

## 修改密碼

修改當前用戶的密碼。

```http
PUT /api/v2/auth/password
```

### 請求頭

```http
Authorization: Bearer <access_token>
```

### 請求體

```json
{
  "current_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

### 響應

```json
{
  "success": true,
  "message": "密碼修改成功"
}
```

### 驗證規則

- `current_password`: 必須與當前密碼匹配
- `new_password`: 最少8位，包含大小寫字母、數字和特殊字符
- `confirm_password`: 必須與new_password一致

## 啟用MFA

為用戶帳戶啟用多因子認證。

```http
POST /api/v2/auth/mfa/enable
```

### 請求頭

```http
Authorization: Bearer <access_token>
```

### 響應

```json
{
  "success": true,
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",  // 用於設置驗證器應用
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "backup_codes": [
      "12345678",
      "87654321",
      "11223344"
    ]
  },
  "message": "請使用驗證器應用掃描二維碼"
}
```

## 驗證MFA

完成MFA設置或在登錄時提供MFA代碼。

```http
POST /api/v2/auth/mfa/verify
```

### 請求體

```json
{
  "code": "string",      // 6位數字代碼
  "backup_code": "string" // 可選，使用備用代碼
}
```

### 響應

```json
{
  "success": true,
  "message": "MFA驗證成功"
}
```

## 禁用MFA

禁用用戶的MFA功能。

```http
POST /api/v2/auth/mfa/disable
```

### 請求頭

```http
Authorization: Bearer <access_token>
```

### 請求體

```json
{
  "password": "string",
  "code": "string"  // 當前MFA代碼
}
```

### 響應

```json
{
  "success": true,
  "message": "MFA已禁用"
}
```

## 會話管理

查看和管理當前用戶的所有活動會話。

### 獲取會話列表

```http
GET /api/v2/auth/sessions
```

### 響應

```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "sess_123",
        "device": "Chrome on Windows",
        "ip_address": "192.168.1.100",
        "location": "Shanghai, China",
        "created_at": "2025-12-19T09:00:00Z",
        "last_active": "2025-12-19T10:30:00Z",
        "is_current": true
      }
    ]
  }
}
```

### 撤銷會話

```http
DELETE /api/v2/auth/sessions/{session_id}
```

### 響應

```json
{
  "success": true,
  "message": "會話已撤銷"
}
```

## 錯誤代碼

| 錯誤代碼 | 說明 |
|---------|------|
| `INVALID_CREDENTIALS` | 用戶名或密碼錯誤 |
| `ACCOUNT_DISABLED` | 帳戶已被禁用 |
| `ACCOUNT_LOCKED` | 帳戶已被鎖定 |
| `TOKEN_EXPIRED` | 訪問令牌已過期 |
| `TOKEN_INVALID` | 訪問令牌無效 |
| `MFA_REQUIRED` | 需要多因子認證 |
| `MFA_INVALID` | MFA代碼錯誤 |
| `PASSWORD_WEAK` | 密碼強度不足 |
| `RATE_LIMIT_EXCEEDED` | 請求頻率超限 |

## 安全建議

1. 使用HTTPS進行所有API調用
2. 定期輪換密碼
3. 啟用MFA增強安全性
4. 不要在客戶端存儲刷新令牌
5. 使用短期有效的訪問令牌
6. 監控異常登錄活動
7. 定期檢查活動會話