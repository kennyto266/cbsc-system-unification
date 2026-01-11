"""
Unit Tests for Strategy Services
策略服務單元測試

測試所有服務的業務邏輯，確保正確性
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from .base_test_classes import ServiceTestCase, MockDataGenerator, TestAssertions


class TestBaseStrategyService(ServiceTestCase):
    """
    BaseStrategyService 測試
    """

    @pytest.mark.asyncio
    async def test_create_strategy_success(self, strategy_service):
        """測試成功創建策略"""
        # 準備測試數據
        strategy_data = MockDataGenerator.generate_strategy_data()
        user_id = 1

        # 執行測試
        result = await self.assert_service_response(
            strategy_service.create_strategy(strategy_data, user_id)
        )

        # 驗證結果
        assert result.name == strategy_data["name"]
        assert result.user_id == user_id
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_strategy_duplicate_name(self, strategy_service):
        """測試創建重複名稱的策略"""
        # 準備測試數據
        strategy_data = MockDataGenerator.generate_strategy_data()
        user_id = 1

        # 第一次創建
        await strategy_service.create_strategy(strategy_data, user_id)

        # 第二次創建相同名稱
        with pytest.raises(Exception) as exc_info:
            await strategy_service.create_strategy(strategy_data, user_id)

        assert "name already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_strategies_with_pagination(self, strategy_service):
        """測試帶分頁的策略列表"""
        # 創建多個策略
        user_id = 1
        strategies = []
        for i in range(25):
            strategy_data = MockDataGenerator.generate_strategy_data()
            strategy_data["name"] = f"Strategy_{i}"
            strategy = await strategy_service.create_strategy(strategy_data, user_id)
            strategies.append(strategy)

        # 測試分頁
        result = await strategy_service.list_strategies(
            user_id=user_id,
            page=1,
            page_size=10
        )

        assert len(result["items"]) == 10
        assert result["page"] == 1
        assert result["total"] == 25
        assert result["pages"] == 3

    @pytest.mark.asyncio
    async def test_update_strategy(self, strategy_service):
        """測試更新策略"""
        # 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        user_id = 1
        strategy = await strategy_service.create_strategy(strategy_data, user_id)

        # 更新策略
        update_data = {
            "name": "Updated Strategy Name",
            "description": "Updated description"
        }
        updated_strategy = await strategy_service.update_strategy(
            strategy.id, update_data, user_id
        )

        assert updated_strategy.name == update_data["name"]
        assert updated_strategy.description == update_data["description"]
        assert updated_strategy.updated_at > strategy.updated_at

    @pytest.mark.asyncio
    async def test_delete_strategy(self, strategy_service):
        """測試刪除策略"""
        # 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        user_id = 1
        strategy = await strategy_service.create_strategy(strategy_data, user_id)

        # 刪除策略
        await strategy_service.delete_strategy(strategy.id, user_id)

        # 驗證刪除
        with pytest.raises(Exception) as exc_info:
            await strategy_service.get_strategy(strategy.id, user_id)

        assert "not found" in str(exc_info.value).lower()


class TestExecutionService(ServiceTestCase):
    """
    ExecutionService 測試
    """

    @pytest.mark.asyncio
    async def test_create_execution(self, execution_service):
        """測試創建執行"""
        execution_request = {
            "strategy_id": "test_strategy_001",
            "execution_mode": "backtest",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc) + timedelta(days=1),
            "initial_capital": 100000
        }
        user_id = 1

        result = await self.assert_service_response(
            execution_service.create_execution(
                execution_request["strategy_id"], user_id, execution_request
            )
        )

        assert result.strategy_id == execution_request["strategy_id"]
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_stop_execution(self, execution_service):
        """測試停止執行"""
        # 創建執行
        execution_request = MockDataGenerator.generate_execution_data("strategy_001")
        user_id = 1
        execution = await execution_service.create_execution(
            execution_request["strategy_id"], user_id, execution_request
        )

        # 停止執行
        await execution_service.stop_execution(execution.id, user_id)

        # 驗證狀態
        updated_execution = await execution_service.get_execution(execution.id, user_id)
        assert updated_execution.status == "stopped"

    @pytest.mark.asyncio
    async def test_get_execution_history(self, execution_service):
        """測試獲取執行歷史"""
        strategy_id = "test_strategy_001"
        user_id = 1

        # 創建多個執行
        executions = []
        for i in range(5):
            execution_request = MockDataGenerator.generate_execution_data(strategy_id)
            execution = await execution_service.create_execution(strategy_id, user_id, execution_request)
            executions.append(execution)

        # 獲取執行歷史
        history = await execution_service.get_execution_history(strategy_id, user_id)

        assert len(history) >= 5
        assert all(e.strategy_id == strategy_id for e in history)


class TestPerformanceService(ServiceTestCase):
    """
    PerformanceService 測試
    """

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics(self, performance_service):
        """測試計算性能指標"""
        strategy_id = "test_strategy_001"
        user_id = 1

        # 模擬交易數據
        trades = MockDataGenerator.generate_trade_data(20)

        # Mock repository methods
        performance_service.execution_repo.get_strategy_executions = AsyncMock(
            return_value=[{"id": "exec_001"}]
        )
        performance_service.execution_repo.get_execution_trades = AsyncMock(
            return_value=[{
                "trade_id": f"trade_{i}",
                "timestamp": datetime.now(timezone.utc),
                "symbol": "TEST",
                "action": "SELL" if i % 2 == 1 else "BUY",
                "quantity": 100,
                "price": 100 + i,
                "value": (100 + i) * 100,
                "pnl": i if i % 2 == 1 else 0
            } for i in range(20)]
        )

        # 計算性能指標
        metrics = await performance_service.calculate_strategy_performance(
            strategy_id, user_id
        )

        # 驗證結果
        TestAssertions.assert_performance_metrics_valid(metrics.__dict__)
        assert metrics.strategy_id == strategy_id
        assert metrics.user_id == user_id

    @pytest.mark.asyncio
    async def test_performance_comparison(self, performance_service):
        """測試策略性能對比"""
        strategy_ids = ["strategy_001", "strategy_002", "strategy_003"]
        user_id = 1

        # Mock performance data
        mock_metrics = MockDataGenerator.generate_performance_metrics()

        performance_service.calculate_strategy_performance = AsyncMock(
            return_value=Mock()
        )
        performance_service.calculate_strategy_performance.return_value.__dict__ = mock_metrics

        # 執行對比
        comparison = await performance_service.get_performance_comparison(
            strategy_ids, user_id
        )

        # 驗證結果結構
        assert "strategies" in comparison
        assert "metrics" in comparison
        assert "rankings" in comparison
        assert len(comparison["strategies"]) == 3

    @pytest.mark.asyncio
    async def test_generate_performance_report(self, performance_service):
        """測試生成性能報告"""
        strategy_id = "test_strategy_001"
        user_id = 1

        # Mock metrics
        mock_metrics = MockDataGenerator.generate_performance_metrics()
        performance_service.calculate_strategy_performance = AsyncMock(
            return_value=Mock()
        )
        performance_service.calculate_strategy_performance.return_value.__dict__ = mock_metrics

        # 生成摘要報告
        report = await performance_service.generate_performance_report(
            strategy_id, user_id, "summary"
        )

        # 驗證報告結構
        assert "strategy_id" in report
        assert "summary" in report
        assert "risk_metrics" in report
        assert "total_return" in report["summary"]

    @pytest.mark.asyncio
    async def test_performance_with_time_range(self, performance_service):
        """測試時間範圍性能計算"""
        strategy_id = "test_strategy_001"
        user_id = 1
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)

        # Mock repository methods with date filtering
        performance_service.execution_repo.get_strategy_executions = AsyncMock(
            return_value=[]
        )

        # 計算性能指標（無交易數據）
        metrics = await performance_service.calculate_strategy_performance(
            strategy_id, user_id, start_date, end_date
        )

        # 驗證空指標
        assert metrics.total_return == 0.0
        assert metrics.total_trades == 0
        assert metrics.time_range == "1月"  # 30天約為1月


class TestServiceIntegration(ServiceTestCase):
    """
    服務集成測試
    測試服務之間的交互
    """

    @pytest.mark.asyncio
    async def test_strategy_execution_flow(self, strategy_service, execution_service):
        """測試策略執行流程"""
        user_id = 1

        # 1. 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        strategy = await strategy_service.create_strategy(strategy_data, user_id)

        # 2. 執行策略
        execution_request = MockDataGenerator.generate_execution_data(strategy.id)
        execution = await execution_service.create_execution(
            strategy.id, user_id, execution_request
        )

        # 3. 更新策略狀態
        await strategy_service.update_strategy_status(
            strategy.id, "running", user_id
        )

        # 4. 完成執行
        await execution_service.complete_execution(
            execution.id, {"final_value": 110000}
        )

        # 5. 更新策略狀態
        await strategy_service.update_strategy_status(
            strategy.id, "completed", user_id
        )

        # 驗證流程
        updated_strategy = await strategy_service.get_strategy(strategy.id, user_id)
        updated_execution = await execution_service.get_execution(execution.id, user_id)

        assert updated_strategy.status == "completed"
        assert updated_execution.status == "completed"

    @pytest.mark.asyncio
    async def test_performance_after_execution(
        self,
        strategy_service,
        execution_service,
        performance_service
    ):
        """測試執行後的性能計算"""
        user_id = 1

        # 1. 創建並執行策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        strategy = await strategy_service.create_strategy(strategy_data, user_id)

        execution_request = MockDataGenerator.generate_execution_data(strategy.id)
        execution = await execution_service.create_execution(
            strategy.id, user_id, execution_request
        )

        # 2. 模擬執行結果
        execution_results = {
            "trades": MockDataGenerator.generate_trade_data(10),
            "final_value": 105000,
            "start_time": datetime.now(timezone.utc) - timedelta(hours=1),
            "end_time": datetime.now(timezone.utc)
        }
        await execution_service.complete_execution(execution.id, execution_results)

        # 3. 計算性能
        performance_service.execution_repo.get_strategy_executions = AsyncMock(
            return_value=[{"id": execution.id}]
        )
        performance_service.execution_repo.get_execution_trades = AsyncMock(
            return_value=execution_results["trades"]
        )

        metrics = await performance_service.calculate_strategy_performance(
            strategy.id, user_id
        )

        # 驗證性能指標
        assert metrics.strategy_id == strategy.id
        assert metrics.total_trades > 0


# 測試工具函數
class TestUtils:
    """
    測試工具函數
    """

    @staticmethod
    def assert_service_error(service_method, error_code: str = None):
        """
        輔助函數：驗證服務拋出錯誤
        """
        with pytest.raises(Exception) as exc_info:
            asyncio.run(service_method)

        if error_code:
            assert hasattr(exc_info.value, 'code')
            assert exc_info.value.code == error_code

    @staticmethod
    def create_mock_strategy_repository():
        """創建模擬策略倉庫"""
        mock_repo = Mock()
        mock_repo.create = AsyncMock()
        mock_repo.get_by_id = AsyncMock()
        mock_repo.list = AsyncMock()
        mock_repo.update = AsyncMock()
        mock_repo.delete = AsyncMock()
        return mock_repo

    @staticmethod
    def create_mock_execution_repository():
        """創建模擬執行倉庫"""
        mock_repo = Mock()
        mock_repo.create = AsyncMock()
        mock_repo.get_by_id = AsyncMock()
        mock_repo.get_strategy_executions = AsyncMock()
        mock_repo.get_execution_trades = AsyncMock()
        mock_repo.stop = AsyncMock()
        return mock_repo

    @staticmethod
    def create_mock_cache_manager():
        """創建模擬緩存管理器"""
        mock_cache = Mock()
        mock_cache.get = AsyncMock()
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock()
        mock_cache.get_ttl = AsyncMock()
        return mock_cache


# Pytest 配置
@pytest.fixture
def event_loop():
    """創建事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """模擬數據庫"""
    db = Mock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.get_session = Mock()
    return db


# 測試標記
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance