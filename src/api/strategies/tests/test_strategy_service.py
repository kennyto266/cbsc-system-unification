"""
策略服务测试
Strategy Service Tests
"""

import pytest
import asyncio
from datetime import datetime

from ..services.strategy_service import BaseStrategyService
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..utils.cache import CacheManager
from ..utils.validators import StrategyValidator
from ..models import Strategy, StrategyType, StrategyStatus, RiskLevel
from ..schemas import StrategyCreate, StrategyUpdate


@pytest.fixture
def strategy_service():
    """创建策略服务测试fixture"""
    strategy_repo = StrategyRepository()
    user_repo = UserRepository()
    cache_manager = CacheManager()
    validator = StrategyValidator()

    service = BaseStrategyService(strategy_repo, user_repo, cache_manager, validator)
    return service


@pytest.fixture
def sample_strategy_create():
    """示例策略创建请求"""
    return StrategyCreate(
        name="测试策略",
        description="这是一个测试策略",
        strategy_type=StrategyType.DIRECT_RSI,
        parameters={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        },
        risk_level=RiskLevel.MEDIUM
    )


class TestBaseStrategyService:
    """BaseStrategyService测试类"""

    @pytest.mark.asyncio
    async def test_create_strategy(self, strategy_service, sample_strategy_create):
        """测试创建策略"""
        # 创建策略
        strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 验证结果
        assert strategy is not None
        assert strategy.name == "测试策略"
        assert strategy.strategy_type == StrategyType.DIRECT_RSI
        assert strategy.user_id == 1
        assert strategy.status == StrategyStatus.INACTIVE
        assert strategy.is_active == False

    @pytest.mark.asyncio
    async def test_get_strategy_detail(self, strategy_service, sample_strategy_create):
        """测试获取策略详情"""
        # 先创建策略
        created_strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 获取策略详情
        detail = await strategy_service.get_strategy_detail(created_strategy.id, user_id=1)

        # 验证结果
        assert detail is not None
        assert "strategy" in detail
        assert detail["strategy"].id == created_strategy.id
        assert detail["strategy"].name == "测试策略"

    @pytest.mark.asyncio
    async def test_list_strategies(self, strategy_service, sample_strategy_create):
        """测试获取策略列表"""
        # 创建多个策略
        await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 创建第二个策略
        sample_strategy_create.name = "测试策略2"
        await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 获取策略列表
        result = await strategy_service.list_strategies(user_id=1)

        # 验证结果
        assert result is not None
        assert "strategies" in result
        assert len(result["strategies"]) >= 2
        assert result["total_count"] >= 2

    @pytest.mark.asyncio
    async def test_update_strategy(self, strategy_service, sample_strategy_create):
        """测试更新策略"""
        # 创建策略
        strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 更新策略
        update_request = StrategyUpdate(
            name="更新后的策略名称",
            description="更新后的描述"
        )
        updated_strategy = await strategy_service.update_strategy(
            strategy.id, update_request, user_id=1
        )

        # 验证结果
        assert updated_strategy is not None
        assert updated_strategy.name == "更新后的策略名称"
        assert updated_strategy.description == "更新后的描述"
        assert updated_strategy.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_strategy(self, strategy_service, sample_strategy_create):
        """测试删除策略"""
        # 创建策略
        strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 删除策略
        await strategy_service.delete_strategy(strategy.id, user_id=1)

        # 验证策略已删除
        with pytest.raises(ValueError, match="策略不存在"):
            await strategy_service.get_strategy_detail(strategy.id, user_id=1)

    @pytest.mark.asyncio
    async def test_batch_operation(self, strategy_service, sample_strategy_create):
        """测试批量操作"""
        # 创建多个策略
        strategy1 = await strategy_service.create_strategy(sample_strategy_create, user_id=1)
        sample_strategy_create.name = "策略2"
        strategy2 = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 批量激活
        result = await strategy_service.batch_operation(
            [strategy1.id, strategy2.id], "activate", user_id=1
        )

        # 验证结果
        assert result is not None
        assert "success" in result
        assert "failed" in result
        assert len(result["success"]) == 2
        assert len(result["failed"]) == 0

    @pytest.mark.asyncio
    async def test_get_templates(self, strategy_service):
        """测试获取策略模板"""
        # 获取所有模板
        templates = await strategy_service.get_templates()

        # 验证结果
        assert templates is not None
        assert len(templates) > 0
        assert any(t.strategy_type == StrategyType.DIRECT_RSI for t in templates)

    @pytest.mark.asyncio
    async def test_permission_check(self, strategy_service, sample_strategy_create):
        """测试权限检查"""
        # 用户1创建策略
        strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 用户2尝试访问
        with pytest.raises(PermissionError):
            await strategy_service.get_strategy_detail(strategy.id, user_id=2)

    @pytest.mark.asyncio
    async def test_caching(self, strategy_service, sample_strategy_create):
        """测试缓存功能"""
        # 创建策略
        strategy = await strategy_service.create_strategy(sample_strategy_create, user_id=1)

        # 第一次获取（从数据库）
        detail1 = await strategy_service.get_strategy_detail(strategy.id, user_id=1)

        # 第二次获取（从缓存）
        detail2 = await strategy_service.get_strategy_detail(strategy.id, user_id=1)

        # 验证结果一致
        assert detail1["strategy"].id == detail2["strategy"].id


if __name__ == "__main__":
    # 运行测试
    asyncio.run(pytest.main([__file__, "-v"]))