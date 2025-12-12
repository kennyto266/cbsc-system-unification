"""
策略倉庫測試
Strategy Repository Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from ..repositories.strategy_repository import StrategyRepository
from ..models import (
    Strategy, StrategySignal, StrategyPerformance, StrategyExecution,
    StrategyType, StrategyStatus, RiskLevel, SignalType, ExecutionStatus
)


class TestStrategyRepository:
    """策略倉庫測試類"""

    @pytest.fixture
    def repository(self):
        """創建策略倉庫fixture"""
        return StrategyRepository()

    @pytest.fixture
    def sample_strategy(self):
        """示例策略"""
        return Strategy(
            id="test_strategy_001",
            name="測試策略",
            description="測試用策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={"rsi_period": 14},
            status=StrategyStatus.INACTIVE,
            is_active=False,
            user_id=1,
            risk_level=RiskLevel.MEDIUM
        )

    @pytest.fixture
    def sample_signal(self):
        """示例信號"""
        return StrategySignal(
            signal_id="test_signal_001",
            strategy_id="test_strategy_001",
            strategy_type=StrategyType.DIRECT_RSI,
            signal_type=SignalType.BUY,
            confidence=0.8,
            strength=0.9
        )

    @pytest.fixture
    def sample_performance(self):
        """示例性能"""
        return StrategyPerformance(
            strategy_id="test_strategy_001",
            total_return=0.15,
            sharpe_ratio=1.2,
            win_rate=0.6
        )

    @pytest.mark.asyncio
    async def test_create_strategy(self, repository, sample_strategy):
        """測試創建策略"""
        result = await repository.create(sample_strategy)

        assert result is not None
        assert result.id == sample_strategy.id
        assert result.name == "測試策略"

    @pytest.mark.asyncio
    async def test_create_duplicate_strategy(self, repository, sample_strategy):
        """測試創建重複策略"""
        # 第一次創建
        await repository.create(sample_strategy)

        # 第二次創建應該失敗
        with pytest.raises(ValueError, match="策略ID已存在"):
            await repository.create(sample_strategy)

    @pytest.mark.asyncio
    async def test_get_strategy_by_id(self, repository, sample_strategy):
        """測試根據ID獲取策略"""
        # 創建策略
        created = await repository.create(sample_strategy)

        # 獲取策略
        found = await repository.get_by_id(sample_strategy.id)

        assert found is not None
        assert found.id == sample_strategy.id
        assert found.name == "測試策略"

    @pytest.mark.asyncio
    async def test_get_nonexistent_strategy(self, repository):
        """測試獲取不存在的策略"""
        result = await repository.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_strategy(self, repository, sample_strategy):
        """測試更新策略"""
        # 創建策略
        await repository.create(sample_strategy)

        # 更新策略
        sample_strategy.name = "更新後的策略"
        sample_strategy.description = "更新後的描述"

        updated = await repository.update(sample_strategy)

        assert updated.name == "更新後的策略"
        assert updated.description == "更新後的描述"
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_nonexistent_strategy(self, repository, sample_strategy):
        """測試更新不存在的策略"""
        with pytest.raises(ValueError, match="策略不存在"):
            await repository.update(sample_strategy)

    @pytest.mark.asyncio
    async def test_delete_strategy(self, repository, sample_strategy):
        """測試刪除策略"""
        # 創建策略
        await repository.create(sample_strategy)

        # 刪除策略
        result = await repository.delete(sample_strategy.id)

        assert result is True

        # 驗證已刪除
        found = await repository.get_by_id(sample_strategy.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_strategy(self, repository):
        """測試刪除不存在的策略"""
        result = await repository.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_strategies(self, repository):
        """測試獲取策略列表"""
        # 創建多個策略
        strategies = [
            Strategy(
                id=f"strategy_{i}",
                name=f"策略{i}",
                description=f"測試策略{i}",
                strategy_type=StrategyType.DIRECT_RSI,
                status=StrategyStatus.INACTIVE,
                is_active=i % 2 == 0,
                user_id=1,
                risk_level=RiskLevel.MEDIUM
            )
            for i in range(5)
        ]

        for strategy in strategies:
            await repository.create(strategy)

        # 獲取列表
        result, total = await repository.list_strategies(page=1, page_size=3)

        assert len(result) == 3
        assert total == 5
        assert all(s.user_id == 1 for s in result)

    @pytest.mark.asyncio
    async def test_list_strategies_with_filters(self, repository):
        """測試帶過濾條件的策略列表"""
        # 創建不同類型的策略
        strategies = [
            Strategy(
                id=f"strategy_{i}",
                name=f"策略{i}",
                description=f"測試策略{i}",
                strategy_type=StrategyType.DIRECT_RSI if i % 2 == 0 else StrategyType.AI_ML,
                status=StrategyStatus.ACTIVE if i % 2 == 0 else StrategyStatus.INACTIVE,
                is_active=True,
                user_id=1,
                risk_level=RiskLevel.MEDIUM
            )
            for i in range(4)
        ]

        for strategy in strategies:
            await repository.create(strategy)

        # 測試類型過濾
        result, total = await repository.list_strategies(
            filters={"strategy_type": "direct_rsi"}
        )
        assert len(result) == 2
        assert all(s.strategy_type.value == "direct_rsi" for s in result)

        # 測試狀態過濾
        result, total = await repository.list_strategies(
            filters={"status": "active"}
        )
        assert len(result) == 2
        assert all(s.status.value == "active" for s in result)

    @pytest.mark.asyncio
    async def test_add_signal(self, repository, sample_signal):
        """測試添加信號"""
        result = await repository.add_signal(sample_signal)

        assert result is not None
        assert result.signal_id == sample_signal.signal_id
        assert result.strategy_id == sample_signal.strategy_id

    @pytest.mark.asyncio
    async def test_get_recent_signals(self, repository):
        """測試獲取最近信號"""
        strategy_id = "test_strategy_001"

        # 添加多個信號
        for i in range(5):
            signal = StrategySignal(
                signal_id=f"signal_{i}",
                strategy_id=strategy_id,
                strategy_type=StrategyType.DIRECT_RSI,
                signal_type=SignalType.BUY,
                confidence=0.8,
                strength=0.9,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            await repository.add_signal(signal)

        # 獲取最近信號
        signals = await repository.get_recent_signals(strategy_id, limit=3)

        assert len(signals) == 3
        # 應該按時間倒序排列
        assert signals[0].timestamp >= signals[1].timestamp

    @pytest.mark.asyncio
    async def test_save_performance(self, repository, sample_performance):
        """測試保存性能"""
        result = await repository.save_performance(sample_performance)

        assert result is not None
        assert result.strategy_id == sample_performance.strategy_id
        assert result.total_return == 0.15

    @pytest.mark.asyncio
    async def test_get_performance(self, repository, sample_performance):
        """測試獲取性能"""
        # 保存性能
        await repository.save_performance(sample_performance)

        # 獲取性能
        result = await repository.get_performance(sample_performance.strategy_id)

        assert result is not None
        assert result.strategy_id == sample_performance.strategy_id
        assert result.total_return == 0.15

    @pytest.mark.asyncio
    async def test_update_performance_metrics(self, repository, sample_performance):
        """測試更新性能指標"""
        strategy_id = sample_performance.strategy_id

        # 更新性能指標
        metrics = {
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
            "win_rate": 0.7
        }

        result = await repository.update_performance_metrics(strategy_id, metrics)

        assert result is True

        # 驗證更新
        performance = await repository.get_performance(strategy_id)
        assert performance.total_return == 0.25
        assert performance.sharpe_ratio == 1.5
        assert performance.win_rate == 0.7

    @pytest.mark.asyncio
    async def test_save_execution(self, repository):
        """測試保存執行"""
        execution = StrategyExecution(
            execution_id="exec_001",
            strategy_id="test_strategy_001",
            status=ExecutionStatus.RUNNING
        )

        result = await repository.save_execution(execution)

        assert result is not None
        assert result.execution_id == execution.execution_id
        assert result.status == ExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_get_running_executions(self, repository):
        """測試獲取運行中的執行"""
        strategy_id = "test_strategy_001"

        # 添加運行中的執行
        running_exec = StrategyExecution(
            execution_id="exec_running",
            strategy_id=strategy_id,
            status=ExecutionStatus.RUNNING
        )
        await repository.save_execution(running_exec)

        # 添加已完成的執行
        completed_exec = StrategyExecution(
            execution_id="exec_completed",
            strategy_id=strategy_id,
            status=ExecutionStatus.COMPLETED
        )
        await repository.save_execution(completed_exec)

        # 獲取運行中的執行
        running_executions = await repository.get_running_executions(strategy_id)

        assert len(running_executions) == 1
        assert running_executions[0].execution_id == "exec_running"
        assert running_executions[0].status == ExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_is_running(self, repository):
        """測試檢查是否正在運行"""
        strategy_id = "test_strategy_001"

        # 初始狀態應該不是運行中
        assert not await repository.is_running(strategy_id)

        # 添加運行中的執行
        execution = StrategyExecution(
            execution_id="exec_001",
            strategy_id=strategy_id,
            status=ExecutionStatus.RUNNING
        )
        await repository.save_execution(execution)

        # 現在應該是運行中
        assert await repository.is_running(strategy_id)

    @pytest.mark.asyncio
    async def test_get_strategy_statistics(self, repository):
        """測試獲取策略統計"""
        # 創建不同類型的策略
        strategies = [
            Strategy(
                id=f"strategy_{i}",
                name=f"策略{i}",
                description=f"測試策略{i}",
                strategy_type=StrategyType.DIRECT_RSI if i < 2 else StrategyType.AI_ML,
                status=StrategyStatus.ACTIVE if i < 3 else StrategyStatus.INACTIVE,
                is_active=i % 2 == 0,
                user_id=1,
                risk_level=RiskLevel.HIGH if i == 0 else RiskLevel.MEDIUM
            )
            for i in range(5)
        ]

        for strategy in strategies:
            await repository.create(strategy)

        # 獲取統計
        stats = await repository.get_strategy_statistics(user_id=1)

        assert stats["total_strategies"] == 6  # 5 + 1 sample data
        assert stats["active_strategies"] == 3  # is_active=True
        assert stats["inactive_strategies"] == 3
        assert "strategies_by_type" in stats
        assert "strategies_by_status" in stats
        assert "strategies_by_risk" in stats

    @pytest.mark.asyncio
    async def test_get_signal_statistics(self, repository):
        """測試獲取信號統計"""
        strategy_id = "test_strategy_001"

        # 添加不同類型的信號
        signals = [
            StrategySignal(
                signal_id=f"signal_{i}",
                strategy_id=strategy_id,
                strategy_type=StrategyType.DIRECT_RSI,
                signal_type=SignalType.BUY if i < 2 else SignalType.SELL,
                confidence=0.8 + i * 0.05,
                strength=0.7 + i * 0.1
            )
            for i in range(4)
        ]

        for signal in signals:
            await repository.add_signal(signal)

        # 獲取統計
        stats = await repository.get_signal_statistics(strategy_id, days=30)

        assert stats["total_signals"] == 4
        assert stats["buy_signals"] == 2
        assert stats["sell_signals"] == 2
        assert stats["avg_confidence"] > 0
        assert stats["avg_strength"] > 0


if __name__ == "__main__":
    # 運行測試
    asyncio.run(pytest.main([__file__, "-v"]))