"""
Tests for ClaudeCodeAssistant

Test suite for ClaudeCodeAssistant class including
code generation, parameter optimization, and error analysis.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from cbsc_strategy_sdk.claude.assistant import (
    ClaudeCodeAssistant,
    GeneratedCode,
    ParameterSuggestions,
    FixSuggestions,
    GenerationMode,
    StrategyType,
)
from cbsc_strategy_sdk.exceptions import APIError


@pytest.fixture
def assistant():
    """Create ClaudeCodeAssistant for testing."""
    return ClaudeCodeAssistant(
        api_key="test-key-123",
        fallback_to_template=True,
    )


@pytest.fixture
def mock_api_response():
    """Mock Claude API response."""
    return '''
Here's the generated strategy code:

```python
"""
TestStrategy

Momentum-based trading strategy.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

class TestStrategy:
    """Momentum strategy implementation."""

    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        momentum = data['close'].pct_change(self.lookback_period)
        signals = pd.Series(0, index=data.index)
        signals[momentum > 0.02] = 1
        signals[momentum < -0.02] = -1
        return signals

    def backtest(self, data: pd.DataFrame, initial_capital: float = 100000) -> Dict[str, Any]:
        """Run backtest."""
        signals = self.generate_signals(data)
        returns = signals.shift(1) * data['close'].pct_change()
        equity = (1 + returns * 0.1).cumprod() * initial_capital
        return {"final_equity": equity.iloc[-1]}
```
'''


class TestClaudeCodeAssistant:
    """Test ClaudeCodeAssistant main functionality."""

    def test_initialization(self):
        """Test assistant initialization."""
        assistant = ClaudeCodeAssistant(api_key="test-key")

        assert assistant.api_key == "test-key"
        assert assistant.fallback_to_template is True

    def test_initialization_without_api_key(self):
        """Test initialization can work without API key (template mode)."""
        assistant = ClaudeCodeAssistant(
            api_key=None,
            fallback_to_template=True,
        )

        assert assistant.client is None
        assert assistant.is_api_available() is False

    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    def test_generate_strategy_via_template(self, mock_client_class, assistant):
        """Test template-based code generation."""
        # Mock client as unavailable
        assistant._client = None

        # Generate using template
        result = assistant.generate_strategy(
            description="Simple momentum strategy",
            strategy_type=StrategyType.MOMENTUM,
            mode=GenerationMode.TEMPLATE,
        )

        assert isinstance(result, GeneratedCode)
        assert result.code != ""
        assert result.strategy_type == StrategyType.MOMENTUM
        assert result.mode_used == GenerationMode.TEMPLATE
        # Template generation should be valid
        assert result.is_valid is True

    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    def test_generate_strategy_via_api(self, mock_client_class, mock_api_response):
        """Test API-based code generation."""
        # Setup mock client
        mock_client = Mock()
        mock_client.generate.return_value = mock_api_response
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client

        assistant = ClaudeCodeAssistant(api_key="test-key")
        assistant._client = mock_client

        # Generate using API
        result = assistant.generate_strategy(
            description="Moving average crossover",
            strategy_type=StrategyType.MOMENTUM,
            mode=GenerationMode.API,
        )

        assert isinstance(result, GeneratedCode)
        assert result.mode_used == GenerationMode.API
        assert "TestStrategy" in result.code
        assert "def generate_signals" in result.code

    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    def test_generate_strategy_hybrid_with_api_fallback(self, mock_client_class):
        """Test hybrid mode falls back to template when API fails."""
        # Setup mock to raise error
        mock_client = Mock()
        mock_client.generate.side_effect = APIError("API unavailable")
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client

        assistant = ClaudeCodeAssistant(api_key="test-key", fallback_to_template=True)

        # Generate using hybrid mode
        result = assistant.generate_strategy(
            description="Mean reversion strategy",
            strategy_type=StrategyType.MEAN_REVERSION,
            mode=GenerationMode.HYBRID,
        )

        # Should fall back to template
        assert result.mode_used == GenerationMode.TEMPLATE
        assert result.is_valid is True

    def test_generate_with_custom_parameters(self, assistant):
        """Test generation with custom parameters."""
        assistant._client = None  # Force template mode

        parameters = {
            "lookback_period": 15,
            "threshold": 0.03,
            "position_size": 0.2,
        }

        result = assistant.generate_strategy(
            description="Custom momentum",
            strategy_type=StrategyType.MOMENTUM,
            parameters=parameters,
            mode=GenerationMode.TEMPLATE,
        )

        assert "lookback_period = 15" in result.code
        assert "threshold = 0.03" in result.code

    def test_extract_strategy_name(self, assistant):
        """Test strategy name extraction from description."""
        name1 = assistant._extract_name_from_description("Create MovingAverage strategy")
        assert "MovingAverage" in name1

        name2 = assistant._extract_name_from_description("RSI trading strategy")
        assert "RSI" in name2

        name3 = assistant._extract_name_from_description("Generic description")
        assert "CustomStrategy" in name3

    def test_extract_code_from_response(self, assistant):
        """Test code extraction from API response."""
        response_with_markdown = '''
Some text here.

```python
def strategy():
    pass
```

More text.
'''

        code = assistant._extract_code_from_response(response_with_markdown)
        assert "def strategy():" in code

    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    def test_optimize_parameters(self, mock_client_class):
        """Test parameter optimization suggestions."""
        mock_client = Mock()
        mock_client.generate.return_value = "Based on the metrics, try increasing lookback_period to 25"
        mock_client_class.return_value = mock_client

        assistant = ClaudeCodeAssistant(api_key="test-key")
        assistant._client = mock_client

        metrics = {
            "sharpe_ratio": 0.5,
            "max_drawdown": -0.15,
            "total_return": 0.10,
        }

        suggestions = assistant.optimize_parameters(
            code="def strategy(): pass",
            performance_metrics=metrics,
        )

        assert isinstance(suggestions, ParameterSuggestions)
        assert isinstance(suggestions.suggested_parameters, dict)
        assert suggestions.rationale != ""

    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    def test_analyze_errors(self, mock_client_class):
        """Test error analysis and fix suggestions."""
        corrected_code = '''
```python
def strategy(data):
    # Fixed: Added type hint and proper handling
    return data
```'''

        mock_client = Mock()
        mock_client.generate.return_value = f"Root cause: Missing type hint\n{corrected_code}\nUse proper type hints."
        mock_client_class.return_value = mock_client

        assistant = ClaudeCodeAssistant(api_key="test-key")
        assistant._client = mock_client

        fix = assistant.analyze_errors(
            code="def strategy(data):",
            error_message="TypeError: NoneType has no len",
        )

        assert isinstance(fix, FixSuggestions)
        assert fix.corrected_code != ""
        assert fix.root_cause != ""
        assert len(fix.prevention_tips) > 0

    @pytest.mark.asyncio
    @patch("cbsc_strategy_sdk.claude.assistant.ClaudeClient")
    async def test_generate_async(self, mock_client_class, mock_api_response):
        """Test asynchronous code generation."""
        mock_async_client = Mock()
        mock_async_client.generate_async = AsyncMock(return_value=mock_api_response)
        mock_async_client.is_available.return_value = True
        mock_client_class.return_value = mock_async_client

        assistant = ClaudeCodeAssistant(api_key="test-key")
        assistant._client = mock_async_client

        result = await assistant.generate_async(
            description="Async test strategy",
            strategy_type=StrategyType.MOMENTUM,
        )

        assert isinstance(result, GeneratedCode)
        assert result.mode_used == GenerationMode.API

    def test_get_usage_stats(self):
        """Test getting API usage statistics."""
        mock_client = Mock()
        mock_usage = Mock()
        mock_usage.total_requests = 10
        mock_usage.total_tokens = 5000
        mock_client.get_usage_stats.return_value = mock_usage

        assistant = ClaudeCodeAssistant(api_key="test-key")
        assistant._client = mock_client

        stats = assistant.get_usage_stats()

        assert stats.total_requests == 10
        assert stats.total_tokens == 5000


class TestGenerationResults:
    """Test generation result data classes."""

    def test_generated_code(self):
        """Test GeneratedCode dataclass."""
        result = GeneratedCode(
            code="def strategy(): pass",
            strategy_type=StrategyType.MOMENTUM,
            mode_used=GenerationMode.TEMPLATE,
            is_valid=True,
            validation_errors=[],
            warnings=[],
            suggestions=[],
        )

        assert result.is_valid is True
        assert bool(result) is True

    def test_generated_code_invalid(self):
        """Test GeneratedCode with errors."""
        result = GeneratedCode(
            code="invalid code",
            strategy_type=StrategyType.MOMENTUM,
            mode_used=GenerationMode.API,
            is_valid=False,
            validation_errors=["Syntax error"],
            warnings=[],
            suggestions=[],
        )

        assert result.is_valid is False
        assert bool(result) is False

    def test_parameter_suggestions(self):
        """Test ParameterSuggestions dataclass."""
        suggestions = ParameterSuggestions(
            suggested_parameters={"lookback": 25},
            rationale="Improve signal quality",
            expected_improvement="Higher Sharpe ratio",
            confidence=0.8,
            risks=["Overfitting"],
        )

        assert suggestions.suggested_parameters["lookback"] == 25
        assert suggestions.confidence == 0.8

    def test_fix_suggestions(self):
        """Test FixSuggestions dataclass."""
        fix = FixSuggestions(
            corrected_code="def fixed(): pass",
            explanation="Fixed syntax error",
            root_cause="Missing colon",
            prevention_tips=["Use linter"],
        )

        assert fix.corrected_code != ""
        assert len(fix.prevention_tips) == 1


class TestDefaultParameters:
    """Test default parameter generation."""

    def test_momentum_defaults(self, assistant):
        """Test default parameters for momentum strategy."""
        defaults = assistant._get_default_parameters(StrategyType.MOMENTUM)

        assert "lookback_period" in defaults
        assert defaults["lookback_period"] == 20
        assert "threshold" in defaults

    def test_mean_reversion_defaults(self, assistant):
        """Test default parameters for mean reversion strategy."""
        defaults = assistant._get_default_parameters(StrategyType.MEAN_REVERSION)

        assert "lookback_period" in defaults
        assert "entry_threshold" in defaults
        assert "exit_threshold" in defaults

    def test_arbitrage_defaults(self, assistant):
        """Test default parameters for arbitrage strategy."""
        defaults = assistant._get_default_parameters(StrategyType.ARBITRAGE)

        assert "assets" in defaults
        assert len(defaults["assets"]) == 2

    def test_pair_trading_defaults(self, assistant):
        """Test default parameters for pair trading strategy."""
        defaults = assistant._get_default_parameters(StrategyType.PAIR_TRADING)

        assert "pair" in defaults
        assert len(defaults["pair"]) == 2

    def test_ml_strategy_defaults(self, assistant):
        """Test default parameters for ML strategy."""
        defaults = assistant._get_default_parameters(StrategyType.ML_STRATEGY)

        assert "model_type" in defaults
        assert "features" in defaults
        assert len(defaults["features"]) > 0
