"""
Persistent Context Storage Service
持久化上下文存储服务

This service provides AI-assisted development context persistence across sessions
with automatic saves, compression, search capabilities, and team collaboration.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理
    Startup and shutdown logic for the application
    """
    # Startup logic
    logger.info("Starting Persistent Context Storage Service...")

    # Ensure required directories exist
    directories = [
        "data",           # Database directory
        "storage",        # Compressed context files
        "search_index",   # Whoosh search index
        "logs"            # Log files
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

    # Initialize environment variables with defaults
    os.environ.setdefault("DATABASE_URL", "data/contexts.db")
    os.environ.setdefault("STORAGE_PATH", "storage")
    os.environ.setdefault("SEARCH_INDEX_PATH", "search_index")
    os.environ.setdefault("AUTO_SAVE_INTERVAL", "300")  # 5 minutes
    os.environ.setdefault("COMPRESSION_LEVEL", "6")

    # Initialize SQLAlchemy database
    from config.database import init_sqlalchemy_database
    if init_sqlalchemy_database():
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed")

    logger.info("Service startup completed successfully")

    yield

    # Shutdown logic
    logger.info("Shutting down Persistent Context Storage Service...")
    # Clean up resources here if needed
    logger.info("Service shutdown completed")

# Create FastAPI application
app = FastAPI(
    title="Persistent Context Storage Service",
    description="AI-assisted development context persistence with auto-save, compression, and search",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    健康检查端点
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "persistent-context-storage",
        "version": "1.0.0"
    }

# Import API routers
try:
    from api import context_router, session_router, team_router
    logger.info("Successfully imported context_router, session_router and team_router")
    app.include_router(context_router, prefix="/api", tags=["contexts"])
    app.include_router(session_router, prefix="/api", tags=["sessions"])
    app.include_router(team_router, prefix="/api/team", tags=["team", "sharing", "permissions"])
    logger.info("Successfully included context_router, session_router and team_router")
except Exception as e:
    logger.error(f"Failed to import or include routers: {e}")
    import traceback
    traceback.print_exc()

# Root endpoint
@app.get("/")
async def root():
    """
    根端点
    Root endpoint
    """
    return {
        "message": "Persistent Context Storage Service",
        "description": "AI-assisted development context persistence with auto-save, compression, and search",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3007,
        reload=True,
        log_level="info"
    )