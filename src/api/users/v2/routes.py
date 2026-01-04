"""
User API v2 Routes
用戶管理 API v2 路由

Main router registration for user management v2 API endpoints
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter

# Import endpoint router
from .user_endpoints import router as user_router

logger = logging.getLogger(__name__)

# Create v2 router
router = APIRouter(prefix="/api/v2", tags=["users-v2"])

# Include user management endpoints
router.include_router(user_router)


# ============================================================================
# Version and Metadata Endpoints
# ============================================================================

@router.get("/version")
async def get_api_version():
    """
    獲取 API 版本信息

    Returns:
        API version and metadata
    """
    return {
        "version": "2.0.0",
        "name": "User Management API",
        "description": "RESTful API for user management",
        "features": {
            "profile_management": True,
            "password_management": True,
            "mfa_support": True,
            "user_preferences": True,
            "api_key_management": True,
            "activity_logging": True
        },
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    API 健康檢查
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }