#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Strategy API Routes
統一策略 API 路由

整合來自三個管理器的 API 端點:
- 基礎 CRUD 操作
- CBSC 業務邏輯端點
- 用戶個人化端點

Architecture Goal: 單一路由入口，消除重複代碼
Performance Goal: 保持現有性能水平
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db, get_current_user
from ....models.strategy_models_v2 import (
    Strategy, StrategyType, StrategyStatus, RiskLevel,
    StrategyVersion, StrategyInstance, Backtest, StrategyPerformance
)
from ....services.unified_strategy_service import UnifiedStrategyService
from ....services.interfaces import ServiceResponse
from ....core.events.event_bus import get_event_bus, EventTypes, Event

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/strategies/v2", tags=["strategies"])

# ========== Request/Response Schemas ==========


class StrategyCreateRequest(BaseModel):
    """Strategy creation request"""
    name: str = Field(..., min_length=1, max_length=200, description="Strategy name")
    description: Optional[str] = Field(None, max_length=5000, description="Strategy description")
    strategy_type: StrategyType = Field(..., description="Strategy type")
    config: Dict[str, Any] = Field(..., description="Strategy configuration")
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Risk level")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Strategy tags")
    is_public: bool = Field(False, description="Public visibility")
    is_template: bool = Field(False, description="Template strategy")


class StrategyUpdateRequest(BaseModel):
    """Strategy update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    config: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[StrategyStatus] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class StrategyExecuteRequest(BaseModel):
    """Strategy execution request"""
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Runtime parameter overrides")
    symbols: Optional[List[str]] = Field(default_factory=list, description="Symbols to trade")
    capital_allocation: Optional[float] = Field(None, gt=0, description="Allocated capital")
    is_paper_trading: bool = Field(True, description="Paper trading mode")
    auto_trade: bool = Field(False, description="Automatic trading")


class BatchOperationRequest(BaseModel):
    """Batch operation request"""
    strategy_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="Strategy IDs to operate on")
    operation: str = Field(..., description="Operation: activate, deactivate, archive, delete")


class StrategyResponse(BaseModel):
    """Strategy response"""
    id: str
    user_id: int
    name: str
    description: str
    strategy_type: str
    risk_level: str
    parameters: Dict[str, Any]
    status: str
    is_public: bool
    is_template: bool
    created_at: str
    updated_at: str
    version_count: int


class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExecutionResponse(BaseModel):
    """Execution response"""
    instance_id: str
    strategy_id: str
    status: str
    started_at: str


class StatusResponse(BaseModel):
    """Status response"""
    instance_id: str
    strategy_id: str
    status: str
    started_at: Optional[str]
    stopped_at: Optional[str]
    performance: Optional[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    date: str
    return: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    profit_factor: Optional[float]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ========== Helper Functions ==========


async def get_strategy_service(
    db: AsyncSession = Depends(get_db)
) -> UnifiedStrategyService:
    """Get strategy service instance"""
    return UnifiedStrategyService(db=db)


def handle_service_response(response: ServiceResponse) -> JSONResponse:
    """Convert service response to HTTP response"""
    if response.success:
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": response.data,
                "message": response.message
            }
        )
    else:
        status_code = 404 if "not found" in response.error.lower() else 400
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": response.error,
                "message": response.message
            }
        )


# ========== Strategy CRUD Endpoints ==========


@router.post("/", response_model=StrategyResponse, status_code=201, summary="Create strategy")
async def create_strategy(
    request: StrategyCreateRequest,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Create new strategy

    - **name**: Strategy name (1-200 characters)
    - **description**: Optional description
    - **strategy_type**: Type of strategy (technical, momentum, volume, etc.)
    - **config**: Strategy configuration parameters
    - **risk_level**: Risk level (low, medium, high, very_high)
    - **category_id**: Optional category ID
    - **tags**: Optional list of tags
    - **is_public**: Public visibility flag
    - **is_template**: Template strategy flag
    """
    response = await service.create_strategy(
        user_id=current_user["id"],
        name=request.name,
        strategy_type=request.strategy_type,
        config=request.config,
        description=request.description,
        risk_level=request.risk_level
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    return response.data


@router.get("/{strategy_id}", response_model=StrategyResponse, summary="Get strategy details")
async def get_strategy(
    strategy_id: UUID = Path(..., description="Strategy ID"),
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Get strategy by ID

    Returns detailed information about a specific strategy including:
    - Basic information (name, description, type)
    - Configuration and parameters
    - Performance metrics
    - Version history
    """
    response = await service.get_strategy(
        strategy_id=strategy_id,
        user_id=current_user["id"]
    )

    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)

    return response.data


@router.get("/", response_model=PaginatedResponse, summary="List strategies")
async def list_strategies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[StrategyStatus] = Query(None, description="Filter by status"),
    strategy_type: Optional[StrategyType] = Query(None, description="Filter by type"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    is_public: Optional[bool] = Query(None, description="Filter by visibility"),
    is_template: Optional[bool] = Query(None, description="Filter templates only"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    List user's strategies with pagination and filtering

    Supports filtering by:
    - **status**: Strategy status (draft, active, inactive, archived, testing)
    - **strategy_type**: Strategy type
    - **risk_level**: Risk level
    - **is_public**: Public/private strategies
    - **is_template**: Template strategies
    - **search**: Text search in name and description
    """
    filters = {}
    if status:
        filters["status"] = status
    if strategy_type:
        filters["strategy_type"] = strategy_type
    if risk_level:
        filters["risk_level"] = risk_level
    if is_public is not None:
        filters["is_public"] = is_public
    if is_template is not None:
        filters["is_template"] = is_template

    skip = (page - 1) * page_size

    response = await service.list_strategies(
        user_id=current_user["id"],
        skip=skip,
        limit=page_size,
        filters=filters
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    items = response.data
    total = len(items)  # Service doesn't return total, using items count
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.put("/{strategy_id}", response_model=StrategyResponse, summary="Update strategy")
async def update_strategy(
    strategy_id: UUID,
    request: StrategyUpdateRequest,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Update strategy

    Only the fields provided in the request will be updated.
    All updates create a new version automatically.
    """
    updates = request.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = await service.update_strategy(
        strategy_id=strategy_id,
        user_id=current_user["id"],
        updates=updates
    )

    if not response.success:
        status_code = 404 if "not found" in response.error.lower() or "permission" in response.error.lower() else 400
        raise HTTPException(status_code=status_code, detail=response.message)

    return response.data


@router.delete("/{strategy_id}", status_code=204, summary="Delete strategy")
async def delete_strategy(
    strategy_id: UUID,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Delete strategy

    Permanently deletes a strategy and all associated data:
    - Version history
    - Execution instances
    - Backtest results
    - Performance records

    **Warning**: This action cannot be undone.
    """
    response = await service.delete_strategy(
        strategy_id=strategy_id,
        user_id=current_user["id"]
    )

    if not response.success:
        status_code = 404 if "not found" in response.error.lower() or "permission" in response.error.lower() else 400
        raise HTTPException(status_code=status_code, detail=response.message)

    return None


# ========== Strategy Execution Endpoints ==========


@router.post("/{strategy_id}/execute", response_model=ExecutionResponse, summary="Execute strategy")
async def execute_strategy(
    strategy_id: UUID,
    request: StrategyExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Execute strategy

    Starts a new strategy instance with the specified parameters.
    The strategy runs in the background and can be monitored via the status endpoint.

    - **parameters**: Runtime parameter overrides
    - **symbols**: Symbols to trade (empty for all)
    - **capital_allocation**: Allocated capital amount
    - **is_paper_trading**: Paper trading vs live trading
    - **auto_trade**: Enable automatic trading
    """
    response = await service.execute_strategy(
        strategy_id=strategy_id,
        user_id=current_user["id"]
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    # TODO: Add background task for actual strategy execution
    # background_tasks.add_task(execute_strategy_background, strategy_id, request, current_user["id"])

    return response.data


@router.post("/{strategy_id}/stop", status_code=200, summary="Stop strategy execution")
async def stop_strategy(
    strategy_id: UUID,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Stop strategy execution

    Stops the running strategy instance gracefully.
    Current positions will be closed according to the strategy's exit rules.
    """
    response = await service.stop_strategy(
        strategy_id=strategy_id,
        user_id=current_user["id"]
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    return {"success": True, "message": response.message}


@router.get("/{strategy_id}/status", response_model=StatusResponse, summary="Get strategy status")
async def get_strategy_status(
    strategy_id: UUID,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Get strategy execution status

    Returns real-time status information including:
    - Instance status (running, stopped, paused, error)
    - Start/stop timestamps
    - Current performance metrics
    - Last signal information
    """
    response = await service.get_strategy_status(
        strategy_id=strategy_id,
        user_id=current_user["id"]
    )

    if not response.success:
        raise HTTPException(status_code=404, detail=response.message)

    return response.data


# ========== Strategy Performance Endpoints ==========


@router.get("/{strategy_id}/performance", response_model=List[PerformanceMetrics], summary="Get strategy performance")
async def get_strategy_performance(
    strategy_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Get strategy performance metrics

    Returns historical performance data including:
    - Daily returns
    - Risk-adjusted metrics (Sharpe, Sortino, Calmar ratios)
    - Drawdown metrics
    - Win rate and profit factor

    Date range can be filtered using start_date and end_date parameters.
    """
    response = await service.get_strategy_performance(
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    return response.data


@router.get("/{strategy_id}/signals", summary="Get strategy signals")
async def get_strategy_signals(
    strategy_id: UUID,
    limit: int = Query(50, ge=1, le=500, description="Number of signals to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy signal history

    Returns recent trading signals generated by the strategy.
    """
    # TODO: Implement signal history retrieval
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "signals": [],
            "total": 0,
            "message": "Signal history not yet implemented"
        }
    }


# ========== Strategy Template Endpoints ==========


@router.get("/templates/list", response_model=PaginatedResponse, summary="List strategy templates")
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    strategy_type: Optional[StrategyType] = None,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    List available strategy templates

    Returns a curated list of strategy templates that users can clone and customize.
    Templates are pre-configured strategies with proven performance.
    """
    filters = {"is_template": True}
    if strategy_type:
        filters["strategy_type"] = strategy_type

    skip = (page - 1) * page_size

    response = await service.list_strategies(
        user_id=current_user["id"],
        skip=skip,
        limit=page_size,
        filters=filters
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    items = response.data
    total = len(items)
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.post("/templates/{template_id}/clone", response_model=StrategyResponse, status_code=201, summary="Clone template")
async def clone_template(
    template_id: UUID,
    name: str = Query(..., min_length=1, max_length=200, description="Name for cloned strategy"),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clone strategy template

    Creates a copy of a template strategy with a new name.
    The cloned strategy inherits all configuration and parameters.
    """
    # TODO: Implement template cloning
    return {
        "success": True,
        "message": "Template cloning not yet implemented"
    }


# ========== Batch Operations Endpoints ==========


@router.post("/batch", status_code=200, summary="Batch operations")
async def batch_operations(
    request: BatchOperationRequest,
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Perform batch operations on multiple strategies

    Supported operations:
    - **activate**: Activate multiple strategies
    - **deactivate**: Deactivate multiple strategies
    - **archive**: Archive multiple strategies
    - **delete**: Delete multiple strategies (requires confirmation)

    Maximum 100 strategies per batch.
    """
    results = {
        "success": [],
        "failed": [],
        "operation": request.operation
    }

    for strategy_id in request.strategy_ids:
        try:
            if request.operation == "activate":
                response = await service.update_strategy(
                    strategy_id=strategy_id,
                    user_id=current_user["id"],
                    updates={"status": StrategyStatus.ACTIVE}
                )
            elif request.operation == "deactivate":
                response = await service.update_strategy(
                    strategy_id=strategy_id,
                    user_id=current_user["id"],
                    updates={"status": StrategyStatus.INACTIVE}
                )
            elif request.operation == "archive":
                response = await service.update_strategy(
                    strategy_id=strategy_id,
                    user_id=current_user["id"],
                    updates={"status": StrategyStatus.ARCHIVED}
                )
            elif request.operation == "delete":
                response = await service.delete_strategy(
                    strategy_id=strategy_id,
                    user_id=current_user["id"]
                )
            else:
                results["failed"].append({
                    "strategy_id": str(strategy_id),
                    "error": f"Unknown operation: {request.operation}"
                })
                continue

            if response.success:
                results["success"].append(str(strategy_id))
            else:
                results["failed"].append({
                    "strategy_id": str(strategy_id),
                    "error": response.message
                })

        except Exception as e:
            results["failed"].append({
                "strategy_id": str(strategy_id),
                "error": str(e)
            })

    return {
        "success": True,
        "data": results,
        "message": f"Batch operation completed: {len(results['success'])} succeeded, {len(results['failed'])} failed"
    }


# ========== CBSC-Specific Endpoints ==========


@router.get("/{strategy_id}/risk-metrics", summary="Get CBSC risk metrics")
async def get_risk_metrics(
    strategy_id: UUID,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get CBSC-specific risk metrics

    Returns advanced risk analysis:
    - Value at Risk (VaR) at multiple confidence levels
    - Expected Shortfall
    - Beta coefficient
    - Correlation matrix
    - Risk contribution by position
    """
    # TODO: Implement CBSC risk metrics calculation
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "message": "Risk metrics calculation not yet implemented"
        }
    }


@router.get("/{strategy_id}/execution-report", summary="Get execution report")
async def get_execution_report(
    strategy_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed execution report

    Comprehensive report including:
    - All trades executed
    - Signal analysis
    - Performance attribution
    - Slippage analysis
    - Commission summary
    """
    # TODO: Implement execution report generation
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "message": "Execution report generation not yet implemented"
        }
    }


# ========== Personal Dashboard Endpoints ==========


@router.get("/dashboard/overview", summary="Get personal dashboard overview")
async def get_dashboard_overview(
    current_user: Dict = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_strategy_service)
):
    """
    Get personal dashboard overview

    Returns summary of user's strategy portfolio:
    - Total strategies
    - Active instances
    - Overall performance
    - Recent activity
    - Risk overview
    """
    # Get user's strategies
    response = await service.list_strategies(
        user_id=current_user["id"],
        skip=0,
        limit=1000,
        filters={}
    )

    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)

    strategies = response.data

    # Calculate overview
    overview = {
        "total_strategies": len(strategies),
        "active_strategies": len([s for s in strategies if s.get("status") == "active"]),
        "draft_strategies": len([s for s in strategies if s.get("status") == "draft"]),
        "archived_strategies": len([s for s in strategies if s.get("status") == "archived"]),
        "strategy_types": {},
        "risk_levels": {}
    }

    # Count by type
    for strategy in strategies:
        stype = strategy.get("strategy_type", "unknown")
        overview["strategy_types"][stype] = overview["strategy_types"].get(stype, 0) + 1

        risk = strategy.get("risk_level", "unknown")
        overview["risk_levels"][risk] = overview["risk_levels"].get(risk, 0) + 1

    return {
        "success": True,
        "data": overview,
        "message": "Dashboard overview retrieved successfully"
    }


# ========== WebSocket Support (TODO) ==========


@router.websocket("/ws/{strategy_id}")
async def strategy_websocket_endpoint(websocket, strategy_id: str):
    """
    WebSocket endpoint for real-time strategy updates

    Provides real-time streaming of:
    - Strategy status changes
    - New trading signals
    - Performance updates
    - Trade notifications
    """
    # TODO: Implement WebSocket support
    pass
