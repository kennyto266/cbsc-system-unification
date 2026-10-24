"""
策略执行引擎
Strategy Execution Engine

职责：
- 策略执行管理
- 执行状态跟踪
- 性能分析和报告
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional
import logging

from .services.execution_service import ExecutionService
from .repositories.execution_repository import ExecutionRepository
from .repositories.strategy_repository import StrategyRepository
from .utils.cache import CacheManager
from .utils.validators import ExecutionValidator
from .utils.permissions import get_current_user, require_strategy_permission
from .schemas import (
    ExecutionRequest, ExecutionResponse, ExecutionStatusResponse,
    PerformanceMetrics, ExecutionReport, BaseResponse
)
from .models import User

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# 依赖注入
async def get_execution_service() -> ExecutionService:
    """获取执行服务实例"""
    # 这里应该通过依赖注入容器获取
    strategy_repo = StrategyRepository()
    execution_repo = ExecutionRepository()
    cache_manager = CacheManager()
    validator = ExecutionValidator()
    return ExecutionService(strategy_repo, execution_repo, cache_manager, validator)


# ============================================================================
# 策略执行端点 (Strategy Execution Endpoints)
# ============================================================================

@router.post("/{strategy_id}/execute", response_model=ExecutionResponse)
async def execute_strategy(
    strategy_id: str,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    执行策略

    支持两种执行模式：
    - backtest: 历史数据回测
    - real_time: 实时数据执行

    执行将在后台进行，可通过执行ID查询状态。
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "execute", current_user)

        # 设置策略ID
        request.strategy_id = strategy_id

        # 执行策略
        result = await execution_service.execute_strategy(
            strategy_id,
            request,
            background_tasks,
            current_user.id
        )

        return result

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
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"执行策略失败: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    获取执行状态

    返回执行的当前状态、进度和性能信息。
    """
    try:
        result = await execution_service.get_execution_status(execution_id)

        # 权限检查 - 验证用户是否有权限查看此执行
        execution = await execution_service.execution_repo.get_by_id(execution_id)
        if execution:
            await require_strategy_permission(execution.strategy_id, "view", current_user)

        return result

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
        logger.error(f"获取执行状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取执行状态失败: {str(e)}"
        )


@router.post("/{strategy_id}/stop", response_model=BaseResponse)
async def stop_strategy_execution(
    strategy_id: str,
    execution_id: Optional[str] = Query(None, description="执行ID，不指定则停止所有执行"),
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    停止策略执行

    可以停止指定的执行实例，或停止策略的所有执行。
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "control", current_user)

        result = await execution_service.stop_execution(
            strategy_id,
            execution_id,
            current_user.id
        )

        return BaseResponse(
            data=result,
            message="策略执行已停止"
        )

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
        logger.error(f"停止策略执行失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"停止策略执行失败: {str(e)}"
        )


@router.get("/{strategy_id}/performance", response_model=PerformanceMetrics)
async def get_strategy_performance(
    strategy_id: str,
    time_range: int = Query(30, ge=1, le=365, description="时间范围（天数）"),
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    获取策略性能指标

    计算指定时间范围内的策略性能指标：
    - 总收益率
    - 年化收益率
    - 夏普比率
    - 最大回撤
    - 胜率
    - 盈利因子
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "view", current_user)

        metrics = await execution_service.calculate_performance_metrics(
            strategy_id,
            time_range
        )

        return metrics

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
        logger.error(f"获取策略性能失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略性能失败: {str(e)}"
        )


@router.get("/{strategy_id}/reports", response_model=ExecutionReport)
async def get_strategy_report(
    strategy_id: str,
    report_type: str = Query("summary", pattern="^(summary|detailed|trade|risk)$", description="报告类型"),
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    获取策略报告

    支持多种报告类型：
    - summary: 摘要报告
    - detailed: 详细报告
    - trade: 交易分析报告
    - risk: 风险分析报告
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "view", current_user)

        report = await execution_service.generate_strategy_report(
            strategy_id,
            report_type
        )

        return report

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
        logger.error(f"获取策略报告失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略报告失败: {str(e)}"
        )


@router.get("/{strategy_id}/executions", response_model=dict)
async def list_strategy_executions(
    strategy_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="执行状态过滤"),
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    获取策略执行历史

    返回策略的所有执行记录，支持分页和状态过滤。
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "view", current_user)

        # 获取执行列表
        executions, total_count = await execution_service.execution_repo.get_executions(
            strategy_id=strategy_id,
            page=page,
            page_size=page_size,
            status=status
        )

        # 转换为响应格式
        result = {
            "executions": [
                {
                    "execution_id": e.execution_id,
                    "strategy_id": e.strategy_id,
                    "status": e.status.value,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                    "execution_mode": e.execution_mode,
                    "total_signals": len(e.signals) if e.signals else 0,
                    "performance_summary": {
                        "total_return": e.performance.total_return,
                        "sharpe_ratio": e.performance.sharpe_ratio
                    } if e.performance else None
                }
                for e in executions
            ],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }

        return result

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取执行历史失败: {str(e)}"
        )


@router.post("/{strategy_id}/optimize", response_model=BaseResponse)
async def optimize_strategy(
    strategy_id: str,
    optimization_request: dict,
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    策略参数优化

    使用指定的优化方法自动寻找最优参数组合。
    支持的优化方法：
    - grid_search: 网格搜索
    - random_search: 随机搜索
    - bayesian: 贝叶斯优化
    """
    try:
        # 权限检查
        await require_strategy_permission(strategy_id, "optimize", current_user)

        # 这里应该调用优化服务
        # 暂时返回模拟结果
        result = {
            "strategy_id": strategy_id,
            "optimization_id": f"opt_{strategy_id}_{execution_service.execution_repo.generate_id()}",
            "status": "started",
            "message": "优化任务已启动"
        }

        return BaseResponse(
            data=result,
            message="策略优化已启动"
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"策略优化失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"策略优化失败: {str(e)}"
        )


@router.get("/executions/running", response_model=dict)
async def list_running_executions(
    current_user: User = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    获取所有运行中的执行

    返回当前用户的所有正在运行的策略执行。
    """
    try:
        # 获取用户的所有策略
        user_strategies = await execution_service.strategy_repo.get_user_strategies(current_user.id)

        # 获取所有运行中的执行
        running_executions = []
        for strategy in user_strategies:
            executions = await execution_service.execution_repo.get_running_executions(strategy.id)
            for execution in executions:
                running_executions.append({
                    "execution_id": execution.execution_id,
                    "strategy_id": execution.strategy_id,
                    "strategy_name": strategy.name,
                    "start_time": execution.start_time,
                    "progress": await execution_service._calculate_execution_progress(execution),
                    "current_step": await execution_service._get_current_execution_step(execution)
                })

        return {
            "running_executions": running_executions,
            "total_count": len(running_executions)
        }

    except Exception as e:
        logger.error(f"获取运行中执行失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取运行中执行失败: {str(e)}"
        )