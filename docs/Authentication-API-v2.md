# Authentication API v2 Documentation
# 認證 API v2 文檔

## Overview
This document describes the enhanced Authentication API v2 for the CBSC Strategy Management System. This API provides secure authentication with multi-factor authentication (MFA), JWT token management, device tracking, and comprehensive security features.

本文檔描述了 CBSC 策略管理系統的增強版認證 API v2。此 API 提供帶有多因子認證 (MFA)、JWT 令牌管理、設備跟踪和綜合安全功能的安全認證。

## Features
- **Multi-Factor Authentication (MFA)**: TOTP, email, and SMS support
- **JWT Access & Refresh Tokens**: Secure token-based authentication
- **Device Management**: Track and manage trusted devices
- **Rate Limiting**: Prevent brute force attacks
- **Password Strength Validation**: Enforce strong password policies
- **Audit Logging**: Comprehensive security event tracking
- **API Key Support**: Programmatic access with API keys

## Features
- **多因子認證 (MFA)**：支持 TOTP、郵件和短信
- **JWT 訪問和刷新令牌**：基於令牌的安全認證
- **設備管理**：跟踪和管理信任設備
- **速率限制**：防止暴力攻擊
- **密碼強度驗證**：強制執行強密碼策略
- **審計日誌**：全面的安全事件跟踪
- **API 密鑰支持**：通過 API 密鑰進行編程訪問

## Base URL
```
https://your-domain.com/api/v2/auth
```

## Authentication Flow
### 1. Basic Login (Without MFA)
```bash
POST /api/v2/auth/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "SecurePass123!",
    "device_fingerprint": "unique-device-id",
    "device_name": "My Laptop"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "requires_mfa": false,
    "token_info": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 1800,
        "refresh_expires_in": 604800
    }
}
```

### 2. Login with MFA
If MFA is enabled, the login response will include MFA challenge:

如果啟用了 MFA，登入響應將包含 MFA 挑戰：
```json
{
    "success": true,
    "message": "Please complete MFA verification",
    "requires_mfa": true,
    "mfa_types": ["totp"],
    "mfa_challenge_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Complete MFA Verification
```bash
POST /api/v2/auth/mfa/verify
Content-Type: application/json

{
    "mfa_challenge_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "code": "123456"
}
```

**Or using backup code:**
```bash
{
    "mfa_challenge_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "backup_code": "ABCD1234"
}
```

## Endpoints

### Login
POST /api/v2/auth/login

Authenticates a user with username/email and password.

使用用戶名/郵件和密碼認證用戶。

**Request Body:**
- `username` (string, required): Username or email
- `password` (string, required): User password
- `device_fingerprint` (string, optional): Unique device identifier
- `device_name` (string, optional): Human-readable device name

**Response:** LoginResponse object

### MFA Verification
POST /api/v2/auth/mfa/verify

Verifies MFA code to complete login.

驗證 MFA 代碼以完成登入。

**Request Body:**
- `mfa_challenge_token` (string, required): Token from login response
- `code` (string, optional): 6-digit MFA code
- `backup_code` (string, optional): 8-character backup code

**Response:** LoginResponse object with tokens

### Register
POST /api/v2/auth/register

Creates a new user account.

創建新的用戶帳戶。

**Request Body:**
- `username` (string, required): Username (3-50 chars, alphanumeric only)
- `email` (string, required): Valid email address
- `password` (string, required): Password (min 8 chars, complex)
- `confirm_password` (string, required): Password confirmation
- `full_name` (string, optional): Full name
- `accept_terms` (boolean, required): Accept terms and conditions

**Response:** RegisterResponse object

### Token Refresh
POST /api/v2/auth/refresh

Refreshes an expired access token using a refresh token.

使用刷新令牌刷新過期的訪問令牌。

**Request Body:**
- `refresh_token` (string, required): Valid refresh token
- `device_fingerprint` (string, required): Device fingerprint

**Response:** TokenRefreshResponse object

### Logout
POST /api/v2/auth/logout

Securely logs out a user and revokes all tokens.

安全地登出用戶並撤銷所有令牌。

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** LogoutResponse object

### Change Password
POST /api/v2/auth/change-password

Changes user password.

更改用戶密碼。

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
- `old_password` (string, required): Current password
- `new_password` (string, required): New password
- `confirm_password` (string, required): New password confirmation

**Response:** AuthResponse object

### Setup MFA
POST /api/v2/auth/mfa/setup

Sets up multi-factor authentication for a user.

為用戶設置多因子認證。

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
- `mfa_type` (MFAType, required): Type of MFA (totp, email, sms)
- `email` (string, optional): Email for email MFA
- `phone` (string, optional): Phone number for SMS MFA

**Response:** MFASetupResponse object

### Get Profile
GET /api/v2/auth/me

Gets current user profile information.

獲取當前用戶資料信息。

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** UserProfile object

## Device Fingerprinting

The API uses device fingerprinting to enhance security. Include a unique device identifier in login requests to track devices:

API 使用設備指紋識別來增強安全性。在登入請求中包含唯一的設備標識符來跟踪設備：

```javascript
// Example device fingerprint generation
const generateDeviceFingerprint = () => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);

    const fingerprint = btoa(
        navigator.userAgent +
        navigator.language +
        screen.width + screen.height +
        canvas.toDataURL()
    );

    return fingerprint.replace(/[^a-zA-Z0-9]/g, '').substring(0, 32);
};
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

API 實施速率限制以防止濫用：

- **Login attempts**: 5 attempts per 15 minutes per IP
- **Login attempts per user**: 10 attempts per hour
- **MFA attempts**: 3 attempts per challenge
- **Password reset**: 3 requests per hour

## Security Best Practices

### For Clients
1. **Always use HTTPS**: All API calls must be over HTTPS
2. **Validate SSL certificates**: Never disable certificate validation
3. **Store tokens securely**: Use secure storage mechanisms
4. **Implement token refresh**: Refresh tokens before expiration
5. **Handle errors gracefully**: Don't expose error details to users

### For Servers
1. **Rotate secrets regularly**: Change JWT secrets periodically
2. **Monitor audit logs**: Review security events regularly
3. **Implement IP whitelisting**: Restrict API access by IP
4. **Use short-lived access tokens**: 30 minutes recommended
5. **Revoke tokens on logout**: Ensure proper token cleanup

## Error Handling

The API returns standard HTTP status codes with detailed error messages:

API 返回標準 HTTP 狀態碼和詳細錯誤消息：

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Password must be at least 8 characters long",
        "details": {
            "field": "password",
            "reason": "min_length"
        }
    },
    "timestamp": "2025-12-18T10:30:00Z"
}
```

## Common Error Codes

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid credentials or token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## SDK Examples

### Python
```python
import requests

class AuthClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, username, password, device_fp=None):
        response = self.session.post(
            f"{self.base_url}/login",
            json={
                "username": username,
                "password": password,
                "device_fingerprint": device_fp
            }
        )

        if response.json().get("requires_mfa"):
            # Handle MFA challenge
            return self.complete_mfa(response.json()["mfa_challenge_token"])

        # Set authorization header for future requests
        token = response.json()["token_info"]["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

        return response.json()

    def refresh_token(self, refresh_token, device_fp):
        response = self.session.post(
            f"{self.base_url}/refresh",
            json={
                "refresh_token": refresh_token,
                "device_fingerprint": device_fp
            }
        )

        if response.status_code == 200:
            token = response.json()["token_info"]["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        return response.json()
```

### JavaScript
```javascript
class AuthAPI {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.token = null;
    }

    async login(username, password, deviceFingerprint) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                device_fingerprint: deviceFingerprint
            })
        });

        const data = await response.json();

        if (data.requires_mfa) {
            return await this.verifyMFA(data.mfa_challenge_token);
        }

        this.token = data.token_info.access_token;
        return data;
    }

    async verifyMFA(challengeToken, code) {
        const response = await fetch(`${this.baseURL}/mfa/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mfa_challenge_token: challengeToken,
                code: code
            })
        });

        const data = await response.json();
        this.token = data.token_info.access_token;
        return data;
    }

    async authenticatedFetch(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            ...options.headers
        };

        return fetch(url, {
            ...options,
            headers
        });
    }
}
```

## Testing

Run the test suite to verify API functionality:

運行測試套件以驗證 API 功能：

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest src/api/auth/test_auth_v2.py -v
```

## Migration

To migrate from v1 to v2 authentication:

從 v1 遷移到 v2 認證：

1. Run database migration:
```bash
python src/migrations/scripts/execute_migration.py 004_create_auth_v2_tables.sql
```

2. Update client code to use v2 endpoints
3. Implement device fingerprinting
4. Enable MFA for enhanced security

## Support

For support or questions about the Authentication API v2:

關於認證 API v2 的支持或問題：

- Create an issue in the project repository
- Email: support@cbsc.com
- Documentation: https://docs.cbsc.com/auth-v2