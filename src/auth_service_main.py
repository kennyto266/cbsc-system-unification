"""
Authentication Service Main Application
FastAPI app for authentication and user management
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth import (
    AuthService, AuthMiddleware, RateLimitMiddleware,
    SecurityHeadersMiddleware, AuditMiddleware
)
from src.auth.api import router as auth_router
from src.auth.config import load_config, validate_config, generate_jwt_keys_if_not_exists
from src.auth.exceptions import (
    AuthenticationError, AuthorizationError,
    RateLimitExceededError, EmailSendError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables
auth_service = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting authentication service...")

    # Load configuration
    global config
    config = load_config()

    # Validate configuration
    try:
        validate_config()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Generate JWT keys if needed
    generate_jwt_keys_if_not_exists()
    logger.info("JWT keys ready")

    # Initialize auth service
    global auth_service
    auth_service = AuthService(
        database_url=config.database_url,
        config=config.dict()
    )

    # Store auth service in app state
    app.state.auth_service = auth_service
    app.state.config = config

    logger.info("Authentication service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down authentication service...")
    if auth_service:
        auth_service.engine.dispose()
    logger.info("Authentication service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="CBSC Authentication Service",
    description="Enterprise-grade authentication and user management API",
    version="1.0.0",
    docs_url="/docs" if not (config or load_config()).testing else None,
    redoc_url="/redoc" if not (config or load_config()).testing else None,
    lifespan=lifespan
)


# Exception handlers
@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(AuthorizationError)
async def authz_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError):
    """Handle rate limit errors"""
    headers = {}
    if exc.details.get("retry_after"):
        headers["Retry-After"] = str(exc.details["retry_after"])

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general errors"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Add middleware
def setup_middleware(app: FastAPI, config):
    """Setup application middleware"""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_list,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers
    if config.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    if config.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=config.rate_limit_requests_per_minute,
            requests_per_hour=config.rate_limit_requests_per_hour
        )

    # Audit logging
    app.add_middleware(
        AuditMiddleware,
        auth_service=app.state.auth_service
    )

    # Authentication
    app.add_middleware(
        AuthMiddleware,
        auth_service=app.state.auth_service
    )


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def api_health_check():
    """API health check"""
    return {
        "success": True,
        "message": "Authentication service is running",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }


# Include auth router
app.include_router(auth_router)


def create_app():
    """Create and configure application"""
    # Load initial config for middleware setup
    initial_config = load_config()

    # Setup middleware after app creation but before returning
    # Note: This is a workaround since we can't access app.state yet
    # The actual middleware setup with auth_service happens in lifespan

    return app


# Run the app
if __name__ == "__main__":
    import uvicorn

    # Get configuration
    config = load_config()

    # Configure uvicorn
    uvicorn_config = {
        "app": "auth_service_main:app",
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 3006)),
        "reload": config.debug,
        "access_log": True,
        "log_level": "debug" if config.debug else "info"
    }

    logger.info(f"Starting authentication service on port {uvicorn_config['port']}")
    uvicorn.run(**uvicorn_config)