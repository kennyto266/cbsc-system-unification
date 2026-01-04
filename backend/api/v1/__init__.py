"""
API v1 routers - Legacy endpoints for backward compatibility.
"""

from fastapi import APIRouter

# Import individual module routers
from . import auth, strategies

# Create main v1 router
router = APIRouter()

# Include module routers
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication v1 (Legacy)"]
)

router.include_router(
    strategies.router,
    prefix="/strategies",
    tags=["Strategies v1 (Legacy)"]
)

__all__ = ["router"]
