"""
Tests for Strategy Templates

Test suite for strategy template system including
base template class and all concrete implementations.
"""

import pytest

from cbsc_strategy_sdk.claude.templates import (
    StrategyTemplate,
    StrategyType,
    MomentumTemplate,
    MeanReversionTemplate,
    ArbitrageTemplate,
    PairTradingTemplate,
    MLStrategyTemplate,
    TemplateFactory,
)


class TestStrategyType:
    """Test StrategyType enum."""

    def test_all_types_defined(self):
        """Test all expected strategy types are defined."""
        assert StrategyType.MOMENTUM.value == "momentum"
        assert StrategyType.MEAN_REVERSION.value == "mean_reversion"
        assert StrategyType.ARBITRAGE.value == "arbitrage"
        assert StrategyType.PAIR_TRADING.value == "pair_trading"
        assert StrategyType.ML_STRATEGY.value == "ml_strategy"


class TestMomentumTemplate:
    """Test MomentumTemplate implementation."""

    @pytest.fixture
    def template(self):
        return MomentumTemplate()

    def test_strategy_type(self, template):
        assert template.get_strategy_type() == StrategyType.MOMENTUM

    def test_required_parameters(self, template):
        required = template.get_required_parameters()
        assert "lookback_period" in required
        assert "threshold" in required
        assert "position_size" in required

    def test_optional_parameters(self, template):
        optional = template.get_optional_parameters()
        assert "use_rsi" in optional
        assert "rsi_period" in optional

    def test_generate_code_basic(self, template):
        parameters = {
            "name": "TestMomentum",
            "lookback_period": 20,
            "threshold": 0.02,
            "position_size": 0.1,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "TestMomentum" in code
        assert "lookback_period = 20" in code
        assert "threshold = 0.02" in code
        assert "def generate_signals" in code
        assert "def backtest" in code

    def test_generate_code_with_rsi(self, template):
        parameters = {
            "name": "TestMomentum",
            "lookback_period": 15,
            "threshold": 0.03,
            "position_size": 0.2,
            "use_rsi": True,
            "rsi_period": 14,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "_calculate_rsi" in code
        assert "rsi_period = 14" in code

    def test_parameter_validation(self, template):
        # Valid parameters
        valid, error = template.validate_parameters({
            "lookback_period": 20,
            "threshold": 0.02,
            "position_size": 0.1,
        })
        assert valid is True
        assert error is None

        # Missing required parameter
        valid, error = template.validate_parameters({
            "lookback_period": 20,
        })
        assert valid is False
        assert "Missing required parameter" in error

        # Invalid lookback
        valid, error = template.validate_parameters({
            "lookback_period": -5,
            "threshold": 0.02,
            "position_size": 0.1,
        })
        assert valid is False


class TestMeanReversionTemplate:
    """Test MeanReversionTemplate implementation."""

    @pytest.fixture
    def template(self):
        return MeanReversionTemplate()

    def test_strategy_type(self, template):
        assert template.get_strategy_type() == StrategyType.MEAN_REVERSION

    def test_required_parameters(self, template):
        required = template.get_required_parameters()
        assert "lookback_period" in required
        assert "entry_threshold" in required
        assert "exit_threshold" in required

    def test_generate_code_basic(self, template):
        parameters = {
            "name": "TestMeanReversion",
            "lookback_period": 20,
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
            "position_size": 0.1,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "TestMeanReversion" in code
        assert "z_score" in code
        assert "def generate_signals" in code


class TestArbitrageTemplate:
    """Test ArbitrageTemplate implementation."""

    @pytest.fixture
    def template(self):
        return ArbitrageTemplate()

    def test_strategy_type(self, template):
        assert template.get_strategy_type() == StrategyType.ARBITRAGE

    def test_required_parameters(self, template):
        required = template.get_required_parameters()
        assert "assets" in required
        assert "correlation_window" in required

    def test_generate_code_basic(self, template):
        parameters = {
            "name": "TestArbitrage",
            "assets": ["AAPL", "MSFT"],
            "correlation_window": 30,
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
            "position_size": 0.5,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "TestArbitrage" in code
        assert "AAPL" in code
        assert "MSFT" in code
        assert "hedge_ratio" in code

    def test_parameter_validation(self, template):
        # Need at least 2 assets
        valid, error = template.validate_parameters({
            "assets": ["ONLY_ONE"],
            "correlation_window": 30,
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
        })
        assert valid is False
        assert "At least 2 assets" in error


class TestPairTradingTemplate:
    """Test PairTradingTemplate implementation."""

    @pytest.fixture
    def template(self):
        return PairTradingTemplate()

    def test_strategy_type(self, template):
        assert template.get_strategy_type() == StrategyType.PAIR_TRADING

    def test_required_parameters(self, template):
        required = template.get_required_parameters()
        assert "pair" in required
        assert "lookback_window" in required

    def test_generate_code_basic(self, template):
        parameters = {
            "name": "TestPairTrading",
            "pair": ("XOM", "CVX"),
            "lookback_window": 30,
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
            "position_size": 0.5,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "TestPairTrading" in code
        assert "XOM" in code
        assert "CVX" in code
        assert "cointegration" in code.lower()


class TestMLStrategyTemplate:
    """Test MLStrategyTemplate implementation."""

    @pytest.fixture
    def template(self):
        return MLStrategyTemplate()

    def test_strategy_type(self, template):
        assert template.get_strategy_type() == StrategyType.ML_STRATEGY

    def test_required_parameters(self, template):
        required = template.get_required_parameters()
        assert "model_type" in required
        assert "features" in required
        assert "prediction_threshold" in required

    def test_generate_code_rf(self, template):
        parameters = {
            "name": "TestMLStrategy",
            "model_type": "rf",
            "features": ["returns", "volume", "volatility"],
            "prediction_threshold": 0.5,
            "position_size": 0.1,
        }
        indicators = {}

        code = template.generate_code(parameters, indicators)

        assert "TestMLStrategy" in code
        assert "RandomForest" in code
        assert "def train" in code
        assert "def prepare_features" in code

    def test_parameter_validation(self, template):
        # Invalid model type
        valid, error = template.validate_parameters({
            "model_type": "invalid_model",
            "features": ["returns"],
            "prediction_threshold": 0.5,
        })
        assert valid is False


class TestTemplateFactory:
    """Test TemplateFactory for template management."""

    def test_get_template(self):
        """Test getting template by type."""
        momentum_template = TemplateFactory.get_template(StrategyType.MOMENTUM)
        assert isinstance(momentum_template, MomentumTemplate)

        mean_rev_template = TemplateFactory.get_template(StrategyType.MEAN_REVERSION)
        assert isinstance(mean_rev_template, MeanReversionTemplate)

    def test_get_unknown_template(self):
        """Test error for unknown strategy type."""
        # Create a dummy enum value that won't be registered
        from enum import Enum

        class DummyType(Enum):
            DUMMY = "dummy_strategy"

        with pytest.raises(ValueError, match="Unknown strategy type"):
            TemplateFactory.get_template(DummyType.DUMMY)

    def test_available_types(self):
        """Test getting all available types."""
        types = TemplateFactory.get_available_types()

        assert len(types) == 5
        assert StrategyType.MOMENTUM in types
        assert StrategyType.MEAN_REVERSION in types
        assert StrategyType.ARBITRAGE in types
        assert StrategyType.PAIR_TRADING in types
        assert StrategyType.ML_STRATEGY in types

    def test_is_registered(self):
        """Test checking if type is registered."""
        assert TemplateFactory.is_registered(StrategyType.MOMENTUM) is True
        assert TemplateFactory.is_registered(StrategyType.MEAN_REVERSION) is True


class TestGeneratedCodeQuality:
    """Test quality of generated code from templates."""

    def test_momentum_code_structure(self):
        """Test generated momentum code has proper structure."""
        template = MomentumTemplate()
        code = template.generate_code(
            {"name": "Test", "lookback_period": 20, "threshold": 0.02, "position_size": 0.1},
            {}
        )

        # Check for required methods
        assert "def __init__" in code
        assert "def generate_signals" in code
        assert "def backtest" in code

        # Check for imports
        assert "import pandas" in code
        assert "import numpy" in code

    def test_mean_reversion_code_structure(self):
        """Test generated mean reversion code has proper structure."""
        template = MeanReversionTemplate()
        code = template.generate_code(
            {"name": "Test", "lookback_period": 20, "entry_threshold": 2.0, "exit_threshold": 0.5},
            {}
        )

        # Check for z-score calculation
        assert "rolling" in code
        assert "std()" in code

    def test_code_imports_type_hints(self):
        """Test that generated code includes type hints."""
        template = MomentumTemplate()
        code = template.generate_code(
            {"name": "Test", "lookback_period": 20, "threshold": 0.02, "position_size": 0.1},
            {}
        )

        # Should have type hints
        assert "pd.DataFrame" in code
        assert "-> pd.Series" in code
