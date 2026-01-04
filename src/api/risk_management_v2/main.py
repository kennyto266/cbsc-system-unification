"""
Risk Management API v2 - Main Application
==========================================

Main FastAPI application for risk management API.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uuid

from .config import settings, create_directories, setup_logging
from .routes import router as risk_router
from .websocket import (
    websocket_risk_monitoring,
    websocket_alert_stream,
    monitor_connection_health,
    send_heartbeat_to_connections,
    manager
)
from .dependencies import get_database, get_risk_engine
from .middleware import (
    rate_limit_middleware,
    auth_middleware,
    audit_middleware,
    error_handler_middleware
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting Risk Management API v2...")

    # Create necessary directories
    create_directories()

    # Initialize database
    db = next(get_database())
    logger.info("Database initialized")

    # Start risk engine
    risk_engine = get_risk_engine()
    monitor_task = asyncio.create_task(risk_engine.start())
    logger.info("Risk engine started")

    # Start WebSocket monitoring tasks
    health_task = asyncio.create_task(monitor_connection_health())
    heartbeat_task = asyncio.create_task(send_heartbeat_to_connections())
    logger.info("WebSocket monitoring tasks started")

    yield

    # Shutdown
    logger.info("Shutting down Risk Management API v2...")

    # Stop risk engine
    await risk_engine.stop()
    logger.info("Risk engine stopped")

    # Cancel background tasks
    monitor_task.cancel()
    heartbeat_task.cancel()

    # Close database connection
    db.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Advanced risk analysis and management for quantitative trading strategies",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Custom middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(auth_middleware)
app.middleware("http")(audit_middleware)
app.middleware("http")(error_handler_middleware)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "type": "http_error"
            },
            "timestamp": time.time(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
                "type": "validation_error"
            },
            "timestamp": time.time(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Include routers
app.include_router(risk_router)


# WebSocket endpoints
@app.websocket("/ws/risk/monitoring/{connection_id}")
async def websocket_risk_monitoring_endpoint(websocket, connection_id: str):
    """WebSocket endpoint for real-time risk monitoring"""
    # Extract user ID from query params (in production, this would be from token)
    user_id = websocket.query_params.get("user_id", "anonymous")
    await websocket_risk_monitoring(websocket, connection_id, user_id)


@app.websocket("/ws/risk/alerts/{connection_id}")
async def websocket_alerts_endpoint(websocket, connection_id: str):
    """WebSocket endpoint for real-time alerts"""
    # Extract user ID from query params (in production, this would be from token)
    user_id = websocket.query_params.get("user_id", "anonymous")
    await websocket_alert_stream(websocket, connection_id, user_id)


# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "Risk Management API",
        "version": settings.api_version,
        "timestamp": time.time()
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies all dependencies are ready"""
    try:
        # Check database
        from sqlalchemy import text
        db = next(get_database())
        db.execute(text("SELECT 1"))
        db.close()

        # Check risk engine
        risk_engine = get_risk_engine()
        if not risk_engine.running:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "Risk engine not running"
                }
            )

        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                "risk_engine": "ok"
            }
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e)
            }
        )


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check - verifies the service is responsive"""
    return {
        "status": "alive",
        "timestamp": time.time()
    }


# Metrics endpoint (if Prometheus is enabled)
if settings.prometheus_enabled:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    @app.get("/metrics", tags=["Metrics"])
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import Counter, Histogram, Gauge, REGISTRY

        # Create metrics if they don't exist
        if "api_requests_total" not in REGISTRY._names_to_collectors:
            api_requests = Counter(
                "api_requests_total",
                "Total API requests",
                ["method", "endpoint", "status"]
            )
            api_request_duration = Histogram(
                "api_request_duration_seconds",
                "API request duration"
            )
            active_connections = Gauge(
                "websocket_active_connections",
                "Active WebSocket connections"
            )

            # Register metrics
            REGISTRY.register(api_requests)
            REGISTRY.register(api_request_duration)
            REGISTRY.register(active_connections)

        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": "Advanced risk analysis and management for quantitative trading strategies",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health": "/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Risk Management API v{settings.api_version} started successfully")
    logger.info(f"Server running on {settings.host}:{settings.port}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Risk Management API shutting down")


# Run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )