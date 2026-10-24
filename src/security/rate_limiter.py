"""
Advanced Rate Limiting System

This module provides comprehensive rate limiting with Redis backend,
including user-based and IP-based limits, DDoS protection,
and advanced rate limiting strategies for different API endpoints.
"""

import os
import asyncio
import time
import json
from typing import Dict, Optional, List, Tuple, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import redis
import logging
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_503_SERVICE_UNAVAILABLE

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting"""

    def __init__(self):
        # Default rate limits
        self.limits = {
            # API call limits per minute
            'api_calls_per_minute': 60,
            'api_calls_per_hour': 3600,
            'api_calls_per_day': 86400,

            # Real-time connection limits
            'real_time_connections': 5,
            'websocket_connections': 10,

            # Data operation limits
            'data_exports_per_hour': 10,
            'data_imports_per_hour': 5,
            'strategy_executions_per_hour': 100,

            # Special limits for non-price strategies
            'macro_data_calls_per_minute': 30,
            'sentiment_api_calls_per_minute': 20,
            'hkma_api_calls_per_minute': 10,

            # Security limits
            'login_attempts_per_minute': 5,
            'password_resets_per_hour': 3,
        }

        # Penalties for violations
        self.penalties = {
            'minor_violation': 1.5,  # 1.5x normal limit
            'major_violation': 0.5,  # 0.5x normal limit
            'critical_violation': 0,  # Block completely
        }

        # DDoS protection thresholds
        self.ddos_thresholds = {
            'requests_per_second': 100,
            'concurrent_requests': 50,
            'burst_threshold': 500,
        }

        # Redis configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB_RATELIMIT', '1'))
        self.redis_key_prefix = "rate_limit"


class RateLimiter:
    """Advanced rate limiting with Redis backend"""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.redis_client = None
        self._connect_redis()

    def _connect_redis(self):
        """Connect to Redis with fallback to in-memory"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Using in-memory rate limiting.")
            self.redis_client = None
            self._init_in_memory_storage()

    def _init_in_memory_storage(self):
        """Initialize in-memory storage as fallback"""
        self._memory_storage = defaultdict(lambda: defaultdict(int))
        self._memory_timestamps = defaultdict(deque)

    async def check_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        custom_limit: Optional[int] = None,
        window: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if identifier has exceeded rate limit"""

        limit = custom_limit or self._get_limit_for_role(limit_type, user_role)
        window = window or self._get_window_for_limit(limit_type)

        try:
            if self.redis_client:
                return await self._check_redis_limit(identifier, limit_type, limit, window)
            else:
                return await self._check_memory_limit(identifier, limit_type, limit, window)

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {"remaining": limit, "reset_time": time.time() + window}

    async def _check_redis_limit(
        self,
        identifier: str,
        limit_type: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis"""

        key = f"{self.config.redis_key_prefix}:{limit_type}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - window

        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiration
        pipe.expire(key, window * 2)

        # Execute pipeline
        results = pipe.execute()
        current_count = results[1]

        # Check if limit exceeded
        if current_count > limit:
            # Get oldest request timestamp
            oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
            reset_time = oldest[0][1] + window if oldest else current_time + window

            await self._log_rate_limit_violation(identifier, limit_type, limit, current_count)

            return False, {
                "remaining": 0,
                "reset_time": reset_time,
                "limit": limit,
                "current": current_count
            }

        return True, {
            "remaining": limit - current_count,
            "reset_time": current_time + window,
            "limit": limit,
            "current": current_count
        }

    async def _check_memory_limit(
        self,
        identifier: str,
        limit_type: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory storage"""

        current_time = time.time()
        window_start = current_time - window
        key = f"{identifier}:{limit_type}"

        # Clean old entries
        timestamps = self._memory_timestamps[key]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        # Check limit
        current_count = len(timestamps)
        if current_count >= limit:
            await self._log_rate_limit_violation(identifier, limit_type, limit, current_count)
            return False, {
                "remaining": 0,
                "reset_time": timestamps[0] + window if timestamps else current_time + window,
                "limit": limit,
                "current": current_count
            }

        # Add current request
        timestamps.append(current_time)

        return True, {
            "remaining": limit - current_count,
            "reset_time": current_time + window,
            "limit": limit,
            "current": current_count
        }

    def _get_limit_for_role(self, limit_type: str, user_role: Optional[str]) -> int:
        """Get rate limit based on user role"""

        # Role-based multipliers
        role_multipliers = {
            'basic': 1.0,
            'premium': 3.0,
            'institutional': 10.0,
            'admin': 50.0,
            'quant_analyst': 5.0,
            'non_price_viewer': 1.5,
            'non_price_analyst': 4.0,
            'non_price_admin': 20.0,
        }

        base_limit = self.config.limits.get(limit_type, self.config.limits['api_calls_per_minute'])
        multiplier = role_multipliers.get(user_role, 1.0)

        return int(base_limit * multiplier)

    def _get_window_for_limit(self, limit_type: str) -> int:
        """Get time window for limit type in seconds"""

        if 'per_minute' in limit_type:
            return 60
        elif 'per_hour' in limit_type:
            return 3600
        elif 'per_day' in limit_type:
            return 86400
        else:
            return 60  # Default to 1 minute

    async def _log_rate_limit_violation(
        self,
        identifier: str,
        limit_type: str,
        limit: int,
        current_count: int
    ) -> None:
        """Log rate limit violations for security monitoring"""

        violation_entry = {
            "timestamp": datetime.now().isoformat(),
            "identifier": identifier,
            "limit_type": limit_type,
            "limit": limit,
            "current_count": current_count,
            "violation_severity": self._determine_violation_severity(limit, current_count)
        }

        logger.warning(f"Rate limit violation: {violation_entry}")

        # Store in Redis for monitoring
        if self.redis_client:
            try:
                monitoring_key = f"security_events:rate_limit_violations:{datetime.now().strftime('%Y-%m-%d')}"
                self.redis_client.lpush(monitoring_key, json.dumps(violation_entry))
                self.redis_client.expire(monitoring_key, 86400 * 7)  # Keep for 7 days
            except Exception as e:
                logger.error(f"Failed to store rate limit violation: {e}")

    def _determine_violation_severity(self, limit: int, current_count: int) -> str:
        """Determine violation severity based on excess"""

        excess_ratio = (current_count - limit) / limit

        if excess_ratio > 2:
            return "critical"
        elif excess_ratio > 1:
            return "major"
        elif excess_ratio > 0.5:
            return "minor"
        else:
            return "info"

    async def check_ddos_protection(self, ip_address: str) -> bool:
        """Check if IP address is exhibiting DDoS behavior"""

        if not self.redis_client:
            return True  # Skip DDoS check without Redis

        try:
            current_time = int(time.time())
            key = f"ddos_check:{ip_address}"

            # Get request count in last second
            requests_last_second = self.redis_client.zcount(
                key, current_time - 1, current_time
            )

            # Get concurrent requests
            concurrent_requests = self.redis_client.zcard(key)

            # Clean old entries
            self.redis_client.zremrangebyscore(key, 0, current_time - 60)
            self.redis_client.expire(key, 300)  # Keep for 5 minutes

            # Check thresholds
            if requests_last_second > self.config.ddos_thresholds['requests_per_second']:
                await self._trigger_ddos_protection(ip_address, "requests_per_second")
                return False

            if concurrent_requests > self.config.ddos_thresholds['concurrent_requests']:
                await self._trigger_ddos_protection(ip_address, "concurrent_requests")
                return False

            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})

            return True

        except Exception as e:
            logger.error(f"DDoS protection check failed: {e}")
            return True  # Fail open

    async def _trigger_ddos_protection(self, ip_address: str, reason: str) -> None:
        """Trigger DDoS protection for IP address"""

        protection_key = f"ddos_blocked:{ip_address}"
        block_duration = 3600  # 1 hour

        # Block the IP
        if self.redis_client:
            self.redis_client.setex(protection_key, block_duration, reason)

        logger.critical(f"DDoS protection triggered for IP {ip_address}: {reason}")

        # Log to audit system
        from .audit_logger import audit_logger, AuditEventType, EventSeverity
        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id=None,
            ip_address=ip_address,
            severity=EventSeverity.CRITICAL,
            details={
                "violation_type": "ddos_attack",
                "reason": reason,
                "action": "ip_blocked",
                "duration": block_duration
            },
            success=False
        )

    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked due to DDoS protection"""

        if not self.redis_client:
            return False

        try:
            block_key = f"ddos_blocked:{ip_address}"
            return bool(self.redis_client.exists(block_key))
        except Exception:
            return False


class RateLimitMiddleware:
    """FastAPI middleware for comprehensive rate limiting"""

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        # Extract identifiers
        user_id = await self._extract_user_id(request)
        ip_address = request.client.host if request.client else "unknown"

        # Check DDoS protection first
        if not await self.rate_limiter.check_ddos_protection(ip_address):
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service temporarily unavailable",
                    "code": "DDOS_PROTECTION_ACTIVATED",
                    "retry_after": 3600
                }
            )

        # Check if IP is blocked
        if await self.rate_limiter.is_ip_blocked(ip_address):
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Access blocked",
                    "code": "IP_BLOCKED"
                }
            )

        # Determine limit type and identifier
        limit_type = self._determine_limit_type(request.url.path)
        identifier = user_id or ip_address

        # Get user role for role-based limits
        user_role = await self._get_user_role(user_id) if user_id else None

        # Check rate limit
        allowed, limit_info = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            limit_type=limit_type,
            user_role=user_role
        )

        if not allowed:
            # Calculate retry after
            retry_after = int(limit_info["reset_time"] - time.time())
            if retry_after <= 0:
                retry_after = 60

            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit_type": limit_type,
                    "limit": limit_info["limit"],
                    "current": limit_info["current"],
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(limit_info["remaining"]),
                    "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
                }
            )

        # Add rate limit headers to successful response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(limit_info["reset_time"]))

        return response

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""

        # Try to get from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would integrate with your JWT decoding logic
                # token = auth_header.split(" ")[1]
                # payload = decode_jwt(token)
                # return payload.get("user_id")
                pass
            except Exception:
                pass

        # Try to get from session
        session = getattr(request.state, 'session', None)
        if session and 'user_id' in session:
            return session['user_id']

        return None

    async def _get_user_role(self, user_id: str) -> Optional[str]:
        """Get user role for rate limiting"""

        # This would integrate with your user management system
        # For now, return default role
        return "basic"

    def _determine_limit_type(self, path: str) -> str:
        """Determine rate limit type based on request path"""

        # Non-price strategy endpoints
        if path.startswith("/api/non-price/strategies/execute"):
            return "strategy_executions_per_hour"
        elif path.startswith("/api/non-price/macro"):
            return "macro_data_calls_per_minute"
        elif path.startswith("/api/non-price/sentiment"):
            return "sentiment_api_calls_per_minute"
        elif path.startswith("/api/non-price/hkma"):
            return "hkma_api_calls_per_minute"
        elif path.startswith("/api/non-price/ws"):
            return "real_time_connections"
        elif path.startswith("/api/non-price/export"):
            return "data_exports_per_hour"

        # Authentication endpoints
        elif path.startswith("/api/auth/login"):
            return "login_attempts_per_minute"
        elif path.startswith("/api/auth/reset-password"):
            return "password_resets_per_hour"

        # Default API calls
        elif path.startswith("/api/"):
            return "api_calls_per_minute"

        # No limit for static assets
        else:
            return "none"


# Global rate limiter instance
rate_limiter = RateLimiter()


async def initialize_rate_limiter():
    """Initialize rate limiter with configuration"""
    logger.info("Rate limiter initialized")