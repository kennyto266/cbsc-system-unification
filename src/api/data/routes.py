"""
Data API v2 Routes
數據API v2路由

Main router for data service endpoints including market data, economic indicators, and export functionality
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter

# Import endpoint routers
from .market_data_endpoints import market_router
from .economic_data_endpoints import economic_router
from .export_endpoints import export_router

logger = logging.getLogger(__name__)

# Create v2 router for data API
data_router = APIRouter(prefix="/api/v2", tags=["data-v2"])

# Include all endpoint routers
data_router.include_router(market_router)
data_router.include_router(economic_router)
data_router.include_router(export_router)


# ============================================================================
# Version and Health Endpoints
# ============================================================================

@data_router.get("/data/version")
async def get_data_api_version():
    """
    獲取數據 API 版本信息

    Returns:
        API version and metadata
    """
    return {
        "version": "2.0.0",
        "name": "Quant Strategy Management Data API",
        "description": "RESTful API for market data, economic indicators, and data export",
        "features": {
            "market_data": True,
            "economic_indicators": True,
            "data_export": True,
            "real_time_data": True,
            "bulk_operations": True,
            "websocket_ready": True,
            "rate_limiting": True,
            "caching": True
        },
        "data_sources": {
            "influxdb": "Time-series database",
            "cache": "Redis caching",
            "websocket": "Real-time streaming"
        },
        "export_formats": ["csv", "json", "excel"],
        "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"],
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }


@data_router.get("/data/health")
async def health_check():
    """
    數據 API 健康檢查
    """
    # Check service health
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {}
    }

    # Check InfluxDB service
    try:
        from ...services.influxdb_client import InfluxDBService
        influxdb_service = InfluxDBService()
        # Try to ping InfluxDB
        # await influxdb_service.ping()
        health_status["services"]["influxdb"] = "healthy"
    except Exception as e:
        logger.error(f"InfluxDB health check failed: {e}")
        health_status["services"]["influxdb"] = f"unhealthy: {str(e)}"
        health_status["api"] = "degraded"

    # Check cache service
    try:
        from ...services.cache_service import CacheService
        cache_service = CacheService()
        # Try to set/get a test key
        await cache_service.set("health_check", "ok", expire=10)
        result = await cache_service.get("health_check")
        if result == "ok":
            health_status["services"]["cache"] = "healthy"
        else:
            health_status["services"]["cache"] = "degraded"
            health_status["api"] = "degraded"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["services"]["cache"] = f"unhealthy: {str(e)}"
        health_status["api"] = "degraded"

    # Check WebSocket service (if applicable)
    try:
        from ...websocket.websocket_server import WebSocketManager
        ws_manager = WebSocketManager()
        health_status["services"]["websocket"] = "healthy"
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        health_status["services"]["websocket"] = f"unhealthy: {str(e)}"

    return health_status


# ============================================================================
# Data Service Information Endpoints
# ============================================================================

@data_router.get("/data/info/market", response_model=Dict[str, Any])
async def get_market_data_info():
    """
    獲取市場數據服務信息

    Returns:
        Market data service capabilities and information
    """
    return {
        "service": "market_data",
        "description": "Historical and real-time market data service",
        "capabilities": {
            "historical_data": {
                "intervals": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"],
                "max_records_per_request": 10000,
                "supported_exchanges": ["NYSE", "NASDAQ", "HKEX", "LSE"],
                "data_points": ["open", "high", "low", "close", "volume", "adjusted_close"],
                "pre_post_market": True
            },
            "real_time_data": {
                "update_frequency": "real-time",
                "cache_duration": "30 seconds",
                "bulk_requests": True,
                "max_symbols_per_request": 100
            },
            "statistics": {
                "volatility_calculations": True,
                "moving_averages": True,
                "technical_indicators": ["SMA", "EMA", "RSI", "MACD", "BB"],
                "risk_metrics": ["sharpe_ratio", "max_drawdown", "beta"]
            }
        },
        "rate_limits": {
            "requests_per_minute": 1000,
            "requests_per_hour": 50000,
            "bulk_requests_per_hour": 100
        },
        "data_retention": {
            "tick_data": "7 days",
            "minute_data": "1 year",
            "daily_data": "10 years",
            "weekly_data": "20 years"
        }
    }


@data_router.get("/data/info/economic", response_model=Dict[str, Any])
async def get_economic_data_info():
    """
    獲取經濟指標數據服務信息

    Returns:
        Economic indicators service capabilities and information
    """
    return {
        "service": "economic_indicators",
        "description": "Global economic indicators and metrics",
        "categories": {
            "interest_rates": {
                "indicators": ["HIBOR", "Fed_Funds", "LIBOR", "EURIBOR"],
                "frequency": "daily",
                "sources": ["Central Banks", "ICE"]
            },
            "gdp": {
                "indicators": ["GDP_Growth", "GDP_Level", "GDP_Per_Capita"],
                "frequency": "quarterly",
                "sources": ["World Bank", "IMF", "National Statistics"]
            },
            "employment": {
                "indicators": ["Unemployment_Rate", "Non_Farm_Payrolls", "Labor_Participation"],
                "frequency": "monthly",
                "sources": ["BLS", "Eurostat"]
            },
            "inflation": {
                "indicators": ["CPI", "PPI", "Core_Inflation"],
                "frequency": "monthly",
                "sources": ["National Statistics Agencies"]
            },
            "pmi": {
                "indicators": ["Manufacturing_PMI", "Services_PMI", "Composite_PMI"],
                "frequency": "monthly",
                "sources": ["IHS Markit", "ISM"]
            }
        },
        "countries": ["US", "UK", "EU", "JP", "CN", "HK", "SG"],
        "update_schedule": {
            "daily_indicators": "16:00 UTC",
            "monthly_indicators": "Varies by country",
            "quarterly_indicators": "With GDP releases"
        }
    }


@data_router.get("/data/info/export", response_model=Dict[str, Any])
async def get_export_service_info():
    """
    獲取數據導出服務信息

    Returns:
        Data export service capabilities and information
    """
    return {
        "service": "data_export",
        "description": "Bulk data export service with background processing",
        "formats": {
            "csv": {
                "description": "Comma-separated values",
                "max_size": "1GB",
                "compression": "Available"
            },
            "json": {
                "description": "JavaScript Object Notation",
                "max_size": "500MB",
                "metadata": "Included by default"
            },
            "excel": {
                "description": "Microsoft Excel format",
                "max_size": "100MB",
                "sheets": "Multiple sheets supported"
            }
        },
        "processing": {
            "background_jobs": True,
            "max_concurrent_jobs": 10,
            "job_retention": "30 days",
            "email_notifications": "Configurable"
        },
        "limits": {
            "max_records_per_export": 1000000,
            "max_date_range": "10 years",
            "max_symbols_per_request": 1000,
            "export_timeout": "1 hour"
        },
        "features": [
            "Progress tracking",
            "Job cancellation",
            "Retry on failure",
            "Partial export support",
            "Delta exports",
            "Scheduled exports"
        ]
    }