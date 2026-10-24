"""
Strategy API v2 Routes
策略管理 API v2 路由定義

RESTful 設計原則：
- 使用標準 HTTP 方法
- 資源導向的 URL
- 合理的 HTTP 狀態碼
- 統一的錯誤響應格式
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..services.strategy_service import BaseStrategyService
from ..services.execution_service import ExecutionService
from ..services.performance_service import PerformanceService
from ..container import get_strategy_service, get_execution_service, get_performance_service
from ..utils.permissions import get_current_user
from ..models import User
from ..schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListResponse, ExecutionRequest, ExecutionResponse,
    PerformanceMetrics
)
from ..config.features import is_feature_enabled

logger = logging.getLogger(__name__)

# Create v2 router
router = APIRouter(prefix="/api/v2", tags=["strategies-v2"])


# ============================================================================
# Version and Metadata Endpoints
# ============================================================================

@router.get("/version")
async def get_api_version():
    """
    獲取 API 版本信息

    Returns:
        API version and metadata
    """
    return {
        "version": "2.0.0",
        "name": "Strategy Management API",
        "description": "RESTful API for strategy management",
        "features": {
            "real_time_execution": is_feature_enabled("ENABLE_REAL_TIME_EXECUTION"),
            "enhanced_cache": is_feature_enabled("USE_ENHANCED_CACHE"),
            "v2_responses": is_feature_enabled("USE_V2_RESPONSE_FORMAT")
        },
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    API 健康檢查
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


# ============================================================================
# Strategy Resource Endpoints
# ============================================================================

@router.get("/strategies", response_model=Dict[str, Any])
async def list_strategies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    filter_type: Optional[str] = Query(None, description="Filter by strategy type"),
    filter_status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service),
    api_version: str = Header("2.0", alias="API-Version")
):
    """
    獲取策略列表

    支持分頁、排序、過濾和搜索：
    - 分頁：page, page_size
    - 排序：sort_by, sort_order
    - 過濾：filter_type, filter_status
    - 搜索：search
    """
    try:
        # Build filters
        filters = {}
        if filter_type:
            filters["strategy_type"] = filter_type
        if filter_status:
            filters["status"] = filter_status

        # Build sort options
        sort_options = {}
        if sort_by:
            sort_options["field"] = sort_by
            sort_options["order"] = sort_order

        # Get strategies
        result = await strategy_service.list_strategies(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            filters=filters,
            sort_options=sort_options,
            search=search
        )

        # Format response based on version
        if is_feature_enabled("USE_V2_RESPONSE_FORMAT"):
            return {
                "data": result["items"],
                "pagination": {
                    "page": result["page"],
                    "pageSize": result["page_size"],
                    "total": result["total"],
                    "pages": result["pages"],
                    "hasNext": result["page"] < result["pages"],
                    "hasPrev": result["page"] > 1
                },
                "filters": filters,
                "sort": sort_options,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Legacy format for compatibility
            return {
                "success": True,
                "data": result["items"],
                "pagination": result,
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"獲取策略列表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve strategies"
        )


@router.post("/strategies", response_model=Dict[str, Any], status_code=201)
async def create_strategy(
    strategy_data: StrategyCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    創建新策略

    支持異步處理：
    - 立即返回策略 ID
    - 後台處理策略驗證和初始化
    """
    try:
        # Create strategy
        strategy = await strategy_service.create_strategy(strategy_data, current_user.id)

        # Add background task for strategy initialization
        background_tasks.add_task(
            _initialize_strategy,
            strategy.id,
            current_user.id
        )

        response = {
            "id": strategy.id,
            "name": strategy.name,
            "status": strategy.status,
            "message": "策略創建成功，正在初始化...",
            "created_at": strategy.created_at.isoformat()
        }

        # Add location header for resource location
        return JSONResponse(
            content=response,
            status_code=201,
            headers={"Location": f"/api/v2/strategies/{strategy.id}"}
        )

    except Exception as e:
        logger.error(f"創建策略失敗: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create strategy: {str(e)}"
        )


@router.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy(
    strategy_id: str,
    include: Optional[str] = Query(None, description="Include additional data (performance,executions)"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service),
    performance_service: PerformanceService = Depends(get_performance_service)
):
    """
    獲取策略詳情

    支持包含額外數據：
    - performance: 包含性能指標
    - executions: 包含執行歷史
    """
    try:
        # Get basic strategy info
        strategy = await strategy_service.get_strategy(strategy_id, current_user.id)

        response = strategy.dict()

        # Include additional data if requested
        if include:
            includes = include.split(",")

            if "performance" in includes:
                # Get performance metrics
                metrics = await performance_service.calculate_strategy_performance(
                    strategy_id, current_user.id
                )
                response["performance"] = metrics.dict()

            if "executions" in includes:
                # Get execution history
                executions = await strategy_service.get_strategy_executions(
                    strategy_id, current_user.id
                )
                response["executions"] = executions

        return response

    except Exception as e:
        logger.error(f"獲取策略詳情失敗: {e}")
        raise HTTPException(
            status_code=404,
            detail="Strategy not found"
        )


@router.put("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def update_strategy(
    strategy_id: str,
    update_data: StrategyUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    更新策略

    支持部分更新和後台處理
    """
    try:
        # Update strategy
        strategy = await strategy_service.update_strategy(
            strategy_id, update_data, current_user.id
        )

        # Add background task for strategy revalidation if parameters changed
        if update_data.parameters:
            background_tasks.add_task(
                _revalidate_strategy,
                strategy_id,
                current_user.id
            )

        return {
            "id": strategy.id,
            "name": strategy.name,
            "updated_at": strategy.updated_at.isoformat(),
            "message": "策略更新成功"
        }

    except Exception as e:
        logger.error(f"更新策略失敗: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update strategy: {str(e)}"
        )


@router.delete("/strategies/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: str,
    force: Optional[bool] = Query(False, description="Force delete even if active"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    刪除策略

    安全刪除：
    - 檢查是否有活躍的執行
    - 支持強制刪除
    """
    try:
        # Check if strategy has active executions
        if not force:
            active_executions = await strategy_service.get_active_executions(
                strategy_id, current_user.id
            )
            if active_executions:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete strategy with active executions. Use ?force=true to override."
                )

        # Delete strategy
        await strategy_service.delete_strategy(strategy_id, current_user.id)

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除策略失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete strategy"
        )


# ============================================================================
# Strategy Execution Endpoints
# ============================================================================

@router.post("/strategies/{strategy_id}/executions", response_model=Dict[str, Any], status_code=202)
async def execute_strategy(
    strategy_id: str,
    execution_request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    執行策略

    異步執行：
    - 立即返回執行 ID
    - 後台執行策略
    """
    try:
        # Create execution
        execution = await execution_service.create_execution(
            strategy_id, current_user.id, execution_request
        )

        # Add background task for strategy execution
        background_tasks.add_task(
            _execute_strategy_async,
            execution.id,
            current_user.id
        )

        return {
            "execution_id": execution.id,
            "strategy_id": strategy_id,
            "status": "queued",
            "message": "策略執行已排隊",
            "queued_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"執行策略失敗: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to execute strategy: {str(e)}"
        )


@router.get("/strategies/{strategy_id}/executions/{execution_id}")
async def get_execution_status(
    strategy_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    獲取執行狀態
    """
    try:
        execution = await execution_service.get_execution(
            execution_id, current_user.id
        )

        return {
            "execution_id": execution.id,
            "strategy_id": strategy_id,
            "status": execution.status,
            "progress": execution.progress,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "results": execution.results,
            "error_message": execution.error_message
        }

    except Exception as e:
        logger.error(f"獲取執行狀態失敗: {e}")
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )


@router.post("/strategies/{strategy_id}/executions/{execution_id}/stop")
async def stop_execution(
    strategy_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    停止策略執行
    """
    try:
        await execution_service.stop_execution(execution_id, current_user.id)

        return {
            "execution_id": execution_id,
            "strategy_id": strategy_id,
            "status": "stopped",
            "stopped_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"停止執行失敗: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to stop execution"
        )


# ============================================================================
# Strategy Performance Endpoints
# ============================================================================

@router.get("/strategies/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: str,
    time_range: Optional[str] = Query(None, description="Time range (1d, 1w, 1m, 1y)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
):
    """
    獲取策略性能指標
    """
    try:
        # Parse date range
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Get performance metrics
        metrics = await performance_service.calculate_strategy_performance(
            strategy_id, current_user.id, start_dt, end_dt
        )

        return metrics.dict()

    except Exception as e:
        logger.error(f"獲取策略性能失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get performance metrics"
        )


@router.get("/strategies/{strategy_id}/performance/comparison")
async def compare_strategies(
    strategy_id: str,
    compare_with: List[str] = Query(..., description="Strategy IDs to compare with"),
    time_range: Optional[str] = Query(None, description="Time range"),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
):
    """
    策略性能對比
    """
    try:
        # Parse date range
        start_date, end_date = _parse_time_range(time_range)

        # Get comparison
        comparison = await performance_service.get_performance_comparison(
            [strategy_id] + compare_with,
            current_user.id,
            start_date,
            end_date
        )

        return comparison

    except Exception as e:
        logger.error(f"策略對比失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare strategies"
        )


@router.get("/strategies/{strategy_id}/performance/report")
async def get_performance_report(
    strategy_id: str,
    report_type: str = Query("summary", regex="^(summary|detailed|monthly)$"),
    time_range: Optional[str] = Query(None, description="Time range"),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
):
    """
    生成性能報告
    """
    try:
        # Parse date range
        start_date, end_date = _parse_time_range(time_range)

        # Generate report
        report = await performance_service.generate_performance_report(
            strategy_id,
            current_user.id,
            report_type,
            start_date,
            end_date
        )

        return report

    except Exception as e:
        logger.error(f"生成報告失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )


# ============================================================================
# Batch Operations Endpoints
# ============================================================================

@router.post("/strategies/batch", response_model=Dict[str, Any])
async def batch_operation(
    operation: str = Query(..., regex="^(delete|activate|deactivate)$"),
    strategy_ids: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    批量操作策略

    支持的批量操作：
    - delete: 批量刪除
    - activate: 批量激活
    - deactivate: 批量停用
    """
    try:
        results = []

        for strategy_id in strategy_ids:
            try:
                if operation == "delete":
                    await strategy_service.delete_strategy(strategy_id, current_user.id)
                    results.append({"id": strategy_id, "status": "deleted"})
                elif operation == "activate":
                    await strategy_service.activate_strategy(strategy_id, current_user.id)
                    results.append({"id": strategy_id, "status": "activated"})
                elif operation == "deactivate":
                    await strategy_service.deactivate_strategy(strategy_id, current_user.id)
                    results.append({"id": strategy_id, "status": "deactivated"})
            except Exception as e:
                results.append({"id": strategy_id, "status": "error", "error": str(e)})

        return {
            "operation": operation,
            "total": len(strategy_ids),
            "successful": len([r for r in results if r.get("status") != "error"]),
            "failed": len([r for r in results if r.get("status") == "error"]),
            "results": results
        }

    except Exception as e:
        logger.error(f"批量操作失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail="Batch operation failed"
        )


# ============================================================================
# Background Tasks
# ============================================================================

async def _initialize_strategy(strategy_id: str, user_id: int):
    """後台任務：初始化策略"""
    try:
        strategy_service = await get_strategy_service()
        await strategy_service.initialize_strategy(strategy_id, user_id)
        logger.info(f"策略 {strategy_id} 初始化完成")
    except Exception as e:
        logger.error(f"策略初始化失敗 {strategy_id}: {e}")


async def _revalidate_strategy(strategy_id: str, user_id: int):
    """後台任務：重新驗證策略"""
    try:
        strategy_service = await get_strategy_service()
        await strategy_service.revalidate_strategy(strategy_id, user_id)
        logger.info(f"策略 {strategy_id} 重新驗證完成")
    except Exception as e:
        logger.error(f"策略重新驗證失敗 {strategy_id}: {e}")


async def _execute_strategy_async(execution_id: str, user_id: int):
    """後台任務：異步執行策略"""
    try:
        execution_service = await get_execution_service()
        await execution_service.run_execution(execution_id, user_id)
        logger.info(f"策略執行完成 {execution_id}")
    except Exception as e:
        logger.error(f"策略執行失敗 {execution_id}: {e}")


def _parse_time_range(time_range: Optional[str]) -> tuple:
    """解析時間範圍"""
    if not time_range:
        return None, None

    from datetime import datetime, timedelta

    end_time = datetime.utcnow()

    if time_range == "1d":
        start_time = end_time - timedelta(days=1)
    elif time_range == "1w":
        start_time = end_time - timedelta(weeks=1)
    elif time_range == "1m":
        start_time = end_time - timedelta(days=30)
    elif time_range == "1y":
        start_time = end_time - timedelta(days=365)
    else:
        return None, None

    return start_time, end_time