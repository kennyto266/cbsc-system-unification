"""
Vectorized Backtest Engine with Multi-Asset Support
====================================================

High-performance vectorized backtest engine that supports:
- Multi-asset portfolio backtesting
- Vectorized calculations for speed
- Advanced transaction cost modeling
- Parameter optimization
- Parallel execution

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import numba as nb
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
from datetime import datetime, timedelta
import warnings
from scipy import optimize
import json
import pickle
import os

# Import base backtest engine
try:
    from .enhanced_backtest_engine import BacktestConfig, BacktestResult, Position, Trade
    from .transaction_cost_model import TransactionCostModel
    from .portfolio_optimizer import PortfolioOptimizer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from enhanced_backtest_engine import BacktestConfig, BacktestResult, Position, Trade

logger = logging.getLogger(__name__)


class VectorizedBacktestMode(Enum):
    """Vectorized backtest execution modes"""
    SINGLE_ASSET = "single_asset"
    MULTI_ASSET = "multi_asset"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    PARAMETER_SWEEP = "parameter_sweep"


@dataclass
class TransactionCostConfig:
    """Transaction cost configuration"""
    # Commission models
    commission_model: str = "percentage"  # percentage, fixed, tiered, per_share
    commission_rate: float = 0.001  # 0.1%
    fixed_commission: float = 1.0  # $1 per trade
    min_commission: float = 0.0
    max_commission: float = float('inf')

    # Slippage models
    slippage_model: str = "linear"  # linear, square_root, percentage, volatility_adjusted
    slippage_rate: float = 0.0005  # 5 bps
    slippage_impact_factor: float = 0.1  # Market impact factor
    slippage_volatility_factor: float = 0.5

    # Financing costs
    financing_rate: float = 0.02  # 2% annual
    short_financing_premium: float = 0.005  # Additional 0.5% for shorts

    # Taxes
    tax_rate: float = 0.0  # Capital gains tax
    stt_rate: float = 0.001  # Securities Transaction Tax

    # Other costs
    exchange_fees: float = 0.0001  # 1 bps
    clearing_fees: float = 0.0001  # 1 bps


@dataclass
class PortfolioConfig:
    """Portfolio configuration for multi-asset backtesting"""
    assets: List[str]
    initial_weights: Dict[str, float] = field(default_factory=dict)
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_turnover: float = 1.0  # Maximum daily turnover
    sector_constraints: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Optimization settings
    optimization_method: str = "mean_variance"  # mean_variance, risk_parity, equal_risk
    lookback_window: int = 252  # Trading days for optimization
    optimization_frequency: str = "monthly"
    risk_free_rate: float = 0.02

    # Constraints
    target_volatility: Optional[float] = None
    max_drawdown_target: Optional[float] = None
    beta_target: Optional[float] = None


@dataclass
class ParameterSweepConfig:
    """Parameter sweep configuration"""
    parameters: Dict[str, List[Any]]  # Parameter name -> list of values
    sweep_type: str = "grid"  # grid, random, bayesian
    n_combinations: Optional[int] = None  # For random/bayesian sweeps
    objective_metric: str = "sharpe_ratio"  # Optimization objective
    early_stopping: bool = True
    early_stopping_patience: int = 50
    n_jobs: int = -1  # Parallel jobs, -1 for all CPUs


class VectorizedBacktestEngine:
    """
    High-performance vectorized backtest engine
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize vectorized backtest engine

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.transaction_cost_config = TransactionCostConfig()

        # Internal state
        self.prices: Optional[pd.DataFrame] = None
        self.returns: Optional[pd.DataFrame] = None
        self.signals: Optional[pd.DataFrame] = None
        self.positions: Optional[pd.DataFrame] = None
        self.trades: List[Trade] = []
        self.performance_metrics: Dict[str, Any] = {}

        # Optimization results
        self.optimization_results: List[BacktestResult] = []
        self.best_parameters: Optional[Dict[str, Any]] = None

        logger.info("Vectorized backtest engine initialized")

    def load_data(self, prices: pd.DataFrame, benchmark_data: Optional[pd.DataFrame] = None) -> None:
        """
        Load price data for backtesting

        Args:
            prices: DataFrame with prices (datetime index, assets as columns)
            benchmark_data: Optional benchmark data
        """
        try:
            # Validate data
            self._validate_price_data(prices)

            # Store data
            self.prices = prices.copy()
            self.returns = prices.pct_change().fillna(0)

            # Add benchmark if provided
            if benchmark_data is not None:
                self.benchmark_prices = benchmark_data.copy()
                self.benchmark_returns = benchmark_data.pct_change().fillna(0)

            logger.info(f"Data loaded: {len(prices)} observations, {len(prices.columns)} assets")

        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            raise

    def run_vectorized_backtest(
        self,
        strategy: Union[Callable, pd.DataFrame],
        mode: VectorizedBacktestMode = VectorizedBacktestMode.MULTI_ASSET,
        portfolio_config: Optional[PortfolioConfig] = None,
        parameter_config: Optional[ParameterSweepConfig] = None
    ) -> BacktestResult:
        """
        Run vectorized backtest

        Args:
            strategy: Strategy function or pre-computed signals DataFrame
            mode: Backtest execution mode
            portfolio_config: Portfolio configuration for multi-asset backtests
            parameter_config: Parameter sweep configuration

        Returns:
            BacktestResult: Comprehensive backtest results
        """
        try:
            logger.info(f"Starting vectorized backtest in {mode.value} mode")

            if mode == VectorizedBacktestMode.SINGLE_ASSET:
                return self._run_single_asset_backtest(strategy)
            elif mode == VectorizedBacktestMode.MULTI_ASSET:
                return self._run_multi_asset_backtest(strategy, portfolio_config)
            elif mode == VectorizedBacktestMode.PORTFOLIO_OPTIMIZATION:
                return self._run_portfolio_optimization_backtest(strategy, portfolio_config)
            elif mode == VectorizedBacktestMode.PARAMETER_SWEEP:
                return self._run_parameter_sweep_backtest(strategy, parameter_config)
            else:
                raise ValueError(f"Unsupported mode: {mode}")

        except Exception as e:
            logger.error(f"Vectorized backtest failed: {e}")
            raise

    def _run_single_asset_backtest(self, strategy: Callable) -> BacktestResult:
        """Run single asset backtest with vectorized calculations"""

        # Generate signals
        if callable(strategy):
            signals = self._generate_signals_vectorized(strategy)
        else:
            signals = strategy

        # Calculate positions with vectorized operations
        positions = self._calculate_positions_vectorized(signals)

        # Calculate returns with transaction costs
        returns = self._calculate_returns_vectorized(positions)

        # Calculate performance metrics
        metrics = self._calculate_performance_metrics_vectorized(returns)

        # Create result object
        return self._create_result_from_metrics(metrics)

    def _run_multi_asset_backtest(
        self,
        strategy: Union[Callable, pd.DataFrame],
        portfolio_config: Optional[PortfolioConfig] = None
    ) -> BacktestResult:
        """Run multi-asset portfolio backtest"""

        if portfolio_config is None:
            portfolio_config = PortfolioConfig(assets=list(self.prices.columns))

        # Generate signals for each asset
        if callable(strategy):
            signals = self._generate_multi_asset_signals_vectorized(strategy, portfolio_config)
        else:
            signals = strategy

        # Apply portfolio rebalancing
        weights = self._apply_portfolio_rebalaling(signals, portfolio_config)

        # Calculate positions with weights
        positions = self._calculate_positions_from_weights(weights)

        # Calculate portfolio returns with transaction costs
        returns = self._calculate_portfolio_returns_vectorized(positions, weights)

        # Calculate performance metrics
        metrics = self._calculate_portfolio_performance_metrics(returns, weights)

        # Create result object
        return self._create_result_from_metrics(metrics)

    def _run_portfolio_optimization_backtest(
        self,
        strategy: Union[Callable, pd.DataFrame],
        portfolio_config: PortfolioConfig
    ) -> BacktestResult:
        """Run portfolio optimization backtest"""

        # Create portfolio optimizer
        optimizer = PortfolioOptimizer(portfolio_config)

        # Optimize portfolio at each rebalance date
        optimized_weights = optimizer.optimize_portfolio(
            self.returns,
            self.prices,
            rebalance_frequency=portfolio_config.rebalance_frequency
        )

        # Calculate positions from optimized weights
        positions = self._calculate_positions_from_weights(optimized_weights)

        # Calculate portfolio returns
        returns = self._calculate_portfolio_returns_vectorized(positions, optimized_weights)

        # Calculate performance metrics
        metrics = self._calculate_portfolio_performance_metrics(returns, optimized_weights)

        # Add optimization-specific metrics
        metrics.update({
            'optimization_method': portfolio_config.optimization_method,
            'optimization_frequency': portfolio_config.optimization_frequency,
            'turnover': self._calculate_turnover(optimized_weights)
        })

        return self._create_result_from_metrics(metrics)

    def _run_parameter_sweep_backtest(
        self,
        strategy: Callable,
        parameter_config: ParameterSweepConfig
    ) -> BacktestResult:
        """Run parameter sweep optimization"""

        # Generate parameter combinations
        parameter_combinations = self._generate_parameter_combinations(parameter_config)

        # Run backtests in parallel
        results = self._run_parallel_backtests(strategy, parameter_combinations)

        # Find best parameters
        best_result = self._find_best_parameters(results, parameter_config.objective_metric)

        self.optimization_results = results
        self.best_parameters = best_result['parameters']

        return best_result['result']

    def _generate_signals_vectorized(self, strategy: Callable) -> pd.DataFrame:
        """Generate trading signals using vectorized operations"""

        # Create signals DataFrame
        signals = pd.DataFrame(index=self.prices.index, columns=self.prices.columns)

        # Apply strategy to each asset with vectorized operations
        for asset in self.prices.columns:
            prices = self.prices[asset].values
            returns = self.returns[asset].values

            # Generate signals using vectorized operations
            asset_signals = strategy(prices, returns)
            signals[asset] = asset_signals

        return signals.fillna(0)

    def _generate_multi_asset_signals_vectorized(
        self,
        strategy: Callable,
        portfolio_config: PortfolioConfig
    ) -> pd.DataFrame:
        """Generate multi-asset signals with portfolio constraints"""

        # Apply portfolio strategy
        weights = strategy(self.prices, self.returns, portfolio_config)

        # Apply constraints
        weights = self._apply_portfolio_constraints(weights, portfolio_config)

        return weights

    def _apply_portfolio_rebalaling(
        self,
        signals: pd.DataFrame,
        portfolio_config: PortfolioConfig
    ) -> pd.DataFrame:
        """Apply portfolio rebalancing rules"""

        # Convert signals to weights if needed
        if signals.abs().max() > 1.0:
            # Assume signals are positions, convert to weights
            weights = signals.div(signals.abs().sum(axis=1), axis=0).fillna(0)
        else:
            weights = signals

        # Apply rebalancing frequency
        if portfolio_config.rebalance_frequency == "daily":
            return weights
        elif portfolio_config.rebalance_frequency == "weekly":
            return weights.resample('W').ffill()
        elif portfolio_config.rebalance_frequency == "monthly":
            return weights.resample('M').ffill()
        elif portfolio_config.rebalance_frequency == "quarterly":
            return weights.resample('Q').ffill()
        else:
            return weights

    def _apply_portfolio_constraints(
        self,
        weights: pd.DataFrame,
        portfolio_config: PortfolioConfig
    ) -> pd.DataFrame:
        """Apply portfolio constraints to weights"""

        # Apply min/max weight constraints
        weights = weights.clip(lower=portfolio_config.min_weight, upper=portfolio_config.max_weight)

        # Normalize to sum to 1
        weights = weights.div(weights.sum(axis=1), axis=0).fillna(0)

        # Apply sector constraints if provided
        if portfolio_config.sector_constraints:
            for sector, constraints in portfolio_config.sector_constraints.items():
                sector_assets = [asset for asset in weights.columns if asset.startswith(sector)]
                if sector_assets:
                    sector_weight = weights[sector_assets].sum(axis=1)
                    # Apply sector constraints (this would need more sophisticated implementation)
                    weights[sector_assets] *= constraints.get('max_weight', 1.0) / sector_weight.max()

        return weights.fillna(0)

    def _calculate_positions_vectorized(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Calculate positions from signals using vectorized operations"""

        # Convert signals to positions
        positions = signals.copy()

        # Apply position sizing
        positions = positions * self.config.initial_capital / self.prices

        return positions.fillna(0)

    def _calculate_positions_from_weights(self, weights: pd.DataFrame) -> pd.DataFrame:
        """Calculate positions from portfolio weights"""

        # Calculate portfolio value at each time step
        portfolio_values = self._calculate_portfolio_values(weights)

        # Calculate positions
        positions = weights.mul(portfolio_values, axis=0).div(self.prices, axis=1)

        return positions.fillna(0)

    def _calculate_portfolio_values(self, weights: pd.DataFrame) -> pd.Series:
        """Calculate portfolio value over time"""

        # Initialize with initial capital
        portfolio_values = pd.Series(
            index=self.prices.index,
            data=self.config.initial_capital
        )

        # Calculate returns
        portfolio_returns = (weights * self.returns).sum(axis=1)

        # Compound returns
        for i in range(1, len(portfolio_values)):
            portfolio_values.iloc[i] = portfolio_values.iloc[i-1] * (1 + portfolio_returns.iloc[i])

        return portfolio_values

    def _calculate_returns_vectorized(self, positions: pd.DataFrame) -> pd.Series:
        """Calculate returns with transaction costs using vectorized operations"""

        # Calculate gross returns
        gross_returns = (positions.shift(1) * self.returns).sum(axis=1)

        # Calculate transaction costs
        transaction_costs = self._calculate_transaction_costs_vectorized(positions)

        # Net returns
        net_returns = gross_returns - transaction_costs

        return net_returns.fillna(0)

    def _calculate_portfolio_returns_vectorized(
        self,
        positions: pd.DataFrame,
        weights: pd.DataFrame
    ) -> pd.Series:
        """Calculate portfolio returns with transaction costs"""

        # Calculate gross portfolio returns
        gross_returns = (weights * self.returns).sum(axis=1)

        # Calculate transaction costs from weight changes
        weight_changes = weights.diff().abs().sum(axis=1)
        portfolio_values = self._calculate_portfolio_values(weights)
        transaction_costs = weight_changes * portfolio_values * self.transaction_cost_config.commission_rate

        # Net returns
        net_returns = gross_returns - transaction_costs / portfolio_values.shift(1)

        return net_returns.fillna(0)

    def _calculate_transaction_costs_vectorized(self, positions: pd.DataFrame) -> pd.Series:
        """Calculate transaction costs using vectorized operations"""

        # Calculate position changes
        position_changes = positions.diff().abs()

        # Calculate transaction value
        transaction_values = position_changes.mul(self.prices, axis=1).sum(axis=1)

        # Apply commission
        commission = transaction_values * self.transaction_cost_config.commission_rate

        # Apply slippage (linear model)
        slippage = transaction_values * self.transaction_cost_config.slippage_rate

        # Total transaction costs
        total_costs = commission + slippage

        # Apply minimum commission
        total_costs = total_costs.clip(lower=self.transaction_cost_config.min_commission)

        return total_costs.fillna(0)

    def _calculate_performance_metrics_vectorized(self, returns: pd.Series) -> Dict[str, Any]:
        """Calculate performance metrics using vectorized operations"""

        # Basic metrics
        total_return = (1 + returns).prod() - 1
        n_days = len(returns)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1

        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Risk metrics
        var_95 = returns.quantile(0.05)
        var_99 = returns.quantile(0.01)

        # Downside risk
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0

        # Other metrics
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'var_95': var_95,
            'var_99': var_99,
            'sortino_ratio': sortino_ratio,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'returns': returns,
            'cumulative_returns': cumulative,
            'drawdown': drawdown
        }

    def _calculate_portfolio_performance_metrics(
        self,
        returns: pd.Series,
        weights: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""

        # Get basic performance metrics
        metrics = self._calculate_performance_metrics_vectorized(returns)

        # Add portfolio-specific metrics
        metrics.update({
            'weights_history': weights,
            'turnover': self._calculate_turnover(weights),
            'concentration': self._calculate_concentration(weights),
            'effective_assets': self._calculate_effective_assets(weights)
        })

        # Calculate benchmark-relative metrics if benchmark available
        if hasattr(self, 'benchmark_returns'):
            benchmark_returns = self.benchmark_returns.reindex(returns.index, fill_value=0)
            excess_returns = returns - benchmark_returns

            metrics.update({
                'alpha': excess_returns.mean() * 252,
                'beta': self._calculate_beta(returns, benchmark_returns),
                'tracking_error': excess_returns.std() * np.sqrt(252),
                'information_ratio': (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))
            })

        return metrics

    def _calculate_turnover(self, weights: pd.DataFrame) -> pd.Series:
        """Calculate portfolio turnover"""
        weight_changes = weights.diff().abs().sum(axis=1)
        return weight_changes

    def _calculate_concentration(self, weights: pd.DataFrame) -> pd.Series:
        """Calculate portfolio concentration (Herfindahl-Hirschman Index)"""
        return (weights ** 2).sum(axis=1)

    def _calculate_effective_assets(self, weights: pd.DataFrame) -> pd.Series:
        """Calculate effective number of assets"""
        concentration = self._calculate_concentration(weights)
        return 1 / concentration

    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to benchmark"""
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        if len(aligned_returns) == 0:
            return 0
        covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
        benchmark_variance = np.var(aligned_benchmark)
        return covariance / benchmark_variance if benchmark_variance > 0 else 0

    def _generate_parameter_combinations(
        self,
        config: ParameterSweepConfig
    ) -> List[Dict[str, Any]]:
        """Generate parameter combinations for sweep"""

        if config.sweep_type == "grid":
            # Generate all combinations
            from itertools import product
            keys = list(config.parameters.keys())
            values = list(config.parameters.values())
            combinations = list(product(*values))

            parameter_combinations = [
                dict(zip(keys, combo)) for combo in combinations
            ]

        elif config.sweep_type == "random":
            # Generate random combinations
            n_combinations = config.n_combinations or 100
            parameter_combinations = []

            for _ in range(n_combinations):
                combo = {}
                for key, value_range in config.parameters.items():
                    combo[key] = np.random.choice(value_range)
                parameter_combinations.append(combo)

        else:
            raise ValueError(f"Unsupported sweep type: {config.sweep_type}")

        # Limit combinations if specified
        if config.n_combinations and len(parameter_combinations) > config.n_combinations:
            parameter_combinations = parameter_combinations[:config.n_combinations]

        return parameter_combinations

    def _run_parallel_backtests(
        self,
        strategy: Callable,
        parameter_combinations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run backtests in parallel"""

        n_jobs = mp.cpu_count() if config.n_jobs == -1 else config.n_jobs

        results = []

        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            # Submit all tasks
            futures = []
            for params in parameter_combinations:
                future = executor.submit(self._run_single_backtest_with_params, strategy, params)
                futures.append((future, params))

            # Collect results
            for future, params in futures:
                try:
                    result = future.result()
                    results.append({
                        'parameters': params,
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Backtest failed for params {params}: {e}")
                    continue

        return results

    def _run_single_backtest_with_params(
        self,
        strategy: Callable,
        parameters: Dict[str, Any]
    ) -> BacktestResult:
        """Run single backtest with given parameters"""

        # Create strategy with parameters
        def parameterized_strategy(prices, returns, **kwargs):
            return strategy(prices, returns, **parameters, **kwargs)

        # Run backtest
        result = self._run_single_asset_backtest(parameterized_strategy)

        # Add parameters to result
        result.parameters = parameters

        return result

    def _find_best_parameters(
        self,
        results: List[Dict[str, Any]],
        objective_metric: str
    ) -> Dict[str, Any]:
        """Find best parameters based on objective metric"""

        # Sort results by objective metric
        sorted_results = sorted(
            results,
            key=lambda x: getattr(x['result'], objective_metric, 0),
            reverse=True
        )

        return sorted_results[0]

    def _create_result_from_metrics(self, metrics: Dict[str, Any]) -> BacktestResult:
        """Create BacktestResult from performance metrics"""

        return BacktestResult(
            total_return=metrics.get('total_return', 0),
            annualized_return=metrics.get('annualized_return', 0),
            volatility=metrics.get('volatility', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            max_drawdown=metrics.get('max_drawdown', 0),
            calmar_ratio=metrics.get('calmar_ratio', 0),
            var_95=metrics.get('var_95', 0),
            var_99=metrics.get('var_99', 0),
            expected_shortfall_95=0,  # Calculate if needed
            expected_shortfall_99=0,  # Calculate if needed
            total_trades=0,  # Calculate from trades
            win_rate=0,  # Calculate from trades
            avg_win=0,  # Calculate from trades
            avg_loss=0,  # Calculate from trades
            profit_factor=0,  # Calculate from trades
            equity_curve=metrics.get('cumulative_returns'),
            returns=metrics.get('returns'),
            positions=[],  # Convert from positions DataFrame
            trades=self.trades
        )

    def _validate_price_data(self, prices: pd.DataFrame) -> None:
        """Validate price data"""

        if prices.empty:
            raise ValueError("Price data is empty")

        if not isinstance(prices.index, pd.DatetimeIndex):
            raise ValueError("Price data must have DatetimeIndex")

        if prices.isnull().any().any():
            logger.warning("Price data contains null values")
            prices = prices.fillna(method='ffill').fillna(method='bfill')

        # Check for minimum data length
        if len(prices) < 30:
            raise ValueError("Price data must have at least 30 observations")

        # Check for positive prices
        if (prices <= 0).any().any():
            raise ValueError("Prices must be positive")

    def save_results(self, filepath: str) -> None:
        """Save backtest results to file"""

        results_data = {
            'config': self.config.__dict__,
            'performance_metrics': self.performance_metrics,
            'optimization_results': self.optimization_results,
            'best_parameters': self.best_parameters
        }

        with open(filepath, 'wb') as f:
            pickle.dump(results_data, f)

        logger.info(f"Results saved to {filepath}")

    def load_results(self, filepath: str) -> None:
        """Load backtest results from file"""

        with open(filepath, 'rb') as f:
            results_data = pickle.load(f)

        self.performance_metrics = results_data.get('performance_metrics', {})
        self.optimization_results = results_data.get('optimization_results', [])
        self.best_parameters = results_data.get('best_parameters')

        logger.info(f"Results loaded from {filepath}")


# Vectorized strategy examples
def moving_average_crossover_vectorized(prices: np.ndarray, returns: np.ndarray, fast_window: int = 20, slow_window: int = 50) -> np.ndarray:
    """
    Vectorized moving average crossover strategy

    Args:
        prices: Price array
        returns: Returns array
        fast_window: Fast MA window
        slow_window: Slow MA window

    Returns:
        Signals array (-1, 0, 1)
    """

    # Calculate moving averages using convolution
    fast_ma = np.convolve(prices, np.ones(fast_window)/fast_window, mode='same')
    slow_ma = np.convolve(prices, np.ones(slow_window)/slow_window, mode='same')

    # Generate signals
    signals = np.zeros(len(prices))
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma < slow_ma] = -1

    # Shift signals to avoid look-ahead bias
    signals = np.roll(signals, 1)
    signals[0] = 0

    return signals


def mean_reversion_vectorized(prices: np.ndarray, returns: np.ndarray, lookback: int = 20, threshold: float = 2.0) -> np.ndarray:
    """
    Vectorized mean reversion strategy

    Args:
        prices: Price array
        returns: Returns array
        lookback: Lookback window for mean calculation
        threshold: Standard deviation threshold

    Returns:
        Signals array (-1, 0, 1)
    """

    # Calculate rolling mean and standard deviation
    mean_prices = np.convolve(prices, np.ones(lookback)/lookback, mode='same')
    std_prices = np.array([np.std(prices[max(0, i-lookback):i+1]) for i in range(len(prices))])

    # Calculate z-score
    z_score = (prices - mean_prices) / std_prices

    # Generate signals
    signals = np.zeros(len(prices))
    signals[z_score < -threshold] = 1  # Buy when oversold
    signals[z_score > threshold] = -1  # Sell when overbought

    # Shift signals to avoid look-ahead bias
    signals = np.roll(signals, 1)
    signals[0] = 0

    return signals


@nb.jit(nopython=True)
def calculate_returns_numba(prices: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """
    Numba-optimized returns calculation

    Args:
        prices: Price array
        positions: Position array

    Returns:
        Returns array
    """

    n = len(prices)
    returns = np.zeros(n)

    for i in range(1, n):
        if positions[i-1] != 0:
            returns[i] = positions[i-1] * (prices[i] - prices[i-1]) / prices[i-1]

    return returns


__all__ = [
    'VectorizedBacktestEngine',
    'VectorizedBacktestMode',
    'TransactionCostConfig',
    'PortfolioConfig',
    'ParameterSweepConfig',
    'moving_average_crossover_vectorized',
    'mean_reversion_vectorized',
    'calculate_returns_numba'
]