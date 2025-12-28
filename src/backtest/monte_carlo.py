"""
Monte Carlo Simulation Module

This module provides Monte Carlo simulation capabilities for
strategy performance analysis and risk assessment.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns

from ..risk.risk_metrics import RiskMetrics


@dataclass
class MCSimulationConfig:
    """Configuration for Monte Carlo simulation"""
    n_simulations: int = 10000
    time_horizon: int = 252  # trading days
    confidence_levels: List[float] = None
    return_method: str = 'bootstrap'  # 'bootstrap', 'parametric', 'historical'
    volatility_window: int = 60
    random_seed: Optional[int] = None

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.90, 0.95, 0.99]

        if self.random_seed is not None:
            np.random.seed(self.random_seed)


@dataclass
class MCResults:
    """Results from Monte Carlo simulation"""
    final_values: np.ndarray
    equity_curves: np.ndarray
    statistics: Dict[str, float]
    confidence_intervals: Dict[float, Tuple[float, float]]
    drawdowns: np.ndarray
    var: Dict[float, float]  # Value at Risk
    cvar: Dict[float, float]  # Conditional Value at Risk
    success_probability: Dict[str, float]  # Probability of meeting targets


class MonteCarloSimulator:
    """Monte Carlo simulation engine for trading strategies"""

    def __init__(self, config: Optional[MCSimulationConfig] = None):
        """
        Initialize Monte Carlo Simulator

        Args:
            config: Simulation configuration
        """
        self.config = config or MCSimulationConfig()
        self.risk_calculator = RiskMetrics()

    def simulate_bootstrap(
        self,
        returns: pd.Series,
        initial_capital: float = 100000,
        **kwargs
    ) -> MCResults:
        """
        Bootstrap simulation using historical returns

        Args:
            returns: Historical strategy returns
            initial_capital: Starting capital
            **kwargs: Additional simulation parameters

        Returns:
            MCResults: Simulation results
        """
        n_sim = self.config.n_simulations
        n_days = self.config.time_horizon

        # Generate random paths using bootstrap
        equity_curves = np.zeros((n_sim, n_days))
        equity_curves[:, 0] = initial_capital

        for i in range(n_sim):
            # Sample returns with replacement
            sampled_returns = np.random.choice(returns, size=n_days-1, replace=True)

            # Generate equity curve
            daily_returns = 1 + sampled_returns
            equity_curves[i, 1:] = initial_capital * np.cumprod(daily_returns)

        return self._analyze_results(equity_curves, initial_capital)

    def simulate_parametric(
        self,
        returns: pd.Series,
        initial_capital: float = 100000,
        distribution: str = 'normal',
        **kwargs
    ) -> MCResults:
        """
        Parametric simulation using distribution fitting

        Args:
            returns: Historical strategy returns
            initial_capital: Starting capital
            distribution: Distribution type ('normal', 't', 'skew_t')
            **kwargs: Additional distribution parameters

        Returns:
            MCResults: Simulation results
        """
        n_sim = self.config.n_simulations
        n_days = self.config.time_horizon

        # Calculate statistics
        mean_return = returns.mean()
        std_return = returns.std()

        # Generate correlated returns for each simulation
        if distribution == 'normal':
            simulated_returns = np.random.normal(
                mean_return, std_return, (n_sim, n_days-1)
            )
        elif distribution == 't':
            df = kwargs.get('df', 5)  # degrees of freedom
            simulated_returns = mean_return + std_return * np.random.standard_t(
                df, (n_sim, n_days-1)
            ) / np.sqrt(df / (df - 2))
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")

        # Generate equity curves
        equity_curves = np.zeros((n_sim, n_days))
        equity_curves[:, 0] = initial_capital

        daily_returns = 1 + simulated_returns
        equity_curves[:, 1:] = initial_capital * np.cumprod(daily_returns, axis=1)

        return self._analyze_results(equity_curves, initial_capital)

    def simulate_geometric_brownian(
        self,
        returns: pd.Series,
        initial_capital: float = 100000,
        **kwargs
    ) -> MCResults:
        """
        Geometric Brownian Motion simulation

        Args:
            returns: Historical returns
            initial_capital: Starting capital
            **kwargs: Additional parameters

        Returns:
            MCResults: Simulation results
        """
        n_sim = self.config.n_simulations
        n_days = self.config.time_horizon
        dt = 1/252  # daily time step

        # Calculate parameters from historical returns
        mu = returns.mean() * 252  # annual drift
        sigma = returns.std() * np.sqrt(252)  # annual volatility

        # Generate random shocks
        Z = np.random.standard_normal((n_sim, n_days-1))

        # Generate paths using GBM formula
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * Z

        # Calculate log returns and convert to prices
        log_returns = drift + diffusion
        equity_curves = np.zeros((n_sim, n_days))
        equity_curves[:, 0] = initial_capital
        equity_curves[:, 1:] = initial_capital * np.exp(np.cumsum(log_returns, axis=1))

        return self._analyze_results(equity_curves, initial_capital)

    def simulate_parallel(
        self,
        method: str,
        returns: pd.Series,
        initial_capital: float = 100000,
        n_workers: Optional[int] = None,
        **kwargs
    ) -> MCResults:
        """
        Run Monte Carlo simulation in parallel

        Args:
            method: Simulation method
            returns: Historical returns
            initial_capital: Starting capital
            n_workers: Number of parallel workers
            **kwargs: Additional parameters

        Returns:
            MCResults: Combined simulation results
        """
        if n_workers is None:
            n_workers = min(mp.cpu_count(), 8)

        n_sim = self.config.n_simulations
        sims_per_worker = n_sim // n_workers

        # Split simulations across workers
        tasks = []
        for i in range(n_workers):
            start = i * sims_per_worker
            end = (i + 1) * sims_per_worker if i < n_workers - 1 else n_sim

            # Create config for this worker
            worker_config = MCSimulationConfig(
                n_simulations=end - start,
                time_horizon=self.config.time_horizon,
                confidence_levels=self.config.confidence_levels,
                return_method=self.config.return_method,
                volatility_window=self.config.volatility_window,
                random_seed=self.config.random_seed + i if self.config.random_seed else None
            )

            tasks.append({
                'method': method,
                'returns': returns,
                'initial_capital': initial_capital,
                'config': worker_config,
                'kwargs': kwargs
            })

        # Run simulations in parallel
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(self._worker_simulation, task) for task in tasks]

            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    warnings.warn(f"Simulation worker failed: {e}")
                    continue

        # Combine results
        all_equity_curves = []
        all_final_values = []
        all_drawdowns = []

        for result in results:
            all_equity_curves.append(result.equity_curves)
            all_final_values.append(result.final_values)
            all_drawdowns.append(result.drawdowns)

        combined_equity = np.vstack(all_equity_curves)
        combined_final = np.concatenate(all_final_values)
        combined_dd = np.vstack(all_drawdowns)

        # Recalculate statistics
        combined_stats = self._calculate_statistics(combined_final)
        combined_cis = self._calculate_confidence_intervals(combined_final)
        combined_var = self._calculate_var(combined_final)
        combined_cvar = self._calculate_cvar(combined_final)
        combined_success = self._calculate_success_probability(combined_final)

        return MCResults(
            final_values=combined_final,
            equity_curves=combined_equity,
            statistics=combined_stats,
            confidence_intervals=combined_cis,
            drawdowns=combined_dd,
            var=combined_var,
            cvar=combined_cvar,
            success_probability=combined_success
        )

    def _worker_simulation(self, task: Dict) -> MCResults:
        """Worker function for parallel simulation"""
        # Create temporary simulator with worker config
        temp_simulator = MonteCarloSimulator(task['config'])

        if task['method'] == 'bootstrap':
            return temp_simulator.simulate_bootstrap(
                task['returns'],
                task['initial_capital'],
                **task['kwargs']
            )
        elif task['method'] == 'parametric':
            return temp_simulator.simulate_parametric(
                task['returns'],
                task['initial_capital'],
                **task['kwargs']
            )
        elif task['method'] == 'gbm':
            return temp_simulator.simulate_geometric_brownian(
                task['returns'],
                task['initial_capital'],
                **task['kwargs']
            )
        else:
            raise ValueError(f"Unknown simulation method: {task['method']}")

    def _analyze_results(
        self,
        equity_curves: np.ndarray,
        initial_capital: float
    ) -> MCResults:
        """Analyze simulation results and calculate metrics"""
        final_values = equity_curves[:, -1]

        # Calculate statistics
        statistics = self._calculate_statistics(final_values)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(final_values)

        # Calculate drawdowns for each simulation
        drawdowns = self._calculate_drawdowns(equity_curves)

        # Calculate VaR and CVaR
        var = self._calculate_var(final_values)
        cvar = self._calculate_cvar(final_values)

        # Calculate success probabilities
        success_probability = self._calculate_success_probability(final_values)

        return MCResults(
            final_values=final_values,
            equity_curves=equity_curves,
            statistics=statistics,
            confidence_intervals=confidence_intervals,
            drawdowns=drawdowns,
            var=var,
            cvar=cvar,
            success_probability=success_probability
        )

    def _calculate_statistics(self, final_values: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistics"""
        return {
            'mean': np.mean(final_values),
            'median': np.median(final_values),
            'std': np.std(final_values),
            'min': np.min(final_values),
            'max': np.max(final_values),
            'skewness': self._skewness(final_values),
            'kurtosis': self._kurtosis(final_values),
            'percentile_5': np.percentile(final_values, 5),
            'percentile_95': np.percentile(final_values, 95)
        }

    def _calculate_confidence_intervals(
        self,
        values: np.ndarray
    ) -> Dict[float, Tuple[float, float]]:
        """Calculate confidence intervals"""
        intervals = {}
        for level in self.config.confidence_levels:
            alpha = 1 - level
            lower = np.percentile(values, alpha/2 * 100)
            upper = np.percentile(values, (1 - alpha/2) * 100)
            intervals[level] = (lower, upper)
        return intervals

    def _calculate_drawdowns(self, equity_curves: np.ndarray) -> np.ndarray:
        """Calculate maximum drawdown for each simulation"""
        drawdowns = []

        for curve in equity_curves:
            peak = np.maximum.accumulate(curve)
            drawdown = (curve - peak) / peak
            drawdowns.append(drawdown)

        return np.array(drawdowns)

    def _calculate_var(self, final_values: np.ndarray) -> Dict[float, float]:
        """Calculate Value at Risk"""
        var = {}
        for level in self.config.confidence_levels:
            var[level] = -np.percentile(final_values, (1-level) * 100)
        return var

    def _calculate_cvar(self, final_values: np.ndarray) -> Dict[float, float]:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        cvar = {}
        for level in self.config.confidence_levels:
            var = np.percentile(final_values, (1-level) * 100)
            cvar[level] = -np.mean(final_values[final_values <= var])
        return cvar

    def _calculate_success_probability(
        self,
        final_values: np.ndarray,
        initial_capital: float = 100000
    ) -> Dict[str, float]:
        """Calculate probability of meeting various targets"""
        return {
            'positive_return': np.mean(final_values > initial_capital),
            'beating_10pct': np.mean(final_values > initial_capital * 1.10),
            'beating_20pct': np.mean(final_values > initial_capital * 1.20),
            'beating_50pct': np.mean(final_values > initial_capital * 1.50),
            'doubling': np.mean(final_values > initial_capital * 2.0),
            'halving': np.mean(final_values < initial_capital * 0.5)
        }

    def _skewness(self, x: np.ndarray) -> float:
        """Calculate skewness"""
        mean = np.mean(x)
        std = np.std(x)
        return np.mean(((x - mean) / std) ** 3)

    def _kurtosis(self, x: np.ndarray) -> float:
        """Calculate excess kurtosis"""
        mean = np.mean(x)
        std = np.std(x)
        return np.mean(((x - mean) / std) ** 4) - 3

    def generate_report(self, results: MCResults) -> Dict:
        """Generate comprehensive simulation report"""
        return {
            'summary': {
                'total_simulations': len(results.final_values),
                'time_horizon_days': self.config.time_horizon,
                'mean_final_value': results.statistics['mean'],
                'median_final_value': results.statistics['median'],
                'volatility': results.statistics['std'],
                'success_probability': results.success_probability['positive_return']
            },
            'risk_metrics': {
                'var_95': results.var[0.95],
                'var_99': results.var[0.99],
                'cvar_95': results.cvar[0.95],
                'cvar_99': results.cvar[0.99],
                'max_drawdown': np.min(results.drawdowns),
                'avg_max_drawdown': np.mean(np.min(results.drawdowns, axis=1))
            },
            'confidence_intervals': {
                f'confidence_{int(level*100)}': {
                    'lower': ci[0],
                    'upper': ci[1]
                } for level, ci in results.confidence_intervals.items()
            },
            'target_probabilities': results.success_probability,
            'distribution_stats': {
                'skewness': results.statistics['skewness'],
                'kurtosis': results.statistics['kurtosis'],
                'percentile_5': results.statistics['percentile_5'],
                'percentile_95': results.statistics['percentile_95']
            }
        }

    def plot_results(
        self,
        results: MCResults,
        n_paths_to_plot: int = 100,
        save_path: Optional[str] = None
    ) -> None:
        """Plot Monte Carlo simulation results"""
        plt.figure(figsize=(15, 10))

        # Plot 1: Sample paths
        plt.subplot(2, 3, 1)
        n_plot = min(n_paths_to_plot, len(results.equity_curves))
        indices = np.random.choice(len(results.equity_curves), n_plot, replace=False)

        for idx in indices:
            plt.plot(results.equity_curves[idx], alpha=0.3, linewidth=0.5)

        plt.title(f'Sample {n_plot} Equity Curves')
        plt.xlabel('Days')
        plt.ylabel('Portfolio Value')

        # Plot 2: Final value distribution
        plt.subplot(2, 3, 2)
        plt.hist(results.final_values, bins=50, alpha=0.7, edgecolor='black')
        plt.axvline(np.mean(results.final_values), color='red', linestyle='--', label='Mean')
        plt.axvline(np.median(results.final_values), color='green', linestyle='--', label='Median')
        plt.title('Final Value Distribution')
        plt.xlabel('Final Portfolio Value')
        plt.ylabel('Frequency')
        plt.legend()

        # Plot 3: Drawdown distribution
        plt.subplot(2, 3, 3)
        max_drawdowns = np.min(results.drawdowns, axis=1)
        plt.hist(max_drawdowns * 100, bins=50, alpha=0.7, edgecolor='black')
        plt.title('Maximum Drawdown Distribution')
        plt.xlabel('Maximum Drawdown (%)')
        plt.ylabel('Frequency')

        # Plot 4: Percentiles over time
        plt.subplot(2, 3, 4)
        percentiles = [5, 25, 50, 75, 95]
        for p in percentiles:
            plt.plot(np.percentile(results.equity_curves, p, axis=0), label=f'{p}th percentile')

        plt.title('Equity Curve Percentiles')
        plt.xlabel('Days')
        plt.ylabel('Portfolio Value')
        plt.legend()

        # Plot 5: Heatmap of returns
        plt.subplot(2, 3, 5)
        returns_matrix = results.equity_curves[:, 1:] / results.equity_curves[:, :-1] - 1
        sns.heatmap(
            returns_matrix[:50, :50],
            cmap='RdBu_r',
            center=0,
            cbar_kws={'label': 'Daily Return'}
        )
        plt.title('Returns Heatmap (First 50 Simulations/Days)')
        plt.xlabel('Day')
        plt.ylabel('Simulation')

        # Plot 6: Cumulative probability
        plt.subplot(2, 3, 6)
        sorted_values = np.sort(results.final_values)
        cumulative = np.arange(1, len(sorted_values) + 1) / len(sorted_values)
        plt.plot(sorted_values, cumulative)
        plt.axvline(np.percentile(results.final_values, 5), color='red', linestyle='--', alpha=0.5, label='5th percentile')
        plt.axvline(np.percentile(results.final_values, 95), color='red', linestyle='--', alpha=0.5, label='95th percentile')
        plt.title('Cumulative Distribution')
        plt.xlabel('Final Portfolio Value')
        plt.ylabel('Cumulative Probability')
        plt.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()


# Convenience function for quick simulation
def run_monte_carlo(
    returns: pd.Series,
    method: str = 'bootstrap',
    n_simulations: int = 10000,
    time_horizon: int = 252,
    initial_capital: float = 100000,
    parallel: bool = False,
    **kwargs
) -> MCResults:
    """
    Quick Monte Carlo simulation

    Args:
        returns: Historical returns
        method: Simulation method ('bootstrap', 'parametric', 'gbm')
        n_simulations: Number of simulations
        time_horizon: Simulation horizon in days
        initial_capital: Starting capital
        parallel: Use parallel processing
        **kwargs: Additional parameters

    Returns:
        MCResults: Simulation results
    """
    config = MCSimulationConfig(
        n_simulations=n_simulations,
        time_horizon=time_horizon
    )

    simulator = MonteCarloSimulator(config)

    if parallel:
        return simulator.simulate_parallel(
            method, returns, initial_capital, **kwargs
        )

    if method == 'bootstrap':
        return simulator.simulate_bootstrap(returns, initial_capital, **kwargs)
    elif method == 'parametric':
        return simulator.simulate_parametric(returns, initial_capital, **kwargs)
    elif method == 'gbm':
        return simulator.simulate_geometric_brownian(returns, initial_capital, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")


__all__ = [
    'MonteCarloSimulator',
    'MCSimulationConfig',
    'MCResults',
    'run_monte_carlo'
]