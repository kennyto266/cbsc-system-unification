"""
Health Check API Endpoints
提供系統健康狀態檢查端點
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import aiohttp
import asyncio

from src.core.database import get_db
from src.services.cache_service import get_redis_client
from src.services.influxdb_client import get_influxdb_client

router = APIRouter()


class HealthStatus:
    """健康狀態枚舉"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@router.get("/health", summary="基本健康檢查")
async def health_check():
    """
    基本健康檢查端點
    返回服務基本狀態信息
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CBS-C Strategy Management System",
        "version": "2.0.0"
    }


@router.get("/health/detailed", summary="詳細健康檢查")
async def detailed_health_check(
    db: Session = Depends(get_db)
):
    """
    詳細健康檢查端點
    檢查所有依賴服務的狀態
    """
    health_info = {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CBS-C Strategy Management System",
        "version": "2.0.0",
        "checks": {}
    }

    # 檢查數據庫連接
    db_status = await check_database(db)
    health_info["checks"]["database"] = db_status

    # 檢查Redis連接
    redis_status = await check_redis()
    health_info["checks"]["redis"] = redis_status

    # 檢查InfluxDB連接
    influxdb_status = await check_influxdb()
    health_info["checks"]["influxdb"] = influxdb_status

    # 檢查外部API連接
    external_status = await check_external_apis()
    health_info["checks"]["external_apis"] = external_status

    # 檢查系統資源
    resource_status = await check_system_resources()
    health_info["checks"]["resources"] = resource_status

    # 確定整體健康狀態
    overall_status = determine_overall_status(health_info["checks"])
    health_info["status"] = overall_status

    # 根據狀態返回相應的HTTP狀態碼
    status_code = 200 if overall_status == HealthStatus.HEALTHY else 503

    return health_info, status_code


@router.get("/health/ready", summary="就緒檢查")
async def readiness_check(
    db: Session = Depends(get_db)
):
    """
    就緒檢查端點
    檢查服務是否準備好接收請求
    """
    checks = {
        "database": await check_database(db),
        "redis": await check_redis()
    }

    # 如果所有核心服務都健康，則服務就緒
    all_healthy = all(
        check["status"] == HealthStatus.HEALTHY
        for check in checks.values()
    )

    if all_healthy:
        return {
            "status": HealthStatus.HEALTHY,
            "ready": True,
            "checks": checks
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": HealthStatus.UNHEALTHY,
                "ready": False,
                "checks": checks
            }
        )


@router.get("/health/live", summary="存活檢查")
async def liveness_check():
    """
    存活檢查端點
    檢查服務是否存活（簡單檢查）
    """
    return {
        "status": HealthStatus.HEALTHY,
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


async def check_database(db: Session) -> Dict[str, Any]:
    """檢查數據庫連接狀態"""
    try:
        # 執行簡單查詢測試連接
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # 獲取連接池狀態
        pool_status = {
            "status": HealthStatus.HEALTHY,
            "connection_pool": {
                "size": db.connection().pool.size(),
                "checked_in": db.connection().pool.checkedin(),
                "checked_out": db.connection().pool.checkedout()
            }
        }

        return {
            "status": HealthStatus.HEALTHY,
            "message": "數據庫連接正常",
            "details": pool_status
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"數據庫連接失敗: {str(e)}",
            "error": str(e)
        }


async def check_redis() -> Dict[str, Any]:
    """檢查Redis連接狀態"""
    try:
        redis_client = get_redis_client()

        # 測試基本操作
        await redis_client.ping()

        # 獲取Redis信息
        info = await redis_client.info()

        return {
            "status": HealthStatus.HEALTHY,
            "message": "Redis連接正常",
            "details": {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Redis連接失敗: {str(e)}",
            "error": str(e)
        }


async def check_influxdb() -> Dict[str, Any]:
    """檢查InfluxDB連接狀態"""
    try:
        influxdb_client = get_influxdb_client()

        # 測試連接
        health = influxdb_client.health()

        if health.status == "pass":
            return {
                "status": HealthStatus.HEALTHY,
                "message": "InfluxDB連接正常",
                "details": {
                    "version": health.version
                }
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"InfluxDB健康檢查失敗: {health.message}"
            }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"InfluxDB連接失敗: {str(e)}",
            "error": str(e)
        }


async def check_external_apis() -> Dict[str, Any]:
    """檢查外部API連接狀態"""
    apis = {
        "futu_api": "https://openapi.futunn.com",
        "market_data": "https://api.marketdata.com"
    }

    results = {}
    overall_status = HealthStatus.HEALTHY

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in apis.items():
            tasks.append(check_api_endpoint(session, name, url))

        api_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in api_results:
            if isinstance(result, Exception):
                overall_status = HealthStatus.DEGRADED
                continue
            results[result["name"]] = result
            if result["status"] != HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

    return {
        "status": overall_status,
        "message": "外部API連接檢查完成",
        "apis": results
    }


async def check_api_endpoint(session: aiohttp.ClientSession, name: str, url: str) -> Dict[str, Any]:
    """檢查單個API端點"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status < 400:
                return {
                    "name": name,
                    "status": HealthStatus.HEALTHY,
                    "response_time": response.headers.get("X-Response-Time"),
                    "status_code": response.status
                }
            else:
                return {
                    "name": name,
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"API返回錯誤狀態碼: {response.status}",
                    "status_code": response.status
                }
    except asyncio.TimeoutError:
        return {
            "name": name,
            "status": HealthStatus.UNHEALTHY,
            "message": "API請求超時"
        }
    except Exception as e:
        return {
            "name": name,
            "status": HealthStatus.UNHEALTHY,
            "message": f"API連接失敗: {str(e)}",
            "error": str(e)
        }


async def check_system_resources() -> Dict[str, Any]:
    """檢查系統資源狀態"""
    import psutil

    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 內存使用率
        memory = psutil.virtual_memory()

        # 磁盤使用率
        disk = psutil.disk_usage('/')

        # 判斷資源狀態
        status = HealthStatus.HEALTHY
        warnings = []

        if cpu_percent > 80:
            status = HealthStatus.DEGRADED
            warnings.append(f"CPU使用率過高: {cpu_percent}%")

        if memory.percent > 85:
            status = HealthStatus.DEGRADED
            warnings.append(f"內存使用率過高: {memory.percent}%")

        if disk.percent > 90:
            status = HealthStatus.DEGRADED
            warnings.append(f"磁盤使用率過高: {disk.percent}%")

        return {
            "status": status,
            "message": "系統資源檢查完成",
            "warnings": warnings,
            "resources": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"系統資源檢查失敗: {str(e)}",
            "error": str(e)
        }


def determine_overall_status(checks: Dict[str, Any]) -> str:
    """根據各項檢查結果確定整體健康狀態"""
    if not checks:
        return HealthStatus.UNHEALTHY

    statuses = [
        check.get("status")
        for check in checks.values()
        if isinstance(check, dict) and "status" in check
    ]

    # 如果有任一核心服務不健康，整體狀態為不健康
    core_services = ["database", "redis"]
    for service in core_services:
        if service in checks and checks[service].get("status") == HealthStatus.UNHEALTHY:
            return HealthStatus.UNHEALTHY

    # 如果有任一服務降級，整體狀態為降級
    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED

    # 所有服務健康
    return HealthStatus.HEALTHY


@router.get("/metrics", summary="Prometheus指標端點")
async def metrics():
    """
    Prometheus指標收集端點
    返回系統指標數據
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    # 此處需要實現Prometheus指標收集邏輯
    # 返回指標數據
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/version", summary="版本信息")
async def version_info():
    """
    獲取應用版本信息
    """
    return {
        "version": "2.0.0",
        "build_date": "2025-12-19T10:00:00Z",
        "git_commit": "abc123def456",
        "python_version": "3.11.0",
        "fastapi_version": "0.104.1"
    }