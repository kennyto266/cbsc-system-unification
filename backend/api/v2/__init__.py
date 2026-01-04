"""
API v2 routers - New architecture with improved structure.
"""

from fastapi import APIRouter

# Import individual module routers
from . import auth, strategies, backtests

# Create main v2 router
router = APIRouter()

# Include module routers
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication v2"]
)

router.include_router(
    strategies.router,
    prefix="/strategies",
    tags=["Strategies v2"]
)

router.include_router(
    backtests.router,
    prefix="/backtests",
    tags=["Backtests v2"]
)

__all__ = ["router"]
