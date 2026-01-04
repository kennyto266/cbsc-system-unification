"""
Risk Management API v2 - Dependencies
======================================

Dependency injection for FastAPI routes.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

from functools import lru_cache
from typing import Generator, Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from .config import Settings
from ..risk_monitor.risk_engine import RiskEngine
from ..risk_monitor.config import RiskConfig

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# Settings instance
settings = Settings()

# Database engine
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=settings.debug
)


def get_database() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    from .database import Base

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_risk_engine() -> RiskEngine:
    """
    Dependency to get risk engine instance (cached)
    """
    config = RiskConfig(
        calculation_interval=settings.risk_calculation_interval,
        var_confidence_levels=settings.var_confidence_levels,
        es_confidence_levels=settings.es_confidence_levels,
        volatility_windows=settings.volatility_windows,
        max_drawdown_window=settings.max_drawdown_window,
        alert_enabled=settings.alert_enabled,
        dynamic_adjustment_enabled=settings.dynamic_adjustment_enabled,
        websocket_host=settings.websocket_host,
        websocket_port=settings.websocket_port,
        influxdb_host=settings.influxdb_host,
        influxdb_port=settings.influxdb_port,
        influxdb_database=settings.influxdb_database,
        influxdb_username=settings.influxdb_username,
        influxdb_password=settings.influxdb_password
    )

    return RiskEngine(config)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user
    """
    try:
        # In a real implementation, this would validate the JWT token
        # and extract user information from it
        token = credentials.credentials

        # Mock user validation - replace with actual JWT validation
        if token.startswith("mock_"):
            user_id = token.split("_")[1]
            user = {
                "id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "permissions": ["risk:read", "risk:write"],
                "is_active": True
            }
            return user

        # Actual JWT validation would go here
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_user_permissions(
    current_user: dict = Depends(get_current_user)
) -> list:
    """
    Dependency to get user permissions
    """
    return current_user.get("permissions", [])


def require_permission(permission: str):
    """
    Factory function to create a dependency that requires a specific permission
    """
    async def permission_dependency(
        user_permissions: list = Depends(get_user_permissions)
    ):
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return True

    return permission_dependency


def require_permissions(permissions: list):
    """
    Factory function to create a dependency that requires multiple permissions
    """
    async def permissions_dependency(
        user_permissions: list = Depends(get_user_permissions)
    ):
        missing = [p for p in permissions if p not in user_permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions required: {', '.join(missing)}"
            )
        return True

    return permissions_dependency


async def validate_portfolio_access(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> bool:
    """
    Validate that user has access to the specified portfolio
    """
    # In a real implementation, this would check user's portfolio access rights
    # For now, allow access to all portfolios for authenticated users
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    return True


async def validate_strategy_access(
    strategy_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> bool:
    """
    Validate that user has access to the specified strategy
    """
    # In a real implementation, this would check user's strategy access rights
    # For now, allow access to all strategies for authenticated users
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    return True


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
) -> dict:
    """
    Get and validate pagination parameters
    """
    # Validate page
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )

    # Validate size
    if size < 1 or size > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 1000"
        )

    # Validate sort order
    if sort_order and sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sort order must be 'asc' or 'desc'"
        )

    return {
        "page": page,
        "size": size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }


def validate_date_range(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> tuple:
    """
    Validate date range parameters
    """
    if start_date and end_date:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        # Limit date range to 1 year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 1 year"
            )

    return start_date, end_date


def get_rate_limiter():
    """
    Get rate limiter instance
    """
    from ..middleware.rate_limiter import RateLimiter
    return RateLimiter(
        redis_url=settings.redis_url,
        default_limits=settings.rate_limits
    )


def get_cache():
    """
    Get cache instance
    """
    from ..middleware.cache import CacheManager
    return CacheManager(
        redis_url=settings.redis_url,
        default_ttl=settings.cache_ttl
    )