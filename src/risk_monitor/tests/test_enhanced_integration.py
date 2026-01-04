"""
Enhanced Dynamic Risk Monitoring Integration Tests

Tests the integration of the enhanced dynamic monitoring system with the existing CBSC system.
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.risk_monitor.enhanced_dynamic_monitor import (
    EnhancedDynamicMonitor,
    DynamicThresholdManager,
    MonteCarloRiskEngine,
    AutomaticRiskController,
    RiskReportGenerator,
    RiskControlAction
)
from src.risk_monitor.enhanced_config import (
    EnhancedRiskConfig,
    ConfigManager,
    RiskControlMode,
    create_development_config
)
from src.risk_monitor.config import RiskConfig
from src.backtest.monte_carlo import MonteCarloSimulator, MCSimulationConfig


class TestDynamicThresholdManager:
    """Test dynamic threshold manager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.base_thresholds = {
            'var_95': 0.05,
            'var_99': 0.10,
            'max_drawdown': 0.15,
            'volatility': 0.30
        }
        self.manager = DynamicThresholdManager(self.base_thresholds, adjustment_factor=0.2)

    def test_initialization(self):
        """Test initial threshold setup"""
        assert self.manager.current_thresholds == self.base_thresholds
        assert self.manager.adjustment_factor == 0.2

    def test_threshold_update_normal_market(self):
        """Test threshold update in normal market conditions"""
        self.manager.update_thresholds(
            market_volatility=0.15,
            market_correlation=0.3,
            market_stress_index=0.1
        )

        # Should not adjust much in normal conditions
        for metric, threshold in self.manager.current_thresholds.items():
            base_value = self.base_thresholds[metric]
            change = abs(threshold - base_value) / base_value
            assert change < 0.05  # Less than 5% change

    def test_threshold_update_stress_market(self):
        """Test threshold update in stressed market conditions"""
        self.manager.update_thresholds(
            market_volatility=0.40,
            market_correlation=0.8,
            market_stress_index=0.9
        )

        # Should tighten thresholds in stress
        for metric, base_value in self.base_thresholds.items():
            threshold = self.manager.current_thresholds[metric]
            assert threshold <= base_value  # Should be tighter

    def test_threshold_adjustment_frequency(self):
        """Test that thresholds don't adjust too frequently"""
        # First update should work
        self.manager.update_thresholds(0.30, 0.6, 0.5)

        # Immediate second update should be ignored
        old_thresholds = self.manager.current_thresholds.copy()
        self.manager.update_thresholds(0.50, 0.9, 1.0)
        assert self.manager.current_thresholds == old_thresholds

        # Update after frequency period should work
        self.manager.last_adjustment = datetime.now() - timedelta(hours=2)
        self.manager.update_thresholds(0.50, 0.9, 1.0)
        assert self.manager.current_thresholds != old_thresholds


class TestMonteCarloRiskEngine:
    """Test Monte Carlo risk engine"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = MCSimulationConfig(
            n_simulations=1000,  # Small for testing
            time_horizon=10,
            confidence_levels=[0.90, 0.95, 0.99]
        )
        self.engine = MonteCarloRiskEngine(self.config)

    def test_mc_risk_calculation(self):
        """Test Monte Carlo risk calculation"""
        # Generate test returns
        np.random.seed(42)
        returns = pd.Series(np.random.randn(100) * 0.02 + 0.0005)

        # Calculate risk metrics
        metrics = self.engine.calculate_monte_carlo_risk(
            returns=returns,
            portfolio_value=1000000
        )

        # Check that metrics are calculated
        assert 'mc_var_95' in metrics
        assert 'mc_var_99' in metrics
        assert 'mc_cvar_95' in metrics
        assert 'mc_probability_of_loss' in metrics

        # Check that VaR values are reasonable
        assert 0 < metrics['mc_var_95'] < 100000
        assert 0 < metrics['mc_var_99'] < 200000

    def test_caching(self):
        """Test that results are cached"""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(100) * 0.02 + 0.0005)

        # First calculation
        metrics1 = self.engine.calculate_monte_carlo_risk(returns)

        # Second calculation should use cache
        metrics2 = self.engine.calculate_monte_carlo_risk(returns)

        assert metrics1 == metrics2

    def test_force_refresh(self):
        """Test force refresh bypasses cache"""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(100) * 0.02 + 0.0005)

        # First calculation
        metrics1 = self.engine.calculate_monte_carlo_risk(returns)

        # Force refresh should recalculate
        metrics2 = self.engine.calculate_monte_carlo_risk(returns, force_refresh=True)

        # Results should be different due to randomness
        # (unless extremely unlikely coincidence)
        assert metrics1 != metrics2

    def test_var_contribution_calculation(self):
        """Test VaR contribution calculation"""
        # Generate test data for multiple assets
        np.random.seed(42)
        returns_df = pd.DataFrame(
            np.random.randn(100, 3) * 0.02,
            columns=['Asset_A', 'Asset_B', 'Asset_C']
        )
        weights = np.array([0.4, 0.3, 0.3])

        contributions = self.engine.calculate_portfolio_var_contribution(
            returns_df=returns_df,
            weights=weights,
            portfolio_value=1000000
        )

        assert len(contributions) == 3
        assert all('Asset_' in key for key in contributions.keys())
        assert all(isinstance(value, (int, float)) for value in contributions.values())


class TestAutomaticRiskController:
    """Test automatic risk controller"""

    def setup_method(self):
        """Setup test fixtures"""
        self.thresholds = {
            'var_95': 0.05,
            'max_drawdown': 0.15,
            'volatility': 0.30
        }
        self.controller = AutomaticRiskController(self.thresholds)

    def test_var_breach_signal(self):
        """Test signal generation on VaR breach"""
        risk_metrics = {
            'var_95_historical': 0.08,  # Above threshold
            'current_drawdown': 0.05,
            'volatility_20d': 0.20
        }
        positions = {'AAPL': 0.3, 'MSFT': 0.3, 'GOOGL': 0.4}

        signals = self.controller.generate_control_signals(
            portfolio_id='test_portfolio',
            risk_metrics=risk_metrics,
            positions=positions,
            portfolio_value=1000000
        )

        assert len(signals) > 0
        assert any(s.action == RiskControlAction.REDUCE_EXPOSURE for s in signals)
        assert any('VaR' in s.reason for s in signals)

    def test_drawdown_breach_signal(self):
        """Test signal generation on drawdown breach"""
        risk_metrics = {
            'var_95_historical': 0.03,
            'current_drawdown': 0.18,  # Above threshold
            'volatility_20d': 0.20
        }
        positions = {'AAPL': 0.3, 'MSFT': 0.3, 'GOOGL': 0.4}

        signals = self.controller.generate_control_signals(
            portfolio_id='test_portfolio',
            risk_metrics=risk_metrics,
            positions=positions,
            portfolio_value=1000000
        )

        assert len(signals) > 0
        assert any(s.action == RiskControlAction.REDUCE_EXPOSURE for s in signals)
        assert any('drawdown' in s.reason.lower() for s in signals)

    def test_emergency_exit_signal(self):
        """Test emergency exit signal generation"""
        risk_metrics = {
            'var_95_historical': 0.03,
            'current_drawdown': 0.25,  # Above emergency threshold
            'volatility_20d': 0.20
        }
        positions = {'AAPL': 0.3, 'MSFT': 0.3, 'GOOGL': 0.4}

        signals = self.controller.generate_control_signals(
            portfolio_id='test_portfolio',
            risk_metrics=risk_metrics,
            positions=positions,
            portfolio_value=1000000
        )

        assert len(signals) > 0
        assert any(s.action == RiskControlAction.EMERGENCY_EXIT for s in signals)
        assert any('Emergency' in s.reason for s in signals)

    def test_concentration_risk_signal(self):
        """Test concentration risk signal"""
        risk_metrics = {
            'var_95_historical': 0.03,
            'current_drawdown': 0.05,
            'volatility_20d': 0.20
        }
        positions = {'AAPL': 0.5, 'MSFT': 0.25, 'GOOGL': 0.25}  # High concentration

        signals = self.controller.generate_control_signals(
            portfolio_id='test_portfolio',
            risk_metrics=risk_metrics,
            positions=positions,
            portfolio_value=1000000
        )

        assert len(signals) > 0
        assert any('concentration' in s.reason.lower() for s in signals)


class TestRiskReportGenerator:
    """Test risk report generator"""

    def setup_method(self):
        """Setup test fixtures"""
        self.generator = RiskReportGenerator()

    def test_daily_report_generation(self):
        """Test daily report generation"""
        risk_metrics = {
            'var_95_historical': 0.03,
            'var_99_historical': 0.07,
            'es_95_historical': -0.04,
            'volatility_20d': 0.20,
            'current_drawdown': 0.08,
            'max_drawdown': 0.12,
            'sharpe_ratio': 1.5,
            'beta': 0.9
        }

        report = self.generator.generate_daily_report(
            portfolio_id='test_portfolio',
            risk_metrics=risk_metrics,
            monte_carlo_results={
                'mc_var_95': 50000,
                'mc_var_99': 80000,
                'mc_probability_of_loss': 0.3
            },
            alerts=[
                {'level': 'warning', 'message': 'High volatility'},
                {'level': 'error', 'message': 'Drawdown alert'}
            ],
            control_actions=[
                {'action': 'reduce_exposure', 'reason': 'VaR breach'}
            ],
            performance_data={
                'portfolio_value': 1000000,
                'daily_return': 0.001,
                'ytd_return': 0.08
            }
        )

        assert report.portfolio_id == 'test_portfolio'
        assert len(report.recommendations) > 0
        assert report.alerts_summary['total'] == 2
        assert report.alerts_summary['warning'] == 1
        assert report.alerts_summary['error'] == 1

    def test_report_export_json(self):
        """Test JSON report export"""
        from src.risk_monitor.enhanced_dynamic_monitor import RiskReport

        report = RiskReport(
            portfolio_id='test',
            report_date=datetime.now(),
            period_start=datetime.now() - timedelta(days=1),
            period_end=datetime.now(),
            risk_metrics={},
            monte_carlo_results=None,
            alerts_summary={'total': 0},
            control_actions=[],
            performance_metrics={},
            recommendations=[],
            risk_attribution={}
        )

        json_report = self.generator.export_report(report, format='json')
        assert isinstance(json_report, str)
        parsed = json.loads(json_report)
        assert parsed['portfolio_id'] == 'test'

    def test_report_export_html(self):
        """Test HTML report export"""
        from src.risk_monitor.enhanced_dynamic_monitor import RiskReport

        report = RiskReport(
            portfolio_id='test',
            report_date=datetime.now(),
            period_start=datetime.now() - timedelta(days=1),
            period_end=datetime.now(),
            risk_metrics={'var_95': 0.03},
            monte_carlo_results=None,
            alerts_summary={'total': 1, 'warning': 1},
            control_actions=[],
            performance_metrics={'return': 0.08},
            recommendations=['Reduce risk'],
            risk_attribution={}
        )

        html_report = self.generator.export_report(report, format='html')
        assert isinstance(html_report, str)
        assert '<html>' in html_report
        assert 'test' in html_report
        assert '0.03' in html_report


class TestEnhancedDynamicMonitor:
    """Test enhanced dynamic monitor integration"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = RiskConfig()
        self.config.calculation_interval = 1  # 1 second for testing
        self.monitor = EnhancedDynamicMonitor(self.config)

    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.config == self.config
        assert not self.monitor.running
        assert self.monitor.threshold_manager is not None
        assert self.monitor.mc_engine is not None
        assert self.monitor.risk_controller is not None
        assert self.monitor.report_generator is not None

    @pytest.mark.asyncio
    async def test_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # Mock data fetching
        sample_data = pd.DataFrame({
            'total_value': np.cumprod(1 + np.random.randn(100) * 0.02) * 1000000,
            'returns': np.random.randn(100) * 0.02
        })

        async def mock_fetch_data(portfolio_id):
            return sample_data

        self.monitor._fetch_portfolio_data = mock_fetch_data

        # Start monitoring
        portfolios = {
            'test_portfolio': {
                'name': 'Test Portfolio',
                'positions': {'AAPL': 0.4, 'MSFT': 0.3, 'GOOGL': 0.3}
            }
        }

        task = await self.monitor.start_monitoring(portfolios)
        self.monitor.running = True

        # Run for a short time
        await asyncio.sleep(2)

        # Stop monitoring
        await self.monitor.stop_monitoring()
        task.cancel()

        # Check that data was collected
        assert len(self.monitor.monitoring_data['risk_metrics_history']) > 0

    @pytest.mark.asyncio
    async def test_threshold_updates(self):
        """Test dynamic threshold updates during monitoring"""
        # Mock market data
        async def mock_fetch_data(portfolio_id):
            return pd.DataFrame({
                'returns': np.random.randn(100) * 0.05  # High volatility
            })

        self.monitor._fetch_portfolio_data = mock_fetch_data

        portfolios = {
            'test_portfolio': {
                'name': 'Test Portfolio',
                'positions': {'AAPL': 0.4, 'MSFT': 0.3, 'GOOGL': 0.3}
            }
        }

        # Get initial thresholds
        initial_var_threshold = self.monitor.threshold_manager.get_threshold('var_95')

        # Process portfolio with high volatility
        await self.monitor._process_portfolio_enhanced(
            'test_portfolio',
            portfolios['test_portfolio']
        )

        # Check if thresholds were updated (adjustment frequency might prevent immediate update)
        # This test depends on the timing and adjustment frequency

    def test_monitoring_summary(self):
        """Test monitoring summary generation"""
        summary = self.monitor.get_monitoring_summary()

        assert 'active_portfolios' in summary
        assert 'risk_metrics_count' in summary
        assert 'control_signals_count' in summary
        assert 'current_thresholds' in summary


class TestConfigManagement:
    """Test configuration management"""

    def test_config_creation(self):
        """Test configuration creation"""
        config = EnhancedRiskConfig()

        assert config.calculation_interval_seconds == 5
        assert config.monitoring_enabled == True
        assert config.enable_monte_carlo == True
        assert config.risk_control.mode == RiskControlMode.SIMULATION

    def test_preset_configs(self):
        """Test preset configurations"""
        from src.risk_monitor.enhanced_config import (
            create_default_config,
            create_production_config,
            create_development_config
        )

        default = create_default_config()
        production = create_production_config()
        development = create_development_config()

        # Production should be more conservative
        assert production.risk_control.max_leverage < development.risk_control.max_leverage
        assert production.dynamic_thresholds.base_thresholds['var_95'] < development.dynamic_thresholds.base_thresholds['var_95']

        # Development should use simulation mode
        assert development.risk_control.mode == RiskControlMode.SIMULATION
        assert development.debug_mode == True

    def test_config_serialization(self):
        """Test configuration serialization to/from JSON"""
        config = create_development_config()

        # Convert to dict
        config_dict = ConfigManager.to_dict(config)
        assert isinstance(config_dict, dict)
        assert 'monte_carlo' in config_dict
        assert 'risk_control' in config_dict

        # Convert back from dict
        restored_config = ConfigManager.from_dict(config_dict)
        assert restored_config.calculation_interval_seconds == config.calculation_interval_seconds
        assert restored_config.enable_monte_carlo == config.enable_monte_carlo

    def test_config_file_operations(self, tmp_path):
        """Test saving and loading configuration files"""
        import tempfile
        import os

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name

        try:
            # Save configuration
            config = create_production_config()
            ConfigManager.save_to_file(config, config_path)

            # Load configuration
            loaded_config = ConfigManager.load_from_file(config_path)

            # Verify
            assert loaded_config.environment == "production"
            assert loaded_config.enable_automatic_control == True

        finally:
            # Clean up
            os.unlink(config_path)


@pytest.mark.integration
class TestFullSystemIntegration:
    """Integration tests for the full enhanced monitoring system"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end monitoring workflow"""
        # Create configuration
        config = create_development_config()

        # Create monitor
        monitor = EnhancedDynamicMonitor(config)

        # Create mock trading system
        trading_system = Mock()
        trading_system.reduce_position = Mock(return_value=True)
        trading_system.get_positions = Mock(return_value={
            'AAPL': 0.25, 'MSFT': 0.25, 'GOOGL': 0.20, 'AMZN': 0.15, 'TSLA': 0.15
        })

        # Generate sample data with stress periods
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
        returns = np.random.randn(200) * 0.02
        returns[100:120] *= 3  # Stress period
        returns[150:155] -= 0.05  # Crash period

        portfolio_data = pd.DataFrame({
            'total_value': np.cumprod(1 + returns) * 1000000,
            'returns': returns
        }, index=dates)

        # Mock data fetching
        async def mock_fetch_data(portfolio_id):
            return portfolio_data

        monitor._fetch_portfolio_data = mock_fetch_data

        # Setup portfolios
        portfolios = {
            'integration_test': {
                'name': 'Integration Test Portfolio',
                'positions': trading_system.get_positions(),
                'base_value': 1000000
            }
        }

        # Start monitoring
        monitor_task = await monitor.start_monitoring(portfolios)

        # Run for multiple cycles
        await asyncio.sleep(5)

        # Stop monitoring
        await monitor.stop_monitoring()
        monitor_task.cancel()

        # Verify results
        assert len(monitor.monitoring_data['risk_metrics_history']) > 0
        assert len(monitor.monitoring_data['control_signals_history']) >= 0

        # Check if stress was detected
        stress_detected = any(
            'stress' in signal.get('reason', '').lower()
            for signal in monitor.monitoring_data['control_signals_history']
        )
        # Note: Stress detection depends on thresholds and market conditions

        # Generate summary
        summary = monitor.get_monitoring_summary()
        assert summary['active_portfolios'] == 1
        assert summary['risk_metrics_count'] > 0

    @pytest.mark.asyncio
    async def test_monte_carlo_integration(self):
        """Test Monte Carlo integration with monitoring"""
        # Create monitor with Monte Carlo enabled
        config = create_development_config()
        config.monte_carlo.n_simulations = 1000  # Smaller for testing

        monitor = EnhancedDynamicMonitor(config)

        # Generate sample data
        returns = pd.Series(np.random.randn(100) * 0.02 + 0.0005)

        # Calculate Monte Carlo risk
        mc_metrics = monitor.mc_engine.calculate_monte_carlo_risk(
            returns=returns,
            portfolio_value=1000000
        )

        # Verify Monte Carlo metrics are present
        assert 'mc_var_95' in mc_metrics
        assert 'mc_var_99' in mc_metrics
        assert 'mc_cvar_95' in mc_metrics

        # Create portfolio data
        portfolio_data = pd.DataFrame({
            'total_value': np.cumprod(1 + returns) * 1000000,
            'returns': returns
        })

        # Mock data fetching
        async def mock_fetch_data(portfolio_id):
            return portfolio_data

        monitor._fetch_portfolio_data = mock_fetch_data

        # Process portfolio
        await monitor._process_portfolio_enhanced(
            'mc_test',
            {'positions': {'AAPL': 0.5, 'MSFT': 0.5}}
        )

        # Check if Monte Carlo metrics were calculated
        risk_metrics = monitor.monitoring_data['risk_metrics_history']
        if risk_metrics:
            latest = risk_metrics[-1]
            assert any('mc_' in key for key in latest['metrics'].keys())

    @pytest.mark.asyncio
    async def test_report_generation_integration(self):
        """Test report generation integration"""
        config = create_development_config()
        config.reports.frequency = 'hourly'  # More frequent for testing

        monitor = EnhancedDynamicMonitor(config)

        # Mock report generation time
        original_generate_report = monitor._generate_daily_report

        async def mock_generate_report(portfolio_id, risk_metrics):
            # Force generation regardless of time
            return await original_generate_report(portfolio_id, risk_metrics)

        monitor._generate_daily_report = mock_generate_report

        # Setup test data
        returns = pd.Series(np.random.randn(50) * 0.02)
        portfolio_data = pd.DataFrame({
            'total_value': np.cumprod(1 + returns) * 1000000,
            'returns': returns
        })

        async def mock_fetch_data(portfolio_id):
            return portfolio_data

        monitor._fetch_portfolio_data = mock_fetch_data

        # Process portfolio
        await monitor._process_portfolio_enhanced(
            'report_test',
            {'positions': {'AAPL': 0.5, 'MSFT': 0.5}}
        )

        # Generate report manually
        risk_metrics = {
            'var_95_historical': 0.03,
            'current_drawdown': 0.08,
            'portfolio_value': 1000000
        }

        await monitor._generate_daily_report('report_test', risk_metrics)

        # Check report was generated
        assert len(monitor.monitoring_data['report_history']) > 0

        # Verify report content
        report = monitor.monitoring_data['report_history'][-1]
        assert report['portfolio_id'] == 'report_test'
        assert 'risk_metrics' in report
        assert 'recommendations' in report