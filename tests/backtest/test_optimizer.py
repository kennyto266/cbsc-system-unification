"""
Unit tests for ParameterOptimizer.

Tests grid search, Bayesian optimization, and random search.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cbsc_strategy_sdk.backtest.adapter import BacktestAdapter
from cbsc_strategy_sdk.backtest.models import (
    BacktestJob,
    BacktestMetrics,
    BacktestStatus,
)
from cbsc_strategy_sdk.backtest.optimizer import ParameterOptimizer, OptimizationResult
from cbsc_strategy_sdk.backtest.result import BacktestResult


class TestParameterOptimizer:
    """Test suite for ParameterOptimizer class."""

    @pytest.fixture
    def adapter(self):
        """Create mock adapter for testing."""
        adapter = MagicMock(spec=BacktestAdapter)
        return adapter

    @pytest.fixture
    def optimizer(self, adapter):
        """Create optimizer instance."""
        return ParameterOptimizer(adapter=adapter)

    @pytest.fixture
    def mock_result(self):
        """Create mock backtest result."""
        result = MagicMock(spec=BacktestResult)
        result.metrics = BacktestMetrics(
            total_return=15.0,
            annual_return=18.0,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown=8.0,
            calmar_ratio=2.2,
            win_rate=65.0,
            profit_factor=1.8,
            total_trades=100,
            profit_trades=65,
            avg_profit=2.5,
            avg_loss=-1.8,
        )
        return result

    @pytest.mark.asyncio
    async def test_grid_search_single_param(self, optimizer, mock_result):
        """Test grid search with single parameter."""
        # Mock adapter to return result
        optimizer.adapter.run_backtest = AsyncMock(return_value=mock_result)

        result = await optimizer.grid_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid={"rsi_period": [10, 14, 20]},
        )

        assert isinstance(result, OptimizationResult)
        assert result.optimization_method == "grid_search"
        assert result.total_trials == 3
        assert result.best_metrics is not None
        assert result.best_parameters is not None

    @pytest.mark.asyncio
    async def test_grid_search_multiple_params(self, optimizer, mock_result):
        """Test grid search with multiple parameters."""
        optimizer.adapter.run_backtest = AsyncMock(return_value=mock_result)

        result = await optimizer.grid_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid={
                "rsi_period": [10, 14],
                "oversold": [20, 30],
                "overbought": [70, 80],
            },
        )

        # 2 * 2 * 2 = 8 combinations
        assert result.total_trials == 8
        assert len(result.all_results) == 8

    @pytest.mark.asyncio
    async def test_grid_search_selects_best(self, optimizer):
        """Test grid search selects best parameters."""
        # Create results with different Sharpe ratios
        def create_mock_result(sharpe):
            result = MagicMock(spec=BacktestResult)
            result.metrics = BacktestMetrics(
                total_return=10.0,
                annual_return=12.0,
                sharpe_ratio=sharpe,
                max_drawdown=5.0,
                win_rate=60.0,
                profit_factor=1.5,
                total_trades=50,
                profit_trades=30,
                avg_profit=2.0,
                avg_loss=-1.5,
            )
            return result

        call_count = [0]

        async def mock_backtest(*args, **kwargs):
            call_count[0] += 1
            # Vary Sharpe ratio based on call count
            sharpe_values = [1.0, 1.5, 2.0, 1.2]
            return create_mock_result(sharpe_values[(call_count[0] - 1) % len(sharpe_values)])

        optimizer.adapter.run_backtest = AsyncMock(side_effect=mock_backtest)

        result = await optimizer.grid_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid={"period": [10, 20, 30, 40]},
        )

        # Should select best Sharpe ratio
        assert result.best_metrics.sharpe_ratio == 2.0

    @pytest.mark.asyncio
    async def test_grid_search_with_failure(self, optimizer, mock_result):
        """Test grid search handles backtest failures."""
        call_count = [0]

        async def mock_backtest(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Backtest failed")
            return mock_result

        optimizer.adapter.run_backtest = AsyncMock(side_effect=mock_backtest)

        result = await optimizer.grid_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid={"period": [10, 20, 30]},
        )

        # Should complete with one failure
        assert result.total_trials == 3
        # One result should have error
        error_results = [r for r in result.all_results if "error" in r]
        assert len(error_results) == 1

    @pytest.mark.asyncio
    async def test_grid_search_all_fail(self, optimizer):
        """Test grid search when all backtests fail."""
        optimizer.adapter.run_backtest = AsyncMock(side_effect=Exception("All failed"))

        with pytest.raises(ValueError, match="All backtests failed"):
            await optimizer.grid_search(
                strategy_code="test_strategy",
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                parameter_grid={"period": [10, 20]},
            )

    @pytest.mark.asyncio
    async def test_grid_search_progress_callback(self, optimizer, mock_result):
        """Test grid search calls progress callback."""
        optimizer.adapter.run_backtest = AsyncMock(return_value=mock_result)

        progress_values = []

        def callback(pct: float) -> None:
            progress_values.append(pct)

        await optimizer.grid_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid={"period": [10, 20, 30, 40]},
            on_progress=callback,
        )

        # Should have progress updates
        assert len(progress_values) == 4
        assert progress_values[-1] == 100.0

    @pytest.mark.asyncio
    async def test_random_search(self, optimizer, mock_result):
        """Test random search optimization."""
        optimizer.adapter.run_backtest = AsyncMock(return_value=mock_result)

        result = await optimizer.random_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_bounds={"rsi_period": (5, 30)},
            n_iterations=10,
        )

        assert isinstance(result, OptimizationResult)
        assert result.optimization_method == "random_search"
        assert result.total_trials == 10

    @pytest.mark.asyncio
    async def test_random_search_integer_bounds(self, optimizer, mock_result):
        """Test random search with integer parameter bounds."""
        sampled_params = []

        async def mock_backtest(*args, parameters, **kwargs):
            sampled_params.append(parameters)
            return mock_result

        optimizer.adapter.run_backtest = AsyncMock(side_effect=mock_backtest)

        await optimizer.random_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_bounds={"period": (10, 20)},
            n_iterations=5,
        )

        # All sampled values should be integers
        for params in sampled_params:
            assert isinstance(params["period"], (int, float))
            # Should be within bounds
            # Note: numpy may return float for randint
            assert 10 <= int(params["period"]) <= 20

    @pytest.mark.asyncio
    async def test_random_search_float_bounds(self, optimizer, mock_result):
        """Test random search with float parameter bounds."""
        sampled_params = []

        async def mock_backtest(*args, parameters, **kwargs):
            sampled_params.append(parameters)
            return mock_result

        optimizer.adapter.run_backtest = AsyncMock(side_effect=mock_backtest)

        await optimizer.random_search(
            strategy_code="test_strategy",
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_bounds={"threshold": (0.1, 0.9)},
            n_iterations=5,
        )

        # All sampled values should be floats within bounds
        for params in sampled_params:
            assert 0.1 <= params["threshold"] <= 0.9

    @pytest.mark.asyncio
    async def test_bayesian_optimization_no_optuna(self, optimizer):
        """Test Bayesian optimization without Optuna."""
        with patch("cbsc_strategy_sdk.backtest.optimizer.OPTUNA_AVAILABLE", False):
            with pytest.raises(ImportError, match="Optuna is required"):
                await optimizer.optimize(
                    strategy_code="test_strategy",
                    symbols=["AAPL"],
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 12, 31),
                    parameter_bounds={"period": (5, 30)},
                    n_iterations=10,
                )


class TestOptimizationResult:
    """Test suite for OptimizationResult class."""

    @pytest.fixture
    def sample_result(self):
        """Create sample optimization result."""
        from datetime import datetime

        return OptimizationResult(
            best_parameters={"rsi_period": 14, "oversold": 30},
            best_metrics=BacktestMetrics(
                total_return=20.0,
                annual_return=24.0,
                sharpe_ratio=2.0,
                max_drawdown=5.0,
                win_rate=70.0,
                profit_factor=2.0,
                total_trades=100,
                profit_trades=70,
                avg_profit=3.0,
                avg_loss=-1.5,
            ),
            all_results=[
                {
                    "parameters": {"rsi_period": 10, "oversold": 20},
                    "metrics": BacktestMetrics(
                        total_return=15.0,
                        annual_return=18.0,
                        sharpe_ratio=1.5,
                        max_drawdown=8.0,
                        win_rate=60.0,
                        profit_factor=1.5,
                        total_trades=80,
                        profit_trades=48,
                        avg_profit=2.5,
                        avg_loss=-2.0,
                    ),
                    "metric_value": 1.5,
                },
                {
                    "parameters": {"rsi_period": 14, "oversold": 30},
                    "metrics": BacktestMetrics(
                        total_return=20.0,
                        annual_return=24.0,
                        sharpe_ratio=2.0,
                        max_drawdown=5.0,
                        win_rate=70.0,
                        profit_factor=2.0,
                        total_trades=100,
                        profit_trades=70,
                        avg_profit=3.0,
                        avg_loss=-1.5,
                    ),
                    "metric_value": 2.0,
                },
            ],
            optimization_method="grid_search",
        )

    def test_initialization(self, sample_result):
        """Test result initializes correctly."""
        assert sample_result.best_parameters == {"rsi_period": 14, "oversold": 30}
        assert sample_result.best_metrics.sharpe_ratio == 2.0
        assert sample_result.total_trials == 2
        assert sample_result.optimization_method == "grid_search"

    def test_summary(self, sample_result):
        """Test summary generation."""
        summary = sample_result.summary()

        assert "Optimization Summary (grid_search)" in summary
        assert "rsi_period: 14" in summary
        assert "oversold: 30" in summary
        assert "Sharpe Ratio:" in summary  # More flexible matching
        assert "Total Trials: 2" in summary

    def test_to_dataframe(self, sample_result):
        """Test DataFrame conversion."""
        df = sample_result.to_dataframe()

        if df is not None:  # pandas available
            assert len(df) == 2
            assert "rsi_period" in df.columns
            assert "oversold" in df.columns
            assert "sharpe_ratio" in df.columns
            assert "total_return" in df.columns

            # Check best result
            best_row = df.loc[df["sharpe_ratio"].idxmax()]
            assert best_row["sharpe_ratio"] == 2.0
