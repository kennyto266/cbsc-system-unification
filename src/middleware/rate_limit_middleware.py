"""
API Rate Limiting Middleware
API 速率限制中間件

Redis基礎的速率限制中間件，支持用戶級和IP級限流，動態限流策略
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_503_SERVICE_UNAVAILABLE
import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration"""

    def __init__(self):
        # Default rate limits per user tier
        self.user_limits = {
            'basic': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000,
                'burst_allowance': 10,
                'priority_multiplier': 1.0
            },
            'premium': {
                'requests_per_minute': 120,
                'requests_per_hour': 2400,
                'requests_per_day': 24000,
                'burst_allowance': 20,
                'priority_multiplier': 2.0
            },
            'institutional': {
                'requests_per_minute': 300,
                'requests_per_hour': 6000,
                'requests_per_day': 60000,
                'burst_allowance': 50,
                'priority_multiplier': 5.0
            },
            'admin': {
                'requests_per_minute': 1000,
                'requests_per_hour': 20000,
                'requests_per_day': 200000,
                'burst_allowance': 100,
                'priority_multiplier': 10.0
            }
        }

        # IP-based limits (for unauthenticated requests)
        self.ip_limits = {
            'requests_per_minute': 20,
            'requests_per_hour': 500,
            'requests_per_day': 5000,
            'burst_allowance': 5
        }

        # Special endpoint limits
        self.endpoint_limits = {
            '/api/auth/login': {
                'requests_per_minute': 5,
                'requests_per_hour': 20,
                'burst_allowance': 2
            },
            '/api/auth/register': {
                'requests_per_minute': 3,
                'requests_per_hour': 10,
                'burst_allowance': 1
            },
            '/api/auth/reset-password': {
                'requests_per_minute': 3,
                'requests_per_hour': 10,
                'burst_allowance': 1
            },
            '/api/strategies/backtest': {
                'requests_per_hour': 50,
                'burst_allowance': 10
            },
            '/api/data/export': {
                'requests_per_hour': 20,
                'burst_allowance': 5
            }
        }

        # Penalty factors for violations
        self.violation_penalties = {
            'minor': 0.9,      # 10% reduction
            'moderate': 0.7,   # 30% reduction
            'severe': 0.5,     # 50% reduction
            'critical': 0.0    # Complete block
        }


class RedisRateLimiter:
    """Redis-based rate limiter with sliding window"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.config = RateLimitConfig()
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Rate limiter connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect Redis for rate limiting: {e}")
                self.redis_client = None

    async def check_rate_limit(
        self,
        identifier: str,
        window: str = 'minute',
        user_tier: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit for identifier

        Args:
            identifier: User ID, IP address, or other identifier
            window: Time window ('minute', 'hour', 'day')
            user_tier: User tier for tier-based limits
            endpoint: Endpoint path for special limits
            user_id: Actual user ID (if different from identifier)

        Returns:
            Tuple of (allowed, limit_info)
        """
        if not self.redis_client:
            # Fallback to allow if Redis is unavailable
            return True, {'remaining': 999999, 'reset_time': int(time.time() + 60)}

        # Get limits
        limits = self._get_limits(user_tier, endpoint, identifier)

        # Convert window to seconds
        window_seconds = self._window_to_seconds(window)
        limit_key = f"rate_limit:{window}:{identifier}"

        async with self._lock:
            try:
                # Use Redis pipeline for atomic operations
                pipe = self.redis_client.pipeline()
                current_time = time.time()
                window_start = current_time - window_seconds

                # Remove expired entries
                pipe.zremrangebyscore(limit_key, 0, window_start)

                # Get current count
                pipe.zcard(limit_key)

                # Add current request
                pipe.zadd(limit_key, {str(current_time): current_time})

                # Set expiration (keep key for twice the window duration)
                pipe.expire(limit_key, window_seconds * 2)

                # Execute pipeline
                results = await pipe.execute()
                current_count = results[1]

                # Get the limit for this window
                limit = limits.get(f'requests_per_{window}', 100)

                # Calculate info
                remaining = max(0, limit - current_count)
                reset_time = int(current_time + window_seconds)

                limit_info = {
                    'limit': limit,
                    'remaining': remaining,
                    'current': current_count,
                    'reset_time': reset_time,
                    'window': window,
                    'retry_after': window_seconds if remaining == 0 else None
                }

                # Check if violation penalty should be applied
                penalty_factor = await self._get_violation_penalty(identifier)
                if penalty_factor < 1.0:
                    adjusted_limit = int(limit * penalty_factor)
                    limit_info['adjusted_limit'] = adjusted_limit
                    if current_count > adjusted_limit:
                        limit_info['penalty_active'] = True
                        limit_info['penalty_factor'] = penalty_factor
                        limit_info['remaining'] = 0
                        return False, limit_info

                # Log the request for analytics
                await self._log_request(identifier, user_tier, endpoint, window, current_count)

                return current_count <= limit, limit_info

            except Exception as e:
                logger.error(f"Rate limit check error: {e}")
                # Fail open - allow request
                return True, {'remaining': 999999, 'reset_time': int(time.time() + 60)}

    async def _get_violation_penalty(self, identifier: str) -> float:
        """Get violation penalty factor for identifier"""
        if not self.redis_client:
            return 1.0

        try:
            penalty_key = f"rate_penalty:{identifier}"
            penalty_data = await self.redis_client.get(penalty_key)

            if penalty_data:
                penalty = json.loads(penalty_data)
                # Check if penalty is still active
                if time.time() < penalty['expires_at']:
                    return penalty['factor']
                else:
                    # Remove expired penalty
                    await self.redis_client.delete(penalty_key)

            return 1.0
        except Exception as e:
            logger.error(f"Error getting violation penalty: {e}")
            return 1.0

    async def apply_violation_penalty(
        self,
        identifier: str,
        severity: str,
        duration_minutes: int = 60
    ):
        """Apply violation penalty to identifier"""
        if not self.redis_client:
            return

        try:
            penalty_factor = self.config.violation_penalties.get(severity, 0.9)
            expires_at = time.time() + (duration_minutes * 60)

            penalty_data = {
                'factor': penalty_factor,
                'severity': severity,
                'applied_at': time.time(),
                'expires_at': expires_at
            }

            penalty_key = f"rate_penalty:{identifier}"
            await self.redis_client.setex(
                penalty_key,
                duration_minutes * 60,
                json.dumps(penalty_data)
            )

            logger.warning(
                f"Applied rate limit penalty: {identifier} - {severity}",
                extra={'identifier': identifier, 'penalty': penalty_data}
            )
        except Exception as e:
            logger.error(f"Error applying violation penalty: {e}")

    def _get_limits(
        self,
        user_tier: Optional[str],
        endpoint: Optional[str],
        identifier: str
    ) -> Dict[str, int]:
        """Get rate limits based on user tier and endpoint"""

        # Check for endpoint-specific limits first
        if endpoint:
            for endpoint_pattern, limits in self.config.endpoint_limits.items():
                if endpoint.startswith(endpoint_pattern):
                    return limits

        # Use tier-based limits for authenticated users
        if user_tier and user_tier in self.config.user_limits:
            return self.config.user_limits[user_tier]

        # Use IP limits for unauthenticated requests
        return self.config.ip_limits

    def _window_to_seconds(self, window: str) -> int:
        """Convert window string to seconds"""
        window_map = {
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        return window_map.get(window, 60)

    async def _log_request(
        self,
        identifier: str,
        user_tier: Optional[str],
        endpoint: Optional[str],
        window: str,
        current_count: int
    ):
        """Log rate limit data for analytics"""
        if not self.redis_client:
            return

        try:
            log_key = f"rate_log:{datetime.now().strftime('%Y-%m-%d:%H')}"
            log_entry = {
                'timestamp': time.time(),
                'identifier': identifier,
                'user_tier': user_tier or 'anonymous',
                'endpoint': endpoint,
                'window': window,
                'count': current_count
            }

            # Store with expiration (keep for 7 days)
            await self.redis_client.lpush(log_key, json.dumps(log_entry))
            await self.redis_client.expire(log_key, 7 * 24 * 3600)
        except Exception as e:
            logger.error(f"Error logging rate limit data: {e}")

    async def get_rate_limit_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit statistics for identifier"""
        if not self.redis_client:
            return {}

        try:
            stats = {}

            # Check all windows
            for window in ['minute', 'hour', 'day']:
                limit_key = f"rate_limit:{window}:{identifier}"
                current_time = time.time()
                window_seconds = self._window_to_seconds(window)
                window_start = current_time - window_seconds

                # Clean and get count
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(limit_key, 0, window_start)
                pipe.zcard(limit_key)
                results = await pipe.execute()

                stats[f'{window}_count'] = results[1]

            # Check penalty status
            penalty_key = f"rate_penalty:{identifier}"
            penalty_data = await self.redis_client.get(penalty_key)
            if penalty_data:
                stats['penalty'] = json.loads(penalty_data)

            return stats
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    def __init__(self, app, redis_limiter: RedisRateLimiter):
        super().__init__(app)
        self.redis_limiter = redis_limiter

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Get client info
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        user_tier = getattr(request.state, 'user_tier', None)

        # Determine identifier (user_id if authenticated, IP otherwise)
        identifier = user_id or client_ip

        # Get endpoint path
        endpoint = request.url.path

        # Check rate limits for all windows
        windows_to_check = ['minute', 'hour', 'day']

        for window in windows_to_check:
            # Skip day window for health endpoints
            if window == 'day' and endpoint.startswith('/health'):
                continue

            allowed, limit_info = await self.redis_limiter.check_rate_limit(
                identifier=identifier,
                window=window,
                user_tier=user_tier,
                endpoint=endpoint,
                user_id=user_id
            )

            if not allowed:
                # Log rate limit violation
                logger.warning(
                    f"Rate limit exceeded: {identifier} - {window}",
                    extra={
                        'identifier': identifier,
                        'user_id': user_id,
                        'client_ip': client_ip,
                        'endpoint': endpoint,
                        'window': window,
                        'limit_info': limit_info
                    }
                )

                # Apply penalty if this is a severe violation
                if limit_info.get('current', 0) > limit_info.get('limit', 0) * 2:
                    severity = 'severe' if user_id else 'moderate'
                    await self.redis_limiter.apply_violation_penalty(
                        identifier, severity, 60
                    )

                # Return 429 with rate limit headers
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Limit: {limit_info["limit"]} per {window}',
                        'retry_after': limit_info.get('retry_after', 60),
                        'limit_info': limit_info
                    },
                    headers={
                        'X-RateLimit-Limit': str(limit_info['limit']),
                        'X-RateLimit-Remaining': str(limit_info['remaining']),
                        'X-RateLimit-Reset': str(limit_info['reset_time']),
                        'Retry-After': str(limit_info.get('retry_after', 60))
                    }
                )

        # Process request
        response = await call_next(request)

        # Add rate limit headers for the smallest window (minute)
        _, minute_info = await self.redis_limiter.check_rate_limit(
            identifier=identifier,
            window='minute',
            user_tier=user_tier,
            endpoint=endpoint,
            user_id=user_id
        )

        response.headers['X-RateLimit-Limit'] = str(minute_info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(minute_info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(minute_info['reset_time'])

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies"""
        # Check Cloudflare
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip

        # Check standard proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"


# Global instances
rate_limiter = RedisRateLimiter()
rate_limit_middleware = None


def get_rate_limiter() -> RedisRateLimiter:
    """Get rate limiter instance"""
    return rate_limiter


def create_rate_limit_middleware(app) -> RateLimitMiddleware:
    """Create rate limit middleware"""
    global rate_limit_middleware
    rate_limit_middleware = RateLimitMiddleware(app, rate_limiter)
    return rate_limit_middleware


async def initialize_rate_limiting():
    """Initialize rate limiting system"""
    await rate_limiter.initialize()
    logger.info("Rate limiting system initialized")