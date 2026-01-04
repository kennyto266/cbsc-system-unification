"""
API Performance Monitoring and Rate Limiting
============================================

Comprehensive monitoring system for API performance with:
- Request/response tracking
- Rate limiting with multiple strategies
- Performance analytics
- Alert system
- Metrics collection

Author: CBSC Quant Team
Version: 1.0.0
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import redis
import redis.asyncio as redis_async
from functools import wraps
import hashlib
import psutil
import aiofiles
import os
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import prometheus_client as prometheus
from prometheus_client import Counter, Histogram, Gauge, generate_latest

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10
    strategy: str = "sliding_window"  # "sliding_window", "token_bucket", "fixed_window"


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    threshold: float
    operator: str = ">"  # ">", "<", ">=", "<=", "=="
    duration: int = 300  # seconds
    enabled: bool = True
    action: str = "log"  # "log", "email", "webhook"


@dataclass
class RequestMetrics:
    """Request metrics data"""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[redis_async.Redis] = None
        self.local_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await redis_async.from_url(self.redis_url, decode_responses=True)

    async def is_allowed(
        self,
        key: str,
        config: RateLimitConfig,
        identifier: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Rate limit key (e.g., "api", "endpoint", "user")
            config: Rate limit configuration
            identifier: Unique identifier (e.g., IP, user ID)

        Returns:
            Tuple of (allowed, info)
        """
        if not identifier:
            identifier = "anonymous"

        full_key = f"rate_limit:{key}:{identifier}"

        if config.strategy == "sliding_window":
            return await self._sliding_window(full_key, config)
        elif config.strategy == "token_bucket":
            return await self._token_bucket(full_key, config)
        elif config.strategy == "fixed_window":
            return await self._fixed_window(full_key, config)
        else:
            raise ValueError(f"Unknown rate limiting strategy: {config.strategy}")

    async def _sliding_window(
        self,
        key: str,
        config: RateLimitConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting"""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Use Redis sorted set for sliding window
        async with self.redis.pipeline() as pipe:
            # Remove old entries
            await pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            await pipe.zcard(key)

            # Add current request
            await pipe.zadd(key, {str(now): now})

            # Set expiration
            await pipe.expire(key, 60)

            results = await pipe.execute()
            current_requests = results[1]

        info = {
            "current_requests": current_requests,
            "limit": config.requests_per_minute,
            "remaining": max(0, config.requests_per_minute - current_requests),
            "reset_time": now + 60
        }

        return current_requests < config.requests_per_minute, info

    async def _token_bucket(
        self,
        key: str,
        config: RateLimitConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        now = time.time()
        bucket_key = f"{key}:bucket"

        # Get current bucket state
        bucket_data = await self.redis.hgetall(bucket_key)
        tokens = float(bucket_data.get("tokens", config.burst_size))
        last_refill = float(bucket_data.get("last_refill", now))

        # Refill tokens based on time passed
        time_passed = now - last_refill
        refill_rate = config.requests_per_minute / 60  # tokens per second
        new_tokens = min(config.burst_size, tokens + time_passed * refill_rate)

        # Check if request can be processed
        if new_tokens >= 1:
            tokens = new_tokens - 1

            # Update bucket state
            await self.redis.hset(bucket_key, mapping={
                "tokens": tokens,
                "last_refill": now
            })
            await self.redis.expire(bucket_key, 60)

            info = {
                "tokens": tokens,
                "capacity": config.burst_size,
                "refill_rate": refill_rate,
                "remaining_tokens": tokens
            }

            return True, info
        else:
            info = {
                "tokens": tokens,
                "capacity": config.burst_size,
                "refill_rate": refill_rate,
                "remaining_tokens": 0,
                "retry_after": 1 / refill_rate
            }

            return False, info

    async def _fixed_window(
        self,
        key: str,
        config: RateLimitConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        now = datetime.utcnow()
        window_key = f"{key}:{now.strftime('%Y%m%d%H%M')}"  # 1-minute windows

        # Increment counter
        current_requests = await self.redis.incr(window_key)

        # Set expiration for the window
        await self.redis.expire(window_key, 60)

        info = {
            "current_requests": current_requests,
            "limit": config.requests_per_minute,
            "remaining": max(0, config.requests_per_minute - current_requests),
            "reset_time": (now.replace(second=0, microsecond=0) + timedelta(minutes=1)).timestamp()
        }

        return current_requests <= config.requests_per_minute, info


class PerformanceMonitor:
    """Performance monitoring and analytics"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        metrics_retention: int = 86400 * 7,  # 7 days
        sample_rate: float = 1.0
    ):
        """
        Initialize performance monitor

        Args:
            redis_url: Redis connection URL
            metrics_retention: Retention period for metrics (seconds)
            sample_rate: Sampling rate (0.0 to 1.0)
        """
        self.redis_url = redis_url
        self.redis: Optional[redis_async.Redis] = None
        self.metrics_retention = metrics_retention
        self.sample_rate = sample_rate

        # Metrics storage
        self.metrics: deque = deque(maxlen=10000)
        self.real_time_stats: Dict[str, Any] = {}
        self.alert_rules: List[AlertRule] = []

        # Prometheus metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        self.active_requests = Gauge(
            'http_requests_active',
            'Active HTTP requests'
        )
        self.error_rate = Gauge(
            'http_error_rate',
            'HTTP error rate (5xx)'
        )

    async def initialize(self):
        """Initialize monitoring system"""
        self.redis = await redis_async.from_url(self.redis_url, decode_responses=True)

        # Load alert rules
        await self._load_alert_rules()

        # Start background tasks
        asyncio.create_task(self._update_real_time_stats())
        asyncio.create_task(self._check_alerts())

        logger.info("Performance monitor initialized")

    async def record_request(
        self,
        metrics: RequestMetrics
    ):
        """
        Record request metrics

        Args:
            metrics: Request metrics
        """
        # Sample based on rate
        import random
        if random.random() > self.sample_rate:
            return

        # Store in memory
        self.metrics.append(metrics)

        # Update Prometheus metrics
        self.request_count.labels(
            method=metrics.method,
            endpoint=metrics.path,
            status_code=str(metrics.status_code)
        ).inc()

        self.request_duration.labels(
            method=metrics.method,
            endpoint=metrics.path
        ).observe(metrics.response_time)

        # Store in Redis for analytics
        timestamp = metrics.timestamp.timestamp()
        await self._store_metrics(timestamp, metrics)

        # Update real-time stats
        self._update_stats(metrics)

    async def get_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> List[RequestMetrics]:
        """
        Get metrics with filters

        Args:
            start_time: Start time filter
            end_time: End time filter
            endpoint: Endpoint filter
            status_code: Status code filter

        Returns:
            Filtered metrics
        """
        # Query from Redis
        metrics = []

        # Generate time range
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)

        # Query Redis for metrics
        # Implementation depends on storage format
        # For now, use in-memory metrics

        for m in self.metrics:
            if m.timestamp < start_time or m.timestamp > end_time:
                continue
            if endpoint and m.path != endpoint:
                continue
            if status_code and m.status_code != status_code:
                continue
            metrics.append(m)

        return metrics

    async def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        # Calculate stats from recent metrics
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        recent_metrics = [m for m in self.metrics if m.timestamp >= recent_time]

        if not recent_metrics:
            return self.real_time_stats

        # Calculate aggregates
        response_times = [m.response_time for m in recent_metrics]
        error_count = sum(1 for m in recent_metrics if m.status_code >= 500)

        stats = {
            "requests_per_minute": len(recent_metrics),
            "avg_response_time": sum(response_times) / len(response_times),
            "p95_response_time": self._percentile(response_times, 95),
            "p99_response_time": self._percentile(response_times, 99),
            "error_rate": error_count / len(recent_metrics),
            "top_endpoints": self._get_top_endpoints(recent_metrics),
            "system_stats": await self._get_system_stats()
        }

        return stats

    async def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_rules.append(rule)
        await self._save_alert_rules()

    async def _store_metrics(self, timestamp: float, metrics: RequestMetrics):
        """Store metrics in Redis"""
        # Store in time series format
        key = f"metrics:{int(timestamp // 60)}:{int(timestamp % 60 * 1000)}"
        value = json.dumps(asdict(metrics), default=str)

        await self.redis.setex(key, self.metrics_retention, value)

    async def _load_alert_rules(self):
        """Load alert rules from storage"""
        # Implementation for loading rules from file or database
        pass

    async def _save_alert_rules(self):
        """Save alert rules to storage"""
        # Implementation for saving rules to file or database
        pass

    def _update_stats(self, metrics: RequestMetrics):
        """Update real-time statistics"""
        # Initialize if needed
        if "total_requests" not in self.real_time_stats:
            self.real_time_stats = {
                "total_requests": 0,
                "error_requests": 0,
                "total_response_time": 0,
                "requests_per_minute": 0,
                "last_minute_requests": deque(maxlen=60)
            }

        # Update counters
        self.real_time_stats["total_requests"] += 1
        if metrics.status_code >= 500:
            self.real_time_stats["error_requests"] += 1
        self.real_time_stats["total_response_time"] += metrics.response_time

        # Update per-minute counter
        self.real_time_stats["last_minute_requests"].append(metrics.timestamp)

    async def _update_real_time_stats(self):
        """Background task to update real-time statistics"""
        while True:
            try:
                # Calculate requests per minute
                if self.real_time_stats.get("last_minute_requests"):
                    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
                    recent_requests = [
                        t for t in self.real_time_stats["last_minute_requests"]
                        if t > one_minute_ago
                    ]
                    self.real_time_stats["requests_per_minute"] = len(recent_requests)

                # Update Prometheus gauge
                total_requests = self.real_time_stats.get("total_requests", 0)
                error_requests = self.real_time_stats.get("error_requests", 0)
                if total_requests > 0:
                    error_rate = error_requests / total_requests
                    self.error_rate.set(error_rate)

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                logger.error(f"Error updating real-time stats: {e}")
                await asyncio.sleep(30)

    async def _check_alerts(self):
        """Background task to check alert conditions"""
        while True:
            try:
                stats = await self.get_stats()

                for rule in self.alert_rules:
                    if not rule.enabled:
                        continue

                    # Check alert condition
                    metric_value = stats.get(rule.metric, 0)
                    triggered = False

                    if rule.operator == ">":
                        triggered = metric_value > rule.threshold
                    elif rule.operator == "<":
                        triggered = metric_value < rule.threshold
                    elif rule.operator == ">=":
                        triggered = metric_value >= rule.threshold
                    elif rule.operator == "<=":
                        triggered = metric_value <= rule.threshold
                    elif rule.operator == "==":
                        triggered = metric_value == rule.threshold

                    if triggered:
                        await self._trigger_alert(rule, metric_value)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
                await asyncio.sleep(60)

    async def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger alert action"""
        message = f"Alert: {rule.name} - {rule.metric} is {value} {rule.operator} {rule.threshold}"

        if rule.action == "log":
            logger.warning(message)
        elif rule.action == "email":
            # Send email alert
            pass
        elif rule.action == "webhook":
            # Send webhook alert
            pass

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _get_top_endpoints(self, metrics: List[RequestMetrics], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        endpoint_counts = defaultdict(int)
        for m in metrics:
            endpoint_counts[m.path] += 1

        sorted_endpoints = sorted(
            endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in sorted_endpoints[:limit]
        ]

    async def _get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3)
        }


class MonitoringMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for monitoring"""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        monitor: PerformanceMonitor,
        rate_limit_config: Optional[Dict[str, RateLimitConfig]] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.monitor = monitor
        self.rate_limit_config = rate_limit_config or {}

    async def dispatch(self, request: Request, call_next):
        """Process request with monitoring"""
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_id = request.headers.get("X-User-ID")
        user_agent = request.headers.get("User-Agent", "")

        # Rate limiting
        path = request.url.path
        if path in self.rate_limit_config:
            key = path.lstrip('/')
            config = self.rate_limit_config[key]

            # Check IP-based limit
            ip_allowed, ip_info = await self.rate_limiter.is_allowed(
                f"{key}:ip",
                config,
                client_ip
            )

            # Check user-based limit if user ID is present
            user_allowed = True
            user_info = {}
            if user_id:
                user_allowed, user_info = await self.rate_limiter.is_allowed(
                    f"{key}:user",
                    config,
                    user_id
                )

            if not ip_allowed or not user_allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(config.requests_per_minute),
                        "X-RateLimit-Remaining": str(ip_info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(int(ip_info.get("reset_time", 0)))
                    }
                )

        # Record start time
        start_time = time.time()
        active_requests = self.monitor.active_requests._value.get()
        self.monitor.active_requests.inc()

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            response_time = time.time() - start_time
            request_size = len(await request.body()) if hasattr(request, '_body') else 0
            response_size = len(response.body) if hasattr(response, 'body') else 0

            # Create metrics object
            metrics = RequestMetrics(
                timestamp=datetime.utcnow(),
                method=request.method,
                path=path,
                status_code=response.status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent
            )

            # Record metrics
            await self.monitor.record_request(metrics)

            # Add response headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"

            return response

        finally:
            # Decrement active requests
            self.monitor.active_requests.dec()


# Decorators for monitoring
def monitor_performance(monitor: PerformanceMonitor):
    """Decorator to monitor function performance"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"Function {func.__name__} took {duration:.3f}s [{status}]")
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Initialize components
        rate_limiter = RateLimiter()
        await rate_limiter.initialize()

        monitor = PerformanceMonitor()
        await monitor.initialize()

        # Add alert rule
        alert_rule = AlertRule(
            name="High Error Rate",
            metric="error_rate",
            threshold=0.05,  # 5%
            operator=">",
            action="log"
        )
        await monitor.add_alert_rule(alert_rule)

        # Test rate limiting
        config = RateLimitConfig(requests_per_minute=10)
        for i in range(15):
            allowed, info = await rate_limiter.is_allowed("test", config, "user123")
            print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'} - {info}")

        # Get stats
        stats = await monitor.get_stats()
        print(f"Performance stats: {stats}")

    # Run example
    asyncio.run(example_usage())