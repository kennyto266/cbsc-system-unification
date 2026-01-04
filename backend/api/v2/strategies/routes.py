"""
Strategy API v2 routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth import get_current_active_user
from services.strategy_service import StrategyService
from schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    StrategyToggleRequest,
    BatchOperationRequest
)
from schemas.common import PaginatedResponse, PaginationParams
from models.user import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse[StrategyListResponse])
async def list_strategies_v2(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[StrategyListResponse]:
    """List current user's strategies with pagination."""
    service = StrategyService(db)

    skip = (page - 1) * page_size
    strategies = await service.list(
        user_id=current_user.id,
        status=status,
        category=category,
        skip=skip,
        limit=page_size
    )

    # Get total count (simplified - should use count query in production)
    total = len(strategies)

    items = [StrategyListResponse.model_validate(s) for s in strategies]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_v2(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StrategyResponse:
    """Get strategy by ID."""
    service = StrategyService(db)
    strategy = await service.get_by_id(strategy_id, current_user.id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    return StrategyResponse.model_validate(strategy)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy_v2(
    data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StrategyResponse:
    """Create a new strategy."""
    service = StrategyService(db)
    strategy = await service.create(current_user.id, data)
    return StrategyResponse.model_validate(strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy_v2(
    strategy_id: int,
    data: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StrategyResponse:
    """Update strategy."""
    service = StrategyService(db)
    strategy = await service.update(strategy_id, current_user.id, data)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    return StrategyResponse.model_validate(strategy)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy_v2(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete strategy."""
    service = StrategyService(db)
    success = await service.delete(strategy_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )


@router.patch("/{strategy_id}/toggle", response_model=StrategyResponse)
async def toggle_strategy_v2(
    strategy_id: int,
    data: StrategyToggleRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StrategyResponse:
    """Toggle strategy active status."""
    service = StrategyService(db)
    strategy = await service.toggle_status(
        strategy_id,
        current_user.id,
        data.is_active
    )

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    return StrategyResponse.model_validate(strategy)


@router.post("/batch", response_model=dict)
async def batch_control_strategies_v2(
    data: BatchOperationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Perform batch operation on strategies."""
    service = StrategyService(db)
    results = await service.batch_operation(
        data.strategy_ids,
        current_user.id,
        data.operation
    )

    success_count = sum(1 for v in results.values() if v)
    failed_count = len(results) - success_count

    return {
        "success": True,
        "results": [
            {"strategy_id": sid, "success": success}
            for sid, success in results.items()
        ],
        "summary": {
            "total": len(results),
            "success": success_count,
            "failed": failed_count
        }
    }
