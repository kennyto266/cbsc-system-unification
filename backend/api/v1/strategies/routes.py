"""
Strategy API v1 routes - Legacy endpoints for backward compatibility.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth import get_current_active_user
from services.strategy_service import StrategyService
from schemas.strategy import StrategyResponse, StrategyListResponse
from models.user import User

router = APIRouter()


@router.get("", response_model=List[StrategyListResponse])
async def list_strategies_v1(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[StrategyListResponse]:
    """
    Legacy v1 endpoint to list strategies.

    Returns simplified list without pagination.
    """
    service = StrategyService(db)
    strategies = await service.list(user_id=current_user.id, limit=100)
    return [StrategyListResponse.model_validate(s) for s in strategies]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_v1(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StrategyResponse:
    """Legacy v1 endpoint to get strategy by ID."""
    service = StrategyService(db)
    strategy = await service.get_by_id(strategy_id, current_user.id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    return StrategyResponse.model_validate(strategy)
