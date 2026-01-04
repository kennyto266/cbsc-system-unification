"""
Strategy Operations API v2 Endpoints
策略操作API v2端點實現

Operations for strategy management: activate, pause, duplicate, versions
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.dependencies import get_db
from src.services.strategy_service_v2 import StrategyServiceV2
from src.schemas.strategy_schemas import (
    StrategyResponse,
    StrategyStatus
)
from src.models.strategy_models_v2 import StrategyStatus as StrategyStatusModel

logger = logging.getLogger(__name__)

# Create router for operations
operation_router = APIRouter(prefix="/strategies", tags=["strategies-operations"])


def get_strategy_service(db: AsyncSession) -> StrategyServiceV2:
    """Get strategy service instance with database session"""
    return StrategyServiceV2(db)


@operation_router.post(
    "/{strategy_id}/activate",
    response_model=StrategyResponse,
    summary="Activate strategy",
    description="Activate a strategy for trading"
)
async def activate_strategy(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate strategy

    Args:
        strategy_id: Strategy UUID
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

        # Check if strategy can be activated
        if existing_strategy.status == StrategyStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strategy is already active"
            )

        # Activate strategy
        strategy = await strategy_service.change_strategy_status(
            db=db,
            strategy_id=strategy_id,
            status=StrategyStatus.ACTIVE
        )

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate strategy"
            )

        return StrategyResponse.from_model(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate strategy: {str(e)}"
        )


@operation_router.post(
    "/{strategy_id}/pause",
    response_model=StrategyResponse,
    summary="Pause strategy",
    description="Pause a strategy (temporarily stop trading)"
)
async def pause_strategy(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Pause strategy

    Args:
        strategy_id: Strategy UUID
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

        # Check if strategy can be paused
        if existing_strategy.status == StrategyStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strategy is already paused"
            )

        # Pause strategy
        strategy = await strategy_service.change_strategy_status(
            db=db,
            strategy_id=strategy_id,
            status=StrategyStatus.PAUSED
        )

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause strategy"
            )

        return StrategyResponse.from_model(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause strategy: {str(e)}"
        )


@operation_router.post(
    "/{strategy_id}/duplicate",
    response_model=StrategyResponse,
    summary="Duplicate strategy",
    description="Create a copy of an existing strategy"
)
async def duplicate_strategy(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    new_name: Optional[str] = Query(None, description="New strategy name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Duplicate strategy

    Args:
        strategy_id: Strategy UUID to duplicate
        new_name: Optional new name for duplicated strategy
        db: Database session

    Returns:
        Created strategy details
    """
    try:
        # Get original strategy
        original_strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not original_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Generate new name if not provided
        if not new_name:
            new_name = f"{original_strategy.name}_copy"

        # Check if name already exists
        existing_with_name = await strategy_service.get_strategy_by_name(db, new_name)
        if existing_with_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy with name '{new_name}' already exists"
            )

        # Duplicate strategy
        duplicated_strategy = await strategy_service.duplicate_strategy(
            db=db,
            strategy_id=strategy_id,
            new_name=new_name
        )

        return StrategyResponse.from_model(duplicated_strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate strategy: {str(e)}"
        )


@operation_router.get(
    "/{strategy_id}/versions",
    response_model=List[Dict[str, Any]],
    summary="Get strategy versions",
    description="Get version history of a strategy"
)
async def get_strategy_versions(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy version history

    Args:
        strategy_id: Strategy UUID
        skip: Number of records to skip
        limit: Number of records to return
        db: Database session

    Returns:
        List of strategy versions
    """
    try:
        # Check if strategy exists
        strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Get version history
        versions = await strategy_service.get_strategy_versions(
            db,
            strategy_id,
            skip=skip,
            limit=limit
        )

        return versions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy versions {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy versions: {str(e)}"
        )


@operation_router.post(
    "/{strategy_id}/restore/{version_id}",
    response_model=StrategyResponse,
    summary="Restore strategy version",
    description="Restore a strategy to a previous version"
)
async def restore_strategy_version(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    version_id: UUID = Path(..., description="Version UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Restore strategy to a previous version

    Args:
        strategy_id: Strategy UUID
        version_id: Version UUID to restore
        db: Database session

    Returns:
        Updated strategy details
    """
    try:
        # Check if strategy exists
        strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Restore version
        restored_strategy = await strategy_service.restore_strategy_version(
            db=db,
            strategy_id=strategy_id,
            version_id=version_id
        )

        if not restored_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found or restore failed"
            )

        return StrategyResponse.from_model(restored_strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore strategy version {strategy_id}/{version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore strategy version: {str(e)}"
        )


@operation_router.get(
    "/{strategy_id}/backtest",
    summary="Get strategy backtests",
    description="Get backtest history for a strategy"
)
async def get_strategy_backtests(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by backtest status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy backtest history

    Args:
        strategy_id: Strategy UUID
        skip: Number of records to skip
        limit: Number of records to return
        status: Filter by backtest status
        db: Database session

    Returns:
        List of backtest results
    """
    try:
        # Check if strategy exists
        strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Build filters
        filters = {}
        if status:
            filters["status"] = status

        # Get backtest history
        backtests = await strategy_service.get_strategy_backtests(
            db=db,
            strategy_id=strategy_id,
            skip=skip,
            limit=limit,
            filters=filters
        )

        return backtests

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy backtests {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy backtests: {str(e)}"
        )


@operation_router.get(
    "/{strategy_id}/performance",
    summary="Get strategy performance",
    description="Get performance metrics for a strategy"
)
async def get_strategy_performance(
    strategy_id: UUID = Path(..., description="Strategy UUID"),
    period: Optional[str] = Query("1M", description="Performance period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy performance metrics

    Args:
        strategy_id: Strategy UUID
        period: Performance period
        db: Database session

    Returns:
        Performance metrics
    """
    try:
        # Check if strategy exists
        strategy = await strategy_service.get_strategy_by_id(db, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Get performance metrics
        performance = await strategy_service.get_strategy_performance(
            db=db,
            strategy_id=strategy_id,
            period=period
        )

        return performance

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy performance {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy performance: {str(e)}"
        )