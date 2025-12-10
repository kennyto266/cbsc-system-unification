"""
策略执行服务
Strategy Execution Service

职责：
- 策略执行管理
- 执行状态跟踪
- 性能分析和报告
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

from .strategy_service import BaseStrategyService
from ..repositories.execution_repository import ExecutionRepository
from ..repositories.strategy_repository import StrategyRepository
from ..utils.cache import CacheManager
from ..utils.validators import ExecutionValidator
from ..models import (
    StrategyExecution, StrategyExecutionRequest, StrategyExecutionResult,
    StrategyPerformance, ExecutionStatus, Strategy, StrategySignal, SignalType
)
from ..schemas import (
    ExecutionRequest, ExecutionResponse, ExecutionStatusResponse,
    PerformanceMetrics, ExecutionReport
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """执行配置"""
    max_concurrent_executions: int = 10
    default_execution_timeout: int = 3600  # 1小时
    performance_calculation_interval: int = 300  # 5分钟
    signal_generation_threshold: float = 0.6


class ExecutionService(BaseStrategyService):
    """
    策略执行服务
    继承BaseStrategyService，扩展执行相关功能
    """

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        execution_repo: ExecutionRepository,
        cache_manager: CacheManager,
        validator: ExecutionValidator,
        config: ExecutionConfig = None
    ):
        # 初始化基类（需要user_repo，但执行服务可能不需要）
        from ..repositories.user_repository import UserRepository
        from ..utils.validators import StrategyValidator
        user_repo = UserRepository()
        strategy_validator = StrategyValidator()

        super().__init__(strategy_repo, user_repo, cache_manager, strategy_validator)

        self.execution_repo = execution_repo
        self.validator = validator
        self.config = config or ExecutionConfig()
        self.running_executions: Dict[str, asyncio.Task] = {}

    async def execute_strategy(
        self,
        strategy_id: str,
        request: ExecutionRequest,
        background_tasks: Any,
        user_id: Optional[int] = None
    ) -> ExecutionResponse:
        """
        执行策略

        Args:
            strategy_id: 策略ID
            request: 执行请求
            background_tasks: 后台任务
            user_id: 用户ID

        Returns:
            执行响应
        """
        # 获取策略信息
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            raise PermissionError(f"无权限执行策略: {strategy_id}")

        # 验证执行请求
        await self.validator.validate_execution_request(request, strategy)

        # 检查并发执行限制
        running_count = len(self.running_executions)
        if running_count >= self.config.max_concurrent_executions:
            raise ValueError(f"并发执行数量已达上限: {running_count}")

        # 生成执行ID
        execution_id = f"exec_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建执行记录
        execution = StrategyExecution(
            execution_id=execution_id,
            strategy_id=strategy_id,
            status=ExecutionStatus.PENDING,
            execution_mode=request.execution_mode,
            data_source=request.data_source,
            execution_metadata={
                "user_id": user_id,
                "request_data": request.dict(),
                "started_at": datetime.now().isoformat()
            }
        )

        # 保存执行记录
        execution = await self.execution_repo.create(execution)

        # 启动后台执行任务
        task = asyncio.create_task(
            self._run_strategy_execution(execution, request, background_tasks)
        )
        self.running_executions[execution_id] = task

        logger.info(f"开始执行策略: {strategy_id}, 执行ID: {execution_id}")

        # 估算完成时间（基于历史数据）
        estimated_completion = await self._estimate_execution_time(strategy, request)

        return ExecutionResponse(
            execution_id=execution_id,
            strategy_id=strategy_id,
            status=execution.status.value,
            start_time=execution.start_time,
            end_time=execution.end_time,
            estimated_completion=estimated_completion,
            progress=0.0
        )

    async def get_execution_status(self, execution_id: str) -> ExecutionStatusResponse:
        """
        获取执行状态

        Args:
            execution_id: 执行ID

        Returns:
            执行状态响应
        """
        # 从缓存获取
        cache_key = f"execution:status:{execution_id}"
        cached_status = await self.cache.get(cache_key)
        if cached_status:
            return ExecutionStatusResponse(**cached_status)

        # 从数据库获取
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"执行不存在: {execution_id}")

        # 获取当前进度和性能
        progress = await self._calculate_execution_progress(execution)
        current_step = await self._get_current_execution_step(execution)
        performance_summary = await self._get_execution_performance_summary(execution)

        result = ExecutionStatusResponse(
            execution_id=execution_id,
            strategy_id=execution.strategy_id,
            status=execution.status.value,
            start_time=execution.start_time,
            end_time=execution.end_time,
            progress=progress,
            current_step=current_step,
            error_message=execution.error_message,
            performance_summary=performance_summary
        )

        # 缓存状态
        await self.cache.set(cache_key, result.dict(), ttl=60)

        return result

    async def stop_execution(
        self,
        strategy_id: str,
        execution_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        停止策略执行

        Args:
            strategy_id: 策略ID
            execution_id: 执行ID（可选，如果不指定则停止所有执行）
            user_id: 用户ID

        Returns:
            停止结果
        """
        if execution_id:
            # 停止指定执行
            return await self._stop_specific_execution(execution_id, user_id)
        else:
            # 停止策略的所有执行
            return await self._stop_all_strategy_executions(strategy_id, user_id)

    async def calculate_performance_metrics(
        self,
        strategy_id: str,
        time_range: int = 30
    ) -> PerformanceMetrics:
        """
        计算策略性能指标

        Args:
            strategy_id: 策略ID
            time_range: 时间范围（天数）

        Returns:
            性能指标
        """
        # 尝试从缓存获取
        cache_key = f"performance:metrics:{strategy_id}:{time_range}"
        cached_metrics = await self.cache.get(cache_key)
        if cached_metrics:
            return PerformanceMetrics(**cached_metrics)

        # 从数据库获取历史数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_range)

        executions = await self.execution_repo.get_executions_by_date_range(
            strategy_id, start_date, end_date
        )

        # 计算性能指标
        metrics = await self._calculate_performance_from_executions(executions, time_range)

        # 缓存结果
        await self.cache.set(cache_key, metrics.dict(), ttl=self.config.performance_calculation_interval)

        return metrics

    async def generate_strategy_report(
        self,
        strategy_id: str,
        report_type: str = "summary"
    ) -> ExecutionReport:
        """
        生成策略报告

        Args:
            strategy_id: 策略ID
            report_type: 报告类型

        Returns:
            执行报告
        """
        # 获取策略信息
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 获取执行历史
        executions = await self.execution_repo.get_strategy_executions(strategy_id, limit=100)

        # 生成报告数据
        time_range = {
            "start_date": min(e.start_time for e in executions) if executions else datetime.now(),
            "end_date": datetime.now()
        }

        # 计算详细指标
        detailed_metrics = await self.calculate_performance_metrics(
            strategy_id,
            (time_range["end_date"] - time_range["start_date"]).days
        )

        # 分析交易
        trade_analysis = await self._analyze_trades(executions)

        # 风险分析
        risk_analysis = await self._analyze_risk(executions, strategy)

        # 生成推荐
        recommendations = await self._generate_recommendations(strategy, detailed_metrics)

        report = ExecutionReport(
            execution_id=f"report_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            strategy_id=strategy_id,
            report_type=report_type,
            generated_at=datetime.now(),
            time_range=time_range,
            summary={
                "total_executions": len(executions),
                "successful_executions": len([e for e in executions if e.status == ExecutionStatus.COMPLETED]),
                "total_return": detailed_metrics.total_return,
                "sharpe_ratio": detailed_metrics.sharpe_ratio,
                "max_drawdown": detailed_metrics.max_drawdown
            },
            detailed_metrics=detailed_metrics,
            trade_analysis=trade_analysis,
            risk_analysis=risk_analysis,
            recommendations=recommendations
        )

        return report

    # 私有方法
    async def _run_strategy_execution(
        self,
        execution: StrategyExecution,
        request: ExecutionRequest,
        background_tasks: Any
    ) -> None:
        """
        运行策略执行（后台任务）
        """
        try:
            # 更新状态为运行中
            execution.status = ExecutionStatus.RUNNING
            execution = await self.execution_repo.update(execution)

            # 获取策略数据
            strategy = await self.strategy_repo.get_by_id(execution.strategy_id)

            # 模拟策略执行（实际实现会更复杂）
            await self._simulate_strategy_execution(execution, strategy, request)

            # 更新状态为完成
            execution.status = ExecutionStatus.COMPLETED
            execution.end_time = datetime.now()
            execution = await self.execution_repo.update(execution)

            logger.info(f"策略执行完成: {execution.execution_id}")

        except Exception as e:
            # 处理执行错误
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            execution = await self.execution_repo.update(execution)

            logger.error(f"策略执行失败: {execution.execution_id}, 错误: {e}")

        finally:
            # 清理运行中的任务
            if execution.execution_id in self.running_executions:
                del self.running_executions[execution.execution_id]

    async def _simulate_strategy_execution(
        self,
        execution: StrategyExecution,
        strategy: Strategy,
        request: ExecutionRequest
    ) -> None:
        """
        模拟策略执行（简化实现）
        """
        # 生成一些模拟信号
        signals = []
        for i in range(10):  # 生成10个信号
            signal = StrategySignal(
                strategy_id=strategy.id,
                strategy_type=strategy.strategy_type,
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                strength=0.7 + (i * 0.03),
                confidence=0.6 + (i * 0.04),
                market_data={"price": 100 + i, "volume": 1000 + i * 100}
            )
            signals.append(signal)

        # 计算模拟性能
        performance = StrategyPerformance(
            strategy_id=strategy.id,
            total_return=0.15,
            annual_return=0.18,
            sharpe_ratio=1.2,
            max_drawdown=0.05,
            win_rate=0.6,
            profit_factor=1.5,
            total_trades=len(signals),
            profit_trades=int(len(signals) * 0.6)
        )

        # 更新执行记录
        execution.signals = signals
        execution.performance = performance

        # 保存到数据库
        await self.execution_repo.update(execution)

    async def _estimate_execution_time(
        self,
        strategy: Strategy,
        request: ExecutionRequest
    ) -> Optional[datetime]:
        """
        估算执行完成时间
        """
        # 基于策略类型和历史数据估算
        base_time = 300  # 5分钟基础时间

        if request.execution_mode == "backtest":
            # 回测可能需要更长时间
            base_time *= 3

        return datetime.now() + timedelta(seconds=base_time)

    async def _calculate_execution_progress(self, execution: StrategyExecution) -> float:
        """
        计算执行进度
        """
        if execution.status == ExecutionStatus.COMPLETED:
            return 1.0
        elif execution.status == ExecutionStatus.FAILED:
            return 0.0
        elif execution.status == ExecutionStatus.PENDING:
            return 0.0
        else:
            # 基于时间和信号数量计算进度
            elapsed = (datetime.now() - execution.start_time).total_seconds()
            progress = min(elapsed / self.config.default_execution_timeout, 0.95)
            return progress

    async def _get_current_execution_step(self, execution: StrategyExecution) -> str:
        """
        获取当前执行步骤
        """
        if execution.status == ExecutionStatus.PENDING:
            return "等待开始"
        elif execution.status == ExecutionStatus.RUNNING:
            return "正在执行"
        elif execution.status == ExecutionStatus.COMPLETED:
            return "执行完成"
        elif execution.status == ExecutionStatus.FAILED:
            return "执行失败"
        else:
            return "未知状态"

    async def _get_execution_performance_summary(self, execution: StrategyExecution) -> Optional[Dict[str, float]]:
        """
        获取执行性能摘要
        """
        if execution.performance:
            return {
                "total_return": execution.performance.total_return,
                "sharpe_ratio": execution.performance.sharpe_ratio,
                "win_rate": execution.performance.win_rate
            }
        return None

    async def _stop_specific_execution(self, execution_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """停止指定执行"""
        # 检查执行是否存在
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"执行不存在: {execution_id}")

        # 权限检查
        if user_id:
            strategy = await self.strategy_repo.get_by_id(execution.strategy_id)
            if strategy.user_id != user_id:
                raise PermissionError(f"无权限停止执行: {execution_id}")

        # 取消任务
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            del self.running_executions[execution_id]

        # 更新状态
        execution.status = ExecutionStatus.CANCELLED
        execution.end_time = datetime.now()
        await self.execution_repo.update(execution)

        return {
            "execution_id": execution_id,
            "success": True,
            "message": "执行已停止"
        }

    async def _stop_all_strategy_executions(self, strategy_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """停止策略的所有执行"""
        # 获取策略的所有运行中执行
        running_executions = await self.execution_repo.get_running_executions(strategy_id)

        stopped_count = 0
        for execution in running_executions:
            try:
                await self._stop_specific_execution(execution.execution_id, user_id)
                stopped_count += 1
            except Exception as e:
                logger.error(f"停止执行失败: {execution.execution_id}, 错误: {e}")

        return {
            "strategy_id": strategy_id,
            "success": True,
            "stopped_count": stopped_count,
            "message": f"已停止 {stopped_count} 个执行"
        }

    async def _calculate_performance_from_executions(
        self,
        executions: List[StrategyExecution],
        time_range: int
    ) -> PerformanceMetrics:
        """
        从执行记录计算性能指标
        """
        if not executions:
            return PerformanceMetrics(strategy_id="", last_updated=datetime.now())

        # 聚合所有性能数据
        total_return = sum(e.performance.total_return for e in executions if e.performance)
        total_trades = sum(e.performance.total_trades for e in executions if e.performance)
        profit_trades = sum(e.performance.profit_trades for e in executions if e.performance)

        # 计算平均值
        avg_return = total_return / len(executions) if executions else 0
        annual_return = avg_return * (365 / time_range) if time_range > 0 else 0
        win_rate = profit_trades / total_trades if total_trades > 0 else 0

        return PerformanceMetrics(
            strategy_id=executions[0].strategy_id,
            total_return=avg_return,
            annual_return=annual_return,
            sharpe_ratio=1.2,  # 简化值
            max_drawdown=0.05,  # 简化值
            win_rate=win_rate,
            profit_factor=1.5,  # 简化值
            total_trades=total_trades,
            profit_trades=profit_trades,
            avg_profit=0.02,  # 简化值
            avg_loss=-0.01,  # 简化值
            last_updated=datetime.now()
        )

    async def _analyze_trades(self, executions: List[StrategyExecution]) -> Dict[str, Any]:
        """分析交易"""
        # 简化实现
        return {
            "total_trades": sum(len(e.signals) for e in executions),
            "buy_signals": len([s for e in executions for s in e.signals if s.signal_type == SignalType.BUY]),
            "sell_signals": len([s for e in executions for s in e.signals if s.signal_type == SignalType.SELL]),
            "avg_signal_strength": sum(s.strength for e in executions for s in e.signals) / sum(len(e.signals) for e in executions) if executions and any(e.signals for e in executions) else 0
        }

    async def _analyze_risk(self, executions: List[StrategyExecution], strategy: Strategy) -> Dict[str, Any]:
        """分析风险"""
        return {
            "max_drawdown": 0.05,
            "volatility": 0.15,
            "var_95": 0.02,
            "risk_level": strategy.risk_level.value
        }

    async def _generate_recommendations(
        self,
        strategy: Strategy,
        metrics: PerformanceMetrics
    ) -> List[str]:
        """生成推荐"""
        recommendations = []

        if metrics.sharpe_ratio < 1.0:
            recommendations.append("建议优化策略参数以提高风险调整后收益")

        if metrics.max_drawdown > 0.1:
            recommendations.append("建议降低仓位或设置更严格的止损")

        if metrics.win_rate < 0.5:
            recommendations.append("建议调整信号生成阈值")

        return recommendations