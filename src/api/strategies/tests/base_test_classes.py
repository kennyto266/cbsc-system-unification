"""
Base Test Classes for Strategy Module
策略模塊測試基類

提供通用測試工具和基類，減少測試代碼重複
"""

import pytest
import asyncio
from typing import Generator, Any, Dict, Optional
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import tempfile
import os
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from ..database.database import Database, Base
from ..container import Container
from ..models import Strategy, User
from ..services.strategy_service import BaseStrategyService
from ..repositories.strategy_repository import StrategyRepository


class BaseTestCase:
    """
    測試基類
    提供通用的測試設置和工具方法
    """

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """設置測試環境"""
        # 創建臨時數據庫
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_url = f"sqlite:///{self.temp_db.name}"

        # 初始化數據庫
        self.db = Database(self.db_url)
        await self.db.connect()
        self.db.create_tables()

        # 初始化容器
        self.container = Container()
        self.container.config.database_url.from_value(self.db_url)
        self.container.config.redis_url.from_value("redis://localhost:6379/1")  # 測試Redis DB

        # 創建測試用戶
        self.test_user = self._create_test_user()

        yield

        # 清理
        self.db.disconnect()
        self.temp_db.close()
        os.unlink(self.temp_db.name)

    def _create_test_user(self) -> User:
        """創建測試用戶"""
        return User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

    def create_test_strategy(self, **overrides) -> Strategy:
        """創建測試策略"""
        strategy_data = {
            "id": "test_strategy_001",
            "name": "測試RSI策略",
            "description": "用於測試的RSI策略",
            "user_id": self.test_user.id,
            "parameters": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70
            },
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        strategy_data.update(overrides)
        return Strategy(**strategy_data)


class ServiceTestCase(BaseTestCase):
    """
    服務層測試基類
    """

    @pytest.fixture
    async def strategy_service(self):
        """提供策略服務實例"""
        from ..container import get_strategy_service
        return await get_strategy_service()

    @pytest.fixture
    async def execution_service(self):
        """提供執行服務實例"""
        from ..container import get_execution_service
        return await get_execution_service()

    @pytest.fixture
    async def performance_service(self):
        """提供性能服務實例"""
        from ..container import get_performance_service
        return await get_performance_service()

    async def assert_service_response(
        self,
        service_method,
        expected_success: bool = True,
        expected_error_code: Optional[str] = None
    ):
        """
        輔助方法：驗證服務響應
        """
        try:
            result = await service_method
            assert expected_success, "Expected failure but got success"
            return result
        except Exception as e:
            assert not expected_success, f"Expected success but got error: {e}"
            if expected_error_code:
                assert hasattr(e, 'code') and e.code == expected_error_code


class RepositoryTestCase(BaseTestCase):
    """
    數據訪問層測試基類
    """

    @pytest.fixture
    async def strategy_repository(self):
        """提供策略倉庫實例"""
        from ..repositories.strategy_repository import StrategyRepository
        return StrategyRepository(self.db)

    @pytest.fixture
    async def execution_repository(self):
        """提供執行倉庫實例"""
        from ..repositories.execution_repository import ExecutionRepository
        return ExecutionRepository(self.db)

    async def assert_database_record(
        self,
        repository,
        record_id: str,
        expected_data: Dict[str, Any],
        exclude_fields: list = None
    ):
        """
        輔助方法：驗證數據庫記錄
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']

        record = await repository.get_by_id(record_id)
        assert record is not None, f"Record {record_id} not found"

        record_dict = record.__dict__.copy()
        for field in exclude_fields:
            record_dict.pop(field, None)

        for key, value in expected_data.items():
            if key in record_dict:
                assert record_dict[key] == value, \
                    f"Field {key} mismatch: expected {value}, got {record_dict[key]}"


class APIEndpointTestCase(BaseTestCase):
    """
    API端點測試基類
    """

    @pytest.fixture
    def client(self):
        """提供測試客戶端"""
        from ..main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """提供認證頭"""
        return {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        }

    def assert_api_response(
        self,
        response,
        expected_status: int = 200,
        expected_success: bool = True,
        check_data_schema: bool = True
    ):
        """
        輔助方法：驗證API響應
        """
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}"

        data = response.json()

        if expected_success:
            assert data.get("success", True), "API response indicates failure"
        else:
            assert not data.get("success", False), "API response indicates success"

        if check_data_schema and "data" in data:
            assert isinstance(data["data"], (dict, list)), "Data should be dict or list"

        return data


class IntegrationTestCase(BaseTestCase):
    """
    集成測試基類
    測試組件之間的交互
    """

    async def setup_integration_test(self):
        """設置集成測試環境"""
        # 初始化所有必要的服务
        self.strategy_service = await self.container.strategy_service()
        self.execution_service = await self.container.execution_service()
        self.performance_service = await self.container.performance_service()

    async def create_test_workflow(self):
        """
        創建完整的測試工作流：
        1. 創建策略
        2. 執行策略
        3. 分析性能
        """
        # 1. 創建策略
        strategy = self.create_test_strategy()
        created_strategy = await self.strategy_service.create_strategy(
            strategy, self.test_user.id
        )

        # 2. 執行策略（模擬）
        execution_request = {
            "strategy_id": created_strategy.id,
            "execution_mode": "backtest",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "initial_capital": 100000
        }
        # execution = await self.execution_service.execute_strategy(execution_request)

        # 3. 分析性能
        # performance = await self.performance_service.calculate_strategy_performance(
        #     created_strategy.id, self.test_user.id
        # )

        return {
            "strategy": created_strategy,
            # "execution": execution,
            # "performance": performance
        }


class MockDataGenerator:
    """
    模擬數據生成器
    生成測試所需的各種數據
    """

    @staticmethod
    def generate_strategy_data(count: int = 1) -> list:
        """生成策略數據"""
        strategies = []
        for i in range(count):
            strategies.append({
                "name": f"測試策略_{i+1}",
                "description": f"第{i+1}個測試策略",
                "parameters": {
                    "period": 14 + i,
                    "threshold": 30 - i
                }
            })
        return strategies if count > 1 else strategies[0]

    @staticmethod
    def generate_execution_data(strategy_id: str) -> dict:
        """生成執行數據"""
        return {
            "strategy_id": strategy_id,
            "execution_mode": "backtest",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "initial_capital": 100000,
            "status": "completed"
        }

    @staticmethod
    def generate_trade_data(count: int = 10) -> list:
        """生成交易數據"""
        trades = []
        base_price = 100
        for i in range(count):
            price = base_price + (i % 5) * 2
            trades.append({
                "timestamp": datetime.now(timezone.utc),
                "symbol": "TEST",
                "action": "BUY" if i % 2 == 0 else "SELL",
                "quantity": 100,
                "price": price,
                "value": price * 100,
                "pnl": (price - base_price) * 100 if i % 2 == 1 else 0
            })
        return trades

    @staticmethod
    def generate_performance_metrics() -> dict:
        """生成性能指標"""
        return {
            "total_return": 0.15,
            "annualized_return": 0.18,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.08,
            "win_rate": 0.65,
            "profit_factor": 2.1,
            "total_trades": 50,
            "volatility": 0.12
        }


class TestAssertions:
    """
    測試斷言工具類
    提供常用的測試斷言方法
    """

    @staticmethod
    def assert_performance_metrics_valid(metrics: dict):
        """驗證性能指標的有效性"""
        required_fields = [
            "total_return", "sharpe_ratio", "max_drawdown",
            "win_rate", "profit_factor", "total_trades"
        ]

        for field in required_fields:
            assert field in metrics, f"Missing required field: {field}"

        # 驗證數值範圍
        assert -1 <= metrics["total_return"] <= 10, "Total return out of range"
        assert metrics["sharpe_ratio"] >= 0 or metrics["sharpe_ratio"] <= 0, "Invalid Sharpe ratio"
        assert -1 <= metrics["max_drawdown"] <= 0, "Max drawdown should be negative or zero"
        assert 0 <= metrics["win_rate"] <= 1, "Win rate should be between 0 and 1"
        assert metrics["profit_factor"] >= 0, "Profit factor should be non-negative"
        assert metrics["total_trades"] >= 0, "Total trades should be non-negative"

    @staticmethod
    def assert_strategy_data_valid(strategy_data: dict):
        """驗證策略數據的有效性"""
        assert "name" in strategy_data, "Missing strategy name"
        assert "user_id" in strategy_data, "Missing user_id"
        assert len(strategy_data["name"]) > 0, "Strategy name cannot be empty"
        assert strategy_data["user_id"] > 0, "Invalid user_id"

    @staticmethod
    def assert_api_response_structure(response: dict):
        """驗證API響應結構"""
        if "success" in response:
            assert isinstance(response["success"], bool), "Success should be boolean"

        if response.get("success", True) and "data" in response:
            assert response["data"] is not None, "Data should not be null in success response"

        if not response.get("success", True) and "error" in response:
            assert "code" in response["error"], "Error should have code"
            assert "message" in response["error"], "Error should have message"


# Export all test utilities
__all__ = [
    "BaseTestCase",
    "ServiceTestCase",
    "RepositoryTestCase",
    "APIEndpointTestCase",
    "IntegrationTestCase",
    "MockDataGenerator",
    "TestAssertions"
]