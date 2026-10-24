"""
执行数据访问层
Execution Data Access Layer

职责：
- 策略执行数据管理
- 执行状态跟踪
- 执行历史记录
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import uuid

from ..models import (
    StrategyExecution, StrategyPerformance, StrategySignal,
    ExecutionStatus, SignalType
)

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """执行数据访问层"""

    def __init__(self):
        """
        初始化执行仓库
        简化实现使用内存存储
        """
        self._executions: Dict[str, StrategyExecution] = {}
        self._execution_logs: Dict[str, List[Dict[str, Any]]] = {}

    # ============================================================================
    # 执行管理
    # ============================================================================

    async def create(self, execution: StrategyExecution) -> StrategyExecution:
        """
        创建执行记录
        """
        # 确保执行ID唯一
        if execution.execution_id in self._executions:
            raise ValueError(f"执行ID已存在: {execution.execution_id}")

        # 设置默认值
        if not execution.start_time:
            execution.start_time = datetime.now()

        # 保存执行记录
        self._executions[execution.execution_id] = execution

        # 初始化日志
        self._execution_logs[execution.execution_id] = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "执行创建",
                "details": {"execution_id": execution.execution_id}
            }
        ]

        logger.info(f"创建执行: {execution.execution_id}")
        return execution

    async def get_by_id(self, execution_id: str) -> Optional[StrategyExecution]:
        """
        根据ID获取执行
        """
        return self._executions.get(execution_id)

    async def update(self, execution: StrategyExecution) -> StrategyExecution:
        """
        更新执行记录
        """
        if execution.execution_id not in self._executions:
            raise ValueError(f"执行不存在: {execution.execution_id}")

        # 保存更新
        self._executions[execution.execution_id] = execution

        # 记录更新日志
        await self.log_execution_event(
            execution.execution_id,
            "INFO",
            "执行更新",
            {"status": execution.status.value}
        )

        logger.debug(f"更新执行: {execution.execution_id}")
        return execution

    async def delete(self, execution_id: str) -> bool:
        """
        删除执行记录
        """
        if execution_id not in self._executions:
            return False

        # 删除执行记录
        del self._executions[execution_id]
        del self._execution_logs[execution_id]

        logger.info(f"删除执行: {execution_id}")
        return True

    # ============================================================================
    # 执行查询
    # ============================================================================

    async def list_executions(
        self,
        strategy_id: Optional[str] = None,
        status: Optional[str] = None,
        execution_mode: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[StrategyExecution], int]:
        """
        获取执行列表
        """
        executions = list(self._executions.values())

        # 过滤
        if strategy_id:
            executions = [e for e in executions if e.strategy_id == strategy_id]
        if status:
            executions = [e for e in executions if e.status.value == status]
        if execution_mode:
            executions = [e for e in executions if e.execution_mode == execution_mode]

        # 排序（按开始时间倒序）
        executions.sort(key=lambda x: x.start_time, reverse=True)

        # 分页
        total_count = len(executions)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_executions = executions[start_index:end_index]

        return paginated_executions, total_count

    async def get_strategy_executions(
        self,
        strategy_id: str,
        limit: int = 50
    ) -> List[StrategyExecution]:
        """
        获取策略的所有执行
        """
        executions = [
            e for e in self._executions.values()
            if e.strategy_id == strategy_id
        ]

        # 排序（按开始时间倒序）
        executions.sort(key=lambda x: x.start_time, reverse=True)

        return executions[:limit]

    async def get_running_executions(self, strategy_id: str) -> List[StrategyExecution]:
        """
        获取运行中的执行
        """
        return [
            e for e in self._executions.values()
            if e.strategy_id == strategy_id and e.status == ExecutionStatus.RUNNING
        ]

    async def get_executions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> List[StrategyExecution]:
        """
        获取指定日期范围的执行
        """
        executions = [
            e for e in self._executions.values()
            if start_date <= e.start_time <= end_date
        ]

        # 如果指定了用户ID，需要进一步过滤
        # 这里需要策略仓库支持，简化实现

        # 排序
        executions.sort(key=lambda x: x.start_time, reverse=True)

        return executions

    async def get_recent_executions(
        self,
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[StrategyExecution]:
        """
        获取最近的执行
        """
        executions = list(self._executions.values())

        # 如果指定了用户ID，需要进一步过滤
        # 简化实现

        # 排序（按开始时间倒序）
        executions.sort(key=lambda x: x.start_time, reverse=True)

        return executions[:limit]

    # ============================================================================
    # 执行状态管理
    # ============================================================================

    async def update_status(
        self,
        execution_id: str,
        new_status: ExecutionStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新执行状态
        """
        execution = await self.get_by_id(execution_id)
        if not execution:
            return False

        old_status = execution.status
        execution.status = new_status

        if new_status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            execution.end_time = datetime.now()

        if error_message:
            execution.error_message = error_message

        await self.update(execution)

        # 记录状态变更
        await self.log_execution_event(
            execution_id,
            "INFO",
            f"状态变更: {old_status.value} -> {new_status.value}",
            {"error_message": error_message}
        )

        return True

    async def set_progress(
        self,
        execution_id: str,
        progress: float,
        current_step: Optional[str] = None
    ) -> bool:
        """
        设置执行进度
        """
        execution = await self.get_by_id(execution_id)
        if not execution:
            return False

        # 更新执行元数据
        execution.execution_metadata["progress"] = progress
        if current_step:
            execution.execution_metadata["current_step"] = current_step

        await self.update(execution)

        return True

    async def add_signal(
        self,
        execution_id: str,
        signal: StrategySignal
    ) -> bool:
        """
        添加执行信号
        """
        execution = await self.get_by_id(execution_id)
        if not execution:
            return False

        execution.signals.append(signal)

        await self.update(execution)

        # 记录信号生成
        await self.log_execution_event(
            execution_id,
            "INFO",
            f"生成信号: {signal.signal_type.value}",
            {
                "signal_id": signal.signal_id,
                "strength": signal.strength,
                "confidence": signal.confidence
            }
        )

        return True

    async def update_performance(
        self,
        execution_id: str,
        performance: StrategyPerformance
    ) -> bool:
        """
        更新执行性能
        """
        execution = await self.get_by_id(execution_id)
        if not execution:
            return False

        execution.performance = performance

        await self.update(execution)

        # 记录性能更新
        await self.log_execution_event(
            execution_id,
            "INFO",
            "性能数据更新",
            {
                "total_return": performance.total_return,
                "sharpe_ratio": performance.sharpe_ratio,
                "win_rate": performance.win_rate
            }
        )

        return True

    # ============================================================================
    # 执行日志
    # ============================================================================

    async def log_execution_event(
        self,
        execution_id: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录执行事件
        """
        if execution_id not in self._execution_logs:
            self._execution_logs[execution_id] = []

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }

        self._execution_logs[execution_id].append(log_entry)

        # 限制日志条数，避免内存泄漏
        if len(self._execution_logs[execution_id]) > 1000:
            self._execution_logs[execution_id] = self._execution_logs[execution_id][-500:]

        logger.debug(f"执行日志 [{execution_id}]: {level} - {message}")

    async def get_execution_logs(
        self,
        execution_id: str,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取执行日志
        """
        logs = self._execution_logs.get(execution_id, [])

        # 过滤日志级别
        if level:
            logs = [log for log in logs if log["level"] == level.upper()]

        # 返回最新的日志
        return logs[-limit:] if logs else []

    # ============================================================================
    # 执行统计
    # ============================================================================

    async def get_execution_statistics(
        self,
        strategy_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取执行统计信息
        """
        start_date = datetime.now() - timedelta(days=days)

        # 获取执行记录
        if strategy_id:
            executions = await self.get_strategy_executions(strategy_id, 1000)
        else:
            executions = await self.get_executions_by_date_range(start_date, datetime.now())

        # 过滤日期范围
        executions = [
            e for e in executions
            if e.start_time >= start_date
        ]

        total_executions = len(executions)
        completed_executions = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.FAILED])
        running_executions = len([e for e in executions if e.status == ExecutionStatus.RUNNING])

        # 计算平均执行时间
        execution_times = []
        for execution in executions:
            if execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                execution_times.append(duration)

        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        # 按模式统计
        backtest_executions = len([e for e in executions if e.execution_mode == "backtest"])
        realtime_executions = len([e for e in executions if e.execution_mode == "real_time"])

        # 按日期统计
        daily_stats = {}
        for execution in executions:
            date_key = execution.start_time.strftime("%Y-%m-%d")
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0
                }

            daily_stats[date_key]["total"] += 1
            if execution.status == ExecutionStatus.COMPLETED:
                daily_stats[date_key]["completed"] += 1
            elif execution.status == ExecutionStatus.FAILED:
                daily_stats[date_key]["failed"] += 1

        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "success_rate": completed_executions / total_executions if total_executions > 0 else 0,
            "avg_execution_time_seconds": avg_execution_time,
            "backtest_executions": backtest_executions,
            "realtime_executions": realtime_executions,
            "daily_statistics": daily_stats,
            "period_days": days
        }

    async def get_performance_summary(
        self,
        strategy_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取性能摘要
        """
        executions = await self.get_strategy_executions(strategy_id, 1000)

        # 过滤成功的执行
        successful_executions = [
            e for e in executions
            if e.status == ExecutionStatus.COMPLETED and e.performance
        ]

        if not successful_executions:
            return {
                "total_executions": len(executions),
                "successful_executions": 0,
                "avg_return": 0,
                "best_return": 0,
                "worst_return": 0,
                "avg_sharpe_ratio": 0
            }

        # 计算性能指标
        returns = [e.performance.total_return for e in successful_executions]
        sharpe_ratios = [e.performance.sharpe_ratio for e in successful_executions]

        return {
            "total_executions": len(executions),
            "successful_executions": len(successful_executions),
            "avg_return": sum(returns) / len(returns),
            "best_return": max(returns),
            "worst_return": min(returns),
            "avg_sharpe_ratio": sum(sharpe_ratios) / len(sharpe_ratios),
            "max_drawdown": min(e.performance.max_drawdown for e in successful_executions),
            "avg_win_rate": sum(e.performance.win_rate for e in successful_executions) / len(successful_executions)
        }

    # ============================================================================
    # 批量操作
    # ============================================================================

    async def cancel_all_running_executions(self, strategy_id: str) -> int:
        """
        取消所有运行中的执行
        """
        running_executions = await self.get_running_executions(strategy_id)
        cancelled_count = 0

        for execution in running_executions:
            if await self.update_status(execution.execution_id, ExecutionStatus.CANCELLED):
                cancelled_count += 1

        return cancelled_count

    async def cleanup_old_executions(self, days: int = 90) -> int:
        """
        清理旧的执行记录
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        old_executions = [
            e for e in self._executions.values()
            if e.start_time < cutoff_date and e.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
        ]

        deleted_count = 0
        for execution in old_executions:
            if await self.delete(execution.execution_id):
                deleted_count += 1

        logger.info(f"清理旧执行记录: {deleted_count} 条")
        return deleted_count

    def generate_id(self) -> str:
        """
        生成唯一ID
        """
        return str(uuid.uuid4())