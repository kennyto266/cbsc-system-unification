"""
FastAPI Application Factory
FastAPI 應用工廠模式實現
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import get_settings
from ..core.exceptions import QuantSystemException, handle_exception
from ..core.logging import get_logger, log_system_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger = get_logger("api")

    # Startup
    logger.info("Starting Hong Kong Quantitative Trading System API")
    try:
        log_system_info()
        # Initialize services here
        logger.info("API system initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize API system: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down API system")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise-grade quantitative trading platform for Hong Kong stocks",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    setup_middleware(app)

    # Add exception handlers
    setup_exception_handlers(app)

    # Add routes
    setup_routes(app)

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Hong Kong Quantitative Trading System API",
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else "Documentation not available in production"
        }

    return app


def setup_middleware(app: FastAPI):
    """Setup custom middleware."""
    from ..core.logging import clear_request_context

    @app.middleware("http")
    async def add_request_id_middleware(request, call_next):
        """Add request ID and context to all requests."""
        import uuid
        request_id = str(uuid.uuid4())

        # Set request context
        from ..core.logging import set_request_context
        set_request_context(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()

    @app.middleware("http")
    async def logging_middleware(request, call_next):
        """Request logging middleware."""
        import time
        logger = get_logger("api.request")

        start_time = time.perf_counter()

        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_seconds=round(duration, 4)
            )

            return response

        except Exception as e:
            duration = time.perf_counter() - start_time

            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration_seconds=round(duration, 4)
            )
            raise


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers."""
    logger = get_logger("api.exceptions")

    @app.exception_handler(QuantSystemException)
    async def quant_system_exception_handler(request, exc: QuantSystemException):
        """Handle custom QuantSystem exceptions."""
        error_data = handle_exception(exc, context=f"API request: {request.url}")

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": error_data
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url)
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": "HTTPException",
                    "message": exc.detail,
                    "status_code": exc.status_code
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle general exceptions."""
        logger.error(
            "Unhandled exception",
            error_type=exc.__class__.__name__,
            error=str(exc),
            url=str(request.url),
            exc_info=True
        )

        error_data = handle_exception(exc, context=f"Unhandled API request: {request.url}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": error_data
            }
        )


def setup_routes(app: FastAPI):
    """Setup API routes."""
    try:
        # Import route modules
        from .routes import analysis, monitoring, multi_strategy, optimization

        # Register routes
        app.include_router(
            analysis.router,
            prefix="/api",
            tags=["analysis"],
            responses={404: {"description": "Not found"}}
        )

        app.include_router(
            optimization.router,
            prefix="/api",
            tags=["optimization"],
            responses={404: {"description": "Not found"}}
        )

        app.include_router(
            monitoring.router,
            prefix="/api",
            tags=["monitoring"],
            responses={404: {"description": "Not found"}}
        )

        app.include_router(
            multi_strategy.router,
            prefix="/api/multi-strategy",
            tags=["multi-strategy"],
            responses={404: {"description": "Not found"}}
        )

    except ImportError as e:
        logger = get_logger("api.setup")
        logger.warning(f"Could not import route modules: {e}")

        # Add placeholder routes when route modules are not available
        @app.get("/api/placeholder")
        async def placeholder():
            return {"message": "Route modules not yet implemented"}
