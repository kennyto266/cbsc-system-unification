"""
Strategy CRUD API v2 Endpoints
策略CRUD API v2端點實現

Enhanced CRUD operations for strategy management
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.dependencies import get_db
from src.services.strategy_service_v2 import StrategyServiceV2
from src.schemas.strategy_schemas import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse
)
from src.models.strategy_models_v2 import StrategyStatus, StrategyType

logger = logging.getLogger(__name__)

# Create router for CRUD operations
crud_router = APIRouter(prefix="/strategies", tags=["strategies-crud"])


def get_strategy_service(db: AsyncSession) -> StrategyServiceV2:
    """Get strategy service instance with database session"""
    return StrategyServiceV2(db)


@crud_router.get(
    "",
    response_model=StrategyListResponse,
    summary="List strategies",
    description="Retrieve a paginated list of strategies with filtering and sorting options"
)
async def list_strategies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[StrategyStatus] = Query(None, description="Filter by strategy status"),
    strategy_type: Optional[StrategyType] = Query(None, description="Filter by strategy type"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term for strategy name/description"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db)
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
        db: Database session

    Returns:
        Paginated list of strategies
    """
    try:
        # Get service instance
        strategy_service = get_strategy_service(db)

        # Build filters
        filters = {}
        if status:
            filters["status"] = status.value
        if strategy_type:
            filters["strategy_type"] = strategy_type.value
        if category_id:
            filters["category_id"] = str(category_id)
        if search:
            filters["search"] = search

        # Get strategies
        strategies = await strategy_service.list_strategies(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get total count
        total = await strategy_service.count_strategies(db, filters)

        return StrategyListResponse(
            strategies=[
                StrategyResponse.from_orm(strategy) if hasattr(StrategyResponse, 'from_orm') else strategy for strategy in strategies
            ],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list strategies: {str(e)}"
        )


@crud_router.post(
    "",
    response_model=StrategyResponse,
    status_code=201,
    summary="Create strategy",
    description="Create a new trading strategy with configuration and parameters"
)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new strategy

    Args:
        strategy_data: Strategy creation data
        db: Database session

    Returns:
        Created strategy details
    """
    try:
        # Validate strategy configuration
        validation_result = await strategy_service.validate_strategy_config(
            strategy_data.strategy_type,
            strategy_data.parameters
        )

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid strategy configuration: {validation_result['errors']}"
            )

        # Create strategy
        strategy = await strategy_service.create_strategy(
            db=db,
            strategy_data=strategy_data
        )

        return StrategyResponse.from_model(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create strategy: {str(e)}"
        )


@crud_router.get(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Get strategy details",
    description="Retrieve detailed information about a specific strategy"
)
async def get_strategy(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy by ID

    Args:
        strategy_id: Strategy UUID
        db: Database session

    Returns:
        Strategy details
    """
    try:
        strategy = await strategy_service.get_strategy_by_id(db, strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        return StrategyResponse.from_model(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get strategy: {str(e)}"
        )


@crud_router.put(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Update strategy",
    description="Update strategy configuration and metadata"
)
async def update_strategy(
    strategy_data: StrategyUpdate,
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update strategy

    Args:
        strategy_id: Strategy UUID
        strategy_data: Strategy update data
        db: Database session

    Returns:
        Updated strategy details
    """
    try:
        # Check if strategy exists
        existing_strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not existing_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Validate new configuration if provided
        if strategy_data.parameters:
            strategy_type = strategy_data.strategy_type or existing_strategy.strategy_type
            validation_result = await strategy_service.validate_strategy_config(
                strategy_type,
                strategy_data.parameters
            )

            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid strategy configuration: {validation_result['errors']}"
                )

        # Update strategy
        strategy = await strategy_service.update_strategy(
            db=db,
            strategy_id=strategy_id,
            strategy_data=strategy_data
        )

        return StrategyResponse.from_model(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update strategy: {str(e)}"
        )


@crud_router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete strategy",
    description="Soft delete a strategy (marks as archived)"
)
async def delete_strategy(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete strategy (soft delete)

    Args:
        strategy_id: Strategy UUID
        db: Database session
    """
    try:
        # Check if strategy exists
        existing_strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not existing_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Soft delete strategy
        success = await strategy_service.delete_strategy(db, strategy_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete strategy"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete strategy: {str(e)}"
        )