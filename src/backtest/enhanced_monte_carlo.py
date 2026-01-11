"""
Enhanced Monte Carlo Simulation System with VectorBT Integration
===========================================================

Advanced parallel Monte Carlo simulation system featuring:
- VectorBT-powered vectorized operations
- Multi-process parallel execution
- Large-scale simulation support (10,000+ runs)
- Risk metrics and sensitivity analysis
- Statistical analysis tools

Author: Claude Code Assistant
Date: 2025-01-19
"""

import asyncio
import logging
import multiprocessing as mp
import time
import warnings
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import numpy as np
import pandas as pd
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle
import uuid

# VectorBT imports
try:
    import vectorbt as vbt
    import vectorbt.records as vbt_recs
    import vectorbt.signals as vbt_sig
    import vectorbt.generic as vbt_gen
    from vectorbt.portfolio.enums import Direction
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None
    warnings.warn("VectorBT not installed. Install with: pip install vectorbt>=0.25.0")

# Scientific computing imports
from scipy import stats
from scipy.optimize import minimize
import sklearn.metrics as metrics
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Internal imports
from .monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults
from .parallel_processor import ParallelProcessor, ExecutionMode, TaskStatus

logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)


class SimulationMethod(str, Enum):
    """Simulation methods"""
    BOOTSTRAP = "bootstrap"
    PARAMETRIC_NORMAL = "parametric_normal"
    PARAMETRIC_T = "parametric_t"
    GEOMETRIC_BROWNIAN = "geometric_brownian"
    VECTORBT_RESAMPLE = "vectorbt_resample"
    VECTORBT_MONTECARLO = "vectorbt_montecarlo"


class RiskMeasure(str, Enum):
    """Risk measures"""
    VAR = "var"  # Value at Risk
    CVAR = "cvar"  # Conditional VaR
    MAX_DD = "max_dd"  # Maximum Drawdown
    DOWNSIDE_DEV = "downside_dev"  # Downside Deviation
    FIRST_LOWER_PARTIAL_MOMENT = "flpm"  # First Lower Partial Moment


@dataclass
class EnhancedMCConfig:
    """Enhanced configuration for Monte Carlo simulation"""
    # Basic config
    n_simulations: int = 10000
    time_horizon: int = 252  # trading days
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95, 0.99])

    # Parallel execution
    n_workers: int = field(default_factory=lambda: min(32, mp.cpu_count()))
    chunk_size: int = 1000  # Simulations per worker
    enable_memory_optimization: bool = True
    memory_limit_per_worker: float = 2048  # MB

    # VectorBT settings
    use_vectorbt: bool = True
    vectorbt_settings: Dict[str, Any] = field(default_factory=dict)
    cache_data: bool = True

    # Advanced features
    enable_sensitivity_analysis: bool = True
    sensitivity_params: List[str] = field(default_factory=lambda: ['volatility', 'mean', 'skewness'])
    enable_stress_testing: bool = True
    stress_scenarios: Dict[str, Dict] = field(default_factory=dict)

    # Output
    save_intermediate: bool = False
    output_dir: str = "monte_carlo_results"
    random_seed: Optional[int] = None


@dataclass
class SimulationScenario:
    """Simulation scenario definition"""
    name: str
    params: Dict[str, Any]
    weights: Optional[np.ndarray] = None  # For portfolio scenarios

    # Scenario metadata
    description: Optional[str] = None
    category: str = "custom"  # 'stress', 'optimistic', 'pessimistic', 'custom'


@dataclass
class SensitivityResult:
    """Sensitivity analysis result"""
    param_name: str
    param_values: np.ndarray
    results: List[MCResults]
    sensitivities: Dict[str, float]  # Sensitivity metrics
    correlations: Optional[pd.DataFrame] = None

    # Visualisation data
    scenario_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedMCResults(MCResults):
    """Enhanced Monte Carlo results with additional metrics"""
    # Original results
    final_values: np.ndarray
    equity_curves: np.ndarray
    statistics: Dict[str, float]
    confidence_intervals: Dict[float, Tuple[float, float]]
    drawdowns: np.ndarray
    var: Dict[float, float]
    cvar: Dict[float, float]
    success_probability: Dict[str, float]

    # Enhanced metrics
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    performance_attribution: Dict[str, float] = field(default_factory=dict)
    scenario_results: Dict[str, MCResults] = field(default_factory=dict)
    sensitivity_results: Optional[SensitivityResult] = None

    # Distribution analysis
    distribution_fits: Dict[str, Dict] = field(default_factory=dict)
    tail_metrics: Dict[str, float] = field(default_factory=dict)

    # VectorBT specific
    vectorbt_metrics: Optional[Dict[str, Any]] = None

    # Execution metadata
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class VectorBTMonteCarlo:
    """VectorBT-specific Monte Carlo operations"""

    def __init__(self, price_data: pd.DataFrame, **settings):
        """
        Initialize VectorBT Monte Carlo

        Args:
            price_data: DataFrame with price data (OHLCV)
            **settings: VectorBT settings
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for this class")

        self.price_data = price_data
        self.settings = settings

        # Calculate basic metrics
        self.returns = price_data['close'].pct_change().dropna()
        self.log_returns = np.log(price_data['close'] / price_data['close'].shift(1)).dropna()

    def generate_paths_vectorized(
        self,
        n_paths: int,
        n_steps: int,
        method: str = 'geometric_brownian',
        **params
    ) -> np.ndarray:
        """
        Generate Monte Carlo paths using VectorBT vectorization

        Args:
            n_paths: Number of paths to generate
            n_steps: Number of time steps
            method: Generation method
            **params: Method parameters

        Returns:
            Array of shape (n_paths, n_steps) with generated paths
        """
        if method == 'geometric_brownian':
            return self._gbm_paths_vectorized(n_paths, n_steps, **params)
        elif method == 'resample':
            return self._resample_paths_vectorized(n_paths, n_steps, **params)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _gbm_paths_vectorized(
        self,
        n_paths: int,
        n_steps: int,
        mu: Optional[float] = None,
        sigma: Optional[float] = None,
        dt: float = 1/252
    ) -> np.ndarray:
        """Generate GBM paths using vectorized operations"""
        if mu is None:
            mu = self.returns.mean() * 252
        if sigma is None:
            sigma = self.returns.std() * np.sqrt(252)

        # Generate all random shocks at once
        Z = np.random.standard_normal((n_paths, n_steps))

        # Vectorized GBM formula
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * Z

        # Calculate log returns and convert to prices
        log_returns = drift + diffusion
        price_paths = np.exp(np.cumsum(log_returns, axis=1))

        # Normalize to starting price of 1
        price_paths = np.hstack([np.ones((n_paths, 1)), price_paths])

        return price_paths

    def _resample_paths_vectorized(
        self,
        n_paths: int,
        n_steps: int,
        block_size: int = 20
    ) -> np.ndarray:
        """Generate paths using block bootstrap"""
        paths = []
        n_blocks = n_steps // block_size + 1

        for _ in range(n_paths):
            # Randomly sample blocks
            block_starts = np.random.choice(
                len(self.returns) - block_size,
                size=n_blocks,
                replace=True
            )

            # Combine blocks
            sampled_returns = []
            for start in block_starts[:n_steps // block_size]:
                block = self.returns.iloc[start:start + block_size].values
                sampled_returns.extend(block)

            # Pad if necessary
            if len(sampled_returns) < n_steps:
                sampled_returns.extend([0] * (n_steps - len(sampled_returns)))

            # Convert to price path
            price_path = np.cumprod(1 + np.array(sampled_returns[:n_steps]))
            price_path = np.insert(price_path, 0, 1)  # Starting price of 1
            paths.append(price_path)

        return np.array(paths)

    def calculate_risk_metrics_vectorized(
        self,
        equity_curves: np.ndarray,
        confidence_levels: List[float] = [0.90, 0.95, 0.99]
    ) -> Dict[str, np.ndarray]:
        """
        Calculate risk metrics using VectorBT vectorization

        Args:
            equity_curves: Array of equity curves
            confidence_levels: Confidence levels for VaR/CVaR

        Returns:
            Dictionary of risk metrics
        """
        # Calculate returns
        returns = equity_curves[:, 1:] / equity_curves[:, :-1] - 1

        metrics = {}

        # VaR for each confidence level
        for level in confidence_levels:
            metrics[f'var_{int(level*100)}'] = -np.percentile(returns, (1-level) * 100, axis=1)
            metrics[f'cvar_{int(level*100)}'] = -np.mean(
                np.sort(returns, axis=1)[:, :int((1-level) * returns.shape[1])],
                axis=1
            )

        # Maximum drawdown
        peak = np.maximum.accumulate(equity_curves, axis=1)
        drawdown = (equity_curves - peak) / peak
        metrics['max_drawdown'] = np.min(drawdown, axis=1)
        metrics['avg_drawdown'] = np.mean(drawdown[drawdown < 0], axis=1)

        # Sharpe ratio (annualized)
        mean_return = np.mean(returns, axis=1) * 252
        return_std = np.std(returns, axis=1) * np.sqrt(252)
        metrics['sharpe_ratio'] = mean_return / (return_std + 1e-8)

        # Sortino ratio
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        downside_std = np.std(downside_returns, axis=1) * np.sqrt(252)
        metrics['sortino_ratio'] = mean_return / (downside_std + 1e-8)

        # Calmar ratio
        metrics['calmar_ratio'] = mean_return / (np.abs(metrics['max_drawdown']) + 1e-8)

        return metrics

    def portfolio_optimization_monte_carlo(
        self,
        returns: pd.DataFrame,
        n_simulations: int = 10000,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Any]:
        """
        Monte Carlo portfolio optimization

        Args:
            returns: DataFrame of asset returns
            n_simulations: Number of portfolio simulations
            risk_free_rate: Risk-free rate

        Returns:
            Optimization results
        """
        n_assets = returns.shape[1]

        # Generate random weights
        weights = np.random.random((n_simulations, n_assets))
        weights = weights / weights.sum(axis=1, keepdims=True)

        # Calculate portfolio metrics
        port_returns = np.dot(weights, returns.mean() * 252)
        port_std = np.sqrt(np.dot(weights, np.dot(returns.cov() * 252, weights.T)))
        port_sharpe = (port_returns - risk_free_rate) / port_std

        # Find optimal portfolios
        max_sharpe_idx = np.argmax(port_sharpe)
        min_var_idx = np.argmin(port_std)

        results = {
            'optimal_sharpe': {
                'weights': weights[max_sharpe_idx],
                'return': port_returns[max_sharpe_idx],
                'volatility': port_std[max_sharpe_idx],
                'sharpe_ratio': port_sharpe[max_sharpe_idx]
            },
            'minimum_variance': {
                'weights': weights[min_var_idx],
                'return': port_returns[min_var_idx],
                'volatility': port_std[min_var_idx],
                'sharpe_ratio': port_sharpe[min_var_idx]
            },
            'all_weights': weights,
            'all_returns': port_returns,
            'all_volatilities': port_std,
            'all_sharpe_ratios': port_sharpe
        }

        return results


class EnhancedMonteCarloSimulator:
    """Enhanced Monte Carlo Simulator with VectorBT integration and parallel processing"""

    def __init__(self, config: Optional[EnhancedMCConfig] = None):
        """
        Initialize Enhanced Monte Carlo Simulator

        Args:
            config: Simulation configuration
        """
        self.config = config or EnhancedMCConfig()

        # Initialize components
        self.base_simulator = MonteCarloSimulator(
            MCSimulationConfig(
                n_simulations=self.config.n_simulations,
                time_horizon=self.config.time_horizon,
                confidence_levels=self.config.confidence_levels
            )
        )

        # Parallel processor
        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.n_workers,
            execution_mode=ExecutionMode.PROCESS,
            enable_resource_monitoring=True,
            max_memory_per_worker=self.config.memory_limit_per_worker
        )

        # Initialize random seed
        if self.config.random_seed:
            np.random.seed(self.config.random_seed)

        # Output directory
        if self.config.save_intermediate:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

        self.simulation_id = str(uuid.uuid4())[:8]

    async def simulate_parallel(
        self,
        returns: pd.Series,
        method: Union[SimulationMethod, str] = SimulationMethod.BOOTSTRAP,
        initial_capital: float = 100000,
        scenarios: Optional[List[SimulationScenario]] = None,
        **kwargs
    ) -> EnhancedMCResults:
        """
        Run enhanced parallel Monte Carlo simulation

        Args:
            returns: Historical returns
            method: Simulation method
            initial_capital: Starting capital
            scenarios: Additional scenarios to run
            **kwargs: Additional parameters

        Returns:
            Enhanced simulation results
        """
        start_time = time.time()
        method = SimulationMethod(method)

        logger.info(f"Starting enhanced Monte Carlo simulation: {method.value}")
        logger.info(f"Configuration: {self.config.n_simulations} simulations, {self.config.n_workers} workers")

        # Initialize parallel processor
        await self.parallel_processor.initialize()

        # Main simulation
        if self.config.use_vectorbt and VECTORBT_AVAILABLE:
            main_results = await self._run_vectorbt_simulation(
                returns, method, initial_capital, **kwargs
            )
        else:
            main_results = await self._run_standard_simulation(
                returns, method, initial_capital, **kwargs
            )

        # Scenario analysis
        scenario_results = {}
        if scenarios:
            logger.info(f"Running {len(scenarios)} scenario analyses")
            scenario_results = await self._run_scenarios(
                returns, scenarios, method, initial_capital, **kwargs
            )

        # Sensitivity analysis
        sensitivity_results = None
        if self.config.enable_sensitivity_analysis:
            logger.info("Running sensitivity analysis")
            sensitivity_results = await self._run_sensitivity_analysis(
                returns, method, initial_capital, **kwargs
            )

        # Stress testing
        if self.config.enable_stress_testing:
            logger.info("Running stress tests")
            await self._run_stress_tests(returns, initial_capital)

        # Aggregate results
        enhanced_results = self._aggregate_enhanced_results(
            main_results, scenario_results, sensitivity_results, start_time
        )

        # Save results if configured
        if self.config.save_intermediate:
            await self._save_results(enhanced_results)

        # Shutdown parallel processor
        await self.parallel_processor.shutdown()

        execution_time = time.time() - start_time
        logger.info(f"Simulation completed in {execution_time:.2f}s")

        return enhanced_results

    async def _run_vectorbt_simulation(
        self,
        returns: pd.Series,
        method: SimulationMethod,
        initial_capital: float,
        **kwargs
    ) -> MCResults:
        """Run simulation using VectorBT"""
        # Convert returns to price data for VectorBT
        prices = (1 + returns).cumprod() * initial_capital
        price_df = pd.DataFrame({'close': prices})

        # Create VectorBT Monte Carlo instance
        vbt_mc = VectorBTMonteCarlo(price_df, **self.config.vectorbt_settings)

        # Generate paths
        if method == SimulationMethod.GEOMETRIC_BROWNIAN:
            equity_curves = vbt_mc.generate_paths_vectorized(
                self.config.n_simulations,
                self.config.time_horizon,
                method='geometric_brownian',
                **kwargs
            )
        elif method == SimulationMethod.VECTORBT_RESAMPLE:
            equity_curves = vbt_mc.generate_paths_vectorized(
                self.config.n_simulations,
                self.config.time_horizon,
                method='resample',
                **kwargs
            )
        else:
            # Fall back to standard method
            return await self._run_standard_simulation(returns, method, initial_capital, **kwargs)

        # Scale to initial capital
        equity_curves *= initial_capital

        # Calculate results
        final_values = equity_curves[:, -1]

        # Use VectorBT for risk metrics
        risk_metrics = vbt_mc.calculate_risk_metrics_vectorized(
            equity_curves,
            self.config.confidence_levels
        )

        # Convert to MCResults format
        statistics = self._calculate_statistics(final_values)
        confidence_intervals = self._calculate_confidence_intervals(final_values)
        drawdowns = self._calculate_drawdowns(equity_curves)
        var = {level: -risk_metrics[f'var_{int(level*100)}'].mean() for level in self.config.confidence_levels}
        cvar = {level: -risk_metrics[f'cvar_{int(level*100)}'].mean() for level in self.config.confidence_levels}
        success_probability = self._calculate_success_probability(final_values, initial_capital)

        # Store VectorBT metrics
        vectorbt_metrics = {
            'avg_sharpe_ratio': np.mean(risk_metrics['sharpe_ratio']),
            'avg_sortino_ratio': np.mean(risk_metrics['sortino_ratio']),
            'avg_calmar_ratio': np.mean(risk_metrics['calmar_ratio']),
            'all_risk_metrics': risk_metrics
        }

        results = MCResults(
            final_values=final_values,
            equity_curves=equity_curves,
            statistics=statistics,
            confidence_intervals=confidence_intervals,
            drawdowns=drawdowns,
            var=var,
            cvar=cvar,
            success_probability=success_probability
        )

        # Store VectorBT metrics
        results.vectorbt_metrics = vectorbt_metrics

        return results

    async def _run_standard_simulation(
        self,
        returns: pd.Series,
        method: SimulationMethod,
        initial_capital: float,
        **kwargs
    ) -> MCResults:
        """Run simulation using parallel processing"""
        # Split simulations across workers
        n_workers = self.config.n_workers
        sims_per_worker = self.config.n_simulations // n_workers

        tasks = []
        for i in range(n_workers):
            start = i * sims_per_worker
            end = (i + 1) * sims_per_worker if i < n_workers - 1 else self.config.n_simulations

            # Create worker config
            worker_config = MCSimulationConfig(
                n_simulations=end - start,
                time_horizon=self.config.time_horizon,
                confidence_levels=self.config.confidence_levels,
                return_method=method.value.replace('_', ' '),
                random_seed=self.config.random_seed + i if self.config.random_seed else None
            )

            task_data = (
                f"mc_sim_{i}_{self.simulation_id}",
                self._worker_simulation,
                (method, returns, initial_capital, worker_config, kwargs)
            )
            tasks.append(task_data)

        # Execute in parallel
        task_results = await self.parallel_processor.process_batch(
            tasks,
            max_concurrent=n_workers
        )

        # Combine results
        all_equity_curves = []
        all_final_values = []
        all_drawdowns = []

        for task_id, result in task_results.items():
            if result.status == TaskStatus.COMPLETED and result.result:
                all_equity_curves.append(result.result.equity_curves)
                all_final_values.append(result.result.final_values)
                all_drawdowns.append(result.result.drawdowns)

        combined_equity = np.vstack(all_equity_curves)
        combined_final = np.concatenate(all_final_values)
        combined_dd = np.vstack(all_drawdowns)

        # Calculate combined statistics
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

    @staticmethod
    def _worker_simulation(
        method: SimulationMethod,
        returns: pd.Series,
        initial_capital: float,
        config: MCSimulationConfig,
        kwargs: Dict[str, Any]
    ) -> MCResults:
        """Worker function for parallel simulation"""
        temp_simulator = MonteCarloSimulator(config)

        if method == SimulationMethod.BOOTSTRAP:
            return temp_simulator.simulate_bootstrap(
                returns, initial_capital, **kwargs
            )
        elif method == SimulationMethod.PARAMETRIC_NORMAL:
            return temp_simulator.simulate_parametric(
                returns, initial_capital, distribution='normal', **kwargs
            )
        elif method == SimulationMethod.PARAMETRIC_T:
            return temp_simulator.simulate_parametric(
                returns, initial_capital, distribution='t', **kwargs
            )
        elif method == SimulationMethod.GEOMETRIC_BROWNIAN:
            return temp_simulator.simulate_geometric_brownian(
                returns, initial_capital, **kwargs
            )
        else:
            raise ValueError(f"Unknown simulation method: {method}")

    async def _run_scenarios(
        self,
        returns: pd.Series,
        scenarios: List[SimulationScenario],
        method: SimulationMethod,
        initial_capital: float,
        **kwargs
    ) -> Dict[str, MCResults]:
        """Run scenario analyses"""
        results = {}

        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario.name}")

            # Apply scenario parameters
            scenario_returns = self._apply_scenario(returns, scenario)

            # Run simulation with scenario returns
            if self.config.use_vectorbt and VECTORBT_AVAILABLE:
                scenario_result = await self._run_vectorbt_simulation(
                    scenario_returns, method, initial_capital, **kwargs
                )
            else:
                scenario_result = await self._run_standard_simulation(
                    scenario_returns, method, initial_capital, **kwargs
                )

            results[scenario.name] = scenario_result

        return results

    def _apply_scenario(
        self,
        returns: pd.Series,
        scenario: SimulationScenario
    ) -> pd.Series:
        """Apply scenario adjustments to returns"""
        scenario_returns = returns.copy()

        # Adjust mean return
        if 'mean_adjustment' in scenario.params:
            scenario_returns += scenario.params['mean_adjustment']

        # Adjust volatility
        if 'volatility_multiplier' in scenario.params:
            scenario_returns *= scenario.params['volatility_multiplier']

        # Add specific stress events
        if 'stress_events' in scenario.params:
            for event in scenario.params['stress_events']:
                start = event.get('start')
                end = event.get('end')
                adjustment = event.get('adjustment', 0)

                if start and end:
                    scenario_returns.loc[start:end] += adjustment

        # Apply weights if provided (for portfolio scenarios)
        if scenario.weights is not None and len(scenario.weights) > 1:
            # This is a simplified approach - in practice, you'd have multiple return series
            pass

        return scenario_returns

    async def _run_sensitivity_analysis(
        self,
        returns: pd.Series,
        method: SimulationMethod,
        initial_capital: float,
        **kwargs
    ) -> SensitivityResult:
        """Run sensitivity analysis on key parameters"""
        sensitivity_results = {}

        for param in self.config.sensitivity_params:
            logger.info(f"Analyzing sensitivity to {param}")

            if param == 'volatility':
                param_values = np.linspace(0.5, 2.0, 10)  # Volatility multipliers
                param_results = []

                for value in param_values:
                    adjusted_returns = returns * value
                    if self.config.use_vectorbt and VECTORBT_AVAILABLE:
                        result = await self._run_vectorbt_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    else:
                        result = await self._run_standard_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    param_results.append(result)

                # Calculate sensitivities
                final_values = [r.final_values.mean() for r in param_results]
                sharpe_ratios = [r.statistics.get('sharpe', 0) for r in param_results]

                sensitivity_results[param] = {
                    'param_values': param_values,
                    'final_values': final_values,
                    'sharpe_ratios': sharpe_ratios,
                    'sensitivity_final': np.polyfit(param_values, final_values, 1)[0],
                    'sensitivity_sharpe': np.polyfit(param_values, sharpe_ratios, 1)[0]
                }

            elif param == 'mean':
                param_values = np.linspace(-0.001, 0.003, 10)  # Mean adjustments
                param_results = []

                for value in param_values:
                    adjusted_returns = returns + value
                    if self.config.use_vectorbt and VECTORBT_AVAILABLE:
                        result = await self._run_vectorbt_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    else:
                        result = await self._run_standard_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    param_results.append(result)

                # Calculate sensitivities
                final_values = [r.final_values.mean() for r in param_results]
                sharpe_ratios = [r.statistics.get('sharpe', 0) for r in param_results]

                sensitivity_results[param] = {
                    'param_values': param_values,
                    'final_values': final_values,
                    'sharpe_ratios': sharpe_ratios,
                    'sensitivity_final': np.polyfit(param_values, final_values, 1)[0],
                    'sensitivity_sharpe': np.polyfit(param_values, sharpe_ratios, 1)[0]
                }

            elif param == 'skewness':
                # Adjust skewness by adding specific return patterns
                param_values = np.linspace(-2, 2, 10)
                param_results = []

                for value in param_values:
                    # Simple skewness adjustment - add occasional large returns
                    adjusted_returns = returns.copy()
                    if value > 0:
                        # Add positive skew
                        n_large = int(len(returns) * abs(value) * 0.01)
                        large_returns = np.random.choice(len(returns), n_large, replace=False)
                        adjusted_returns.iloc[large_returns] += 0.05  # 5% positive returns
                    elif value < 0:
                        # Add negative skew
                        n_large = int(len(returns) * abs(value) * 0.01)
                        large_returns = np.random.choice(len(returns), n_large, replace=False)
                        adjusted_returns.iloc[large_returns] -= 0.05  # -5% negative returns

                    if self.config.use_vectorbt and VECTORBT_AVAILABLE:
                        result = await self._run_vectorbt_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    else:
                        result = await self._run_standard_simulation(
                            adjusted_returns, method, initial_capital, **kwargs
                        )
                    param_results.append(result)

                # Calculate sensitivities
                final_values = [r.final_values.mean() for r in param_results]
                sharpe_ratios = [r.statistics.get('sharpe', 0) for r in param_results]

                sensitivity_results[param] = {
                    'param_values': param_values,
                    'final_values': final_values,
                    'sharpe_ratios': sharpe_ratios,
                    'sensitivity_final': np.polyfit(param_values, final_values, 1)[0],
                    'sensitivity_sharpe': np.polyfit(param_values, sharpe_ratios, 1)[0]
                }

        # Create SensitivityResult object
        sensitivity_result = SensitivityResult(
            param_name="multi_parameter",
            param_values=np.array([]),
            results=[],
            sensitivities=sensitivity_results,
            correlations=pd.DataFrame(sensitivity_results).T if sensitivity_results else None
        )

        return sensitivity_result

    async def _run_stress_tests(
        self,
        returns: pd.Series,
        initial_capital: float
    ):
        """Run predefined stress test scenarios"""
        stress_scenarios = self.config.stress_scenarios or {
            'crash': {
                'mean_adjustment': -0.02,
                'volatility_multiplier': 3.0
            },
            'bull_market': {
                'mean_adjustment': 0.01,
                'volatility_multiplier': 0.5
            },
            'high_volatility': {
                'volatility_multiplier': 5.0
            }
        }

        for scenario_name, scenario_params in stress_scenarios.items():
            logger.info(f"Running stress test: {scenario_name}")

            scenario = SimulationScenario(
                name=scenario_name,
                params=scenario_params,
                category="stress"
            )

            # Apply and run (results are stored internally or logged)
            scenario_returns = self._apply_scenario(returns, scenario)

            # Here you could store results or generate alerts
            # For brevity, just logging
            logger.info(f"Stress test {scenario_name} completed")

    def _aggregate_enhanced_results(
        self,
        main_results: MCResults,
        scenario_results: Dict[str, MCResults],
        sensitivity_results: Optional[SensitivityResult],
        start_time: float
    ) -> EnhancedMCResults:
        """Aggregate all results into EnhancedMCResults"""
        # Calculate additional risk metrics
        risk_metrics = self._calculate_enhanced_risk_metrics(main_results)

        # Performance attribution
        performance_attribution = self._calculate_performance_attribution(main_results)

        # Distribution analysis
        distribution_fits = self._analyze_distributions(main_results.final_values)

        # Tail metrics
        tail_metrics = self._calculate_tail_metrics(main_results.final_values)

        # Execution stats
        execution_stats = {
            'execution_time': time.time() - start_time,
            'simulations_per_second': self.config.n_simulations / (time.time() - start_time),
            'n_workers_used': self.config.n_workers,
            'memory_optimized': self.config.enable_memory_optimization,
            'vectorbt_used': self.config.use_vectorbt and VECTORBT_AVAILABLE
        }

        # Create enhanced results
        enhanced_results = EnhancedMCResults(
            final_values=main_results.final_values,
            equity_curves=main_results.equity_curves,
            statistics=main_results.statistics,
            confidence_intervals=main_results.confidence_intervals,
            drawdowns=main_results.drawdowns,
            var=main_results.var,
            cvar=main_results.cvar,
            success_probability=main_results.success_probability,
            risk_metrics=risk_metrics,
            performance_attribution=performance_attribution,
            scenario_results=scenario_results,
            sensitivity_results=sensitivity_results,
            distribution_fits=distribution_fits,
            tail_metrics=tail_metrics,
            vectorbt_metrics=getattr(main_results, 'vectorbt_metrics', None),
            execution_stats=execution_stats
        )

        return enhanced_results

    def _calculate_enhanced_risk_metrics(self, results: MCResults) -> Dict[str, float]:
        """Calculate enhanced risk metrics"""
        returns = results.equity_curves[:, 1:] / results.equity_curves[:, :-1] - 1
        final_values = results.final_values

        metrics = {}

        # Downside deviation
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        metrics['downside_deviation'] = np.std(downside_returns) * np.sqrt(252)

        # Upside deviation
        upside_returns = returns.copy()
        upside_returns[upside_returns < 0] = 0
        metrics['upside_deviation'] = np.std(upside_returns) * np.sqrt(252)

        # Gain/Loss ratio
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        metrics['gain_loss_ratio'] = np.mean(gains) / abs(np.mean(losses)) if len(losses) > 0 else np.inf

        # Omega ratio (threshold = 0)
        metrics['omega_ratio'] = np.sum(returns[returns > 0]) / abs(np.sum(returns[returns < 0])) if np.any(returns < 0) else np.inf

        # Tail ratio
        var_95 = np.percentile(final_values, 5)
        var_99 = np.percentile(final_values, 1)
        metrics['tail_ratio'] = var_99 / var_95 if var_95 != 0 else 0

        # Information ratio (using mean as benchmark)
        benchmark_return = np.mean(final_values)
        tracking_error = np.std(final_values - benchmark_return)
        metrics['information_ratio'] = (np.mean(final_values) - benchmark_return) / (tracking_error + 1e-8)

        return metrics

    def _calculate_performance_attribution(self, results: MCResults) -> Dict[str, float]:
        """Calculate performance attribution"""
        # This is a simplified attribution analysis
        equity_curves = results.equity_curves
        initial_capital = equity_curves[0, 0]

        attribution = {}

        # Volatility effect
        volatility = np.std(equity_curves[:, -1] / initial_capital - 1)
        attribution['volatility_effect'] = volatility * np.sqrt(self.config.time_horizon)

        # Skewness effect
        skewness = self._skewness(equity_curves[:, -1])
        attribution['skewness_effect'] = skewness

        # Kurtosis effect
        kurtosis = self._kurtosis(equity_curves[:, -1])
        attribution['kurtosis_effect'] = kurtosis

        # Trend effect (average drift)
        daily_returns = equity_curves[:, 1:] / equity_curves[:, :-1] - 1
        trend_effect = np.mean(daily_returns) * self.config.time_horizon
        attribution['trend_effect'] = trend_effect

        return attribution

    def _analyze_distributions(self, values: np.ndarray) -> Dict[str, Dict]:
        """Analyze and fit distributions to final values"""
        distributions = {}

        # Fit various distributions
        dist_names = ['norm', 'lognorm', 'gamma', 'beta', 't']

        for dist_name in dist_names:
            try:
                if dist_name == 'norm':
                    dist = stats.norm
                elif dist_name == 'lognorm':
                    dist = stats.lognorm
                elif dist_name == 'gamma':
                    dist = stats.gamma
                elif dist_name == 'beta':
                    dist = stats.beta
                elif dist_name == 't':
                    dist = stats.t

                # Fit distribution
                params = dist.fit(values)

                # Calculate goodness of fit
                ks_statistic, p_value = stats.kstest(values, lambda x: dist.cdf(x, *params))

                distributions[dist_name] = {
                    'params': params,
                    'ks_statistic': ks_statistic,
                    'p_value': p_value,
                    'aic': 2 * len(params) - 2 * np.sum(dist.logpdf(values, *params))
                }
            except Exception as e:
                logger.warning(f"Failed to fit {dist_name} distribution: {e}")

        # Find best fit (lowest AIC)
        if distributions:
            best_dist = min(distributions.keys(), key=lambda k: distributions[k]['aic'])
            for dist_name in distributions:
                distributions[dist_name]['is_best'] = (dist_name == best_dist)

        return distributions

    def _calculate_tail_metrics(self, values: np.ndarray) -> Dict[str, float]:
        """Calculate tail-specific risk metrics"""
        tail_metrics = {}

        # Tail risk at different percentiles
        tail_metrics['var_99'] = -np.percentile(values, 1)
        tail_metrics['var_99_9'] = -np.percentile(values, 0.1)

        # Expected shortfall (CVaR)
        var_99 = np.percentile(values, 1)
        tail_metrics['cvar_99'] = -np.mean(values[values <= var_99])

        var_99_9 = np.percentile(values, 0.1)
        tail_metrics['cvar_99_9'] = -np.mean(values[values <= var_99_9])

        # Tail ratio (99th to 95th percentile)
        var_95 = np.percentile(values, 5)
        tail_metrics['tail_ratio_99_95'] = var_99_9 / var_95 if var_95 != 0 else 0

        # Tail index (Hill estimator)
        sorted_values = np.sort(values)
        n = len(sorted_values)
        k = int(0.1 * n)  # Use top 10% for tail index

        if k > 0:
            tail_values = sorted_values[:k]
            tail_metrics['tail_index'] = 1 / (np.mean(np.log(tail_values / tail_values[-1])) + 1e-8)
        else:
            tail_metrics['tail_index'] = 0

        return tail_metrics

    async def _save_results(self, results: EnhancedMCResults):
        """Save simulation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monte_carlo_results_{self.simulation_id}_{timestamp}.json"
        filepath = Path(self.config.output_dir) / filename

        try:
            # Convert results to serializable format
            serializable_results = {
                'simulation_id': results.simulation_id,
                'statistics': results.statistics,
                'confidence_intervals': {
                    str(k): v for k, v in results.confidence_intervals.items()
                },
                'var': results.var,
                'cvar': results.cvar,
                'success_probability': results.success_probability,
                'risk_metrics': results.risk_metrics,
                'performance_attribution': results.performance_attribution,
                'tail_metrics': results.tail_metrics,
                'execution_stats': results.execution_stats,
                'vectorbt_metrics': results.vectorbt_metrics
            }

            # Add distribution fits (convert params to list)
            serializable_results['distribution_fits'] = {}
            for dist_name, fits in results.distribution_fits.items():
                serializable_results['distribution_fits'][dist_name] = {
                    'params': list(fits['params']) if hasattr(fits['params'], '__iter__') else fits['params'],
                    'ks_statistic': fits['ks_statistic'],
                    'p_value': fits['p_value'],
                    'aic': fits['aic'],
                    'is_best': fits['is_best']
                }

            # Save array statistics (not full arrays for size)
            serializable_results['final_values_summary'] = {
                'mean': np.mean(results.final_values),
                'std': np.std(results.final_values),
                'min': np.min(results.final_values),
                'max': np.max(results.final_values),
                'percentiles': {
                    'p1': np.percentile(results.final_values, 1),
                    'p5': np.percentile(results.final_values, 5),
                    'p25': np.percentile(results.final_values, 25),
                    'p50': np.percentile(results.final_values, 50),
                    'p75': np.percentile(results.final_values, 75),
                    'p95': np.percentile(results.final_values, 95),
                    'p99': np.percentile(results.final_values, 99)
                }
            }

            # Save to file
            with open(filepath, 'w') as f:
                json.dump(serializable_results, f, indent=2)

            logger.info(f"Results saved to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    # Helper methods (reused from base class)
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


# Convenience function for enhanced simulation
async def run_enhanced_monte_carlo(
    returns: pd.Series,
    method: Union[SimulationMethod, str] = SimulationMethod.BOOTSTRAP,
    n_simulations: int = 10000,
    time_horizon: int = 252,
    initial_capital: float = 100000,
    n_workers: Optional[int] = None,
    use_vectorbt: bool = True,
    **kwargs
) -> EnhancedMCResults:
    """
    Quick enhanced Monte Carlo simulation

    Args:
        returns: Historical returns
        method: Simulation method
        n_simulations: Number of simulations
        time_horizon: Simulation horizon in days
        initial_capital: Starting capital
        n_workers: Number of parallel workers
        use_vectorbt: Use VectorBT acceleration
        **kwargs: Additional parameters

    Returns:
        Enhanced simulation results
    """
    config = EnhancedMCConfig(
        n_simulations=n_simulations,
        time_horizon=time_horizon,
        n_workers=n_workers or min(32, mp.cpu_count()),
        use_vectorbt=use_vectorbt,
        **kwargs
    )

    simulator = EnhancedMonteCarloSimulator(config)
    return await simulator.simulate_parallel(
        returns=returns,
        method=method,
        initial_capital=initial_capital,
        **kwargs
    )


# Utility functions for report generation
def generate_monte_carlo_report(results: EnhancedMCResults) -> Dict[str, Any]:
    """
    Generate comprehensive Monte Carlo simulation report

    Args:
        results: Enhanced simulation results

    Returns:
        Report dictionary
    """
    report = {
        'executive_summary': {
            'simulation_id': results.simulation_id,
            'total_simulations': len(results.final_values),
            'time_horizon_days': len(results.equity_curves[0]) - 1,
            'mean_final_value': results.statistics['mean'],
            'median_final_value': results.statistics['median'],
            'volatility': results.statistics['std'],
            'success_probability': results.success_probability['positive_return']
        },
        'risk_analysis': {
            'var_metrics': results.var,
            'cvar_metrics': results.cvar,
            'max_drawdown': np.min(results.drawdowns),
            'avg_max_drawdown': np.mean(np.min(results.drawdowns, axis=1)),
            'downside_deviation': results.risk_metrics.get('downside_deviation'),
            'tail_ratio': results.risk_metrics.get('tail_ratio')
        },
        'performance_metrics': {
            'sharpe_ratio': results.risk_metrics.get('sharpe_ratio', results.statistics.get('sharpe', 0)),
            'sortino_ratio': results.risk_metrics.get('sortino_ratio', 0),
            'calmar_ratio': results.risk_metrics.get('calmar_ratio', 0),
            'gain_loss_ratio': results.risk_metrics.get('gain_loss_ratio'),
            'omega_ratio': results.risk_metrics.get('omega_ratio')
        },
        'distribution_analysis': {
            'best_fit_distribution': None,
            'fit_metrics': {}
        },
        'sensitivity_analysis': {},
        'scenario_analysis': {},
        'execution_stats': results.execution_stats
    }

    # Add best fit distribution
    for dist_name, fits in results.distribution_fits.items():
        if fits.get('is_best'):
            report['distribution_analysis']['best_fit_distribution'] = dist_name
        report['distribution_analysis']['fit_metrics'][dist_name] = {
            'aic': fits['aic'],
            'p_value': fits['p_value']
        }

    # Add sensitivity results if available
    if results.sensitivity_results:
        report['sensitivity_analysis'] = results.sensitivity_results.sensitivities

    # Add scenario summary
    for scenario_name, scenario_results in results.scenario_results.items():
        report['scenario_analysis'][scenario_name] = {
            'mean_value': scenario_results.statistics['mean'],
            'success_prob': scenario_results.success_probability['positive_return'],
            'var_95': scenario_results.var[0.95]
        }

    return report


__all__ = [
    'EnhancedMonteCarloSimulator',
    'EnhancedMCConfig',
    'EnhancedMCResults',
    'SimulationMethod',
    'SimulationScenario',
    'SensitivityResult',
    'VectorBTMonteCarlo',
    'run_enhanced_monte_carlo',
    'generate_monte_carlo_report'
]