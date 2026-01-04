"""
Strategy management API v2 endpoints
策略管理API v2端點
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import logging

from ....database.strategy_models import Strategy, StrategyConfig, StrategyCategory
from ....models.strategy_models import (
    StrategyType, RiskTolerance, BacktestType,
    StrategyCreateRequest, StrategyUpdateRequest,
    StrategyConfigCreateRequest, StrategyConfigUpdateRequest,
    StrategyResponse, StrategyConfigResponse, BacktestSummaryResponse,
    PerformanceMetricsResponse, PaginatedResponse
)
from ....services.strategy_service import StrategyService
from ....dependencies import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["strategies"])

def get_strategy_service(db: Session = Depends(get_db)) -> StrategyService:
    """Get strategy service instance"""
    return StrategyService(db)

# Strategy endpoints
@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: StrategyCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Create a new strategy
    創建新策略
    """
    try:
        strategy = service.create_strategy(request)
        return StrategyResponse(strategy=strategy, categories=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Get strategy by ID
    根�ID獲取策略
    """
    try:
        strategy = service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        return StrategyResponse(strategy=strategy, categories=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_strategies(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    strategy_type: Optional[StrategyType] = Query(None, description="Filter by strategy type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    List strategies with pagination and filtering
    列出策略（分頁和過濾）
    """
    try:
        return service.list_strategies(
            user_id=user_id,
            strategy_type=strategy_type,
            is_active=is_active,
            page=page,
            size=size,
            search=search
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    request: StrategyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Update strategy
    更新策略
    """
    try:
        strategy = service.update_strategy(strategy_id, request)
        return StrategyResponse(strategy=strategy, categories=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Delete strategy (soft delete)
    刪除策略（軟刪除）
    """
    try:
        service.delete_strategy(strategy_id, current_user["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Strategy Config endpoints
@router.post("/{strategy_id}/configs", response_model=StrategyConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy_config(
    strategy_id: str = Path(..., description="Strategy ID"),
    request: StrategyConfigCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Create strategy configuration
    創建策略配置
    """
    try:
        # Ensure strategy_id is set in the request
        config_data = request.config_data.dict()
        config_data["strategy_id"] = strategy_id

        create_request = StrategyConfigCreateRequest(config_data=config_data)
        config = service.create_strategy_config(create_request, current_user["id"])

        return StrategyConfigResponse(config=config, strategy=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating strategy config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{strategy_id}/configs/{config_id}", response_model=StrategyConfigResponse)
async def get_strategy_config(
    strategy_id: str = Path(..., description="Strategy ID"),
    config_id: str = Path(..., description="Configuration ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Get strategy configuration by ID
    根據ID獲取策略配置
    """
    try:
        config = service.get_strategy_config(config_id, current_user["id"])
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found"
            )
        return StrategyConfigResponse(config=config, strategy=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting strategy config {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{strategy_id}/configs", response_model=PaginatedResponse)
async def list_strategy_configs(
    strategy_id: str = Path(..., description="Strategy ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    risk_tolerance: Optional[RiskTolerance] = Query(None, description="Filter by risk tolerance"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    List strategy configurations
    列出策略配置
    """
    try:
        return service.list_strategy_configs(
            user_id=current_user["id"],
            strategy_id=strategy_id,
            is_active=is_active,
            risk_tolerance=risk_tolerance,
            page=page,
            size=size
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing strategy configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{strategy_id}/configs/{config_id}", response_model=StrategyConfigResponse)
async def update_strategy_config(
    strategy_id: str = Path(..., description="Strategy ID"),
    config_id: str = Path(..., description="Configuration ID"),
    request: StrategyConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Update strategy configuration
    更新策略配置
    """
    try:
        config = service.update_strategy_config(config_id, request, current_user["id"])
        return StrategyConfigResponse(config=config, strategy=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating strategy config {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{strategy_id}/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy_config(
    strategy_id: str = Path(..., description="Strategy ID"),
    config_id: str = Path(..., description="Configuration ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Delete strategy configuration (soft delete)
    刪除策略配置（軟刪除）
    """
    try:
        service.delete_strategy_config(config_id, current_user["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting strategy config {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Analytics endpoints
@router.get("/{strategy_id}/summary", response_model=Dict[str, Any])
async def get_strategy_summary(
    strategy_id: str = Path(..., description="Strategy ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Get strategy summary with latest performance
    獲取策略摘要和最新表現
    """
    try:
        return service.get_strategy_summary(strategy_id, current_user["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting strategy summary {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{strategy_id}/performance", response_model=PerformanceMetricsResponse)
async def get_strategy_performance_metrics(
    strategy_id: str = Path(..., description="Strategy ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    Get strategy performance metrics
    獲取策略性能指標
    """
    try:
        metrics = service.get_strategy_performance_metrics(strategy_id, current_user["id"])
        return PerformanceMetricsResponse(**metrics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting strategy performance metrics {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Category endpoints
@router.get("/categories", response_model=List[StrategyCategory])
async def list_strategy_categories(
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service)
):
    """
    List strategy categories
    列出策略分類
    """
    try:
        categories = service.list_strategy_categories(is_active=is_active)
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "display_name": cat.display_name,
                "description": cat.description,
                "parent_id": cat.parent_id,
                "level": cat.level,
                "is_active": cat.is_active,
                "created_at": cat.created_at
            }
            for cat in categories
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing strategy categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/types", response_model=List[Dict[str, Any]])
async def list_strategy_types():
    """
    List available strategy types
    列出可用的策略類型
    """
    return [
        {
            "value": st.value,
            "label": st.value.replace("_", " ").title(),
            "description": {
                StrategyType.TECHNICAL_INDICATORS: "Technical analysis based strategies",
                StrategyType.MOMENTUM: "Momentum-based trading strategies",
                StrategyType.MEAN_REVERSION: "Mean reversion strategies",
                StrategyType.VOLUME: "Volume analysis strategies",
                StrategyType.VOLATILITY: "Volatility trading strategies",
                StrategyType.FUNDAMENTAL: "Fundamental analysis strategies",
                StrategyType.QUANTITATIVE: "Mathematical models strategies",
                StrategyType.PORTFOLIO: "Multi-asset portfolio strategies",
                StrategyType.ARBITRAGE: "Statistical arbitrage strategies",
                StrategyType.MACRO: "Macroeconomic factor strategies"
            }.get(st.value, "")
        }
        for st in StrategyType
    ]

@router.get("/risk-tolerances", response_model=List[Dict[str, Any]])
async def list_risk_tolerances():
    """
    List available risk tolerance levels
    列出可用的風險承受水平
    """
    return [
        {
            "value": rt.value,
            "label": rt.value.title(),
            "description": {
                RiskTolerance.LOW: "Conservative risk management with low drawdown limits",
                RiskTolerance.MEDIUM: "Moderate risk management for balanced returns",
                RiskTolerance.HIGH: "Aggressive risk management for higher returns",
                RiskTolerance.EXTREME: "Very aggressive risk management"
            }.get(rt.value, "")
        }
        for rt in RiskTolerance
    ]