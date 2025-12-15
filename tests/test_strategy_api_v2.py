"""
策略API v2 测试套件
Strategy API v2 Test Suite

测试新架构的策略API功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.api.strategies.services.strategy_service import BaseStrategyService
from src.api.strategies.services.execution_service import ExecutionService
from src.api.strategies.services.personal_service import PersonalService
from src.api.strategies.utils.response import (
    ResponseBuilder, APIError, ValidationError,
    NotFoundError, PermissionError
)
from src.api.strategies.utils.validators import StrategyValidator, ExecutionValidator
from src.api.strategies.models import (
    Strategy, StrategyType, StrategyStatus, RiskLevel,
    StrategyExecution, ExecutionStatus, StrategySignal, SignalType
)
from src.api.strategies.schemas import (
    StrategyCreate, StrategyUpdate, ExecutionRequest,
    UserPreferences, StrategyControlRequest
)


class TestResponseBuilder:
    """测试响应构建器"""

    def test_success_response(self):
        """测试成功响应"""
        data = {"id": 1, "name": "test"}
        response = ResponseBuilder.build_success(
            data=data,
            message="操作成功"
        )

        assert response.success is True
        assert response.code.value == "success"
        assert response.message == "操作成功"
        assert response.data == data
        assert response.timestamp is not None

    def test_paginated_response(self):
        """测试分页响应"""
        items = [{"id": i} for i in range(1, 6)]
        response = ResponseBuilder.build_paginated(
            items=items,
            total=100,
            page=1,
            page_size=20
        )

        assert response.success is True
        assert response.data["total"] == 100
        assert response.data["page"] == 1
        assert response.data["page_size"] == 20
        assert response.data["total_pages"] == 5
        assert response.data["has_next"] is True
        assert response.data["has_prev"] is False

    def test_error_response(self):
        """测试错误响应"""
        error = ValidationError("名称不能为空", field="name")
        response = ResponseBuilder.build_error(error)

        assert response.success is False
        assert response.code.value == "validation_error"
        assert response.message == "名称不能为空"
        assert response.errors is not None


class TestStrategyValidator:
    """测试策略验证器"""

    @pytest.mark.asyncio
    async def test_validate_create_request_valid(self):
        """测试有效的创建请求"""
        validator = StrategyValidator()
        request = StrategyCreate(
            name="测试策略",
            description="这是一个测试策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={"rsi_period": 14},
            risk_level=RiskLevel.MEDIUM
        )

        # 应该不抛出异常
        await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_invalid_name(self):
        """测试无效的策略名称"""
        validator = StrategyValidator()
        request = StrategyCreate(
            name="",  # 空名称
            description="这是一个测试策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={"rsi_period": 14},
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValidationError) as exc_info:
            await validator.validate_create_request(request)
        assert "策略名称是必填字段" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_rsi_parameters_valid(self):
        """测试有效的RSI参数"""
        validator = StrategyValidator()
        parameters = {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "stop_loss": 0.02,
            "take_profit": 0.05
        }

        # 应该不抛出异常
        validator._validate_rsi_parameters(parameters)

    @pytest.mark.asyncio
    async def test_validate_rsi_parameters_invalid_thresholds(self):
        """测试无效的RSI阈值"""
        validator = StrategyValidator()
        parameters = {
            "rsi_period": 14,
            "rsi_oversold": 70,  # 错误：超卖线高于超买线
            "rsi_overbought": 30
        }

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_rsi_parameters(parameters)
        assert "RSI超卖线必须小于超买线" in str(exc_info.value)


class TestExecutionValidator:
    """测试执行验证器"""

    @pytest.mark.asyncio
    async def test_validate_execution_request_valid(self):
        """测试有效的执行请求"""
        validator = ExecutionValidator()
        request = ExecutionRequest(
            execution_mode="backtest",
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now()
        )

        strategy = Mock(spec=Strategy)
        strategy.is_active = True
        strategy.parameters = {"rsi_period": 14}
        strategy.strategy_type = StrategyType.DIRECT_RSI

        # 应该不抛出异常
        await validator.validate_execution_request(request, strategy)

    @pytest.mark.asyncio
    async def test_validate_execution_request_invalid_mode(self):
        """测试无效的执行模式"""
        validator = ExecutionValidator()
        request = ExecutionRequest(
            execution_mode="invalid_mode"  # 无效模式
        )

        strategy = Mock(spec=Strategy)
        strategy.is_active = True
        strategy.parameters = {"rsi_period": 14}
        strategy.strategy_type = StrategyType.DIRECT_RSI

        with pytest.raises(ValidationError) as exc_info:
            await validator.validate_execution_request(request, strategy)
        assert "无效的执行模式" in str(exc_info.value)


class TestBaseStrategyService:
    """测试基础策略服务"""

    @pytest.fixture
    def mock_dependencies(self):
        """模拟依赖"""
        strategy_repo = AsyncMock()
        user_repo = AsyncMock()
        cache_manager = AsyncMock()
        validator = Mock(spec=StrategyValidator)

        return {
            "strategy_repo": strategy_repo,
            "user_repo": user_repo,
            "cache_manager": cache_manager,
            "validator": validator
        }

    @pytest.fixture
    def service(self, mock_dependencies):
        """创建服务实例"""
        return BaseStrategyService(**mock_dependencies.values())

    @pytest.mark.asyncio
    async def test_list_strategies_from_cache(self, service, mock_dependencies):
        """测试从缓存获取策略列表"""
        # 模拟缓存命中
        cached_result = {
            "strategies": [{"id": 1, "name": "策略1"}],
            "total_count": 1
        }
        mock_dependencies["cache_manager"].get.return_value = cached_result

        result = await service.list_strategies()

        assert result == cached_result
        mock_dependencies["cache_manager"].get.assert_called_once()
        mock_dependencies["strategy_repo"].list_strategies.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_strategies_from_db(self, service, mock_dependencies):
        """测试从数据库获取策略列表"""
        # 模拟缓存未命中
        mock_dependencies["cache_manager"].get.return_value = None

        # 模拟数据库返回
        strategies = [Mock()]
        total_count = 1
        mock_dependencies["strategy_repo"].list_strategies.return_value = (strategies, total_count)

        result = await service.list_strategies()

        assert "strategies" in result
        assert result["total_count"] == total_count
        mock_dependencies["cache_manager"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_strategy_success(self, service, mock_dependencies):
        """测试成功创建策略"""
        # 模拟依赖
        mock_dependencies["validator"].validate_create_request = AsyncMock()
        mock_dependencies["strategy_repo"].name_exists.return_value = False
        mock_dependencies["strategy_repo"].create = AsyncMock(return_value=Mock())

        request = StrategyCreate(
            name="新策略",
            description="测试策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={},
            risk_level=RiskLevel.MEDIUM
        )

        result = await service.create_strategy(request, user_id=1)

        assert result is not None
        mock_dependencies["validator"].validate_create_request.assert_called_once_with(request)
        mock_dependencies["strategy_repo"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_strategy_name_exists(self, service, mock_dependencies):
        """测试创建策略时名称已存在"""
        # 模拟名称已存在
        mock_dependencies["validator"].validate_create_request = AsyncMock()
        mock_dependencies["strategy_repo"].name_exists.return_value = True

        request = StrategyCreate(
            name="已存在的策略",
            description="测试策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={},
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValueError) as exc_info:
            await service.create_strategy(request, user_id=1)
        assert "策略名称已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_strategy_not_found(self, service, mock_dependencies):
        """测试删除不存在的策略"""
        mock_dependencies["strategy_repo"].get_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await service.delete_strategy("non_existent_id")
        assert "策略不存在" in str(exc_info.value)


class TestExecutionService:
    """测试执行服务"""

    @pytest.fixture
    def mock_execution_dependencies(self):
        """模拟执行服务依赖"""
        strategy_repo = AsyncMock()
        execution_repo = AsyncMock()
        cache_manager = AsyncMock()
        validator = Mock(spec=ExecutionValidator)

        return {
            "strategy_repo": strategy_repo,
            "execution_repo": execution_repo,
            "cache_manager": cache_manager,
            "validator": validator
        }

    @pytest.fixture
    def execution_service(self, mock_execution_dependencies):
        """创建执行服务实例"""
        return ExecutionService(**mock_execution_dependencies.values())

    @pytest.mark.asyncio
    async def test_execute_strategy_success(self, execution_service, mock_execution_dependencies):
        """测试成功执行策略"""
        # 模拟策略存在
        strategy = Mock(spec=Strategy)
        strategy.id = "strategy_123"
        strategy.user_id = 1
        mock_execution_dependencies["strategy_repo"].get_by_id.return_value = strategy

        # 模拟验证通过
        mock_execution_dependencies["validator"].validate_execution_request = AsyncMock()

        # 模拟创建执行记录
        execution = Mock(spec=StrategyExecution)
        execution.execution_id = "exec_123"
        execution.strategy_id = "strategy_123"
        execution.status = ExecutionStatus.PENDING
        execution.start_time = datetime.now()
        mock_execution_dependencies["execution_repo"].create.return_value = execution

        request = ExecutionRequest(
            execution_mode="backtest",
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now()
        )

        result = await execution_service.execute_strategy(
            strategy_id="strategy_123",
            request=request,
            background_tasks=Mock()
        )

        assert result.execution_id == "exec_123"
        assert result.strategy_id == "strategy_123"
        mock_execution_dependencies["execution_repo"].create.assert_called_once()


class TestPersonalService:
    """测试个人服务"""

    @pytest.fixture
    def mock_personal_dependencies(self):
        """模拟个人服务依赖"""
        strategy_repo = AsyncMock()
        user_repo = AsyncMock()
        cache_manager = AsyncMock()
        validator = Mock(spec=StrategyValidator)

        return {
            "strategy_repo": strategy_repo,
            "user_repo": user_repo,
            "cache_manager": cache_manager,
            "validator": validator
        }

    @pytest.fixture
    def personal_service(self, mock_personal_dependencies):
        """创建个人服务实例"""
        # 需要使用PersonalDataValidator
        from src.api.strategies.utils.validators import PersonalDataValidator
        mock_personal_dependencies["validator"] = Mock(spec=PersonalDataValidator)
        return PersonalService(**mock_personal_dependencies.values())

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, personal_service, mock_personal_dependencies):
        """测试获取仪表板数据"""
        # 模拟用户策略
        strategies = [Mock(spec=Strategy)]
        mock_personal_dependencies["strategy_repo"].get_user_strategies.return_value = strategies

        # 模拟性能数据
        mock_personal_dependencies["strategy_repo"].get_performance.return_value = None

        result = await personal_service.get_dashboard_data(user_id=1)

        assert result.total_strategies == 1
        assert result.active_strategies == 0
        mock_personal_dependencies["cache_manager"].get.assert_called_once()
        mock_personal_dependencies["cache_manager"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_control_strategy_enable(self, personal_service, mock_personal_dependencies):
        """测试启用策略"""
        # 模拟策略存在
        strategy = Mock(spec=Strategy)
        strategy.id = "strategy_123"
        strategy.user_id = 1
        strategy.is_active = False
        mock_personal_dependencies["strategy_repo"].get_by_id.return_value = strategy

        # 模拟更新
        mock_personal_dependencies["strategy_repo"].update.return_value = strategy
        mock_personal_dependencies["strategy_repo"].is_running.return_value = False

        request = StrategyControlRequest(
            action="enable",
            reason="手动启用"
        )

        result = await personal_service.control_strategy(
            user_id=1,
            strategy_id="strategy_123",
            request=request
        )

        assert result["success"] is True
        assert result["action"] == "enable"
        assert result["new_status"] is True


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_strategy_lifecycle(self):
        """测试策略生命周期"""
        # 创建模拟依赖
        strategy_repo = AsyncMock()
        user_repo = AsyncMock()
        cache_manager = AsyncMock()
        validator = Mock(spec=StrategyValidator)

        # 创建服务
        service = BaseStrategyService(strategy_repo, user_repo, cache_manager, validator)

        # 模拟数据
        strategy_id = "test_strategy_123"
        strategy = Mock(spec=Strategy)
        strategy.id = strategy_id
        strategy.user_id = 1
        strategy.name = "测试策略"
        strategy.status = StrategyStatus.INACTIVE

        # 设置模拟返回值
        strategy_repo.get_by_id.return_value = strategy
        strategy_repo.create.return_value = strategy
        strategy_repo.update.return_value = strategy
        strategy_repo.name_exists.return_value = False
        strategy_repo.is_running.return_value = False

        # 测试创建
        request = StrategyCreate(
            name="测试策略",
            description="测试描述",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={},
            risk_level=RiskLevel.MEDIUM
        )
        validator.validate_create_request = AsyncMock()

        created = await service.create_strategy(request, user_id=1)
        assert created is not None

        # 测试更新
        update_request = StrategyUpdate(description="更新后的描述")
        validator.validate_update_request = AsyncMock()

        updated = await service.update_strategy(strategy_id, update_request, user_id=1)
        assert updated is not None

        # 测试删除
        await service.delete_strategy(strategy_id, user_id=1)

        # 验证调用
        strategy_repo.create.assert_called_once()
        strategy_repo.update.assert_called_once()
        strategy_repo.delete.assert_called_once()


# 测试工具函数
def create_test_strategy(
    strategy_id: str = "test_123",
    name: str = "测试策略",
    status: StrategyStatus = StrategyStatus.ACTIVE
) -> Strategy:
    """创建测试策略"""
    return Strategy(
        id=strategy_id,
        name=name,
        description="测试策略描述",
        strategy_type=StrategyType.DIRECT_RSI,
        parameters={"rsi_period": 14},
        user_id=1,
        status=status,
        is_active=status == StrategyStatus.ACTIVE,
        risk_level=RiskLevel.MEDIUM,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_test_execution(
    execution_id: str = "exec_123",
    strategy_id: str = "test_123",
    status: ExecutionStatus = ExecutionStatus.RUNNING
) -> StrategyExecution:
    """创建测试执行"""
    return StrategyExecution(
        execution_id=execution_id,
        strategy_id=strategy_id,
        status=status,
        execution_mode="backtest",
        start_time=datetime.now(),
        data_source="test"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])