"""
策略管理API路由
Strategy Management API Router

基于新架构的统一策略管理API路由
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ..services.strategy_service import BaseStrategyService
from ..services.execution_service import ExecutionService
from ..services.personal_service import PersonalService
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..repositories.execution_repository import ExecutionRepository
from ..utils.cache import CacheManager
from ..utils.validators import ValidatorFactory
from ..utils.response import ResponseBuilder, handle_api_errors, ValidationError
from ..schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    ExecutionRequest, ExecutionResponse, ExecutionStatusResponse,
    DashboardResponse, UserPreferences, StrategyControlRequest,
    OperationHistoryResponse, StrategyRecommendations,
    RealTimeUpdate, PaginatedResponse
)

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v2/strategies", tags=["策略管理 v2"])

# 导入增强路由器并注册
try:
    from .enhanced_router import router as enhanced_router
    # 将增强路由器作为子路由器包含
    router.include_router(enhanced_router, tags=["策略管理 v1-增强版"])
except ImportError as e:
    logger.warning(f"增强路由器导入失败: {e}")

# 依赖注入 - 获取服务实例
async def get_strategy_service() -> BaseStrategyService:
    """获取策略服务实例"""
    strategy_repo = StrategyRepository()
    user_repo = UserRepository()
    cache_manager = CacheManager()
    validator = ValidatorFactory.get_validator("strategy")
    return BaseStrategyService(strategy_repo, user_repo, cache_manager, validator)

async def get_execution_service() -> ExecutionService:
    """获取执行服务实例"""
    strategy_repo = StrategyRepository()
    execution_repo = ExecutionRepository()
    cache_manager = CacheManager()
    validator = ValidatorFactory.get_validator("execution")
    return ExecutionService(strategy_repo, execution_repo, cache_manager, validator)

async def get_personal_service() -> PersonalService:
    """获取个人服务实例"""
    strategy_repo = StrategyRepository()
    user_repo = UserRepository()
    cache_manager = CacheManager()
    validator = ValidatorFactory.get_validator("personal")
    return PersonalService(strategy_repo, user_repo, cache_manager, validator)


# ============================================================================
# 策略CRUD操作
# ============================================================================

@router.get("", response_model=Dict[str, Any])
@handle_api_errors
async def list_strategies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略列表
    """
    result = await service.list_strategies(
        page=page,
        page_size=page_size,
        strategy_type=strategy_type,
        status=status,
        user_id=user_id,
        is_active=is_active
    )

    return ResponseBuilder.build_paginated(
        items=result["strategies"],
        total=result["total_count"],
        page=page,
        page_size=page_size
    ).dict()


@router.post("", response_model=Dict[str, Any])
@handle_api_errors
async def create_strategy(
    request: StrategyCreate,
    user_id: int,
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    创建新策略
    """
    strategy = await service.create_strategy(request, user_id)
    return ResponseBuilder.build_success(
        data=strategy.dict(),
        message="策略创建成功"
    ).dict()


@router.get("/{strategy_id}", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_detail(
    strategy_id: str,
    user_id: Optional[int] = None,
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略详情
    """
    result = await service.get_strategy_detail(strategy_id, user_id)
    return ResponseBuilder.build_success(
        data=result,
        message="获取策略详情成功"
    ).dict()


@router.put("/{strategy_id}", response_model=Dict[str, Any])
@handle_api_errors
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdate,
    user_id: Optional[int] = None,
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    更新策略
    """
    strategy = await service.update_strategy(strategy_id, request, user_id)
    return ResponseBuilder.build_success(
        data=strategy.dict(),
        message="策略更新成功"
    ).dict()


@router.delete("/{strategy_id}", response_model=Dict[str, Any])
@handle_api_errors
async def delete_strategy(
    strategy_id: str,
    user_id: Optional[int] = None,
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    删除策略
    """
    await service.delete_strategy(strategy_id, user_id)
    return ResponseBuilder.build_success(
        message="策略删除成功"
    ).dict()


@router.post("/batch", response_model=Dict[str, Any])
@handle_api_errors
async def batch_operation(
    strategy_ids: List[str],
    operation: str,
    user_id: Optional[int] = None,
    parameters: Optional[Dict[str, Any]] = None,
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    批量操作策略
    """
    result = await service.batch_operation(
        strategy_ids=strategy_ids,
        operation=operation,
        user_id=user_id,
        parameters=parameters
    )
    return ResponseBuilder.build_success(
        data=result,
        message=f"批量{operation}操作完成"
    ).dict()


@router.get("/templates/list", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_templates(
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略模板列表
    """
    templates = await service.get_templates(strategy_type)
    return ResponseBuilder.build_success(
        data=[t.dict() for t in templates],
        message="获取策略模板成功"
    ).dict()


# ============================================================================
# 策略执行
# ============================================================================

@router.post("/{strategy_id}/execute", response_model=Dict[str, Any])
@handle_api_errors
async def execute_strategy(
    strategy_id: str,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[int] = None,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    执行策略
    """
    result = await service.execute_strategy(
        strategy_id=strategy_id,
        request=request,
        background_tasks=background_tasks,
        user_id=user_id
    )
    return ResponseBuilder.build_success(
        data=result.dict(),
        message="策略执行已启动"
    ).dict()


@router.get("/{strategy_id}/executions/{execution_id}/status", response_model=Dict[str, Any])
@handle_api_errors
async def get_execution_status(
    execution_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    获取执行状态
    """
    status = await service.get_execution_status(execution_id)
    return ResponseBuilder.build_success(
        data=status.dict(),
        message="获取执行状态成功"
    ).dict()


@router.post("/{strategy_id}/stop", response_model=Dict[str, Any])
@handle_api_errors
async def stop_strategy_execution(
    strategy_id: str,
    execution_id: Optional[str] = None,
    user_id: Optional[int] = None,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    停止策略执行
    """
    result = await service.stop_strategy(strategy_id, execution_id, user_id)
    return ResponseBuilder.build_success(
        data=result,
        message="策略执行已停止"
    ).dict()


@router.get("/{strategy_id}/performance", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_performance(
    strategy_id: str,
    time_range: int = Query(30, ge=1, le=365, description="时间范围（天）"),
    service: ExecutionService = Depends(get_execution_service)
):
    """
    获取策略性能指标
    """
    metrics = await service.calculate_performance_metrics(strategy_id, time_range)
    return ResponseBuilder.build_success(
        data=metrics.dict(),
        message="获取性能指标成功"
    ).dict()


@router.get("/{strategy_id}/report", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_report(
    strategy_id: str,
    report_type: str = Query("summary", description="报告类型"),
    service: ExecutionService = Depends(get_execution_service)
):
    """
    生成策略报告
    """
    report = await service.generate_strategy_report(strategy_id, report_type)
    return ResponseBuilder.build_success(
        data=report.dict(),
        message="生成策略报告成功"
    ).dict()


# ============================================================================
# 个人策略管理
# ============================================================================

@router.get("/dashboard/user/{user_id}", response_model=Dict[str, Any])
@handle_api_errors
async def get_user_dashboard(
    user_id: int,
    service: PersonalService = Depends(get_personal_service)
):
    """
    获取用户仪表板数据
    """
    dashboard = await service.get_dashboard_data(user_id)
    return ResponseBuilder.build_success(
        data=dashboard.dict(),
        message="获取仪表板数据成功"
    ).dict()


@router.get("/users/{user_id}/preferences", response_model=Dict[str, Any])
@handle_api_errors
async def get_user_preferences(
    user_id: int,
    service: PersonalService = Depends(get_personal_service)
):
    """
    获取用户偏好设置
    """
    preferences = await service.get_user_preferences(user_id)
    return ResponseBuilder.build_success(
        data=preferences.dict(),
        message="获取用户偏好成功"
    ).dict()


@router.put("/users/{user_id}/preferences", response_model=Dict[str, Any])
@handle_api_errors
async def update_user_preferences(
    user_id: int,
    preferences: UserPreferences,
    service: PersonalService = Depends(get_personal_service)
):
    """
    更新用户偏好设置
    """
    updated = await service.update_user_preferences(user_id, preferences)
    return ResponseBuilder.build_success(
        data=updated.dict(),
        message="更新用户偏好成功"
    ).dict()


@router.post("/{strategy_id}/control", response_model=Dict[str, Any])
@handle_api_errors
async def control_strategy(
    strategy_id: str,
    request: StrategyControlRequest,
    user_id: int,
    service: PersonalService = Depends(get_personal_service)
):
    """
    控制策略（启用/禁用/启动/停止/暂停）
    """
    result = await service.control_strategy(user_id, strategy_id, request)
    return ResponseBuilder.build_success(
        data=result,
        message=f"策略{request.action}操作成功"
    ).dict()


@router.get("/{strategy_id}/history", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_history(
    strategy_id: str,
    user_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    service: PersonalService = Depends(get_personal_service)
):
    """
    获取策略操作历史
    """
    history = await service.get_strategy_history(user_id, strategy_id, limit)
    return ResponseBuilder.build_success(
        data=history.dict(),
        message="获取操作历史成功"
    ).dict()


@router.get("/users/{user_id}/recommendations", response_model=Dict[str, Any])
@handle_api_errors
async def get_strategy_recommendations(
    user_id: int,
    service: PersonalService = Depends(get_personal_service)
):
    """
    获取策略推荐
    """
    recommendations = await service.get_strategy_recommendations(user_id)
    return ResponseBuilder.build_success(
        data=recommendations.dict(),
        message="获取策略推荐成功"
    ).dict()


@router.get("/users/{user_id}/realtime", response_model=Dict[str, Any])
@handle_api_errors
async def get_real_time_updates(
    user_id: int,
    service: PersonalService = Depends(get_personal_service)
):
    """
    获取实时更新数据
    """
    updates = await service.get_real_time_updates(user_id)
    return ResponseBuilder.build_success(
        data=updates.dict(),
        message="获取实时更新成功"
    ).dict()


# ============================================================================
# 工具和辅助端点
# ============================================================================

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    健康检查
    """
    return ResponseBuilder.build_success(
        data={"status": "healthy", "version": "2.0.0"},
        message="服务运行正常"
    ).dict()


@router.get("/info", response_model=Dict[str, Any])
async def get_api_info():
    """
    获取API信息
    """
    return ResponseBuilder.build_success(
        data={
            "name": "策略管理API",
            "version": "2.0.0",
            "description": "基于新架构的统一策略管理API",
            "features": [
                "统一的响应格式",
                "完整的错误处理",
                "高性能缓存",
                "模块化设计"
            ]
        },
        message="获取API信息成功"
    ).dict()


# 异常处理器
@router.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """处理验证错误"""
    error_response = ResponseBuilder.build_error(exc)
    return JSONResponse(
        status_code=400,
        content=error_response.dict()
    )


@router.exceptionHandler(NotFoundError)
async def not_found_error_handler(request, exc):
    """处理资源未找到错误"""
    error_response = ResponseBuilder.build_error(exc)
    return JSONResponse(
        status_code=404,
        content=error_response.dict()
    )


@router.exceptionHandler(PermissionError)
async def permission_error_handler(request, exc):
    """处理权限错误"""
    error_response = ResponseBuilder.build_error(exc)
    return JSONResponse(
        status_code=403,
        content=error_response.dict()
    )