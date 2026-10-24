---
status: ready
priority: p1
issue_id: "002"
tags: [security, authentication, websocket, code-review]
dependencies: []
---

# Problem Statement

WebSocket server in `websocket_server.py` lacks authentication and authorization mechanisms, exposing real-time market data endpoints to unauthorized access and potential security breaches.

# Findings

## Security Analysis Results

**Critical security gap in WebSocket connection handling:**
- No authentication required for WebSocket connections
- No rate limiting on connection attempts
- No input validation for incoming messages
- No session management or token validation
- Missing CORS policies and security headers

### Root Cause Analysis
- WebSocket endpoint `/ws` accepts connections without authentication
- No middleware for request validation
- Direct access to sensitive market data streams
- Missing connection lifecycle management

### Attack Vectors
1. **Unauthorized Data Access**: Anyone can connect and receive real-time market data
2. **Connection Flooding**: No rate limiting allows DoS attacks
3. **Message Injection**: No validation of incoming WebSocket messages
4. **Session Hijacking**: No session management or token validation

### Impact Assessment
- **Severity**: CRITICAL (9.0/10)
- **Exploitability**: HIGH
- **Impact**: Data breach, system abuse, potential market manipulation
- **Scope**: All WebSocket-connected clients and data streams

### Affected Files
- `simplified_system/src/realtime/websocket_server.py` (lines 160-180)
- WebSocket endpoint handling and connection management
- Real-time data broadcasting mechanisms

# Proposed Solutions

## Solution 1: JWT-based WebSocket Authentication (Recommended)

**Description:** Implement JWT token validation for WebSocket connections

**Implementation:**
```python
import jwt
from datetime import datetime, timedelta
from fastapi import WebSocket, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class WebSocketAuthenticator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=24)

    def generate_token(self, user_id: str, permissions: List[str]) -> str:
        """Generate JWT token for WebSocket authentication."""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# WebSocket authentication middleware
@self.app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extract token from query parameter or header
    token = websocket.query_params.get('token')
    if not token:
        token = websocket.headers.get('authorization', '').replace('Bearer ', '')

    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Validate token
    try:
        payload = self.authenticator.validate_token(token)
        user_id = payload['user_id']
        permissions = payload['permissions']

        # Check permissions for real-time data access
        if 'realtime_data' not in permissions:
            await websocket.close(code=4003, reason="Insufficient permissions")
            return

    except HTTPException:
        await websocket.close(code=4001, reason="Invalid authentication")
        return

    # Accept connection with user context
    await websocket.accept()

    # Store user context with connection
    connection_context = {
        'user_id': user_id,
        'permissions': permissions,
        'connected_at': datetime.now(),
        'subscription_filters': {}
    }

    self.connection_manager.add_connection(websocket, connection_context)
```

**Pros:**
- ✅ Industry-standard authentication
- ✅ Stateless token validation
- ✅ Built-in expiration handling
- ✅ Permission-based access control
- ✅ Easy integration with existing auth systems

**Cons:**
- ❌ Requires secret key management
- ❌ Token revocation complexity

**Effort:** Medium (3-4 days)
**Risk:** Low

## Solution 2: Session-based Authentication with Redis

**Description:** Implement server-side session management with Redis storage

**Implementation:**
```python
import uuid
import redis
from typing import Optional, Dict, Any

class WebSocketSessionManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_timeout = 3600  # 1 hour

    def create_session(self, user_id: str, permissions: List[str]) -> str:
        """Create session ID and store in Redis."""
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        self.redis.setex(
            f"ws_session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )

        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return user data."""
        session_data = self.redis.get(f"ws_session:{session_id}")
        if not session_data:
            return None

        data = json.loads(session_data)

        # Update last activity
        self.redis.expire(f"ws_session:{session_id}", self.session_timeout)

        return data

# WebSocket endpoint with session validation
@self.app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = websocket.query_params.get('session_id')

    if not session_id:
        await websocket.close(code=4001, reason="Session ID required")
        return

    session_data = self.session_manager.validate_session(session_id)
    if not session_data:
        await websocket.close(code=4001, reason="Invalid or expired session")
        return

    await websocket.accept()

    connection_context = {
        'session_id': session_id,
        'user_id': session_data['user_id'],
        'permissions': session_data['permissions']
    }

    self.connection_manager.add_connection(websocket, connection_context)
```

**Pros:**
- ✅ Server-side session control
- ✅ Easy session revocation
- ✅ Detailed session tracking
- ✅ Integration with existing Redis infrastructure

**Cons:**
- ❌ Stateful (requires Redis for all operations)
- ❌ Session storage overhead
- ❌ More complex session lifecycle management

**Effort:** Medium (3-4 days)
**Risk:** Low

## Solution 3: API Key Authentication with Rate Limiting

**Description:** Implement API key-based authentication with per-key rate limiting

**Implementation:**
```python
import hashlib
from collections import defaultdict

class APIKeyManager:
    def __init__(self):
        self.api_keys = {
            # Format: api_key_hash -> {user_id, permissions, rate_limit}
            "hash1": {"user_id": "user1", "permissions": ["realtime_data"], "rate_limit": 100},
            "hash2": {"user_id": "user2", "permissions": ["realtime_data", "historical"], "rate_limit": 500}
        }
        self.rate_limiter = defaultdict(list)  # api_key -> [timestamps]

    def validate_api_key(self, api_key: str, client_ip: str) -> Optional[Dict[str, Any]]:
        """Validate API key and check rate limits."""
        if not api_key:
            return None

        # Hash the API key for security
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self.api_keys:
            return None

        key_info = self.api_keys[key_hash]

        # Check rate limiting
        now = time.time()
        self.rate_limiter[key_hash] = [
            ts for ts in self.rate_limiter[key_hash] if now - ts < 60  # Last minute
        ]

        if len(self.rate_limiter[key_hash]) >= key_info["rate_limit"]:
            return None  # Rate limited

        self.rate_limiter[key_hash].append(now)

        return key_info

# WebSocket endpoint with API key validation
@self.app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    api_key = websocket.query_params.get('api_key')
    client_ip = websocket.client.host

    key_info = self.api_key_manager.validate_api_key(api_key, client_ip)
    if not key_info:
        await websocket.close(code=4001, reason="Invalid or rate-limited API key")
        return

    await websocket.accept()

    connection_context = {
        'user_id': key_info['user_id'],
        'permissions': key_info['permissions'],
        'api_key_hash': hashlib.sha256(api_key.encode()).hexdigest()
    }

    self.connection_manager.add_connection(websocket, connection_context)
```

**Pros:**
- ✅ Simple implementation
- ✅ Built-in rate limiting
- ✅ Easy API key management
- ✅ No JWT complexity

**Cons:**
- ❌ API key management overhead
- ❌ Key rotation complexity
- ❌ No built-in expiration (except rate limiting)

**Effort:** Low (2-3 days)
**Risk:** Low

# Recommended Action

**CRITICAL - IMPLEMENT IMMEDIATELY (48 hours):**

1. **Add JWT-based authentication to WebSocket endpoint**
   - Implement token extraction from query parameters or headers
   - Add token validation middleware before connection acceptance
   - Set proper error codes for authentication failures

2. **Implement immediate security protections:**
   - Rate limiting: 100 connections/minute per IP address
   - Input validation for all incoming WebSocket messages
   - Connection timeout and maximum connection limits

3. **Security monitoring and logging:**
   - Log all authentication attempts (success/failure)
   - Implement connection monitoring for abuse detection
   - Add alerting for suspicious connection patterns

4. **Integration with existing system:**
   - Add auth configuration to config management
   - Ensure compatibility with current market data flow
   - Test with existing WebSocket clients

**BLOCKS PRODUCTION DEPLOYMENT until resolved.**

# Acceptance Criteria

- [ ] WebSocket connections require valid JWT token
- [ ] Unauthorized connections are rejected immediately
- [ ] Rate limiting prevents connection flooding (100 connections/minute/IP)
- [ ] All incoming messages are validated and sanitized
- [ ] Proper security headers implemented (CORS, CSP, etc.)
- [ ] Connection lifecycle properly managed
- [ ] Comprehensive test coverage for authentication flows
- [ ] Monitoring and logging for security events
- [ ] Performance impact measured and acceptable (<5% overhead)

# Technical Details

**Files to modify:**
- `simplified_system/src/realtime/websocket_server.py` (lines 160-200)
- Add: `simplified_system/src/realtime/auth.py` (authentication module)
- Add: `simplified_system/src/realtime/rate_limiter.py` (rate limiting)

**Dependencies to add:**
- `python-jose[cryptography]>=3.3.0` (JWT handling)
- `passlib[bcrypt]>=1.7.4` (password hashing)

**Database changes:**
- User management table (if not exists)
- API key storage table
- Session/activity logs

**Security considerations:**
- JWT secret key management
- Token refresh mechanism
- API key rotation policy
- Connection monitoring and alerting

# Resources

**Security references:**
- [WebSocket Security Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket_API/Using_WebSockets)
- [JWT Authentication for FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [OWASP WebSocket Security](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets)

**Code examples:**
- [FastAPI WebSocket authentication](https://fastapi.tiangolo.com/advanced/websockets/)
- [JWT implementation patterns](https://github.com/jpadilla/pyjwt)

**Related files:**
- `simplified_system/src/realtime/websocket_server.py` - primary implementation
- `simplified_system/phase3_core_demo.py` - test authentication flows
- Configuration management for JWT settings

# Work Log

## 2025-11-29 - Authentication Security Review

**By:** Code Review Agent

**Actions:**
- Analyzed WebSocket security vulnerabilities in Phase 3 codebase
- Identified missing authentication and authorization mechanisms
- Evaluated multiple authentication approaches (JWT, session, API key)
- Created comprehensive implementation plan with security best practices
- Designed rate limiting and connection management strategies

**Learnings:**
- WebSocket endpoints often overlooked in security reviews
- Authentication must happen before connection acceptance
- Rate limiting essential for WebSocket DoS prevention
- Token management critical for real-time systems
- Connection lifecycle management prevents resource leaks

## Next Steps

1. **Immediate (P1):** Implement JWT-based WebSocket authentication
2. **P2:** Add comprehensive rate limiting and monitoring
3. **P3:** Implement session management and user analytics
4. **P3:** Add security monitoring and alerting system