# Authentication and User Management Services

## Overview

This document describes the comprehensive authentication and user management services for the CBSC trading system. These services provide enterprise-grade security features including JWT authentication, role-based access control, session management, password reset workflows, and comprehensive audit logging.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Layer                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Endpoints (backend/api/auth.py)                     │
│  ├── Login/Logout                                           │
│  ├── Token Refresh                                          │
│  ├── User Registration                                      │
│  └── Password Reset                                         │
├─────────────────────────────────────────────────────────────┤
│  Services Layer                                              │
│  ├── RBAC Service (rbac_service.py)                         │
│  ├── Session Service (session_service.py)                   │
│  ├── Password Reset Service (password_reset_service.py)     │
│  └── Audit Service (audit_service.py)                       │
├─────────────────────────────────────────────────────────────┤
│  Utilities                                                   │
│  ├── JWT Token Management (utils/auth.py)                   │
│  ├── Password Hashing (Argon2)                              │
│  └── Rate Limiting Middleware                               │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                  │
│  ├── User Model (unified_models.py)                         │
│  ├── Role Model                                             │
│  ├── Session Model                                          │
│  └── Audit Log Model                                        │
└─────────────────────────────────────────────────────────────┘
```

## Services

### 1. RBAC Service (`rbac_service.py`)

Role-Based Access Control with hierarchical permissions.

#### Features
- Predefined role definitions (super_admin, admin, trader, analyst, developer, viewer)
- Permission inheritance and aggregation
- Resource-action based permissions
- Decorator for endpoint protection
- Effective permission calculation with caching

#### Role Definitions

```python
ROLE_DEFINITIONS = {
    "super_admin": Full system access
    "admin": User and strategy management
    "trader": Trading and execution
    "analyst": Read-only analysis access
    "developer": API and webhook access
    "viewer": Limited read-only access
}
```

#### Usage Examples

```python
from services.rbac_service import rbac_service, require_permission

# Check permissions programmatically
has_perm = rbac_service.has_permission(
    user_roles=['admin', 'trader'],
    resource='strategies',
    action='execute'
)

# Protect endpoints with decorator
@router.post("/strategies/{id}/execute")
@require_permission("strategies", "execute")
async def execute_strategy(id: int, current_user: User = Depends(get_current_user)):
    ...
```

#### API Reference

```python
# Check single permission
rbac_service.has_permission(user_roles, resource, action) -> bool

# Check multiple permissions (any)
rbac_service.has_any_permission(user_roles, resource, actions) -> bool

# Check multiple permissions (all)
rbac_service.has_all_permissions(user_roles, resource, actions) -> bool

# Get effective permissions for user
rbac_service.get_effective_permissions(role_names) -> Dict[str, Set[str]]
```

---

### 2. Session Service (`session_service.py`)

User session and device management with security monitoring.

#### Features
- Session creation and lifecycle management
- Device fingerprinting using user agent parsing
- Suspicious activity detection (new devices)
- Session refresh and revocation
- Multi-session management with configurable limits
- Login attempt tracking for brute force detection

#### Device Information

```python
DeviceInfo(
    device_type: DeviceType,  # desktop, mobile, tablet
    os_family: OSFamily,      # windows, macos, linux, android, ios
    browser: str,             # Chrome, Firefox, Safari, Edge, Opera
    ip_address: str,
    is_trusted: bool,
    last_seen: datetime
)
```

#### Usage Examples

```python
from services.session_service import session_manager

# Create session on login
session_data = await session_manager.create_session(
    user_id=123,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    remember_me=True
)

# Get active sessions for user
sessions = await session_manager.get_user_sessions(user_id=123)

# Revoke specific session
await session_manager.revoke_session(user_id=123, session_id="abc123")

# Revoke all sessions (except current)
await session_manager.revoke_all_sessions(
    user_id=123,
    except_session_id="current_session_id"
)

# Refresh session using refresh token
new_tokens = await session_manager.refresh_session(refresh_token="xyz789")
```

#### Security Features

1. **Device Fingerprinting**
   - Hash-based device identification
   - Detects new devices for existing users
   - Trusted device management

2. **Suspicious Activity Detection**
   - New device alerts
   - Location-based anomalies (future enhancement)
   - Behavioral patterns (future enhancement)

3. **Brute Force Protection**
   - Tracks failed login attempts per IP
   - Warns on >5 failed attempts in 15 minutes
   - Integrates with rate limiting middleware

---

### 3. Password Reset Service (`password_reset_service.py`)

Password reset and email verification workflows.

#### Features
- Secure token generation with expiration
- Email-based password reset
- Email verification for new accounts
- Rate limiting for reset requests
- SMTP email sending with HTML templates
- Token validation and usage tracking

#### Workflow

```
1. User requests password reset
   └── Service generates secure token (15 min expiry)
   └── Sends email with reset link

2. User clicks reset link
   └── Service validates token
   └── Allows password change

3. Token is marked as used
   └── Cannot be reused
```

#### Usage Examples

```python
from services.password_reset_service import password_reset_service

# Request password reset
result = await password_reset_service.request_password_reset(
    email="user@example.com",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Validate reset token
is_valid = await password_reset_service.validate_reset_token(
    token="abc123...",
    email="user@example.com"
)

# Reset password with token
result = await password_reset_service.reset_password(
    token="abc123...",
    email="user@example.com",
    new_password="SecureNewPassword123!"
)

# Send email verification
await password_reset_service.send_email_verification(
    email="newuser@example.com",
    user_id=123,
    username="newuser"
)

# Verify email
result = await password_reset_service.verify_email(
    token="verification_token..."
)
```

#### Configuration

```python
# Email settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "noreply@cbsc.com"
SMTP_FROM = "CBSC System <noreply@cbsc.com>"

# Token settings
RESET_TOKEN_EXPIRE_MINUTES = 15
VERIFICATION_TOKEN_EXPIRE_HOURS = 24
MAX_RESET_ATTEMPTS_PER_HOUR = 3
```

#### Email Templates

The service includes HTML email templates for:
- Password reset emails
- Email verification emails
- Password change confirmation

---

### 4. Audit Service (`audit_service.py`)

Comprehensive security audit logging for compliance and monitoring.

#### Features
- Structured event logging with severity levels
- Event type classification (auth, authz, data, security)
- Sensitive data masking
- User activity tracking
- Failed login attempt monitoring
- Audit report generation
- Security threshold checking
- Configurable retention policy

#### Event Types

```python
# Authentication Events
- AUTH_LOGIN_SUCCESS
- AUTH_LOGIN_FAILED
- AUTH_LOGOUT
- AUTH_PASSWORD_CHANGE
- AUTH_MFA_ENABLED/DISABLED
- AUTH_SESSION_CREATED/REVOKED

# Authorization Events
- AUTHZ_ROLE_GRANTED/REVOKED
- AUTHZ_PERMISSION_GRANTED/REVOKED

# User Management Events
- USER_CREATED/UPDATED/DELETED
- USER_SUSPENDED/UNSUSPENDED

# Data Access Events
- DATA_ACCESS
- DATA_EXPORT
- DATA_DELETE
- DATA_MODIFY

# Security Events
- SECURITY_ALERT
- SECURITY_INCIDENT
- SECURITY_BRUTE_FORCE
- SECURITY_SUSPICIOUS_ACTIVITY
```

#### Usage Examples

```python
from services.audit_service import audit_logger, AuditEventType, EventSeverity

# Log authentication event
await audit_logger.log_auth_event(
    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    user_id=123,
    username="john_doe",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    success=True
)

# Log authorization change
await audit_logger.log_authorization_event(
    event_type=AuditEventType.AUTHZ_ROLE_GRANTED,
    admin_user_id=1,
    admin_username="admin",
    target_user_id=123,
    target_username="john_doe",
    role="trader",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Log data access
await audit_logger.log_data_access(
    user_id=123,
    username="john_doe",
    resource_type="strategy",
    resource_id="456",
    action="read",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Log security event
await audit_logger.log_security_event(
    event_type=AuditEventType.SECURITY_BRUTE_FORCE,
    severity=EventSeverity.CRITICAL,
    description="Multiple failed login attempts detected",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    details={"attempts": 15, "timeframe": "5 minutes"}
)

# Query audit events
user_events = await audit_logger.get_user_events(user_id=123, limit=100)
failed_logins = await audit_logger.get_events_by_type(AuditEventType.AUTH_LOGIN_FAILED)

# Generate audit report
report = await audit_logger.generate_audit_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)

# Check for security violations
alerts = await audit_logger.check_security_thresholds()
```

#### Audit Event Structure

```python
AuditEvent(
    event_type: AuditEventType,
    user_id: Optional[int],
    username: Optional[str],
    ip_address: str,
    user_agent: str,
    timestamp: datetime,
    severity: EventSeverity,
    resource_type: Optional[str],
    resource_id: Optional[str],
    success: bool,
    details: Dict[str, Any],
    metadata: Dict[str, Any]
)
```

#### Security Features

1. **Sensitive Data Masking**
   - Automatically masks passwords, tokens, keys
   - Configurable sensitive field patterns
   - Preserves audit trail while protecting data

2. **PII Hashing**
   - Hash personally identifiable information
   - Maintains traceability without storing raw data

3. **Retention Policy**
   - Configurable retention period (default: 90 days)
   - Automatic cleanup of old events
   - Manual cleanup available

---

## Integration Guide

### Setting Up Dependencies

```python
# Install required packages
pip install fastapi uvicorn sqlalchemy pydantic pyjwt argon2-cffi

# Email support
pip install aiosmtplib email-validator
```

### Configuration

Create `.env` file:

```env
# JWT Settings
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Settings
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true

# Session Settings
SESSION_EXPIRE_MINUTES=60
MAX_SESSIONS_PER_USER=5

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@cbsc.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=CBSC System <noreply@cbsc.com>

# Audit Settings
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_ASYNC=true
AUDIT_LOG_SENSITIVE_DATA_MASKING=true
```

### Database Models

Ensure these models exist in `models/unified_models.py`:

```python
class User(Base):
    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool
    email_verified: bool
    roles: List[Role]

class Role(Base):
    id: int
    name: str
    permissions: Dict[str, List[str]]

class MfaDevice(Base):
    id: int
    user_id: int
    device_type: str
    secret: str
    is_verified: bool

class UserActivity(Base):
    id: int
    user_id: int
    action: str
    ip_address: str
    user_agent: str
    metadata: JSON
    timestamp: datetime
```

### API Endpoints Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from services.rbac_service import require_permission
from services.session_service import session_manager
from services.audit_service import audit_logger, AuditEventType

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login")
async def login(credentials: LoginRequest, request: Request):
    """User login with session creation"""
    # Authenticate user
    user = await authenticate_user(credentials.username, credentials.password)

    # Create session
    session_data = await session_manager.create_session(
        user_id=user.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        remember_me=credentials.remember_me
    )

    # Log successful login
    await audit_logger.log_auth_event(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        success=True
    )

    return session_data

@router.get("/users/me/sessions")
async def get_my_sessions(current_user: User = Depends(get_current_user)):
    """Get current user's active sessions"""
    return await session_manager.get_user_sessions(current_user.id)

@router.post("/users/me/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke a specific session"""
    success = await session_manager.revoke_session(
        user_id=current_user.id,
        session_id=session_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session revoked"}
```

---

## Security Best Practices

### 1. Password Security
- Use Argon2id for password hashing (already implemented)
- Enforce strong password requirements
- Implement password history checking
- Force password change on first login for new users

### 2. Token Security
- Use RS256 algorithm for JWT in production (requires key pair)
- Implement token rotation for refresh tokens
- Store refresh tokens securely (httpOnly cookies)
- Invalidate tokens on password change

### 3. Session Security
- Implement session fixation prevention
- Use secure, httpOnly cookies
- Implement CSRF protection
- Limit session lifetime

### 4. Rate Limiting
- Apply to all authentication endpoints
- Use stricter limits for sensitive operations
- Implement IP-based blocking for repeated failures
- Use Redis for distributed rate limiting

### 5. Audit Logging
- Log all security-relevant events
- Use tamper-evident logging
- Implement log aggregation and monitoring
- Regular audit log review process

### 6. Email Security
- Use SPF, DKIM, DMARC records
- Implement email verification
- Use transactional email service in production
- Include security headers in emails

---

## Testing

### Unit Tests

```python
import pytest
from services.rbac_service import rbac_service

def test_admin_has_full_access():
    """Test admin role has all permissions"""
    assert rbac_service.has_permission(['admin'], 'users', 'create')
    assert rbac_service.has_permission(['admin'], 'strategies', 'delete')
    assert rbac_service.has_permission(['admin'], 'api_keys', 'manage')

def test_viewer_limited_access():
    """Test viewer role has limited permissions"""
    assert rbac_service.has_permission(['viewer'], 'strategies', 'read')
    assert not rbac_service.has_permission(['viewer'], 'strategies', 'delete')
    assert not rbac_service.has_permission(['viewer'], 'users', 'create')

def test_role_inheritance():
    """Test permission inheritance"""
    perms = rbac_service.get_effective_permissions(['admin'])
    assert 'users' in perms
    assert 'create' in perms['users']
```

### Integration Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient):
    """Test complete login flow"""
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]

    # Access protected endpoint
    headers = {"Authorization": f"Bearer {data['data']['access_token']}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Review and update environment variables
- [ ] Generate secure JWT secret keys
- [ ] Configure SMTP settings for email
- [ ] Set up Redis for production caching
- [ ] Configure database backups
- [ ] Set up log aggregation (ELK, CloudWatch, etc.)

### Security Review
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Configure CORS properly
- [ ] Set up API rate limiting
- [ ] Enable security headers (CSP, HSTS, etc.)
- [ ] Configure WAF rules
- [ ] Set up intrusion detection

### Monitoring
- [ ] Configure authentication failure alerts
- [ ] Set up brute force detection monitoring
- [ ] Configure audit log monitoring
- [ ] Set up performance monitoring
- [ ] Configure uptime monitoring

### Compliance
- [ ] Review audit log retention policy
- [ ] Configure data export for compliance
- [ ] Set up regular security audits
- [ ] Document data handling procedures
- [ ] Create incident response plan

---

## Troubleshooting

### Common Issues

#### 1. JWT Token Not Valid
```
Error: "Could not validate credentials"
Solution:
- Check JWT_SECRET_KEY is consistent
- Verify token hasn't expired
- Check token format in Authorization header
```

#### 2. Email Not Sending
```
Error: "Failed to send email"
Solution:
- Verify SMTP settings
- Check app-specific password for Gmail
- Ensure port 587 is open
- Check firewall rules
```

#### 3. Session Not Found
```
Error: "Session not found or expired"
Solution:
- Check session expiry time
- Verify session storage (Redis/in-memory)
- Check session ID format
```

#### 4. Permission Denied
```
Error: "Permission denied"
Solution:
- Verify user roles in database
- Check role definitions in RBAC service
- Review permission decorator configuration
```

---

## Future Enhancements

1. **Multi-Factor Authentication (MFA)**
   - TOTP (Google Authenticator)
   - SMS-based verification
   - Biometric authentication

2. **OAuth 2.0 / OpenID Connect**
   - Social login (Google, GitHub)
   - Enterprise SSO (SAML)
   - Single sign-on

3. **Advanced Security Features**
   - Device geolocation tracking
   - Behavioral biometrics
   - Anomaly detection with ML
   - Risk-based authentication

4. **Compliance Features**
   - GDPR data export/delete
   - SOC 2 reporting
   - HIPAA compliance mode
   - Audit log archiving

5. **Performance Optimization**
   - Distributed session storage
   - Cached permission checks
   - Batch audit log writes
   - Query optimization

---

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [Argon2 RFC](https://tools.ietf.org/html/html/rfc9106.html)

---

*Document Version: 1.0*
*Last Updated: 2025-12-25*
*Maintained by: CBSC Development Team*
