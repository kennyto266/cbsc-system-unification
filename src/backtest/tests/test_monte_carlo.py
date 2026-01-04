"""
Tests for Monte Carlo simulation module
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, Mock

from ..monte_carlo import (
    MonteCarloSimulator,
    MCSimulationConfig,
    MCResults,
    run_monte_carlo
)


class TestMCSimulationConfig:
    """Test cases for MC simulation configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = MCSimulationConfig()

        assert config.n_simulations == 10000
        assert config.time_horizon == 252
        assert config.confidence_levels == [0.90, 0.95, 0.99]
        assert config.return_method == 'bootstrap'
        assert config.volatility_window == 60
        assert config.random_seed is None

    def test_custom_config(self):
        """Test custom configuration"""
        config = MCSimulationConfig(
            n_simulations=5000,
            time_horizon=100,
            confidence_levels=[0.95],
            return_method='parametric',
            random_seed=42
        )

        assert config.n_simulations == 5000
        assert config.time_horizon == 100
        assert config.confidence_levels == [0.95]
        assert config.return_method == 'parametric'
        assert config.random_seed == 42

    def test_random_seed(self):
        """Test random seed setting"""
        config1 = MCSimulationConfig(random_seed=42)
        config2 = MCSimulationConfig(random_seed=42)

        # Both should generate the same random numbers
        assert config1.random_seed == config2.random_seed


class TestMonteCarloSimulator:
    """Test cases for Monte Carlo Simulator"""

    @pytest.fixture
    def sample_returns(self):
        """Create sample return data"""
        np.random.seed(42)
        returns = pd.Series(
            np.random.normal(0.001, 0.02, 252),
            index=pd.date_range('2023-01-01', periods=252)
        )
        return returns

    @pytest.fixture
    def simulator(self):
        """Create simulator instance with smaller sample size for testing"""
        config = MCSimulationConfig(
            n_simulations=100,  # Smaller for faster tests
            time_horizon=60,
            confidence_levels=[0.95],
            random_seed=42
        )
        return MonteCarloSimulator(config)

    def test_initialization(self):
        """Test simulator initialization"""
        config = MCSimulationConfig()
        simulator = MonteCarloSimulator(config)

        assert simulator.config == config
        assert simulator.risk_calculator is not None

    def test_bootstrap_simulation(self, simulator, sample_returns):
        """Test bootstrap simulation"""
        results = simulator.simulate_bootstrap(sample_returns, initial_capital=100000)

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 100
        assert results.equity_curves.shape == (100, 60)
        assert np.all(results.equity_curves[:, 0] == 100000)

        # Check that results are reasonable
        assert results.statistics['mean'] > 0
        assert results.statistics['std'] > 0
        assert len(results.confidence_intervals) == 1
        assert 0.95 in results.confidence_intervals

    def test_parametric_simulation(self, simulator, sample_returns):
        """Test parametric simulation"""
        results = simulator.simulate_parametric(
            sample_returns,
            initial_capital=100000,
            distribution='normal'
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 100
        assert results.equity_curves.shape == (100, 60)

    def test_gbm_simulation(self, simulator, sample_returns):
        """Test Geometric Brownian Motion simulation"""
        results = simulator.simulate_geometric_brownian(
            sample_returns,
            initial_capital=100000
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 100
        assert results.equity_curves.shape == (100, 60)

        # GBM should always produce positive values
        assert np.all(results.equity_curves > 0)

    def test_invalid_distribution(self, simulator, sample_returns):
        """Test invalid distribution parameter"""
        with pytest.raises(ValueError, match="Unsupported distribution"):
            simulator.simulate_parametric(
                sample_returns,
                initial_capital=100000,
                distribution='invalid'
            )

    def test_t_distribution(self, simulator, sample_returns):
        """Test Student's t distribution"""
        results = simulator.simulate_parametric(
            sample_returns,
            initial_capital=100000,
            distribution='t',
            df=5
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 100

    def test_statistics_calculation(self, simulator, sample_returns):
        """Test statistics calculation"""
        results = simulator.simulate_bootstrap(sample_returns)

        stats = results.statistics

        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'skewness' in stats
        assert 'kurtosis' in stats
        assert 'percentile_5' in stats
        assert 'percentile_95' in stats

        # Check basic properties
        assert stats['min'] <= stats['median'] <= stats['max']
        assert stats['std'] >= 0

    def test_confidence_intervals(self, simulator, sample_returns):
        """Test confidence interval calculation"""
        results = simulator.simulate_bootstrap(sample_returns)

        ci_95 = results.confidence_intervals[0.95]
        assert len(ci_95) == 2
        assert ci_95[0] < ci_95[1]

        # Verify confidence level
        lower_count = np.sum(results.final_values < ci_95[0])
        upper_count = np.sum(results.final_values > ci_95[1])
        total_outside = lower_count + upper_count

        # Approximately 5% should be outside 95% CI
        assert abs(total_outside / len(results.final_values) - 0.05) < 0.02

    def test_drawdown_calculation(self, simulator, sample_returns):
        """Test drawdown calculation"""
        results = simulator.simulate_bootstrap(sample_returns)

        assert results.drawdowns.shape == (100, 60)

        # Drawdowns should be negative or zero
        assert np.all(results.drawdowns <= 0)

        # Each simulation should have at least one zero drawdown (start)
        for dd in results.drawdowns:
            assert np.any(dd == 0)

    def test_var_calculation(self, simulator, sample_returns):
        """Test Value at Risk calculation"""
        results = simulator.simulate_bootstrap(sample_returns)

        assert 0.95 in results.var
        assert results.var[0.95] > 0

        # Verify VaR calculation manually
        manual_var_95 = -np.percentile(results.final_values, 5)
        assert abs(results.var[0.95] - manual_var_95) < 1e-10

    def test_cvar_calculation(self, simulator, sample_returns):
        """Test Conditional Value at Risk calculation"""
        results = simulator.simulate_bootstrap(sample_returns)

        assert 0.95 in results.cvar
        assert results.cvar[0.95] > 0

        # CVaR should be greater than VaR (more conservative)
        assert results.cvar[0.95] >= results.var[0.95]

    def test_success_probability(self, simulator, sample_returns):
        """Test success probability calculation"""
        initial_capital = 100000
        results = simulator.simulate_bootstrap(sample_returns, initial_capital)

        success_probs = results.success_probability

        assert 'positive_return' in success_probs
        assert 'beating_10pct' in success_probs
        assert 'beating_20pct' in success_probs
        assert 'doubling' in success_probs
        assert 'halving' in success_probs

        # Probabilities should be between 0 and 1
        for prob in success_probs.values():
            assert 0 <= prob <= 1

        # More stringent targets should have lower probabilities
        assert success_probs['doubling'] <= success_probs['beating_50pct']
        assert success_probs['beating_50pct'] <= success_probs['beating_20pct']
        assert success_probs['beating_20pct'] <= success_probs['beating_10pct']

    @patch('multiprocessing.cpu_count')
    def test_parallel_simulation(self, mock_cpu_count, simulator, sample_returns):
        """Test parallel simulation"""
        mock_cpu_count.return_value = 4

        # Use smaller number of simulations for parallel test
        config = MCSimulationConfig(
            n_simulations=40,
            time_horizon=30,
            random_seed=42
        )
        parallel_simulator = MonteCarloSimulator(config)

        results = parallel_simulator.simulate_parallel(
            'bootstrap',
            sample_returns,
            initial_capital=100000,
            n_workers=2
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 40
        assert results.equity_curves.shape == (40, 30)

    def test_generate_report(self, simulator, sample_returns):
        """Test report generation"""
        results = simulator.simulate_bootstrap(sample_returns)
        report = simulator.generate_report(results)

        assert 'summary' in report
        assert 'risk_metrics' in report
        assert 'confidence_intervals' in report
        assert 'target_probabilities' in report
        assert 'distribution_stats' in report

        # Check summary
        summary = report['summary']
        assert summary['total_simulations'] == 100
        assert summary['time_horizon_days'] == 60
        assert 'mean_final_value' in summary
        assert 'success_probability' in summary

        # Check risk metrics
        risk_metrics = report['risk_metrics']
        assert 'var_95' in risk_metrics
        assert 'cvar_95' in risk_metrics
        assert 'max_drawdown' in risk_metrics

    @patch('matplotlib.pyplot.show')
    def test_plot_results(self, mock_show, simulator, sample_returns):
        """Test results plotting"""
        results = simulator.simulate_bootstrap(sample_returns)

        # Should not raise any errors
        simulator.plot_results(results, n_paths_to_plot=10)

        # Check that show was called
        mock_show.assert_called_once()


class TestRunMonteCarlo:
    """Test cases for the convenience function"""

    @pytest.fixture
    def sample_returns(self):
        """Create sample return data"""
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.02, 100))

    def test_run_bootstrap(self, sample_returns):
        """Test running bootstrap simulation"""
        results = run_monte_carlo(
            sample_returns,
            method='bootstrap',
            n_simulations=50,
            time_horizon=30
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 50
        assert results.equity_curves.shape == (50, 30)

    def test_run_parametric(self, sample_returns):
        """Test running parametric simulation"""
        results = run_monte_carlo(
            sample_returns,
            method='parametric',
            n_simulations=50,
            time_horizon=30
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 50

    def test_run_gbm(self, sample_returns):
        """Test running GBM simulation"""
        results = run_monte_carlo(
            sample_returns,
            method='gbm',
            n_simulations=50,
            time_horizon=30
        )

        assert isinstance(results, MCResults)
        assert len(results.final_values) == 50

    def test_run_parallel(self, sample_returns):
        """Test running parallel simulation"""
        with patch('multiprocessing.cpu_count', return_value=4):
            results = run_monte_carlo(
                sample_returns,
                method='bootstrap',
                n_simulations=40,
                time_horizon=30,
                parallel=True
            )

            assert isinstance(results, MCResults)
            assert len(results.final_values) == 40

    def test_invalid_method(self, sample_returns):
        """Test invalid simulation method"""
        with pytest.raises(ValueError, match="Unknown method"):
            run_monte_carlo(sample_returns, method='invalid')


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_returns(self):
        """Test with empty returns"""
        simulator = MonteCarloSimulator(MCSimulationConfig(n_simulations=10))
        empty_returns = pd.Series([], dtype=float)

        with pytest.raises(ValueError):
            simulator.simulate_bootstrap(empty_returns)

    def test_single_return(self):
        """Test with single return value"""
        simulator = MonteCarloSimulator(MCSimulationConfig(n_simulations=10))
        single_return = pd.Series([0.01])

        with pytest.raises(ValueError):
            simulator.simulate_bootstrap(single_return)

    def test_extreme_values(self):
        """Test with extreme return values"""
        np.random.seed(42)
        extreme_returns = pd.Series(
            np.concatenate([np.random.normal(0, 0.5, 100), [5.0, -5.0, 10.0, -10.0]])
        )

        simulator = MonteCarloSimulator(MCSimulationConfig(n_simulations=50))
        results = simulator.simulate_bootstrap(extreme_returns)

        assert isinstance(results, MCResults)
        # Should handle extreme values without breaking
        assert not np.any(np.isnan(results.final_values))
        assert not np.any(np.isinf(results.final_values))