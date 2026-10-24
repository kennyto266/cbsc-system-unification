"""
策略基础CRUD操作
Strategy Base CRUD Operations

职责：
- 策略的增删改查
- 策略列表和详情
- 基础验证和权限检查
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
import logging

from .services.strategy_service import BaseStrategyService
from .repositories.strategy_repository import StrategyRepository
from .repositories.user_repository import UserRepository
from .utils.cache import CacheManager
from .utils.validators import StrategyValidator
from .utils.permissions import get_current_user, require_strategy_permission
from .container import get_strategy_service
from .schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListResponse, StrategyDetailResponse,
    BatchStrategyOperation, BaseResponse
)
from .models import User, Strategy, StrategyTemplate

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# 依赖注入 - 使用 DI 容器
# 已在 container.py 中定义 get_strategy_service 函数


# ============================================================================
# 策略CRUD端点 (Strategy CRUD Endpoints)
# ============================================================================

@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略列表

    支持分页和多种过滤条件：
    - 按策略类型过滤
    - 按状态过滤
    - 按激活状态过滤
    """
    try:
        result = await strategy_service.list_strategies(
            page=page,
            page_size=page_size,
            strategy_type=strategy_type,
            status=status,
            user_id=current_user.id,
            is_active=is_active
        )
        return StrategyListResponse(**result)
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略列表失败: {str(e)}"
        )


@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    request: StrategyCreate,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    创建新策略

    支持从模板创建策略，如果指定了template_id，将使用模板的默认参数。
    策略名称在同一用户下必须唯一。
    """
    try:
        strategy = await strategy_service.create_strategy(request, current_user.id)
        return strategy
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"创建策略失败: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略详情

    返回策略的完整信息，：
    - 基本信息
    - 最近信号
    - 性能指标
    - 执行历史
    """
    try:
        result = await strategy_service.get_strategy_detail(strategy_id, current_user.id)
        return StrategyDetailResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略详情失败: {str(e)}"
        )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    更新策略信息

    可以更新的字段包括：
    - 名称
    - 描述
    - 参数
    - 状态
    - 激活状态
    - 风险等级
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "update", current_user)

        strategy = await strategy_service.update_strategy(strategy_id, request, current_user.id)
        return strategy
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新策略失败: {str(e)}"
        )


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    删除策略

    注意：
    - 无法删除正在运行的策略
    - 删除操作不可逆
    - 相关的历史数据也会被删除
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "delete", current_user)

        await strategy_service.delete_strategy(strategy_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除策略失败: {str(e)}"
        )


@router.post("/batch-operation", response_model=BaseResponse)
async def batch_operation(
    request: BatchStrategyOperation,
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    批量操作策略

    支持的批量操作：
    - activate: 批量激活
    - deactivate: 批量停用
    - delete: 批量删除
    - execute: 批量执行
    """
    try:
        # 权限检查（对每个策略）
        for strategy_id in request.strategy_ids:
            await require_strategy_permission(strategy_id, "batch", current_user)

        result = await strategy_service.batch_operation(
            request.strategy_ids,
            request.operation,
            current_user.id,
            request.parameters
        )

        return BaseResponse(
            data=result,
            message=f"批量操作完成: 成功 {len(result['success'])} 个, 失败 {len(result['failed'])} 个"
        )
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量操作失败: {str(e)}"
        )


# ============================================================================
# 策略模板端点 (Strategy Template Endpoints)
# ============================================================================

@router.get("/templates/", response_model=List[StrategyTemplate])
async def get_strategy_templates(
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    获取策略模板列表

    返回所有可用的策略模板，可以按类型过滤。
    模板包含预定义的参数和约束。
    """
    try:
        from .models import StrategyType
        templates = await strategy_service.get_templates(
            StrategyType(strategy_type) if strategy_type else None
        )
        return templates
    except Exception as e:
        logger.error(f"获取策略模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略模板失败: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=StrategyTemplate)
async def get_strategy_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取策略模板详情

    返回指定模板的完整信息，包括：
    - 基本描述
    - 默认参数
    - 参数约束
    - 适用场景
    """
    try:
        from .models import StrategyTemplates
        template = StrategyTemplates.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"模板不存在: {template_id}"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略模板详情失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略模板详情失败: {str(e)}"
        )


# ============================================================================
# 策略复制端点 (Strategy Clone Endpoints)
# ============================================================================

@router.post("/{strategy_id}/clone", response_model=StrategyResponse, status_code=201)
async def clone_strategy(
    strategy_id: str,
    new_name: Optional[str] = Query(None, description="新策略名称"),
    current_user: User = Depends(get_current_user),
    strategy_service: BaseStrategyService = Depends(get_strategy_service)
):
    """
    克隆策略

    创建指定策略的副本，保留所有参数和配置。
    可以选择指定新的策略名称。
    """
    try:
        # 获取原策略详情
        strategy_detail = await strategy_service.get_strategy_detail(strategy_id, current_user.id)
        original_strategy = strategy_detail["strategy"]

        # 创建克隆请求
        clone_request = StrategyCreate(
            name=new_name or f"{original_strategy.name}_副本",
            description=original_strategy.description,
            strategy_type=original_strategy.strategy_type,
            parameters=await strategy_service.strategy_repo.get_strategy_parameters(strategy_id),
            risk_level=original_strategy.risk_level
        )

        # 创建新策略
        new_strategy = await strategy_service.create_strategy(clone_request, current_user.id)

        return new_strategy
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"克隆策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"克隆策略失败: {str(e)}"
        )