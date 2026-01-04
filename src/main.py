"""
CBSC Strategy Management System Backend API
CBSC 策略管理系統後端 API

Main FastAPI application entry point
主要的 FastAPI 應用程序入口點
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import uvicorn

# Add src to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from core.database import engine, Base

# Import logger first for error reporting
import logging
logger = logging.getLogger(__name__)

# Import v1 API routers with fallbacks
try:
    from api.v1 import auth, strategies, users
except ImportError as e:
    logger.warning(f"Warning: Some v1 modules not available: {e}")
    auth, strategies, users = None, None, None

# Import auth endpoints with real authentication
try:
    from api.auth_endpoints import router as auth_endpoints_router
except ImportError:
    logger.warning("Auth endpoints router not available")
    auth_endpoints_router = None

# Import monitoring and rbac optionally
try:
    from api.v1 import monitoring, rbac
except ImportError:
    monitoring, rbac = None, None

# Import v2 routers with fallbacks
try:
    from api.strategies.v2 import routes as strategies_v2
except ImportError:
    strategies_v2 = None
    logger.warning("strategies_v2 not available")

# Optional unified routers (may not be available)
try:
    from api.strategies.v2 import unified_crud_router
except (ImportError, AttributeError):
    unified_crud_router = None

try:
    from api.strategies.v2 import unified_operation_router
except (ImportError, AttributeError):
    unified_operation_router = None
try:
    from api.auth.auth_endpoints_v2 import router as auth_v2_router
except ImportError:
    auth_v2_router = None
try:
    from api.users.v2 import routes as users_v2
except ImportError:
    users_v2 = None

# Optional data router (requires influxdb_client)
try:
    from api.data.routes import data_router
    DATA_ROUTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Data router not available: {e}")
    DATA_ROUTER_AVAILABLE = False
    data_router = None

# Import middleware with fallbacks
try:
    from middleware.rate_limit_middleware import create_rate_limit_middleware, initialize_rate_limiting
except ImportError:
    logger.warning("Rate limit middleware not available")
    create_rate_limit_middleware = None
    async def initialize_rate_limiting(): pass

try:
    from middleware.security_audit_middleware import create_security_audit_middleware
except ImportError:
    logger.warning("Security audit middleware not available")
    create_security_audit_middleware = None

try:
    from middleware.auth_middleware import (
        require_permissions,
        require_role,
        get_current_user_with_permissions
    )
except ImportError:
    logger.warning("Auth middleware not available")
    require_permissions = None
    require_role = None
    get_current_user_with_permissions = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    應用程序生命週期管理器
    """
    # Startup
    logger.info("Starting CBSC Strategy Management System API...")

    # Initialize rate limiting
    await initialize_rate_limiting()
    logger.info("Rate limiting initialized")

    # Initialize security audit logging (already initialized at module load)
    # from security.audit_logger import initialize_audit_logging
    # await initialize_audit_logging()
    logger.info("Security audit logging initialized")

    # Initialize anomaly detection
    # from security.anomaly_detector import initialize_anomaly_detection
    # await initialize_anomaly_detection()
    # logger.info("Anomaly detection initialized")

    # Add middleware after app is created
    # Security audit middleware (first to capture all requests)
    if create_security_audit_middleware:
        security_middleware = create_security_audit_middleware(app)
    else:
        logger.warning("Security audit middleware not available")

    # Rate limiting middleware
    if create_rate_limit_middleware:
        rate_middleware = create_rate_limit_middleware(app)
    else:
        logger.warning("Rate limit middleware not available")

    logger.info("Security middleware initialized")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")
    logger.info("CBSC Strategy Management System API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down CBSC Strategy Management System API...")


# Create FastAPI application
app = FastAPI(
    title="CBSC Strategy Management System API",
    description="CBSC量化交易策略管理系統API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Add CORS middleware
try:
    cors_origins = settings.api.cors_origins
    cors_allow_credentials = settings.api.cors_allow_credentials
    cors_allow_methods = settings.api.cors_allow_methods
    cors_allow_headers = settings.api.cors_allow_headers
except AttributeError:
    # Fallback to defaults if api settings not available
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:8888",
        "http://192.168.1.5:3000",
        "http://192.168.1.5:3006",
        "http://127.0.0.1:3000",
        "null"  # Support for file:// protocol (opening HTML directly)
    ]
    cors_allow_credentials = True
    cors_allow_methods = ["*"]
    cors_allow_headers = ["*"]
    logger.warning("API settings not available, using default CORS configuration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=cors_allow_methods,
    allow_headers=cors_allow_headers,
)


# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure based on your environment
)


# Note: Security middleware is added in lifespan function


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time header to responses
    為響應添加處理時間頭部
    """
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    全局異常處理器
    """
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error occurred"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    根端點
    """
    return {
        "message": "CBSC Strategy Management System API",
        "version": "1.0.0",
        "status": "running"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    健康檢查端點
    """
    try:
        # Check database connection
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# API Routes
# Include auth endpoints with real authentication (prefix already set in router)
if auth_endpoints_router and hasattr(auth_endpoints_router, 'routes'):
    app.include_router(auth_endpoints_router)
    logger.info("Auth endpoints router included (real authentication)")

if auth and hasattr(auth, 'router'):
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )

# Include Dashboard API router FIRST (before strategies router to override)
# This provides unauthenticated access for frontend development
try:
    from api.dashboard_api import router as dashboard_router
    app.include_router(
        dashboard_router,
        tags=["Dashboard"]
    )
    logger.info("Dashboard API router included (unauthenticated access)")
except ImportError as e:
    logger.warning(f"Dashboard API not available: {e}")

if strategies and hasattr(strategies, 'router'):
    app.include_router(
        strategies.router,
        prefix="/api/v1/strategies",
        tags=["Strategies"]
    )

if users and hasattr(users, 'router'):
    app.include_router(
        users.router,
        prefix="/api/v1/users",
        tags=["Users"]
    )

if monitoring and hasattr(monitoring, 'router'):
    app.include_router(
        monitoring.router,
        prefix="/api/v1/monitoring",
        tags=["Monitoring"]
    )

if rbac and hasattr(rbac, 'router'):
    app.include_router(
        rbac.router,
        prefix="/api/v1/rbac",
        tags=["RBAC"]
    )

# Include v2 API routers
if DATA_ROUTER_AVAILABLE and data_router:
    app.include_router(
        data_router,
        tags=["Data API v2"]
    )

if strategies_v2 and hasattr(strategies_v2, 'router'):
    app.include_router(
        strategies_v2.router,
        tags=["Strategies v2"]
    )

# Include unified strategy routers (NEW - consolidates 3 managers)
if unified_crud_router:
    app.include_router(
        unified_crud_router,
        tags=["Strategies Unified CRUD"]
    )

if unified_operation_router:
    app.include_router(
        unified_operation_router,
        tags=["Strategies Unified Operations"]
    )

# Include authentication v2 router
if auth_v2_router:
    app.include_router(
        auth_v2_router,
        tags=["Authentication v2"]
    )

# Include users v2 router
if users_v2 and hasattr(users_v2, 'router'):
    app.include_router(
        users_v2.router,
        tags=["Users v2"]
    )

# Include security API router
try:
    from api.v1 import security
    if hasattr(security, 'router'):
        app.include_router(
            security.router,
            tags=["Security"]
        )
except ImportError:
    pass

# Include VectorBT Simple API router
try:
    from api.vectorbt_simple_api import router as vectorbt_router
    app.include_router(
        vectorbt_router,
        tags=["VectorBT"]
    )
    logger.info("VectorBT Simple API router included")
except ImportError as e:
    logger.warning(f"VectorBT Simple API not available: {e}")

# Note: Security endpoints are now in api/v1/security.py

# Import and integrate all agent-developed components
try:
    from integration.agent_integration import integrate_all_components

    # Integrate all components
    integration_results = integrate_all_components(app)

    if not integration_results["success"]:
        logger.warning("Some components failed to integrate. Check logs for details.")

except ImportError as e:
    logger.error(f"Failed to import integration module: {e}")
except Exception as e:
    logger.error(f"Integration failed: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level="info"
    )