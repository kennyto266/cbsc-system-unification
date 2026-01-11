"""
策略数据访问层
Strategy Data Access Layer

职责：
- 策略数据的CRUD操作
- 数据库查询封装
- 数据持久化管理
"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

from ..models import (
    Strategy, StrategySignal, StrategyPerformance, StrategyExecution,
    StrategyType, StrategyStatus, RiskLevel, SignalType
)

logger = logging.getLogger(__name__)

def get_enum_value(enum_field: Union[str, Enum]) -> str:
    """
    获取枚举值的字符串表示
    处理可能已经是字符串的情况
    """
    if hasattr(enum_field, 'value'):
        return enum_field.value
    return enum_field


class StrategyRepository:
    """策略数据访问层"""

    def __init__(self):
        """
        初始化策略仓库
        注意：这里应该使用真正的数据库连接池
        简化实现使用内存存储
        """
        self._strategies: Dict[str, Strategy] = {}
        self._signals: List[StrategySignal] = []
        self._performances: Dict[str, StrategyPerformance] = {}
        self._executions: Dict[str, StrategyExecution] = {}
        self._running_executions: Dict[str, List[str]] = {}

        # 初始化一些示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        # 创建示例策略
        sample_strategy = Strategy(
            id="sample_strategy_001",
            name="RSI策略示例",
            description="基于RSI指标的交易策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "stop_loss": 0.05,
                "take_profit": 0.1
            },
            status=StrategyStatus.INACTIVE,
            is_active=False,
            user_id=1,
            risk_level=RiskLevel.MEDIUM,
            created_at=datetime.now() - timedelta(days=7)
        )
        self._strategies[sample_strategy.id] = sample_strategy

    # ============================================================================
    # 策略CRUD操作
    # ============================================================================

    async def create(self, strategy: Strategy) -> Strategy:
        """
        创建策略
        """
        # 检查ID是否已存在
        if strategy.id in self._strategies:
            raise ValueError(f"策略ID已存在: {strategy.id}")

        # 保存策略
        self._strategies[strategy.id] = strategy

        logger.info(f"创建策略: {strategy.id}")
        return strategy

    async def get_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """
        根据ID获取策略
        """
        return self._strategies.get(strategy_id)

    async def update(self, strategy: Strategy) -> Strategy:
        """
        更新策略
        """
        if strategy.id not in self._strategies:
            raise ValueError(f"策略不存在: {strategy.id}")

        # 更新时间戳
        strategy.updated_at = datetime.now()

        # 保存更新
        self._strategies[strategy.id] = strategy

        logger.info(f"更新策略: {strategy.id}")
        return strategy

    async def delete(self, strategy_id: str) -> bool:
        """
        删除策略
        """
        if strategy_id not in self._strategies:
            return False

        # 删除策略
        del self._strategies[strategy_id]

        # 删除相关数据
        self._signals = [s for s in self._signals if s.strategy_id != strategy_id]
        if strategy_id in self._performances:
            del self._performances[strategy_id]
        if strategy_id in self._executions:
            del self._executions[strategy_id]
        if strategy_id in self._running_executions:
            del self._running_executions[strategy_id]

        logger.info(f"删除策略: {strategy_id}")
        return True

    async def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> tuple[List[Strategy], int]:
        """
        获取策略列表
        """
        # 获取所有策略
        strategies = list(self._strategies.values())

        # 应用过滤条件
        if filters:
            if "strategy_type" in filters:
                strategies = [s for s in strategies if get_enum_value(s.strategy_type) == filters["strategy_type"]]
            if "status" in filters:
                strategies = [s for s in strategies if get_enum_value(s.status) == filters["status"]]
            if "is_active" in filters:
                strategies = [s for s in strategies if s.is_active == filters["is_active"]]

        # 按用户过滤
        if user_id is not None:
            strategies = [s for s in strategies if s.user_id == user_id]

        # 排序（按创建时间倒序）
        strategies.sort(key=lambda x: x.created_at, reverse=True)

        # 分页
        total_count = len(strategies)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_strategies = strategies[start_index:end_index]

        return paginated_strategies, total_count

    async def get_user_strategies(self, user_id: int) -> List[Strategy]:
        """
        获取用户的所有策略
        """
        return [s for s in self._strategies.values() if s.user_id == user_id]

    async def name_exists(self, name: str, user_id: int) -> bool:
        """
        检查策略名称是否已存在
        """
        for strategy in self._strategies.values():
            if strategy.user_id == user_id and strategy.name == name:
                return True
        return False

    async def is_running(self, strategy_id: str) -> bool:
        """
        检查策略是否正在运行
        """
        running_executions = self._running_executions.get(strategy_id, [])
        return len(running_executions) > 0

    async def get_strategy_parameters(self, strategy_id: str) -> Dict[str, Any]:
        """
        获取策略参数
        """
        strategy = await self.get_by_id(strategy_id)
        if not strategy:
            return {}
        return strategy.parameters

    async def get_execution_history(
        self,
        strategy_id: str,
        limit: int = 10
    ) -> List[StrategyExecution]:
        """
        获取策略执行历史
        """
        executions = self._executions.get(strategy_id, [])

        # 按时间倒序排序
        executions.sort(key=lambda x: x.start_time, reverse=True)

        return executions[:limit]

    # ============================================================================
    # 信号相关操作
    # ============================================================================

    async def add_signal(self, signal: StrategySignal) -> StrategySignal:
        """
        添加策略信号
        """
        self._signals.append(signal)
        logger.debug(f"添加信号: {signal.signal_id}")
        return signal

    async def get_recent_signals(
        self,
        strategy_id: str,
        limit: int = 10
    ) -> List[StrategySignal]:
        """
        获取最近的信号
        """
        strategy_signals = [
            s for s in self._signals
            if s.strategy_id == strategy_id
        ]

        # 按时间倒序排序
        strategy_signals.sort(key=lambda x: x.timestamp, reverse=True)

        return strategy_signals[:limit]

    async def get_recent_signals_by_strategies(
        self,
        strategy_ids: List[str],
        limit: int = 10
    ) -> List[StrategySignal]:
        """
        获取多个策略的最近信号
        """
        filtered_signals = [
            s for s in self._signals
            if s.strategy_id in strategy_ids
        ]

        # 按时间倒序排序
        filtered_signals.sort(key=lambda x: x.timestamp, reverse=True)

        return filtered_signals[:limit]

    async def get_latest_signal(self, strategy_id: str) -> Optional[StrategySignal]:
        """
        获取最新信号
        """
        signals = await self.get_recent_signals(strategy_id, 1)
        return signals[0] if signals else None

    # ============================================================================
    # 性能相关操作
    # ============================================================================

    async def save_performance(
        self,
        performance: StrategyPerformance
    ) -> StrategyPerformance:
        """
        保存策略性能
        """
        self._performances[performance.strategy_id] = performance
        logger.debug(f"保存性能数据: {performance.strategy_id}")
        return performance

    async def get_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """
        获取策略性能
        """
        return self._performances.get(strategy_id)

    async def update_performance_metrics(
        self,
        strategy_id: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        更新性能指标
        """
        performance = await self.get_performance(strategy_id)
        if not performance:
            # 创建新的性能记录
            performance = StrategyPerformance(
                strategy_id=strategy_id,
                **metrics
            )
        else:
            # 更新现有记录
            for key, value in metrics.items():
                if hasattr(performance, key):
                    setattr(performance, key, value)
            performance.last_updated = datetime.now()

        await self.save_performance(performance)
        return True

    # ============================================================================
    # 执行相关操作
    # ============================================================================

    async def save_execution(self, execution: StrategyExecution) -> StrategyExecution:
        """
        保存策略执行
        """
        self._executions[execution.execution_id] = execution

        # 处理status值（可能是字符串或枚举）
        status_value = get_enum_value(execution.status)

        # 更新运行中的执行列表
        if status_value == "running":
            if execution.strategy_id not in self._running_executions:
                self._running_executions[execution.strategy_id] = []
            self._running_executions[execution.strategy_id].append(execution.execution_id)
        elif status_value in ["completed", "failed", "cancelled"]:
            # 从运行列表中移除
            if execution.strategy_id in self._running_executions:
                if execution.execution_id in self._running_executions[execution.strategy_id]:
                    self._running_executions[execution.strategy_id].remove(execution.execution_id)

        logger.debug(f"保存执行: {execution.execution_id}")
        return execution

    async def get_execution(self, execution_id: str) -> Optional[StrategyExecution]:
        """
        获取策略执行
        """
        return self._executions.get(execution_id)

    async def get_running_executions(self, strategy_id: str) -> List[StrategyExecution]:
        """
        获取运行中的执行
        """
        running_execution_ids = self._running_executions.get(strategy_id, [])
        return [
            self._executions[eid] for eid in running_execution_ids
            if eid in self._executions
        ]

    async def get_strategy_executions(
        self,
        strategy_id: str,
        limit: int = 50
    ) -> List[StrategyExecution]:
        """
        获取策略执行历史
        """
        executions = [
            e for e in self._executions.values()
            if e.strategy_id == strategy_id
        ]

        # 按时间倒序排序
        executions.sort(key=lambda x: x.start_time, reverse=True)

        return executions[:limit]

    async def get_executions(
        self,
        strategy_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> tuple[List[StrategyExecution], int]:
        """
        获取执行列表
        """
        executions = list(self._executions.values())

        # 过滤
        if strategy_id:
            executions = [e for e in executions if e.strategy_id == strategy_id]
        if status:
            executions = [e for e in executions if get_enum_value(e.status) == status]

        # 排序
        executions.sort(key=lambda x: x.start_time, reverse=True)

        # 分页
        total_count = len(executions)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_executions = executions[start_index:end_index]

        return paginated_executions, total_count

    async def get_executions_by_date_range(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[StrategyExecution]:
        """
        获取指定日期范围的执行
        """
        executions = [
            e for e in self._executions.values()
            if e.strategy_id == strategy_id
            and start_date <= e.start_time <= end_date
        ]

        executions.sort(key=lambda x: x.start_time, reverse=True)
        return executions

    def generate_id(self) -> str:
        """
        生成唯一ID
        """
        import uuid
        return str(uuid.uuid4())

    # ============================================================================
    # 统计和分析
    # ============================================================================

    async def get_strategy_statistics(
        self,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取策略统计信息
        """
        strategies = list(self._strategies.values())

        if user_id is not None:
            strategies = [s for s in strategies if s.user_id == user_id]

        total_count = len(strategies)
        active_count = len([s for s in strategies if s.is_active])

        # 按类型统计
        type_stats = {}
        for strategy in strategies:
            type_name = get_enum_value(strategy.strategy_type)
            type_stats[type_name] = type_stats.get(type_name, 0) + 1

        # 按状态统计
        status_stats = {}
        for strategy in strategies:
            status_name = get_enum_value(strategy.status)
            status_stats[status_name] = status_stats.get(status_name, 0) + 1

        # 按风险等级统计
        risk_stats = {}
        for strategy in strategies:
            risk_name = get_enum_value(strategy.risk_level)
            risk_stats[risk_name] = risk_stats.get(risk_name, 0) + 1

        return {
            "total_strategies": total_count,
            "active_strategies": active_count,
            "inactive_strategies": total_count - active_count,
            "strategies_by_type": type_stats,
            "strategies_by_status": status_stats,
            "strategies_by_risk": risk_stats
        }

    async def get_signal_statistics(
        self,
        strategy_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取信号统计信息
        """
        start_date = datetime.now() - timedelta(days=days)
        signals = [
            s for s in self._signals
            if s.strategy_id == strategy_id and s.timestamp >= start_date
        ]

        total_signals = len(signals)
        buy_signals = len([s for s in signals if s.signal_type == SignalType.BUY])
        sell_signals = len([s for s in signals if s.signal_type == SignalType.SELL])
        hold_signals = len([s for s in signals if s.signal_type == SignalType.HOLD])

        avg_confidence = sum(s.confidence for s in signals) / total_signals if total_signals > 0 else 0
        avg_strength = sum(s.strength for s in signals) / total_signals if total_signals > 0 else 0

        return {
            "total_signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "avg_confidence": avg_confidence,
            "avg_strength": avg_strength,
            "period_days": days
        }

    # ============================================================================
    # 批量操作
    # ============================================================================

    async def batch_update(
        self,
        strategy_ids: List[str],
        update_data: Dict[str, Any]
    ) -> int:
        """
        批量更新策略
        """
        updated_count = 0

        for strategy_id in strategy_ids:
            strategy = await self.get_by_id(strategy_id)
            if strategy:
                for key, value in update_data.items():
                    if hasattr(strategy, key):
                        setattr(strategy, key, value)
                strategy.updated_at = datetime.now()
                await self.update(strategy)
                updated_count += 1

        return updated_count

    async def batch_delete(self, strategy_ids: List[str]) -> int:
        """
        批量删除策略
        """
        deleted_count = 0

        for strategy_id in strategy_ids:
            if await self.delete(strategy_id):
                deleted_count += 1

        return deleted_count