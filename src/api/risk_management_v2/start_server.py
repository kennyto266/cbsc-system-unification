"""
Risk Management API v2 - Server Startup Script
==============================================

Startup script for the Risk Management API server.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.risk_management_v2.main import app
from src.api.risk_management_v2.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

if settings.log_file:
    file_handler = logging.FileHandler(settings.log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)


def create_directories():
    """Create necessary directories"""
    directories = [
        settings.reports_dir,
        "./logs",
        "./temp"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def check_dependencies():
    """Check if all required dependencies are available"""
    required_services = {
        "Database": settings.database_url,
        "Redis": settings.redis_url
    }

    # Check database connection
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

    # Check Redis connection
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False

    # Check InfluxDB (if configured)
    if settings.influxdb_host:
        try:
            from influxdb_client import InfluxDBClient
            client = InfluxDBClient(
                url=f"http://{settings.influxdb_host}:{settings.influxdb_port}",
                token="test"  # We'll test connection without auth
            )
            # Note: This is a basic check - InfluxDB connection might need more complex validation
            logger.info("✓ InfluxDB configuration found")
        except Exception as e:
            logger.warning(f"⚠ InfluxDB might not be available: {e}")

    return True


def main():
    """Main function to start the server"""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info("=" * 60)

    # Create directories
    create_directories()

    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Exiting.")
        sys.exit(1)

    # Log configuration
    logger.info(f"Server host: {settings.host}")
    logger.info(f"Server port: {settings.port}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'sqlite'}")
    logger.info(f"Redis URL: {settings.redis_url.split('@')[-1] if '@' in settings.redis_url else 'localhost'}")

    # Import and run uvicorn
    import uvicorn

    config = uvicorn.Config(
        app=app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True,
        # Performance settings
        workers=1 if settings.reload else 4,
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=5
    )

    server = uvicorn.Server(config)

    try:
        logger.info("\n" + "=" * 60)
        logger.info("Starting server...")
        logger.info(f"API Documentation: http://{settings.host}:{settings.port}/docs")
        logger.info(f"ReDoc Documentation: http://{settings.host}:{settings.port}/redoc")
        logger.info(f"Health Check: http://{settings.host}:{settings.port}/health")
        logger.info("=" * 60 + "\n")

        server.run()

    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt. Shutting down gracefully...")
        server.should_exit = True
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()