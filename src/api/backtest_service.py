"""
Integrated Backtest API Service
================================

Main service integration file that combines all Phase 5.2 components:
- Enhanced backtest API v2
- Configuration validation
- Async task queue
- Result caching
- Performance monitoring
- Rate limiting

Author: CBSC Quant Team
Version: 2.0.0
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .backtest_api_v2 import app as api_app
from .backtest_validator import BacktestConfigValidator, create_validator
from .task_queue import TaskQueue, task
from .result_cache import ResultCache, CacheConfig, cached
from .api_monitoring import RateLimiter, PerformanceMonitor, MonitoringMiddleware, RateLimitConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BacktestService:
    """Integrated backtest service manager"""

    def __init__(self):
        """Initialize the backtest service"""
        self.app: Optional[FastAPI] = None
        self.task_queue: Optional[TaskQueue] = None
        self.cache: Optional[ResultCache] = None
        self.validator: Optional[BacktestConfigValidator] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.monitor: Optional[PerformanceMonitor] = None

        # Configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load service configuration"""
        return {
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "api_host": os.getenv("API_HOST", "0.0.0.0"),
            "api_port": int(os.getenv("API_PORT", "8002")),
            "max_workers": int(os.getenv("MAX_WORKERS", "10")),
            "enable_monitoring": os.getenv("ENABLE_MONITORING", "true").lower() == "true",
            "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3004").split(","),
            "environment": os.getenv("ENVIRONMENT", "development")
        }

    async def initialize(self):
        """Initialize all service components"""
        logger.info("Initializing Backtest Service v2.0")

        try:
            # Initialize Redis-dependent components
            redis_url = self.config["redis_url"]

            # Initialize cache
            cache_config = CacheConfig(
                redis_url=redis_url,
                default_ttl=self.config["cache_ttl"]
            )
            self.cache = ResultCache(cache_config)
            await self.cache.initialize()
            logger.info("✓ Cache system initialized")

            # Initialize task queue
            self.task_queue = TaskQueue(
                redis_url=redis_url,
                max_workers=self.config["max_workers"]
            )
            await self.task_queue.start()
            logger.info("✓ Task queue initialized")

            # Initialize validator
            self.validator = create_validator()
            self.validator.data_provider = self  # Set data provider
            logger.info("✓ Validator initialized")

            # Initialize rate limiter
            self.rate_limiter = RateLimiter(redis_url=redis_url)
            await self.rate_limiter.initialize()
            logger.info("✓ Rate limiter initialized")

            # Initialize monitoring if enabled
            if self.config["enable_monitoring"]:
                self.monitor = PerformanceMonitor(redis_url=redis_url)
                await self.monitor.initialize()

                # Add default alert rules
                from .api_monitoring import AlertRule
                await self.monitor.add_alert_rule(AlertRule(
                    name="High Response Time",
                    metric="avg_response_time",
                    threshold=5.0,  # 5 seconds
                    operator=">"
                ))
                await self.monitor.add_alert_rule(AlertRule(
                    name="High Error Rate",
                    metric="error_rate",
                    threshold=0.05,  # 5%
                    operator=">"
                ))
                logger.info("✓ Monitoring system initialized")

            # Create FastAPI app with all middleware
            self.app = self._create_app()

            # Register task functions
            self._register_task_functions()

            logger.info("✅ Backtest Service initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize service: {e}")
            raise

    def _create_app(self) -> FastAPI:
        """Create FastAPI application with middleware"""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage application lifecycle"""
            # Startup
            logger.info("Backtest API starting up...")
            yield
            # Shutdown
            logger.info("Backtest API shutting down...")
            await self.shutdown()

        # Create FastAPI app
        app = FastAPI(
            title="CBSC Backtest API v2",
            description="Advanced backtesting service with risk management and analytics",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            lifespan=lifespan
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config["cors_origins"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

        # Add Gzip middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Add monitoring middleware if enabled
        if self.monitor and self.rate_limiter:
            rate_limit_configs = {
                "backtest": RateLimitConfig(requests_per_minute=10),
                "api/v2/backtest": RateLimitConfig(requests_per_minute=5),
                "batch": RateLimitConfig(requests_per_minute=2)
            }
            app.add_middleware(
                MonitoringMiddleware,
                rate_limiter=self.rate_limiter,
                monitor=self.monitor,
                rate_limit_config=rate_limit_configs
            )

        # Include API routes
        app.include_router(api_app, prefix="/api/v2")

        # Add health and stats endpoints
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "backtest-api-v2",
                "version": "2.0.0",
                "environment": self.config["environment"],
                "components": {
                    "task_queue": self.task_queue.is_running if self.task_queue else False,
                    "cache": self.cache is not None,
                    "monitoring": self.monitor is not None
                }
            }

        @app.get("/stats")
        async def get_stats():
            """Get service statistics"""
            stats = {
                "service": "backtest-api-v2",
                "timestamp": "2024-12-18T10:00:00Z",
                "task_queue": await self.task_queue.get_queue_stats() if self.task_queue else {},
                "cache": await self.cache.get_stats() if self.cache else {},
                "monitoring": await self.monitor.get_stats() if self.monitor else {}
            }
            return stats

        # Global exception handler
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logger.error(f"Global exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": str(id(request))
                }
            )

        return app

    def _register_task_functions(self):
        """Register task functions with the queue"""
        # Register backtest execution task
        @task("execute_backtest", self.task_queue)
        async def execute_backtest_task(
            task_id: str,
            request_data: Dict[str, Any],
            user_id: str
        ) -> Dict[str, Any]:
            """Execute backtest task"""
            from .backtest_api_v2 import execute_backtest
            await execute_backtest(task_id, request_data, user_id)
            return {"task_id": task_id, "status": "completed"}

        # Register batch processing task
        @task("process_batch", self.task_queue)
        async def process_batch_task(
            batch_id: str,
            requests: list[Dict[str, Any]],
            user_id: str
        ) -> Dict[str, Any]:
            """Process batch of backtest requests"""
            results = []
            for req in requests:
                # Create task for each request
                task_id = await self.task_queue.enqueue(
                    "execute_backtest",
                    args=(str(uuid.uuid4()), req, user_id)
                )
                results.append(task_id)
            return {"batch_id": batch_id, "task_ids": results}

        logger.info("✓ Task functions registered")

    async def shutdown(self):
        """Shutdown all service components"""
        logger.info("Shutting down Backtest Service...")

        if self.task_queue:
            await self.task_queue.stop()
            logger.info("✓ Task queue stopped")

        if self.cache:
            await self.cache.close()
            logger.info("✓ Cache connection closed")

        if self.rate_limiter:
            # Rate limiter doesn't need explicit shutdown
            pass

        logger.info("✅ Backtest Service shutdown complete")

    async def run(self):
        """Run the service"""
        await self.initialize()

        # Import uvicorn for running the server
        import uvicorn

        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            app=self.app,
            host=self.config["api_host"],
            port=self.config["api_port"],
            log_level=self.config["log_level"].lower(),
            access_log=True,
            reload=self.config["environment"] == "development"
        )

        # Create and run server
        server = uvicorn.Server(uvicorn_config)

        try:
            logger.info(f"Starting Backtest API on {self.config['api_host']}:{self.config['api_port']}")
            await server.serve()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.shutdown()


# Service instance
service = BacktestService()


# Convenience functions
async def get_service() -> BacktestService:
    """Get the global service instance"""
    if not service.app:
        await service.initialize()
    return service


def create_app() -> FastAPI:
    """Create FastAPI application"""
    return service.app


# For running directly
if __name__ == "__main__":
    import asyncio
    import uuid

    # Run the service
    asyncio.run(service.run())