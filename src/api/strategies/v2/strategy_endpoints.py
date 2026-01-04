"""
Strategy API Endpoints v2.0
RESTful API endpoints for strategy management
Phase 3.2 - 開發策略管理服務
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.strategy_service_v2 import StrategyService
from ...models.strategy_models_v2 import (
    Strategy, StrategyType, StrategyStatus, RiskLevel
)
from ...api.schemas.strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse,
    StrategyVersionResponse, StrategyInstanceCreate, StrategyInstanceUpdate,
    StrategyInstanceResponse, BacktestCreate, BacktestResponse,
    StrategyFilter, PaginationParams, PaginationResponse,
    BacktestFilter, InstanceStatus
)
from ...core.auth import get_current_user
from ...models.user import User

router = APIRouter(prefix="/strategies", tags=["strategies"])


def get_strategy_service(db: Session = Depends(get_db)) -> StrategyService:
    """Get strategy service instance"""
    return StrategyService(db)


# Strategy CRUD endpoints
@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create new strategy"""
    try:
        strategy = strategy_service.create_strategy(strategy_data, current_user.id)
        return StrategyResponse.from_orm(strategy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    search: Optional[str] = Query(None, description="Search term"),
    strategy_type: Optional[StrategyType] = Query(None, description="Strategy type"),
    status: Optional[StrategyStatus] = Query(None, description="Strategy status"),
    category_id: Optional[UUID] = Query(None, description="Category ID"),
    risk_level: Optional[RiskLevel] = Query(None, description="Risk level"),
    is_public: Optional[bool] = Query(None, description="Public strategies only"),
    is_template: Optional[bool] = Query(None, description="Template strategies only"),
    featured: Optional[bool] = Query(None, description="Featured strategies only"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    author_id: Optional[UUID] = Query(None, description="Filter by author"),
    min_sharpe: Optional[float] = Query(None, ge=-10, le=10, description="Minimum Sharpe ratio"),
    max_drawdown_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum drawdown"),
    created_after: Optional[datetime] = Query(None, description="Created after this date"),
    created_before: Optional[datetime] = Query(None, description="Created before this date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[User] = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """List strategies with filtering and pagination"""
    try:
        # Build filters
        filters = StrategyFilter(
            search=search,
            strategy_type=strategy_type,
            status=status,
            category_id=category_id,
            risk_level=risk_level,
            is_public=is_public,
            is_template=is_template,
            featured=featured,
            tags=tags,
            author_id=author_id,
            min_sharpe=min_sharpe,
            max_drawdown_max=max_drawdown_max,
            created_after=created_after,
            created_before=created_before
        )

        pagination = PaginationParams(page=page, size=size)
        user_id = current_user.id if current_user else None

        strategies, total = strategy_service.get_strategies(
            filter_params=filters,
            pagination=pagination,
            user_id=user_id
        )

        pagination_response = PaginationResponse.create(total, page, size)

        return StrategyListResponse(
            strategies=[StrategyResponse.from_orm(s) for s in strategies],
            total=total,
            page=page,
            size=size,
            total_pages=pagination_response.total_pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get strategy by ID"""
    try:
        user_id = current_user.id if current_user else None
        strategy = strategy_service.get_strategy(strategy_id, user_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        return StrategyResponse.from_orm(strategy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    update_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Update strategy"""
    try:
        strategy = strategy_service.update_strategy(
            strategy_id, update_data, current_user.id
        )
        return StrategyResponse.from_orm(strategy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Delete strategy"""
    try:
        strategy_service.delete_strategy(strategy_id, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{strategy_id}/publish", response_model=StrategyResponse)
async def publish_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Publish strategy to public gallery"""
    try:
        strategy = strategy_service.publish_strategy(strategy_id, current_user.id)
        return StrategyResponse.from_orm(strategy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Strategy Version endpoints
@router.get("/{strategy_id}/versions", response_model=List[StrategyVersionResponse])
async def get_strategy_versions(
    strategy_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get strategy version history"""
    try:
        user_id = current_user.id if current_user else None
        versions = strategy_service.get_strategy_versions(strategy_id, user_id)
        return [StrategyVersionResponse.from_orm(v) for v in versions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{strategy_id}/versions", response_model=StrategyVersionResponse)
async def create_strategy_version(
    strategy_id: UUID,
    version_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create new strategy version"""
    try:
        version = strategy_service.create_strategy_version(
            strategy_id, version_data, current_user.id
        )
        return StrategyVersionResponse.from_orm(version)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Strategy Instance endpoints
@router.post("/{strategy_id}/instances", response_model=StrategyInstanceResponse)
async def create_strategy_instance(
    strategy_id: UUID,
    instance_data: StrategyInstanceCreate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create strategy instance"""
    try:
        # Set strategy_id from path
        instance_data.strategy_id = strategy_id
        instance = strategy_service.create_strategy_instance(instance_data, current_user.id)
        return StrategyInstanceResponse.from_orm(instance)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/instances/", response_model=List[StrategyInstanceResponse])
async def get_strategy_instances(
    strategy_id: Optional[UUID] = Query(None, description="Filter by strategy ID"),
    status: Optional[InstanceStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get user's strategy instances"""
    try:
        instances = strategy_service.get_strategy_instances(
            current_user.id, strategy_id, status
        )
        return [StrategyInstanceResponse.from_orm(i) for i in instances]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/instances/{instance_id}", response_model=StrategyInstanceResponse)
async def update_strategy_instance(
    instance_id: UUID,
    update_data: StrategyInstanceUpdate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Update strategy instance"""
    try:
        instance = strategy_service.update_strategy_instance(
            instance_id, update_data.dict(exclude_unset=True), current_user.id
        )
        return StrategyInstanceResponse.from_orm(instance)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/instances/{instance_id}/start", status_code=status.HTTP_200_OK)
async def start_strategy_instance(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Start strategy instance"""
    try:
        strategy_service.update_strategy_instance(
            instance_id,
            {"status": "running", "started_at": datetime.utcnow()},
            current_user.id
        )
        return {"message": "Instance started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/instances/{instance_id}/stop", status_code=status.HTTP_200_OK)
async def stop_strategy_instance(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Stop strategy instance"""
    try:
        strategy_service.update_strategy_instance(
            instance_id,
            {"status": "stopped", "stopped_at": datetime.utcnow()},
            current_user.id
        )
        return {"message": "Instance stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Backtest endpoints
@router.post("/{strategy_id}/backtests", response_model=BacktestResponse)
async def create_backtest(
    strategy_id: UUID,
    backtest_data: BacktestCreate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create backtest"""
    try:
        # Set strategy_id from path
        backtest_data.strategy_id = strategy_id
        backtest = strategy_service.create_backtest(backtest_data, current_user.id)
        return BacktestResponse.from_orm(backtest)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/backtests/", response_model=List[BacktestResponse])
async def get_backtests(
    strategy_id: Optional[UUID] = Query(None, description="Filter by strategy ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    symbols: Optional[List[str]] = Query(None, description="Filter by symbols"),
    start_date_after: Optional[date] = Query(None, description="Filter by start date"),
    start_date_before: Optional[date] = Query(None, description="Filter by start date"),
    min_return: Optional[float] = Query(None, description="Minimum return"),
    max_drawdown: Optional[float] = Query(None, description="Maximum drawdown"),
    min_sharpe: Optional[float] = Query(None, description="Minimum Sharpe ratio"),
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get backtests"""
    try:
        filters = BacktestFilter(
            status=status,
            symbols=symbols,
            start_date_after=start_date_after,
            start_date_before=start_date_before,
            min_return=min_return,
            max_drawdown_max=max_drawdown,
            min_sharpe=min_sharpe
        )

        backtests = strategy_service.get_backtests(
            user_id=current_user.id,
            strategy_id=strategy_id,
            filter_params=filters
        )
        return [BacktestResponse.from_orm(b) for b in backtests]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Analytics endpoints
@router.get("/analytics/statistics")
async def get_strategy_statistics(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get strategy statistics"""
    try:
        stats = strategy_service.get_strategy_statistics(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates")
async def get_strategy_templates(
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get available strategy templates"""
    try:
        templates = strategy_service.get_strategy_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/templates/{template_name}", response_model=StrategyResponse)
async def create_strategy_from_template(
    template_name: str,
    customizations: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create strategy from template"""
    try:
        strategy = strategy_service.create_strategy_from_template(
            template_name, customizations, current_user.id
        )
        return StrategyResponse.from_orm(strategy)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Performance endpoints
@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: UUID,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    current_user: Optional[User] = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get strategy performance data"""
    try:
        user_id = current_user.id if current_user else None
        performance = strategy_service.get_strategy_performance(
            strategy_id, start_date, end_date
        )

        if not performance and user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Performance data not found"
            )

        return [p.__dict__ for p in performance]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{strategy_id}/performance")
async def record_strategy_performance(
    strategy_id: UUID,
    performance_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Record strategy performance"""
    try:
        # Verify user owns the strategy
        strategy = strategy_service.get_strategy(strategy_id, current_user.id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        performance = strategy_service.record_strategy_performance(
            strategy_id, performance_data
        )
        return {"message": "Performance recorded successfully", "id": performance.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )