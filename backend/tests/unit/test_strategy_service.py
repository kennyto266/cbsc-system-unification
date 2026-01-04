"""
Unit tests for Unified Strategy Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.unified_strategy_service import UnifiedStrategyService
from src.services.interfaces import ServiceResponse


@pytest.mark.unit
class TestUnifiedStrategyService:
    """Test UnifiedStrategyService"""

    @pytest.mark.asyncio
    async def test_create_strategy_success(self, db_session, test_user):
        """Test successful strategy creation"""
        service = UnifiedStrategyService(db=db_session, user_id=test_user.id)
        
        result = await service.create_strategy(
            user_id=test_user.id,
            name="Test Strategy",
            strategy_type="momentum",
            config={"short_window": 5, "long_window": 20},
            description="A test strategy"
        )
        
        assert result.success is True
        assert result.data is not None
        assert result.data["name"] == "Test Strategy"
        assert result.data["strategy_type"] == "momentum"
        assert result.data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_strategy_missing_name(self, db_session, test_user):
        """Test strategy creation fails without name"""
        service = UnifiedStrategyService(db=db_session, user_id=test_user.id)
        
        result = await service.create_strategy(
            user_id=test_user.id,
            name="",  # Empty name
            strategy_type="momentum",
            config={}
        )
        
        assert result.success is False
        assert "name" in result.error.lower()

    @pytest.mark.asyncio
    async def test_get_strategy_success(self, db_session, test_strategy):
        """Test successful strategy retrieval"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        result = await service.get_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        assert result.success is True
        assert result.data["name"] == test_strategy.name

    @pytest.mark.asyncio
    async def test_get_strategy_not_found(self, db_session, test_user):
        """Test getting non-existent strategy"""
        service = UnifiedStrategyService(db=db_session, user_id=test_user.id)
        
        result = await service.get_strategy(
            strategy_id="non-existent-id",
            user_id=test_user.id
        )
        
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_update_strategy_success(self, db_session, test_strategy):
        """Test successful strategy update"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        result = await service.update_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id,
            name="Updated Strategy Name",
            status="active"
        )
        
        assert result.success is True
        assert result.data["name"] == "Updated Strategy Name"
        assert result.data["status"] == "active"

    @pytest.mark.asyncio
    async def test_delete_strategy_success(self, db_session, test_strategy):
        """Test successful strategy deletion"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        result = await service.delete_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_list_strategies_with_filters(self, db_session, test_strategies, test_user):
        """Test listing strategies with filters"""
        service = UnifiedStrategyService(db=db_session, user_id=test_user.id)
        
        # Test filtering by status
        result = await service.list_strategies(
            user_id=test_user.id,
            filters={"status": "active"},
            limit=10
        )
        
        assert result.success is True
        assert len(result.data) == 2  # Only active strategies
        assert all(s["status"] == "active" for s in result.data)

    @pytest.mark.asyncio
    async def test_execute_strategy_success(self, db_session, test_strategy, mock_event_bus):
        """Test successful strategy execution"""
        with patch('services.unified_strategy_service.get_event_bus', return_value=mock_event_bus):
            service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
            
            result = await service.execute_strategy(
                strategy_id=str(test_strategy.id),
                user_id=test_strategy.user_id
            )
            
            assert result.success is True
            assert result.data["status"] == "running"

    @pytest.mark.asyncio
    async def test_stop_strategy_success(self, db_session, test_strategy):
        """Test stopping strategy execution"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        result = await service.stop_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_strategy_performance_calculation(self, db_session, test_strategy):
        """Test performance metrics calculation"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        result = await service.get_strategy_status(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        assert result.success is True
        assert "performance" in result.data


@pytest.mark.unit
class TestStrategyServiceCaching:
    """Test strategy service caching behavior"""

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, db_session, test_strategy):
        """Test cache is invalidated after update"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        
        # First call should populate cache
        await service.get_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        # Update should invalidate cache
        await service.update_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id,
            name="Updated"
        )
        
        # Second call should fetch fresh data
        result = await service.get_strategy(
            strategy_id=str(test_strategy.id),
            user_id=test_strategy.user_id
        )
        
        assert result.data["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, db_session, test_strategy):
        """Test cache is invalidated after delete"""
        service = UnifiedStrategyService(db=db_session, user_id=test_strategy.user_id)
        strategy_id = str(test_strategy.id)
        
        # Populate cache
        await service.get_strategy(
            strategy_id=strategy_id,
            user_id=test_strategy.user_id
        )
        
        # Delete should invalidate cache
        await service.delete_strategy(
            strategy_id=strategy_id,
            user_id=test_strategy.user_id
        )
        
        # Subsequent get should fail
        result = await service.get_strategy(
            strategy_id=strategy_id,
            user_id=test_strategy.user_id
        )
        
        assert result.success is False
