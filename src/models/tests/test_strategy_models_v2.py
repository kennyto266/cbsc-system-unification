"""
Strategy Models v2.0 Tests
Test-driven development for strategy data models
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from ..strategy_models_v2 import (
    Strategy, StrategyCategory, StrategyVersion, StrategyInstance,
    StrategyPerformance, Backtest, Trade,
    StrategyType, StrategyStatus, RiskLevel, TimeFrame
)


class TestStrategyCategory:
    """Test StrategyCategory model"""

    def test_create_category(self):
        """Test creating a strategy category"""
        category = StrategyCategory(
            name="Technical Indicators",
            description="Strategies based on technical analysis",
            icon="chart-line",
            color="#FF6B6B"
        )

        assert category.id is not None
        assert isinstance(category.id, uuid.UUID)
        assert category.name == "Technical Indicators"
        assert category.description == "Strategies based on technical analysis"
        assert category.icon == "chart-line"
        assert category.color == "#FF6B6B"
        assert category.is_active is True
        assert category.parent_id is None
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_create_subcategory(self, db_session):
        """Test creating a subcategory with parent"""
        # Create parent category
        parent = StrategyCategory(name="Technical")
        db_session.add(parent)
        db_session.commit()

        # Create subcategory
        child = StrategyCategory(
            name="Momentum",
            parent_id=parent.id,
            description="Momentum-based strategies"
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_id == parent.id
        assert child.parent == parent
        assert child in parent.children

    def test_category_unique_name(self, db_session):
        """Test category names must be unique"""
        # Create first category
        category1 = StrategyCategory(name="UniqueName")
        db_session.add(category1)
        db_session.commit()

        # Second category with same name should fail
        category2 = StrategyCategory(name="UniqueName")
        db_session.add(category2)

        with pytest.raises(Exception):  # IntegrityError expected
            db_session.commit()


class TestStrategy:
    """Test Strategy model"""

    @pytest.fixture
    def sample_category(self, db_session):
        """Create a sample category for testing"""
        category = StrategyCategory(name="Test Category")
        db_session.add(category)
        db_session.commit()
        return category

    @pytest.fixture
    def sample_user(self, db_session):
        """Create a sample user for testing"""
        # Create a minimal user object for testing
        class MockUser:
            def __init__(self):
                self.id = uuid.uuid4()
                self.username = "testuser"
                self.email = "test@example.com"

        user = MockUser()
        return user

    def test_create_strategy(self, db_session, sample_category, sample_user):
        """Test creating a strategy"""
        strategy = Strategy(
            name="RSI Mean Reversion",
            slug="rsi-mean-reversion",
            description="RSI-based mean reversion strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=sample_category.id,
            author_id=sample_user.id,
            config={
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70
            },
            default_parameters={
                "period": 14,
                "threshold": 0.5
            },
            risk_level=RiskLevel.MEDIUM,
            expected_return=15.5,
            timeframes=["1h", "4h", "1d"]
        )

        db_session.add(strategy)
        db_session.commit()

        assert strategy.id is not None
        assert strategy.name == "RSI Mean Reversion"
        assert strategy.slug == "rsi-mean-reversion"
        assert strategy.strategy_type == StrategyType.TECHNICAL
        assert strategy.status == StrategyStatus.DRAFT
        assert strategy.category_id == sample_category.id
        assert strategy.category == sample_category
        assert strategy.author_id == sample_user.id
        assert strategy.config["rsi_period"] == 14
        assert strategy.default_parameters["period"] == 14
        assert strategy.risk_level == RiskLevel.MEDIUM
        assert strategy.expected_return == 15.5
        assert "1h" in strategy.timeframes
        assert strategy.usage_count == 0
        assert strategy.is_public is False
        assert strategy.is_template is False

    def test_strategy_slug_validation(self):
        """Test slug format validation"""
        # Valid slugs
        assert Strategy(slug="valid-slug")  # Should not raise
        assert Strategy(slug="slug-with-123-numbers")

        # Invalid slugs
        with pytest.raises(ValueError, match="Slug must contain only lowercase"):
            Strategy(slug="Invalid-Slug")
        with pytest.raises(ValueError, match="Slug must contain only lowercase"):
            Strategy(slug="slug_with_underscores")
        with pytest.raises(ValueError, match="Slug must contain only lowercase"):
            Strategy(slug="slug with spaces")

    def test_strategy_config_validation(self):
        """Test configuration validation"""
        # Valid config
        strategy = Strategy(config={"key": "value"})
        assert strategy.config == {"key": "value"}

        # Invalid config
        with pytest.raises(ValueError, match="Configuration must be a dictionary"):
            Strategy(config="invalid_config")
        with pytest.raises(ValueError, match="Configuration must be a dictionary"):
            Strategy(config=["invalid", "config"])

    def test_strategy_check_constraints(self, db_session, sample_category, sample_user):
        """Test database check constraints"""
        # Test expected_return range
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=sample_category.id,
            author_id=sample_user.id,
            expected_return=150.0  # Invalid: > 1000
        )
        db_session.add(strategy)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

        db_session.rollback()

        # Test win_rate range
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy-2",
            strategy_type=StrategyType.TECHNICAL,
            category_id=sample_category.id,
            author_id=sample_user.id,
            win_rate=150.0  # Invalid: > 100
        )
        db_session.add(strategy)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_strategy_version_relationship(self, db_session, sample_category, sample_user):
        """Test strategy-versions relationship"""
        strategy = Strategy(
            name="Versioned Strategy",
            slug="versioned-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=sample_category.id,
            author_id=sample_user.id
        )
        db_session.add(strategy)
        db_session.commit()

        # Add versions
        version1 = StrategyVersion(
            strategy_id=strategy.id,
            version="1.0.0",
            config={"param": "v1"}
        )
        version2 = StrategyVersion(
            strategy_id=strategy.id,
            version="1.1.0",
            config={"param": "v1.1"}
        )

        db_session.add_all([version1, version2])
        db_session.commit()

        assert len(strategy.versions) == 2
        assert strategy.versions[0].version == "1.0.0"
        assert strategy.versions[1].version == "1.1.0"

    def test_strategy_instance_relationship(self, db_session, sample_category, sample_user):
        """Test strategy-instances relationship"""
        strategy = Strategy(
            name="Instance Strategy",
            slug="instance-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=sample_category.id,
            author_id=sample_user.id
        )
        db_session.add(strategy)
        db_session.commit()

        # Add instances
        instance1 = StrategyInstance(
            strategy_id=strategy.id,
            user_id=sample_user.id,
            name="Instance 1",
            capital_allocation=10000
        )
        instance2 = StrategyInstance(
            strategy_id=strategy.id,
            user_id=sample_user.id,
            name="Instance 2",
            capital_allocation=20000
        )

        db_session.add_all([instance1, instance2])
        db_session.commit()

        assert len(strategy.instances) == 2
        assert strategy.instances[0].capital_allocation == 10000
        assert strategy.instances[1].capital_allocation == 20000


class TestStrategyVersion:
    """Test StrategyVersion model"""

    @pytest.fixture
    def sample_strategy(self, db_session):
        """Create a sample strategy for testing"""
        from ..database import User
        category = StrategyCategory(name="Test Category")
        user = User(id=uuid.uuid4(), username="testuser", email="test@example.com")
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=category.id,
            author_id=user.id
        )
        db_session.add_all([category, user, strategy])
        db_session.commit()
        return strategy

    def test_create_version(self, db_session, sample_strategy):
        """Test creating a strategy version"""
        version = StrategyVersion(
            strategy_id=sample_strategy.id,
            version="1.0.0",
            changelog="Initial version",
            config={
                "param1": "value1",
                "param2": "value2"
            },
            parameters={
                "period": 14,
                "threshold": 0.5
            },
            is_major=True,
            is_stable=True
        )

        db_session.add(version)
        db_session.commit()

        assert version.id is not None
        assert version.strategy_id == sample_strategy.id
        assert version.version == "1.0.0"
        assert version.changelog == "Initial version"
        assert version.config["param1"] == "value1"
        assert version.parameters["period"] == 14
        assert version.is_major is True
        assert version.is_stable is True
        assert version.created_at is not None

    def test_unique_version_per_strategy(self, db_session, sample_strategy):
        """Test version uniqueness constraint"""
        # Create first version
        version1 = StrategyVersion(
            strategy_id=sample_strategy.id,
            version="1.0.0",
            config={}
        )
        db_session.add(version1)
        db_session.commit()

        # Second version with same number should fail
        version2 = StrategyVersion(
            strategy_id=sample_strategy.id,
            version="1.0.0",
            config={}
        )
        db_session.add(version2)

        with pytest.raises(Exception):  # UniqueConstraint violation
            db_session.commit()


class TestStrategyInstance:
    """Test StrategyInstance model"""

    @pytest.fixture
    def sample_strategy(self, db_session):
        """Create a sample strategy for testing"""
        category = StrategyCategory(name="Test Category")

        # Create mock user
        class MockUser:
            def __init__(self):
                self.id = uuid.uuid4()

        user = MockUser()
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=category.id,
            author_id=user.id
        )
        db_session.add(category)
        db_session.commit()
        return strategy, user

    def test_create_instance(self, db_session, sample_strategy):
        """Test creating a strategy instance"""
        strategy, user = sample_strategy

        instance = StrategyInstance(
            strategy_id=strategy.id,
            user_id=user.id,
            name="My Trading Instance",
            parameters={
                "rsi_period": 20,
                "threshold": 0.6
            },
            symbols=["AAPL", "GOOGL", "MSFT"],
            capital_allocation=50000,
            position_sizing={
                "method": "equal_weight",
                "max_position": 0.3
            },
            risk_settings={
                "max_drawdown": 20,
                "var_limit": 1000
            },
            is_paper_trading=True,
            auto_trade=False
        )

        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert instance.strategy_id == strategy.id
        assert instance.user_id == user.id
        assert instance.name == "My Trading Instance"
        assert instance.parameters["rsi_period"] == 20
        assert "AAPL" in instance.symbols
        assert instance.capital_allocation == 50000
        assert instance.status == "stopped"
        assert instance.is_paper_trading is True
        assert instance.auto_trade is False
        assert instance.start_equity is None
        assert instance.current_equity is None

    def test_instance_performance_tracking(self, db_session, sample_strategy):
        """Test instance performance tracking fields"""
        strategy, user = sample_strategy

        instance = StrategyInstance(
            strategy_id=strategy.id,
            user_id=user.id,
            name="Performance Test",
            start_equity=100000,
            current_equity=115000,
            total_return=0.15,
            daily_return=0.005,
            current_drawdown=5.5,
            var_95=2000
        )

        db_session.add(instance)
        db_session.commit()

        assert instance.start_equity == 100000
        assert instance.current_equity == 115000
        assert instance.total_return == 0.15
        assert instance.daily_return == 0.005
        assert instance.current_drawdown == 5.5
        assert instance.var_95 == 2000

    def test_instance_state_fields(self, db_session, sample_strategy):
        """Test instance state management fields"""
        strategy, user = sample_strategy

        instance = StrategyInstance(
            strategy_id=strategy.id,
            user_id=user.id,
            name="State Test",
            status="running",
            last_signal={
                "type": "BUY",
                "symbol": "AAPL",
                "price": 150.25,
                "confidence": 0.8
            },
            current_positions=[
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 148.50
                }
            ]
        )

        db_session.add(instance)
        db_session.commit()

        assert instance.status == "running"
        assert instance.last_signal["type"] == "BUY"
        assert instance.last_signal["symbol"] == "AAPL"
        assert len(instance.current_positions) == 1
        assert instance.current_positions[0]["symbol"] == "AAPL"
        assert instance.current_positions[0]["quantity"] == 100


class TestStrategyPerformance:
    """Test StrategyPerformance model"""

    @pytest.fixture
    def sample_strategy(self, db_session):
        """Create a sample strategy for testing"""
        from ..database import User
        category = StrategyCategory(name="Test Category")
        user = User(id=uuid.uuid4(), username="testuser", email="test@example.com")
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=category.id,
            author_id=user.id
        )
        db_session.add_all([category, user, strategy])
        db_session.commit()
        return strategy

    def test_create_performance_record(self, db_session, sample_strategy):
        """Test creating a performance record"""
        performance = StrategyPerformance(
            strategy_id=sample_strategy.id,
            date=datetime.now(timezone.utc),
            daily_return=0.005,
            cumulative_return=0.15,
            annualized_return=0.18,
            volatility=0.12,
            max_drawdown=8.5,
            current_drawdown=2.3,
            sharpe_ratio=1.45,
            sortino_ratio=1.92,
            calmar_ratio=2.11,
            benchmark_return=0.10,
            alpha=0.08,
            beta=0.95,
            tracking_error=0.04,
            win_rate=0.62,
            profit_factor=1.85,
            avg_trade_return=0.0035,
            trade_count=156,
            equity=115000,
            exposure=0.85,
            leverage=1.0
        )

        db_session.add(performance)
        db_session.commit()

        assert performance.id is not None
        assert performance.strategy_id == sample_strategy.id
        assert performance.daily_return == 0.005
        assert performance.cumulative_return == 0.15
        assert performance.annualized_return == 0.18
        assert performance.volatility == 0.12
        assert performance.max_drawdown == 8.5
        assert performance.sharpe_ratio == 1.45
        assert performance.win_rate == 0.62
        assert performance.trade_count == 156
        assert performance.equity == 115000

    def test_unique_strategy_date(self, db_session, sample_strategy):
        """Test unique constraint on strategy_id + date"""
        date = datetime.now(timezone.utc)

        # Create first record
        perf1 = StrategyPerformance(
            strategy_id=sample_strategy.id,
            date=date,
            daily_return=0.01
        )
        db_session.add(perf1)
        db_session.commit()

        # Second record with same date should fail
        perf2 = StrategyPerformance(
            strategy_id=sample_strategy.id,
            date=date,
            daily_return=0.02
        )
        db_session.add(perf2)

        with pytest.raises(Exception):  # UniqueConstraint violation
            db_session.commit()


class TestBacktest:
    """Test Backtest model"""

    @pytest.fixture
    def sample_strategy(self, db_session):
        """Create a sample strategy for testing"""
        category = StrategyCategory(name="Test Category")

        # Create mock user
        class MockUser:
            def __init__(self):
                self.id = uuid.uuid4()

        user = MockUser()
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=category.id,
            author_id=user.id
        )
        db_session.add(category)
        db_session.commit()
        return strategy, user

    def test_create_backtest(self, db_session, sample_strategy):
        """Test creating a backtest"""
        strategy, user = sample_strategy

        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)

        backtest = Backtest(
            strategy_id=strategy.id,
            user_id=user.id,
            name="2023 Annual Backtest",
            parameters={
                "rsi_period": 14,
                "threshold": 0.5
            },
            symbols=["AAPL", "GOOGL", "MSFT"],
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000,
            final_equity=118500,
            total_return=0.185,
            annualized_return=0.185,
            max_drawdown=12.5,
            volatility=0.15,
            var_95=2500,
            expected_shortfall=3200,
            sharpe_ratio=1.23,
            sortino_ratio=1.67,
            calmar_ratio=1.48,
            total_trades=89,
            winning_trades=52,
            losing_trades=37,
            win_rate=0.584,
            avg_win=0.028,
            avg_loss=-0.018,
            profit_factor=2.11,
            benchmark_return=0.10,
            alpha=0.085,
            beta=0.92,
            information_ratio=0.95,
            equity_curve=[
                {"date": "2023-01-01", "equity": 100000},
                {"date": "2023-12-31", "equity": 118500}
            ],
            trade_history=[
                {
                    "symbol": "AAPL",
                    "direction": "long",
                    "entry": "2023-01-15",
                    "exit": "2023-02-01",
                    "pnl": 1500
                }
            ],
            computation_time=45.7,
            status="completed"
        )

        db_session.add(backtest)
        db_session.commit()

        assert backtest.id is not None
        assert backtest.strategy_id == strategy.id
        assert backtest.user_id == user.id
        assert backtest.name == "2023 Annual Backtest"
        assert backtest.initial_capital == 100000
        assert backtest.final_equity == 118500
        assert backtest.total_return == 0.185
        assert backtest.sharpe_ratio == 1.23
        assert backtest.win_rate == 0.584
        assert backtest.profit_factor == 2.11
        assert backtest.status == "completed"
        assert backtest.computation_time == 45.7
        assert len(backtest.equity_curve) == 2
        assert len(backtest.trade_history) == 1


class TestTrade:
    """Test Trade model"""

    @pytest.fixture
    def sample_instance(self, db_session):
        """Create a sample strategy instance for testing"""
        category = StrategyCategory(name="Test Category")

        # Create mock user
        class MockUser:
            def __init__(self):
                self.id = uuid.uuid4()

        user = MockUser()
        strategy = Strategy(
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            category_id=category.id,
            author_id=user.id
        )
        instance = StrategyInstance(
            strategy_id=strategy.id,
            user_id=user.id,
            name="Test Instance"
        )
        db_session.add_all([category, strategy, instance])
        db_session.commit()
        return instance

    def test_create_trade(self, db_session, sample_instance):
        """Test creating a trade"""
        entry_time = datetime(2023, 6, 15, 10, 30, tzinfo=timezone.utc)
        exit_time = datetime(2023, 6, 20, 14, 45, tzinfo=timezone.utc)

        trade = Trade(
            instance_id=sample_instance.id,
            symbol="AAPL",
            direction="long",
            quantity=100,
            entry_price=150.25,
            exit_price=155.80,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_value=15025.0,
            exit_value=15580.0,
            gross_pnl=555.0,
            fees=5.55,
            net_pnl=549.45,
            return_pct=0.0366,
            exit_reason="signal",
            signal_confidence=0.82,
            strategy_notes="RSI oversold signal"
        )

        db_session.add(trade)
        db_session.commit()

        assert trade.id is not None
        assert trade.instance_id == sample_instance.id
        assert trade.symbol == "AAPL"
        assert trade.direction == "long"
        assert trade.quantity == 100
        assert trade.entry_price == 150.25
        assert trade.exit_price == 155.80
        assert trade.entry_time == entry_time
        assert trade.exit_time == exit_time
        assert trade.entry_value == 15025.0
        assert trade.exit_value == 15580.0
        assert trade.gross_pnl == 555.0
        assert trade.fees == 5.55
        assert trade.net_pnl == 549.45
        assert trade.return_pct == 0.0366
        assert trade.exit_reason == "signal"
        assert trade.signal_confidence == 0.82
        assert trade.strategy_notes == "RSI oversold signal"

    def test_open_trade(self, db_session, sample_instance):
        """Test creating an open trade (without exit)"""
        trade = Trade(
            instance_id=sample_instance.id,
            symbol="GOOGL",
            direction="short",
            quantity=50,
            entry_price=2750.50,
            entry_time=datetime.now(timezone.utc),
            entry_value=137525.0
        )

        db_session.add(trade)
        db_session.commit()

        assert trade.exit_price is None
        assert trade.exit_time is None
        assert trade.exit_value is None
        assert trade.gross_pnl is None
        assert trade.fees == 0
        assert trade.net_pnl is None
        assert trade.return_pct is None
        assert trade.exit_reason is None

    def test_trade_constraints(self, db_session, sample_instance):
        """Test trade constraint validations"""
        # Test quantity constraint
        trade = Trade(
            instance_id=sample_instance.id,
            symbol="MSFT",
            direction="long",
            quantity=-10,  # Invalid: negative quantity
            entry_price=300.0,
            entry_time=datetime.now(timezone.utc)
        )
        db_session.add(trade)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

        db_session.rollback()

        # Test entry_price constraint
        trade = Trade(
            instance_id=sample_instance.id,
            symbol="MSFT",
            direction="long",
            quantity=100,
            entry_price=0,  # Invalid: zero price
            entry_time=datetime.now(timezone.utc)
        )
        db_session.add(trade)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()


# Fixtures for database session
@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ..strategy_models_v2 import Base

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()