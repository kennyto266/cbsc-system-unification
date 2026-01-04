"""
Strategy Schemas Tests
Test-driven development for strategy management Pydantic schemas
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from ..strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyCategoryCreate, StrategyCategoryUpdate, StrategyCategoryResponse,
    StrategyInstanceCreate, StrategyInstanceUpdate, StrategyInstanceResponse,
    TradeCreate, TradeResponse, StrategyFilters, PaginationParams,
    StrategyParameterSchema, StrategyListResponse,
    DirectionEnum, ExitReasonEnum,
    StrategyType, StrategyStatus, RiskLevel, TimeFrame
)


class TestStrategyParameterSchema:
    """Test strategy parameter schema validation"""

    def test_valid_parameter_schemas(self):
        """Test valid parameter schema definitions"""
        # String parameter
        param = StrategyParameterSchema(
            name="symbol",
            type="string",
            default="AAPL",
            description="Trading symbol",
            required=True
        )
        assert param.name == "symbol"
        assert param.type == "string"
        assert param.default == "AAPL"

        # Numeric parameter with range
        param = StrategyParameterSchema(
            name="rsi_period",
            type="integer",
            default=14,
            min_value=2,
            max_value=50,
            description="RSI period"
        )
        assert param.min_value == 2
        assert param.max_value == 50

        # Boolean parameter
        param = StrategyParameterSchema(
            name="enable_stop_loss",
            type="boolean",
            default=True,
            description="Enable stop loss"
        )
        assert param.default is True

        # Enum-like parameter with options
        param = StrategyParameterSchema(
            name="timeframe",
            type="string",
            default="1h",
            options=["1m", "5m", "15m", "1h", "4h", "1d"],
            description="Timeframe"
        )
        assert param.options == ["1m", "5m", "15m", "1h", "4h", "1d"]

    def test_invalid_parameter_schema(self):
        """Test invalid parameter schema validations"""
        # Numeric constraints on non-numeric type
        with pytest.raises(ValueError, match="Numeric constraints only valid"):
            StrategyParameterSchema(
                name="text_param",
                type="string",
                default="test",
                min_value=1  # Invalid for string type
            )

        # Default value type mismatch
        with pytest.raises(ValueError, match="Default value type"):
            StrategyParameterSchema(
                name="number_param",
                type="number",
                default="not_a_number"  # String for numeric type
            )


class TestStrategyCategorySchemas:
    """Test strategy category schemas"""

    def test_category_create_valid(self):
        """Test valid category creation"""
        category = StrategyCategoryCreate(
            name="Technical Indicators",
            description="Strategies based on technical analysis",
            icon="chart-line",
            color="#FF6B6B",
            sort_order=10
        )
        assert category.name == "Technical Indicators"
        assert category.icon == "chart-line"
        assert category.color == "#FF6B6B"
        assert category.sort_order == 10

    def test_category_create_invalid(self):
        """Test invalid category creation"""
        # Empty name
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            StrategyCategoryCreate(name="   ")

        # Invalid color format
        with pytest.raises(ValueError, match="String should match pattern"):
            StrategyCategoryCreate(
                name="Test",
                color="invalid_color"
            )

        # Negative sort order
        with pytest.raises(ValueError):
            StrategyCategoryCreate(
                name="Test",
                sort_order=-1
            )

    def test_category_update(self):
        """Test category update"""
        update = StrategyCategoryUpdate(
            name="Updated Name",
            color="#00FF00"
        )
        assert update.name == "Updated Name"
        assert update.color == "#00FF00"

    def test_category_response(self):
        """Test category response schema"""
        now = datetime.now(timezone.utc)
        category_id = uuid4()

        response = StrategyCategoryResponse(
            id=category_id,
            name="Test Category",
            description="Test description",
            created_at=now,
            updated_at=now,
            children=[],
            strategy_count=5
        )
        assert response.id == category_id
        assert response.name == "Test Category"
        assert response.strategy_count == 5


class TestStrategySchemas:
    """Test strategy schemas"""

    def test_strategy_create_valid(self):
        """Test valid strategy creation"""
        strategy = StrategyCreate(
            name="RSI Mean Reversion",
            description="RSI-based mean reversion strategy",
            strategy_type=StrategyType.TECHNICAL,
            config={"rsi_period": 14},
            default_parameters={"threshold": 0.5},
            risk_level=RiskLevel.MEDIUM,
            expected_return=15.5,
            timeframes=[TimeFrame.HOUR_1, TimeFrame.DAY_1],
            symbols=["AAPL", "GOOGL"],
            min_capital=10000
        )
        assert strategy.name == "RSI Mean Reversion"
        assert strategy.strategy_type == StrategyType.TECHNICAL
        assert strategy.slug == "rsi-mean-reversion"  # Auto-generated
        assert strategy.config["rsi_period"] == 14
        assert strategy.expected_return == 15.5
        assert "AAPL" in strategy.symbols
        assert strategy.min_capital == 10000

    def test_strategy_create_with_slug(self):
        """Test strategy creation with custom slug"""
        strategy = StrategyCreate(
            name="Custom Strategy",
            slug="custom-slug-123",
            strategy_type=StrategyType.MOMENTUM
        )
        assert strategy.slug == "custom-slug-123"

    def test_strategy_create_invalid_slug(self):
        """Test strategy creation with invalid slug"""
        with pytest.raises(ValueError, match="String should match pattern"):
            StrategyCreate(
                name="Test",
                slug="Invalid Slug!",
                strategy_type=StrategyType.TECHNICAL
            )

    def test_strategy_create_invalid_values(self):
        """Test strategy creation with invalid values"""
        # Empty name
        with pytest.raises(ValueError, match="Strategy name cannot be empty"):
            StrategyCreate(
                name="   ",
                strategy_type=StrategyType.TECHNICAL
            )

        # Expected return out of range
        with pytest.raises(ValueError):
            StrategyCreate(
                name="Test",
                strategy_type=StrategyType.TECHNICAL,
                expected_return=1500  # > 1000
            )

        # Win rate out of range
        with pytest.raises(ValueError):
            StrategyCreate(
                name="Test",
                strategy_type=StrategyType.TECHNICAL,
                win_rate=150  # > 100
            )

        # Negative capital
        with pytest.raises(ValueError):
            StrategyCreate(
                name="Test",
                strategy_type=StrategyType.TECHNICAL,
                min_capital=-1000
            )

    def test_strategy_update(self):
        """Test strategy update"""
        update = StrategyUpdate(
            name="Updated Strategy",
            status=StrategyStatus.ACTIVE,
            expected_return=20.0,
            featured=True
        )
        assert update.name == "Updated Strategy"
        assert update.status == StrategyStatus.ACTIVE
        assert update.featureed is True

    def test_strategy_response(self):
        """Test strategy response schema"""
        now = datetime.now(timezone.utc)
        strategy_id = uuid4()
        author_id = uuid4()

        response = StrategyResponse(
            id=strategy_id,
            name="Test Strategy",
            slug="test-strategy",
            strategy_type=StrategyType.TECHNICAL,
            status=StrategyStatus.DRAFT,
            author_id=author_id,
            created_at=now,
            updated_at=now,
            rating=4.5,
            rating_count=10,
            backtest_count=5,
            avg_return=0.15,
            popularity_score=85.5
        )
        assert response.id == strategy_id
        assert response.name == "Test Strategy"
        assert response.rating == 4.5
        assert response.backtest_count == 5


class TestStrategyInstanceSchemas:
    """Test strategy instance schemas"""

    def test_instance_create_valid(self):
        """Test valid instance creation"""
        instance = StrategyInstanceCreate(
            strategy_id=uuid4(),
            name="My Trading Bot",
            parameters={"rsi_period": 20},
            symbols=["AAPL", "MSFT", "GOOGL"],
            capital_allocation=50000,
            risk_settings={"max_drawdown": 20},
            is_paper_trading=True,
            auto_trade=False
        )
        assert instance.name == "My Trading Bot"
        assert instance.parameters["rsi_period"] == 20
        assert len(instance.symbols) == 3
        assert instance.capital_allocation == 50000
        assert instance.is_paper_trading is True

    def test_instance_create_invalid(self):
        """Test invalid instance creation"""
        # Empty name
        with pytest.raises(ValueError, match="Instance name cannot be empty"):
            StrategyInstanceCreate(
                strategy_id=uuid4(),
                name="   ",
                capital_allocation=1000
            )

        # Zero or negative capital
        with pytest.raises(ValueError):
            StrategyInstanceCreate(
                strategy_id=uuid4(),
                name="Test",
                capital_allocation=0
            )

    def test_instance_update(self):
        """Test instance update"""
        update = StrategyInstanceUpdate(
            name="Updated Instance",
            capital_allocation=75000,
            status="running",
            auto_trade=True
        )
        assert update.name == "Updated Instance"
        assert update.capital_allocation == 75000
        assert update.status == "running"

    def test_instance_response(self):
        """Test instance response schema"""
        now = datetime.now(timezone.utc)
        instance_id = uuid4()
        strategy_id = uuid4()
        user_id = uuid4()

        response = StrategyInstanceResponse(
            id=instance_id,
            strategy_id=strategy_id,
            user_id=user_id,
            name="Test Instance",
            capital_allocation=100000,
            status="running",
            start_equity=100000,
            current_equity=115000,
            total_return=0.15,
            roi_percentage=15.0,
            is_paper_trading=True,
            created_at=now,
            started_at=now
        )
        assert response.id == instance_id
        assert response.capital_allocation == 100000
        assert response.roi_percentage == 15.0


class TestTradeSchemas:
    """Test trade schemas"""

    def test_trade_create_valid(self):
        """Test valid trade creation"""
        entry_time = datetime.now(timezone.utc)
        exit_time = entry_time + timedelta(days=5)

        trade = TradeCreate(
            instance_id=uuid4(),
            symbol="AAPL",
            direction=DirectionEnum.LONG,
            quantity=100,
            entry_price=150.25,
            entry_time=entry_time,
            exit_price=155.80,
            exit_time=exit_time,
            exit_reason=ExitReasonEnum.TAKE_PROFIT,
            signal_confidence=0.85
        )
        assert trade.symbol == "AAPL"
        assert trade.direction == DirectionEnum.LONG
        assert trade.quantity == 100
        assert trade.entry_price == 150.25
        assert trade.exit_price == 155.80
        assert trade.exit_reason == ExitReasonEnum.TAKE_PROFIT
        assert trade.signal_confidence == 0.85

    def test_trade_create_open(self):
        """Test creating an open trade (without exit)"""
        trade = TradeCreate(
            instance_id=uuid4(),
            symbol="GOOGL",
            direction=DirectionEnum.SHORT,
            quantity=50,
            entry_price=2750.50,
            entry_time=datetime.now(timezone.utc)
        )
        assert trade.exit_price is None
        assert trade.exit_time is None
        assert trade.exit_reason is None

    def test_trade_create_invalid(self):
        """Test invalid trade creation"""
        # Empty symbol
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            TradeCreate(
                instance_id=uuid4(),
                symbol="   ",
                direction=DirectionEnum.LONG,
                quantity=100,
                entry_price=100,
                entry_time=datetime.now()
            )

        # Negative quantity
        with pytest.raises(ValueError):
            TradeCreate(
                instance_id=uuid4(),
                symbol="AAPL",
                direction=DirectionEnum.LONG,
                quantity=-10,
                entry_price=100,
                entry_time=datetime.now()
            )

        # Zero price
        with pytest.raises(ValueError):
            TradeCreate(
                instance_id=uuid4(),
                symbol="AAPL",
                direction=DirectionEnum.LONG,
                quantity=100,
                entry_price=0,
                entry_time=datetime.now()
            )

        # Exit time before entry time
        entry_time = datetime.now()
        exit_time = entry_time - timedelta(hours=1)

        with pytest.raises(ValueError, match="Exit time must be after entry time"):
            TradeCreate(
                instance_id=uuid4(),
                symbol="AAPL",
                direction=DirectionEnum.LONG,
                quantity=100,
                entry_price=100,
                entry_time=entry_time,
                exit_price=110,
                exit_time=exit_time
            )

        # Mismatched exit fields
        with pytest.raises(ValueError, match="Exit price and exit time must both be provided"):
            TradeCreate(
                instance_id=uuid4(),
                symbol="AAPL",
                direction=DirectionEnum.LONG,
                quantity=100,
                entry_price=100,
                entry_time=datetime.now(),
                exit_price=110  # Without exit_time
            )

    def test_trade_response(self):
        """Test trade response schema"""
        now = datetime.now(timezone.utc)
        trade_id = uuid4()
        instance_id = uuid4()

        response = TradeResponse(
            id=trade_id,
            instance_id=instance_id,
            symbol="MSFT",
            direction="long",
            quantity=100,
            entry_price=300.50,
            exit_price=310.25,
            entry_time=now,
            exit_time=now + timedelta(days=3),
            gross_pnl=975,
            fees=9.75,
            net_pnl=965.25,
            return_pct=0.0321,
            exit_reason="signal",
            created_at=now,
            is_open=False,
            pnl_percentage=3.21
        )
        assert response.id == trade_id
        assert response.symbol == "MSFT"
        assert response.net_pnl == 965.25
        assert response.is_open is False


class TestFilterAndPaginationSchemas:
    """Test filter and pagination schemas"""

    def test_strategy_filters(self):
        """Test strategy filters"""
        filters = StrategyFilters(
            strategy_type=StrategyType.TECHNICAL,
            status=StrategyStatus.ACTIVE,
            risk_level=RiskLevel.MEDIUM,
            is_public=True,
            tags=["momentum", "rsi"],
            min_rating=4.0,
            min_return=0.10,
            search="RSI"
        )
        assert filters.strategy_type == StrategyType.TECHNICAL
        assert filters.tags == ["momentum", "rsi"]
        assert filters.min_rating == 4.0

    def test_pagination_params(self):
        """Test pagination parameters"""
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50
        assert params.offset == 50  # (2-1)*50

        # Default values
        default_params = PaginationParams()
        assert default_params.page == 1
        assert default_params.page_size == 20
        assert default_params.offset == 0

    def test_pagination_invalid(self):
        """Test invalid pagination parameters"""
        # Invalid page
        with pytest.raises(ValueError):
            PaginationParams(page=0)

        # Invalid page size
        with pytest.raises(ValueError):
            PaginationParams(page_size=0)

        with pytest.raises(ValueError):
            PaginationParams(page_size=101)

        # Invalid sort order
        with pytest.raises(ValueError):
            PaginationParams(sort_order="invalid")

    def test_strategy_list_response(self):
        """Test strategy list response"""
        response = StrategyListResponse(
            items=[],
            total=100,
            page=2,
            page_size=20,
            total_pages=5,
            has_next=True,
            has_prev=True
        )
        assert response.total == 100
        assert response.page == 2
        assert response.has_next is True
        assert response.has_prev is True


class TestValidationEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_maximum_values(self):
        """Test maximum allowed values"""
        strategy = StrategyCreate(
            name="A" * 200,  # Max length name
            description="A" * 2000,  # Max length description
            strategy_type=StrategyType.TECHNICAL,
            expected_return=1000,  # Max expected return
            max_drawdown=100,  # Max drawdown
            win_rate=100,  # Max win rate
            symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
            min_capital=999999999  # Large number
        )
        assert len(strategy.name) == 200
        assert strategy.expected_return == 1000

    def test_minimum_values(self):
        """Test minimum allowed values"""
        strategy = StrategyCreate(
            name="Min",
            strategy_type=StrategyType.TECHNICAL,
            expected_return=-100,  # Min expected return
            min_return=-100,
            capital_allocation=0.01,  # Minimum positive
            quantity=0.01,  # Minimum positive for trades
            entry_price=0.01  # Minimum positive price
        )
        assert strategy.expected_return == -100

    def test_unicode_handling(self):
        """Test Unicode character handling"""
        strategy = StrategyCreate(
            name="量化交易策略 🚀",
            description="Multi-language description with 中文, español, and русский",
            tags=["漢字", "español", "русский"],
            strategy_type=StrategyType.TECHNICAL
        )
        assert "量化" in strategy.name
        assert "中文" in strategy.description

    def test_json_field_validation(self):
        """Test JSON field validation"""
        # Valid JSON structures
        strategy = StrategyCreate(
            name="JSON Test",
            strategy_type=StrategyType.TECHNICAL,
            config={"nested": {"key": "value"}, "array": [1, 2, 3]},
            default_parameters={"param": None, "bool": True, "number": 3.14}
        )
        assert strategy.config["nested"]["key"] == "value"
        assert strategy.default_parameters["bool"] is True

        # Invalid JSON (should be dict)
        with pytest.raises(ValueError, match="Configuration and parameters must be dictionaries"):
            StrategyCreate(
                name="Invalid JSON",
                strategy_type=StrategyType.TECHNICAL,
                config="not_a_dict"
            )