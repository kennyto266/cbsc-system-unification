"""
Tests for Enhanced Monte Carlo Simulation System
==============================================

Test suite for the enhanced Monte Carlo simulation with VectorBT integration
and parallel processing capabilities.

Author: Claude Code Assistant
Date: 2025-01-19
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import tempfile
import shutil
from pathlib import Path

# Import the module to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_monte_carlo import (
    EnhancedMonteCarloSimulator,
    EnhancedMCConfig,
    EnhancedMCResults,
    SimulationMethod,
    SimulationScenario,
    VectorBTMonteCarlo,
    run_enhanced_monte_carlo,
    generate_monte_carlo_report
)

# Suppress warnings for cleaner test output
import warnings
warnings.filterwarnings('ignore')


class TestEnhancedMonteCarloSimulator(unittest.TestCase):
    """Test cases for EnhancedMonteCarloSimulator"""

    def setUp(self):
        """Set up test data"""
        # Generate sample return data
        np.random.seed(42)
        n_days = 252
        self.returns = pd.Series(
            np.random.normal(0.001, 0.02, n_days),
            index=pd.date_range(start='2023-01-01', periods=n_days, freq='D')
        )

        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    def test_config_initialization(self):
        """Test EnhancedMCConfig initialization"""
        config = EnhancedMCConfig()
        self.assertEqual(config.n_simulations, 10000)
        self.assertEqual(config.time_horizon, 252)
        self.assertTrue(config.use_vectorbt)
        self.assertTrue(config.enable_sensitivity_analysis)

        # Test custom config
        custom_config = EnhancedMCConfig(
            n_simulations=5000,
            time_horizon=126,
            n_workers=4,
            use_vectorbt=False
        )
        self.assertEqual(custom_config.n_simulations, 5000)
        self.assertEqual(custom_config.time_horizon, 126)
        self.assertEqual(custom_config.n_workers, 4)
        self.assertFalse(custom_config.use_vectorbt)

    def test_scenario_creation(self):
        """Test SimulationScenario creation"""
        scenario = SimulationScenario(
            name="test_scenario",
            params={"volatility_multiplier": 2.0},
            description="Test scenario with doubled volatility"
        )
        self.assertEqual(scenario.name, "test_scenario")
        self.assertEqual(scenario.params["volatility_multiplier"], 2.0)
        self.assertEqual(scenario.description, "Test scenario with doubled volatility")
        self.assertEqual(scenario.category, "custom")

    async def test_standard_simulation_bootstrap(self):
        """Test standard bootstrap simulation"""
        config = EnhancedMCConfig(
            n_simulations=100,  # Small number for testing
            time_horizon=30,    # Short horizon for testing
            n_workers=2,
            use_vectorbt=False  # Use standard method
        )

        simulator = EnhancedMonteCarloSimulator(config)

        results = await simulator.simulate_parallel(
            returns=self.returns,
            method=SimulationMethod.BOOTSTRAP,
            initial_capital=100000
        )

        # Verify results
        self.assertIsInstance(results, EnhancedMCResults)
        self.assertEqual(len(results.final_values), 100)
        self.assertEqual(results.equity_curves.shape[0], 100)
        self.assertEqual(results.equity_curves.shape[1], 31)  # 30 days + initial

        # Check that results contain expected keys
        self.assertIn('mean', results.statistics)
        self.assertIn('var', results)
        self.assertIn('cvar', results)
        self.assertIn('success_probability', results)

    async def test_standard_simulation_parametric(self):
        """Test standard parametric simulation"""
        config = EnhancedMCConfig(
            n_simulations=100,
            time_horizon=30,
            n_workers=2,
            use_vectorbt=False
        )

        simulator = EnhancedMonteCarloSimulator(config)

        results = await simulator.simulate_parallel(
            returns=self.returns,
            method=SimulationMethod.PARAMETRIC_NORMAL,
            initial_capital=100000
        )

        # Verify results structure
        self.assertIsInstance(results, EnhancedMCResults)
        self.assertGreater(results.statistics['mean'], 0)
        self.assertLess(results.var[0.95], 0)  # VaR should be negative

    async def test_sensitivity_analysis(self):
        """Test sensitivity analysis functionality"""
        config = EnhancedMCConfig(
            n_simulations=50,  # Small number for testing
            time_horizon=20,
            n_workers=2,
            use_vectorbt=False,
            enable_sensitivity_analysis=True,
            sensitivity_params=['volatility']  # Test only volatility
        )

        simulator = EnhancedMonteCarloSimulator(config)

        results = await simulator.simulate_parallel(
            returns=self.returns,
            method=SimulationMethod.BOOTSTRAP,
            initial_capital=100000
        )

        # Check that sensitivity results were generated
        self.assertIsNotNone(results.sensitivity_results)
        if results.sensitivity_results:
            self.assertIn('sensitivities', results.sensitivity_results.__dict__)
            self.assertIn('volatility', results.sensitivity_results.sensitivities)

    async def test_scenario_analysis(self):
        """Test scenario analysis functionality"""
        # Create test scenarios
        scenarios = [
            SimulationScenario(
                name="crash",
                params={"mean_adjustment": -0.01, "volatility_multiplier": 3.0},
                category="stress"
            ),
            SimulationScenario(
                name="bull_market",
                params={"mean_adjustment": 0.005},
                category="optimistic"
            )
        ]

        config = EnhancedMCConfig(
            n_simulations=50,
            time_horizon=20,
            n_workers=2,
            use_vectorbt=False
        )

        simulator = EnhancedMonteCarloSimulator(config)

        results = await simulator.simulate_parallel(
            returns=self.returns,
            method=SimulationMethod.BOOTSTRAP,
            initial_capital=100000,
            scenarios=scenarios
        )

        # Check that scenario results were generated
        self.assertIn('crash', results.scenario_results)
        self.assertIn('bull_market', results.scenario_results)

        # Crash scenario should have lower mean returns
        crash_mean = results.scenario_results['crash'].statistics['mean']
        bull_mean = results.scenario_results['bull_market'].statistics['mean']
        self.assertLess(crash_mean, bull_mean)

    def test_risk_metrics_calculation(self):
        """Test enhanced risk metrics calculation"""
        config = EnhancedMCConfig(
            n_simulations=100,
            time_horizon=30,
            n_workers=2,
            use_vectorbt=False
        )

        simulator = EnhancedMonteCarloSimulator(config)

        # Create a simple MCResults object for testing
        n_sim = 100
        n_days = 31
        equity_curves = np.ones((n_sim, n_days)) * 100000

        # Add some random variation
        for i in range(n_sim):
            daily_returns = np.random.normal(0.001, 0.02, n_days - 1)
            for j in range(1, n_days):
                equity_curves[i, j] = equity_curves[i, j-1] * (1 + daily_returns[j-1])

        # Create MCResults
        final_values = equity_curves[:, -1]
        drawdowns = simulator._calculate_drawdowns(equity_curves)

        from enhanced_monte_carlo import MCResults
        mc_results = MCResults(
            final_values=final_values,
            equity_curves=equity_curves,
            statistics=simulator._calculate_statistics(final_values),
            confidence_intervals=simulator._calculate_confidence_intervals(final_values),
            drawdowns=drawdowns,
            var=simulator._calculate_var(final_values),
            cvar=simulator._calculate_cvar(final_values),
            success_probability=simulator._calculate_success_probability(final_values)
        )

        # Test enhanced risk metrics
        risk_metrics = simulator._calculate_enhanced_risk_metrics(mc_results)

        # Check that expected metrics are present
        self.assertIn('downside_deviation', risk_metrics)
        self.assertIn('upside_deviation', risk_metrics)
        self.assertIn('gain_loss_ratio', risk_metrics)
        self.assertIn('omega_ratio', risk_metrics)
        self.assertIn('tail_ratio', risk_metrics)

        # Verify metric values make sense
        self.assertGreaterEqual(risk_metrics['downside_deviation'], 0)
        self.assertGreater(risk_metrics['gain_loss_ratio'], 0)

    def test_distribution_analysis(self):
        """Test distribution fitting and analysis"""
        config = EnhancedMCConfig()
        simulator = EnhancedMonteCarloSimulator(config)

        # Generate test data
        np.random.seed(42)
        test_values = np.random.lognormal(10, 0.5, 1000)

        # Analyze distributions
        distributions = simulator._analyze_distributions(test_values)

        # Check that distributions were fitted
        self.assertIn('norm', distributions)
        self.assertIn('lognorm', distributions)
        self.assertIn('gamma', distributions)

        # Each distribution should have required metrics
        for dist_name, fits in distributions.items():
            self.assertIn('params', fits)
            self.assertIn('ks_statistic', fits)
            self.assertIn('p_value', fits)
            self.assertIn('aic', fits)
            self.assertIn('is_best', fits)

        # Check that exactly one distribution is marked as best
        best_fits = [d for d in distributions.values() if d.get('is_best', False)]
        self.assertEqual(len(best_fits), 1)

    def test_tail_metrics_calculation(self):
        """Test tail risk metrics calculation"""
        config = EnhancedMCConfig()
        simulator = EnhancedMonteCarloSimulator(config)

        # Generate test data with fat tails
        np.random.seed(42)
        test_values = np.random.standard_t(3, 10000) * 0.02 + 0.001
        test_values = (1 + test_values).cumprod() * 100000

        # Calculate tail metrics
        tail_metrics = simulator._calculate_tail_metrics(test_values)

        # Check expected metrics
        self.assertIn('var_99', tail_metrics)
        self.assertIn('var_99_9', tail_metrics)
        self.assertIn('cvar_99', tail_metrics)
        self.assertIn('cvar_99_9', tail_metrics)
        self.assertIn('tail_ratio_99_95', tail_metrics)
        self.assertIn('tail_index', tail_metrics)

        # Verify metric relationships
        self.assertLessEqual(tail_metrics['var_99_9'], tail_metrics['var_99'])
        self.assertLessEqual(tail_metrics['cvar_99_9'], tail_metrics['cvar_99'])

    async def test_results_persistence(self):
        """Test saving and loading simulation results"""
        config = EnhancedMCConfig(
            n_simulations=50,
            time_horizon=20,
            n_workers=2,
            use_vectorbt=False,
            save_intermediate=True,
            output_dir=str(self.temp_path)
        )

        simulator = EnhancedMonteCarloSimulator(config)

        results = await simulator.simulate_parallel(
            returns=self.returns,
            method=SimulationMethod.BOOTSTRAP,
            initial_capital=100000
        )

        # Check that results file was created
        json_files = list(self.temp_path.glob("*.json"))
        self.assertGreater(len(json_files), 0)

        # Verify file contains expected data
        import json
        with open(json_files[0], 'r') as f:
            saved_data = json.load(f)

        self.assertIn('simulation_id', saved_data)
        self.assertIn('statistics', saved_data)
        self.assertIn('execution_stats', saved_data)


class TestVectorBTMonteCarlo(unittest.TestCase):
    """Test cases for VectorBTMonteCarlo class"""

    def setUp(self):
        """Set up test data"""
        # Generate sample price data
        np.random.seed(42)
        n_days = 252
        returns = np.random.normal(0.001, 0.02, n_days)
        prices = 100 * np.exp(np.cumsum(returns))

        self.price_data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000, 10000, n_days)
        }, index=pd.date_range(start='2023-01-01', periods=n_days, freq='D'))

    def test_gbm_paths_generation(self):
        """Test GBM path generation"""
        # Check if VectorBT is available
        try:
            import vectorbt as vbt
        except ImportError:
            self.skipTest("VectorBT not installed")

        vbt_mc = VectorBTMonteCarlo(self.price_data)

        # Generate paths
        n_paths = 100
        n_steps = 30
        paths = vbt_mc.generate_paths_vectorized(
            n_paths=n_paths,
            n_steps=n_steps,
            method='geometric_brownian'
        )

        # Verify shape
        self.assertEqual(paths.shape, (n_paths, n_steps))

        # Verify all paths start at 1
        np.testing.assert_array_equal(paths[:, 0], np.ones(n_paths))

        # Verify paths are generally positive
        self.assertTrue(np.all(paths > 0))

    def test_resample_paths_generation(self):
        """Test resample path generation"""
        # Check if VectorBT is available
        try:
            import vectorbt as vbt
        except ImportError:
            self.skipTest("VectorBT not installed")

        vbt_mc = VectorBTMonteCarlo(self.price_data)

        # Generate paths
        n_paths = 50
        n_steps = 30
        paths = vbt_mc.generate_paths_vectorized(
            n_paths=n_paths,
            n_steps=n_steps,
            method='resample',
            block_size=10
        )

        # Verify shape
        self.assertEqual(paths.shape, (n_paths, n_steps))

        # Verify all paths start at 1
        np.testing.assert_array_equal(paths[:, 0], np.ones(n_paths))

    def test_risk_metrics_vectorized(self):
        """Test vectorized risk metrics calculation"""
        # Check if VectorBT is available
        try:
            import vectorbt as vbt
        except ImportError:
            self.skipTest("VectorBT not installed")

        vbt_mc = VectorBTMonteCarlo(self.price_data)

        # Generate test equity curves
        n_paths = 100
        n_steps = 31
        equity_curves = np.ones((n_paths, n_steps)) * 100000

        for i in range(n_paths):
            daily_returns = np.random.normal(0.001, 0.02, n_steps - 1)
            for j in range(1, n_steps):
                equity_curves[i, j] = equity_curves[i, j-1] * (1 + daily_returns[j-1])

        # Calculate risk metrics
        metrics = vbt_mc.calculate_risk_metrics_vectorized(equity_curves)

        # Check expected metrics
        expected_metrics = [
            'var_90', 'var_95', 'var_99',
            'cvar_90', 'cvar_95', 'cvar_99',
            'max_drawdown', 'avg_drawdown',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio'
        ]

        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertEqual(len(metrics[metric]), n_paths)

        # Verify metric values make sense
        self.assertTrue(np.all(metrics['max_drawdown'] <= 0))  # Drawdowns should be <= 0


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""

    def setUp(self):
        """Set up test data"""
        np.random.seed(42)
        n_days = 100
        self.returns = pd.Series(
            np.random.normal(0.001, 0.02, n_days),
            index=pd.date_range(start='2023-01-01', periods=n_days, freq='D')
        )

    async def test_run_enhanced_monte_carlo_function(self):
        """Test the convenience function"""
        results = await run_enhanced_monte_carlo(
            returns=self.returns,
            method=SimulationMethod.BOOTSTRAP,
            n_simulations=50,  # Small for testing
            time_horizon=20,
            initial_capital=100000,
            n_workers=2,
            use_vectorbt=False
        )

        # Verify results
        self.assertIsInstance(results, EnhancedMCResults)
        self.assertEqual(len(results.final_values), 50)
        self.assertIn('execution_stats', results)

    def test_generate_monte_carlo_report(self):
        """Test report generation"""
        # Create a mock EnhancedMCResults object
        from enhanced_monte_carlo import MCResults, EnhancedMCResults

        n_sim = 100
        equity_curves = np.ones((n_sim, 31)) * 100000

        # Add variation
        for i in range(n_sim):
            daily_returns = np.random.normal(0.001, 0.02, 30)
            equity_curves[i, 1:] = equity_curves[i, :-1] * (1 + daily_returns)

        # Create enhanced results
        results = EnhancedMCResults(
            final_values=equity_curves[:, -1],
            equity_curves=equity_curves,
            statistics={'mean': 110000, 'median': 105000, 'std': 20000, 'skewness': 0.5, 'kurtosis': 3.0,
                       'min': 70000, 'max': 150000, 'percentile_5': 80000, 'percentile_95': 140000},
            confidence_intervals={0.95: (80000, 140000)},
            drawdowns=np.zeros((n_sim, 31)),
            var={0.95: -20000},
            cvar={0.95: -25000},
            success_probability={'positive_return': 0.7},
            simulation_id='test_123',
            risk_metrics={'downside_deviation': 0.15, 'upside_deviation': 0.18,
                         'gain_loss_ratio': 1.2, 'omega_ratio': 1.5, 'tail_ratio': 0.8},
            tail_metrics={'var_99': -30000, 'cvar_99': -35000, 'tail_index': 3.0},
            execution_stats={'execution_time': 10.5, 'simulations_per_second': 10.0}
        )

        # Generate report
        report = generate_monte_carlo_report(results)

        # Verify report structure
        self.assertIn('executive_summary', report)
        self.assertIn('risk_analysis', report)
        self.assertIn('performance_metrics', report)
        self.assertIn('distribution_analysis', report)
        self.assertIn('execution_stats', report)

        # Check executive summary
        exec_summary = report['executive_summary']
        self.assertEqual(exec_summary['simulation_id'], 'test_123')
        self.assertEqual(exec_summary['total_simulations'], 100)
        self.assertEqual(exec_summary['mean_final_value'], 110000)


def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.makeSuite(TestEnhancedMonteCarloSimulator))
    suite.addTest(unittest.makeSuite(TestVectorBTMonteCarlo))
    suite.addTest(unittest.makeSuite(TestUtilityFunctions))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    # Run tests when script is executed directly
    success = run_tests()
    sys.exit(0 if success else 1)