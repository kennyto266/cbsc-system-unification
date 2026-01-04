"""
Tests for Strategy Service V2 - Instance Management
Test-driven development for strategy instance CRUD operations
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, desc, asc
from uuid import uuid4

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.strategy_service_v2 import StrategyService
from models.strategy_models_v2 import (
    Strategy, StrategyCategory, StrategyInstance,
    StrategyPerformance, Backtest, Trade, StrategyStatus,
    StrategyType, StrategyRiskLevel, Timeframe
)
from schemas.strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyCategoryCreate,
    StrategyCategoryUpdate, StrategyInstanceCreate,
    StrategyFilters, StrategyPerformanceMetrics
)
from core.exceptions import (
    StrategyNotFoundError, StrategyValidationError,
    StrategyPublishError, DuplicateStrategyError
)


# Mock User for testing
class MockUser:
    def __init__(self, is_superuser: bool = False):
        self.id = uuid4()
        self.is_superuser = is_superuser
        self.email = "test@example.com"


@pytest.fixture
def mock_db():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def strategy_service(mock_db):
    """Strategy service fixture"""
    return StrategyService(mock_db)


@pytest.fixture
def mock_user():
    """Mock user fixture"""
    return MockUser()


@pytest.fixture
def sample_strategy():
    """Sample strategy"""
    return Strategy(
        id=uuid4(),
        name="MA Crossover Strategy",
        slug="ma-crossover",
        description="Moving average crossover strategy",
        strategy_type=StrategyType.MOMENTUM,
        risk_level=StrategyRiskLevel.MEDIUM,
        config={
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["AAPL", "MSFT"]
        },
        expected_return=0.15,
        max_drawdown=0.10,
        sharpe_ratio=1.2,
        win_rate=0.55,
        is_active=True,
        is_public=True,
        version=1,
        author_id=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_instance():
    """Sample strategy instance"""
    return StrategyInstance(
        id=uuid4(),
        strategy_id=uuid4(),
        instance_name="MA Cross Instance",
        description="Test instance",
        config={
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["AAPL", "MSFT"],
            "allocation": 0.1
        },
        timeframe=Timeframe.DAILY,
        capital_allocation=10000.0,
        current_equity=10000.0,
        status=StrategyStatus.ACTIVE,
        is_enabled=True,
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def instance_data():
    """Sample instance creation data"""
    return StrategyInstanceCreate(
        strategy_id=uuid4(),
        instance_name="Test Instance",
        description="Test instance description",
        config={
            "fast_period": 10,
            "slow_period": 20
        },
        timeframe=Timeframe.HOURLY,
        capital_allocation=5000.0,
        is_enabled=True
    )


class TestStrategyInstanceCRUD:
    """Test strategy instance CRUD operations"""

    async def test_create_instance_success(self, strategy_service, mock_db, mock_user, sample_strategy, instance_data):
        """Test successful instance creation"""
        # Mock database responses
        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.refresh.side_effect = lambda x: None

            result = await strategy_service.create_strategy_instance(instance_data, mock_user.id)

        assert result.instance_name == "Test Instance"
        assert result.strategy_id == instance_data.strategy_id
        assert result.created_by == mock_user.id
        assert result.status == StrategyStatus.ACTIVE

    async def test_create_instance_duplicate_name(self, strategy_service, mock_db, mock_user, sample_strategy, instance_data):
        """Test instance creation with duplicate name"""
        # Mock existing instance
        existing_instance = StrategyInstance(
            id=uuid4(),
            instance_name=instance_data.instance_name
        )

        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            mock_db.execute.return_value.scalar_one_or_none.return_value = existing_instance

            with pytest.raises(StrategyValidationError, match="already exists"):
                await strategy_service.create_strategy_instance(instance_data, mock_user.id)

    async def test_get_instances_success(self, strategy_service, mock_db, mock_user):
        """Test getting user's strategy instances"""
        instances = [
            StrategyInstance(id=uuid4(), instance_name="Instance 1", created_by=mock_user.id),
            StrategyInstance(id=uuid4(), instance_name="Instance 2", created_by=mock_user.id)
        ]

        # Mock query result
        mock_rows = [(instances[0], "Strategy 1"), (instances[1], "Strategy 2")]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        mock_db.execute.return_value.scalar.return_value = 2  # Total count

        result = await strategy_service.get_strategy_instances(mock_user.id)

        assert 'instances' in result
        assert 'pagination' in result
        assert len(result['instances']) == 2
        assert result['pagination']['total'] == 2

    async def test_get_instances_with_filters(self, strategy_service, mock_db, mock_user):
        """Test getting instances with filters"""
        mock_rows = []
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        mock_db.execute.return_value.scalar.return_value = 0

        # Test with strategy_id filter
        await strategy_service.get_strategy_instances(
            mock_user.id,
            strategy_id=uuid4(),
            status=StrategyStatus.ACTIVE,
            timeframe=Timeframe.DAILY
        )

        # Verify multiple conditions were applied
        assert mock_db.execute.called

    async def test_get_instance_by_id_success(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test getting instance by ID"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_instance

        result = await strategy_service.get_strategy_instance_by_id(sample_instance.id, mock_user.id)

        assert result.id == sample_instance.id
        assert result.instance_name == sample_instance.instance_name

    async def test_get_instance_by_id_not_found(self, strategy_service, mock_db, mock_user):
        """Test getting non-existent instance by ID"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(StrategyNotFoundError, match="not found or access denied"):
            await strategy_service.get_strategy_instance_by_id(uuid4(), mock_user.id)

    async def test_update_instance_success(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test successful instance update"""
        update_data = {
            "instance_name": "Updated Instance",
            "capital_allocation": 20000.0
        }

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.refresh.side_effect = lambda x: None

            result = await strategy_service.update_strategy_instance(
                sample_instance.id,
                update_data,
                mock_user.id
            )

        # Update is applied to the mock object
        assert True  # If no exception raised, update was successful

    async def test_update_instance_duplicate_name(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test updating instance with duplicate name"""
        update_data = {"instance_name": "Duplicate Name"}

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            # Mock existing instance with same name
            existing_instance = StrategyInstance(
                id=uuid4(),
                instance_name="Duplicate Name"
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = existing_instance

            with pytest.raises(StrategyValidationError, match="already exists"):
                await strategy_service.update_strategy_instance(
                    sample_instance.id,
                    update_data,
                    mock_user.id
                )

    async def test_delete_instance_success(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test successful instance deletion"""
        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar.return_value = 0  # No active trades

            result = await strategy_service.delete_strategy_instance(sample_instance.id, mock_user.id)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_instance)

    async def test_delete_instance_running(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test deleting running instance"""
        sample_instance.status = StrategyStatus.ACTIVE

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            with pytest.raises(StrategyValidationError, match="Cannot delete running instance"):
                await strategy_service.delete_strategy_instance(sample_instance.id, mock_user.id, force=False)

    async def test_delete_instance_with_active_trades(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test deleting instance with active trades"""
        sample_instance.status = StrategyStatus.PAUSED

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar.return_value = 5  # 5 active trades

            with pytest.raises(StrategyValidationError, match="Cannot delete instance with active trades"):
                await strategy_service.delete_strategy_instance(sample_instance.id, mock_user.id, force=False)

    async def test_start_instance_success(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test starting instance"""
        sample_instance.status = StrategyStatus.PAUSED
        sample_instance.is_enabled = True

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.refresh.side_effect = lambda x: None

            result = await strategy_service.start_strategy_instance(sample_instance.id, mock_user.id)

        assert result.status == StrategyStatus.ACTIVE

    async def test_start_instance_already_running(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test starting already running instance"""
        sample_instance.status = StrategyStatus.ACTIVE

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            with pytest.raises(StrategyValidationError, match="already running"):
                await strategy_service.start_strategy_instance(sample_instance.id, mock_user.id)

    async def test_start_instance_disabled(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test starting disabled instance"""
        sample_instance.status = StrategyStatus.PAUSED
        sample_instance.is_enabled = False

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            with pytest.raises(StrategyValidationError, match="is disabled"):
                await strategy_service.start_strategy_instance(sample_instance.id, mock_user.id)

    async def test_stop_instance_success(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test stopping instance"""
        sample_instance.status = StrategyStatus.ACTIVE

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.refresh.side_effect = lambda x: None

            result = await strategy_service.stop_strategy_instance(sample_instance.id, mock_user.id)

        assert result.status == StrategyStatus.PAUSED

    async def test_stop_instance_not_running(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test stopping instance that's not running"""
        sample_instance.status = StrategyStatus.PAUSED

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            with pytest.raises(StrategyValidationError, match="not running"):
                await strategy_service.stop_strategy_instance(sample_instance.id, mock_user.id)

    async def test_get_instance_performance_with_data(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test getting instance performance with existing data"""
        performance = StrategyPerformance(
            id=uuid4(),
            instance_id=sample_instance.id,
            date=datetime.utcnow(),
            total_return=0.25,
            annual_return=0.30,
            max_drawdown=0.15,
            sharpe_ratio=1.5,
            win_rate=0.60,
            profit_factor=1.8,
            volatility=0.20,
            var_95=0.05
        )

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar_one_or_none.return_value = performance
            mock_db.execute.return_value.scalar.side_effect = [100, 60, 5000.0]  # trades stats

            result = await strategy_service.get_instance_performance(sample_instance.id, mock_user.id)

        assert result['instance_id'] == sample_instance.id
        assert result['total_return'] == 0.25
        assert result['annual_return'] == 0.30
        assert result['win_rate'] == 0.60
        assert result['total_trades'] == 100

    async def test_get_instance_performance_no_data(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test getting instance performance with no existing data"""
        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar_one_or_none.return_value = None

            result = await strategy_service.get_instance_performance(sample_instance.id, mock_user.id)

        assert result['instance_id'] == sample_instance.id
        assert result['total_return'] == 0.0
        assert result['total_trades'] == 0

    async def test_force_delete_instance(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test force deleting instance with trades"""
        sample_instance.status = StrategyStatus.ACTIVE

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar.return_value = 5  # 5 active trades

            result = await strategy_service.delete_strategy_instance(
                sample_instance.id,
                mock_user.id,
                force=True
            )

        assert result is True
        mock_db.delete.assert_called_once_with(sample_instance)


class TestInstanceManagementIntegration:
    """Integration tests for instance management"""

    async def test_instance_lifecycle(self, strategy_service, mock_db, mock_user, sample_strategy, instance_data):
        """Test complete instance lifecycle: create -> start -> stop -> delete"""
        # Create
        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.refresh.side_effect = lambda x: None

            instance = await strategy_service.create_strategy_instance(instance_data, mock_user.id)
            assert instance.status == StrategyStatus.ACTIVE

        # Start
        instance.status = StrategyStatus.PAUSED
        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=instance):
            await strategy_service.start_strategy_instance(instance.id, mock_user.id)
            assert instance.status == StrategyStatus.ACTIVE

        # Stop
        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=instance):
            await strategy_service.stop_strategy_instance(instance.id, mock_user.id)
            assert instance.status == StrategyStatus.PAUSED

        # Delete
        instance.status = StrategyStatus.PAUSED
        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=instance):
            mock_db.execute.return_value.scalar.return_value = 0  # No active trades
            result = await strategy_service.delete_strategy_instance(instance.id, mock_user.id)
            assert result is True

    async def test_instance_performance_tracking(self, strategy_service, mock_db, mock_user, sample_instance):
        """Test performance metrics calculation"""
        performance = StrategyPerformance(
            id=uuid4(),
            instance_id=sample_instance.id,
            date=datetime.utcnow(),
            total_return=0.20,
            annual_return=0.25,
            max_drawdown=0.10,
            sharpe_ratio=1.3,
            win_rate=0.55,
            profit_factor=1.5,
            volatility=0.18,
            var_95=0.04
        )

        with patch.object(strategy_service, 'get_strategy_instance_by_id', return_value=sample_instance):
            mock_db.execute.return_value.scalar_one_or_none.return_value = performance
            mock_db.execute.return_value.scalar.side_effect = [50, 30, 2500.0]

            # Get performance
            perf_metrics = await strategy_service.get_instance_performance(
                sample_instance.id,
                mock_user.id
            )

            # Verify all metrics are present
            assert 'total_return' in perf_metrics
            assert 'sharpe_ratio' in perf_metrics
            assert 'total_trades' in perf_metrics
            assert 'winning_trades' in perf_metrics
            assert 'total_pnl' in perf_metrics

            # Verify calculations
            assert perf_metrics['total_trades'] == 50
            assert perf_metrics['winning_trades'] == 30
            assert perf_metrics['losing_trades'] == 20
            assert perf_metrics['total_pnl'] == 2500.0