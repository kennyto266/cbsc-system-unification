"""
CBSC 策略管理系統 - 健康檢查端點
Health check endpoints for CBSC Strategy Management System
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import psutil
import redis
import asyncpg
import aiohttp
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_db
from src.core.logging import logger
from src.api.strategies.v2.routes import router as strategies_router
from src.services.strategy_service_v2 import StrategyServiceV2
from src.services.cache_service import CacheService

# Create health check router
health_router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

# Response models
class HealthStatus(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    checks: Dict[str, Dict[str, Any]]

class CheckResult(BaseModel):
    """Individual check result model"""
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    duration_ms: float
    metadata: Optional[Dict[str, Any]] = None

# Global variables for uptime tracking
start_time = time.time()

class HealthChecker:
    """Health check service"""

    def __init__(self):
        self.cache_service = CacheService()
        self.strategy_service = StrategyServiceV2()

    async def get_system_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - start_time

    async def check_database(self) -> CheckResult:
        """Check database connectivity and health"""
        start_time_check = time.time()

        try:
            # Test database connection
            db: Session = next(get_db())

            # Simple query to test connectivity
            result = db.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()

            if row and row[0] == 1:
                duration = (time.time() - start_time_check) * 1000

                # Get additional database stats
                try:
                    db_stats = db.execute(text("""
                        SELECT
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections
                        FROM pg_stat_activity
                    """))
                    stats = db_stats.fetchone()

                    metadata = {
                        "total_connections": stats[0] if stats else 0,
                        "active_connections": stats[1] if stats else 0,
                    }
                except Exception as e:
                    logger.warning(f"Could not get database stats: {e}")
                    metadata = {}

                return CheckResult(
                    status="healthy",
                    message="Database connection successful",
                    duration_ms=duration,
                    metadata=metadata
                )
            else:
                return CheckResult(
                    status="unhealthy",
                    message="Database query failed",
                    duration_ms=(time.time() - start_time_check) * 1000
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

    async def check_redis(self) -> CheckResult:
        """Check Redis connectivity and health"""
        start_time_check = time.time()

        try:
            # Test Redis connection
            cache_service = CacheService()

            # Set a test key and retrieve it
            test_key = f"health_check_{int(time.time())}"
            test_value = "test"

            await cache_service.set(test_key, test_value, ttl=10)
            retrieved_value = await cache_service.get(test_key)

            # Clean up test key
            await cache_service.delete(test_key)

            if retrieved_value == test_value:
                # Get Redis info
                try:
                    redis_info = await cache_service.client.info()
                    metadata = {
                        "used_memory": redis_info.get('used_memory_human'),
                        "connected_clients": redis_info.get('connected_clients'),
                        "uptime_in_seconds": redis_info.get('uptime_in_seconds'),
                    }
                except Exception:
                    metadata = {}

                return CheckResult(
                    status="healthy",
                    message="Redis connection successful",
                    duration_ms=(time.time() - start_time_check) * 1000,
                    metadata=metadata
                )
            else:
                return CheckResult(
                    status="unhealthy",
                    message="Redis test operation failed",
                    duration_ms=(time.time() - start_time_check) * 1000
                )

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"Redis connection failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

    async def check_influxdb(self) -> CheckResult:
        """Check InfluxDB connectivity and health"""
        start_time_check = time.time()

        try:
            # Check InfluxDB health endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://influxdb:8086/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()

                        metadata = {
                            "name": health_data.get("name"),
                            "message": health_data.get("message"),
                            "checks": health_data.get("checks", {}),
                        }

                        return CheckResult(
                            status="healthy",
                            message="InfluxDB connection successful",
                            duration_ms=(time.time() - start_time_check) * 1000,
                            metadata=metadata
                        )
                    else:
                        return CheckResult(
                            status="unhealthy",
                            message=f"InfluxDB health check failed with status {response.status}",
                            duration_ms=(time.time() - start_time_check) * 1000
                        )

        except asyncio.TimeoutError:
            return CheckResult(
                status="unhealthy",
                message="InfluxDB connection timeout",
                duration_ms=(time.time() - start_time_check) * 1000
            )
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"InfluxDB connection failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

    async def check_external_services(self) -> CheckResult:
        """Check external services connectivity"""
        start_time_check = time.time()

        try:
            # List of external services to check
            services = [
                {"name": "market_data", "url": "http://market-data-service:8080/health"},
                {"name": "notification", "url": "http://notification-service:8081/health"},
            ]

            healthy_services = []
            unhealthy_services = []

            async with aiohttp.ClientSession() as session:
                for service in services:
                    try:
                        async with session.get(
                            service["url"],
                            timeout=aiohttp.ClientTimeout(total=3)
                        ) as response:
                            if response.status == 200:
                                healthy_services.append(service["name"])
                            else:
                                unhealthy_services.append(service["name"])
                    except Exception:
                        unhealthy_services.append(service["name"])

            duration = (time.time() - start_time_check) * 1000

            if unhealthy_services:
                status = "degraded" if healthy_services else "unhealthy"
                message = f"Unhealthy services: {', '.join(unhealthy_services)}"
            else:
                status = "healthy"
                message = "All external services healthy"

            metadata = {
                "healthy_services": healthy_services,
                "unhealthy_services": unhealthy_services,
                "total_services": len(services)
            }

            return CheckResult(
                status=status,
                message=message,
                duration_ms=duration,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"External services check failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

    async def check_disk_space(self) -> CheckResult:
        """Check disk space availability"""
        start_time_check = time.time()

        try:
            disk_usage = psutil.disk_usage('/')

            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_gb = disk_usage.free / (1024**3)

            duration = (time.time() - start_time_check) * 1000

            # Determine status based on usage
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 80:
                status = "degraded"
            else:
                status = "healthy"

            metadata = {
                "total_gb": disk_usage.total / (1024**3),
                "used_gb": disk_usage.used / (1024**3),
                "free_gb": free_gb,
                "used_percent": round(used_percent, 2),
            }

            message = f"Disk usage: {used_percent:.1f}% ({free_gb:.1f}GB free)"

            return CheckResult(
                status=status,
                message=message,
                duration_ms=duration,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"Disk space check failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

    async def check_memory_usage(self) -> CheckResult:
        """Check memory usage"""
        start_time_check = time.time()

        try:
            memory = psutil.virtual_memory()

            used_percent = memory.percent
            available_gb = memory.available / (1024**3)

            duration = (time.time() - start_time_check) * 1000

            # Determine status based on usage
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 80:
                status = "degraded"
            else:
                status = "healthy"

            metadata = {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "available_gb": available_gb,
                "used_percent": round(used_percent, 2),
            }

            message = f"Memory usage: {used_percent:.1f}% ({available_gb:.1f}GB available)"

            return CheckResult(
                status=status,
                message=message,
                duration_ms=duration,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
            return CheckResult(
                status="unhealthy",
                message=f"Memory usage check failed: {str(e)}",
                duration_ms=(time.time() - start_time_check) * 1000
            )

# Create health checker instance
health_checker = HealthChecker()

@health_router.get("/")
async def health_check() -> HealthStatus:
    """
    Main health check endpoint
    Returns overall system health status
    """
    overall_status = "healthy"
    checks = {}

    # Run all health checks concurrently
    check_tasks = {
        "database": health_checker.check_database(),
        "redis": health_checker.check_redis(),
        "influxdb": health_checker.check_influxdb(),
        "disk_space": health_checker.check_disk_space(),
        "memory": health_checker.check_memory_usage(),
        "external_services": health_checker.check_external_services(),
    }

    # Execute all checks
    results = await asyncio.gather(*check_tasks.values(), return_exceptions=True)

    # Process results
    for i, (check_name, check_result) in enumerate(zip(check_tasks.keys(), results)):
        if isinstance(check_result, Exception):
            # Handle unexpected errors
            checks[check_name] = {
                "status": "unhealthy",
                "message": f"Health check error: {str(check_result)}",
                "duration_ms": 0,
                "metadata": None
            }
            overall_status = "unhealthy"
        else:
            checks[check_name] = check_result.dict()

            # Update overall status
            if check_result.status == "unhealthy":
                overall_status = "unhealthy"
            elif check_result.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version="2.0.0",  # Should be updated from version file
        uptime=await health_checker.get_system_uptime(),
        checks=checks
    )

@health_router.get("/simple")
async def simple_health_check() -> Dict[str, str]:
    """
    Simple health check for load balancers
    Returns minimal information for quick health checks
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

@health_router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes
    Checks if the application is ready to serve traffic
    """
    # Check critical components only
    critical_checks = [
        health_checker.check_database(),
        health_checker.check_redis(),
    ]

    results = await asyncio.gather(*critical_checks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception) or result.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@health_router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes
    Checks if the application is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@health_router.get("/db")
async def database_health_check() -> CheckResult:
    """
    Database-specific health check
    """
    return await health_checker.check_database()

@health_router.get("/redis")
async def redis_health_check() -> CheckResult:
    """
    Redis-specific health check
    """
    return await health_checker.check_redis()

@health_router.get("/influxdb")
async def influxdb_health_check() -> CheckResult:
    """
    InfluxDB-specific health check
    """
    return await health_checker.check_influxdb()

@health_router.get("/external")
async def external_services_health_check() -> CheckResult:
    """
    External services health check
    """
    return await health_checker.check_external_services()

# Export the health router for use in main app
__all__ = ["health_router"]