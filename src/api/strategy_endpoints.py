#!/usr/bin/env python3
"""
CBSC策略管理API端点 (Task 005)
CBSC Strategy Management API Endpoints

提供完整的CBSC策略管理REST API接口，包括策略CRUD、执行、监控等功能
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi import status

from .strategy_management_api import (
    Strategy, StrategySignal, StrategyPerformance, StrategyType,
    SignalType, StrategyStatus, RiskLevel, StrategyExecutionRequest,
    StrategyExecutionResult, CreateStrategyRequest, UpdateStrategyRequest,
    StrategyListResponse, StrategyDetailResponse, BatchStrategyOperation,
    StrategyOptimizationRequest, StrategyOptimizationResult,
    CBSCStrategyTemplate, StrategyTemplates, DataCompatibilityAdapter
)

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/strategies", tags=["strategies"])

# ============================================================================
# 全局状态管理 (Global State Management)
# ============================================================================

class StrategyManager:
    """策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.signals: List[StrategySignal] = []
        self.performances: Dict[str, StrategyPerformance] = {}
        self.executions: Dict[str, StrategyExecutionResult] = {}
        self.templates: Dict[str, CBSCStrategyTemplate] = {}

    async def initialize(self):
        """初始化策略管理器"""
        logger.info("初始化策略管理器...")

        # 加载默认模板
        templates = StrategyTemplates.get_all_templates()
        for template in templates:
            self.templates[template.id] = template

        # 加载现有策略
        await self._load_existing_strategies()

        logger.info(f"策略管理器初始化完成: {len(self.strategies)}个策略, {len(self.templates)}个模板")

    async def _load_existing_strategies(self):
        """加载现有策略"""
        # 实现从数据库加载策略的逻辑
        pass

# 全局策略管理器实例
strategy_manager = StrategyManager()

# ============================================================================
# 依赖注入 (Dependency Injection)
# ============================================================================

async def get_strategy_manager() -> StrategyManager:
    """获取策略管理器实例"""
    return strategy_manager

async def validate_strategy_exists(strategy_id: str) -> Strategy:
    """验证策略是否存在"""
    if strategy_id not in strategy_manager.strategies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在: {strategy_id}"
        )
    return strategy_manager.strategies[strategy_id]

# ============================================================================
# 策略CRUD操作 (Strategy CRUD Operations)
# ============================================================================

@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型过滤"),
    status: Optional[StrategyStatus] = Query(None, description="状态过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> StrategyListResponse:
    """
    获取策略列表

    - **page**: 页码，从1开始
    - **page_size**: 每页大小，最大100
    - **strategy_type**: 策略类型过滤
    - **status**: 状态过滤
    - **is_active**: 是否激活过滤
    """
    try:
        # 应用过滤条件
        filtered_strategies = list(manager.strategies.values())

        if strategy_type:
            filtered_strategies = [s for s in filtered_strategies if s.strategy_type == strategy_type]

        if status:
            filtered_strategies = [s for s in filtered_strategies if s.status == status]

        if is_active is not None:
            filtered_strategies = [s for s in filtered_strategies if s.is_active == is_active]

        # 分页
        total_count = len(filtered_strategies)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_strategies = filtered_strategies[start_index:end_index]

        return StrategyListResponse(
            strategies=paginated_strategies,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )

@router.post("/", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: CreateStrategyRequest,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> Strategy:
    """
    创建新策略

    - **name**: 策略名称 (1-100字符)
    - **description**: 策略描述 (1-500字符)
    - **strategy_type**: 策略类型
    - **parameters**: 策略参数
    - **template_id**: 可选，基于模板创建
    """
    try:
        # 验证策略名称唯一性
        for strategy in manager.strategies.values():
            if strategy.name == request.name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"策略名称已存在: {request.name}"
                )

        # 如果指定了模板，使用模板参数
        parameters = request.parameters
        if request.template_id and request.template_id in manager.templates:
            template = manager.templates[request.template_id]
            parameters = template.default_parameters

        # 生成策略ID
        strategy_id = f"{request.strategy_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建策略
        strategy = Strategy(
            id=strategy_id,
            name=request.name,
            description=request.description,
            strategy_type=request.strategy_type,
            parameters=parameters,
            is_active=False  # 新创建的策略默认不激活
        )

        # 保存策略
        manager.strategies[strategy_id] = strategy

        logger.info(f"创建策略成功: {strategy_id} - {strategy.name}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}"
        )

@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy: Strategy = Depends(validate_strategy_exists),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> StrategyDetailResponse:
    """
    获取策略详情

    - **strategy_id**: 策略ID
    """
    try:
        # 获取最近信号
        recent_signals = [
            signal for signal in manager.signals[-50:]
            if signal.strategy_type == strategy.strategy_type
        ]

        # 获取性能数据
        performance = manager.performances.get(strategy.id)

        # 获取执行历史
        execution_history = [
            exec_result for exec_id, exec_result in manager.executions.items()
            if exec_result.strategy_id == strategy.id
        ]

        return StrategyDetailResponse(
            strategy=strategy,
            recent_signals=recent_signals,
            performance=performance,
            execution_history=execution_history
        )

    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略详情失败: {str(e)}"
        )

@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy: Strategy = Depends(validate_strategy_exists),
    request: UpdateStrategyRequest = None,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> Strategy:
    """
    更新策略

    - **strategy_id**: 策略ID
    - **name**: 可选，策略名称
    - **description**: 可选，策略描述
    - **parameters**: 可选，策略参数
    - **status**: 可选，策略状态
    - **is_active**: 可选，是否激活
    """
    try:
        # 更新策略字段
        if request.name is not None:
            strategy.name = request.name

        if request.description is not None:
            strategy.description = request.description

        if request.parameters is not None:
            strategy.parameters = request.parameters

        if request.status is not None:
            strategy.status = request.status

        if request.is_active is not None:
            strategy.is_active = request.is_active

        strategy.updated_at = datetime.now()

        logger.info(f"更新策略成功: {strategy.id}")
        return strategy

    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新策略失败: {str(e)}"
        )

@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy: Strategy = Depends(validate_strategy_exists),
    manager: StrategyManager = Depends(get_strategy_manager)
):
    """
    删除策略

    - **strategy_id**: 策略ID
    """
    try:
        # 删除策略
        del manager.strategies[strategy.id]

        # 删除相关数据
        if strategy.id in manager.performances:
            del manager.performances[strategy.id]

        # 删除相关的执行记录
        exec_ids_to_delete = [
            exec_id for exec_id, exec_result in manager.executions.items()
            if exec_result.strategy_id == strategy.id
        ]
        for exec_id in exec_ids_to_delete:
            del manager.executions[exec_id]

        logger.info(f"删除策略成功: {strategy.id}")

    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除策略失败: {str(e)}"
        )

# ============================================================================
# 策略执行管理 (Strategy Execution Management)
# ============================================================================

@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResult)
async def execute_strategy(
    strategy: Strategy = Depends(validate_strategy_exists),
    request: StrategyExecutionRequest = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> StrategyExecutionResult:
    """
    执行策略

    - **strategy_id**: 策略ID
    - **start_time**: 可选，开始时间
    - **end_time**: 可选，结束时间
    - **execution_mode**: 执行模式 (backtest/real_time)
    - **data_source**: 可选，数据源
    - **parameters_override**: 可选，参数覆盖
    """
    try:
        # 生成执行ID
        execution_id = f"exec_{strategy.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建执行请求
        if request is None:
            request = StrategyExecutionRequest(
                strategy_id=strategy.id,
                execution_mode="backtest"
            )

        # 初始化执行结果
        execution_result = StrategyExecutionResult(
            execution_id=execution_id,
            strategy_id=strategy.id,
            status="running",
            start_time=request.start_time or datetime.now()
        )

        # 保存执行结果
        manager.executions[execution_id] = execution_result

        # 在后台执行策略
        background_tasks.add_task(
            _execute_strategy_background,
            strategy,
            request,
            execution_result,
            manager
        )

        logger.info(f"开始执行策略: {strategy.id} - {execution_id}")
        return execution_result

    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行策略失败: {str(e)}"
        )

@router.get("/{strategy_id}/executions/{execution_id}", response_model=StrategyExecutionResult)
async def get_execution_result(
    strategy: Strategy = Depends(validate_strategy_exists),
    execution_id: str,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> StrategyExecutionResult:
    """
    获取策略执行结果

    - **strategy_id**: 策略ID
    - **execution_id**: 执行ID
    """
    try:
        if execution_id not in manager.executions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"执行记录不存在: {execution_id}"
            )

        execution_result = manager.executions[execution_id]

        # 验证执行记录是否属于该策略
        if execution_result.strategy_id != strategy.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"执行记录不属于策略: {strategy.id}"
            )

        return execution_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行结果失败: {str(e)}"
        )

@router.post("/{strategy_id}/stop", status_code=status.HTTP_200_OK)
async def stop_strategy_execution(
    strategy: Strategy = Depends(validate_strategy_exists),
    execution_id: Optional[str] = Query(None, description="执行ID，如果不指定则停止所有执行"),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> Dict[str, str]:
    """
    停止策略执行

    - **strategy_id**: 策略ID
    - **execution_id**: 可选，执行ID，如果不指定则停止所有执行
    """
    try:
        stopped_count = 0

        if execution_id:
            # 停止指定执行
            if execution_id in manager.executions:
                exec_result = manager.executions[execution_id]
                if exec_result.strategy_id == strategy.id and exec_result.status == "running":
                    exec_result.status = "stopped"
                    exec_result.end_time = datetime.now()
                    stopped_count = 1
        else:
            # 停止所有相关执行
            for exec_result in manager.executions.values():
                if exec_result.strategy_id == strategy.id and exec_result.status == "running":
                    exec_result.status = "stopped"
                    exec_result.end_time = datetime.now()
                    stopped_count += 1

        logger.info(f"停止策略执行: {strategy.id} - 停止了{stopped_count}个执行")
        return {
            "strategy_id": strategy.id,
            "stopped_executions": stopped_count,
            "message": f"成功停止{stopped_count}个执行"
        }

    except Exception as e:
        logger.error(f"停止策略执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略执行失败: {str(e)}"
        )

# ============================================================================
# 信号管理 (Signal Management)
# ============================================================================

@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy: Strategy = Depends(validate_strategy_exists),
    limit: int = Query(100, ge=1, le=1000, description="信号数量限制"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    signal_type: Optional[SignalType] = Query(None, description="信号类型过滤"),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> Dict[str, List[StrategySignal]]:
    """
    获取策略信号

    - **strategy_id**: 策略ID
    - **limit**: 信号数量限制
    - **start_time**: 可选，开始时间
    - **end_time**: 可选，结束时间
    - **signal_type**: 可选，信号类型过滤
    """
    try:
        # 过滤策略信号
        signals = [
            signal for signal in manager.signals
            if signal.strategy_type == strategy.strategy_type
        ]

        # 时间范围过滤
        if start_time:
            signals = [s for s in signals if s.timestamp >= start_time]

        if end_time:
            signals = [s for s in signals if s.timestamp <= end_time]

        # 信号类型过滤
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]

        # 按时间倒序排列并限制数量
        signals.sort(key=lambda x: x.timestamp, reverse=True)
        signals = signals[:limit]

        return {"signals": signals}

    except Exception as e:
        logger.error(f"获取策略信号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略信号失败: {str(e)}"
        )

# ============================================================================
# 批量操作 (Batch Operations)
# ============================================================================

@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_operation(
    request: BatchStrategyOperation,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> Dict[str, Any]:
    """
    批量策略操作

    - **strategy_ids**: 策略ID列表
    - **operation**: 操作类型 (activate/deactivate/delete)
    - **parameters**: 可选，操作参数
    """
    try:
        if request.operation not in ["activate", "deactivate", "delete"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {request.operation}"
            )

        success_count = 0
        failed_operations = []

        for strategy_id in request.strategy_ids:
            try:
                if strategy_id not in manager.strategies:
                    failed_operations.append({
                        "strategy_id": strategy_id,
                        "error": "策略不存在"
                    })
                    continue

                strategy = manager.strategies[strategy_id]

                if request.operation == "activate":
                    strategy.is_active = True
                    strategy.status = StrategyStatus.ACTIVE
                elif request.operation == "deactivate":
                    strategy.is_active = False
                    strategy.status = StrategyStatus.INACTIVE
                elif request.operation == "delete":
                    del manager.strategies[strategy_id]
                    # 删除相关数据
                    if strategy_id in manager.performances:
                        del manager.performances[strategy_id]

                success_count += 1
                strategy.updated_at = datetime.now()

            except Exception as e:
                failed_operations.append({
                    "strategy_id": strategy_id,
                    "error": str(e)
                })

        logger.info(f"批量操作完成: {request.operation} - 成功{success_count}个, 失败{len(failed_operations)}个")

        return {
            "operation": request.operation,
            "total_strategies": len(request.strategy_ids),
            "success_count": success_count,
            "failed_count": len(failed_operations),
            "failed_operations": failed_operations
        }

    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )

# ============================================================================
# 策略模板 (Strategy Templates)
# ============================================================================

@router.get("/templates", response_model=List[CBSCStrategyTemplate])
async def get_strategy_templates(
    category: Optional[str] = Query(None, description="模板分类过滤"),
    manager: StrategyManager = Depends(get_strategy_manager)
) -> List[CBSCStrategyTemplate]:
    """
    获取策略模板列表

    - **category**: 可选，模板分类过滤
    """
    try:
        templates = list(manager.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    except Exception as e:
        logger.error(f"获取策略模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略模板失败: {str(e)}"
        )

@router.get("/templates/{template_id}", response_model=CBSCStrategyTemplate)
async def get_strategy_template(
    template_id: str,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> CBSCStrategyTemplate:
    """
    获取策略模板详情

    - **template_id**: 模板ID
    """
    try:
        if template_id not in manager.templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板不存在: {template_id}"
            )

        return manager.templates[template_id]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略模板失败: {str(e)}"
        )

# ============================================================================
# 参数优化 (Parameter Optimization)
# ============================================================================

@router.post("/{strategy_id}/optimize", response_model=StrategyOptimizationResult)
async def optimize_strategy_parameters(
    strategy: Strategy = Depends(validate_strategy_exists),
    request: StrategyOptimizationRequest,
    background_tasks: BackgroundTasks,
    manager: StrategyManager = Depends(get_strategy_manager)
) -> StrategyOptimizationResult:
    """
    优化策略参数

    - **strategy_id**: 策略ID
    - **optimization_method**: 优化方法 (grid/random/bayes)
    - **parameter_ranges**: 参数范围
    - **objective_metric**: 优化目标
    - **max_iterations**: 最大迭代次数
    - **time_range**: 时间范围
    """
    try:
        # 生成优化ID
        optimization_id = f"opt_{strategy.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建初始优化结果
        optimization_result = StrategyOptimizationResult(
            optimization_id=optimization_id,
            strategy_id=strategy.id,
            best_parameters=strategy.parameters,
            best_performance=StrategyPerformance(
                strategy_type=strategy.strategy_type,
                total_return=0.0,
                annual_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                calmar_ratio=0.0,
                total_trades=0,
                profit_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
                last_updated=datetime.now()
            ),
            optimization_history=[],
            convergence_info={}
        )

        # 在后台执行优化
        background_tasks.add_task(
            _optimize_strategy_background,
            strategy,
            request,
            optimization_result,
            manager
        )

        logger.info(f"开始参数优化: {strategy.id} - {optimization_id}")
        return optimization_result

    except Exception as e:
        logger.error(f"参数优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数优化失败: {str(e)}"
        )

# ============================================================================
# 后台任务 (Background Tasks)
# ============================================================================

async def _execute_strategy_background(
    strategy: Strategy,
    request: StrategyExecutionRequest,
    execution_result: StrategyExecutionResult,
    manager: StrategyManager
):
    """后台执行策略"""
    try:
        logger.info(f"后台执行策略: {strategy.id}")

        # 模拟策略执行
        await asyncio.sleep(2)

        # 生成模拟信号
        signals = []
        for i in range(5):
            signal = StrategySignal(
                signal_id=f"{execution_result.execution_id}_signal_{i+1}",
                strategy_type=strategy.strategy_type,
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                strength=75.0 + i * 5,
                confidence=80.0 + i * 3,
                timestamp=datetime.now(),
                market_data={"price": 150.0 + i * 10, "volume": 1000000 + i * 100000},
                parameters=request.parameters_override or strategy.parameters,
                metadata={"execution_id": execution_result.execution_id}
            )
            signals.append(signal)

        # 计算性能指标
        performance = StrategyPerformance(
            strategy_type=strategy.strategy_type,
            total_return=0.15,
            annual_return=0.18,
            sharpe_ratio=1.25,
            max_drawdown=-0.08,
            win_rate=0.65,
            profit_factor=1.8,
            calmar_ratio=1.5,
            total_trades=50,
            profit_trades=32,
            avg_profit=0.025,
            avg_loss=-0.015,
            last_updated=datetime.now()
        )

        # 更新执行结果
        execution_result.signals = signals
        execution_result.performance = performance
        execution_result.status = "completed"
        execution_result.end_time = datetime.now()

        # 保存信号和性能数据
        manager.signals.extend(signals)
        manager.performances[strategy.id] = performance

        logger.info(f"策略执行完成: {strategy.id} - {execution_result.execution_id}")

    except Exception as e:
        logger.error(f"后台执行策略失败: {e}")
        execution_result.status = "error"
        execution_result.error_message = str(e)
        execution_result.end_time = datetime.now()

async def _optimize_strategy_background(
    strategy: Strategy,
    request: StrategyOptimizationRequest,
    optimization_result: StrategyOptimizationResult,
    manager: StrategyManager
):
    """后台优化策略参数"""
    try:
        logger.info(f"后台优化策略参数: {strategy.id}")

        # 模拟参数优化
        iterations = min(request.max_iterations, 10)  # 限制迭代次数用于演示
        best_performance = 0.0

        for i in range(iterations):
            await asyncio.sleep(0.5)  # 模拟计算时间

            # 模拟优化历史
            history_entry = {
                "iteration": i + 1,
                "parameters": {
                    "rsi_period": 14 + i % 5,
                    "oversold_threshold": 30 + i % 10
                },
                "performance": {
                    "sharpe_ratio": 1.0 + i * 0.05,
                    "total_return": 0.1 + i * 0.01
                }
            }
            optimization_result.optimization_history.append(history_entry)

            # 更新最优结果
            current_performance = history_entry["performance"]["sharpe_ratio"]
            if current_performance > best_performance:
                best_performance = current_performance
                optimization_result.best_performance.sharpe_ratio = current_performance

        # 设置最终结果
        optimization_result.best_parameters = StrategyParameters(
            rsi_period=16,
            oversold_threshold=32,
            overbought_threshold=68
        )

        optimization_result.convergence_info = {
            "converged": True,
            "iterations": iterations,
            "best_iteration": iterations,
            "improvement": best_performance - 1.0
        }

        logger.info(f"参数优化完成: {strategy.id} - {optimization_result.optimization_id}")

    except Exception as e:
        logger.error(f"后台参数优化失败: {e}")
        optimization_result.convergence_info = {
            "converged": False,
            "error": str(e)
        }

# ============================================================================
# 应用生命周期管理 (Application Lifecycle Management)
# ============================================================================

@asynccontextmanager
async def lifespan_strategy_manager(app):
    """策略管理器生命周期管理"""
    # 启动时初始化
    await strategy_manager.initialize()
    yield
    # 关闭时清理资源
    pass

# 导出路由和生命周期管理
__all__ = [
    "router",
    "lifespan_strategy_manager",
    "StrategyManager"
]