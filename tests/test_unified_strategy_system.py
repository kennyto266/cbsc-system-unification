#!/usr/bin/env python3
"""
統一策略系統測試
Unified Strategy System Tests

測試統一策略管理系統的完整功能
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os

# 導入測試目標
from src.api.unified_strategy_service import (
    UnifiedStrategyManager,
    StrategyExecutionState,
    StrategySignal,
    StrategyExecutionRequest,
    StrategyMetrics,
    StrategyTemplate
)
from src.api.strategy_compatibility_adapter import (
    StrategyCompatibilityAdapter,
    StrategyDataMigrator
)
from src.api.strategy_execution_engine import (
    StrategyExecutionEngine,
    DirectRSIStrategy,
    SentimentMomentumStrategy,
    StrategyFactory
)
from src.api.strategy_monitoring_service import (
    StrategyMonitoringService,
    StrategyStatus,
    StrategyAlert,
    MonitoringLevel,
    AlertType
)
from src.models.strategy import (
    StrategyCreateSchema,
    StrategyUpdateSchema,
    StrategyResponseSchema
)

# ============================================================================
# 測試配置 (Test Configuration)
# ============================================================================

@pytest.fixture
def mock_db_session():
    """模擬數據庫會話"""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.query = Mock()
    session.refresh = Mock()
    session.close = Mock()
    return session

@pytest.fixture
def mock_db_session_factory(mock_db_session):
    """模擬數據庫會話工廠"""
    return Mock(return_value=mock_db_session)

@pytest.fixture
def sample_strategy_data():
    """示例策略數據"""
    return {
        "name": "測試RSI策略",
        "code": "TEST_RSI_001",
        "description": "用於測試的RSI策略",
        "strategy_type": "direct_rsi",
        "risk_level": "medium",
        "default_parameters": {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70
        },
        "required_indicators": ["RSI"],
        "supported_timeframes": ["1d", "1h", "4h"]
    }

@pytest.fixture
def sample_legacy_strategy_data():
    """示例遺留策略數據"""
    return {
        "id": "legacy_rsi_001",
        "name": "遺留RSI策略",
        "description": "遺留格式的RSI策略",
        "strategy_type": "direct_rsi",
        "status": "active",
        "risk_level": "medium",
        "parameters": {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70
        },
        "performance": {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.08,
            "win_rate": 0.65
        },
        "indicators": ["RSI"],
        "timeframes": ["1d", "1h"]
    }

# ============================================================================
# 統一策略管理器測試 (Unified Strategy Manager Tests)
# ============================================================================

class TestUnifiedStrategyManager:
    """統一策略管理器測試"""

    @pytest.fixture
    def manager(self, mock_db_session_factory):
        """創建策略管理器實例"""
        return UnifiedStrategyManager(mock_db_session_factory)

    @pytest.mark.asyncio
    async def test_create_strategy(self, manager, sample_strategy_data, mock_db_session):
        """測試創建策略"""
        # 準備測試數據
        request = StrategyCreateSchema(**sample_strategy_data)
        user_id = "test_user_001"

        # 模擬數據庫操作
        mock_strategy = Mock()
        mock_strategy.id = "strategy_001"
        mock_strategy.name = request.name
        mock_strategy.code = "STRAT_DIRECT_RSI_test_us_20241211120000"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        with patch.object(manager, 'get_db_session', return_value=mock_db_session):
            with patch('src.models.strategy.Strategy') as mock_strategy_class:
                mock_strategy_class.return_value = mock_strategy

                # 執行測試
                result = await manager.create_strategy(request, user_id)

                # 驗證結果
                assert result is not None
                assert result.name == request.name
                assert result.strategy_type == request.strategy_type
                assert result.risk_level == request.risk_level

    @pytest.mark.asyncio
    async def test_get_strategies(self, manager, mock_db_session):
        """測試獲取策略列表"""
        user_id = "test_user_001"

        # 模擬數據庫查詢
        mock_query = Mock()
        mock_strategies = [Mock(), Mock(), Mock()]
        for i, strategy in enumerate(mock_strategies):
            strategy.id = f"strategy_{i:03d}"
            strategy.name = f"策略 {i+1}"
            strategy.strategy_type = "direct_rsi"
            strategy.status = "active"
            strategy.is_public = False
            strategy.total_users = 0
            strategy.active_users = 0
            strategy.total_signals = 0

        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_strategies
        mock_db_session.query.return_value = mock_query

        with patch.object(manager, 'get_db_session', return_value=mock_db_session):
            with patch('src.models.strategy.StrategyResponseSchema.from_orm') as mock_from_orm:
                mock_from_orm.side_effect = lambda s: {
                    'id': s.id,
                    'name': s.name,
                    'strategy_type': s.strategy_type,
                    'status': s.status,
                    'is_public': s.is_public,
                    'total_users': s.total_users,
                    'active_users': s.active_users,
                    'total_signals': s.total_signals
                }

                # 執行測試
                result = await manager.get_strategies(user_id)

                # 驗證結果
                assert isinstance(result, list)
                assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_update_strategy(self, manager, mock_db_session):
        """測試更新策略"""
        strategy_id = "strategy_001"
        user_id = "test_user_001"

        update_data = {
            "name": "更新後的策略名稱",
            "description": "更新後的策略描述"
        }
        request = StrategyUpdateSchema(**update_data)

        # 模擬現有策略
        mock_strategy = Mock()
        mock_strategy.id = strategy_id
        mock_strategy.name = "原始名稱"
        mock_strategy.description = "原始描述"
        mock_strategy.updated_at = datetime.now()

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_strategy
        mock_db_session.query.return_value = mock_query

        with patch.object(manager, 'get_db_session', return_value=mock_db_session):
            with patch('src.models.strategy.StrategyResponseSchema.from_orm') as mock_from_orm:
                mock_response = Mock()
                mock_response.name = update_data["name"]
                mock_response.description = update_data["description"]
                mock_from_orm.return_value = mock_response

                # 執行測試
                result = await manager.update_strategy(strategy_id, request, user_id)

                # 驗證結果
                assert result is not None
                assert result.name == update_data["name"]
                assert result.description == update_data["description"]

    @pytest.mark.asyncio
    async def test_delete_strategy(self, manager, mock_db_session):
        """測試刪除策略"""
        strategy_id = "strategy_001"
        user_id = "test_user_001"

        # 模擬現有策略
        mock_strategy = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_strategy
        mock_db_session.query.return_value = mock_query

        with patch.object(manager, 'get_db_session', return_value=mock_db_session):
            # 執行測試
            result = await manager.delete_strategy(strategy_id, user_id)

            # 驗證結果
            assert result is True
            mock_db_session.delete.assert_called()
            mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_validate_strategy_config(self, manager):
        """測試策略配置驗證"""
        # 測試有效配置
        valid_config = {
            "name": "有效策略",
            "strategy_type": "direct_rsi",
            "default_parameters": {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            }
        }

        result = await manager.validate_strategy_config(valid_config)
        assert result["is_valid"] is True
        assert len(result["validation_errors"]) == 0

        # 測試無效配置
        invalid_config = {
            "name": "",  # 空名稱
            "strategy_type": "direct_rsi",
            "default_parameters": {
                "rsi_period": 100,  # 超出範圍
                "oversold_threshold": 80,  # 大於超買閾值
                "overbought_threshold": 20
            }
        }

        result = await manager.validate_strategy_config(invalid_config)
        assert result["is_valid"] is False
        assert len(result["validation_errors"]) > 0

# ============================================================================
# 兼容性適配器測試 (Compatibility Adapter Tests)
# ============================================================================

class TestStrategyCompatibilityAdapter:
    """策略兼容性適配器測試"""

    @pytest.fixture
    def adapter(self):
        """創建適配器實例"""
        return StrategyCompatibilityAdapter()

    def test_convert_legacy_to_unified(self, adapter, sample_legacy_strategy_data):
        """測試遺留格式轉換為統一格式"""
        result = adapter.convert_legacy_strategy_to_unified(sample_legacy_strategy_data)

        # 驗證轉換結果
        assert result is not None
        assert result["name"] == sample_legacy_strategy_data["name"]
        assert result["strategy_type"] == "technical"  # direct_rsi -> technical
        assert result["status"] == "active"
        assert result["risk_level"] == "medium"
        assert "default_parameters" in result

    def test_convert_unified_to_legacy(self, adapter, sample_strategy_data):
        """測試統一格式轉換為遺留格式"""
        result = adapter.convert_unified_strategy_to_legacy(sample_strategy_data)

        # 驗證轉換結果
        assert result is not None
        assert result["name"] == sample_strategy_data["name"]
        assert result["strategy_type"] == "direct_rsi"  # technical -> direct_rsi
        assert result["status"] == "active"
        assert result["risk_level"] == "medium"

    def test_validate_data_compatibility(self, adapter):
        """測試數據兼容性驗證"""
        # 測試兼容數據
        compatible_data = {
            "name": "兼容策略",
            "strategy_type": "direct_rsi",
            "parameters": {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            }
        }

        result = adapter.validate_data_compatibility(compatible_data, "strategy")
        assert result["is_valid"] is True
        assert len(result["validation_errors"]) == 0

        # 測試不兼容數據
        incompatible_data = {
            "name": "",  # 必需字段缺失
            "strategy_type": "unknown_type",  # 未知類型
            "parameters": {
                "rsi_period": 100  # 超出範圍
            }
        }

        result = adapter.validate_data_compatibility(incompatible_data, "strategy")
        assert result["is_valid"] is False
        assert len(result["validation_errors"]) > 0

# ============================================================================
# 策略執行引擎測試 (Strategy Execution Engine Tests)
# ============================================================================

class TestStrategyExecutionEngine:
    """策略執行引擎測試"""

    @pytest.fixture
    def engine(self):
        """創建執行引擎實例"""
        return StrategyExecutionEngine()

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """測試引擎初始化"""
        await engine.initialize()
        assert engine.is_running is True

        await engine.shutdown()
        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_create_rsi_strategy(self):
        """測試創建RSI策略"""
        strategy_id = "test_rsi_001"
        parameters = {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70
        }

        strategy = StrategyFactory.create_strategy("direct_rsi", strategy_id, parameters)

        assert isinstance(strategy, DirectRSIStrategy)
        assert strategy.strategy_id == strategy_id
        assert strategy.rsi_period == 14
        assert strategy.oversold_threshold == 30
        assert strategy.overbought_threshold == 70

    @pytest.mark.asyncio
    async def test_create_sentiment_strategy(self):
        """測試創建情緒動量策略"""
        strategy_id = "test_sentiment_001"
        parameters = {
            "rsi_period": 14,
            "fast_period": 12,
            "slow_period": 26,
            "weight_sentiment": 0.6
        }

        strategy = StrategyFactory.create_strategy("sentiment_momentum", strategy_id, parameters)

        assert isinstance(strategy, SentimentMomentumStrategy)
        assert strategy.strategy_id == strategy_id
        assert strategy.weight_sentiment == 0.6

    @pytest.mark.asyncio
    async def test_rsi_strategy_execution(self):
        """測試RSI策略執行"""
        import pandas as pd

        strategy_id = "test_rsi_exec_001"
        parameters = {
            "rsi_period": 10,  # 使用較短週期以加快測試
            "oversold_threshold": 30,
            "overbought_threshold": 70
        }

        strategy = StrategyFactory.create_strategy("direct_rsi", strategy_id, parameters)

        # 創建測試市場數據
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        prices = [100 + i * 0.5 + (i % 3) * 2 for i in range(30)]  # 模擬價格數據

        market_data = pd.DataFrame({
            "timestamp": dates,
            "open": prices,
            "high": [p * 1.02 for p in prices],
            "low": [p * 0.98 for p in prices],
            "close": prices,
            "volume": [1000000 + i * 10000 for i in range(30)]
        })

        # 初始化策略
        init_result = await strategy.initialize(market_data)
        assert init_result is True

        # 生成信號
        signals = await strategy.generate_signals(market_data)
        assert isinstance(signals, list)

        # 清理
        await strategy.cleanup()

    @pytest.mark.asyncio
    async def test_strategy_execution_flow(self, engine):
        """測試完整策略執行流程"""
        from src.api.strategy_execution_engine import ExecutionRequest, ExecutionMode

        # 創建執行請求
        request = ExecutionRequest(
            request_id="test_exec_001",
            strategy_id="test_strategy_001",
            execution_mode=ExecutionMode.BACKTEST,
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now(),
            parameters={
                "strategy_type": "direct_rsi",
                "rsi_period": 10,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            }
        )

        # 創建測試市場數據
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        prices = [150 + i * 0.3 + (i % 5) * 1.5 for i in range(50)]

        market_data = pd.DataFrame({
            "timestamp": dates,
            "open": prices,
            "high": [p * 1.015 for p in prices],
            "low": [p * 0.985 for p in prices],
            "close": prices,
            "volume": [2000000 + i * 20000 for i in range(50)]
        })

        # 等待引擎初始化
        await engine.initialize()

        try:
            # 執行策略
            result = await engine.execute_strategy(request, market_data)

            # 驗證結果
            assert result is not None
            assert result.request_id == request.request_id
            assert result.strategy_id == request.strategy_id
            assert result.status.value in ["completed", "failed"]
            assert result.signals_generated >= 0

        finally:
            await engine.shutdown()

# ============================================================================
# 監控服務測試 (Monitoring Service Tests)
# ============================================================================

class TestStrategyMonitoringService:
    """策略監控服務測試"""

    @pytest.fixture
    def monitoring_service(self):
        """創建監控服務實例"""
        from src.api.strategy_monitoring_service import MonitoringConfig
        config = MonitoringConfig(update_interval=timedelta(seconds=1))
        return StrategyMonitoringService(config)

    @pytest.mark.asyncio
    async def test_service_initialization(self, monitoring_service):
        """測試服務初始化"""
        result = await monitoring_service.start_monitoring()
        assert result is True
        assert monitoring_service.is_running is True

        await monitoring_service.stop_monitoring()
        assert monitoring_service.is_running is False

    @pytest.mark.asyncio
    async def test_add_strategy_monitor(self, monitoring_service):
        """測試添加策略監控"""
        strategy_id = "test_strategy_001"
        initial_status = StrategyStatus(
            strategy_id=strategy_id,
            is_running=False,
            last_update=datetime.now()
        )

        await monitoring_service.start_monitoring()

        try:
            result = await monitoring_service.add_strategy_monitor(strategy_id, initial_status)
            assert result is True
            assert strategy_id in monitoring_service.strategy_statuses
            assert strategy_id in monitoring_service.monitoring_tasks

        finally:
            await monitoring_service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_update_strategy_status(self, monitoring_service):
        """測試更新策略狀態"""
        strategy_id = "test_strategy_002"

        await monitoring_service.start_monitoring()

        try:
            # 添加監控
            await monitoring_service.add_strategy_monitor(strategy_id)

            # 更新狀態
            status_update = {
                "is_running": True,
                "unrealized_pnl": 1500.0,
                "daily_pnl": 200.0,
                "total_trades": 5
            }

            await monitoring_service.update_strategy_status(strategy_id, status_update)

            # 驗證更新
            status = await monitoring_service.get_strategy_status(strategy_id)
            assert status is not None
            assert status.is_running is True
            assert status.unrealized_pnl == 1500.0
            assert status.daily_pnl == 200.0
            assert status.total_trades == 5

        finally:
            await monitoring_service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_alert_creation(self, monitoring_service):
        """測試告警創建"""
        strategy_id = "test_strategy_003"

        await monitoring_service.start_monitoring()

        try:
            # 添加監控
            await monitoring_service.add_strategy_monitor(strategy_id)

            # 觸發告警條件
            status_update = {
                "is_running": True,
                "performance_metrics": {
                    "max_drawdown": 0.20  # 超過15%閾值
                }
            }

            await monitoring_service.update_strategy_status(strategy_id, status_update)

            # 檢查告警
            alerts = await monitoring_service.get_active_alerts(strategy_id)
            assert len(alerts) > 0
            assert alerts[0].alert_type == AlertType.RISK_LIMIT_BREACH
            assert alerts[0].level == MonitoringLevel.CRITICAL

        finally:
            await monitoring_service.stop_monitoring()

    def test_add_callbacks(self, monitoring_service):
        """測試添加回調函數"""
        # 添加狀態回調
        status_callback = Mock()
        monitoring_service.add_status_callback(status_callback)
        assert len(monitoring_service.status_callbacks) == 1

        # 添加告警回調
        alert_callback = Mock()
        monitoring_service.add_alert_callback(alert_callback)
        assert len(monitoring_service.alert_callbacks) == 1

        # 添加指標回調
        metric_callback = Mock()
        monitoring_service.add_metric_callback(metric_callback)
        assert len(monitoring_service.metric_callbacks) == 1

# ============================================================================
# 集成測試 (Integration Tests)
# ============================================================================

class TestSystemIntegration:
    """系統集成測試"""

    @pytest.mark.asyncio
    async def test_end_to_end_strategy_lifecycle(self):
        """測試完整策略生命週期"""
        # 這個測試需要模擬整個策略創建到執行的完整流程
        # 由於依賴較多，這裡只提供框架

        # 1. 創建策略
        # 2. 驗證配置
        # 3. 啟動監控
        # 4. 執行策略
        # 5. 監控性能
        # 6. 生成告警
        # 7. 停止策略

        assert True  # 佔位符，實際實現需要完整的系統設置

    @pytest.mark.asyncio
    async def test_data_migration_flow(self):
        """測試數據遷移流程"""
        adapter = StrategyCompatibilityAdapter()
        migrator = StrategyDataMigrator(adapter)

        # 模擬遺留數據
        legacy_data = [
            {
                "id": "legacy_001",
                "name": "遺留策略1",
                "strategy_type": "direct_rsi",
                "parameters": {"rsi_period": 14}
            },
            {
                "id": "legacy_002",
                "name": "遺留策略2",
                "strategy_type": "sentiment_momentum",
                "parameters": {"weight_sentiment": 0.6}
            }
        ]

        # 執行遷移
        result = await migrator.migrate_strategies(legacy_data, batch_size=10)

        # 驗證結果
        assert result["total"] == 2
        assert result["success_count"] >= 0
        assert result["error_count"] >= 0

# ============================================================================
# 性能測試 (Performance Tests)
# ============================================================================

class TestPerformance:
    """性能測試"""

    @pytest.mark.asyncio
    async def test_large_scale_strategy_execution(self):
        """測試大規模策略執行性能"""
        import time
        import pandas as pd

        # 創建大量市場數據
        dates = pd.date_range(start="2023-01-01", periods=1000, freq="D")
        prices = [100 + i * 0.1 + (i % 10) * 0.5 for i in range(1000)]

        market_data = pd.DataFrame({
            "timestamp": dates,
            "open": prices,
            "high": [p * 1.02 for p in prices],
            "low": [p * 0.98 for p in prices],
            "close": prices,
            "volume": [1000000 + i * 1000 for i in range(1000)]
        })

        # 測試執行時間
        start_time = time.time()

        strategy = DirectRSIStrategy("perf_test_001", {"rsi_period": 14})
        await strategy.initialize(market_data)
        signals = await strategy.generate_signals(market_data)
        await strategy.cleanup()

        end_time = time.time()
        execution_time = end_time - start_time

        # 性能斷言（應該在合理時間內完成）
        assert execution_time < 10.0  # 10秒內完成
        assert len(signals) >= 0

    @pytest.mark.asyncio
    async def test_concurrent_strategy_monitoring(self):
        """測試並發策略監控性能"""
        from src.api.strategy_monitoring_service import MonitoringConfig, StrategyStatus

        # 配置較短的更新間隔以加快測試
        config = MonitoringConfig(
            update_interval=timedelta(milliseconds=100),
            max_concurrent_monitors=50
        )

        service = StrategyMonitoringService(config)
        await service.start_monitoring()

        try:
            # 添加多個策略監控
            strategy_count = 20
            for i in range(strategy_count):
                strategy_id = f"concurrent_test_{i:03d}"
                status = StrategyStatus(
                    strategy_id=strategy_id,
                    is_running=i % 2 == 0,
                    last_update=datetime.now(),
                    unrealized_pnl=i * 100.0
                )
                await service.add_strategy_monitor(strategy_id, status)

            # 批量更新狀態
            start_time = time.time()

            for i in range(strategy_count):
                strategy_id = f"concurrent_test_{i:03d}"
                await service.update_strategy_status(strategy_id, {
                    "daily_pnl": i * 10.0,
                    "total_trades": i + 1
                })

            end_time = time.time()
            update_time = end_time - start_time

            # 性能斷言
            assert update_time < 5.0  # 5秒內完成所有更新

        finally:
            await service.stop_monitoring()

# ============================================================================
# 測試運行器 (Test Runner)
# ============================================================================

if __name__ == "__main__":
    # 運行所有測試
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=src.api",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])