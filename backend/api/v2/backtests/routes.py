"""
Backtest API v2 routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth import get_current_active_user
from services.backtest_service import BacktestService
from schemas.backtest import (
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse,
    BacktestStartRequest
)
from schemas.common import PaginatedResponse
from models.user import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse[BacktestListResponse])
async def list_backtests_v2(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    strategy_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[BacktestListResponse]:
    """List current user's backtests with pagination."""
    service = BacktestService(db)

    skip = (page - 1) * page_size
    backtests = await service.list(
        user_id=current_user.id,
        strategy_id=strategy_id,
        status=status_filter,
        skip=skip,
        limit=page_size
    )

    # Get total count (simplified)
    total = len(backtests)

    items = [BacktestListResponse.model_validate(b) for b in backtests]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_v2(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BacktestResponse:
    """Get backtest by ID."""
    service = BacktestService(db)
    backtest = await service.get_by_id(backtest_id, current_user.id)

    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )

    return BacktestResponse.model_validate(backtest)


@router.post("", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest_v2(
    data: BacktestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BacktestResponse:
    """Create a new backtest."""
    service = BacktestService(db)
    backtest = await service.create(current_user.id, data)

    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy not found or access denied"
        )

    return BacktestResponse.model_validate(backtest)


@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest_v2(
    backtest_id: int,
    data: BacktestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BacktestResponse:
    """Update backtest (only pending backtests can be updated)."""
    service = BacktestService(db)
    try:
        backtest = await service.update(backtest_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )

    return BacktestResponse.model_validate(backtest)


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest_v2(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete backtest."""
    service = BacktestService(db)
    success = await service.delete(backtest_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )


@router.post("/{backtest_id}/start", response_model=BacktestResponse)
async def start_backtest_v2(
    backtest_id: int,
    data: Optional[BacktestStartRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BacktestResponse:
    """Start backtest execution."""
    service = BacktestService(db)
    try:
        config = data.config if data else None
        backtest = await service.start(backtest_id, current_user.id, config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )

    return BacktestResponse.model_validate(backtest)


@router.post("/{backtest_id}/cancel", response_model=BacktestResponse)
async def cancel_backtest_v2(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BacktestResponse:
    """Cancel running backtest."""
    service = BacktestService(db)
    try:
        backtest = await service.cancel(backtest_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )

    return BacktestResponse.model_validate(backtest)
