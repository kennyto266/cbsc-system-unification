"""
Unified Strategy Operations API v2 Endpoints
統一策略操作API v2端點實現

Operations for strategy execution management using UnifiedStrategyService
整合三個策略管理器的統一操作端點
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

# Create router for unified operations
unified_operation_router = APIRouter(prefix="/strategies", tags=["strategies-unified-operations"])


async def get_unified_strategy_service(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> UnifiedStrategyService:
    """Get unified strategy service instance with user context"""
    return UnifiedStrategyService(db=db, user_id=current_user.id)


@unified_operation_router.post(
    "/{strategy_id}/execute",
    response_model=Dict[str, Any],
    summary="Execute strategy (Unified)",
    description="Execute a strategy using unified service"
)
async def execute_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    execution_config: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Execute strategy using unified service

    Args:
        strategy_id: Strategy ID
        execution_config: Optional execution configuration
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Execution status and details
    """
    try:
        if execution_config is None:
            execution_config = {}

        # Execute strategy using unified service
        result: ServiceResponse[Dict] = await service.execute_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id,
            **execution_config
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to execute strategy"
            )

        return {
            "success": True,
            "execution": result.data,
            "message": result.message or "Strategy execution started",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute strategy: {str(e)}"
        )


@unified_operation_router.post(
    "/{strategy_id}/stop",
    response_model=Dict[str, Any],
    summary="Stop strategy execution (Unified)",
    description="Stop a running strategy using unified service"
)
async def stop_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Stop strategy execution using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Stop confirmation
    """
    try:
        # Stop strategy using unified service
        result: ServiceResponse[None] = await service.stop_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to stop strategy"
            )

        return {
            "success": True,
            "message": result.message or "Strategy stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop strategy: {str(e)}"
        )


@unified_operation_router.get(
    "/{strategy_id}/status",
    response_model=Dict[str, Any],
    summary="Get strategy status (Unified)",
    description="Get current execution status of a strategy"
)
async def get_strategy_status(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Get strategy execution status using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Strategy execution status
    """
    try:
        # Get status using unified service
        result: ServiceResponse[Dict] = await service.get_strategy_status(
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
            "status": result.data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy status {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy status: {str(e)}"
        )


@unified_operation_router.post(
    "/{strategy_id}/activate",
    response_model=Dict[str, Any],
    summary="Activate strategy (Unified)",
    description="Activate a strategy for trading"
)
async def activate_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Activate strategy using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Updated strategy details
    """
    try:
        # Update strategy status to active
        result: ServiceResponse[Dict] = await service.update_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id,
            status="active"
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to activate strategy"
            )

        return {
            "success": True,
            "strategy": result.data,
            "message": "Strategy activated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate strategy: {str(e)}"
        )


@unified_operation_router.post(
    "/{strategy_id}/pause",
    response_model=Dict[str, Any],
    summary="Pause strategy (Unified)",
    description="Pause a strategy (temporarily stop trading)"
)
async def pause_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Pause strategy using unified service

    Args:
        strategy_id: Strategy ID
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Updated strategy details
    """
    try:
        # Pause strategy first if running
        stop_result: ServiceResponse[None] = await service.stop_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        # Update strategy status to paused
        result: ServiceResponse[Dict] = await service.update_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id,
            status="paused"
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to pause strategy"
            )

        return {
            "success": True,
            "strategy": result.data,
            "message": "Strategy paused successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause strategy: {str(e)}"
        )


@unified_operation_router.post(
    "/{strategy_id}/duplicate",
    response_model=Dict[str, Any],
    summary="Duplicate strategy (Unified)",
    description="Create a copy of an existing strategy"
)
async def duplicate_strategy(
    strategy_id: str = Path(..., description="Strategy ID"),
    new_name: Optional[str] = Query(None, description="New strategy name"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Duplicate strategy using unified service

    Args:
        strategy_id: Strategy ID to duplicate
        new_name: Optional new name for duplicated strategy
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Created strategy details
    """
    try:
        # Get original strategy
        original_result: ServiceResponse[Dict] = await service.get_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        if not original_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original strategy not found"
            )

        original_strategy = original_result.data

        # Generate new name if not provided
        if not new_name:
            new_name = f"{original_strategy.get('name', 'strategy')}_copy"

        # Create duplicate strategy
        result: ServiceResponse[Dict] = await service.create_strategy(
            user_id=current_user.id,
            name=new_name,
            strategy_type=original_strategy.get("strategy_type", "momentum"),
            config=original_strategy.get("config", {}),
            description=original_strategy.get("description", "")
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to duplicate strategy"
            )

        return {
            "success": True,
            "strategy": result.data,
            "message": "Strategy duplicated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate strategy: {str(e)}"
        )


@unified_operation_router.get(
    "/{strategy_id}/performance",
    summary="Get strategy performance (Unified)",
    description="Get performance metrics for a strategy"
)
async def get_strategy_performance(
    strategy_id: str = Path(..., description="Strategy ID"),
    period: Optional[str] = Query("1M", description="Performance period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Get strategy performance metrics using unified service

    Args:
        strategy_id: Strategy ID
        period: Performance period
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Performance metrics
    """
    try:
        # Check if strategy exists
        strategy_result: ServiceResponse[Dict] = await service.get_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
        )

        if not strategy_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )

        # Get performance metrics from strategy data
        # The unified service stores performance in the strategy data
        performance = strategy_result.data.get("performance", {
            "period": period,
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0
        })

        return {
            "success": True,
            "strategy_id": strategy_id,
            "performance": performance,
            "period": period,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy performance {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy performance: {str(e)}"
        )


@unified_operation_router.post(
    "/batch",
    summary="Batch operations (Unified)",
    description="Perform batch operations on multiple strategies"
)
async def batch_operation(
    operation: str = Query(..., regex="^(delete|activate|pause|stop)$", description="Operation to perform"),
    strategy_ids: List[str] = Query(..., description="List of strategy IDs"),
    current_user: User = Depends(get_current_user),
    service: UnifiedStrategyService = Depends(get_unified_strategy_service)
):
    """
    Perform batch operations on strategies

    Args:
        operation: Operation type (delete, activate, pause, stop)
        strategy_ids: List of strategy IDs
        current_user: Current authenticated user
        service: Unified strategy service

    Returns:
        Batch operation results
    """
    try:
        results = []
        successful = 0
        failed = 0

        for strategy_id in strategy_ids:
            try:
                if operation == "delete":
                    result = await service.delete_strategy(strategy_id, current_user.id)
                    if result.success:
                        results.append({"id": strategy_id, "status": "deleted"})
                        successful += 1
                    else:
                        results.append({"id": strategy_id, "status": "error", "error": result.error})
                        failed += 1

                elif operation == "activate":
                    result = await service.update_strategy(strategy_id, current_user.id, status="active")
                    if result.success:
                        results.append({"id": strategy_id, "status": "activated"})
                        successful += 1
                    else:
                        results.append({"id": strategy_id, "status": "error", "error": result.error})
                        failed += 1

                elif operation == "pause":
                    stop_result = await service.stop_strategy(strategy_id, current_user.id)
                    result = await service.update_strategy(strategy_id, current_user.id, status="paused")
                    if result.success:
                        results.append({"id": strategy_id, "status": "paused"})
                        successful += 1
                    else:
                        results.append({"id": strategy_id, "status": "error", "error": result.error})
                        failed += 1

                elif operation == "stop":
                    result = await service.stop_strategy(strategy_id, current_user.id)
                    if result.success:
                        results.append({"id": strategy_id, "status": "stopped"})
                        successful += 1
                    else:
                        results.append({"id": strategy_id, "status": "error", "error": result.error})
                        failed += 1

            except Exception as e:
                results.append({"id": strategy_id, "status": "error", "error": str(e)})
                failed += 1

        return {
            "success": True,
            "operation": operation,
            "total": len(strategy_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch operation failed: {str(e)}"
        )
