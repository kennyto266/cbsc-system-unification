"""
Advanced Monte Carlo Simulation with Multiple Scenarios
======================================================

Comprehensive Monte Carlo simulation engine with:
- Multiple simulation methods (bootstrap, parametric, GBM, regime-switching)
- Parallel execution support
- Advanced scenario analysis
- Stress testing integration
- Confidence interval calculations

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
from scipy import stats
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import base modules
try:
    from .monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults
    from .enhanced_backtest_engine import BacktestResult
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults
    from enhanced_backtest_engine import BacktestResult

logger = logging.getLogger(__name__)


class SimulationMethod(str, Enum):
    """Advanced simulation methods"""
    BOOTSTRAP = "bootstrap"
    PARAMETRIC_NORMAL = "parametric_normal"
    PARAMETRIC_T = "parametric_t"
    GEOMETRIC_BROWNIAN = "geometric_brownian"
    REGIME_SWITCHING = "regime_switching"
    COPULA = "copula"
    BOOTSTRAP_BLOCK = "bootstrap_block"
    SVD_RESAMPLING = "svd_resampling"


class ScenarioType(str, Enum):
    """Scenario analysis types"""
    BASE_CASE = "base_case"
    STRESS_TEST = "stress_test"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    INTEREST_RATE_SHOCK = "interest_rate_shock"


@dataclass
class AdvancedMCConfig:
    """Advanced Monte Carlo configuration"""
    # Base configuration
    base_config: MCSimulationConfig = field(default_factory=MCSimulationConfig)

    # Advanced settings
    simulation_method: SimulationMethod = SimulationMethod.BOOTSTRAP
    n_simulations: int = 10000
    time_horizon: int = 252  # trading days
    n_processes: int = -1  # -1 for all CPUs

    # Regime switching parameters
    n_regimes: int = 2
    regime_persistence: float = 0.95

    # Block bootstrap parameters
    block_size: int = 20  # days
    overlapping_blocks: bool = False

    # Correlation modeling
    use_dynamic_correlation: bool = True
    correlation_window: int = 60  # days

    # Extreme events
    include_extreme_events: bool = True
    extreme_event_probability: float = 0.01
    extreme_event_magnitude: float = -0.20  # -20%

    # Scenario analysis
    scenario_weights: Dict[str, float] = field(default_factory=lambda: {
        ScenarioType.BASE_CASE: 0.7,
        ScenarioType.STRESS_TEST: 0.15,
        ScenarioType.VOLATILITY_SPIKE: 0.1,
        ScenarioType.CORRELATION_BREAKDOWN: 0.05
    })

    # Output settings
    save_paths: bool = False
    generate_reports: bool = True
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95, 0.99])


@dataclass
class ScenarioConfig:
    """Scenario configuration"""
    name: str
    type: ScenarioType
    parameters: Dict[str, Any]
    weight: float
    description: str = ""


class AdvancedMonteCarlo:
    """Advanced Monte Carlo simulation engine"""

    def __init__(self, config: AdvancedMCConfig):
        """
        Initialize advanced Monte Carlo engine

        Args:
            config: Advanced Monte Carlo configuration
        """
        self.config = config
        self.base_simulator = MonteCarloSimulator(config.base_config)

        # Results storage
        self.simulation_results: Dict[str, MCResults] = {}
        self.scenario_results: Dict[str, MCResults] = {}
        self.combined_results: Optional[MCResults] = None

        logger.info(f"Advanced Monte Carlo engine initialized with {config.simulation_method} method")

    def run_simulation(
        self,
        returns: pd.DataFrame,
        portfolio_weights: Optional[pd.Series] = None,
        scenarios: Optional[List[ScenarioConfig]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive Monte Carlo simulation

        Args:
            returns: Historical returns DataFrame
            portfolio_weights: Portfolio weights for multi-asset simulation
            scenarios: Custom scenarios to run

        Returns:
            Dictionary with all simulation results
        """
        try:
            logger.info("Starting advanced Monte Carlo simulation")

            # Prepare data
            portfolio_returns = self._prepare_portfolio_returns(returns, portfolio_weights)

            # Run base simulation
            base_results = self._run_base_simulation(portfolio_returns)
            self.simulation_results['base'] = base_results

            # Run scenario analysis
            if scenarios:
                scenario_results = self._run_scenario_analysis(portfolio_returns, scenarios)
                self.scenario_results.update(scenario_results)

            # Combine results
            if self.scenario_results:
                self.combined_results = self._combine_scenario_results()
            else:
                self.combined_results = base_results

            # Generate reports
            if self.config.generate_reports:
                reports = self._generate_comprehensive_reports()
            else:
                reports = {}

            logger.info("Advanced Monte Carlo simulation completed")

            return {
                'base_results': base_results,
                'scenario_results': self.scenario_results,
                'combined_results': self.combined_results,
                'reports': reports
            }

        except Exception as e:
            logger.error(f"Monte Carlo simulation failed: {e}")
            raise

    def _prepare_portfolio_returns(
        self,
        returns: pd.DataFrame,
        weights: Optional[pd.Series] = None
    ) -> pd.Series:
        """Prepare portfolio returns from individual asset returns"""

        if weights is not None:
            # Calculate weighted portfolio returns
            portfolio_returns = (returns * weights).sum(axis=1)
        elif len(returns.columns) == 1:
            # Single asset
            portfolio_returns = returns.iloc[:, 0]
        else:
            # Equal weighted portfolio
            portfolio_returns = returns.mean(axis=1)

        return portfolio_returns.dropna()

    def _run_base_simulation(self, returns: pd.Series) -> MCResults:
        """Run base Monte Carlo simulation with specified method"""

        if self.config.simulation_method == SimulationMethod.BOOTSTRAP:
            return self._run_bootstrap_simulation(returns)
        elif self.config.simulation_method == SimulationMethod.PARAMETRIC_NORMAL:
            return self._run_parametric_normal_simulation(returns)
        elif self.config.simulation_method == SimulationMethod.PARAMETRIC_T:
            return self._run_parametric_t_simulation(returns)
        elif self.config.simulation_method == SimulationMethod.GEOMETRIC_BROWNIAN:
            return self._run_gbm_simulation(returns)
        elif self.config.simulation_method == SimulationMethod.REGIME_SWITCHING:
            return self._run_regime_switching_simulation(returns)
        elif self.config.simulation_method == SimulationMethod.BOOTSTRAP_BLOCK:
            return self._run_block_bootstrap_simulation(returns)
        else:
            raise ValueError(f"Unknown simulation method: {self.config.simulation_method}")

    def _run_bootstrap_simulation(self, returns: pd.Series) -> MCResults:
        """Bootstrap simulation with parallel execution"""

        if self.config.n_processes == 1:
            return self.base_simulator.simulate_bootstrap(
                returns,
                initial_capital=self.config.base_config.time_horizon
            )
        else:
            return self._run_parallel_bootstrap(returns)

    def _run_parallel_bootstrap(self, returns: pd.Series) -> MCResults:
        """Run bootstrap simulation in parallel"""

        n_workers = mp.cpu_count() if self.config.n_processes == -1 else self.config.n_processes
        sims_per_worker = self.config.n_simulations // n_workers

        results = []

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = []

            for i in range(n_workers):
                start_sim = i * sims_per_worker
                end_sim = (i + 1) * sims_per_worker if i < n_workers - 1 else self.config.n_simulations

                future = executor.submit(
                    self._worker_bootstrap,
                    returns,
                    start_sim,
                    end_sim,
                    i
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel bootstrap worker failed: {e}")
                    continue

        # Combine results
        return self._combine_simulation_results(results)

    def _worker_bootstrap(
        self,
        returns: pd.Series,
        start_sim: int,
        end_sim: int,
        worker_id: int
    ) -> MCResults:
        """Worker function for parallel bootstrap"""

        # Create worker-specific simulator
        worker_config = MCSimulationConfig(
            n_simulations=end_sim - start_sim,
            time_horizon=self.config.time_horizon,
            confidence_levels=self.config.confidence_levels
        )

        worker_simulator = MonteCarloSimulator(worker_config)
        return worker_simulator.simulate_bootstrap(returns)

    def _run_parametric_normal_simulation(self, returns: pd.Series) -> MCResults:
        """Parametric simulation with normal distribution"""

        return self.base_simulator.simulate_parametric(
            returns,
            distribution='normal',
            initial_capital=self.config.base_config.time_horizon
        )

    def _run_parametric_t_simulation(self, returns: pd.Series) -> MCResults:
        """Parametric simulation with t-distribution"""

        # Fit t-distribution
        params = stats.t.fit(returns)
        df, loc, scale = params

        return self.base_simulator.simulate_parametric(
            returns,
            distribution='t',
            df=df,
            initial_capital=self.config.base_config.time_horizon
        )

    def _run_gbm_simulation(self, returns: pd.Series) -> MCResults:
        """Geometric Brownian Motion simulation"""

        return self.base_simulator.simulate_geometric_brownian(
            returns,
            initial_capital=self.config.base_config.time_horizon
        )

    def _run_regime_switching_simulation(self, returns: pd.Series) -> MCResults:
        """Regime-switching simulation"""

        # Fit regime-switching model
        regimes = self._fit_regime_model(returns)

        # Simulate with regime switching
        n_sim = self.config.n_simulations
        n_days = self.config.time_horizon

        equity_curves = np.zeros((n_sim, n_days))
        equity_curves[:, 0] = self.config.base_config.time_horizon

        for i in range(n_sim):
            regime_path = self._simulate_regime_path(n_days)
            returns_path = self._simulate_returns_with_regimes(regime_path, regimes)
            equity_curves[i, 1:] = self.config.base_config.time_horizon * np.cumprod(1 + returns_path)

        return self._analyze_results(equity_curves, self.config.base_config.time_horizon)

    def _fit_regime_model(self, returns: pd.Series) -> Dict[int, Dict[str, float]]:
        """Fit regime-switching model to returns"""

        # Use Gaussian Mixture Model
        n_regimes = self.config.n_regimes

        # Reshape returns for GMM
        returns_array = returns.values.reshape(-1, 1)

        # Fit GMM
        gmm = GaussianMixture(n_components=n_regimes, random_state=42)
        gmm.fit(returns_array)

        regimes = {}
        for i in range(n_regimes):
            regimes[i] = {
                'mean': gmm.means_[i][0],
                'std': np.sqrt(gmm.covariances_[i][0][0]),
                'weight': gmm.weights_[i]
            }

        return regimes

    def _simulate_regime_path(self, n_days: int) -> np.ndarray:
        """Simulate regime path with persistence"""

        regimes = np.arange(self.config.n_regimes)
        path = np.zeros(n_days, dtype=int)

        # Initial regime (random)
        path[0] = np.random.choice(regimes)

        # Simulate with persistence
        persistence = self.config.regime_persistence

        for i in range(1, n_days):
            if np.random.random() < persistence:
                path[i] = path[i-1]  # Stay in same regime
            else:
                # Switch regime
                other_regimes = regimes[regimes != path[i-1]]
                path[i] = np.random.choice(other_regimes)

        return path

    def _simulate_returns_with_regimes(
        self,
        regime_path: np.ndarray,
        regimes: Dict[int, Dict[str, float]]
    ) -> np.ndarray:
        """Simulate returns given regime path"""

        returns_path = np.zeros(len(regime_path))

        for i, regime in enumerate(regime_path):
            mean = regimes[regime]['mean']
            std = regimes[regime]['std']
            returns_path[i] = np.random.normal(mean, std)

        return returns_path

    def _run_block_bootstrap_simulation(self, returns: pd.Series) -> MCResults:
        """Block bootstrap simulation"""

        n_sim = self.config.n_simulations
        n_days = self.config.time_horizon
        block_size = self.config.block_size
        initial_capital = self.config.base_config.time_horizon

        equity_curves = np.zeros((n_sim, n_days))
        equity_curves[:, 0] = initial_capital

        for i in range(n_sim):
            # Block bootstrap
            sampled_returns = self._block_bootstrap(returns, n_days, block_size)
            equity_curves[i, 1:] = initial_capital * np.cumprod(1 + sampled_returns)

        return self._analyze_results(equity_curves, initial_capital)

    def _block_bootstrap(
        self,
        returns: pd.Series,
        n_samples: int,
        block_size: int
    ) -> np.ndarray:
        """Block bootstrap sampling"""

        n_blocks = int(np.ceil(n_samples / block_size))
        sampled_returns = []

        for _ in range(n_blocks):
            # Random starting point
            max_start = len(returns) - block_size
            start_idx = np.random.randint(0, max_start)

            # Sample block
            block = returns.iloc[start_idx:start_idx + block_size].values
            sampled_returns.extend(block)

        return np.array(sampled_returns[:n_samples])

    def _run_scenario_analysis(
        self,
        returns: pd.Series,
        scenarios: List[ScenarioConfig]
    ) -> Dict[str, MCResults]:
        """Run scenario analysis"""

        results = {}

        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario.name}")

            # Modify returns based on scenario
            scenario_returns = self._apply_scenario(returns, scenario)

            # Run simulation on scenario returns
            scenario_result = self._run_base_simulation(scenario_returns)
            results[scenario.name] = scenario_result

        return results

    def _apply_scenario(self, returns: pd.Series, scenario: ScenarioConfig) -> pd.Series:
        """Apply scenario modifications to returns"""

        modified_returns = returns.copy()

        if scenario.type == ScenarioType.STRESS_TEST:
            # Apply stress shock
            shock = scenario.parameters.get('shock', -0.30)
            duration = scenario.parameters.get('duration', 21)
            start_date = scenario.parameters.get('start_date', returns.index[-duration])

            modified_returns.loc[start_date:] += shock

        elif scenario.type == ScenarioType.VOLATILITY_SPIKE:
            # Increase volatility
            vol_multiplier = scenario.parameters.get('vol_multiplier', 3.0)
            modified_returns *= vol_multiplier

        elif scenario.type == ScenarioType.CORRELATION_BREAKDOWN:
            # Add correlation shock (simplified)
            correlation_shock = scenario.parameters.get('correlation_shock', 0.5)
            modified_returns += correlation_shock * np.random.randn(len(modified_returns))

        elif scenario.type == ScenarioType.LIQUIDITY_CRISIS:
            # Add liquidity shock
            liquidity_shock = scenario.parameters.get('liquidity_shock', -0.10)
            modified_returns += liquidity_shock

        return modified_returns

    def _combine_scenario_results(self) -> MCResults:
        """Combine scenario results with weights"""

        # Get all equity curves
        all_equity_curves = []
        all_weights = []

        # Add base results
        base_weight = self.config.scenario_weights.get(ScenarioType.BASE_CASE, 0.7)
        if 'base' in self.simulation_results:
            all_equity_curves.append(self.simulation_results['base'].equity_curves)
            all_weights.extend([base_weight] * len(self.simulation_results['base'].equity_curves))

        # Add scenario results
        for scenario_name, result in self.scenario_results.items():
            # Find scenario weight
            weight = 0.1  # Default weight
            for scenario_type, scenario_weight in self.config.scenario_weights.items():
                if scenario_type in scenario_name.lower():
                    weight = scenario_weight
                    break

            all_equity_curves.append(result.equity_curves)
            all_weights.extend([weight] * len(result.equity_curves))

        # Combine equity curves
        combined_equity = np.vstack(all_equity_curves)
        combined_weights = np.array(all_weights)

        # Weighted statistics
        final_values = combined_equity[:, -1]

        # Calculate weighted statistics
        weighted_mean = np.average(final_values, weights=combined_weights)
        weighted_std = np.sqrt(np.average((final_values - weighted_mean)**2, weights=combined_weights))

        # Create combined results
        combined_results = MCResults(
            final_values=final_values,
            equity_curves=combined_equity,
            statistics={
                'mean': weighted_mean,
                'std': weighted_std,
                'min': np.min(final_values),
                'max': np.max(final_values)
            },
            confidence_intervals={},
            drawdowns=np.zeros_like(combined_equity),
            var={},
            cvar={},
            success_probability={}
        )

        return combined_results

    def _combine_simulation_results(self, results: List[MCResults]) -> MCResults:
        """Combine simulation results from multiple workers"""

        # Combine all equity curves
        all_equity_curves = []
        for result in results:
            all_equity_curves.append(result.equity_curves)

        combined_equity = np.vstack(all_equity_curves)
        final_values = combined_equity[:, -1]

        # Recalculate statistics
        statistics = {
            'mean': np.mean(final_values),
            'median': np.median(final_values),
            'std': np.std(final_values),
            'min': np.min(final_values),
            'max': np.max(final_values)
        }

        return MCResults(
            final_values=final_values,
            equity_curves=combined_equity,
            statistics=statistics,
            confidence_intervals={},
            drawdowns=np.zeros_like(combined_equity),
            var={},
            cvar={},
            success_probability={}
        )

    def _analyze_results(
        self,
        equity_curves: np.ndarray,
        initial_capital: float
    ) -> MCResults:
        """Analyze simulation results"""

        final_values = equity_curves[:, -1]

        # Calculate basic statistics
        statistics = {
            'mean': np.mean(final_values),
            'median': np.median(final_values),
            'std': np.std(final_values),
            'min': np.min(final_values),
            'max': np.max(final_values)
        }

        # Calculate drawdowns
        drawdowns = np.zeros_like(equity_curves)
        for i, curve in enumerate(equity_curves):
            peak = np.maximum.accumulate(curve)
            drawdowns[i] = (curve - peak) / peak

        return MCResults(
            final_values=final_values,
            equity_curves=equity_curves,
            statistics=statistics,
            confidence_intervals={},
            drawdowns=drawdowns,
            var={},
            cvar={},
            success_probability={}
        )

    def _generate_comprehensive_reports(self) -> Dict[str, Any]:
        """Generate comprehensive analysis reports"""

        reports = {
            'summary': self._generate_summary_report(),
            'risk_analysis': self._generate_risk_analysis(),
            'scenario_comparison': self._generate_scenario_comparison()
        }

        # Add visualizations
        if self.config.save_paths:
            reports['visualizations'] = self._generate_visualizations()

        return reports

    def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report"""

        if not self.combined_results:
            return {}

        final_values = self.combined_results.final_values

        return {
            'n_simulations': len(final_values),
            'time_horizon_days': self.config.time_horizon,
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values),
            'volatility': np.std(final_values),
            'percentiles': {
                f'p{p}': np.percentile(final_values, p)
                for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]
            }
        }

    def _generate_risk_analysis(self) -> Dict[str, Any]:
        """Generate risk analysis report"""

        if not self.combined_results:
            return {}

        final_values = self.combined_results.final_values
        initial_capital = self.config.base_config.time_horizon

        # Calculate risk metrics
        returns = final_values / initial_capital - 1

        return {
            'var_95': -np.percentile(returns, 5),
            'var_99': -np.percentile(returns, 1),
            'cvar_95': -np.mean(returns[returns <= np.percentile(returns, 5)]),
            'cvar_99': -np.mean(returns[returns <= np.percentile(returns, 1)]),
            'max_drawdown': np.min(self.combined_results.drawdowns),
            'probability_of_loss': np.mean(returns < 0),
            'probability_of_20pct_loss': np.mean(returns < -0.2)
        }

    def _generate_scenario_comparison(self) -> Dict[str, Any]:
        """Generate scenario comparison report"""

        comparison = {}

        for scenario_name, result in self.scenario_results.items():
            final_values = result.final_values
            comparison[scenario_name] = {
                'mean': np.mean(final_values),
                'std': np.std(final_values),
                'var_95': -np.percentile(final_values, 5),
                'max_drawdown': np.min(result.drawdowns).min()
            }

        return comparison

    def _generate_visualizations(self) -> Dict[str, str]:
        """Generate visualization plots"""

        plots = {}

        if self.combined_results:
            # 1. Equity curves distribution
            fig = go.Figure()

            # Sample paths
            n_sample = min(100, len(self.combined_results.equity_curves))
            sample_indices = np.random.choice(len(self.combined_results.equity_curves), n_sample, replace=False)

            for idx in sample_indices:
                fig.add_trace(go.Scatter(
                    y=self.combined_results.equity_curves[idx],
                    mode='lines',
                    line=dict(width=0.5),
                    opacity=0.3,
                    showlegend=False
                ))

            fig.update_layout(
                title='Monte Carlo Simulation Paths',
                xaxis_title='Days',
                yaxis_title='Portfolio Value'
            )

            plots['equity_curves'] = fig.to_html(include_plotlyjs='cdn')

            # 2. Final value distribution
            fig = go.Figure()

            fig.add_trace(go.Histogram(
                x=self.combined_results.final_values,
                nbinsx=50,
                name='Final Values'
            ))

            fig.add_vline(
                x=np.mean(self.combined_results.final_values),
                line_dash="dash",
                line_color="red",
                annotation_text="Mean"
            )

            fig.update_layout(
                title='Final Value Distribution',
                xaxis_title='Final Portfolio Value',
                yaxis_title='Frequency'
            )

            plots['final_distribution'] = fig.to_html(include_plotlyjs='cdn')

            # 3. Scenario comparison
            if len(self.scenario_results) > 0:
                fig = go.Figure()

                scenarios = list(self.scenario_results.keys())
                means = [np.mean(self.scenario_results[s].final_values) for s in scenarios]
                stds = [np.std(self.scenario_results[s].final_values) for s in scenarios]

                fig.add_trace(go.Bar(
                    name='Mean',
                    x=scenarios,
                    y=means,
                    error_y=dict(type='data', array=stds)
                ))

                fig.update_layout(
                    title='Scenario Comparison',
                    xaxis_title='Scenario',
                    yaxis_title='Mean Final Value'
                )

                plots['scenario_comparison'] = fig.to_html(include_plotlyjs='cdn')

        return plots


# Utility functions
def create_advanced_mc_config(**kwargs) -> AdvancedMCConfig:
    """Create advanced Monte Carlo configuration with defaults"""

    config = {
        'simulation_method': SimulationMethod.BOOTSTRAP,
        'n_simulations': 10000,
        'time_horizon': 252,
        'n_processes': -1,
        'generate_reports': True,
        'confidence_levels': [0.90, 0.95, 0.99]
    }

    config.update(kwargs)
    return AdvancedMCConfig(**config)


def create_stress_scenarios() -> List[ScenarioConfig]:
    """Create standard stress test scenarios"""

    return [
        ScenarioConfig(
            name="market_crash",
            type=ScenarioType.STRESS_TEST,
            parameters={
                'shock': -0.30,
                'duration': 21,
                'start_date': None  # Use last 21 days
            },
            weight=0.3,
            description="30% market crash over 21 days"
        ),
        ScenarioConfig(
            name="volatility_spike",
            type=ScenarioType.VOLATILITY_SPIKE,
            parameters={
                'vol_multiplier': 3.0,
                'duration': 10
            },
            weight=0.2,
            description="3x volatility increase for 10 days"
        ),
        ScenarioConfig(
            name="liquidity_crisis",
            type=ScenarioType.LIQUIDITY_CRISIS,
            parameters={
                'liquidity_shock': -0.15,
                'correlation_increase': 0.3
            },
            weight=0.2,
            description="15% liquidity shock with correlation breakdown"
        ),
        ScenarioConfig(
            name="correlation_breakdown",
            type=ScenarioType.CORRELATION_BREAKDOWN,
            parameters={
                'correlation_shock': 0.5,
                'duration': 15
            },
            weight=0.15,
            description="Sudden increase in asset correlations"
        )
    ]


__all__ = [
    'AdvancedMonteCarlo',
    'AdvancedMCConfig',
    'ScenarioConfig',
    'SimulationMethod',
    'ScenarioType',
    'create_advanced_mc_config',
    'create_stress_scenarios'
]