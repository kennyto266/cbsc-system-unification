"""
Unified Strategy CRUD API v2 Endpoints
統一策略CRUD API v2端點實現

Enhanced CRUD operations using UnifiedStrategyService
整合三個策略管理器的統一CRUD端點
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_async_db
from ....services.unified_strategy_service import UnifiedStrategyService
from ....services.interfaces import ServiceResponse
from ....dependencies import get_current_user
from ....models.user import User

logger = logging.getLogger(__name__)

# Create router for unified CRUD operations
unified_crud_router = APIRouter(prefix="/strategies", tags=["strategies-unified-crud"])


async def get_unified_strategy_service(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> UnifiedStrategyService:
    """Get unified strategy service instance with user context"""
    return UnifiedStrategyService(db=db, user_id=current_user.id)


@unified_crud_router.get(
    "",
    response_model=Dict[str, Any],
    summary="List strategies (Unified)",
    description="Retrieve a paginated list of strategies using unified service"
)
async def list_strategies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by strategy status"),
    strategy_type: Optional[str] = Query(None, description="Filter by strategy type"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term for strategy name/description"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Get list of strategies with pagination and filtering

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        status: Filter by strategy status
        strategy_type: Filter by strategy type
        category_id: Filter by category
        search: Search term
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Paginated list of strategies
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if strategy_type:
            filters["strategy_type"] = strategy_type
        if category_id:
            filters["category_id"] = str(category_id)
        if search:
            filters["search"] = search

        # Get strategies using unified service
        result: ServiceResponse[List[Dict]] = await service.list_strategies(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            filters=filters
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to list strategies"
            )

        # Calculate total pages
        total = result.metadata.get("total", len(result.data))
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "success": True,
            "strategies": result.data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "total_pages": total_pages,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list strategies: {str(e)}"
        )


@unified_crud_router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create strategy (Unified)",
    description="Create a new trading strategy using unified service"
)
async def create_strategy(
    strategy_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Create a new strategy using unified service

    Args:
        strategy_data: Strategy creation data
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Created strategy details
    """
    try:
        # Extract required fields
        name = strategy_data.get("name")
        strategy_type = strategy_data.get("strategy_type", StrategyType.MOMENTUM.value)
        config = strategy_data.get("parameters", {})
        description = strategy_data.get("description", "")

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strategy name is required"
            )

        # Create strategy using unified service
        result: ServiceResponse[Dict] = await service.create_strategy(
            user_id=current_user.id,
            name=name,
            strategy_type=strategy_type,
            config=config,
            description=description
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to create strategy"
            )

        return {
            "success": True,
            "strategy": result.data,
            "message": result.message or "Strategy created successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {str(e)}"
        )


@unified_crud_router.get(
    "/{strategy_id}",
    response_model=Dict[str, Any],
    summary="Get strategy details (Unified)",
    description="Retrieve detailed information about a specific strategy"
)
async def get_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Get strategy by ID using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Strategy details
    """
    try:
        result: ServiceResponse[Dict] = await service.get_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error or "Strategy not found"
            )

        return {
            "success": True,
            "strategy": result.data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy: {str(e)}"
        )


@unified_crud_router.put(
    "/{strategy_id}",
    response_model=Dict[str, Any],
    summary="Update strategy (Unified)",
    description="Update strategy configuration and metadata"
)
async def update_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    strategy_data: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Update strategy using unified service

    Args:
        strategy_id: Strategy ID
        strategy_data: Strategy update data
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Updated strategy details
    """
    try:
        if strategy_data is None:
            strategy_data = {}

        # Update strategy using unified service
        result: ServiceResponse[Dict] = await service.update_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id,
            **strategy_data
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to update strategy"
            )

        return {
            "success": True,
            "strategy": result.data,
            "message": result.message or "Strategy updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy: {str(e)}"
        )


@unified_crud_router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete strategy (Unified)",
    description="Soft delete a strategy (marks as archived)"
)
async def delete_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Delete strategy using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service
    """
    try:
        result: ServiceResponse[None] = await service.delete_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to delete strategy"
            )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete strategy: {str(e)}"
        )
