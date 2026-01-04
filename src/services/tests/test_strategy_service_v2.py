"""
Strategy Service v2.0 Tests
Test-driven development for strategy management service
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..strategy_service_v2 import StrategyService
from ...models.strategy_models_v2 import (
    Strategy, StrategyCategory, StrategyType, StrategyStatus, RiskLevel,
    StrategyInstance, StrategyVersion
)
from ...schemas.strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyFilters, PaginationParams,
    StrategyCategoryCreate, StrategyInstanceCreate
)


class TestStrategyService:
    """Test strategy service CRUD operations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create strategy service with mock database"""
        return StrategyService(mock_db)

    @pytest.fixture
    def sample_category(self):
        """Create a sample strategy category"""
        return StrategyCategory(
            id=uuid4(),
            name="Technical Indicators",
            description="Technical analysis strategies"
        )

    @pytest.fixture
    def sample_strategy_data(self):
        """Create sample strategy creation data"""
        return StrategyCreate(
            name="RSI Strategy",
            description="RSI-based trading strategy",
            strategy_type=StrategyType.TECHNICAL,
            risk_level=RiskLevel.MEDIUM,
            config={"rsi_period": 14},
            default_parameters={"oversold": 30},
            tags=["momentum", "technical"],
            expected_return=15.5,
            timeframes=["1h", "4h", "1d"],
            symbols=["AAPL", "GOOGL"],
            min_capital=10000
        )

    def test_create_strategy_success(self, service, mock_db, sample_strategy_data, sample_category):
        """Test successful strategy creation"""
        # Setup mock
        author_id = uuid4()
        created_strategy = Strategy(
            id=uuid4(),
            name=sample_strategy_data.name,
            slug=sample_strategy_data.slug,
            strategy_type=sample_strategy_data.strategy_type,
            author_id=author_id,
            category_id=sample_category.id
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock strategy factory
        with patch('..strategy_service_v2.StrategyFactory') as mock_factory:
            mock_strategy = Mock()
            mock_strategy.get_parameter_schema.return_value = []
            mock_strategy.get_default_parameters.return_value = {}
            mock_factory.create_strategy_from_config.return_value = mock_strategy

            # Execute
            result = service.create_strategy(sample_strategy_data, author_id)

            # Verify
            assert result is not None
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_strategy_duplicate_slug(self, service, mock_db, sample_strategy_data):
        """Test creating strategy with duplicate slug raises error"""
        # Setup mock for integrity error
        mock_db.add.side_effect = IntegrityError("Duplicate slug", None, None)
        mock_db.rollback.return_value = None

        # Execute and verify
        with pytest.raises(Exception):
            service.create_strategy(sample_strategy_data, uuid4())

        mock_db.rollback.assert_called_once()

    def test_get_strategy_found(self, service, mock_db):
        """Test getting strategy that exists"""
        # Setup
        strategy_id = uuid4()
        strategy = Strategy(id=strategy_id, name="Test Strategy")
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = strategy
        mock_db.refresh.return_value = None

        # Execute
        result = service.get_strategy(strategy_id)

        # Verify
        assert result == strategy
        mock_db.query.assert_called_once_with(Strategy)
        mock_query.filter.assert_called_once()

    def test_get_strategy_not_found(self, service, mock_db):
        """Test getting strategy that doesn't exist"""
        # Setup
        strategy_id = uuid4()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Execute
        result = service.get_strategy(strategy_id)

        # Verify
        assert result is None

    def test_get_strategy_with_access_control(self, service, mock_db):
        """Test getting strategy with user access control"""
        # Setup
        strategy_id = uuid4()
        user_id = uuid4()
        strategy = Strategy(id=strategy_id, author_id=user_id)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = [
            Mock(first=Mock(return_value=strategy))  # First filter for ID
        ]

        # Execute
        result = service.get_strategy(strategy_id, user_id)

        # Verify access control filters were applied
        assert mock_query.filter.call_count >= 2
        assert result == strategy

    def test_get_strategies_with_filters(self, service, mock_db):
        """Test getting strategies with filters"""
        # Setup
        filters = StrategyFilters(
            strategy_type=StrategyType.TECHNICAL,
            status=StrategyStatus.ACTIVE,
            risk_level=RiskLevel.MEDIUM,
            search="RSI"
        )
        pagination = PaginationParams(page=1, page_size=20)

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [Strategy(), Strategy()]

        # Execute
        strategies, total = service.get_strategies(filters, pagination)

        # Verify
        assert len(strategies) == 2
        assert total == 50
        assert mock_query.filter.call_count > 0  # Multiple filters applied

    def test_update_strategy_success(self, service, mock_db):
        """Test successful strategy update"""
        # Setup
        strategy_id = uuid4()
        user_id = uuid4()
        strategy = Strategy(id=strategy_id, name="Old Name")
        update_data = StrategyUpdate(name="New Name", status=StrategyStatus.ACTIVE)

        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = service.update_strategy(strategy_id, update_data, user_id)

        # Verify
        assert result.name == "New Name"
        assert result.status == StrategyStatus.ACTIVE
        mock_db.commit.assert_called_once()

    def test_update_strategy_not_found(self, service, mock_db):
        """Test updating strategy that doesn't exist"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(Exception):
            service.update_strategy(uuid4(), StrategyUpdate(), uuid4())

    def test_delete_strategy_success(self, service, mock_db):
        """Test successful strategy deletion (archive)"""
        # Setup
        strategy_id = uuid4()
        user_id = uuid4()
        strategy = Strategy(id=strategy_id, name="Test Strategy")
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        mock_db.commit.return_value = None

        # Execute
        result = service.delete_strategy(strategy_id, user_id)

        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    def test_delete_strategy_not_found(self, service, mock_db):
        """Test deleting strategy that doesn't exist"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(Exception):
            service.delete_strategy(uuid4(), uuid4())


class TestStrategyServiceCategoryOperations:
    """Test strategy service category operations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create strategy service with mock database"""
        return StrategyService(mock_db)

    def test_create_category_success(self, service, mock_db):
        """Test successful category creation"""
        # Setup
        category_data = StrategyCategoryCreate(
            name="Momentum Strategies",
            description="Momentum-based trading strategies",
            icon="trending-up",
            color="#FF6B6B"
        )
        created_category = StrategyCategory(
            id=uuid4(),
            name=category_data.name
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = service.create_category(category_data)

        # Verify
        assert result is not None
        assert result.name == "Momentum Strategies"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_category_tree(self, service, mock_db):
        """Test getting category tree with subcategories"""
        # Setup
        parent_category = StrategyCategory(id=uuid4(), name="Parent")
        child_category = StrategyCategory(
            id=uuid4(),
            name="Child",
            parent_id=parent_category.id
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = [parent_category, child_category]

        # Execute
        result = service.get_category_tree()

        # Verify
        assert len(result) >= 2


class TestStrategyServiceInstanceOperations:
    """Test strategy service instance operations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create strategy service with mock database"""
        return StrategyService(mock_db)

    @pytest.fixture
    def sample_instance_data(self):
        """Create sample instance data"""
        return StrategyInstanceCreate(
            strategy_id=uuid4(),
            name="My Trading Bot",
            capital_allocation=50000,
            parameters={"rsi_period": 20},
            risk_settings={"max_drawdown": 20}
        )

    def test_create_instance_success(self, service, mock_db, sample_instance_data):
        """Test successful instance creation"""
        # Setup
        created_instance = StrategyInstance(
            id=uuid4(),
            name=sample_instance_data.name,
            strategy_id=sample_instance_data.strategy_id
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = service.create_instance(sample_instance_data, uuid4())

        # Verify
        assert result is not None
        assert result.name == "My Trading Bot"
        assert result.capital_allocation == 50000
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_user_instances(self, service, mock_db):
        """Test getting user's strategy instances"""
        # Setup
        user_id = uuid4()
        instances = [StrategyInstance(), StrategyInstance()]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = instances

        # Execute
        result = service.get_user_instances(user_id)

        # Verify
        assert len(result) == 2
        mock_query.filter.assert_called()


class TestStrategyServiceVersionOperations:
    """Test strategy service version operations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create strategy service with mock database"""
        return StrategyService(mock_db)

    def test_create_version_success(self, service, mock_db):
        """Test successful version creation"""
        # Setup
        strategy_id = uuid4()
        version_data = {
            "version": "1.1.0",
            "changelog": "Updated RSI parameters",
            "config": {"rsi_period": 20},
            "is_major": False,
            "is_stable": True
        }
        created_version = StrategyVersion(
            id=uuid4(),
            strategy_id=strategy_id,
            version=version_data["version"]
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = service.create_version(strategy_id, version_data)

        # Verify
        assert result is not None
        assert result.version == "1.1.0"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_strategy_versions(self, service, mock_db):
        """Test getting strategy version history"""
        # Setup
        strategy_id = uuid4()
        versions = [
            StrategyVersion(id=uuid4(), strategy_id=strategy_id, version="1.0.0"),
            StrategyVersion(id=uuid4(), strategy_id=strategy_id, version="1.1.0")
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = versions

        # Execute
        result = service.get_strategy_versions(strategy_id)

        # Verify
        assert len(result) == 2
        assert result[0].version == "1.0.0"
        assert result[1].version == "1.1.0"

    def test_rollback_strategy_to_version(self, service, mock_db):
        """Test rolling back strategy to previous version"""
        # Setup
        strategy_id = uuid4()
        version_id = uuid4()
        user_id = uuid4()

        strategy = Strategy(id=strategy_id, name="Test Strategy")
        version = StrategyVersion(
            id=version_id,
            strategy_id=strategy_id,
            version="1.0.0",
            config={"old_config": True}
        )

        mock_db.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=strategy)),
            Mock(first=Mock(return_value=version))
        ]
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Execute
        result = service.rollback_to_version(strategy_id, version_id, user_id)

        # Verify
        assert result is not None
        mock_db.commit.assert_called_once()


class TestStrategyServiceBusinessLogic:
    """Test strategy service business logic and validations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create strategy service with mock database"""
        return StrategyService(mock_db)

    def test_duplicate_strategy(self, service, mock_db):
        """Test duplicating a strategy"""
        # Setup
        original_id = uuid4()
        user_id = uuid4()
        original = Strategy(
            id=original_id,
            name="Original Strategy",
            slug="original-strategy",
            config={"param": "value"}
        )
        duplicate_data = {"name": "Strategy Copy", "update_parameters": {"new_param": "new_value"}}

        mock_db.query.return_value.filter.return_value.first.return_value = original

        # Mock strategy factory for parameter updates
        with patch('..strategy_service_v2.StrategyFactory') as mock_factory:
            mock_strategy = Mock()
            mock_factory.create_strategy_from_config.return_value = mock_strategy

            # Execute
            result = service.duplicate_strategy(original_id, duplicate_data, user_id)

            # Verify
            assert result is not None
            assert result.name == "Strategy Copy"
            mock_db.add.assert_called()

    def test_validate_strategy_parameters(self, service, mock_db):
        """Test strategy parameter validation"""
        # Setup
        strategy_id = uuid4()
        strategy = Strategy(
            id=strategy_id,
            name="Test Strategy",
            parameter_schema=[
                {
                    "name": "rsi_period",
                    "type": "integer",
                    "default": 14,
                    "required": True,
                    "min_value": 2,
                    "max_value": 50
                }
            ]
        )

        mock_db.query.return_value.filter.return_value.first.return_value = strategy

        # Test valid parameters
        valid_params = {"rsi_period": 20}
        assert service.validate_parameters(strategy_id, valid_params) is True

        # Test invalid parameters (out of range)
        invalid_params = {"rsi_period": 100}
        assert service.validate_parameters(strategy_id, invalid_params) is False

    def test_calculate_strategy_metrics(self, service, mock_db):
        """Test calculating strategy performance metrics"""
        # Setup
        strategy_id = uuid4()
        performance_data = [
            {"date": "2023-01-01", "return": 0.01},
            {"date": "2023-01-02", "return": -0.005},
            {"date": "2023-01-03", "return": 0.02}
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = performance_data

        # Execute
        metrics = service.calculate_strategy_metrics(strategy_id)

        # Verify calculated metrics
        assert "total_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert metrics["total_return"] > 0

    def test_get_strategy_popularity_score(self, service, mock_db):
        """Test calculating strategy popularity score"""
        # Setup
        strategy_id = uuid4()
        strategy = Strategy(
            id=strategy_id,
            usage_count=50,
            rating=4.5,
            rating_count=10,
            backtest_count=5,
            featured=True
        )

        mock_db.query.return_value.filter.return_value.first.return_value = strategy

        # Execute
        score = service.get_popularity_score(strategy_id)

        # Verify score calculation
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score with these metrics


# Integration tests (would require actual database)
class TestStrategyServiceIntegration:
    """Integration tests for strategy service"""

    @pytest.mark.integration
    def test_full_strategy_lifecycle(self, test_db_session):
        """Test complete strategy lifecycle with real database"""
        # This would require actual database setup
        pass

    @pytest.mark.integration
    def test_concurrent_strategy_access(self, test_db_session):
        """Test concurrent strategy access"""
        # This would test thread safety and transaction handling
        pass