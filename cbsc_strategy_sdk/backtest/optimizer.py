"""
Parameter optimization for strategy backtesting.

This module provides ParameterOptimizer for grid search and Bayesian
optimization of strategy parameters.
"""

import asyncio
import itertools
import logging
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

from .adapter import BacktestAdapter
from .models import BacktestMetrics
from .progress import BacktestProgress


logger = logging.getLogger(__name__)


class OptimizationResult:
    """Result from parameter optimization.

    Attributes:
        best_parameters: Best parameter combination found
        best_metrics: Metrics for best parameters
        all_results: List of all optimization results
        optimization_method: Method used (grid or bayesian)
        total_trials: Number of trials run
    """

    def __init__(
        self,
        best_parameters: Dict[str, Any],
        best_metrics: BacktestMetrics,
        all_results: List[Dict[str, Any]],
        optimization_method: str,
    ) -> None:
        """Initialize optimization result.

        Args:
            best_parameters: Best parameter combination
            best_metrics: Metrics for best parameters
            all_results: All trial results
            optimization_method: Method used
        """
        self.best_parameters = best_parameters
        self.best_metrics = best_metrics
        self.all_results = all_results
        self.optimization_method = optimization_method
        self.total_trials = len(all_results)

    def to_dataframe(self):
        """Convert results to pandas DataFrame.

        Returns:
            DataFrame with all trial results

        Example:
            >>> df = result.to_dataframe()
            >>> print(df.nlargest(5, 'sharpe_ratio'))
        """
        try:
            import pandas as pd

            data = []
            for r in self.all_results:
                row = {**r["parameters"]}
                row["sharpe_ratio"] = r["metrics"].sharpe_ratio
                row["total_return"] = r["metrics"].total_return
                row["max_drawdown"] = r["metrics"].max_drawdown
                row["profit_factor"] = r["metrics"].profit_factor
                row["win_rate"] = r["metrics"].win_rate
                data.append(row)

            return pd.DataFrame(data)

        except ImportError:
            logger.warning("pandas not available for DataFrame conversion")
            return None

    def summary(self) -> str:
        """Generate text summary.

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 60,
            f"Optimization Summary ({self.optimization_method})",
            "=" * 60,
            "",
            "Best Parameters:",
        ]

        for key, value in self.best_parameters.items():
            lines.append(f"  {key}: {value}")

        lines.extend([
            "",
            "Best Metrics:",
            f"  Sharpe Ratio:     {self.best_metrics.sharpe_ratio:>8.2f}",
            f"  Total Return:     {self.best_metrics.total_return:>8.2f}%",
            f"  Max Drawdown:     {self.best_metrics.max_drawdown:>8.2f}%",
            f"  Win Rate:         {self.best_metrics.win_rate:>8.2f}%",
            f"  Profit Factor:    {self.best_metrics.profit_factor:>8.2f}",
            "",
            f"Total Trials: {self.total_trials}",
            "=" * 60,
        ])

        return "\n".join(lines)


class ParameterOptimizer:
    """Optimize strategy parameters using grid search or Bayesian optimization.

    This class provides methods for finding optimal strategy parameters
    through systematic search techniques.

    Attributes:
        adapter: BacktestAdapter instance for running backtests

    Example:
        >>> adapter = BacktestAdapter()
        >>> await adapter.__aenter__()
        >>>
        >>> optimizer = ParameterOptimizer(adapter)
        >>>
        >>> # Grid search
        >>> result = await optimizer.grid_search(
        ...     strategy_code="my_strategy",
        ...     parameter_grid={"rsi_period": [10, 14, 20]},
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 12, 31),
        ...     symbols=["AAPL"]
        ... )
        >>>
        >>> print(result.summary())
    """

    def __init__(
        self,
        adapter: BacktestAdapter,
    ) -> None:
        """Initialize ParameterOptimizer.

        Args:
            adapter: BacktestAdapter instance
        """
        self.adapter = adapter

    async def grid_search(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        parameter_grid: Dict[str, List[Any]],
        metric: str = "sharpe_ratio",
        on_progress: Optional[Callable[[float], None]] = None,
        **backtest_kwargs,
    ) -> OptimizationResult:
        """Run grid search over parameter combinations.

        Args:
            strategy_code: Strategy identifier
            symbols: Trading symbols
            start_date: Backtest start date
            end_date: Backtest end date
            parameter_grid: Dictionary of parameter names to value lists
            metric: Metric to optimize (default: sharpe_ratio)
            on_progress: Optional progress callback
            **backtest_kwargs: Additional arguments for backtest

        Returns:
            OptimizationResult with best parameters and all results

        Example:
            >>> result = await optimizer.grid_search(
            ...     strategy_code="rsi_strategy",
            ...     parameter_grid={
            ...         "rsi_period": [10, 14, 20],
            ...         "oversold": [20, 30],
            ...         "overbought": [70, 80]
            ...     },
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31),
            ...     symbols=["AAPL"]
            ... )
        """
        # Generate all parameter combinations
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        combinations = list(itertools.product(*param_values))

        total_trials = len(combinations)
        logger.info(f"Grid search: {total_trials} combinations")

        # Track results
        all_results: List[Dict[str, Any]] = []
        best_metrics: Optional[BacktestMetrics] = None
        best_parameters: Optional[Dict[str, Any]] = None
        best_metric_value = float("-inf")

        # Run backtests for each combination
        for i, combo in enumerate(combinations):
            parameters = dict(zip(param_names, combo))

            try:
                result = await self.adapter.run_backtest(
                    strategy_code=strategy_code,
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=parameters,
                    **backtest_kwargs,
                )

                # Get metric value
                metric_value = getattr(result.metrics, metric, 0)

                all_results.append({
                    "parameters": parameters,
                    "metrics": result.metrics,
                    "metric_value": metric_value,
                })

                # Update best
                if metric_value > best_metric_value:
                    best_metric_value = metric_value
                    best_parameters = parameters
                    best_metrics = result.metrics

            except Exception as e:
                logger.warning(f"Backtest failed for {parameters}: {e}")
                all_results.append({
                    "parameters": parameters,
                    "metrics": None,
                    "metric_value": float("-inf"),
                    "error": str(e),
                })

            # Update progress
            if on_progress:
                progress_pct = (i + 1) / total_trials * 100
                on_progress(progress_pct)

        if best_metrics is None:
            raise ValueError("All backtests failed during optimization")

        return OptimizationResult(
            best_parameters=best_parameters,
            best_metrics=best_metrics,
            all_results=all_results,
            optimization_method="grid_search",
        )

    async def optimize(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        parameter_bounds: Dict[str, Tuple[float, float]],
        n_iterations: int = 100,
        metric: str = "sharpe_ratio",
        on_progress: Optional[Callable[[float], None]] = None,
        **backtest_kwargs,
    ) -> OptimizationResult:
        """Bayesian optimization of parameters.

        Uses Optuna for efficient Bayesian optimization.

        Args:
            strategy_code: Strategy identifier
            symbols: Trading symbols
            start_date: Backtest start date
            end_date: Backtest end date
            parameter_bounds: Dictionary of parameter names to (min, max) tuples
            n_iterations: Number of optimization iterations
            metric: Metric to optimize
            on_progress: Optional progress callback
            **backtest_kwargs: Additional arguments for backtest

        Returns:
            OptimizationResult with best parameters

        Raises:
            ImportError: If Optuna not installed

        Example:
            >>> result = await optimizer.optimize(
            ...     strategy_code="rsi_strategy",
            ...     parameter_bounds={
            ...         "rsi_period": (5, 30),
            ...         "oversold": (15, 35),
            ...         "overbought": (65, 85)
            ...     },
            ...     n_iterations=50,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31),
            ...     symbols=["AAPL"]
            ... )
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError(
                "Optuna is required for Bayesian optimization. "
                "Install with: pip install optuna"
            )

        # Create Optuna study
        def objective(trial: optuna.Trial) -> float:
            # Suggest parameters
            parameters = {}
            for param_name, (min_val, max_val) in parameter_bounds.items():
                # Determine if integer or float
                if isinstance(min_val, int) and isinstance(max_val, int):
                    parameters[param_name] = trial.suggest_int(param_name, min_val, max_val)
                else:
                    parameters[param_name] = trial.suggest_float(param_name, min_val, max_val)

            # Run backtest (synchronously within objective)
            async def run_backtest():
                try:
                    result = await self.adapter.run_backtest(
                        strategy_code=strategy_code,
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        parameters=parameters,
                        **backtest_kwargs,
                    )
                    return getattr(result.metrics, metric, 0), result.metrics
                except Exception as e:
                    logger.warning(f"Trial failed: {e}")
                    return float("-inf"), None

            # Run the async function
            loop = asyncio.get_event_loop()
            metric_value, metrics = loop.run_until_complete(run_backtest())

            return metric_value

        # Create and run study
        study = optuna.create_study(direction="maximize")

        # Progress callback
        def trial_callback(study, trial):
            if on_progress:
                progress_pct = len(study.trials) / n_iterations * 100
                on_progress(progress_pct)

        study.optimize(
            objective,
            n_trials=n_iterations,
            callbacks=[trial_callback] if on_progress else None,
        )

        # Collect results
        all_results = []
        for trial in study.trials:
            params = trial.params.copy()
            if trial.value is not None:
                # Need to re-run to get metrics (inefficient but simple)
                # In production, cache trial results
                try:
                    result = await self.adapter.run_backtest(
                        strategy_code=strategy_code,
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        parameters=params,
                        **backtest_kwargs,
                    )
                    all_results.append({
                        "parameters": params,
                        "metrics": result.metrics,
                        "metric_value": trial.value,
                    })
                except Exception:
                    all_results.append({
                        "parameters": params,
                        "metrics": None,
                        "metric_value": trial.value or float("-inf"),
                    })
            else:
                all_results.append({
                    "parameters": params,
                    "metrics": None,
                    "metric_value": float("-inf"),
                    "error": "Trial failed",
                })

        # Get best result
        best_trial = study.best_trial
        best_params = best_trial.params.copy()

        # Get metrics for best params
        try:
            result = await self.adapter.run_backtest(
                strategy_code=strategy_code,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                parameters=best_params,
                **backtest_kwargs,
            )
            best_metrics = result.metrics
        except Exception as e:
            raise ValueError(f"Failed to run backtest with best parameters: {e}")

        return OptimizationResult(
            best_parameters=best_params,
            best_metrics=best_metrics,
            all_results=all_results,
            optimization_method="bayesian",
        )

    async def random_search(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        parameter_bounds: Dict[str, Tuple[float, float]],
        n_iterations: int = 100,
        metric: str = "sharpe_ratio",
        on_progress: Optional[Callable[[float], None]] = None,
        **backtest_kwargs,
    ) -> OptimizationResult:
        """Random search over parameter space.

        Args:
            strategy_code: Strategy identifier
            symbols: Trading symbols
            start_date: Backtest start date
            end_date: Backtest end date
            parameter_bounds: Dictionary of parameter names to (min, max) tuples
            n_iterations: Number of random trials
            metric: Metric to optimize
            on_progress: Optional progress callback
            **backtest_kwargs: Additional arguments for backtest

        Returns:
            OptimizationResult with best parameters

        Example:
            >>> result = await optimizer.random_search(
            ...     strategy_code="rsi_strategy",
            ...     parameter_bounds={"rsi_period": (5, 30)},
            ...     n_iterations=20,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31),
            ...     symbols=["AAPL"]
            ... )
        """
        all_results: List[Dict[str, Any]] = []
        best_metrics: Optional[BacktestMetrics] = None
        best_parameters: Optional[Dict[str, Any]] = None
        best_metric_value = float("-inf")

        for i in range(n_iterations):
            # Sample random parameters
            parameters = {}
            for param_name, (min_val, max_val) in parameter_bounds.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    parameters[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    parameters[param_name] = np.random.uniform(min_val, max_val)

            try:
                result = await self.adapter.run_backtest(
                    strategy_code=strategy_code,
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=parameters,
                    **backtest_kwargs,
                )

                metric_value = getattr(result.metrics, metric, 0)

                all_results.append({
                    "parameters": parameters,
                    "metrics": result.metrics,
                    "metric_value": metric_value,
                })

                if metric_value > best_metric_value:
                    best_metric_value = metric_value
                    best_parameters = parameters
                    best_metrics = result.metrics

            except Exception as e:
                logger.warning(f"Random search trial failed: {e}")
                all_results.append({
                    "parameters": parameters,
                    "metrics": None,
                    "metric_value": float("-inf"),
                    "error": str(e),
                })

            if on_progress:
                on_progress((i + 1) / n_iterations * 100)

        if best_metrics is None:
            raise ValueError("All random search trials failed")

        return OptimizationResult(
            best_parameters=best_parameters,
            best_metrics=best_metrics,
            all_results=all_results,
            optimization_method="random_search",
        )
