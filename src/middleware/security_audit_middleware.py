"""
Security Audit Middleware
安全審計中間件

整合安全審計日誌記錄、用戶行為追蹤、異常檢測和實時警報
"""

import time
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as redis
import hashlib
import hmac

from security.audit_logger import audit_logger, AuditEventType, EventSeverity
from core.config import settings

logger = logging.getLogger(__name__)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Security audit middleware for comprehensive request tracking
    安全審計中間件，用於全面的請求追蹤
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = None
        self._suspicious_patterns = self._load_suspicious_patterns()
        self._blocked_ips = {}
        self._user_session_tracker = {}

    async def _init_redis(self):
        """Initialize Redis connection for enhanced tracking"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True
                )
                await self.redis_client.ping()
                logger.info("Security audit middleware connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect Redis for security audit: {e}")
                self.redis_client = None

    def _load_suspicious_patterns(self) -> Dict[str, Any]:
        """Load suspicious activity patterns"""
        return {
            'sql_injection': [
                'union select', 'drop table', 'truncate table', 'exec(',
                'xp_cmdshell', 'sp_executesql', '--', '/*', '*/'
            ],
            'xss': [
                '<script', 'javascript:', 'onload=', 'onerror=',
                'alert(', 'document.cookie', 'window.location'
            ],
            'path_traversal': [
                '../', '..\\', '%2e%2e%2f', '%2e%2e\\',
                'etc/passwd', 'windows/system32'
            ],
            'command_injection': [
                ';', '&&', '||', '|', '`', '$(', '${',
                'nc -l', 'netcat', 'wget', 'curl'
            ],
            'suspicious_user_agents': [
                'sqlmap', 'nikto', 'nmap', 'masscan',
                'dirb', 'dirbuster', 'gobuster', 'burp'
            ]
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security auditing"""
        # Initialize Redis if needed
        if not self.redis_client:
            await self._init_redis()

        # Start timing
        start_time = time.time()
        request_id = self._generate_request_id(request)

        # Extract client information
        client_info = self._extract_client_info(request)

        # Check if IP is blocked
        if await self._is_ip_blocked(client_info['ip_address']):
            await self._log_blocked_attempt(request, client_info)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access blocked"
            )

        # Check for suspicious patterns
        suspicion_score = await self._check_suspicious_patterns(request, client_info)
        if suspicion_score > 0.7:
            await self._handle_suspicious_request(request, client_info, suspicion_score)

        # Track user session
        user_info = await self._track_user_session(request, client_info)

        # Log API access
        await audit_logger.log_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_info.get('user_id'),
            session_id=user_info.get('session_id'),
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            severity=self._determine_severity(request, suspicion_score),
            details={
                'method': request.method,
                'url': str(request.url),
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'request_id': request_id,
                'suspicion_score': suspicion_score,
                'client_info': client_info
            },
            success=True
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Add security headers
            await self._add_security_headers(response)

            # Log successful response
            if response.status_code < 400:
                await audit_logger.log_event(
                    event_type=AuditEventType.DATA_ACCESS if 'data' in request.url.path else AuditEventType.API_ACCESS,
                    user_id=user_info.get('user_id'),
                    session_id=user_info.get('session_id'),
                    ip_address=client_info['ip_address'],
                    details={
                        'status_code': response.status_code,
                        'process_time': process_time,
                        'request_id': request_id,
                        'response_size': getattr(response, 'content-length', 0)
                    },
                    success=True
                )

            # Track response metrics
            await self._track_response_metrics(request, response, process_time, client_info)

            return response

        except HTTPException as e:
            # Log HTTP exceptions
            await audit_logger.log_event(
                event_type=AuditEventType.PERMISSION_DENIED if e.status_code == 403 else AuditEventType.UNAUTHORIZED_ACCESS,
                user_id=user_info.get('user_id'),
                session_id=user_info.get('session_id'),
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                severity=EventSeverity.HIGH if e.status_code == 403 else EventSeverity.MEDIUM,
                details={
                    'status_code': e.status_code,
                    'error_detail': str(e.detail),
                    'request_id': request_id,
                    'path': request.url.path
                },
                success=False
            )
            raise

        except Exception as e:
            # Log unexpected errors
            await audit_logger.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                user_id=user_info.get('user_id'),
                session_id=user_info.get('session_id'),
                ip_address=client_info['ip_address'],
                severity=EventSeverity.HIGH,
                details={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'request_id': request_id,
                    'path': request.url.path
                },
                success=False
            )
            raise

    def _generate_request_id(self, request: Request) -> str:
        """Generate unique request ID"""
        timestamp = str(int(time.time() * 1000))
        content = f"{timestamp}{request.method}{request.url.path}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _extract_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract comprehensive client information"""
        # Get IP address considering proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")
        cf_ip = request.headers.get("CF-Connecting-IP")

        ip_address = (
            cf_ip or
            (forwarded_for.split(',')[0].strip() if forwarded_for else None) or
            real_ip or
            request.client.host if request.client else "unknown"
        )

        return {
            'ip_address': ip_address,
            'user_agent': request.headers.get("User-Agent", ""),
            'referer': request.headers.get("Referer", ""),
            'origin': request.headers.get("Origin", ""),
            'forwarded_for': forwarded_for,
            'request_method': request.method,
            'request_url': str(request.url),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _check_suspicious_patterns(self, request: Request, client_info: Dict[str, Any]) -> float:
        """Check for suspicious patterns in request"""
        suspicion_score = 0.0

        # Check user agent
        user_agent = client_info['user_agent'].lower()
        for pattern in self._suspicious_patterns['suspicious_user_agents']:
            if pattern in user_agent:
                suspicion_score += 0.3
                logger.warning(f"Suspicious user agent detected: {pattern}")

        # Check URL and query parameters
        url_lower = str(request.url).lower()
        params_str = str(dict(request.query_params)).lower()

        for category, patterns in self._suspicious_patterns.items():
            if category == 'suspicious_user_agents':
                continue

            for pattern in patterns:
                if pattern in url_lower or pattern in params_str:
                    suspicion_score += 0.2
                    logger.warning(f"Suspicious pattern detected: {category} - {pattern}")

        # Check request body if present
        if hasattr(request, '_body') and request._body:
            body_lower = request._body.decode('utf-8', errors='ignore').lower()
            for category, patterns in self._suspicious_patterns.items():
                if category == 'suspicious_user_agents':
                    continue
                for pattern in patterns:
                    if pattern in body_lower:
                        suspicion_score += 0.3
                        logger.warning(f"Suspicious pattern in body: {category} - {pattern}")

        # Check for rate limiting anomalies
        ip_address = client_info['ip_address']
        if await self._check_rate_anomalies(ip_address):
            suspicion_score += 0.4

        return min(suspicion_score, 1.0)

    async def _check_rate_anomalies(self, ip_address: str) -> bool:
        """Check for request rate anomalies"""
        if not self.redis_client:
            return False

        try:
            # Check requests in last minute
            minute_key = f"security:rate:{ip_address}:minute"
            current_time = int(time.time())
            window_start = current_time - 60

            # Clean old entries
            await self.redis_client.zremrangebyscore(minute_key, 0, window_start)

            # Count recent requests
            request_count = await self.redis_client.zcard(minute_key)

            # Add current request
            await self.redis_client.zadd(minute_key, {str(current_time): current_time})
            await self.redis_client.expire(minute_key, 300)  # Keep for 5 minutes

            # Check if rate is abnormal (> 100 requests per minute)
            return request_count > 100

        except Exception as e:
            logger.error(f"Error checking rate anomalies: {e}")
            return False

    async def _handle_suspicious_request(self, request: Request, client_info: Dict[str, Any], score: float):
        """Handle suspicious request"""
        await audit_logger.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            severity=EventSeverity.HIGH if score > 0.8 else EventSeverity.MEDIUM,
            details={
                'suspicion_score': score,
                'request_url': str(request.url),
                'method': request.method,
                'user_agent': client_info['user_agent'],
                'patterns_found': self._get_found_patterns(request),
                'client_info': client_info
            },
            success=False
        )

        # Block IP if score is very high
        if score > 0.9:
            await self._block_ip_temporarily(client_info['ip_address'], 3600)  # 1 hour

    async def _block_ip_temporarily(self, ip_address: str, duration: int):
        """Temporarily block an IP address"""
        if not self.redis_client:
            return

        try:
            block_key = f"security:blocked:{ip_address}"
            await self.redis_client.setex(block_key, duration, json.dumps({
                'blocked_at': time.time(),
                'duration': duration,
                'reason': 'Suspicious activity detected'
            }))

            self._blocked_ips[ip_address] = time.time() + duration
            logger.warning(f"IP temporarily blocked: {ip_address} for {duration} seconds")

            # Log the blocking
            await audit_logger.log_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                ip_address=ip_address,
                severity=EventSeverity.HIGH,
                details={
                    'action': 'ip_blocked',
                    'duration': duration,
                    'reason': 'Suspicious activity detected'
                },
                success=False
            )

        except Exception as e:
            logger.error(f"Error blocking IP: {e}")

    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        # Check in-memory cache
        if ip_address in self._blocked_ips:
            if time.time() < self._blocked_ips[ip_address]:
                return True
            else:
                del self._blocked_ips[ip_address]

        # Check Redis
        if self.redis_client:
            try:
                block_key = f"security:blocked:{ip_address}"
                return await self.redis_client.exists(block_key)
            except Exception:
                pass

        return False

    async def _track_user_session(self, request: Request, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Track user session information"""
        # Try to extract user info from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        session_id = getattr(request.state, 'session_id', None)
        user_tier = getattr(request.state, 'user_tier', None)

        # Track concurrent sessions
        if user_id and session_id:
            await self._update_user_sessions(user_id, session_id, client_info)

        return {
            'user_id': user_id,
            'session_id': session_id,
            'user_tier': user_tier
        }

    async def _update_user_sessions(self, user_id: str, session_id: str, client_info: Dict[str, Any]):
        """Update user session tracking"""
        if not self.redis_client:
            return

        try:
            # Track active sessions for user
            sessions_key = f"security:sessions:{user_id}"
            session_data = {
                'session_id': session_id,
                'ip_address': client_info['ip_address'],
                'user_agent': client_info['user_agent'],
                'last_activity': time.time()
            }

            # Add/update session
            await self.redis_client.hset(sessions_key, session_id, json.dumps(session_data))
            await self.redis_client.expire(sessions_key, 24 * 3600)  # Keep for 24 hours

            # Check for multiple concurrent sessions
            sessions = await self.redis_client.hgetall(sessions_key)
            if len(sessions) > 3:  # More than 3 concurrent sessions
                await audit_logger.log_event(
                    event_type=AuditEventType.MULTIPLE_SESSIONS,
                    user_id=user_id,
                    ip_address=client_info['ip_address'],
                    severity=EventSeverity.MEDIUM,
                    details={
                        'active_sessions': len(sessions),
                        'session_details': sessions
                    }
                )

        except Exception as e:
            logger.error(f"Error tracking user sessions: {e}")

    def _determine_severity(self, request: Request, suspicion_score: float) -> EventSeverity:
        """Determine event severity based on request context"""
        if suspicion_score > 0.7:
            return EventSeverity.HIGH
        elif suspicion_score > 0.3:
            return EventSeverity.MEDIUM
        elif request.method in ['POST', 'PUT', 'DELETE']:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    async def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    async def _track_response_metrics(self, request: Request, response: Response, process_time: float, client_info: Dict[str, Any]):
        """Track response metrics for analysis"""
        if not self.redis_client:
            return

        try:
            # Track response times
            metrics_key = f"security:metrics:{datetime.now().strftime('%Y-%m-%d:%H')}"
            await self.redis_client.lpush(metrics_key, json.dumps({
                'timestamp': time.time(),
                'path': request.url.path,
                'method': request.method,
                'status_code': response.status_code,
                'process_time': process_time,
                'ip_address': client_info['ip_address']
            }))
            await self.redis_client.expire(metrics_key, 7 * 24 * 3600)  # Keep for 7 days

            # Alert on slow responses
            if process_time > 5.0:  # 5 seconds
                await audit_logger.log_event(
                    event_type=AuditEventType.SERVICE_UNAVAILABLE,
                    ip_address=client_info['ip_address'],
                    severity=EventSeverity.MEDIUM,
                    details={
                        'slow_response': True,
                        'process_time': process_time,
                        'path': request.url.path
                    }
                )

        except Exception as e:
            logger.error(f"Error tracking response metrics: {e}")

    async def _log_blocked_attempt(self, request: Request, client_info: Dict[str, Any]):
        """Log blocked IP attempt"""
        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            severity=EventSeverity.HIGH,
            details={
                'action': 'access_blocked',
                'reason': 'IP address is blocked',
                'request_url': str(request.url),
                'method': request.method
            },
            success=False
        )

    def _get_found_patterns(self, request: Request) -> List[str]:
        """Get list of suspicious patterns found in request"""
        found_patterns = []
        request_content = f"{str(request.url)} {str(dict(request.query_params))}".lower()

        if hasattr(request, '_body') and request._body:
            request_content += " " + request._body.decode('utf-8', errors='ignore').lower()

        for category, patterns in self._suspicious_patterns.items():
            for pattern in patterns:
                if pattern in request_content:
                    found_patterns.append(f"{category}:{pattern}")

        return found_patterns


# Global instance
security_audit_middleware = None


def create_security_audit_middleware(app):
    """Create security audit middleware"""
    global security_audit_middleware
    security_audit_middleware = SecurityAuditMiddleware(app)
    return security_audit_middleware


def get_security_audit_middleware():
    """Get security audit middleware instance"""
    return security_audit_middleware