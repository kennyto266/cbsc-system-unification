"""
Tests for Strategy Service V2
Test-driven development for strategy CRUD operations
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
def mock_admin_user():
    """Mock admin user fixture"""
    return MockUser(is_superuser=True)


@pytest.fixture
def sample_category():
    """Sample strategy category"""
    return StrategyCategory(
        id=uuid4(),
        name="Technical Analysis",
        slug="technical-analysis",
        description="Technical analysis strategies",
        icon="chart-line",
        sort_order=1,
        is_active=True,
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


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
        config={
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["AAPL", "MSFT"],
            "allocation": 0.1
        },
        timeframe=Timeframe.DAILY,
        status=StrategyStatus.ACTIVE,
        is_enabled=True,
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestStrategyCategoryCRUD:
    """Test strategy category CRUD operations"""

    async def test_create_category_success(self, strategy_service, mock_db, mock_user):
        """Test successful category creation"""
        category_data = StrategyCategoryCreate(
            name="Test Category",
            slug="test-category",
            description="Test description",
            icon="test-icon"
        )

        # Mock database responses
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.get.return_value = None

        # Create mock category
        category = StrategyCategory(
            id=uuid4(),
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            icon=category_data.icon,
            sort_order=0,
            created_by=mock_user.id
        )
        mock_db.refresh.side_effect = lambda x: None

        with patch.object(strategy_service, 'create_category', return_value=category):
            result = await strategy_service.create_category(category_data, mock_user.id)

        assert result.name == "Test Category"
        assert result.slug == "test-category"
        assert result.created_by == mock_user.id

    async def test_create_category_duplicate_slug(self, strategy_service, mock_db):
        """Test category creation with duplicate slug"""
        category_data = StrategyCategoryCreate(
            name="Test Category",
            slug="duplicate-slug",
            description="Test description"
        )

        # Mock existing category
        mock_db.execute.return_value.scalar_one_or_none.return_value = StrategyCategory(
            id=uuid4(),
            name="Existing",
            slug="duplicate-slug"
        )

        with pytest.raises(StrategyValidationError, match="already exists"):
            await strategy_service.create_category(category_data, uuid4())

    async def test_create_category_with_parent(self, strategy_service, mock_db, mock_user, sample_category):
        """Test category creation with parent"""
        category_data = StrategyCategoryCreate(
            name="Subcategory",
            slug="subcategory",
            description="Subcategory test",
            parent_id=sample_category.id
        )

        # Mock database responses
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.get.return_value = sample_category

        category = StrategyCategory(
            id=uuid4(),
            name=category_data.name,
            slug=category_data.slug,
            parent_id=category_data.parent_id,
            created_by=mock_user.id
        )
        mock_db.refresh.side_effect = lambda x: None

        with patch.object(strategy_service, 'create_category', return_value=category):
            result = await strategy_service.create_category(category_data, mock_user.id)

        assert result.parent_id == sample_category.id

    async def test_update_category_success(self, strategy_service, mock_db, sample_category):
        """Test successful category update"""
        update_data = StrategyCategoryUpdate(
            name="Updated Category",
            description="Updated description"
        )

        # Mock database responses
        mock_db.get.return_value = sample_category
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(strategy_service, 'update_category', return_value=sample_category):
            result = await strategy_service.update_category(sample_category.id, update_data)

        assert result.name == sample_category.name

    async def test_update_category_not_found(self, strategy_service, mock_db):
        """Test updating non-existent category"""
        update_data = StrategyCategoryUpdate(name="Updated")

        mock_db.get.return_value = None

        with pytest.raises(StrategyNotFoundError, match="not found"):
            await strategy_service.update_category(uuid4(), update_data)

    async def test_delete_category_success(self, strategy_service, mock_db, sample_category):
        """Test successful category deletion"""
        # Mock database responses
        mock_db.get.return_value = sample_category
        mock_db.execute.return_value.scalar.return_value = 0  # No strategies or subcategories

        result = await strategy_service.delete_category(sample_category.id)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_category)

    async def test_delete_category_with_strategies(self, strategy_service, mock_db, sample_category):
        """Test deleting category with strategies"""
        # Mock database responses
        mock_db.get.return_value = sample_category
        mock_db.execute.return_value.scalar.side_effect = [5, 0]  # 5 strategies, 0 subcategories

        with pytest.raises(StrategyValidationError, match="contains 5 strategies"):
            await strategy_service.delete_category(sample_category.id, force=False)

    async def test_delete_category_force(self, strategy_service, mock_db, sample_category):
        """Test force deleting category with strategies"""
        # Mock database responses
        mock_db.get.return_value = sample_category
        mock_db.execute.return_value.scalar.side_effect = [5, 0]  # 5 strategies, 0 subcategories

        result = await strategy_service.delete_category(sample_category.id, force=True)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_category)

    async def test_get_category_by_id_success(self, strategy_service, mock_db, sample_category):
        """Test getting category by ID"""
        mock_db.get.return_value = sample_category

        result = await strategy_service.get_category_by_id(sample_category.id)

        assert result.id == sample_category.id
        assert result.name == sample_category.name

    async def test_get_category_by_id_not_found(self, strategy_service, mock_db):
        """Test getting non-existent category by ID"""
        mock_db.get.return_value = None

        with pytest.raises(StrategyNotFoundError, match="not found"):
            await strategy_service.get_category_by_id(uuid4())

    async def test_get_category_by_slug_success(self, strategy_service, mock_db, sample_category):
        """Test getting category by slug"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_category
        mock_db.execute.return_value = mock_result

        result = await strategy_service.get_category_by_slug(sample_category.slug)

        assert result.slug == sample_category.slug

    async def test_get_category_tree(self, strategy_service, mock_db):
        """Test getting category tree"""
        categories = [
            StrategyCategory(id=uuid4(), name="Cat1", slug="cat1", parent_id=None, sort_order=1),
            StrategyCategory(id=uuid4(), name="Cat2", slug="cat2", parent_id=None, sort_order=2),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_db.execute.return_value = mock_result
        mock_db.execute.return_value.scalar.return_value = 0  # Strategy count

        with patch.object(strategy_service, 'get_categories', return_value=[]):
            result = await strategy_service.get_category_tree()

        assert isinstance(result, list)

    async def test_get_category_stats(self, strategy_service, mock_db, sample_category):
        """Test getting category statistics"""
        # Mock database responses
        mock_db.get.return_value = sample_category
        mock_db.execute.return_value.scalar.side_effect = [
            10,  # total strategies
            3,   # subcategories
            7,   # active strategies
            0.15 # average return
        ]

        result = await strategy_service.get_category_stats(sample_category.id)

        assert result['category_id'] == sample_category.id
        assert result['category_name'] == sample_category.name
        assert result['total_strategies'] == 10
        assert result['active_strategies'] == 7
        assert result['subcategory_count'] == 3
        assert result['average_annual_return'] == 0.15


class TestStrategyServiceIntegration:
    """Integration tests for strategy service"""

    async def test_category_hierarchy_operations(self, strategy_service, mock_db, mock_user):
        """Test category hierarchy operations"""
        # Create parent category
        parent_data = StrategyCategoryCreate(
            name="Parent",
            slug="parent",
            description="Parent category"
        )

        # Create child category
        child_data = StrategyCategoryCreate(
            name="Child",
            slug="child",
            description="Child category",
            parent_id=uuid4()
        )

        # Test parent creation
        with patch.object(strategy_service, 'create_category') as mock_create:
            mock_create.return_value = StrategyCategory(
                id=uuid4(),
                name="Parent",
                slug="parent",
                created_by=mock_user.id
            )
            parent = await strategy_service.create_category(parent_data, mock_user.id)
            assert parent.name == "Parent"

        # Test child creation with parent
        with patch.object(strategy_service, 'create_category') as mock_create:
            mock_create.return_value = StrategyCategory(
                id=uuid4(),
                name="Child",
                slug="child",
                parent_id=parent.id,
                created_by=mock_user.id
            )
            child = await strategy_service.create_category(child_data, mock_user.id)
            assert child.parent_id == parent.id

    async def test_category_cycle_prevention(self, strategy_service, mock_db, sample_category):
        """Test cycle prevention in category hierarchy"""
        # Mock getting the category
        mock_db.get.return_value = sample_category

        # Mock cycle detection
        with patch.object(strategy_service, '_would_create_cycle', return_value=True):
            update_data = StrategyCategoryUpdate(parent_id=sample_category.id)

            with pytest.raises(StrategyValidationError, match="Cannot move category"):
                await strategy_service.update_category(sample_category.id, update_data)