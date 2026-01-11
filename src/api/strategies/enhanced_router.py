"""
增强策略管理API路由
Enhanced Strategy Management API Router

基于新架构的增强版策略管理API路由
- 支持批量操作
- 实时更新
- 高级搜索
- 完整的错误处理
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.websockets import WebSocketState

from .services.enhanced_strategy_service import (
    EnhancedStrategyService, BatchOperationType, BatchOperationConfig, BatchOperationResult
)
from .services.execution_service import ExecutionService
from .services.websocket_service import WebSocketService
from .repositories.strategy_repository import StrategyRepository
from .repositories.user_repository import UserRepository
from .repositories.execution_repository import ExecutionRepository
from .utils.cache import CacheManager
from .utils.enhanced_validators import (
    ValidatorFactory, ValidationContext, BatchOperationValidator
)
from .utils.response import ResponseBuilder, handle_api_errors
from .utils.errors import ErrorCode, BusinessError
from .schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    ExecutionRequest, ExecutionResponse, ExecutionStatusResponse,
    DashboardResponse, UserPreferences, StrategyControlRequest,
    OperationHistoryResponse, StrategyRecommendations,
    RealTimeUpdate, PaginatedResponse
)

# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["策略管理 v1"])

# 全局WebSocket服务实例
websocket_service = WebSocketService()

# 依赖注入 - 获取增强服务实例
async def get_enhanced_strategy_service() -> EnhancedStrategyService:
    """获取增强策略服务实例"""
    strategy_repo = StrategyRepository()
    user_repo = UserRepository()
    cache_manager = CacheManager()
    validator = ValidatorFactory.get_strategy_validator()
    return EnhancedStrategyService(strategy_repo, user_repo, cache_manager, validator, websocket_service)

async def get_execution_service() -> ExecutionService:
    """获取执行服务实例"""
    strategy_repo = StrategyRepository()
    execution_repo = ExecutionRepository()
    cache_manager = CacheManager()
    validator = ValidatorFactory.get_validator("execution")
    return ExecutionService(strategy_repo, execution_repo, cache_manager, validator)

async def get_websocket_service() -> WebSocketService:
    """获取WebSocket服务实例"""
    return websocket_service


# ============================================================================
# 增强的策略CRUD操作
# ============================================================================

@router.get("/strategies", response_model=Dict[str, Any])
@handle_api_errors
async def list_strategies_enhanced(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    获取策略列表（增强版）
    """
    result = await service.search_strategies_advanced(
        query="",
        user_id=user_id,
        filters={
            "strategy_type": strategy_type,
            "status": status,
            "is_active": is_active
        },
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    return ResponseBuilder.build_success(
        data=result,
        message="获取策略列表成功"
    ).dict()


@router.post("/strategies", response_model=Dict[str, Any])
@handle_api_errors
async def create_strategy_enhanced(
    request: StrategyCreate,
    user_id: int,
    validate_permissions: bool = Query(True, description="是否验证权限"),
    notify_realtime: bool = Query(True, description="是否发送实时通知"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service),
    validator: ValidatorFactory = Depends()
):
    """
    创建新策略（增强版）
    """
    # 创建验证上下文
    context = ValidationContext(user_id=user_id, operation="create")

    # 验证请求
    strategy_validator = validator.get_strategy_validator()
    validation_context = await strategy_validator.validate_create_request(request, context)

    if validation_context.has_errors():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "创建策略验证失败",
                    "details": validation_context.get_errors()
                },
                "timestamp": datetime.now().isoformat()
            }
        )

    # 创建策略
    strategy = await service.create_strategy_with_validation(
        request,
        user_id,
        validate_permissions=validate_permissions,
        notify_realtime=notify_realtime
    )

    return ResponseBuilder.build_success(
        data=strategy.dict(),
        message="策略创建成功",
        metadata={"warnings": validation_context.get_warnings()}
    ).dict()


@router.get("/strategies/search", response_model=Dict[str, Any])
@handle_api_errors
async def search_strategies(
    q: str = Query(..., description="搜索关键词"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    filters: Optional[str] = Query(None, description="过滤条件(JSON格式)"),
    sort_by: str = Query("relevance", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    高级策略搜索
    """
    # 解析过滤条件
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "过滤条件格式错误"
                    }
                }
            )

    result = await service.search_strategies_advanced(
        query=q,
        user_id=user_id,
        filters=filter_dict,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    return ResponseBuilder.build_success(
        data=result,
        message="搜索完成"
    ).dict()


# ============================================================================
# 批量操作
# ============================================================================

@router.post("/strategies/batch", response_model=Dict[str, Any])
@handle_api_errors
async def batch_operation_enhanced(
    strategy_ids: List[str],
    operation: str = Query(..., description="操作类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    parameters: Optional[str] = Query(None, description="操作参数(JSON格式)"),
    batch_size: int = Query(50, ge=1, le=100, description="批次大小"),
    continue_on_error: bool = Query(True, description="出错时是否继续"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service),
    validator: BatchOperationValidator = Depends()
):
    """
    批量操作策略（增强版）
    """
    # 创建验证上下文
    context = ValidationContext(user_id=user_id, operation="batch")

    # 验证批量操作请求
    await validator.validate_batch_operation(strategy_ids, operation, user_id, context)

    if context.has_errors():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "批量操作验证失败",
                    "details": context.get_errors()
                }
            }
        )

    # 解析操作参数
    param_dict = {}
    if parameters:
        try:
            param_dict = json.loads(parameters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "操作参数格式错误"
                    }
                }
            )

    # 创建批量操作配置
    config = BatchOperationConfig(
        batch_size=batch_size,
        continue_on_error=continue_on_error,
        progress_callback=None  # 可以在这里添加进度回调
    )

    # 执行批量操作
    result = await service.batch_operation_enhanced(
        strategy_ids=strategy_ids,
        operation=operation,
        user_id=user_id,
        parameters=param_dict,
        config=config
    )

    return ResponseBuilder.build_success(
        data={
            "operation": result.operation.value,
            "total": result.total,
            "successful": len(result.successful),
            "failed": len(result.failed),
            "success_ids": result.successful,
            "failed_items": result.failed,
            "duration": result.duration,
            "progress": result.progress
        },
        message=f"批量{operation}操作完成"
    ).dict()


@router.get("/strategies/batch/{batch_id}/status", response_model=Dict[str, Any])
async def get_batch_operation_status(
    batch_id: str,
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    获取批量操作状态
    """
    result = service.get_batch_operation_result(batch_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "批量操作不存在"
                }
            }
        )

    return ResponseBuilder.build_success(
        data={
            "operation": result.operation.value,
            "total": result.total,
            "successful": len(result.successful),
            "failed": len(result.failed),
            "duration": result.duration,
            "progress": result.progress,
            "is_completed": result.end_time is not None
        },
        message="获取批量操作状态成功"
    ).dict()


# ============================================================================
# 策略分析
# ============================================================================

@router.get("/strategies/{strategy_id}/analytics", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_analytics(
    strategy_id: str,
    user_id: Optional[int] = Query(None, description="用户ID"),
    time_range: int = Query(30, ge=1, le=365, description="时间范围（天）"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    获取策略分析数据
    """
    analytics = await service.get_strategy_analytics(
        strategy_id=strategy_id,
        user_id=user_id,
        time_range=time_range
    )

    return ResponseBuilder.build_success(
        data=analytics,
        message="获取策略分析成功"
    ).dict()


# ============================================================================
# 实时更新
# ============================================================================

@router.get("/strategies/realtime", response_model=StreamingResponse)
async def get_real_time_updates(
    user_id: int,
    strategy_ids: Optional[str] = Query(None, description="策略ID列表(逗号分隔)"),
    last_update: Optional[str] = Query(None, description="上次更新时间"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    获取实时策略更新（Server-Sent Events）
    """
    # 解析策略ID列表
    ids_list = None
    if strategy_ids:
        ids_list = strategy_ids.split(",")

    # 解析上次更新时间
    last_update_dt = None
    if last_update:
        try:
            last_update_dt = datetime.fromisoformat(last_update)
        except ValueError:
            pass

    async def event_generator():
        try:
            async for update in service.get_real_time_strategy_updates(
                user_id=user_id,
                strategy_ids=ids_list,
                last_update=last_update_dt
            ):
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.websocket("/strategies/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[int] = None,
    strategy_ids: Optional[str] = None
):
    """
    WebSocket端点 - 实时双向通信
    """
    await websocket_service.connect(websocket)

    try:
        # 解析策略ID列表
        ids_list = None
        if strategy_ids:
            ids_list = strategy_ids.split(",")

        # 订阅策略事件
        await websocket_service.subscribe_to_strategy_events(
            websocket=websocket,
            user_id=user_id,
            strategy_ids=ids_list
        )

        # 保持连接
        while websocket.application_state == WebSocketState.CONNECTED:
            try:
                # 接收客户端消息
                data = await websocket.receive_json()

                # 处理客户端请求
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif data.get("type") == "subscribe":
                    # 更新订阅
                    await websocket_service.update_subscription(
                        websocket,
                        data.get("filters", {})
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理错误: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        pass
    finally:
        # 断开连接
        await websocket_service.disconnect(websocket)


# ============================================================================
# 增强的策略控制
# ============================================================================

@router.post("/strategies/{strategy_id}/update-with-lock", response_model=Dict[str, Any])
@handle_api_errors
async def update_strategy_with_lock(
    strategy_id: str,
    request: StrategyUpdate,
    user_id: Optional[int] = None,
    expected_version: Optional[int] = Query(None, description="期望的版本号"),
    service: EnhancedStrategyService = Depends(get_enhanced_strategy_service)
):
    """
    更新策略（支持乐观锁）
    """
    strategy = await service.update_strategy_with_optimistic_lock(
        strategy_id=strategy_id,
        request=request,
        user_id=user_id,
        expected_version=expected_version
    )

    return ResponseBuilder.build_success(
        data=strategy.dict(),
        message="策略更新成功"
    ).dict()


# ============================================================================
# API信息和健康检查
# ============================================================================

@router.get("/health", response_model=Dict[str, Any])
async def health_check_enhanced():
    """
    增强健康检查
    """
    return ResponseBuilder.build_success(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "features": [
                "增强的CRUD操作",
                "高性能批量操作",
                "实时更新支持",
                "高级搜索功能",
                "完整的错误处理",
                "WebSocket支持"
            ],
            "timestamp": datetime.now().isoformat()
        },
        message="服务运行正常"
    ).dict()


@router.get("/info", response_model=Dict[str, Any])
async def get_api_info():
    """
    获取API信息
    """
    return ResponseBuilder.build_success(
        data={
            "name": "增强策略管理API",
            "version": "1.0.0",
            "description": "基于新架构的增强版策略管理API",
            "endpoints": {
                "strategies": "/api/v1/strategies",
                "search": "/api/v1/strategies/search",
                "batch": "/api/v1/strategies/batch",
                "analytics": "/api/v1/strategies/{id}/analytics",
                "realtime": "/api/v1/strategies/realtime",
                "websocket": "/api/v1/strategies/ws"
            },
            "features": [
                "统一的响应格式",
                "完整的错误处理",
                "高性能缓存",
                "模块化设计",
                "实时更新",
                "批量操作"
            ]
        },
        message="获取API信息成功"
    ).dict()